# 一块 GPU 装不下一个长对话：PagedAttention 和前缀缓存是怎么省下 KV cache 的

> **导读**：32K 上下文下，Llama-3-8B 的 KV cache 占用 4 GB 显存，已经接近模型权重的四分之一；如果上下文拉到 128K，这个数字直接追平权重本身。问题不止"大"，vLLM 论文测出来，主流推理框架的 KV cache 实际利用率只有 20.4% 到 38.2%。这篇文章跟走一个推理请求在 GPU 显存里的完整生命周期，看 vLLM 是怎么用 PagedAttention 和前缀缓存，把这块被严重浪费的显存一寸寸收回来。

---

## 一、请求进来：显存里多了一张账本

假设用户发了一条 1024 token 的 prompt 给一个在线大模型服务。

服务接到请求后的第一件事，是把这 1024 个 token 一次性送进 GPU。GPU 跑一遍 transformer 的 prefill 阶段，并行算出所有 token 的 Key 矩阵和 Value 矩阵，存起来。这两份矩阵是后续每一步生成都要回头查的"账本"，整个对话期间都不会被销毁。

到这里为止，显存里多出了两块东西：1024 行历史的 K 矩阵，和 1024 行历史的 V 矩阵。显存占用由这条公式决定：

```Python
bytes = 2 × L × h_kv × d × s × p
```

L 是层数，h_kv 是 KV 头数（MQA：Multi-Query Attention；GQA：Grouped Query Attention，Llama-3 用 GQA，这个数会比注意力头数小），d 是每个头的维度，s 是当前序列长度，p 是精度（FP16 时是 2 字节）。前面的 2 是因为 K 和 V 各占一份。

拿 Llama-3-8B 举例：32 层、8 个 KV 头、head_dim 128、FP16 精度。32K 上下文时，KV cache 占用 4,294,967,296 字节，刚好 4 GB。128K 上下文下是 16 GB，和模型权重本身打平。

换句话说，**一次长对话的 KV cache 占用，已经接近模型权重的体量**。多轮对话、检索增强生成、agent 循环调用模型，这些场景下显存压力主要不是来自模型本身，而是来自这条持续增长的账本。

KV cache 是 attention 机制的必然代价。每次 decode 一个新 token 的时候，模型都要回头问一次：这一轮的 query 和前面所有 token 的 key 之间的相似度是多少？这本质上是一个 attention 计算，需要把新 token 的 query 跟全部历史的 key 都点乘一遍。没有历史的 key，新 token 就不知道该往哪个方向走。

所以 KV cache 做的事情，是把"每生成一步都要重算历史的 K/V 矩阵"这个 O(n) 的额外计算，转化成了"每步多读一段显存"的 O(n) 额外访存。用 FLOPs 算，无 KV cache 时第 t 步要重算 t 个历史 token 的 K/V 再做 attention，单步 O(t²)，n 步加起来 O(n³)。有 KV cache 时是 prefill O(n²) + decode 阶段每步 O(n) × n 步 = O(n²)。KV cache 不是省了计算量，而是用显存换 FLOPs。

> 顺着这个推论，decoder 阶段 GPU 算力通常不紧张，单步计算量小，但每步都要从显存里把 K/V 矩阵全部读一遍给 GPU 用。这其实是 memory-bound，不是 compute-bound。KV cache 越占显存，每次 decode 反而越被访存拖累。

## 二、第一个请求完成之后：连续分配为什么浪费

prefill 结束，decode 阶段开始。每生成一个 token，账本就多一行，KV cache 在显存里稳步增长，直到对话结束。

表面上这没什么问题。但实际跑起来，主流框架的 KV cache 显存利用率只有 20.4% 到 38.2%。

以 FasterTransformer、Orca 这类经典框架为例，它们按请求的"最大可能序列长度"预分配连续内存块。提前留好空间，免得中途不够。问题出在三个地方：

1. **预留浪费**：一个请求的最大可能长度是 2048 token，但实际只生成 50 个 token 就停了。剩下的 1998 个 token 的显存就空在那里。
2. **内部碎片**：不同请求的输入输出长度方差极大，论文里给的数据是 ShareGPT 上请求长度从几十到几千不等，混在一起分配，块和块之间的空隙没法填满。
3. **外部碎片**：用 buddy allocator 这种经典分配策略，2048 和 1025 两种大小的块会留下不可用的空洞。

更麻烦的是，beam search 和 parallel sampling 这两种解码算法天然共享前缀，比如 beam search 里多个候选序列共用同一段 prompt。连续分配下，每个候选都要单独保留一份完整的 K/V 副本，共享根本做不了。vLLM 论文里给了一组数据：在 ShareGPT 数据集上，parallel sampling 内存能省 16.2% 到 30.5%，beam search 能省 44.3% 到 66.3%，前提是有合适的共享机制。

这就是为什么需要换思路。

## 三、PagedAttention：把显存切成页

2023 年，UC Berkeley 的 Kwon 等人发表了 vLLM 论文，提出 PagedAttention。他们借鉴的是操作系统里虚拟内存的思路。

操作系统课上有过这个例子：每个进程的逻辑地址是连续的，但物理内存里可以任意摆放，由 page table 维护映射，缺页时再从磁盘换入。PagedAttention 把这个套路搬到了 KV cache 上：

- **page（页） → KV block**
- **page table（页表） → block table**
- **TLB（Translation Lookaside Buffer）→ block cache（GPU kernel 内缓存）**
- **进程 → 一次推理请求**
- **fork 时的 copy-on-write → beam search 共享同一组物理 block，谁要写就复制一份再写**

把 KV cache 切成固定大小的 block（vLLM 默认 16 个 token 一个 block），每个 block 独立分配在物理显存里的任意位置。每个请求维护一张 block table，记录"第几个逻辑 block 映射到哪块物理 block"。逻辑顺序由 block table 维护，物理位置可以分散。

回到之前的 50 token 请求。它需要 4 个 block（16 × 4 = 64），最后一个 block 只填了 2 个 token，还有 14 个 token 的空位。**浪费被限制在了一个 block 内部**：在这个例子里，利用率是 50/64 ≈ 78%，而在传统连续分配下只有 50/2048 ≈ 2.4%。

论文里给的数据更直接：vLLM 比 FasterTransformer 在 ShareGPT 上吞吐最高 22 倍，比 Orca（Max 预留基线）高 2.7 到 8 倍，长序列场景优势更明显。代价是 PagedAttention 的 attention kernel 本身比 FasterTransformer 的连续版本慢 20-26%，因为 block 不连续，访存模式更散；短序列、小并发场景下，这个代价会吃掉部分吞吐优势。但端到端对比下，显存利用率上去了，能并发的请求数大幅增加，整体吞吐仍然胜出。

beam search 的共享问题也顺手解决了。多个候选序列的 block table 可以指向同一组物理 block，谁要修改这块数据（追加新 token），谁就触发 copy-on-write，把共享的那份复制一份再写。

到这一步为止，第一个请求在 GPU 显存里的旅程基本走完了。prefill 阶段申请 block、decode 阶段往 block 里追加、对话结束释放 block。

接着是第二个请求。

## 四、第二个请求进来：前缀缓存

多轮对话的第二次请求，prompt 通常长这样：

```
[system prompt: 几百 token 的指令]
[历史对话: 上一轮 500 token]
[用户本轮问题: 几十 token]
```

一个朴素的做法是再 prefill 一次，把这 700 多 token 全部重新算一遍 K/V 矩阵。但这 700 多 token 里，system prompt 和历史对话的部分在上一轮已经算过 K/V 矩阵了。重算是浪费。

前缀缓存就是来解决这个问题的：把历史的 K/V 矩阵留下来，碰到相同的前缀直接复用。

vLLM 的实现是 hash-based。每个 block 用"前缀 token + 当前 block 内的 token"算一个 hash 值，作为这个 block 的唯一标识。请求进来时，系统从前往后逐 block 查 hash，能查到就复用，查不到再 prefill。这套机制在 vLLM 里叫 Automatic Prefix Caching，开启方式很简单：

```Python
from vllm import LLM

llm = LLM(model="...", enable_prefix_caching=True)
```

vLLM v1 之后默认开启，hash 计算开销显著降低。

vLLM 论文里给了一组数据：一个 341 token 的 few-shot 前缀，启用 prefix cache 后吞吐达到原来 Orca（Oracle 上界基线）的 3.58 倍。

还有一种更细的方案是 SGLang 的 RadixAttention。它用 radix tree（基数树）来组织前缀缓存，树的边可以携带可变长度的 token 序列，能在更细的粒度上匹配最长公共前缀。和 vLLM 的 block 粒度 hash 表相比，radix tree 粒度更细，命中率可能更高。SGLang 论文里给的数据是 RadixAttention 配合 cache-aware 调度，整体吞吐最高 6.4 倍，延迟最多降低 3.7 倍。

两种方案的核心差异：**vLLM 是 block 粒度的 hash 表，SGLang 是 token 粒度的 radix 树**。前者实现简单，匹配速度快；后者粒度细，理论命中率更高，但树操作引入工程复杂度代价。生产上选哪个，取决于请求的多样性和工程上的取舍。

需要看到的是，前缀缓存本身不是免费午餐。hash 冲突概率极低但理论上存在，模型权重更新后旧缓存会全部失效，前缀缓存占用的显存本身要参与全局调度、挤压新请求空间。淘汰策略上，vLLM 按 block 粒度驱逐，SGLang 按 radix 子树驱逐，这是两种方案在工程取舍上的另一个分水岭。

到这里，KV cache 这条主线基本讲完。一个请求进来、算账、记账，第二个请求进来、查账。PagedAttention 解决了"账本怎么放得不浪费"，前缀缓存解决了"账本怎么不被重复算"。

## 五、这条路还在往哪走

PagedAttention 和前缀缓存是 2023 年的工作。之后的几年里，KV cache 的故事沿着三条线索继续展开。

**第一条线索是压缩。** KIVI 这篇工作发现，Key 矩阵的数值在通道维度上分布不均，Value 矩阵的数值在 token 维度上分布不均，所以可以用非对称的 2-bit 量化：Key 按通道量化、Value 按 token 量化。在不微调模型的前提下，峰值内存（含模型权重）压缩 2.6 倍，吞吐提升 2.35-3.47 倍。更激进的 KVQuant 把 KV 压到 3-bit，困惑度退化不到 0.1，让 LLaMA-7B 在单张 A100-80GB 上能跑 1M token 的上下文。

**第二条线索是分离式推理。** prefill 阶段和 decode 阶段的计算特征完全不同：prefill 是 compute-bound（计算密集），decode 是 memory-bound（访存密集）。把它们放在同一张卡上互相干扰，效率不高。Moonshot AI 的 Mooncake 架构把 prefill 和 decode 部署到不同节点，KV 缓存通过高速网络在节点之间流转，把 Kimi 实际处理的请求量提升 75%。

**第三条线索是架构级革新。** 2026 年发布的 DeepSeek V4 在注意力机制本身上动手：引入 CSA（Compressed Sparse Attention），先把每 m 个 token 的 KV 压缩成一条，再做稀疏检索；引入 HCA（Heavily Compressed Attention）做更激进的压缩。结果是 1M 上下文下，KV cache 压到 V3.2 架构的约 1/10，V4-Pro 的单 token 推理 FLOPs 降到 V3.2 的 27%。

压缩让单位 KV 占用更小，分离式推理让不同阶段的资源各得其所，架构革新让注意力本身的计算模式更高效。三条线索同时推进，KV cache 才从 2023 年那个"挤爆显存的麻烦"，变成 2026 年推理优化的主战场。

## 六、回到那个请求

文章开头的那个 4 GB 的账本，现在有了完整的解释。

它一开始是 prefill 阶段算出来的、用来给 decode 阶段每步查询的 K/V 矩阵。然后在第一个请求的生命周期里，它按 PagedAttention 的方式被切成 16 token 一块、塞进 block table 维护的物理显存里。等到第二个请求进来，system prompt 和历史对话的那部分被 hash 命中，账本的相应部分直接被复用。最后，如果服务器同时跑太多请求，LRU（Least Recently Used）策略会把最久没被命中的 block 淘汰掉，腾出空间给新请求。

KV cache 一直是那个 KV cache，但它的形态可以被分页、被共享、被压缩、被换出。围绕它展开的工程创新，让一个 GPU 集群能同时服务的并发长对话数量大幅提升。

这套打法的内核，是把 GPU 显存当成一种"可以被分页、被共享、被压缩、被换出"的可调度资源。当 KV cache 还只是模型推理的副产物时，它是被动消耗；当它被当作一等公民来设计时，它就成了整个推理系统调度优化的支点。

至于下一个 4 GB 会被怎么安排，是更多 block、更细粒度的 radix 树、更低的 bit 精度，还是更激进的注意力稀疏化。这是 2026 年各推理框架还在竞速的方向。

---

*参考来源：*
- Kwon et al. *Efficient Memory Management for Large Language Model Serving with PagedAttention*. SOSP 2023. https://arxiv.org/abs/2309.06180
- Zheng et al. *SGLang: Efficient Execution of Structured Language Model Programs*. 2023. https://arxiv.org/abs/2312.07104
- Liu et al. *KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache*. 2024. https://arxiv.org/abs/2402.02750
- Hooper et al. *KVQuant: Towards 10 Million Context Length LLM Inference via KV Cache Quantization*. 2024. https://arxiv.org/abs/2401.18079
- Moonshot AI. *Mooncake: A KVCache-centric Disaggregated Architecture for LLM Serving*. 2024. https://arxiv.org/abs/2407.00079
- DeepSeek-AI. *DeepSeek-V4: Towards Highly Efficient Million-Token Context Intelligence*. 2026. https://arxiv.org/abs/2606.19348
- vLLM Automatic Prefix Caching 官方文档. https://docs.vllm.ai/en/latest/features/automatic_prefix_caching
- Llama 3 模型配置. https://huggingface.co/meta-llama/Meta-Llama-3-8B
