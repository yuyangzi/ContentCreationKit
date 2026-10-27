---
title: "把思考移出 token：HybridAgents 的混合介质与工程账单"
date: 2026-10-26
topic: HybridAgents 混合介质与工程账
mode: deep-tech
---

# 把思考移出 token：HybridAgents 的混合介质与工程账单

> **导读**：Agent 的中间推理一直被写成 token，可读、可审计，代价是每一步都要为生成付费。2026 年 10 月，斯坦福、UIUC、Together AI 与 Meta 的团队在 arXiv 挂出 Hybrid Reasoning Agents，让文本与潜空间在同一条生成序列里交替出现：RL 阶段平均提升 10.4%，生成侧 token 少用 35.5% 到 54.7%，推理快 1.8 到 2.6 倍。
>
> 机制成立，相对同规模基线 benchmark 也赢了。只是省下的那笔 token，账单落在了推理栈上。

2026 年 10 月 13 日，斯坦福、UIUC 与 Together AI 的团队把一篇 45 页的论文挂上 arXiv，编号 2610.18861，标题是 Hybrid Reasoning Agents。作者八人，机构栏里还有 Meta，James Zou 是末位作者。

摘要给了一组数字：平均提升 10.4%，token 少用 35.5% 到 54.7%，推理快 1.8 到 2.6 倍，成本降到三分之一。这组数字在 Hacker News 上换来了 520 分和 239 条评论。

它真正回答的是一个介质问题：Agent 的中间推理，是不是一定要逐 token 写成自然语言。工具调用和人工审计都要求可读文本，纯潜空间给不出这两样；论文的答案是「两边都留着」，在同一条生成序列里来回切换。这个答案在机制上成立，在 benchmark 上也赢了。

---

## 三种介质，三种代价

从 ReAct 开始，Agent 的推理介质就是文本。模型把每一步想法写成 token，这些 token 留在上下文里，下一步再读一遍。三项成本随之而来：

- 生成要按 token 付费
- 轨迹挤占本该留给任务信息的窗口
- 逐 token 生成是串行的

潜空间推理想换掉这个介质。Coconut（Chain of Continuous Thought，arXiv:2412.06769）是把最后一层隐状态直接回灌成下一步输入，一步连续思维能同时编码多条候选路径，效果上更接近在解空间里铺开搜索，而不是过早押一条路。这条路省掉了整个解码和重新嵌入的环节。

代价也很明确。潜空间里没有工具接口，模型没法在中途停下来查一次数据库或者跑一次计算；外部也看不到它在想什么，因为中间状态是连续向量。

这个代价在 Agent 任务上是有数据的。论文 Table 1 里，Coconut 8B 在 GAIA 上是 3.9，WebWalker 上 0.5，基本等于失效。这个对比对 Coconut 未必公平，它本来不是为工具任务设计的；即便如此，它至少旁证了上一段的判断：跳过文本，也就跳过了外部世界的接口。

还有两条路线常被混进同一个筐里，但都没有改介质。pause token（arXiv:2310.02226）在答案前插几个可学习的占位 token，让模型多算几步再开口，输出还是可读的文本。

CODI（Continuous Chain-of-Thought via Self-Distillation，arXiv:2502.21074）用自蒸馏把显式思维链压进指定 token 的隐状态，压缩 3.1 倍，但一次前向只吐一个隐状态，中途插不进外部动作。

三种介质的分水岭，不在快慢，在能不能中途停下来跟外部世界说话。

---

## 三件套：适配器、锚点、工作记忆

架构上有三件事，缺一件这套东西就不成立。

**HybridLink 把隐状态送回输入空间。** 潜空间模式下的下一步输入，取自最后一层隐状态 h_t；文本模式下的下一步输入，取自词嵌入 Emb(y_{t+1})。两者维度可能对不上，也可能分布对不上，所以中间需要一个映射：

R(h_t) = h_t + W₂·GELU(W₁·h_t)

两层 MLP 加一条残差。4B 模型上约 10M 参数，大约是 2·d²（论文原文口径）。潜空间步里它取代 LM head 和 token embedding 层，骨干网络一行没改。

残差是这里的关键设计。论文的消融（Table 6，14B，MATH500）里，不加对齐的 identity 版是 71.4，单层 83.6，单层加残差 86.4，两层不加残差 85.8，两层加残差 88.2。残差在两组对比里分别值 2.8 和 2.4 个点，原因是它保住了 h_t 原本的语义，适配器只需要对齐分布上的差异，不必从零学一个完整投影。

仓库里的实现比论文公式多了两处归一化：

```Python
class HybridLink(nn.Module):
    """把最后一层隐状态映射回输入嵌入空间"""
    def __init__(self, hidden_size):
        super().__init__()
        self.proj1 = nn.Linear(hidden_size, hidden_size)
        self.act = nn.GELU()
        self.proj2 = nn.Linear(hidden_size, hidden_size)
        self.pre_ln = nn.LayerNorm(hidden_size)
        self.post_ln = nn.LayerNorm(hidden_size)

    def forward(self, h_t):
        delta = self.proj2(self.act(self.proj1(self.pre_ln(h_t))))
        # 仓库实现（adapter_type: ln_res_adapter）；论文 Eq.4 写作 h + W2·σ(W1·h)，没提归一化
        return self.post_ln(h_t + delta)
```

前向里只有加法和两次线性变换，参数量和词表投影不在一个量级。真正省下来的不是适配器的计算，是跳过 LM head 那一次全词表 softmax，以及跳过把新 token 重新嵌入的那一步。

**锚点 token 决定什么时候进，退出条件决定什么时候出。** 文本模式采样出 `<latent>` 就进入潜空间；在潜空间里每一步算一次 R(h_t)，当它在词表里余弦最近的是 `</latent>` 时切回文本。这两个特殊 token 在 Qwen3 词表里的编号是 151669 和 151670（编号来自 issue #6 复现者的 tokenizer 实测，非论文数据）。

论文说 span 长度是动态涌现的，但实现上有一段钳制：单个潜空间段最短 16 步，最长 256 步（附录 H.3）。所以它是半自适应，退出时机由模型学出来的策略决定，边界是人给的。

**工作记忆就是 KV cache（键值缓存）本身。** 文本 token、潜空间向量、工具返回的结果，全部映射进同一个输入空间，Transformer 统一处理后累积 KV 条目。

论文直接把这些累积的 KV 条目当成 Agent 的工作记忆，跨轮时往后追加，下一轮直接从现有状态继续，不重建 token 序列，也不重新 prefill。附录 A 给了一个定理来论证这种做法的无损性，用的词是 lossless。

这个设计解决的是潜空间推理在多轮场景下的老问题：如果每一轮都把历史重新编码成 token，潜空间那部分会失真甚至丢失。代价是主流推理框架都不支持，作者自己扩展了引擎才跑起来。

---

## 切换点不是超参数，是训练出来的

机制讲完，剩下的问题是切换点怎么来。论文的后训练分两段。第一段 HybridSFT 教骨干模型配合 HybridLink，让「文本、潜空间、文本」的混合生成稳定下来；第二段 HybridRL 在这个基础上学「什么时候该想，什么时候该说」。RL 的实现在论文 §4.2（Algorithm 1 与奖励式 11），本文不展开，值得看的是第一段的数据怎么造。

他们把现成的多轮 agent 演示自动改写成 54K 条混合轨迹，其中两个信号决定每一步走哪种介质。

一个是外部 LLM 评委，判断这一步是不是需要外部信息、是不是需要留下审计痕迹。判「是」的步骤强制留在文本，工具交互和权限相关的动作都在这一档。

另一个是目标模型自己的 token 级熵。在 teacher-forcing（用标准答案逐 token 喂入）下算每一步的平均熵，**低熵的步骤进潜空间，高熵的步骤留文本**。这条信号的直觉很直白：模型很确定的地方，写出来是浪费；模型犹豫的地方，展开成文字才便于人看。

再往外还有一道 visibility audit（可见性审计）兜底：假设把候选的潜空间段整个藏起来，剩下的可见版本还够不够做决策？不够就把那一段退回文本。

这套判据的意义在于它是训练时写进策略的，不是推理时外挂的一条规则。也就是说「哪些思考可以不给外人看」这件事，被编译进了模型的生成行为，而不是留给调用方用 prompt 去约束。

一种常见的误读，是把它讲成快思考与慢思考的双系统。论文和代码仓库里都没有这个提法，HybridSFT 学的是介质切换，不是认知分层。

---

## 数字要按口径读

回到开头那组数字。先把口径拆开，因为摘要把几个不同分母的数字放在了一起。

- **+10.4%** 是 RL 阶段相对同规模文本基线、潜空间基线的平均提升。同一篇论文里，SFT 阶段的对应数字是 18.5%，14B 相对最强 agentic 基线是 17.4%
- **35.5% 到 54.7%** 是生成侧文本 token 的减少量，这个数最实
- **1.8 到 2.6 倍** 是 H100 上的 wall-clock（墙钟时间），正文里给的均值是 2.1 倍
- **2.7 到 3.7 倍** 是纯估算：按每 H100 小时 2.50 美元、10% BF16 利用率折算生成算力，不含 prefill（预填充），不含训练，不含工具执行

分项数据能看出收益落在哪。Table 1 里，8B 的 GAIA 是 43.7 对 ARPO 基线的 38.8，14B 是 52.4 对 43.7；WebWalker 14B 是 49.5 对 40.5，8B 是 42.5 对 32.0。GAIA 上的差距从 4.9 个点拉到 8.7 个点，WebWalker 上 14B 差 9 个点，8B 差 10.5 个点。

但 HLE 是另一回事。HybridAgent 14B 拿 16.0，比自家基线 10.0 高不少，可 GPT-5.6-Luna 是 29.0，Kimi-K3 是 31.4。深度知识类任务上，前沿模型仍然领先一截。

论文的对比是跨训练预算的，模型规模也不对等，这组数字只能说明「小模型在检索和工具任务上追得很近」，不能说明「14B 追平了前沿」。还有一层选集口径：上面这组增益里最厚的两个基准是 GAIA 和 WebWalker，它们恰好是工具检索类任务，正是这套架构最对口的场景，换一类基准，差距未必还是这个量级。

成本那一条尤其要小心。35.5% 到 54.7% 的 token 减少是实打实的，但 2.7 到 3.7 倍是把减少量乘上一个假设的单价，换成缓存命中价、批量价，或者算上 prefill 和训练摊销，倍数就会变。训练侧的账同样没算：54K 条混合轨迹要靠 LLM 评委造出来，HybridRL 也要跑，论文的估算只覆盖生成阶段。这个区间适合当量级参考，不适合当采购依据。

---

## 「可检查」被验证到了什么程度

数字之外，潜空间推理最常被质疑的一点是黑箱。这篇论文在这件事上给的证据比摘要那句「directly inspectable」要具体得多。

机制本身很简单：每个潜空间步算出的 R(h_t)，在词表里找余弦最近的词嵌入，就得到一段可读的伪文本。它不需要额外训练一个解码器，用的就是退出判定那一步的同一个操作。

论文用两个指标衡量这段伪文本有没有意义（附录 F）：readability，即 R(h_t) 与原词嵌入的平均余弦相似度，跟高斯随机向量算出的噪声阈值比；context specificity，即伪文本与来源问题的 Jaccard 重叠，除以它与同任务其他问题的平均重叠。两个指标同时过线的区域才算有意义。

更硬的一组数据在 Table 7。他们让一个盲监控器只看可见文本，去预测整条 rollout（一次完整轨迹）是否正确。弱监控器 GPT-4o-mini 在 8B 和 14B 上的 AUROC（受试者工作特征曲线下面积）是 0.840 和 0.860，同任务上的纯文本 agent 是 0.772 和 0.818。

首个错误的定位率 98% 到 99%，诊断与参考解一致率 97% 到 98%。可见文本还更紧凑：8B 上是 302 个 token，纯文本 agent 是 596 个。

还有一组因果干预（Table 5）。把别的问题的潜空间段换进来，8B 的 MATH500 从 84.6 掉到 44.8；在段内打乱顺序，掉到 73.2；强制只走一步潜空间，掉到 72.2。这说明潜空间段里携带的是真在起作用的推理内容，不是可以随便替换的填充。

这组实验能推开「潜空间等于完全黑箱」这个说法，但它证明的是**可监控性**，不是**忠实性**。读出的是最近邻词嵌入，完整向量里被扔掉的那部分信息，读不出来。Hacker News 上最尖锐的一类批评指向的正是这一点：模型仍然在用你看不见的信息推理，你看到的是一份近似解释，不是一份还原。

对工程来说这两者的差别很实际。可监控性够用，因为你只需要判断这条轨迹靠不靠谱；忠实性不够用，因为一旦要追责「它为什么做了这个决定」，伪文本给不出因果链。

---

## 省下的 token，还给了推理栈

机制和数字都还站在论文这边，问题出在部署：这套东西依赖前缀复用与通用引擎，而连续向量输入两样都打掉了。

**先看 prefix cache。** 推理服务里最省钱的一招是前缀复用：同一个 system prompt、同一套工具定义，被成千上万个请求共享，这部分 KV 只算一次。它的前提是前缀能被一个稳定的 key 标识，通常是 token id 序列。

潜空间段把这个前提打掉了。连续向量注入时，框架要么给一段占位 token id，要么干脆造假 id；两种做法都会让「id 相同但内容不同」的请求撞在一起。

SGLang 的处理是直接拒绝：检测到 `input_embeds` 而 radix cache 还开着，就报错让你加 `--disable-radix-cache`。vLLM 开了 `--enable-prompt-embeds` 之后同样会关掉 prefix caching。

单请求内部还好，工作记忆本来就是往后追加 KV，不需要重新 prefill。被牺牲的是**跨请求的前缀复用**，而 Agent 服务恰恰最依赖这个。潜空间段一出现，同一套工具定义在请求之间的共享就没了。

**再看引擎。** 参考实现没有用任何 serving 框架，是手写的一个 lockstep（锁步）批量引擎：每步显式传 `input_embeds` 而不是 token id，手动管 `position_ids`、`attention_mask` 和 `cache_position`，空闲槽位永久 mask 掉。这套东西能跑，但它不是通用基础设施。

有人在 Hacker News 上说拿 llama.cpp 跑 14B 的 GGUF，卡在同一段话上循环了五分钟。这条后来被澄清是部署问题：不走官方的潜空间推理路径就跑不起来。仓库 README 说明模型目录里是骨干权重加独立的 HybridLink 权重，只有走官方加载路径才会拼上适配器，用 transformers 直接加载得到的只是普通文本模型。

**代码和论文还有一处对不上。** 论文 Eq. 5 说退出条件是余弦最近邻命中 `</latent>`，仓库 `engine.py` 里实际用的是 LM head 的 argmax。

issue 里有人做了受控对照（同一原版 prompt 下只改退出规则）：AIME25 上余弦退出是 68/480，LM head 退出是 34/480，差 7 个百分点。作者回复说两者在 tied embeddings 下等价，会补一句说明，但没有解释代码为什么和公式不一致。

**权重也只放了一半。** Hugging Face 上放了 `HybridAgent-8B-Agentic` 和 `HybridAgent-14B-Agentic` 两个 checkpoint，论文里数学和深推理的结果来自另一批没放出来的权重。有人拿 Agentic 版跑 MATH500，得到 74.8%，论文对应的数字是 84.6%。差 10 个点，原因是领域没对上。

仓库本身的完成度不低：MIT 协议，450 多个 star、50 多个 fork，两阶段训练脚本和数据都在，open issue 数量少，其中一条是长篇的可复现性报告，作者作了一条综合回复。但它是完整的研究代码，不是能直接接进生产推理栈的东西。

### 复现之前要对的三个地方

- **checkpoint 先对领域**。Agentic 和 deep-reasoning 是两批权重，拿错了 MATH500 上就是 74.8 对 84.6
- **工具得真的能用**。搜索不可用而 prompt 里又要求搜索时，回答会在 search cap 为 0 处被静默截断；缺 SciPy 会让依赖它的工具程序 import 失败。这两类问题都不会中止评测，只会让分数莫名低一截
- **预算里要有 prefill 这一项**。省下的是生成 token，多出来的是跨请求前缀没法复用

---

## 回到那个介质问题

Agent 的推理要不要写成文字，这篇论文给出的答案是：不必全写，但也不该全藏。

机制上它做到了两件事同时成立。潜空间段确实在承担推理（因果干预证明了这一点），文本段确实在承担对外接口和审计（工具调用、监控实验都落在这边）。这两件事过去被当成互斥的选项，现在被放进同一条生成序列里，这是论文真正的贡献。

但「省下的 token 还给了推理栈」也不是修辞。通用推理引擎跑不了，公式和代码还有两处对不上（归一化、退出规则），这些都不是可以靠发一个版本修掉的边角问题，它们来自「输入不再是离散 token」这个根本改动。

所以这篇论文现在的状态，是一个机制成立、数字好看、配套没跟上的研究原型。它证明了混合介质这条路走得通，也把这条路的账摆了出来：收益是省下的 token，支出是缓存和批处理要重做一遍。至于这笔支出什么时候能摊薄，取决于 serving 栈值不值得为连续向量输入做这个投入。

那是另一个工程问题，不是这篇论文能回答的。

*参考来源：*

- Hybrid Reasoning Agents，arXiv:2610.18861：[https://arxiv.org/abs/2610.18861](https://arxiv.org/abs/2610.18861)
- 论文 HTML 全文（Eq.1/4/5/6，§3.1–3.2，Table 1/2/5/6/7/9，Appendix A/D/F/H）：[https://arxiv.org/html/2610.18861v1](https://arxiv.org/html/2610.18861v1)
- 代码仓库 togethercomputer/HybridAgent：[https://github.com/togethercomputer/HybridAgent](https://github.com/togethercomputer/HybridAgent)
- 可复现性报告与退出规则对照（issue #6）：[https://github.com/togethercomputer/HybridAgent/issues/6](https://github.com/togethercomputer/HybridAgent/issues/6)
- 权重与数据集：[https://huggingface.co/collections/togethercomputer/hybridagent](https://huggingface.co/collections/togethercomputer/hybridagent)
- Hacker News 讨论（2026-10-18，520 分 / 239 评论）：[https://news.ycombinator.com/item?id=50145337](https://news.ycombinator.com/item?id=50145337)
- Coconut（Training Large Language Models to Reason in a Continuous Latent Space），arXiv:2412.06769：[https://arxiv.org/abs/2412.06769](https://arxiv.org/abs/2412.06769)
- Think before you speak: Training Language Models With Pause Tokens，arXiv:2310.02226：[https://arxiv.org/abs/2310.02226](https://arxiv.org/abs/2310.02226)
- CODI: Compressing Chain-of-Thought into Continuous Space via Self-Distillation，arXiv:2502.21074：[https://arxiv.org/abs/2502.21074](https://arxiv.org/abs/2502.21074)
- SGLang 关于 input_embeds 与 radix cache 的讨论：[https://github.com/sgl-project/sglang/discussions/34194](https://github.com/sgl-project/sglang/discussions/34194)
- vLLM prompt embeds 文档：[https://docs.vllm.ai/en/stable/features/prompt_embeds/](https://docs.vllm.ai/en/stable/features/prompt_embeds/)
