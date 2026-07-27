---
mode: deep-tech
---

# 旧概念还是新范式？Agent 框架集体"图化"背后的矛盾与必然

> **导读**：几乎在同一时间，大多数主流Agent框架（LangGraph、Microsoft Agent Framework、Dify、Coze Studio）都在底层把自己变成了图执行引擎。为什么整个行业不约而同地选了同一个方向？本文从CS理论溯源和运行时机制两个维度切入，探讨"可控性"如何驱动Agent架构从while循环、状态机、DAG一路演进到有环图，以及这背后一种新的编程思维（Graph原生）是否正在成形。

Dex Mareno在2026年7月1日的一篇行业观察里写得很直白——Every AI Agent Framework Became a Graph in 2026（dreaming.press，2026-07-01）。LangGraph的StateGraph用了有环图，Microsoft Agent Framework发布了graph-based Workflow API（v1.0，2026-04），连Rust实现的GraphBit也在用类型化DAG做引擎治理编排。这些团队之间没有开会商量过。他们同时发现了同一个问题：Agent的行为已经复杂到无法用"先A后B再C"的链式思维描述了。

说Graph是旧概念的，在CS理论层面没错；说Graph是新范式的，在工程层面也没错。矛盾不在结论，在观察的层面不一样。

但这两个视角之间的差异，值得拆开来看。

---

## while循环的尴尬：当LLM的输出不受控制

先从最原始的形式——while循环——说起。

任何一个Agent框架的起点都是一个while循环。六行代码的事——调LLM，拿到tool_call就执行，把结果塞回消息列表，再来一轮。LLM觉得够了，返回文字，循环结束。

从裸循环到memory-aware再到operations内外分离，这是Loop结构的三层成熟度进化。但这三层进化留下了一个没展开的问题：从Loop到Graph的这一步，到底发生了什么？

while循环的表面问题是"简单"。但深层问题是，**它在控制层面什么也没有提供**。

LLM的输出是不确定的。同样的prompt，同样的上下文，模型可能这次决定调A工具，下次决定调B工具。对于Demo来说这是灵活性，对于生产环境来说这是不可审计性。你不知道Agent为什么走了这条路而不是那条路，你只能看结果——结果对了就好，结果错了你连从哪开始排查都不知道。

用计算机科学的语言说：while循环的执行图（execution graph）是一个在运行时动态展开的、缺少结构约束的树。每一步都可能分叉到任意方向，而你对分叉逻辑没有任何形式化的控制手段。Prompt engineering是唯一的控制机制，而prompt engineering本质上是自然语言层面的启发式——它不可证明，不可验证，不可组合。

这不仅仅是工程上的不优雅。Wei在2026年的论文"From Agent Loops to Structured Graphs"（arXiv:2604.11378）中从调度器理论角度提出了一套形式化框架（scheduler-theoretic framework）：Agent Loop和Graph Harness是调度器设计的两个维度——ready-set cardinality（就绪集基数，每次调度时有多少候选动作）和policy explicitness（策略显式度，调度逻辑在多大程度上是显式声明的）。裸while循环在policy explicitness维度上趋近于零。

换句话说，**while循环把"接下来做什么"这个最关键的决定，主要交给了LLM的黑箱推理**。你在控制层面的存在感，约等于零。

---

## 状态机：第一次把控制权抢回来

状态机是对while循环的第一次结构化改造。

状态机比裸while循环多做了一件关键的事：**预定义了合法的状态转移路径**。

在while循环里，Agent可以从"思考"跳到"调工具A"，也可以跳到"调工具B"，甚至可以跳到"回答用户"——没有规则限制，完全由LLM决定。状态机说不行：从状态S1，你只能去S2或S3，其他路径不合法。如果LLM的输出落到了不合法的路径上，框架可以在运行时拦截。

这就是"控制权回抢"的第一步。人的控制不再是纯靠prompt engineering的"说服"，而是在结构层面设置"路障"。

但状态机有一个致命的局限：状态爆炸。agentic tasks的语义状态空间太大了，手工枚举所有合法状态转移路径的成本非线性增长。你写一个能处理三种工具、五种错误类型的Agent，手工定义的状态转移图可能就有几十个节点和上百条边。再加一种工具，复杂度不是线性增加的。

这就是为什么纯状态机方案在Agent框架中没有成为主流。它给了控制，但以牺牲表达力为代价。从编程思维的角度看，它仍然是**指令式**的——你作为开发者，需要显式地描述每一步的可能走向。

---

## DAG：声明式的入场

DAG（Directed Acyclic Graph，有向无环图）解决了状态机的表达能力瓶颈，同时保留了结构化的控制。

DAG的核心洞察是：大多数Agent任务的执行路径天然就是无环的。你收集信息→分析信息→做决策→生成输出。中间可能有并发分支（同时查两个数据源），但最终汇聚到一个决策点。这种拓扑结构用DAG表达，既自然，又在数学上好验证。

DAG在"控制权"上的升级体现在两个层面。

第一，**拓扑可验证**。DAG有一个数学上优雅的属性：你可以静态检测环路。这在工程上意味着，你的Agent编排在部署之前就可以被证明"不会出现死循环"——不是通过测试，是通过图算法。

第二，**并发安全**。DAG的拓扑序天然支持fan-out/fan-in（扇出/扇入，指任务从一点分裂成多个并行分支再汇聚到一点）的调度策略。每个节点收到的状态是独立副本，并行的分支不会互相污染。

Yue等人在2026年的综述"From Static Templates to Dynamic Runtime Graphs"（arXiv:2603.22386）中提出了ACG（Agentic Computation Graph，智能体计算图）作为统一抽象，将所有Agent工作流（模板化的、动态构建的、自适应的）统一在一个图式框架下描述。这篇综述的价值不在于提出了新东西，而在于证明了一个趋势：无论你的Agent是从静态模板展开还是运行时动态构建，最终的表达形式都是图。

这个"一切都是图"的趋势不止停留在综述层面。Sarker等人的GraphBit论文（arXiv:2605.13848）给出了一个扎眼的实证数据。他们在GAIA benchmark（68个 curated 任务）上测了LangGraph和GraphBit在不同任务类型下的框架引入幻觉率（framework-induced hallucinations，区别于LLM自身的幻觉）——GraphBit在确定性引擎编排下为0%，而LangGraph整体约为47%（no-tool任务0%，local文档任务15.8%，web任务69.0%）。

这个数字需要仔细读。47%是framework-induced，不是总幻觉率，且主要集中在web任务上。意思是，在LangGraph的编排中，相当一部分错误路由是框架层面的图结构设计导致的——Agent本来应该走A路径，但因为图的拓扑设计不够精确，被引导到了B路径。GraphBit用Rust实现的类型化DAG，通过编译期类型检查消除了这层不确定性。

**"0% framework-induced hallucinations"这个说法的含义是：图的拓扑不引入额外幻觉——框架的确定性执行引擎消除了路由层的不确定性，幻觉只可能来自于LLM节点内部的推理，不来自于图的结构**。

GraphBit的这个结论，恰好印证了DAG背后的编程思维（声明式）在AI场景下的具体体现。你不再描述"怎么做"，你描述"结构是什么"——节点之间的依赖关系、并发约束、数据流向。系统根据拓扑自动决定执行顺序和调度策略。

但DAG也有一个硬伤：**不能回退**。你只能在拓扑允许的方向上前进，不能回到已经走过的节点重新执行。对于需要试错、重试、动态调整策略的复杂Agent任务来说，这是一个结构性的限制。

---

## 有环图：完整的表达力，以及完整的代价

有环图在DAG的基础上加了一个关键能力：edge back——在图中走回头路。

LangGraph是这种架构的代表。它的StateGraph允许条件边（conditional edges），运行时通过一个函数决定下一节点。这个"函数"可以是任意Python代码，也可以是一个LLM调用。图的结构是固定的（人定义的），但图的遍历路径是动态的（运行时决定的）。

这不只是加了一个"回退"按钮。它把Agent的执行从"一条不归路"变成了"可探索的空间"。

LangGraph的运行时机制是为这种"可探索性"设计的。它用Pregel式的BSP（Bulk Synchronous Parallel，批量同步并行）执行模型组织每个super-step（超级步）——Plan → Execute → Reconcile → Checkpoint。每个super-step结束后，完整的State被序列化保存，形成checkpoint。这意味着你可以在任何时候回退到任意历史状态重新执行，类似于数据库的"时间旅行"查询。

确定性并发的实现也很巧妙：每个节点收到的是State的独立副本，并发节点在同一个super-step中并行运行，所有修改在reconcile阶段通过reducer函数合并。避免了竞态和非确定性行为。

这套机制的工程目标是一致的：**在允许Agent自由探索的同时，保证每一步都是可审计、可恢复的**。自由和控制不是对立的——BSP + checkpoint + replay的组合让两者可以同时存在。

Wei的调度器框架（arXiv:2604.11378）在这里提供了一个理论解释。他把LangGraph式的有环图归类为"structured graphs with explicit scheduling policy"——这是一种policy explicitness达到高水平、同时ready-set cardinality也保持高位（因为环路允许回到历史状态）的设计。在调度器设计空间中，这是目前表达能力最强的配置。

和DAG的声明式不同，有环图的编程思维进入了一种我称为**Graph原生**的模式：**你控制图的结构（节点和边的定义），系统控制图的遍历**。哪些边在什么条件下被激活、什么时候回退、什么时候终止，这些不再需要你手写调度代码——框架在遍历层面替你处理了。

---

## 重画CS地图：这不是新概念，但这是新位置

批评"Graph替代Loop"是旧概念换皮的人，从CS理论的角度看是对的。

有环图在计算机科学里有一个更正式的名字：有向有环图（directed cyclic graph）。它的理论根基是Petri网（1962年，Carl Adam Petri提出的并发系统建模工具），而Petri网的数学基础又可以追溯到图灵机和lambda演算的时代。BSP模型是Leslie Valiant在1990年提出的。Checkpoint/replay在分布式系统里用了三十年以上。

但概念的老旧不意味着组合的老旧。Uber的调度系统用了DAG，CI/CD pipeline也用了DAG——但它们用DAG解决的问题和Agent Runtime用DAG解决的问题不是同一个问题。

传统DAG系统要解决的是：给定一个确定性的任务拓扑，如何最优地调度资源？

Agent Runtime的DAG要解决的是：给定一个部分确定的结构框架，如何在LLM的不确定性输出和人的控制需求之间，找到一种可管理的平衡？

**两个问题有不同的解**。

**Graph在Agent Runtime中的应用，不是发明了新东西，而是把旧概念移到了一个新问题的正确位置上**。1990年的BSP解决的是大规模并行计算中的同步问题，2026年的BSP解决的是LLM不确定性下的step-by-step可控性问题——同样的数学工具，不同的工程上下文。

---

## 三种编程思维的对比：指令式、声明式、Graph原生

到这一步，编程思维的演进线已经清楚了。做一个横向对比。

| 维度 | 指令式（while + 状态机） | 声明式（DAG） | Graph原生（有环图） |
|------|------------------------|-------------|-------------------|
| **谁控制执行路径** | 开发者通过prompt + 状态转移表间接控制 | 开发者定义拓扑，系统决定调度 | 开发者定义图结构，系统决定图遍历 |
| **回退/重试** | 需要手写逻辑 | 不支持（无环限制） | 原生支持（checkpoint/replay） |
| **并发安全** | 需要手写锁/同步 | DAG拓扑保证执行顺序，节点内仍需同步 | BSP + reducer保证确定性并发 |
| **可审计性** | 低（执行路径不可预知） | 中（拓扑可静态验证） | 高（每步有checkpoint） |
| **表达能力** | 低（状态爆炸） | 中（无环限制） | 高（但可能死循环） |
| **复杂度代价** | 低 | 中 | 高（BSP、checkpoint、reducer都需要理解） |
| **适合场景** | 简单、确定性Agent | 多步但无回退的工作流 | 需要试错、多轮推理的复杂Agent |

**指令式编程在AI场景下的根本问题是：LLM不是确定性函数**。你写`if condition A: go to step B`，但condition A本身是LLM的输出，而LLM的同一段推理在两次执行中可能给出不同的判断。指令式假设了代码路径的确定性，这个假设在LLM的参与下不再成立。

声明式编程绕过这个问题的办法是：不写条件逻辑，只写拓扑关系。你不在代码里说"如果用户问了价格，走价格查询节点"，你只是在图上定义"用户意图识别节点"和"价格查询节点"之间有一条边。至于这条边什么时候走，由运行时根据节点输出动态决定。

Graph原生编程再进一步：你不用写条件逻辑，也不用穷举所有可能的拓扑关系。你只定义节点和边的基本结构，运行时在遍历过程中自主决定激活哪些边、回退到哪个状态、何时终止。

这个演进有一个清晰的逻辑方向：**这些抽象的共同方向是把"决定权"从开发者手里移交给系统，同时加强对系统行为的可观测性和可恢复性**。

你控制得更少了，但你知道得更多了。

---

## 局限性：Graph不是万能药

但Graph不是万能药。

有环图的第一个硬伤是**死循环**。DAG可以通过静态检测保证无环，但有环图恰恰允许了环路的存在。LangGraph的解决方案是设置最大迭代次数——这是一个工程上的兜底，不是理论上的解决。Gharzeddine和Saab在"Complete Cyclic Subtask Graphs"（arXiv:2604.22820）中分析了有环图在什么条件下有助于任务恢复、什么条件下反而增加协调开销。核心发现是：环路对任务性能的影响存在三个不同区间——环路密度较低时有助于任务恢复，但超过一定密度后协调开销反超收益。

第二个局限是，**Graph不是对所有任务都更优**。Dennis等人的"In-Context Prompting Obsoletes Agent Orchestration for Procedural Tasks"（arXiv:2604.27891v2）对比了LangGraph编排和全量prompt在一次完成（in-context prompting）方案在流程化任务上的表现。结论是：对于结构清晰、步骤固定的任务，把所有信息一次性塞进prompt，效果优于构建复杂的图编排。Graph的优势体现在需要动态决策、多轮试错、条件分支复杂的任务上，而不是所有任务。

第三，Graph引入了**新的复杂度**。BSP执行模型、checkpoint机制、reducer函数、fan-out/fan-in调度——这些概念对于团队来说是学习成本。LangGraph把Agent开发的门槛从"会写Python"提高到了"理解图遍历语义和事务性状态管理"。GraphBit用Rust实现类型化DAG，带来的好处是0%幻觉率，付出的代价是需要Rust编译器和类型系统知识——对一个主用Python的AI工程团队来说，这不是小门槛。

还有一点值得注意：**"Graph替代Loop"这个修辞本身是有误导性的**。Loop没有消失——在LangGraph的每个节点内部，你仍然在跑Loop。Agent调用LLM、获取tool_call、执行工具、更新状态的这一个周期，本质还是while循环。Graph替代的不是Loop，是Loop的无结构调度层。

Graph并没有消灭循环。Graph给循环穿上了拓扑约束的紧身衣。

---

## 编程范式的悄然转向

那篇掘金文章认为Graph是旧概念换皮。这个判断在计算机科学的概念史上成立，在Agent工程的问题域里不成立。

每一次编程范式的变迁，本质上都是"可控性模型"的升级。结构化编程（goto → function）把控制流从任意跳转变成了可预测的调用图。面向对象（function → class）把状态管理的复杂度封装进了对象的边界内部。函数式编程（mutation → immutability）通过消除副作用来消除一整类并发bug。**每一次都是丢掉一些控制自由度，换回一些可推理、可验证、可组合性**。

Graph在Agent Runtime中的角色，是在这条路线上的自然延伸。丢掉的是对每一步执行路径的微观控制，换来的是对整个执行过程的宏观可观测性、可恢复性、可验证性。

"Graph原生"最终会不会成为一个被广泛接受的编程范式分类，现在还不好说。但现在有一个趋势已经很难忽视了：当Agent的行为不再能用一段顺序执行的代码描述时，图结构是目前为止唯一在实践中被大规模验证过的替代抽象。

至于"Graph替代Loop"这个口号——它不够精确，但它的价值在于逼出了一个好问题。不是在问"图比循环好在哪"，而是在问：**当程序的执行路径不再由代码决定、而是由LLM的推理决定时，需要一种新的抽象来组织这些路径。**

Graph可能是第一个答案。不太可能是最后一个。

---

*参考来源：*

- 恋猫de小郭，2026-07-20，"AI又又造词，Graph就又要替代Loop了？"，掘金：[https://juejin.cn/post/7664063148857442347](https://juejin.cn/post/7664063148857442347)
- Wei, 2026, "From Agent Loops to Structured Graphs: A Scheduler-Theoretic Framework for LLM Agent Execution", arXiv:2604.11378, [https://arxiv.org/html/2604.11378](https://arxiv.org/html/2604.11378)
- Sarker et al., 2026, "GraphBit: A Graph-based Agentic Framework for Non-Linear Agent Orchestration", arXiv:2605.13848, [https://arxiv.org/html/2605.13848](https://arxiv.org/html/2605.13848)
- Yue et al., 2026, "From Static Templates to Dynamic Runtime Graphs: A Survey of Workflow Optimization for LLM Agents", arXiv:2603.22386
- Dex Mareno, 2026-07-01, "Every AI Agent Framework Became a Graph in 2026 — and the Hard Part Is Still Unsolved", dreaming.press, [https://dreaming.press/posts/every-ai-agent-framework-became-a-graph.html](https://dreaming.press/posts/every-ai-agent-framework-became-a-graph.html)
- Dennis et al., 2026, "In-Context Prompting Obsoletes Agent Orchestration for Procedural Tasks", arXiv:2604.27891v2
- Gharzeddine & Saab, 2026, "Complete Cyclic Subtask Graphs for Tool-Using LLM Agents", arXiv:2604.22820
- LangGraph官方文档, docs.langchain.com, [https://docs.langchain.com/oss/python/langgraph/graph-api](https://docs.langchain.com/oss/python/langgraph/graph-api)
- Tony Bai（译介，Carlos E. Perez 原文）, "Loop Engineering才火两个月，硅谷已经卷出'Graph Engineering'了", tonybai.com
- Microsoft, 2026-04, "Microsoft Agent Framework v1.0", graph-based Workflow API
