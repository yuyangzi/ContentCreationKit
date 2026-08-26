# 老师傅和学徒：投机解码是怎么白送 K-1 个 token 的

> **导读**：上一篇文章讲了怎么把 KV cache 那本"账本"放得下、用得省。但账本放下来之后，每生成一个 token 还是要让 GPU 跑一遍完整的前向。这一步最费时间。问题是：为什么不能像训练时那样，一次并行算出好几个 token 出来？答案藏在自回归生成本身的串行依赖里，而投机解码（Speculative Decoding）做的事情，就是在不破坏这种依赖的前提下，让"算"这件事变得便宜。

---

## 一、接上一篇：账本放下来了，可账还没算完

上一篇文章最后留了一个悬念：把 KV cache 用 PagedAttention 切成 block、用前缀缓存复用掉重复部分之后，显存这块账本确实放下来了。但账本只是历史记录，每个新 token 真正生成的时候，GPU 还是要跑一遍完整的前向计算，从头到尾把这一轮的 query 和全部历史的 key 都点乘一遍。

decode 阶段的每一步都是 memory-bound，不是 compute-bound。这是上一篇文章已经讲过的判断：单步计算量小，但每步都要把 KV cache 从显存里完整地读出来给 GPU 用。换句话说，**GPU 算力大部分时间是闲着的，只是因为要等显存把数据搬过来**。

那能不能一次多生成几个 token，把 GPU 那部分闲着的算力用上？直觉上当然想这么干。但问题出在自回归的依赖关系上。

---

## 二、为什么不能一次生成多个 token：自回归的串行链

自回归生成的意思是：生成第 t 个 token，需要前面所有 token 都已经在。前一个 token 没确定，后一个 token 就不能开始算。用公式写出来是这样的：

```
p(x_{t+1} | x_1, x_2, ..., x_t)
```

第 t+1 个 token 的概率分布，依赖于第 t 个 token 的具体值。所以第 t 个 token 没生成出来，第 t+1 个 token 就没法算。这就是为什么训练时明明可以并行，推理时却必须串行。

直觉上，把第 t+1 个 token 也猜一个值，下一步直接算下去。

但问题在于，下一步的 query 要和前面所有 token 的 key 做点乘，**包括第 t+1 个 token 自己的 key**。第 t+1 个 token 猜错了，第 t+2 个 token 的 query 也要重算；第 t+2 个 token 又错了，第 t+3 个也跟着错……一次错就全错，整条链都要回滚。

这就是自回归串行生成的本质：**每一步都建在前一步的结果上，错的代价是连锁的**。

所以很长一段时间里，研究者的共识是：token 生成就是串行的，没办法。这就是为什么单条请求的生成速度（tokens per second）一直提不上去。

但 2022 年底，Google 的一个团队做了一件反直觉的事：**猜错了就扔，猜对了就收下**。这就是投机解码的核心想法。

---

## 三、投机解码：老师傅和学徒

打个比方。一个经验老到的老师傅，和一个刚入门的学徒，一起做工。老师傅干活慢但手艺好，学徒干活快但容易出错。如果让学徒先快速做几步粗活，老师傅再做一次质检，挑出错的地方返工、对的地方直接收下。

老师傅的"质检"成本是多少？很低。因为不管学徒提了几份候选，老师傅做一次质检的时间基本不随候选数量增加。他不关心候选有多少，他只是扫一眼。

这就是投机解码的核心结构：

- **目标模型**（target model）：老师傅。手艺好，慢。代表最终输出质量。
- **草稿模型**（draft model）：学徒。手艺差，快。负责提出候选 token。
- **验证过程**：老师傅用一次并行前向，把学徒提出的 K 个候选 token 一起检查一遍。

如果学徒猜得准，老师傅一次性收下 K 个 token，赚到了 K-1 个 token 的加速。如果学徒猜错，从猜错的那个位置开始，老师傅用自己的判断覆盖掉，后面的全部扔掉。这一轮没赚到的，下一轮再来。

整个流程里，目标模型的工作量没增加多少。它还是每个 decode 步只跑一次前向（验证 K 个候选并不比验证 1 个慢多少，因为本来就是要读 KV cache 整本账本，瓶颈在访存而不在算）。但 token 产出量可能增加了好几倍。

这里有一个关键的设计：**目标模型的输出分布被严格保留**。不是说草稿模型的判断最终会被采纳，而是说：哪怕草稿模型参与了，最终每一个被采纳的 token，都经过目标模型自己的验证。验证的方法是，问目标模型"如果只看前文，你也会猜这个 token 吗"，如果同意，就收下；如果更倾向于另一个 token，就以目标模型的判断为准。

Leviathan 等人 2022 年底发表在 arXiv 上的论文（后来 ICML 2023 发表）从数学上证明了这个机制：只要草稿模型和目标模型的概率分布都摆在那里，**最终从投机解码出来的 token 序列，与直接用目标模型生成的序列，在统计上保持一致**。这是一项"无损"加速。

下面是一段简化的伪代码，演示一轮投机解码的核心循环：

```Python
def speculative_step(prefix, draft_model, target_model, K=5):
    # 学徒阶段：草稿模型串行生成 K 个候选 token，并记下每一步的概率分布
    draft_tokens = []
    q_probs = []
    for _ in range(K):
        token = draft_model.generate_next(prefix + draft_tokens)
        draft_tokens.append(token)
        q_probs.append(draft_model.prob_dist(prefix + draft_tokens))

    # 老师傅阶段：目标模型一次并行验证 K 个候选位置
    target_logits = target_model.forward(prefix + draft_tokens)  # 一次前向，K+1 个位置的概率分布

    # 接受环节：从前往后逐个问"目标模型也同意吗"
    accepted = 0
    for i in range(K):
        p = target_logits[i][draft_tokens[i]]   # 目标模型给这个候选 token 的概率
        q = q_probs[i][draft_tokens[i]]         # 草稿模型的概率
        if random() < min(1, p / q):
            accepted += 1                         # 同意，收下
        else:
            break                                 # 不同意，从这里开始全部丢弃

    # 拒绝补救：如果前面 accepted 个都被接受但下一个被拒，
    # 从"修正分布"（目标概率减草稿概率后取正、归一化）重抽一个 token，作为新的起点
    if accepted < K:
        residual = target_logits[accepted] - q_probs[accepted]
        corrected_token = sample_from(residual.clamp(min=0).normalize())
        return draft_tokens[:accepted] + [corrected_token]
    else:
        # 全部接受：再用目标模型自己额外预测一个 token，作为下一轮起点
        bonus_token = sample_from(target_logits[K])
        return draft_tokens + [bonus_token]
```

这段代码里最关键的一行是 `min(1, p / q)`。它就是接受准则：当目标模型和草稿模型对同一个 token 的意见一致时（p/q 接近 1），直接收下；当目标模型觉得这个 token 没那么好时（p/q < 1），按这个比值概率拒绝。最终的统计性质，是 Leviathan 那篇论文证明出来的核心结论。

---

## 四、加速从哪来：用"白嫖"填满访存瓶颈

回到上一篇文章铺垫的那条主线：decode 阶段是 memory-bound，瓶颈在访存。

如果不投机，目标模型每跑一次前向，从显存里读出 KV cache 整本账本，最终只产出 1 个 token。GPU 的算力大部分时间是闲着的。

投机解码做的事情，是让这一轮访存的产出从 1 个 token 变成 A 个 token（A 是这一轮被目标模型接受的草稿 token 平均数）。访存成本没变，token 产出翻了几倍。

这就是加速的来源。**不是算得更快，是用同样的访存换更多的 token**。

这也解释了为什么投机解码在 batch size 小的时候效果最好。batch size 大的时候，目标模型本来就需要把多个请求的 KV cache 都读出来给它用，访存瓶颈已经基本被填满了。这时候再叠加草稿模型的额外开销，反而可能把目标模型的算力也挤占掉一部分。所以 batch 增大之后，加速比会一路跌破 1，投机解码有时比不用还慢。

反过来的极端情况是 batch size = 1。这时目标模型基本是单条请求独占 GPU，访存还远没填满，投机解码可以把空着的算力用上，速度能快 2-3 倍。

所以投机解码是一种"在访存没填满的时候填补空隙"的技术。这句话反过来说也成立：**当访存已经填满，投机解码就帮不上忙了**。

---

## 五、四年：投机解码的变体是怎么长出来的

投机解码的核心思想从 2022 年提出到 2026 年的今天，思路没变，但实现方式变了四代。下面按时间顺序看四个有代表性的方案。

### 5.1 EAGLE 系列：业界事实标准

EAGLE 的思路是反其道而行：不要单独的草稿模型了，直接在目标模型的隐藏层（hidden state）上外挂一个超小的"自回归预测头"。这个预测头只有一层 Transformer，草稿头只占目标模型几个百分点的参数，它从目标模型倒数第二层的特征向量往下推算下一个 token。

EAGLE-1 在 2024 年的 ICML 上发表，13B 模型上测出 3 倍加速，比当时的 Lookahead 快 2 倍、比 Medusa 快 1.6 倍（EAGLE 论文）。

EAGLE-2 引入了"动态 draft tree"：草稿模型不只提一条候选，而是同时提多条可能的分支，让目标模型一起验证，挑出最长的那条。EAGLE-3 在 2025 年的 NeurIPS 上发表，做了两件事：草稿时直接预测 token（不再卡在特征预测的约束上）；用目标模型的多层特征（低层、中层、高层）融合代替单层特征。

到了 2026 年，EAGLE-3 已被业界普遍接受为投机解码的事实标准。vLLM、SGLang、TensorRT-LLM 三大推理框架都原生支持，AWS 在 2026 年初又往前推了一步，把 EAGLE-3 的串行瓶颈也消掉了，叫 P-EAGLE，在真实负载上又提了 1.69 倍（AWS 官方博客）。

### 5.2 Lookahead：完全不要草稿模型的另一条路

如果连草稿模型都不想要呢？

Lookahead 解码（2024 年 ICML）的做法源自一个数学观察：自回归生成可以看成是求解一个非线性方程组，Jacobi 迭代法可以一次算出所有未知数的近似解。多轮 Jacobi 迭代之后，会生成一组 n-gram 候选项。Lookahead 把这些候选项收集起来，存到一个 n-gram 池里，让目标模型下一次前向时一并验证。

它的好处是不需要任何额外的模型、不需要训练。目标模型自己玩自己的事，顺便把可能的 token 都给"猜"出来。代价是猜的命中率没有专门的草稿模型那么高，所以加速比通常落在 1.6 到 2 倍之间。

这条路的代表论文是 Fu 等人的《Break the Sequential Dependency of LLM Inference Using Lookahead Decoding》（arXiv:2402.02057），GitHub 上 hao-ai-lab/LookaheadDecoding 是官方实现。

### 5.3 MTP：把草稿头直接焊进主模型

DeepSeek-V3 的技术报告里（arXiv:2412.19437）讲了一种完全不同的策略：在训练主模型的时候就让它多预测几个 token，把这些"多预测头"作为额外的训练目标。训练完成后，这些预测头可以被扔掉（普通推理不需要），也可以被复用为投机解码的草稿器。

DeepSeek-V3 的论文里给了一组数据：用 MTP 作为草稿器，第二个 token 的接受率稳定在 85% 到 90%，整体推理的 tokens per second 提升 1.8 倍（DeepSeek-V3 技术报告）。SGLang 在 2025 年 7 月把 DeepSeek-V3 的 MTP 模块深度集成后，输出吞吐又涨了 60%（LMSYS 实测）。

这条路的特点是**主模型自己就是草稿模型的母体**。不需要外部的草稿模型，不需要单独训练，权重已经随主模型一起发出来了。代价是训练成本（要算多个 token 的损失）会高一些。

### 5.4 Medusa：给大模型加多个解码头

Medusa 是 EAGLE 同期出现的另一种思路：在目标模型的输出层旁边加多个预测头，每个预测头预测未来第 1、第 2、第 3 个 token。每个头上挂一个独立的分类器。推理时，目标模型一次前向就能给出多个位置的预测，然后用一个"tree attention"机制把多个候选组合在一起验证。

Medusa 的好处是结构简单，缺点是训练成本（每个头都要单独训）和推理时的额外计算（多头同时算）都不小，这也是它最终没能跑赢 EAGLE 的原因之一。

**这四条路线，其实就是草稿器从哪来这个问题的四种回答**：用一个独立小模型（经典 SD）、从目标模型特征里抽一个预测头（EAGLE）、让目标模型自己玩 Jacobi 迭代（Lookahead）、把多 token 预测直接焊进训练目标（MTP）。Medusa 则是另一条线，在推理时于输出层外挂多个解码头（需多任务微调），严格说是介于 EAGLE 与 MTP 之间的思路。工程上各有取舍，最终活下来的、能在生产里跑得动的是 EAGLE 系列和 MTP。

---

## 六、它不是什么万能药

投机解码不破坏输出分布、还能加速 2-3 倍，但它不是所有场景都适用，适用边界很明确。

**第一，高 batch 下收益消失甚至反向。** 投机解码的本质是用目标模型空闲的访存算力换更多 token。当 batch size 大、目标模型本身已经把 GPU 算得满负荷时，草稿模型的开销就变成纯负担了。vLLM 自己也提供了按 batch size 动态关闭投机的开关。这不是投机解码的失败，是访存瓶颈被填满之后的物理事实。

**第二，跨 tokenizer 收益打折。** 草稿模型和目标模型的 tokenizer 不一致时，加速会明显打折。原因是要在两种 token 之间做转换，验证成本上升。

**第三，创意写作接受率低。** 代码补全、数学推理这类任务，token 之间的概率分布相对集中（同一个变量名、同一个推导方向反复出现），接受率高。创意写作里下一个 token 的可能性分布很散，草稿模型很难猜中，接受率低，加速效果自然有限。

**第四，需要额外的显存和算力。** 经典 SD 需要一个独立的草稿模型（即使是 EAGLE 这种极简方案，草稿头也要占目标模型 10% 不到的算力和参数），这部分开销在边缘部署、显存紧张场景下不是小数。

这就是为什么主流推理框架都把投机解码做成了一个**可选项**，由用户在部署时根据场景选择开启。vLLM 在启动时通过 `--speculative-config` 配置草稿方法和投机长度，开发者需要根据自己的流量特征调一组参数（草稿长度 K、模型选型、tokenizer 兼容性），而不是一键开启就能拿到全部收益。

---

## 七、回到那个老师傅

老师傅和学徒一起做工的设想，听起来简单，但落地要解决一连串问题：学徒的手艺怎么训练？学徒做错了老师傅怎么判断？一次让学徒做几步合适？高负载时还要不要让学徒上场？

这四年里投机解码走过的路，就是回答这些问题的过程。经典 SD 给出第一个完整版本；EAGLE 把学徒的培养成本压到极致；Lookahead 让学徒这个角色消失；MTP 把学徒的工作直接编进师傅的成长过程。每一步都让投机解码在更多场景里变得可用，也各自带来新的约束。

**投机解码不是解决 LLM 推理慢的银弹，它只是把目标模型里那些空着的访存算力填上了**。当 GPU 已经满负荷运转，它帮不上忙；当 token 之间的可预测性低，它也帮不上忙。但它是一种"在合适场景下能白送 K-1 个 token"的技巧。这件事在 GPU 推理的语境下，已经是性价比非常高的一种加速手段。

至于下一个 K 是怎么填上的，那要看草稿模型本身的训练、KV cache 进一步压缩、目标模型的稀疏化等几条线分别能推进到什么程度了。

---

*参考来源：*

- Leviathan, Kalman, Matias. *Fast Inference from Transformers via Speculative Decoding*. ICML 2023. https://arxiv.org/abs/2211.17192
- Chen et al. *Accelerating Large Language Model Decoding with Speculative Sampling*. 2023. https://arxiv.org/abs/2302.01318
- Fu, Bailis, Stoica, Zhang. *Break the Sequential Dependency of LLM Inference Using Lookahead Decoding*. ICML 2024. https://arxiv.org/abs/2402.02057
- Li et al. *EAGLE: Speculative Sampling Requires Rethinking Feature Uncertainty*. ICML 2024. https://arxiv.org/abs/2401.15077
- Li et al. *EAGLE-2: Faster Inference of Language Models with Dynamic Draft Trees*. EMNLP 2024. https://arxiv.org/abs/2406.16858
- Li et al. *EAGLE-3: Scaling up Inference Acceleration of Large Language Models via Training-Time Test*. NeurIPS 2025. https://arxiv.org/abs/2503.01840
- Cai et al. *Medusa: Simple LLM Inference Acceleration Framework with Multiple Decoding Heads*. 2024. https://arxiv.org/abs/2401.10774
- DeepSeek-AI. *DeepSeek-V3 Technical Report*. 2024. https://arxiv.org/abs/2412.19437
- SafeAILab. *EAGLE: Official Implementation of EAGLE-1/2/3*. https://github.com/SafeAILab/EAGLE
- vLLM Project. *Speculative Decoding Documentation*. https://docs.vllm.ai/en/latest/features/speculative_decoding
- LMSYS Org. *Accelerating SGLang with Multiple Token Prediction*. 2025. https://www.lmsys.org/blog/2025-07-17-mtp
- AWS Machine Learning Blog. *P-EAGLE: Faster LLM inference with Parallel Speculative Decoding in vLLM*. 2026. https://aws.amazon.com/blogs/machine-learning/p-eagle-faster-llm-inference-with-parallel-speculative-decoding-in-vllm
- Google Research. *Looking back at speculative decoding*. https://research.google/blog/looking-back-at-speculative-decoding
- NVIDIA Developer Blog. *An Introduction to Speculative Decoding for Reducing Latency in AI Inference*. https://developer.nvidia.com/blog/an-introduction-to-speculative-decoding-for-reducing-latency-in-ai-inference
- laumy. *投机解码原理：用草稿模型加速大模型生成*. https://www.laumy.tech/notes/posts/ai/%E7%AE%97%E6%B3%95%E6%A8%A1%E5%9E%8B/%E6%8A%95%E6%9C%BA%E8%A7%A3%E7%A0%81%E5%8E%9F%E7%90%86%E7%94%A8%E8%8D%89%E7%A8%BF%E6%A8%A1%E5%9E%8B%E5%8A%A0%E9%80%9F%E5%A4%A7%E6%A8%A1%E5%9E%8B%E7%94%9F%E6%88%90
