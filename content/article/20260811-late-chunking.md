# Late Chunking：颠倒切分与编码的顺序，解决 RAG 跨块上下文丢失难题

> 把文档先切成小块再逐一编码，是几乎所有 RAG 系统的默认操作。这个操作有一个内在缺陷：它会在切分的瞬间摧毁跨块的上下文。Jina AI 在 2024 年提出了一种叫 Late Chunking 的方法，只做了把切分和编码的顺序颠倒过来这一件事，检索精度就涨了。

---

2024 年 8 月，Jina AI 的研究员 Michael Günther 和 Han Xiao 发了一篇技术博客，标题一句话就说清了这件事：*Late Chunking in Long-Context Embedding Models*[^1]。随后他们又发布了正式论文[^3]和一篇更深的解读[^2]，把这个概念讲清楚了。

核心思想一句话就能说完：**先让 embedding 模型看完整个文档，再在 token 级别的向量上做切分**。名字里的 "late" 指的就是这个时间差——切分发生在编码之后。

这句话听起来简单，但背后依赖一个关键约束：**只有使用 mean pooling 的 embedding 模型才支持这种操作**。CLS pooling 和 max pooling 都不行。这不是工程上的偏好，是架构设计的必然。

---

## 一、一个例子看懂问题在哪

RAG 系统的标准流程是这样的：把一篇文档切成若干块，每块独立送入 embedding 模型生成向量，存进向量数据库。查询时，把用户问题也编码成向量，在数据库里找最相似的块，喂给 LLM 回答。

这个流程在处理短文本时没什么问题。但当文档变长，跨块的指代关系就开始搞破坏了。

论文里有个经典的例子。下面是维基百科 "Berlin" 词条的三个句子，被切成了三个独立的 chunk：

- Chunk 1: *Berlin is the capital and largest city of Germany, both by area and by population.*
- Chunk 2: *Its more than 3.85 million inhabitants make it the European Union's most populous city...*
- Chunk 3: *The city is also one of the states of Germany...*

Chunk 2 和 Chunk 3 都不包含 "Berlin" 这个词。它们用了 "Its" 和 "The city" 来指代。当我们用 "Berlin" 做查询向量时，看看传统分块和 Late Chunking 的余弦相似度对比[^3]：

| 文本 | 传统分块 | Late Chunking |
|------|---------|--------------|
| "Berlin is the capital..."（含 Berlin） | 0.8486 | 0.8495 |
| "**Its** more than 3.85 million..." | 0.7084 | **0.8249** |
| "**The city** is also one of..." | 0.7535 | **0.8498** |

Chunk 1 本身就有 "Berlin"，两个方法差不多。但 Chunk 2 和 Chunk 3（不含这个词）在传统分块下的相似度一路掉到 0.71 和 0.75——向量根本不知道 "Its" 指的是谁。Late Chunking 把这两句的相似度拉回到 0.82 和 0.85，几乎和 Chunk 1 持平。

**向量依然能"认出"这些句子在说柏林，因为模型在编码时已经看到了整段上下文。**

这个差异在实际 RAG 系统里的后果很直接：用户问 "柏林有多少人口"，传统分块系统可能找不到 Chunk 2（因为 "人口" 和 "Berlin" 不在同一个块里），Late Chunking 就能找到。

---

## 二、颠倒顺序，发生了什么

传统分块（论文里叫 naive chunking）的流程是线性的：

```
文本 → [按规则切成 N 块] → [逐块送入模型编码] → N 个独立的 chunk 向量
```

每一步都是串行的，每个 chunk 的编码过程看不到任何其他 chunk 的内容。第 k 个 chunk 的向量和第 k+1 个 chunk 的向量是独立同分布的——它们之间没有任何条件依赖关系。

Late Chunking 改了第二步和第三步的相对位置：

```
文本 → [整篇（或尽可能大的一段）送入 Transformer 编码] → [获得所有 token 的上下文向量] → [按 chunk 边界做 mean pooling] → N 个 chunk 向量
```

关键差别在于**分块发生在 token 级向量生成之后**。Transformer 的 self-attention 已经让每个 token 的表示融合了全文信息，这时再做分块，每个 chunk 的向量天然携带了完整上下文。

用公式来表达更清晰。设 Transformer 编码后第 j 个 token 的向量表示为 ϑⱼ。对于 token 跨度从 cue_start 到 cue_end 的第 i 个 chunk，它的 embedding eᵢ 是：

```
eᵢ = Σ(ϑⱼ) / (cue_end - cue_start + 1)  ， j ∈ [cue_start, cue_end]
```

这就是 mean pooling——只不过求和范围从"全文所有 token"缩小到了"属于该 chunk 的这些 token"。代码实现就是一行（[源码](https://github.com/jina-ai/late-chunking/blob/1d3bb02/chunked_pooling/__init__.py#L47)）：

```Python
pooled_embeddings = [
    embeddings[start:end].sum(dim=0) / (end - start)
    for start, end in annotations
    if (end - start) >= 1
]
```

这个实现只有约 30 行代码，不需要修改模型，不需要重新训练，不需要改动下游的检索 pipeline。它只是改变了 pooling 发生的时间点。

值得强调一个常被误解的点：Late Chunking 的上下文依赖是**双向的**。因为 embedding 模型用的是 encoder-only Transformer，它的 attention 矩阵是全连接的（不像 decoder 那样是因果 mask），所以每个 token 的表示同时受到前文和后文的影响。论文和博客里把这个性质形式化地写成了 vₖ ∼ Q(c₁, c₂, ..., cₙ)，而非 vₖ ∼ Q(cₖ | c₁, ..., cₖ₋₁)。这意味着即使切分边界不够精准，每个 chunk 的向量也已经被双向的全文信息"泡过"了。

这也是为什么 Late Chunking 对切分边界不敏感——论文的消融实验显示，固定 token 长度边界 + Late Chunking 的效果，和语义边界 + Late Chunking 几乎没有差别。

---

## 三、为什么只有 mean pooling 模型才能用

这是 Late Chunking 最核心的理论约束。

Embedding 模型的最后一步叫 **pooling**——把 Transformer 输出的 token 级向量序列压缩成一个文本级向量。主要有三种做法：

- **Mean Pooling**：所有 token 向量取算术平均。e = (1/m) · Σϑⱼ
- **CLS Pooling**：只取 `[CLS]` token 最后一个隐藏层的向量。e = ϑ_CLS
- **Max Pooling**：每个维度取所有 token 的最大值。e_d = max(ϑⱼ,d)

Late Chunking 要在 token 向量序列上**按 chunk 的 token 跨度做子集平均**。这个操作的数学本质是：对 token 序列的任意子集 S，mean(ϑ_S) 能否产生一个有意义的向量表示。

**Mean pooling 可以**，因为平均值运算具有线性可分性——∑(a) + ∑(b) = ∑(a+b)，子集的均值本身就是一个合法的、可解释的 embedding。这个性质来自于加法和除法的定义，不涉及任何非线性压缩。

**CLS pooling 不行**，因为 `[CLS]` 只有一个 token 位置。全文信息被压缩到了一个向量里，但这个压缩过程是非线性的——`[CLS]` 的向量 ≠ 各 token 向量的任何简单组合。你无法从这个单一向量中切出 chunk 1 的部分和 chunk 2 的部分。没有 token 级表示，就没有分段操作的可能。

**Max pooling 也不行**，因为 max 运算不具备可解性——max(a₁, ..., a₁₀) 不等于 max(a₁, ..., a₅) 加 max(a₆, ..., a₁₀)，差远了。更根本的问题在于，不同 chunk 里最突出的特征可能指向完全不同的语义方向，分别取 max 意味着每个 chunk 的向量可能代表了不同的东西。

Han Xiao 在博客里直接写了结论："Models using CLS or max pooling aren't compatible with late chunking."这篇博客的标题就是 *What Late Chunking Really Is & What It's Not*。

这也解释了为什么 Late Chunking 主要和 Jina 的模型绑定——不是技术锁定，而是 jina-embeddings-v2/v3 恰好同时满足两个条件：(1) 长上下文（8192 tokens）；(2) 默认使用 mean pooling。论文也验证了 nomic-embed-text-v1 同样可以支持，只要是 mean pooling + 长上下文的组合就行。

---

## 四、Benchmark 数据：提升多少，什么时候没有提升

论文在 BeIR 基准的五个数据集上做了测试，使用 jina-embeddings-v2-small-en 模型，固定 256 token 切分边界[^3]：

| 数据集 | 平均文档长度（字符） | 传统分块 nDCG@10 | Late Chunking nDCG@10 | 提升 |
|---|---|---|---|---|
| SciFact | 1498 | 64.20% | 66.10% | +1.90 |
| TRECCOVID | 1117 | 63.36% | 64.70% | +1.34 |
| FiQA2018 | 767 | 33.25% | 33.84% | +0.59 |
| NFCorpus | 1590 | 23.46% | 29.98% | +6.52 |
| Quora | 62 | 87.19% | 87.19% | 0.00 |

一个明显的规律：**文档越长，提升越大**。NFCorpus（1590 字符）的提升最大，达到 6.5 个点；Quora（62 字符）零提升——短文本不存在跨块依赖需要保留。

论文还做了模型组合实验，把不同模型 × 分块策略 × 边界策略交叉对比。jina-embeddings-v3 配合 Late Chunking 在测试的所有数据集上均领先。但有一个关键发现：**论文的实验里，没有出现使用 Late Chunking 的较弱模型超越不使用 Late Chunking 的较强模型的情况**。嵌入模型本身仍然是决定检索质量的最重要因素，Late Chunking 是乘数，不是替代。

论文也指出了这个方法的边界：在合成数据集（论文里的 Needle-8192 和 Passkey-8192，把短事实嵌入无关填充文本）上，使用大 chunk 时传统分块反而表现更好[^3]。因为当周围上下文与目标答案毫无关系时，全文编码反而把无关信息注入了 chunk 向量，稀释了目标信号。

这引出了超长文档的处理问题。

---

## 五、Long Late Chunking：当文档比上下文窗口还长

jina-embeddings-v2/v3 的上下文窗口是 8192 tokens（大约十页标准文本）。jina-embeddings-v4 原生支持 32K 上下文，但目前受 API 侧 GPU 资源限制，官方 Embedding API 仅支持最长 8K tokens 的输入，32K 需要通过自部署或云服务厂商的模型托管实现。无论哪种情况，不是所有文档都能塞进窗口。

论文提出的解决方案叫 **Long Late Chunking**（Algorithm 2）[^3]：

1. 将整篇文档分成若干个 "宏块"（macro chunks），每个宏块包含多个小 chunk
2. 相邻宏块之间有 ω 个 token 的重叠，作为补充上下文
3. 对每个宏块独立执行 Late Chunking
4. 拼接所有宏块的 token 级向量，按原始 chunk 边界重新做 mean pooling

核心思想很简单：用一个滑动窗口（带重叠）把超长文档拆成多个能喂进模型的大块，每个大块内部仍然使用 Late Chunking。重叠部分保证 chunk 不会因为恰好落在窗口边界而丢失上下文。

工程上，jina-embeddings-v3 的 API 已经内置了这个逻辑。本地实现的话，论文把宏块大小设为模型可处理的最大长度（上下文窗口上限），重叠 ω 是留给实现者调整的参数。

这里有一个权衡：重叠越大，上下文保留越好，但计算量也越大。论文没有系统性地扫描最优重叠值，实践中 256 token 是一个安全的起点。

---

## 六、工程落地：怎么用，踩什么坑

Late Chunking 的工程集成已经相当成熟。主流 RAG 框架都有了原生或半原生支持：

1. **Jina API 方式**（最简单）：在 API 调用中设置 `late_chunking=True`，传入一组字符串，API 会自动把它们拼接成 "全文"，编码后按原始输入边界返回 chunk embedding：

```Python
import requests
headers = {"Authorization": f"Bearer {API_KEY}"}
data = {
    "model": "jina-embeddings-v3",
    "input": ["Berlin is the capital...",
              "Its more than 3.85 million...",
              "The city is also one of..."],
    "late_chunking": True
}
response = requests.post(
    "https://api.jina.ai/v1/embeddings",
    json=data, headers=headers
)
# 返回 3 个 embedding，每个都包含了彼此之间的上下文信息
```

2. **LangChain**：通过 `langchain-jina` 包的 `LateChunkEmbeddings` 类[^4]。

3. **LlamaIndex**：`JinaEmbedding` 类原生支持 `late_chunking` 参数，直接嵌入到 `ServiceContext` 中使用。

4. **Chroma、Haystack、LightRAG**：均有对应的 `late_chunking` 参数或封装。

5. **本地部署**：下载 jina-embeddings-v3 模型（HuggingFace），获取全部 token 的 `last_hidden_state`，手动按 chunk 边界做 mean pooling。核心代码就是上面那行 `embeddings[start:end].sum(dim=0) / (end - start)`。

**踩坑清单**（来自论文、社区讨论和多个技术博客）：

- **别在短文档上用**：短文本（论文数据里平均 62 字符的 Quora 就是典型）没有可保留的跨块依赖，Late Chunking 零收益，反而增加 API 调用延迟
- **别用 CLS pooling 模型**：这是最常犯的错误。确认你的 embedding 模型默认使用 mean pooling（看模型卡的 pooling 参数）
- **存储成本不变**：Late Chunking 的输出向量数量和 naive chunking 一样（每块一个向量），不会像 ColBERT 那样存储爆炸
- **overlap 不必要**：论文附录明确说，Late Chunking 下 overlap 的 chunk 策略既不提升也不降低效果——上下文已经在编码阶段被保留了
- **推理成本显著增加**：传统分块可以并行处理多个短 chunk，Late Chunking 必须一次性编码整篇文档（注意力矩阵 O(n²)），延迟和 GPU 内存需求均显著上升
- **切换分块策略必须全量重建索引**：不能把 Late Chunking 生成的向量和 naive chunking 的向量放在同一个索引里混用
- **ColBERT 级细粒度的取舍**：ColBERT 在检索质量上仍有 5-12% 的系统性优势（独立基准显示 MRR 平均高出 8%、Recall@10 高出 12%），但存储成本约为 Late Chunking 的 500 倍（10 万文档约 2.5 TB vs 5 GB）。Late Chunking 是在质量与存储成本之间的实用折中，对绝大多数场景已足够

---

## 七、竞争对手：Voyage AI 的 context 模型

Late Chunking 在 2024 年发布后，主要竞争者来自 Voyage AI。

他们采取了不同的技术路线。Jina 的思路是 "用现有的 mean pooling 模型 + 改变编码和切分的顺序"，Voyage AI 的思路是 **"训练专门的上下文化嵌入模型，模型内部已经跟"全文上下文"做了联合表示"**。

Voyage AI 在 2025 年 7 月发布了 voyage-context-3[^5]，2026 年 6 月升级到 voyage-context-4[^6]。他们的自我报告数据显示，voyage-context-3 在 chunk 级检索上超越了 jina-embeddings-v3 的 Late Chunking 约 23.66%，超越 Anthropic Contextual Retrieval（用 LLM 为每个 chunk 生成上下文前缀）约 20.54%；在 document 级检索上分别超越约 6.76% 和 2.40%。

这个数字需要谨慎看待——它是供应商自己的基准测试结果，且 Late Chunking 论文发表于 2024 年 9 月，和 voyage-context-3 之间隔了近一年，不是一个模型代际的对比。更重要的是，两者的技术哲学不同：Late Chunking 是一个**方法**，可以应用于任何 mean pooling 模型；Voyage 的 context 系列是一个**模型**，上下文化能力是训练出来的，换模型就没了。

从工程选型的角度看：如果你已经用 Jina API，设一个 `late_chunking=True` 的成本几乎为零；如果你在选 embedding 供应商，voyage-context 在基准上确实领先，但自测数据需要独立验证。

---

## 八、Span Pooling：训练侧的进一步优化

虽然 Late Chunking 不需要额外训练，论文还是提出了一个专用微调方法——**span pooling**[^3]。

标准 embedding 训练是这样的：给一个查询 q 和一个文档 d，对 d 的所有 token 向量做 mean pooling，得到文档向量 y，用对比学习损失（InfoNCE）拉近 q 和 y 的距离。

Span pooling 的改动在于：训练数据里多了一个标注——文档中与查询相关的文本跨度 ⟨start, end⟩。训练时不对全文做 mean pooling，而是只对 ⟨start, end⟩ 范围内的 token 做。这意味着模型在训练阶段就开始学习 "在长文本中只关注相关片段"，和推理时的 Late Chunking 行为对齐。

论文在 TriviaQA 和 Fever 数据集上做了实验，使用 span pooling 微调后，配合 Late Chunking 的检索指标有进一步提升，但幅度不算大。论文作者也指出，训练数据主要来自 Wikipedia，缺乏领域多样性。如果未来在医学、法律、金融等专业语料上做 span pooling 训练，增益可能会更明显。

对于大多数工程场景，**Span pooling 是可选的优化层，不是必备项**。Late Chunking 开箱即用已经足够有效。

---

## 九、选型建议：什么时候该用，什么时候不该用

**强烈建议使用的场景：**

- 文档有密集的跨块指代（代词回指、"如上一节所述"、"前述"等），如法律合同、学术论文、技术手册
- 文档长度在 1000-8000 字符区间（Late Chunking 收益最显著的区间）
- 你已经在用 jina-embeddings-v3 API（设置一个参数的成本）
- 你想获得上下文保持效果但不想像 Anthropic Contextual Retrieval 那样为每次分块调一次 LLM

**不建议使用的场景：**

- 短文档：无可保留的跨块依赖
- Needle-in-Haystack 类检索（答案是一句话，埋在无关文本中）
- 同一文档内的 chunk 间区分任务：Late Chunking 会让同文档的 chunk 更相似，反而不利于内部分辨。这是 embedding 信息容量有限的必然结果——全局上下文注入越多，每个 chunk 的局部特征越被稀释
- 你用的是默认 BERT 类模型（CLS pooling）：不支持

**一个实用的路由策略**：按文档长度分流。超过 1000 字符的文档走 Late Chunking，短文档走普通分块。这在工程上很容易实现，成本也极低。

---

Late Chunking 做的事情本质上很简单：**不改变 chunk 的文本内容，只改变 chunk 向量包含的信息量**。它利用了 encoder-only Transformer 的基础特性（全注意力矩阵产生的上下文感知 token 向量），然后用最朴素的 mean pooling 把这种感知传递到每个 chunk。

论文作者自己写的一段话是最好的总结："Late chunking provides a more low-level, generic, and natural solution by leveraging the inherent mechanics of the encoder-only transformer."这句话的重点是 "inherent mechanics"——它不是在模型外面套一层工程 tricks，而是把模型本身已经有的能力用好。

对于一个零训练成本、不改 pipeline、30 行代码能实现的优化，它对长文档检索的改善是值得认真对待的。

---

*参考来源：*

[^1]: Günther, M., Xiao, H. "Late Chunking in Long-Context Embedding Models." Jina AI Blog, 2024-08-22. https://jina.ai/news/late-chunking-in-long-context-embedding-models
[^2]: Xiao, H. "What Late Chunking Really Is & What It's Not: Part II." Jina AI Blog, 2024-10-03. https://jina.ai/news/what-late-chunking-really-is-and-what-its-not-part-ii
[^3]: Günther, M., Mohr, I., Williams, D.J., Wang, B., Xiao, H. "Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models." arXiv:2409.04701, 2024. https://arxiv.org/abs/2409.04701
[^4]: langchain-jina. https://github.com/langchain-ai/langchain-jina
[^5]: Voyage AI. "voyage-context-3: Contextualized Chunk Embeddings." 2025-07-23. https://blog.voyageai.com/2025/07/23/voyage-context-3/
[^6]: Voyage AI. "voyage-context-4: Stop Worrying about Chunking." 2026-06-29. https://blog.voyageai.com/2026/06/29/voyage-context-4/
[^7]: 官方实现: jina-ai/late-chunking (GitHub). https://github.com/jina-ai/late-chunking
[^8]: Weaviate Blog. "Late Chunking: Balancing Precision and Cost in Long Context Retrieval." 2024-09-05. https://weaviate.io/blog/late-chunking
[^9]: DataCamp. "Late Chunking for RAG: Implementation With Jina AI." https://www.datacamp.com/tutorial/late-chunking
