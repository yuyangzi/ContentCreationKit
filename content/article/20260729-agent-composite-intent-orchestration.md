# Agent 意图识别与任务编排：从 ReAct 到 Hierarchical Multi-Agent

> **导读**：Agent 领域有一个越来越难回避的问题：我们在编排上花的功夫，有多少是真正创造价值的？Dennis 等人 2026 年 4 月的一篇论文直接宣告"in-context prompting 让 Agent 编排过时了"。把完整流程写进 system prompt，效果居然碾压了 LangGraph 精心编排的同一套模型。

但这篇论文的结论只覆盖了"过程式任务"（步骤已知、路径确定的任务）。但当用户丢进来一句"分析一下竞争对手最近的动态，汇总上周数据发我一份报告，顺便帮我约个会"，事情就完全不一样了。这种复合意图（composite intent）才是编排真正不得不出场的地方。

2026 年 4 月，Dennis 等人在一篇题为"In-Context Prompting Obsoletes Agent Orchestration for Procedural Tasks"的论文里做了一个让编排框架厂商不太舒服的实验：把一整套流程直接写成 system prompt 喂给前沿模型，对比同一模型在 LangGraph 编排下的表现。

结果直截了当——**裸 system prompt 在过程式任务上系统地优于编排版本**。该论文引用 Gupta 等人的同期研究指出，pass@1 能达到 60% 的 Agent，在同一次任务的不同 trial 之间只有 25% 的一致性。编排不仅没有让 Agent 更稳定，反而引入了新的错误源。

这个结论看似否定了编排的全部价值。但论文标题里的"Procedural Tasks"这个限定词，已经说明事情没那么简单。过程式任务的特点是步骤可枚举、依赖关系确定、工具调用路径在任务开始前就已知。这种场景下，in-context prompting 确实更优，因为编排层多出来的路由决策、状态传递、错误重试，每一步都在累积出错概率。

真正让编排变得无法回避的，是复合意图。

你让模型"帮我查一下英伟达今天股价"，这是单一意图（singular intent）。你让模型"分析一下三家竞争对手最近一周的产品动态，汇总上季度销售数据，写一份简报，给团队发邮件约明天下午的讨论会"——这就复杂了。

这里面包含四种不同性质的子任务：

- 信息检索
- 数据分析
- 内容生成
- 工具调用

每种子任务需要的工具和能力不同，它们之间还有依赖关系（你先查了竞品动态才能写简报，写了简报才知道要在邮件里说什么）。

这种复合意图需要的能力不是单一 prompt 能承载的，它需要**意图识别、任务分解、动态编排**三层能力协同工作。

目前主流的编排模式有四种，从最轻量的 ReAct 到复杂度最高的 Hierarchical Multi-Agent。每种模式回答三个问题：它怎么工作、适合什么场景、踩了什么坑。

---

## ReAct：编排的基线

ReAct（Reasoning + Acting）是 Yao 等人在 2022 年提出的范式，核心思想简单到只有四个词：Think → Act → Observe，循环往复。模型先"想一步"（Think），然后执行一个动作（Act），拿到环境反馈后"观察结果"（Observe），再基于新信息继续想下一步。

精简是这个循环最突出的优势：

```Python
# ReAct 核心循环——Think → Act → Observe
def react_loop(query, tools, max_steps=10):
    context = [{"role": "user", "content": query}]
    for step in range(max_steps):
        thought = llm_think(context)       # Think: 推理下一步做什么
        action = parse_action(thought)      # Act: 解析出工具调用
        if action.tool == "finish":
            return action.answer
        observation = execute_tool(action)  # Observe: 执行并获取环境反馈
        context.append({"role": "assistant", "content": thought})
        context.append({"role": "tool", "content": observation})
```

每一步都透明可追溯——出错了能回溯到具体哪一步做的错误决策，这是复杂编排系统做不到的。

ReAct 最适合的场景是 1-5 次工具调用的简单任务——查天气、搜资料、算个数学题。超过这个范围，问题就来了。

它没有全局规划能力，每一步本质上都是贪婪决策（只看当前状态决定下一步），经常走出"局部最优但全局很蠢"的路径。上下文窗口随着循环不断膨胀，每一步都把前一步的思考和观察结果塞回去，10 步之后 prompt 里有一半是历史垃圾。而且它天然是串行的（每一步必须等上一步的工具调用返回结果才能继续），没有任何并行空间。

但 ReAct 最大的价值不是性能，而是它定义了一个基准线。引入任何编排复杂度之前，都应该先问自己：ReAct 能搞定吗？能，就不要往上加东西。Dennis 等人的论文已经证明，多出来的编排层不是你免费获得的保险，而是实打实的错误来源。

---

## Plan-and-Execute：把思考和执行分开

ReAct 的问题在于"边想边做"——思考和执行混在同一个循环里，既让上下文窗口爆炸，又让并行执行变得几乎不可能。Plan-and-Execute 范式的思路是：**先想清楚整条路怎么走，再一次性执行**。

这个思想最早在 Wang 等人的 Plan-and-Solve（2023）里被明确提出，但真正把这件事工程化的是 Kim 等人在 ICML 2024 发表的 LLMCompiler。它的核心贡献，是把 Plan-and-Execute 从"列步骤清单"升级为"建有向无环图"。

LLMCompiler 把任务建模成一个 DAG（有向无环图）G=(V, E)，其中 V 是工具调用的集合，E 是它们之间的依赖边。这个形式化带来的直接好处是：没有依赖关系的工具调用可以并行执行，有依赖关系的按顺序排队。论文（Kim et al., ICML 2024, arXiv:2312.04511）的数据是 3.7 倍延迟降低、6.7 倍成本节省，在准确率上还比 ReAct 提高了约 9%。

核心逻辑长这样：

```Python
# LLMCompiler DAG 任务定义与并行调度
class TaskDAG:
    def __init__(self):
        self.tasks = []   # V: 工具调用列表
        self.edges = []   # E: 依赖边 (from_idx, to_idx)

    async def execute(self):
        done = set()
        for step in parallel_topological_sort(self):
            # 无相互依赖的 task 并行执行
            results = await parallel_dispatch(step, self.tasks)
            done.update(step)
```

Planner（规划器）只被调用一次，生成完整的执行计划。Executor（执行器）按计划执行，有依赖关系的顺序跑，没依赖关系的并行跑。这个架构在 5-20 步的工作流里效果很好。

但它有一个结构性脆弱点：**计划是静态的**。Planner 在任务开始前就锁定了整条路径，执行过程中如果发现 step 3 的输出不是 step 4 期望的输入格式，整个计划就会在过渡点崩溃。

LLMCompiler 论文里讨论过这个问题——工具的输入输出格式不匹配是最常见的计划失败模式。你可以加 replanning 机制（Plan-and-Act，Erdogan et al., ICML 2025），但每次 replanning 都意味着额外的大模型调用，会吃掉 Planner 一次调用的成本优势。

什么时候用它？工作流有 5-20 步、依赖关系可以提前画清楚、工具接口稳定不会出格式意外。研究工作流、数据处理流水线这类场景最合适。但如果你的工具环境是动态变化的（比如 MCP 服务随时可能上新工具），静态计划的风险就会显著上升。

---

## Orchestrator-Worker：并行专业分工

当任务的规模超出一个 Agent 的注意力范围时，Plan-and-Execute 的静态图就撑不住了。你需要的是一个"导演+演员"模型——一个统筹者（Orchestrator）把大问题拆成独立子任务，派给一群专业子 Agent（Workers），各自完成后再汇总。

Anthropic 在 2025 年 6 月公开了他们内部做多 Agent 研究的工程实践，这可能是目前关于 Orchestrator-Worker 模式最有参考价值的生产经验。他们用 Claude Opus 4 做统筹者，Sonnet 4 做执行子 Agent，在做复杂研究任务时这套系统比单独用 Opus 4 提升了 90.2%。

但这个数字有个容易被忽略的前提。Anthropic 的博客里写得很清楚："Teach the orchestrator how to delegate."

具体来说，每个子 Agent 拿到的不是一句笼统的"你去查一下这个"，而是一份结构化的任务描述，包含明确的交付目标（objective）、输出格式要求（output format）、可用工具清单（tool guidance）、任务边界定义（clear boundaries）。不做这套功课，子 Agent 要么在同一区域重复劳动，要么在边界缝隙丢活。

代码层面大概是这个结构：

```Python
# Orchestrator-Worker：统筹者下发结构化子任务
class Orchestrator:
    def delegate(self, query: str) -> list[SubTask]:
        plan = llm_plan(query)
        sub_tasks = []
        for item in plan:
            sub_tasks.append(SubTask(
                objective=item.goal,      # 精确目标
                output_schema=item.schema, # 输出格式约束
                tools=item.tools))         # 可用工具限制
        results = parallel_dispatch(sub_tasks)  # 并行派发
        return synthesize(results)
```

Anthropic 工程团队还总结出一个关键实践：子 Agent 的输出尽量写文件系统而非互相传递——也就是 "game of telephone"（传话游戏）的信息降级问题。

每个子 Agent 把中间结果写到结构化文件里，统筹者去读文件做汇总，这样信息不会在多轮传递中被压缩变形。

Orchestrator-Worker 最大的优势是"广度优先"——你可以同时跑 5 个独立的竞品分析、7 个不同数据源的查询、3 个维度的对比研究。子 Agent 之间上下文隔离，不会互相污染。

但它也有两个硬伤：一是 token 消耗惊人，Anthropic 自己的数据是多 Agent 系统的 token 消耗约为单 Agent 对话的 15 倍；二是统筹者是同步瓶颈（必须等所有子 Agent 全部完成后再做汇总），最慢的那个子任务决定了整体延迟。

什么场景用它？任务有天然并行性（同时查多个源、同时分析多个维度）、单 Agent 上下文装不下的复杂问题、需要多专业能力协同的深度研究。

如果你的任务是一个线性推理链，就别加这套了——Dennis 的论文结论在这里同样适用：为线性任务加编排层等于给自己挖坑。

---

## Hierarchical Multi-Agent：意图驱动的动态子 Agent 工厂

前三种模式解决的是"任务已知、路径可枚举"的问题。但当用户丢进来一个开放式的复合意图："帮我研究一下 Agent 框架的最新进展，对比一下 LangGraph 和 CrewAI 在生产环境的表现，如果 LangGraph 更好就帮我写个 demo"，你会发现任务在开始之前根本无法完全枚举。

你不知道需要查哪些论文，不知道对比维度有多少，甚至不知道"写 demo"这个子任务会不会在执行中被否定掉。

**这正是 Hierarchical Multi-Agent 模式的用武之地：让系统在运行时动态发现工具、动态创建子 Agent、动态调整计划。**

Skywork AI 在 2025 年提出的 AgentOrchestra（arXiv 2506.12508）是这一方向的代表性架构。它基于 TEA（Tool-Environment-Agent）协议，用一个顶层规划 Agent 做意图分解，一个 MCP Manager 做动态工具创建和发现，子 Agent 可以按需从工具池里拉取能力，执行结果通过反馈回路回到规划层触发 replanning。

更值得细看的是 Gao 等人在 2026 年的 SkillWeaver（arXiv 2606.18051），因为它点出了一个关键瓶颈：**skill-aware decomposition（能力感知分解）**。

SkillWeaver 的流程是 Decompose → Retrieve → Compose，核心在于分解任务时必须知道自己手里有什么可用的工具/技能（skills），做不到这点，分解出来的子任务有一半是无法执行的——因为对应的工具不存在。

SkillWeaver 的 SAD（Skill-Aware Decomposition）算法迭代式地把任务分解和工具匹配对齐，每轮分解后查询可用工具库，不匹配就调整分解方式。

这个对齐过程把 DA（分解准确率，Decomposition Accuracy）从 51.0% 拉到了 67.7%；在分解正确的前提下，工具分类召回率 CatR@1 从 34.2% 提升到 37.0%。在动态工具环境里，意图分解的精度上限不是模型推理能力，而是模型对"手头有什么武器"的了解程度。

架构层面，Hierarchical Multi-Agent 的核心是"意图到子 Agent 的映射"：

```Python
# Hierarchical Multi-Agent: 意图 → 技能匹配 → 动态子Agent创建
class HierarchicalOrchestrator:
    def process_composite_intent(self, query: str):
        intent_graph = decompose_intent(query)     # 意图分解
        for node in intent_graph:
            # 能力感知分解：只分解到手头有 tool 能解决的粒度
            skills = match_skills(node, skill_registry)
            if skills.match_score < threshold:
                intent_graph.replan(node)          # 不匹配就重分解
            else:
                agent = AgentFactory.create(       # 动态创建专用子Agent
                    skills=skills, objective=node.goal)
                schedule(agent, node.dependencies)
```

这是四种模式里最复杂的，也是最难调试的。错误可以在三个层级之间"层级传播"——规划层拆错了一个子任务，工具匹配层给了这个子任务一个不合适的工具，执行层用这个不合适工具跑出了一堆垃圾输出，然后这些垃圾输出被当成中间结果传给下一个子 Agent。

等你发现最终答案不对劲，要追溯到是哪个环节出的问题，难度不亚于在分布式系统里找一个竞态 bug。

什么场景用它？企业 Agent 平台（用户意图高度多样、工具动态变化）、跨领域复合任务、运行时才知道有什么工具可用的环境。

什么场景不该用？如果你的工具集是固定的、任务类型是可枚举的，前面三种模式就够了。Hierarchical Multi-Agent 的复杂度不便宜——每多一层编排，就多一层出错空间。

---

## 决策框架：什么时候加编排？

四种模式不是四个"升级选项"——不是说 ReAct 是 1.0、Plan-and-Execute 是 2.0、最后一定要进化到 Hierarchical Multi-Agent。它们为不同类型的问题而设计，选错了在某些场景下比不选更糟。

| 场景 | 推荐模式 | 原因 |
|------|----------|------|
| 单一工具调用，路径确定 | 不加编排（system prompt） | Dennis et al.：编排引入级联错误 |
| 2-5 次工具调用，流程简单 | ReAct | 复杂度最低，绝大多数场景够用 |
| 5-20 步，依赖关系明确 | Plan-and-Execute（LLMCompiler） | 并行执行 + 成本优势 |
| 并行独立研究/多源分析 | Orchestrator-Worker | 子 Agent 隔离避免上下文污染 |
| 工具动态变化，复合意图 | Hierarchical Multi-Agent | 能力感知分解 + 动态工具发现 |

做决定之前，值得记住 Anthropic 在 2024 年 12 月 "Building Effective Agents" 那篇指南里的第一条原则：**从最简单的东西开始**。

单 Agent + 检索在很多场景下比多 Agent 编排效果好。多出来的编排复杂度不是免费午餐——Dennis 的论文把这句话用数据钉死了，Anthropic 自己的生产实践也反复验证了。

---

## 五个避不开的坑

编排好不代表能跑好。下面这些坑来自 2025-2026 年间多个团队的生产事故复盘，每一个都可能显著抬高系统的故障率和成本。

- **过度分解。** 把任务拆成 20 个子任务不叫精细，叫浪费。组织行为学和多 Agent 系统的研究都证实存在"协调税"（coordination tax）：每多一层编排，就多一层通信开销、信息损失和错误累积。在过度分解的极端情况下，大部分 token 和算力花在子任务协调上而非实际执行，产出反而比单 Agent 更差。最优分解粒度取决于任务本身的可并行程度和接口质量——接口越清晰、依赖越少，拆分的收益才越大。

- **意图漂移。** Agent 在每一步路由决策时都可能偏离原始意图。实际工程中，不应该只在入口做一次意图识别就完事了——每次路由决策时都要重新评估当前状态与原始意图的匹配度。常见的做法包括对意图状态做时序版本化（temporal versioning），记录意图在每步决策后的残余度，当残余度低于阈值时触发澄清或回滚。

- **上下文窗口衰减。** Lost in Conversation（LiC）不是新问题，但在编排系统中更致命——不是单个 Agent 的上下文爆炸，是多个 Agent 之间的"传话"让信息逐层衰减。Anthropic 的做法是子 Agent 写文件系统、主 Agent 读文件，而非在 prompt 里传递中间结果。LangGraph 的 checkpointing 机制（节点边界快照）+ compaction（历史上下文压缩）是目前工程上比较成熟的对策。

- **MCP 工具选择错误。** Tool Selection（工具选择）是编排系统里经常被低估的故障点。MCP 服务的工具描述如果写得模糊或不准确，Agent 可能选到一个"看起来像但完全不是"的工具，然后基于错误工具的输出继续推理，整条链全错。这个问题目前还没有简单解法——只能在工具注册时做好描述验证，给每个工具加明确的前置条件和输出格式 Schema。

- **幻觉计划。** LLMCompiler 风格的计划在过渡点最容易出问题——step N 的输出格式是 A，step N+1 的输入格式是 B，但 Planner 假设了 A=B。人看着计划觉得逻辑通顺，但跑起来在接口层就断了。Plan-and-Act（Erdogan et al., ICML 2025, arXiv:2503.09572）的动态 replanning 是补救方案，但更好的做法是在计划生成阶段就用结构化 Schema（Pydantic、JSON Schema）约束每一步的输入输出，让类型系统在运行前就拦住格式不匹配。

---

## 五个值得养成的习惯

这些经验不来自论文，而来自把 Agent 编排系统跑在生产环境里的团队。

- **从简单开始，证明"不够用"再加复杂度。** Anthropic 的生产经验表明：单 Agent + 工具检索能解决大部分问题，编排是最后才加的东西，不是第一件做的事。如果你不能清晰地说出"为什么 ReAct 不够用"，就不必装 LLMCompiler。

- **结构化输出贯穿全链路。** 意图分类用 Pydantic Schema 而非自然语言标签，计划用 JSON 描述每步的输入输出类型，路由决策有确定性的匹配规则而非 prompt 推理。结构化不是为了好看，是为了 debug 的时候有线索可追。

- **在开工前定义好每类故障的应对策略。** 不是"出错了重试"，而是要区分四种层次：
  - retryable（可重试，如网络超时）
  - recoverable（可恢复，如输出格式不对但可以重新解析）
  - blocking（阻塞，如依赖任务失败导致后续无法执行）
  - degraded（降级，如某数据源不可用但可以用缓存替代）

  每一层有不同的处理路径，全用 `max_iter=25` 硬重试是预案缺失的表现。

- **从第一天起就把 tracing 和可观测性做好。** Agent 系统是非确定性的——同一条输入跑三次可能出三个不同结果。没有 trace，很难知道哪一步出了错、为什么同一个任务昨天能跑通今天挂了。LangChain/LangGraph 的 tracing、OpenTelemetry 的 span 埋点、Dify 的 workflow 可视化，选一套，上线第一天就用。

- **推理模型做规划，便宜模型做执行。** 这是 LLMCompiler 论文里隐含、但在生产中被反复验证的一条经验：用高推理能力模型生成计划，用便宜模型跑具体步骤。Plan 需要推理深度，Execute 只需要指令遵循——把贵的 token 花在刀口上。

---

编排的价值不是"让 Agent 更强"，而是"让 Agent 在特定场景下更可控"。Dennis 那篇论文的真正启示不在于"编排没用"，而在于：**大多数重要的编排决策都值得接受同等质疑**。加了一层路由，它带来了什么收益，又引入了什么新的失败模式？这个问题不问清楚，编排就不该上。

复合意图识别和动态任务编排是 Agent 工程里尚未标准化的一层。ReAct、LLMCompiler、Orchestrator-Worker、Hierarchical Multi-Agent 各有各的来路，也各有各的局限。目前这个领域的共识还很浅：先搞清楚面对的是什么类型的意图，再选对武器。

*参考来源：*

- ReAct: Synergizing Reasoning and Acting in Language Models — Yao et al., 2022, [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)
- LLMCompiler: An LLM Compiler for Parallel Function Calling — Kim et al., ICML 2024, [arXiv:2312.04511](https://arxiv.org/abs/2312.04511)
- In-Context Prompting Obsoletes Agent Orchestration for Procedural Tasks — Dennis et al., April 2026, [arXiv:2604.27891](https://arxiv.org/abs/2604.27891)
- How We Built Our Multi-Agent Research System — Anthropic Engineering Blog, June 13, 2025
- Building Effective Agents — Anthropic Research, December 2024
- AgentOrchestra: A Hierarchical Multi-Agent Framework for General-Purpose Task Solving — Skywork AI, [arXiv:2506.12508](https://arxiv.org/abs/2506.12508)
- SkillWeaver: Compositional Skill Routing for LLM Agents: Decompose, Retrieve, and Compose — Gao et al., [arXiv:2606.18051](https://arxiv.org/abs/2606.18051)
- Plan-and-Act: Dynamic Replanning for Plan-and-Execute Agents — Erdogan et al., ICML 2025, [arXiv:2503.09572](https://arxiv.org/abs/2503.09572)
- NaviAgent: Bilevel Planning with Tool Dependency Graph — [arXiv:2506.19500](https://arxiv.org/abs/2506.19500)
