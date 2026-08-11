# Agent 的上下文，一座会自己生长的山

> 操作系统的虚拟内存是一个存在了半个世纪的概念：物理内存有限，但应用程序看到的是"无限"的地址空间。数据在 RAM 和磁盘之间来回搬运，需要时调入，用完后换出。LLM 的上下文窗口（Context Window）正在成为同样的稀缺资源，而且它有一个操作系统没有的麻烦——它自己会生长。

一台服务器跑数据库，内存占用大致是可预测的。但一个 Agent 在长任务中运行，每轮思考、每次工具调用、每一个返回结果，都会变成新的 token 堆积在上下文窗口里。Agent 跑得越久，上下文越臃肿，推理越慢，成本越高，质量越差。跑得足够久，Agent 终会撞上上下文窗口的上限——要么崩溃，要么被迫遗忘最早的信息。

这就是为什么上下文管理正在成为 Agent 工程中最核心的基础设施问题。2025 年到 2026 年，行业主流实践完成了一次共识转向：从"把上下文窗口做大"到"把上下文当成需要预算管理的稀缺资源"。这场转向的起点，是一篇把操作系统虚拟内存思想搬进 LLM 的论文。

---

## 为什么上下文窗口是一座会生长的山

LLM 的推理机制决定了，上下文窗口不只是一个"能塞多少东西"的容量问题。它背后有三层硬约束。

**第一层是计算的平方律。** Transformer 的自注意力机制，计算量和显存占用随序列长度平方增长。这意味着每增加一倍上下文，计算成本不是翻倍，而是四倍。论文 "Lost in the Middle"（arXiv 2307.03172）在 2023 年就发现了一个更棘手的问题：模型不是均匀地使用整段上下文，而是呈现 U 形曲线——开头和结尾的信息记得住，中间的大段内容得分断崖式下降。GPT-3.5-Turbo 在把答案藏在上下文中间位置的测试中，表现反而低于完全不看上下文的闭卷基线。上下文不是越大越好用，填太满反而会让模型"失焦"。

**第二层是 KV Cache（键值缓存）的内存墙。** 推理时，每个 token 的 Key 和 Value 矩阵都被缓存在 GPU 显存中，序列越长，缓存越大。vLLM 团队的测量数据（arXiv 2309.06180）显示：13B 参数的模型处理单条序列时，KV Cache 就要占用约 1.6GB 显存，而现有系统中约 60% 到 80% 的缓存空间被碎片浪费掉了。这还只是单次推理。Agent 每跑一轮循环，整段历史都要重新送进模型，KV Cache 的成本在每轮之间线性叠加。

**还有位置编码的天花板。** RoPE（旋转位置编码，arXiv 2104.09864）内置了一个"远距离衰减"先验：token 之间的距离越远，注意力权重越低。这个衰减不是 bug，而是旋转编码固有的结构属性——它天然地更关注近处的东西（ALiBi，arXiv 2108.12409，则直接把这种偏好做成了线性的注意力偏置）。这意味着即使把上下文窗口扩张到 1M token，模型仍然倾向于聚焦最后几页，而"山顶"上的早期信息，大概率被埋在了注意力权重的谷底。

这三层约束叠加，形成了一组根本性的张力：Agent 需要历史信息来保持连贯性，但上下文窗口不仅有限，而且当你把它填得太满时，模型的信息检索效率往往会下降。

---

## Agent 循环：加速堆叠的雪球

"一个 prompt 进去一个回答出来"的场景里，上下文只是线性增长。一旦 LLM 进入 Agent 循环（思考→工具调用→结果回填→再思考），上下文窗口的膨胀速度就不再是线性的。

Anthropic 在 2025 年 6 月的工程博客里给了一个数据：Agent 场景的 token 消耗大约是普通聊天的 4 倍，多 Agent 系统则达到 15 倍（Anthropic, 2025.06）。因为每一轮不仅是用户输入和模型回复在堆积，还有三块额外的开销：

- 工具定义的固定开销（50 多个 MCP tool 仅定义就要吃掉约 7 万 token，Anthropic 观测到的最坏情况超过 13 万，Anthropic, 2025.11）
- 工具返回结果的持续累积
- extended thinking token（推理过程自 Claude 3.7 起就留在上下文里）

MemGPT 论文（arXiv 2310.08560）用一个更精确的直觉描述了这个问题：上下文窗口里每一条消息都在排队，新消息从队尾进来，旧消息从队头被挤出去。本质上是 FIFO 队列——最早的信息死得最快。但 Agent 的长任务偏偏需要"最早的决策"和"中间的关键转折"同时在线。

比如一个深度研究 Agent 在分析一篇 200 页的论文：它先读摘要形成假设，然后跳去读方法论验证，再切回来修正假设。等它翻了 30 轮之后，最初的假设已经被埋在那座"上下文山"的底部。继续堆还是开始忘，Agent 得自己做这个决定。

---

## 把操作系统搬进上下文：MemGPT 的分页实验

2023 年的 MemGPT 论文做了一个当时看来颇为激进的设计：让 LLM 模仿操作系统管理虚拟内存的方式来管理自己的上下文。

核心思路很简洁。传统 OS 有物理内存（RAM）和磁盘（Disk），通过分页机制（Paging）在两者之间搬运数据，给应用程序一个"内存无限大"的假象。MemGPT 把上下文窗口当作物理内存，把外部向量数据库当作磁盘，给 LLM 配备了一套 function calling 工具，让它自己决定什么数据该留在窗口里，什么该换出去。

具体来说，MemGPT 把上下文拆成三个区域：

- **系统指令区**（只读）：Agent 的身份定义和行为约束
- **工作上下文区**（可读写）：当前任务的关键事实和状态
- **FIFO 消息队列**：对话历史，按时间排列

当消息队列的 token 数达到上下文窗口的 70%，系统注入一条"内存压力警告"，提示模型：快满了，有什么重要的赶紧存。达到 100% 时，强制触发一次"队列冲刷"——把大约一半窗口的内容逐出窗口，生成一段递归摘要（基于旧摘要 + 新被逐出的消息），然后把被逐出的原始消息存入外部召回存储（Recall Storage）。需要时，模型可以通过 `conversation_search` 工具检索回来。

这个设计的妙处在于：压缩（摘要）和存储（原始数据）是分离的。摘要是索引，原始消息是资产，摘要丢了可以从原始数据重建，但反过来不行。MemGPT 在文档分析任务上能处理远超底层模型上下文窗口限制的长文本，在对话 Agent 上让模型在数十轮交互后仍然记得用户的偏好和关键事实。

Letta（MemGPT 的工程化延续，2024 年 9 月更名后独立运营）把这个设计进一步产品化了。它把上下文窗口拆解为更细粒度的记忆块（Memory Block）：每个人格块、人类块、知识块有独立的标签、大小限制和权限。创建一个带记忆的 Agent 只需要几行代码：

```python
from letta_client import Letta, CreateBlock

client = Letta(base_url="http://localhost:8283")
agent = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        CreateBlock(label="human", value="用户叫 Sarah，偏好简洁回答。"),
        CreateBlock(label="persona", value="技术写作助手，擅长用类比解释复杂概念。"),
        CreateBlock(label="knowledge", value="项目使用 React + TypeScript 技术栈。"),
    ],
)
```

每个 block 有独立的大小限制，值可以被 Agent 通过 `memory_replace` 等工具自主编辑，也可以由背景 Agent（Sleep-time Agent）在空闲期更新——就像操作系统的后台进程在你不用电脑时整理磁盘碎片。

Letta 在生产环境中还引入了一个细节：不同模型的上下文压缩触发阈值不一样。GPT-5 系列因为 output token 限制严格，在上下文窗口的 90% 就主动触发压缩；其他模型等到 100% 才动手。

---

## 能用的五种策略，和它们各自要付的代价

MemGPT/Letta 的 OS 模型提供了一个统一的理论框架，但实际工程中并不总是需要（或者能承担）这么完整的方案。Machine Learning Mastery 在 2026 年的一篇文章总结了五种经过实战验证的策略，每种对应不同的场景和代价（Machine Learning Mastery, 2026.06）。

**滑动窗口（Sliding Window）。** 只保留最近 N 条消息，更早的直接丢弃。实现极简，零额外 LLM 调用，延迟零增长。代价是"数字失忆"：Agent 一小时后遇到的问题一小时前刚解决过，但已经彻底忘了。适合短期任务——客服对话、单次代码调试。不适合任何需要跨时间窗口保持状态的场景。

**递归摘要（Recursive Summarization）。** 定期调用 LLM 把旧消息压缩为一段摘要，替换掉原始对话。可以保留"剧情线"（任务的大方向和关键决策不会丢），但细节损失类似 JPEG 压缩：你知道这张图里大概有个人，但看不出表情。进阶做法是分层摘要：每 5 条消息做详细摘要，每 25 条做中等摘要，每 100 条做高层概览，形成一个摘要金字塔。成本比滑动窗口高（每次摘要是一次 LLM 调用），但长程连贯性好得多。

**结构化状态管理（Structured State Management）。** 完全放弃原始对话历史，用一个 JSON 对象跟踪目标、已完成事项、当前约束、已知事实。每次推理只传系统指令 + 当前 JSON + 最新用户输入。这是 token 效率最高的方案，但严重依赖预定义 schema 的完备性。一旦出现 schema 没覆盖的意外变量（比如 Agent 在第五轮发现了一个边缘情况，但这个发现不属于"目标/约束/事实"中的任何一类），它就被静默丢弃了。

**RAG 式外挂上下文（Ephemeral Context via RAG）。** 把历史全部存进向量数据库，每轮推理前用当前问题去检索最相关的 Top-K 片段拼回上下文。理论上可以支持无限长的对话。问题是"检索盲点"：两段看似不相关的历史，恰好共同构成某个结论的前提——向量相似度检测不到这种跨距离的逻辑关联。Agent 可能"记得"所有原始数据，但在需要连接两个散落信息的时候，检索动作本身就是瓶颈。

**动态上下文路由（Dynamic Context Routing）。** 日常任务用便宜小模型 + 小上下文窗口跑；遇到异常（比如同一任务连续失败 3 次），把完整原始历史转给大上下文强力模型做全局分析，返回精简指令。成本友好，但"什么时候该切"的判断逻辑维护起来相当痛苦——有时看起来像卡住了其实还在努力，有时看起来在推进其实在绕圈。

现实中的生产系统很少只用一种。最常见的组合是：滑动窗口保证即时响应，递归摘要保留中期脉络，向量库或图数据库存长期结构化事实。三种策略更多是互补堆叠，而非非此即彼的竞争。

---

## 2025-2026：上下文工程取代提示词工程

如果说 2023 年是"把 LLM 变成 Agent"的实验期，2025 年到 2026 年发生了一件更底层的事：行业对上下文管理的理解，从"写个好 prompt"迁移到了"设计一整套信息环境"。

Anthropic 在 2025 年 9 月的博客 "Effective context engineering for AI agents" 里正式命名了这个概念。核心观点用一句话概括：上下文不只包含你精心撰写的系统提示，还包括工具的 schema、文件内容、历史消息、MCP server 的描述、中间测试结果——这些全部挤在同一个窗口里。上下文工程要回答的问题不是"怎么写 prompt"，而是"在这些东西里，什么该放在窗口里，什么该交给代码处理，什么该外存到别处"。

这个观点很快被行业广泛接受。AI 工程师 Philipp Schmid（原 HuggingFace，后加入 Google DeepMind）甚至说过一句被反复引用的判断："大多数 Agent 失败已经不是模型失败，而是上下文失败。"（Schmid, 2025.06）OpenAI 在 2025 年 9 月到 2026 年间陆续发了三篇 cookbook，分别讲会话级上下文管理（Trimming + Summarizing）、长期个性化状态，以及 compaction + memory 的组合架构。Anthropic 在 Claude 上落地了三件具体工具：context editing（自动清除过期的工具调用结果，只留占位符）、memory tool（文件式外部记忆读写）、server-side compaction（服务端自动压缩，返回一个封装好的 compaction item，开发者不需要理解内部结构，原样塞回去就行）。

Anthropic 在 2025 年的内部评估里给出了两个数字：memory tool + context editing 的组合让 agentic search 任务性能提升 39%；在另一项 100 轮 web search 评测中，单独使用 context editing 让 token 消耗减少 84%（Anthropic context management blog, 2025.09）。这不是一个微调版本号的改进，而是重新定义了"上下文里该放什么"带来的质变。

从更大的视角看，上下文工程不是一个技术点，而是一种新的基础设施层。它连接了 prompt、memory、retrieval、tool use、session state，决定了 Agent 在长程运行中的认知上限。就像数据库的查询优化器决定了 SQL 能跑多快，上下文工程决定了 Agent 能想多远。

---

## 跨会话：一座山搬走了，下一座山还会长

前面讨论的都是单次会话内的上下文管理。但 Agent 不可能永远不关——会话结束，上下文窗口归零。下一次启动，Agent 是失忆的。

这就是长期记忆（Long-term Memory）要解决的问题。单会话内的上下文压缩和跨会话的记忆持久化是两根不同的技术支柱。前者关注"怎么在窗口满的时候优雅地搬东西"，后者关注"怎么让搬出去的东西以后还能找回来"。

目前工业界的主流方案不是"压缩后丢弃"，而是"提取后存储"。

mem0 是这条线上最活跃的开源框架（约 6 万 stars，2025 年 10 月完成 2400 万美元融资，Seed 与 A 轮合计，mem0.ai, 2025.10）。它的做法不是压缩历史消息，而是从对话中提取结构化的记忆事实（用户偏好、关键决策、项目背景），存入向量数据库和图数据库，需要时通过语义相似度 + BM25 关键词 + 实体匹配三条检索路径并行召回。写入策略是"只增不改"（Single-pass ADD-only）：每次只追加新事实，不覆盖旧记录。这听起来保守，但在生产环境中反而是安全的。比起让记忆系统自己决定"旧版本该覆盖还是该合并"，只增不改意味着永远可以回溯到原始记录。

LangMem（LangChain 的记忆 SDK）走了类似的路线，但更强调"热路径写入 + 冷路径整理"：Agent 在交互的实时路径上快速记录关键事实（create_manage_memory_tool），后台异步进程负责去重、合并、泛化旧记忆。这种分离让记忆写入不影响 Agent 的响应延迟。

还有一类思路是"文件即记忆"。Claude Code 维护一个持久的 CLAUDE.md 文件，记录项目上下文和用户偏好，每次会话启动时重新读入、重建状态。OpenAI 的 Agents SDK 也提供了类似的 snapshot/rehydration 机制——把 Agent 的运行时状态序列化，下个 session 加载回来继续跑。

这三类方案（结构化提取、冷热分离、文件快照）的共性在于：它们不再试图让上下文窗口"记住一切"，而是承认窗口是有限的，信息应该分层——最近的信息在上下文里，重要的信息在结构化存储里，完整历史在原始日志里。需要的时候，按需检索、按需重建。

---

## 几条能用的原则

如果从上面这些学术论文、开源框架、厂商实践里提取出几条能直接用的工程原则，大概是这些：

**不要把上下文窗口看作存储，把它看作工作台。** 上下文窗口里的每一段信息都应该对当前的推理决策有直接贡献。历史归档、参考资料、中间产物——放在外面，用的时候再拿。就像你不会把所有图纸铺在工作台上，只铺当前正在用的那一张。

**三分法处理每一轮的新信息。** 本轮产生的数据，按三类分别处理：关键决策和约束更新到结构化状态（JSON scratchpad 或 Memory Block）；有用但不紧急的提取为记忆事实（存入 mem0 / LangMem）；工具返回的原始大块数据，保留引用（文件路径或 UUID），正文只留前几行的预览。

**压缩是索引，不是仓库。** 递归摘要的价值不在于"取代原始数据"，而在于提供一个快速索引——Agent 通过摘要知道自己大致经历了什么，需要细节时去检索原始记录。把摘要当成唯一的历史真相，是摘要漂移（summarization drift）的根源。每次压缩都在丢弃细节，三轮之后摘要里的内容可能跟实际发生的事情已经不太像了。

**预算硬切分，不要让上下文自然生长。** 给系统指令、工具定义、对话历史、检索知识各分配固定 token 预算（常见初始分配：系统指令 10%-15%、工具定义 15%-20%、检索知识 30%-40%、对话历史 20%-30%）。当某个区域超预算时，触发对应策略去压缩，而不是让它继续膨胀。掘金上有一篇讲上下文工程的文章（AI Agent 上下文工程：记忆分层与 Token 预算管理，2026.06）写道："上下文的每一个字节都应该是编排层放进去的，不是自然累积的。"

**忘掉"上下文窗口越大越好"。** 1M token 的窗口能用，但大多数时候不该全灌满。Lost in the Middle 的 U 形曲线至少当前还没有被解决——模型对窗口中间位置信息的利用率，在超过 64K token 之后就开始明显下降。有更大的窗口意味着你有更大的容错空间，但并不意味着你可以不做管理。

---

## 三个常踩的坑

第一个坑是**把摘要当唯一历史记录**。递归摘要每一轮都在前一轮摘要的基础上叠加新的压缩。如果你把原始消息全丢了、只保留最新的摘要文本，三轮之后整个 Agent 的"记忆"就只剩一层模糊的薄雾。需要细节的时候没处回溯，需要对比旧版本决策的时候不知道当初为什么那么选。摘要和原始数据必须共存，摘要用来导航，原始数据用来验证。

第二个坑是**把向量检索等同于记忆检索**。两者的适用场景有本质区别。向量检索适合"跟这段想法类似的东西还有哪些"，但用户问"上周三我让你做了什么事"，这不是语义相似度问题，是时序定位问题。纯向量库在这个场景下拿不到答案。所以越来越多的记忆系统开始在向量检索之上叠加 BM25 关键词匹配、实体链接、时间范围过滤——三条路径并行，结果再融合（RRF）。

第三个坑是**以为上下文腐烂（Context Rot）不会发生在自己身上**。Chroma 研究团队在 2025 年发表的研究把这个问题命名为 context rot，Anthropic 的工程博客随后专门讨论：上下文窗口越长，模型准确回忆起早期信息的能力越差。它不是幻觉，也不是模型变傻了，而是注意力预算的物理限制。

2026 年的 ACL 和 arXiv 上开始出现专门研究 context rot 的论文：ACL 2026 Findings 收录了 ARC 主动反射式上下文管理框架，GAIR-NLP 则发表了系统诊断研究（arXiv 2606.29718），把"上下文越长，模型越容易提前放弃或给出不确定回答"的现象系统化。而更早的 NoLiMa 论文（arXiv 2502.05167, ICML 2025）给出了量化的基线：测试的 13 个主流模型中，11 个在 32K token 时就跌破了自身短上下文基线的一半，GPT-4o 从 99.3% 掉到 69.7%。这不是某一个模型的短板，至少当前主流注意力架构在长上下文场景下都存在这种结构性退化。

---

这个领域在过去两年发生了一件事：越来越多的工程团队开始接受，上下文窗口不是一个可以无脑膨胀的资源。更大不等于更好，能管理才等于能用。

MemGPT 把虚拟内存搬进 LLM 的时候，这个类比也许只是论文里的一句漂亮话。但到了 2026 年，整个行业的工程实践正在让这个类比越来越像真实的架构。上下文窗口是 RAM，Memory Block 是内存页，召回存储是硬盘，背景 Agent 是后台进程。LLM 不需要一个无限大的脑子，它需要一个操作系统的记忆管理模块。

*参考来源：*

- MemGPT: arXiv 2310.08560 (Packer et al., 2023)
- Lost in the Middle: arXiv 2307.03172 (Liu et al., 2023)
- ARC 框架 / ACL 2026 Findings: "Active and Reflection-driven Context Management" (Yao et al., 2026)
- PagedAttention / KV Cache: arXiv 2309.06180 (Kwon et al., 2023)
- RoPE: arXiv 2104.09864 (Su et al., 2021)
- ALiBi: arXiv 2108.12409 (Press et al., 2021)
- NoLiMa: arXiv 2502.05167 (ICML 2025)
- Anthropic, "Effective context engineering for AI agents" (2025.09): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- Anthropic, "How we built our multi-agent research system" (2025.06，4x/15x token 消耗数据): https://www.anthropic.com/engineering/multi-agent-research-system
- Anthropic, "Introducing advanced tool use on the Claude Developer Platform" (工具定义 token 开销): https://www.anthropic.com/engineering/advanced-tool-use
- Anthropic, "Managing context on the Claude Developer Platform" (2025.09): https://claude.com/blog/context-management
- Chroma, "Context Rot" 研究报告 (2025.07，术语命名): https://research.trychroma.com/context-rot
- GAIR-NLP, "Diagnosing and Mitigating Context Rot in Long-horizon Search" (arXiv 2606.29718, 2026.06)
- OpenAI, "Context Engineering - Short-Term Memory Management with Sessions" cookbook (2025.09): https://developers.openai.com/cookbook/examples/agents_sdk/session_memory
- OpenAI, "Context Engineering for Personalization" cookbook (2026.01): https://developers.openai.com/cookbook/examples/agents_sdk/context_personalization
- OpenAI, "Building Reliable Agents with Memory and Compaction" cookbook (2026.05): https://developers.openai.com/cookbook/examples/agents_sdk/building_reliable_agents_memory_compaction
- Letta, "Anatomy of a Context Window: A Guide to Context Engineering" (2025.07): https://www.letta.com/blog/guide-to-context-engineering
- Letta, "Memory Blocks: The Key to Agentic Context Management" (2025.05): https://www.letta.com/blog/memory-blocks
- Machine Learning Mastery, "Context Window Management for Long-Running Agents" (2026.06): https://machinelearningmastery.com/context-window-management-for-long-running-agents-strategies-and-tradeoffs
- AI Master, "AI Agent 记忆工程" (2026.06): https://www.ai-master.cc/article/agent-075
- 掘金, "AI Agent 上下文工程：记忆分层与 Token 预算管理" (2026.06): https://juejin.cn/post/7649740616415854627
- LLM 上下文压缩策略全景对比 (2026.05): https://notes.tsukino.dev/10-LLM基础/2026-05-15-llm-context-compression-strategies
- 阿里云开发者社区, "AI Agent 记忆系统" (2026): https://developer.aliyun.com/article/1710635
- AWS, "Agentic AI 基础设施实践经验：Agent 记忆模块" (2025.09): https://aws.amazon.com/cn/blogs/china/agentic-ai-infrastructure-deep-practice-experience-thinking-series-three-best-practices-for-agent-memory-module/
