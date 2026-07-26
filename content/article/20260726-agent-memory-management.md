# 向量检索不是记忆：Agent 记忆的三层进化

> **导读**：给 Agent 接上向量数据库不等于它就有了记忆。真正的 Agent 持久化记忆系统是一个包含写入路径、维护策略和检索管线的完整子系统——它经历三个阶段：先把原始交互"存下来"（Storage），再学会"归纳和压缩"（Reflection），最终做到"从经验中自主学习"（Experience）。这篇文章展开每一层的核心原理、工程困境和关键代码实现。

2023 年 4 月，斯坦福和 Google 的论文《Generative Agents》（arXiv:2304.03442）让 25 个 AI 角色在一个虚拟小镇里活了起来——它们聊天、散步、策划派对。这篇论文的核心不是模型，而是一套叫"记忆流"（memory stream）的机制：每个 Agent 把自己看到、听到、想到的一切写成自然语言记录，然后按"相关性 × 时效 × 重要性"的三维分数在需要时检索。

三年过去，"Agent 记忆"已经从一个论文概念变成了一个有自己 benchmark 体系、按架构分化的框架生态和一个被量化的 benchmark-to-production 精度鸿沟的独立工程领域。

但一个根本性的混淆始终存在：很多人以为记忆就是检索。给 Agent 接上向量数据库，把对话历史 embed 进去，query 的时候拉回 top-k 相似片段——然后困惑地发现 Agent 还是记不住你是谁。

向量检索本质上还是 RAG，不是真正意义上的记忆。两者的区别不在技术，在生命周期——检索是单向的读操作，记忆有写入路径。

---

## CoALA：一张地图

用一个统一的概念框架来定位三层进化。2023 年普林斯顿团队提出的 CoALA（Cognitive Architectures for Language Agents，arXiv:2309.02427）是目前被引用最广的 Agent 认知架构论文。它将 Agent 记忆分为四种类型：

- **工作记忆**（working memory）：当前任务的临时草稿纸——子目标、中间计算结果、进行中的状态。存于上下文窗口，任务结束即丢弃。
- **情景记忆**（episodic memory）：带时间戳的事件记录——"上次用户问这个问题时，我给了这个答案，他说不对"。追加式日志，按相关性 + 时效检索。
- **语义记忆**（semantic memory）：去上下文化的事实——"用户住在杭州""团队的技术栈是 Python + PostgreSQL"。存于向量数据库或知识图谱，跨会话持久。
- **程序性记忆**（procedural memory）：怎么做的知识——技能、策略、工具使用模式。常驻于系统提示词、Agent 代码、微调权重中。

这四种记忆不是学术分类游戏。它们对应三种不同的存储介质、三种不同的生命周期和三种不同的检索策略。CoALA 的价值在于给后续一切工程方案提供了一张地图——你加的任何一个"记忆功能"，都能在这张地图上找到它属于哪个象限。而大多数"给 Agent 加了记忆"的实现，只碰了语义记忆这一种，忽略了其他三种。

---

## 1. Storage：为什么向量检索不是记忆

**一个写入路径包含三件事：提取、去重、冲突解决。** 三个环节，少了任何一个都会影响记忆质量。

以 Mem0 的生产架构（ECAI 2025, arXiv:2504.19413）为例。当用户说"我把后端从 Django 迁移到 FastAPI 了"，写入管线是这样的：

1. **提取**：LLM 从原始消息中提取结构化事实——`{"fact": "用户后端框架: FastAPI", "source": "message_42", "timestamp": "2026-07-20"}`。这不是简单的文本切片，而是一次语义级别的重写。
2. **去重与冲突检测**：新事实"FastAPI"与旧事实"Django"语义冲突。系统识别后不删除旧记录，而是将新记录标记为 `supersedes: old_record_id`。
3. **存储 + 嵌入**：事实本体存入结构化表，embedding 向量存入向量索引，两者通过 fact_id 关联。

**Supersedes 关系是记忆系统的一等公民。** 追加式存储（append-only）如果没有 superseeds，旧事实永远不会被"更正"，只会被"叠加"。当 Agent 同时检索到"用户后端是 Django"和"用户后端是 FastAPI"时，它需要自己判断哪个更新——而这恰好是 LLM 不擅长的事（它没有内置的时间推理能力）。

```python
from uuid import uuid4
from datetime import datetime, timezone

class MemoryStore:
    """带 supersedes 链条的简化记忆存储"""

    def __init__(self):
        self.facts: list[dict] = []  # 事实表
        # 注意：self.embeddings 仅作示意，生产中使用外部向量索引
        self.embeddings = []         # 向量索引（简化）

    def add(self, fact: str, source: str) -> str:
        """写入：冲突检测 → 生成 ID → 存储"""
        # 冲突检测：对同类事实做语义相似度匹配（stub: 实际使用 LLM）
        conflict = self._find_conflict(fact)
        fact_id = str(uuid4())
        self.facts.append({
            "id": fact_id,
            "fact": fact,
            "source": source,
            "supersedes": conflict["id"] if conflict else None,
            "timestamp": datetime.now(timezone.utc)
        })
        # 嵌入并存入向量索引（stub: 实际使用 embedding model）
        self.embeddings.append({"id": fact_id, "vec": self._embed(fact)})
        return fact_id

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """读取：混合检索 → supersedes 过滤 → 返回活跃事实"""
        # 第一步：多路检索（stub: 向量 + 关键词）
        vector_results = self._vector_search(query, top_k * 2)
        bm25_results = self._bm25_search(query, top_k * 2)
        # 第二步：RRF 融合（Reciprocal Rank Fusion, stub）
        merged = self._rrf_merge(vector_results, bm25_results)
        # 第三步：过滤被 supersede 的记录
        # 收集所有被其他记录指向的 ID（链式 supersedes 自动处理）
        superseded_ids = {f["supersedes"] for f in self.facts if f["supersedes"]}
        valid = [r for r in merged if r["id"] not in superseded_ids]
        return valid[:top_k]
```

即使旧事实的向量相似度高于新事实，检索结果也不会同时返回矛盾的两条。supersedes 链条在检索阶段就完成了"一致性过滤"——不需要 LLM 自己判断哪个版本更新。

**但纯向量检索很难做到精确匹配。** 当用户问"我的 API key 是什么"，向量相似度检索可能返回"API 配置相关"的一大堆内容，但漏掉包含实际 key 的那条记录。生产中常见的解决方案是双路检索：BM25（关键词匹配）+ 稠密向量（语义匹配），再用 RRF 或 cross-encoder 重排序。Elasticsearch Labs 用这套方案在生产环境跑出了 R@10 0.89 的召回率。

---

## 2. Reflection：OS 隐喻下的上下文管理

存下来是第一步。第二步是决定什么该留在上下文里、什么该移到长期存储——并且让 Agent 自己管理这件事。

MemGPT（arXiv:2310.08560，现已更名为 Letta）是这套思路的开创者。它把 LLM 的上下文窗口类比为操作系统的 RAM——容量有限，程序只能访问当前驻留在"内存"里的数据。需要时，操作系统把数据从"磁盘"分页到"内存"；不需要时，swap 出去。

翻译成 Agent 的语境：

> **主上下文（RAM）**：系统提示词 + 工作记忆 + 最近的对话历史（FIFO 队列）。容量 = 模型的 context window。
>
> **外部存储（Disk）**：归档记忆（Archival Memory，存于向量数据库，按语义检索）+ 回忆存储（Recall Storage，完整对话历史的可搜索存档）。

Agent 通过 **function calls 自主管理"分页"**——决定什么时候把当前上下文里的关键信息写入归档、什么时候从归档检索相关记忆回来。这个决策不是写死在代码里的"每 10 轮做一次摘要"，而是 Agent 在运行时自己判断的。

```python
class MemGPTAgent:
    """精简版 MemGPT 的记忆管理循环（一次只处理一个 tool call）"""

    def __init__(self, model, archival_store, max_context_tokens=4096):
        self.model = model
        self.archival = archival_store    # 归档记忆（向量数据库）
        self.recall: list[str] = []       # 回忆存储（完整对话记录）
        self.core_memory = {"persona": "", "human": ""}  # 核心记忆块
        self.max_tokens = max_context_tokens

    def step(self, user_message: str) -> str:
        """单步交互：组装上下文 → LLM 推理 → 解析 tool call → 返回"""
        context = self._assemble_context(user_message)
        response = self.model.chat(context, tools=[
            self._tool_archival_insert,   # 写入归档
            self._tool_archival_search,   # 检索归档
            self._tool_core_memory_edit,  # 编辑核心记忆
        ])
        # 解析 tool calls：本示例假定一次只触发一个 tool call
        for tool_call in response.tool_calls:
            if tool_call.name == "archival_insert":
                self.archival.insert(tool_call.args["content"])
            elif tool_call.name == "archival_search":
                results = self.archival.search(tool_call.args["query"])
                context = self._inject_results(context, results)
                # 重新推理（带检索结果，不再允许进一步 tool call）
                response = self.model.chat(context, tools=[])
                break  # 一次只处理一个 tool call
        return response.text

    def _assemble_context(self, user_msg: str) -> str:
        """组装上下文 = 系统指令 + 核心记忆 + 近期对话 + 用户消息"""
        tokens = self.max_tokens
        system = f"你是 {self.core_memory['persona']}。用户: {self.core_memory['human']}"
        tokens -= self._count(system)  # stub: 实际使用 tokenizer 计数
        # 从最近的 N 条对话中取，直到填满 token 预算的 70%
        # 预留 30% 给 user_msg 和模型输出
        history = []
        for msg in reversed(self.recall[-20:]):  # 20 为回顾轮数上限
            n = self._count(msg)
            if tokens - n < self.max_tokens * 0.3:
                break
            history.insert(0, msg)
            tokens -= n
        return "\n".join([system] + history + [user_msg])
```

这个架构的核心洞察是：**上下文窗口本质上是一块 Agent 主动管理的工作内存，而非单纯的读入通道。** 压缩不是被动的"窗口满了怎么办"，而是 Agent 决策循环的一部分——它决定留什么、存什么、什么时候该召回。

**但压缩有代价。** 2026 年 7 月的一篇综述（Colaco & Lahjouji, arXiv:2607.08032）将 Agent 记忆系统的所有压缩方案统一到了一个框架下：rate-distortion tradeoff。简单来说——压缩就是丢掉信息，丢多少信息换多少 token 节省，是一个不可调和的取舍。

可逆压缩（分页时保留原始副本、时序知识图谱的双时态追踪）保真度最高，但 token 节省有限。不可逆压缩（摘要式压缩、定期归并旧记忆）token 节省明显，但每次压缩丢 5-10% 细节，十轮后的累积漂移足以让 Agent 的行为约束偏离原始设定——"传话游戏"效应。

微软的 ACON（arXiv:2510.00615）用蒸馏策略取得了 26-54% 的 token 压缩，同时保留 95% 以上的任务性能。但它的前提是：压缩器本身是一个更强的模型，需要用教师模型的知识蒸馏训练——这恰恰说明压缩不是一个纯工程优化问题，它依赖模型本身的认知能力。

---

## 3. Experience：记忆的自主进化

前两层解决的是"怎么存"和"怎么管"。但 2026 年最活跃的前沿方向在第三层：让 Agent 自己学会怎么记忆。

ACL 2026 的 AgeMem（Agentic Memory, arXiv:2601.01885）把记忆操作抽象为 Agent 的工具调用——六种操作：ADD（写入长期记忆）、UPDATE（更新）、DELETE（删除）、RETRIEVE（检索）、SUMMARY（摘要）、FILTER（过滤）。关键是，它不是手工写规则决定什么时候用哪种操作，而是用三阶段渐进式 RL 训练：

1. **基础交互**：Agent 在简单对话中学习基本记忆操作的时机
2. **干扰过滤**：训练数据加入大量无关信息，Agent 学会区分"该记的"和"该忽略的"
3. **任务执行**：在需要跨会话记忆的长周期任务上优化决策

结果是，AgeMem 在 5 个长周期 benchmark 上超过了测试中所有手工规则的基线方案。

**但 RL 训练的记忆管理有一个隐含假设：Agent 可以犯错。** 在生产系统中，一条错误删除、一次错误覆盖的代价可能很高——用户偏好被清空、关键上下文被覆盖。

2026 年 3 月的 SSGM 框架（Stability- and Safety-Governed Memory, arXiv:2603.11768）正是针对这个问题：它把记忆分为可变轨道和不可变轨道，Agent 可以自由编辑可变轨道的内容（偏好、学习到的策略），但不可变轨道（系统约束、安全规则）只有验证过的更新才能写入。双轨设计不是阻止自主进化，而是给进化加了护栏。

Letta 在 2026 年 6 月发布的"Memory Models"走了另一条路：不是通过 RL 训练参数，而是通过 sleep-time compute 做持续学习。Agent 在空闲时段自己回顾对话日志、整合新知识、修改核心记忆块——不改变模型权重，只改变上下文。

这和 CoALA 的程序性记忆形成互补：前者在 token 空间做学习，后者在参数空间做学习。目前来看，token 空间的路径更安全、更可审计、也更可控。

---

## 生产数据：benchmark 到现实的距离

Benchmark 数字和现实生产环境之间存在差距。2026 年 5 月 RankSquire 的 Memory Fidelity Curve 给出了一条基于单一案例的拟合曲线（尚未独立验证）：

```
生产精度 ≈ Benchmark 分数 - (0.22 × 陈旧率) - (0.15 × log₁₀(实体数))
```

以 Mem0 v0.8.2 为例：LongMemEval benchmark 上 93.4 分，但在 RankSquire 的 50K 会话生产模拟中，有效精度降至 49.0%，44.4 个百分点的鸿沟。

这个差距主要来自三个因素：

- **实体膨胀**：一个用户 100 条记忆中，只有 20 条还"活跃"，其余 80 条是被 supersede 的旧版、过期偏好、一次性的上下文。向量检索无法自动区分。
- **时效衰减**：生产环境的写入频率远高于 benchmark。benchmark 假设每条记忆都被正确索引和更新，但生产中写入管线有延迟、有失败、有不完整的提取。
- **检索噪声**：向量检索在 1000 条记忆量级上表现良好，到 50K 条时"最近邻"开始混入语义相关但时序无关的内容。

**核心结论不是"这些系统不行"，而是"当前的 benchmark 测的与实际生产需要之间存在着结构性错位"。**

LoCoMo 和 LongMemEval 的评估方式（注入固定事实 → 固定间隔查询 → 统计精度）覆盖了记忆的"读取"面，但没有覆盖"写入"面的质量——提取准确率、冲突解决率、时间推理能力、遗忘合规性。MemoryArena（ICML 2026）和 MemBench 正在补这个缺口，但目前这些新 benchmark 还没有成为行业标准。

---

## 还没解决的问题

前文梳理了三层进化（Storage、Reflection、Experience），每一层都有明确的工程方案和学术基础。但三层串起来后，**压缩和检索之间存在结构性冲突**。

压缩要求你做摘要（用更少的 token 表达同样的信息）。但摘要本身是丢失精度的。当检索依赖的不是原始记录而是压缩后的摘要时，每次检索都在一个已经失真的空间里做搜索。然后新一轮写入又在上一轮检索的失真结果上做提取——这是两个 lossy 步骤的串联，误差会被放大而不是抵消。

MemGPT 用原始副本 + 摘要并存的方案部分缓解了这个问题——检索时用摘要做快速过滤，需要精确内容时回退到原始记录。但这意味着存储成本线性增长。生产系统迟早要面对"删不删"的问题。

而"删不删"的答案，目前看是"不删"。Abhishek Chauhan 在 2026 年的生产实践总结中提出 No-Delete Principle：情景记忆不做自动删除，只做压缩摘要；原始记录保留为审计源；只有用户显式请求删除时才硬删除。这本质上是把"要不要记住"的决策权从系统交还给用户——系统负责检索优化和存储管理，但不替用户删除。

这大概就是 Agent 记忆系统的现状：原理清晰了，工程方案有了，benchmark 也在追赶，但"什么是该记住的、什么是该忘掉的"这个问题，最终还是要人来做决定。

*参考来源：*

- CoALA 论文 — Sumers et al., "Cognitive Architectures for Language Agents" (arXiv:2309.02427, 2023)
- MemGPT 论文 — Packer et al., "MemGPT: Towards LLMs as Operating Systems" (arXiv:2310.08560, 2023)
- Generative Agents 论文 — Park et al., "Generative Agents: Interactive Simulacra of Human Behavior" (arXiv:2304.03442, 2023)
- Zep/Graphiti — "A Temporal Knowledge Graph Architecture for Agent Memory" (arXiv:2501.13956, 2025)
- AgeMem — "Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management" (arXiv:2601.01885, 2026)
- SSGM — "Governing Evolving Memory in LLM Agents" (arXiv:2603.11768, 2026)
- 压缩 rate-distortion 综述 — Colaco & Lahjouji, "What to Keep, What to Forget: A Rate–Distortion View of Memory Compaction" (arXiv:2607.08032, 2026)
- ACON — "Optimizing Context Compression for Long-horizon LLM Agents" (arXiv:2510.00615, 2025)
- 记忆综述 — "Memory in the Age of AI Agents" (arXiv:2512.13564, 2025)
- Mem0 — "Building Production-Ready AI Agents with Scalable Long-Term Memory" (arXiv:2504.19413, 2025)
- 生产架构 — Abhishek Chauhan, "Production Agent Memory: Compaction, Decay, and the Observation Engine" — [dev.to](https://dev.to/ac12644/production-agent-memory-compaction-decay-and-the-observation-engine) (2026)
- Benchmark-to-Production Gap — RankSquire Memory Fidelity Curve — [ranksquire.com](https://ranksquire.com/2026/05/06/long-term-memory-for-ai-agents) (May 2026)
- Elasticsearch Labs — "Agent Memory on Elasticsearch: Hybrid Retrieval and DLS" — [elastic.co](https://www.elastic.co/search-labs/blog/agent-memory-elasticsearch) (2026)
- Letta — https://docs.letta.com/
- Mem0 — https://docs.mem0.ai/
- LangChain Memory — https://docs.langchain.com/oss/python/concepts/memory