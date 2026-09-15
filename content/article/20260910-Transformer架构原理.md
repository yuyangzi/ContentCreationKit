---
title: "从 RNN 到 Mamba：注意力、多头、位置编码各解决了什么问题"
date: 2026-09-10
topic: Transformer架构原理
mode: deep-tech
---

# 从 RNN 到 Mamba：注意力、多头、位置编码各解决了什么问题

> **导读**：2017 年，Google 团队用一篇论文改写了序列建模的主流方案。核心机制只有一个：让序列中每个位置直接关注所有其他位置，一步完成全局关联。这篇文章从零拆解 Transformer 的每个组件（注意力、多头、位置编码、前馈网络、归一化），讲清楚它们各自解决了什么问题，又如何在 2026 年的现代大模型里演进。

2017 年，Vaswani 等人在 "Attention Is All You Need"（arXiv:1706.03762）里写下了一个公式，随后它迅速成为大模型的基础骨架。

这个公式长这样：

```
Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V
```

看起来人畜无害。但它的含义是：序列里的每个元素，都可以直接跟序列里所有其他元素算一次相关性，然后按相关性加权提取信息。不需要像 RNN 那样一个字一个字地往后传，也不需要用 CNN 一层一层地扩大感受野。一步到位，全局可见。

这就是 Transformer 的全部核心。多头、位置编码、前馈网络、归一化，都是为了让这个核心机制能跑起来、跑得稳、跑得快。

## 为什么 RNN 不行了

2017 年之前，处理序列数据的主流方案是 RNN（循环神经网络）和它的改良版 LSTM。它们的工作方式是：把序列里的词一个一个喂进去，每一步更新一个隐状态，隐状态里装着"到目前为止看到了什么"。

这套机制有两个结构性问题。

第一个是串行计算。第 100 个词的表示依赖第 99 个词的隐状态，第 99 个又依赖第 98 个，整条链拆不开。GPU 上有上千个核心，但 RNN 每一步只能用一个，训练速度被序列长度卡死。

第二个是长距离依赖衰减。理论上 LSTM 靠门控机制缓解了梯度消失，但序列一长，早期词的信息在隐状态里仍会被不断稀释。一句话开头说了什么，到了结尾可能已经很难找回。

Transformer 的解法是把"一步一步传"变成"一眼看全"。每个词直接跟所有词算注意力，不管距离多远，计算路径都是一步。并行化和长距离依赖，同时得到极大缓解。

## 注意力机制：Q、K、V 三个矩阵在做什么

Scaled Dot-Product Attention（缩放点积注意力）的名字里每个词都有含义。Dot-Product 指 Q 和 K 算点积，Scaled 指除以 √d_k 做缩放。

Q（Query，查询）、K（Key，键）、V（Value，值）三个矩阵都是从同一个输入线性投影出来的，但用途不同。每个词发出一个 Query，去跟所有词的 Key 算相似度，得到一个注意力分数，再用这个分数对所有词的 Value 加权求和。

这像去图书馆找书（Query），每本书有个标签（Key），标签匹配度越高你越该借这本书，最后你实际带走的是书的内容（Value）。Q 和 K 负责"匹配"，V 负责"提取内容"。

公式里的 softmax 把分数归一化到 0 到 1 之间，保证权重总和为 1。除以 √d_k 是因为：当 d_k 比较大时，Q 和 K 的点积方差会变大，softmax 的输出会趋向 one-hot 分布（最大值接近 1，其余接近 0），梯度极小，学不动。除以 √d_k 让方差回到 1 左右，梯度保持健康。论文脚注 1 给了这个推导。

用 PyTorch 写出来，核心就四行：

```Python
import torch
import torch.nn.functional as F

def scaled_dot_product_attention(q, k, v, mask=None):
    # q, k, v 形状: (batch, heads, seq_len, head_dim)
    d_k = q.size(-1)
    scores = torch.matmul(q, k.transpose(-2, -1)) / (d_k ** 0.5)
    if mask is not None:
        scores = scores.masked_fill(mask == 0, float("-inf"))
    weights = F.softmax(scores, dim=-1)
    return torch.matmul(weights, v)
```

`mask` 参数不改变 Q、K、V 的值，只在 softmax 之前把非法位置的注意力分数设为负无穷，让这些位置的权重归零。Encoder 里不需要掩码（每个词可以看所有词），Decoder 里需要因果掩码（每个词只能看自己和之前的词）。掩码的细节在《GPT 和 BERT 的分野，藏在一张下三角矩阵里》里另有展开。

## 多头注意力：不是分工，是多个子空间

Multi-Head Attention（多头注意力）把 Q、K、V 拆成 h 份，每份独立算一次注意力，最后拼回来再做一次线性投影：

```
MultiHead(Q, K, V) = Concat(head₁, ..., headₕ) · W^O
```

每个头的维度是 d_model / h。原论文用 d_model = 512、h = 8，每头 64 维。

原论文说多头的好处是"让模型同时关注来自不同位置的不同表示子空间的信息"。这句话被无数转述引用，但实际含义比"一个头学语法、一个头学语义"这种说法微妙得多。

研究表明，多数注意力头高度冗余，测试时剪掉一部分对最终性能的影响很小（Michel et al., 2019）；但确实有一部分头表现出明确分工，承担了位置、句法等特定功能（Voita et al., 2019）。至于多头整体为什么有效，也有解释认为关键在于多路投影带来的训练稳定性，而不是严格的"一个头学语法、一个头学语义"式分工。可视化研究显示，有些头确实倾向于关注特定模式（比如相邻词或句法中心词），但这些模式是训练涌现出来的，不是设计出来的。

## 位置编码：给排列不变性装上顺序

自注意力有一个根本性的盲点：它是排列不变的。把输入序列的顺序打乱，输出的各个向量只是相应重排，内容完全不变。"猫吃鱼"和"鱼吃猫"在纯注意力眼里没有区别。

位置编码（Positional Encoding）就是给每个位置注入顺序信息的组件。原始 Transformer 用的是正弦位置编码：

```
PE(pos, 2i) = sin(pos / 10000^(2i/d_model))
PE(pos, 2i+1) = cos(pos / 10000^(2i/d_model))
```

位置编码向量和词嵌入向量直接相加，作为第一层的输入。正弦编码的好处是：它能表示相对位置关系（因为 PE(pos+k) 可以表示成 PE(pos) 的线性函数），并且理论上可以外推到比训练时更长的序列。

但 2026 年的主流大模型中已很少见到正弦编码。LLaMA、Qwen、Mistral 用的都是 RoPE（Rotary Position Embedding，旋转位置编码）。RoPE 的核心思想是：不把位置信息加在输入上，而是在计算 QKᵀ 时让 Q 和 K 携带位置信息——具体做法是用旋转矩阵把位置编码"拧"进 Q 和 K 的向量里。这样做的好处是注意力分数天然包含相对位置关系，对相对距离有平滑的衰减；但裸的 RoPE 同样受训练长度限制，需要配合 YaRN 或 NTK-aware scaling，才能把 4K 上下文训练的模型扩展到 128K 甚至更长。

位置编码的演进还没结束。ALiBi（Attention with Linear Biases）走另一条路：不加位置嵌入，直接在注意力分数上加一个跟距离成正比的负偏置，离得越远分数越低。BLOOM 和 MPT 用了这个方案。它的优势是实现简单、零样本长度外推表现好；不过后来的主流模型多转向 RoPE，再用插值技术补足外推。

## 前馈网络：模型里真正的"知识仓库"

每个 Transformer 层里，除了注意力子层，还有一个 FFN（Feed-Forward Network，前馈网络）。它的结构是两层全连接加一个非线性激活函数：

```
FFN(x) = activation(xW₁ + b₁) · W₂ + b₂
```

W₁ 把维度从 d_model 放大到 d_ff（通常是 4 倍），W₂ 再缩小回 d_model。

这个子层看起来平平无奇，但它占了模型总参数量的约 2/3。注意力子层负责"建立关联"，FFN 负责"存储和提取知识"。一个被广泛接受的解释是：FFN 的每一行 W₁ 可以看作一个"键"，对应的 W₂ 列是"值"，FFN 的工作机制类似于一个 key-value 记忆网络，把预训练时学到的知识以模式匹配的方式存进去（Geva et al., 2021）。

激活函数也有过几次迭代。原始 Transformer 用 ReLU，后来 GELU 成为主流（BERT、GPT-2），到了 LLaMA 时代 SwiGLU 取代了 GELU。SwiGLU 的公式是 `SwiGLU(x) = (xW₁ ⊗ SiLU(xW₃))W₂`，其中 SiLU(xW₃) 作为门控，对 xW₁ 逐元素加权。实验表明 SwiGLU 在大多数任务上优于 GELU（Shazeer, 2020）。在隐藏维相同的情况下它多出一个矩阵，参数量约增加 50%；实践中通常把 d_ff 缩小到约 2/3 来抵消这部分开销。

## LayerNorm 和残差连接：让深层网络能训练

Transformer 原论文用的是 Post-LN：先算子层输出，再做残差连接，最后 LayerNorm。

```
output = LayerNorm(x + SubLayer(x))
```

但 Post-LN 在训练深层 Transformer 时容易不稳定——梯度要么爆炸要么消失，对学习率、warmup 策略非常敏感。后来的研究发现 Pre-LN（先 LayerNorm 再算子层）训练更稳定，代价是最终性能略差一点（Xiong et al., 2020）。LLaMA、GPT-3 之后的模型基本都用 Pre-LN。

LayerNorm（层归一化）和 BatchNorm（批归一化）的区别在于统计量的计算方式。BatchNorm 在一个 batch 的每个特征上算均值和方差，依赖 batch size，在 NLP 任务里序列长度不一、batch 统计量波动大，效果不稳定。LayerNorm 在一个样本的所有特征上算均值和方差，跟 batch 无关，更适合变长序列。

到了 LLaMA 时代，LayerNorm 又被 RMSNorm（Root Mean Square Layer Normalization）替代。RMSNorm 去掉了均值中心化，只保留均方根缩放，计算更快，实验表明效果相当（Zhang & Sennrich, 2019）。

残差连接（Residual Connection）本身不是 Transformer 的发明，但它对深层架构至关重要。没有残差连接，深层网络会因梯度在反向传播中逐层衰减而明显退化，底层很难学到东西。残差连接让梯度可以直接"跳过"子层传到浅层，是深层网络能训练的前提。

## 拼起来：完整的 Encoder-Decoder

把所有组件拼起来，一个完整的 Transformer 层是这样工作的。

**Encoder 层**：输入 → 多头自注意力 → 残差 + LayerNorm → FFN → 残差 + LayerNorm → 输出。每个位置的词都能 attend 到所有位置，信息双向流动。

**Decoder 层**：比 Encoder 多了一个 Cross-Attention（交叉注意力）子层。Decoder 的 Q 来自上一层的输出，K 和 V 来自 Encoder 的输出。这让 Decoder 在生成每个词时，能直接查看 Encoder 的整个输入序列。

**Encoder 和 Decoder 的配合**：Encoder 把输入序列编码成一组连续的表示，Decoder 在生成输出时，通过 Cross-Attention 去"查"Encoder 的表示，同时通过 Masked Self-Attention 保证自回归性质（第 i 个位置的预测只能依赖前 i-1 个词）。

这就是 2017 年论文里描述的标准 Encoder-Decoder 架构，最初为机器翻译设计。后来的演化中，两条路线从这座桥上分了出去：BERT 只用 Encoder（双向注意力，擅长理解任务），GPT 只用 Decoder（因果注意力，擅长生成任务）。但 Encoder-Decoder 本身并没有消失——T5、BART、UL2 都是纯 Encoder-Decoder 架构，在多语言翻译、文本摘要这些需要"理解+生成"的任务上仍然是一类经典选择。

## 2026 年的 Transformer 长什么样

LLaMA-3 到 Llama 4、Qwen-2.5 到 Qwen3 的模型卡仍然自称"Transformer"，但每个组件都跟 2017 年的原始版本不太一样了。

- 注意力从 MHA（Multi-Head Attention）变成 GQA（Grouped-Query Attention）：把 Query 头分组，每组共享一组 K 和 V 头，是 MQA（所有 Q 头共享一组 KV）和 MHA（每个 Q 头都有独立的 K、V 头）之间的折中。KV Cache 的显存占用大幅减少，推理速度提升，性能损失很小。
- 位置编码从正弦换成 RoPE，激活函数从 ReLU 换成 SwiGLU，归一化从 LayerNorm 换成 RMSNorm，前面已分别展开。
- FFN 维度比不再是固定的 4 倍：LLaMA-3 用约 3.5 倍，Qwen2.5 反而加宽到约 5.3 倍。

这些改动大多不是理论推导的产物，更多来自实验筛选。Transformer 的架构演进更多是"筛选"出来的，而不是一次性"设计"出来的——社区试了各种组合，跑 benchmark，留下效果最好的。

还有一个方向是混合架构，2024 年以来它从论文走向产品，成为最受关注的替代路线之一。Jamba、Bamba、Nemotron-H 这些模型用 Mamba（一种 State Space Model，状态空间模型）替换了大部分注意力层，只保留约 1/8 到 1/12 的注意力层。Mamba 的计算复杂度是线性的（O(N)），不像注意力是平方的（O(N²)），在长序列上效率优势明显。Mamba 自身也在迭代：Mamba-2 给出了它与注意力之间的结构化对偶，2026 年的 Mamba-3 进一步补强状态跟踪与检索。但 Mamba 在 in-context learning（上下文学习）和精确信息检索上仍不如注意力，所以混合架构是目前最务实的方案。

## 回到那个公式

开头那个公式 `Attention(Q, K, V) = softmax(QKᵀ / √d_k) · V`，做的事情其实很简单：用 Q 和 K 的相似度做权重，对 V 做加权平均。每个词的输出变成了所有词的加权和，权重由相似度决定。

这个简单机制的后果是深远的。它让并行计算成为可能，让长距离依赖不再是问题，让模型可以扩展到上千亿参数。但它也带来了 O(N²) 的计算复杂度和 O(N) 的 KV Cache 显存占用——这两个问题至今仍然是 Transformer 架构最核心的工程挑战，也是 Mamba 这些新架构试图解决的出发点。

Transformer 不是终点。但在 2026 年的今天，它仍然是大多数大模型的基础骨架。理解它的每个组件怎么工作，是理解后续所有架构演进的前提。

*参考来源：*

- Attention Is All You Need（Vaswani et al., 2017）：[arXiv:1706.03762](https://arxiv.org/abs/1706.03762)
- The Illustrated Transformer（Jay Alammar, 2018）：[jalammar.github.io/illustrated-transformer](https://jalammar.github.io/illustrated-transformer)
- RoPE（Rotary Position Embedding, Su et al., 2021）：[arXiv:2104.09864](https://arxiv.org/abs/2104.09864)
- YaRN: Efficient Context Window Extension of Large Language Models（Peng et al., 2023）：[arXiv:2309.00071](https://arxiv.org/abs/2309.00071)
- ALiBi（Attention with Linear Biases, Press et al., 2021）：[arXiv:2108.12409](https://arxiv.org/abs/2108.12409)
- GQA（Grouped-Query Attention, Ainslie et al., 2023）：[arXiv:2305.13245](https://arxiv.org/abs/2305.13245)
- GLU Variants Improve Transformer（Shazeer, 2020）：[arXiv:2002.05202](https://arxiv.org/abs/2002.05202)
- Analyzing Multi-Head Self-Attention（Voita et al., 2019）：[arXiv:1905.09418](https://arxiv.org/abs/1905.09418)
- Are Sixteen Heads Really Better than One?（Michel et al., 2019）：[arXiv:1905.10650](https://arxiv.org/abs/1905.10650)
- Transformer Feed-Forward Layers Are Key-Value Memories（Geva et al., 2021）：[arXiv:2012.14913](https://arxiv.org/abs/2012.14913)
- On Layer Normalization in the Transformer Architecture（Xiong et al., 2020）：[arXiv:2002.04745](https://arxiv.org/abs/2002.04745)
- Root Mean Square Layer Normalization（Zhang & Sennrich, 2019）：[arXiv:1910.07467](https://arxiv.org/abs/1910.07467)
- Mamba: Linear-Time Sequence Modeling（Gu & Dao, 2023）：[arXiv:2312.00752](https://arxiv.org/abs/2312.00752)
- Transformers are SSMs（Dao & Gu, 2024）：[arXiv:2405.21060](https://arxiv.org/abs/2405.21060)
- Mamba-3（Lahoti et al., 2026）：[arXiv:2603.15569](https://arxiv.org/abs/2603.15569)
- The Rise of Hybrid LLMs（AI21 Labs）：[ai21.com/blog/rise-of-hybrid-llms](https://www.ai21.com/blog/rise-of-hybrid-llms)
- Introducing Meta Llama 3（Meta, 2024）：[ai.meta.com/blog/meta-llama-3](https://ai.meta.com/blog/meta-llama-3/)
- Sebastian Raschka, Recent Developments in LLM Architectures: KV Sharing, mHC, and Compressed Attention（2026.5）：[magazine.sebastianraschka.com/p/recent-developments-in-llm-architectures](https://magazine.sebastianraschka.com/p/recent-developments-in-llm-architectures)
