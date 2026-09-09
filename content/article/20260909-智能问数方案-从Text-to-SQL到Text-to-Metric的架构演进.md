---
mode: deep-tech
---

# 智能问数方案：从 Text-to-SQL 到 Text-to-Metric 的架构演进

2024 年底，Spider 2.0 基准（arXiv:2411.07763）把"已解决"的幻觉戳破了：632 个源自真实企业场景的工作流任务上，GPT-4o 配最简评测框架只解决了 5.7%，配上完整的 Spider-Agent 也只有 12.3%。同一篇论文的对照数字是，GPT-4 系方法在 Spider 1.0（学术基准，小而干净的 SQLite 库）上曾达到 91.2% 的执行准确率。真实企业数据库动辄上千列、命名晦涩、多方言混杂，和学术基准是两个世界。

也不是 GPT-4o 的个案。换成推理更强的 o1-preview、配上论文自己的代码 agent 框架，解决率也只从 12.3% 拉到 21.3%。

学术 benchmark 上的"已解决"，在企业场景里可能连入门门槛都没摸到。但另一条路线（Text-to-Metric，国内数据平台圈也写作 NL2Metric）在同一个基准体系的 Spider2-snow 子集上跑出了 94.15% 的执行准确率（arXiv:2606.31041）。

答案藏在架构里。

## 一、规则时代：当数据库说方言

自然语言转查询这件事，比大模型早了至少二十年。早期的系统是规则引擎：关键词匹配 + 模板填充 + 预定义意图。你问"上个月销售额多少"，系统识别"销售额"关键词和时间修饰词"上个月"，套模板生成 SQL。

这套方案的问题不是准确率低（在预定义范围内准确率可以很高），而是覆盖范围窄得可怜。每增加一种问法就要加一条规则，每接一张新表就要重写映射。维护成本随 schema 规模线性增长，而企业 schema 的增速通常比维护团队快。

更根本的问题是，规则系统不理解语义。"用户"和"客户"和"会员"在业务上是同一个东西，但规则系统眼里是三个不同的词。同义词、缩写、业务黑话——这些对人类再自然不过的语言现象，对规则引擎来说就是一个个需要手动处理的异常。

## 二、Seq2Seq 时代：让模型学翻译

深度学习把 Text-to-SQL 重新定义为翻译问题：自然语言是源语言，SQL 是目标语言，用 encoder-decoder 模型做端到端映射。代表工作如 SQLNet、TypeSQL，以及后来的 IRNet。

这个范式在 WikiSQL（单表查询）上跑到了 90% 以上，看起来很美。但 WikiSQL 的"单表"假设暴露了它的局限——真实企业查询几乎必然涉及多表 JOIN。Spider 基准（2018）把这个问题摆上台面：10,181 个问题、200 个数据库，多表、嵌套子查询、窗口函数全上了。Seq2Seq 模型在 Spider 上的执行准确率长期在 50-60% 徘徊。

核心瓶颈是 schema 编码。模型需要同时理解自然语言问题和数据库 schema（表名、列名、外键关系），但 schema 的规模和结构变化很大——有的库 5 张表，有的 500 张。把整个 schema 塞进 encoder 既不现实也不高效。后续工作如 RESDSQL（arXiv:2302.05965）把 schema linking 和 skeleton parsing 解耦，先筛选相关 schema 再生成 SQL，把 Spider dev 集的精确匹配率（EM，Exact Match）推到 80.5%、执行准确率（EX，Execution Accuracy）推到 84.1%。

但 84% 是在"小而干净"的 schema 上。一旦 schema 变大变脏（列名从 `revenue` 变成 `c_rev_x7`，表间关系从清晰变成需要翻三天文档才能搞明白），Seq2Seq 的翻译范式就开始崩盘。模型学到的是"这种自然语言模式对应那种 SQL 模式"的统计关联，而不是真正的语义理解。当 schema 偏离训练分布，统计关联就断了。

## 三、LLM 单次生成：大力出奇迹

GPT-3.5 和 GPT-4 的出现改变了游戏规则。大语言模型自带海量世界知识，见过各种 schema 命名风格，能理解"c_rev_x7"可能是 revenue 的缩写——这是 Seq2Seq 模型很难做到的。

早期用法很直白：把 schema 描述 + 用户问题一起扔给 LLM，让它直接输出 SQL。DIN-SQL（arXiv:2304.11015, NeurIPS 2023）把这个流程系统化——先做 schema linking 筛选相关表，再按复杂度分类（简单/中等/困难/极难），然后分步生成子查询，最后用执行反馈做自纠错，在 Spider test 上拿到 85.3% EX。

但"大力出奇迹"很快撞上了三个天花板。

**第一个天花板是 schema 规模。** 企业 schema 动辄几百张表、几千列，全部塞进 prompt 会爆上下文窗口。解决方案是 schema 选择：先用一个模型判断哪些表/列和问题相关，只把相关部分传给生成模型（Uber 的 Column Prune Agent 专门干这事，LinkedIn 用多阶段检索（arXiv:2507.14372），先召回 20 张表再排序到 7 张）。

**第二个天花板是复杂查询。** 多表 JOIN、嵌套子查询、窗口函数、递归 CTE——这些 SQL 的高级特性对 LLM 来说不是"更难一点"，而是"容易静默出错"。语法能过编译，但语义是错的。比如 JOIN 条件写错导致笛卡尔积，或者 GROUP BY 漏掉一个维度导致聚合结果翻倍。这种错误比语法错误更危险，因为查询能执行、能返回结果，但结果是错的。

**第三个天花板是业务语义。** 这是最致命也最容易被忽略的。"销售额"在销售部门指含税金额，在财务部门指不含税金额，在运营部门可能指扣除退款后的净额。LLM 从表名和列名里推断不出这些业务口径差异。Salesforce 的官方博客（《Build a Semantic Layer Your AI Agents Can Reason Over》）指出：语义层（Semantic Layer）存在的根本原因，就是 LLM 无法从物理 schema 推断业务逻辑。

## 四、Agent 多步推理：给 LLM 装上工作台

面对单次生成的天花板，2024-2025 年的主流解法是 Agent 化——不再让一个 LLM 端到端生成 SQL，而是把任务拆成多个步骤，每个步骤由一个专门的 Agent 或模块处理。

MAC-SQL（COLING 2025）设计了三个角色：Selector 负责筛选 schema，Decomposer 负责把复杂问题拆成子问题，Refiner 负责纠错。CHASE-SQL（arXiv:2410.01943, ICLR 2025）走得更远——用三条并行路径生成候选 SQL（分治拆解、基于执行计划的 CoT 推理、实例感知的 few-shot 生成），再用一个微调的二分类 LLM 做 pairwise 选择，BIRD test 上 73.0% SOTA。XiYan-SQL（arXiv:2411.08599，阿里系）走多生成器集成路线：多个不同策略的生成器各自产出候选再投票选择，仅 5 个候选就在 BIRD test 集拿到 75.63% EX（提交时的榜单第一）；其期刊扩展版（arXiv:2507.04701，IEEE TKDE）把这套思路称为"专家社会"（society of experts）。

Snowflake 的 Arctic-Text2SQL-R1（2025.05）换了一个角度：与其让模型模仿 SQL 的写法，不如让它学会推理，用执行准确率作为奖励信号做强化学习（RL）。32B 模型在 BIRD test 集达到 71.83% EX，14B 达到 70.04%——证明推理训练 + 执行对齐比单纯堆参数量更有效。

Agent 化确实提升了准确率，但代价是延迟和成本。多 Agent 架构意味着多次 LLM 调用：以 CHASE-SQL 为例，三条路径并行生成候选再做 pairwise 选择，单次查询的调用次数和 token 消耗都是单次生成的数倍。对于交互式分析场景，用户等几十秒才看到一个数字，体验并不好。

更关键的是，Agent 化解决的是"如何更好地生成 SQL"，但没有解决"为什么要让 LLM 生成 SQL"这个更根本的问题。

## 五、语义层中介：LLM 不写 SQL，选指标

Text-to-Metric 的核心思路很简单：LLM 不直接生成 SQL，而是从预定义的业务指标库里选出正确的指标和维度，然后把"选指标"这个任务交给确定性引擎去编译成 SQL。

这个思路的学术化表达来自 arXiv:2606.31041 的 SMQ（Semantic Model Query）模式。整个架构分两层：

**上层是 LLM Agent**，负责理解用户意图。它看到的不是原始 schema（表、列、外键），而是语义层——一个由业务指标、维度、度量组成的抽象层。用户问"上个月华东区 iPhone 的退货率是多少"，LLM 的任务是从语义层里选出"退货率"这个指标、"区域=华东"这个筛选条件、"产品=iPhone"这个筛选条件、"时间=上个月"这个时间范围。

**下层是确定性编译器**，负责把 LLM 选出的指标和维度编译成方言正确的 SQL。编译器从指标定义库解析"退货率"的物理表达式（可能是 `SUM(return_amount) / SUM(sales_amount)`），从 join graph 自动注入表间关系，生成最终 SQL。

```json
// SMQ 示例：LLM 输出的结构化查询
{
  "metrics": ["return_rate"],
  "filters": [
    {"dimension": "region", "op": "IN", "value": ["华东"]},
    {"dimension": "product", "op": "IN", "value": ["iPhone"]},
    {"dimension": "time", "op": "LAST_MONTH"}
  ],
  "group_by": ["time__month"]
}
```

这个设计的精妙之处在于**物理标识符（表名、列名、JOIN 条件）全部来自确定性编译器，而非 LLM 生成**。LLM 只处理业务语义层面的选择——选哪个指标、按什么维度分组、加什么筛选条件。这就在很大程度上消除了 Text-to-SQL 最头疼的"幻觉列名"问题：LLM 的输出只能是语义层里已定义的实体，物理列名要到编译阶段才被展开，它很难凭空造出一个自己根本接触不到的列名。

Spider2-snow（Spider 2.0 的 Snowflake 子集，547 个任务）上的结果验证了这个机制：SMQ 模式达到 94.15% EX，位列官方榜单第三；同一榜单上裸 schema 的 DAIL-SQL + GPT-4o 只有 2.2%。这个对比要打个折扣看——SMQ 的基座是 2026 年的新一代模型，2.2% 是 2024 年 GPT-4o 的成绩，四十多倍里掺着模型代差，不能全记在架构头上。但机制层面的收益是真的：幻觉列名这一整类错误被从解空间里结构性地移除了，这不是模型换代能带来的改变。

## 六、语义层长什么样

语义层不是数据字典。数据字典是"这张表叫什么、那列是什么类型"的技术元数据，语义层是"销售额怎么算、活跃用户怎么定义、这两个指标能不能直接比较"的业务知识图谱。

一个完整的语义层通常包含以下要素：

**指标定义**是核心。每个指标有明确的计算逻辑（聚合公式、过滤条件、口径说明）。"销售额"不是某个表的某列，而是 `SUM(order_amount) WHERE status = 'completed' AND is_test = false`。这个定义一旦确定，无论谁问、怎么问、用什么工具查，结果都一样。

**维度定义**描述怎么切数据。时间维度（按天/周/月）、地理维度（国家/省/城市）、品类维度（一级类目/二级类目）——维度之间有层级关系，维度上有属性（比如"城市"维度有"所属省份"属性）。

**Join 图**定义表间关系。哪些表通过什么条件关联、是 1:1 还是 1:N、是否需要桥接表——这些信息对 LLM 来说很难从 schema 推断，但对确定性编译器来说是输入参数。

**同义词和别名**处理自然语言的变体。"用户"="客户"="会员"="买家"——语义层把这些映射到同一个维度或指标，LLM 不需要自己猜。

**权限规则**控制谁能看什么。行级安全（RLS）在语义层定义，编译 SQL 时自动注入 WHERE 条件，不需要 LLM 理解权限逻辑。

dbt MetricFlow、Cube、Snowflake Semantic Views、Databricks Metric Views 都是这个架构的产品化实现。开源侧的 WrenAI（语义层 + LLM 问数）、DB-GPT、Vanna 也在相近的路线上。区别在于指标定义放在哪里：dbt 放在版本控制的代码里，Snowflake 放在仓库原生视图里，Cube 放在独立的语义服务里。

## 七、分层协作是终局

Text-to-Metric 准确率高，但不是万能的。它的覆盖范围受限于语义层里预定义的指标和维度。如果用户问了一个语义层没覆盖的问题（比如临时想看两个未定义指标的比值，或者探索一个全新的数据关系），语义层就回答不了。

语义层自己也有成本。指标定义要人来建模，要跟着业务口径持续演化，口径一漂移，编译出来的"确定性"就是过时的确定性。SMQ 论文的讨论部分也没回避这两件事：语义层的质量决定方案上限，语义中介在换取 grounding 的同时，也带来过拟合已建模域的风险。建层的钱和持续治理的人，最终都会出现在账上。

这就回到了分层协作的架构：

**治理查询走语义层**。KPI 看板、定期报表、合规审计——这些查询重复性高、口径要求严、结果必须可审计。语义层保证确定性和一致性，Spider2-snow 上的公开最好成绩是 94.15%。

**Ad-hoc 查询走直接 SQL**。探索性分析、临时取数、长尾问题——这些查询灵活性强、覆盖范围广、对延迟敏感。LLM 直接生成 SQL，配合执行反馈和自纠错，准确率可能在 60-80%，但胜在灵活。

Uber 的 QueryGPT 实际上就是这个架构的雏形：Workspaces 按业务域整理表（类似语义层的域划分），Intent Agent 判断问题类型，Table Agent 选表，Column Prune Agent 精简 schema。它没有显式的语义层，但"按业务域缩小搜索范围"本质上是在做语义层做的事。

## 八、Text-to-Chart：问数的延伸

如果把"自然语言 → 数据操作"的链条再延伸一步，就是 Text-to-Chart（NL2Vis）：自然语言直接生成可视化图表。

这个方向比 Text-to-SQL 更难，因为多了一个决策维度——图表类型选择。同一个问题可以用柱状图、折线图、饼图来回答，选哪种取决于数据特征和分析意图。nvBench 是首个大规模 NL2VIS 基准，25,750 对 (NL, VIS)，覆盖 7 种图表类型（基准首发于 SIGMOD 2021，arXiv:2112.12926 是其数据集扩展版）。2025 年的 nvBench 2.0（arXiv:2503.12880）进一步显式建模了查询歧义（同一个问题可能对应多个合理可视化）。

Text-to-Chart 通常建立在 Text-to-SQL 之上：先确定查什么数据，再决定怎么展示。也有一些端到端方案直接生成 Vega-Lite 或 ECharts 配置（arXiv:2404.17136 是这条线上的代表性探索），但公开评测里通常低于"先 SQL 再图表"的分步方案。

从工程角度看，Text-to-Chart 目前更适合"已知问题类型、已知数据范围"的场景——比如 BI 工具里的"智能图表推荐"。这和问数是同构的问题：图表类型和字段映射的收敛越彻底，生成的配置才越可靠。完全开放的 NL2Vis 还有很长的路要走。

## 九、给工程师的实操建议

如果你正在考虑让团队落地智能问数，下面六条经验都有企业案例支撑。

**先建语义层，再上 LLM。** 没有语义层的 Text-to-SQL 在 demo 里好看，在生产里很难稳定。建层是前提，不是可选项。语义层不需要一开始就完美，先从 10-20 个核心指标开始，覆盖 80% 的日常查询。

**Schema 标注比模型升级更有效。** LinkedIn 的消融研究显示：仅 schema 时正确率 9%，加 example queries + 表聚类 + 表/列属性后提升到 49%（专家评审口径，4 分及以上算对）。给每列加业务描述、给每个表加使用场景说明，这些"脏活"比换更大的模型回报更高。

**执行反馈是最低垂的果实。** 生成 SQL → 执行 → 把错误信息喂回 LLM 重试。这个循环实现简单，但效果立竿见影。LinkedIn 把编译错误从 34% 降到 4%，主要靠的就是这个。

**Few-shot 样本要精不要多。** Fidelity 在 AWS re:Invent 2025 分享里有个反直觉发现（据第三方转述）：100+ 个样本效果反而不好，最终精简到 30 个精选样本。每个样本必须有存在的理由——覆盖一种 SQL 模式、展示一种 join 策略、演示一种聚合方式。

**警惕静默失败。** 查询能执行但返回错误结果，比查询直接报错更危险。建立验证机制：EXPLAIN 检查执行计划、LLM-as-a-judge 对比结果集分布、异常值检测。

**混合架构是终局，但不要一步到位。** 先用语义层覆盖核心 KPI，再用直接 SQL 处理长尾。两者共享同一个执行引擎和权限体系，用户不需要知道背后走的是哪条路径。

## 十、准确率之外

两个数字摆在一起：Spider2-snow 的官方榜单上，裸 schema 的 DAIL-SQL + GPT-4o 是 2.2%，语义层中介的 SMQ 方案是 94.15%。前面说过，这不是同模型的 A/B，SMQ 换了新一代基座，代差掺在差距里。但同一条企业级赛道上的断层仍然成立：让 LLM 直接生成物理 SQL，幻觉列名、记错 JOIN 这类错误永远有发生的通道，模型换代只能压低它们的频率；让 LLM 只选语义层实体，物理标识符全部交给确定性编译器，这一整类错误被结构性地移出了解空间。

更根本的变化是任务定义被重新设计了。Text-to-SQL 让 LLM 做它不擅长的事（在噪声中导航物理 schema、记住复杂的 join 关系、保证 SQL 语法和语义的双重正确）。Text-to-Metric 让 LLM 做它擅长的事（理解自然语言意图、在有限选项里做选择），然后把不擅长的部分交给确定性引擎。

这其实是一个通用的工程原则：不要和工具的短板较劲，把任务重新定义到工具的长板上。LLM 的长板是语义理解和模糊匹配，短板是精确计算和确定性执行。语义层的设计恰好利用了长板、规避了短板。

Spider 2.0 把各家框架统统压在 5.7% 到 21.3% 之间，暴露的不是某个模型的失败，是任务定义方式的失败。当架构从"让 LLM 写 SQL"变成"让 LLM 理解意图 + 确定性引擎写 SQL"，准确率不是线性提升，是阶跃。

这也是分层协作成为终局的原因，而不是"语义层取代直接 SQL"。因为有些查询的本质就是探索性的——用户自己都不确定想看什么，这时候让 LLM 自由生成 SQL 反而更合适。好的架构不是选一条路线，而是在正确的场景用正确的工具。

---

*参考来源：*

- *Spider 2.0: Evaluating Language Models on Real-World Enterprise Text-to-SQL Workflows — arXiv:2411.07763 (ICLR 2025 Oral)*
- *A Semantic-Layer-Mediated Agent for Natural Language to SQL over Heterogeneous Enterprise Databases — arXiv:2606.31041 (2026)*
- *CHASE-SQL: Multi-Path Reasoning and Preference Optimized Candidate Selection — arXiv:2410.01943 (ICLR 2025)*
- *XiYan-SQL: Multi-Generator Ensemble Framework — arXiv:2411.08599；期刊扩展版 arXiv:2507.04701 (IEEE TKDE)*
- *DIN-SQL: Decomposed In-Context Learning of Text-to-SQL with Self-Correction — arXiv:2304.11015 (NeurIPS 2023)*
- *RESDSQL: Decoupling Schema Linking and Skeleton Parsing — arXiv:2302.05965 (AAAI 2023)*
- *MAC-SQL: A Multi-Agent Collaborative Framework for Text-to-SQL — arXiv:2312.11242 (COLING 2025)*
- *Arctic-Text2SQL-R1 — Snowflake Technical Blog (2025.05)，arXiv:2505.20315*
- *A Survey of Text-to-SQL in the Era of LLMs — IEEE TKDE vol.37, pp.5735-5754 (2025)*
- *Next-Generation Database Interfaces: A Survey of LLM-based Text-to-SQL — IEEE TKDE (2025)*
- *LinkedIn: Text-to-SQL for Enterprise Data Analytics — arXiv:2507.14372*
- *LinkedIn Engineering Blog: Practical Text-to-SQL for Data Analytics — 2024.12*
- *Uber Engineering Blog: QueryGPT — 2024.09*
- *Salesforce Blog: Build a Semantic Layer Your AI Agents Can Reason Over — 2026.05*
- *Semantic Layer vs. Text-to-SQL: 2026 Benchmark Update — docs.getdbt.com (2026.04)*
- *Fidelity Investments: Text-to-SQL for data analytics at enterprise scale — AWS re:Invent 2025 (IND3323)，数据据 zenn.dev 第三方转述*
- *nvBench: A Large-Scale Synthesized Dataset for Cross-Domain Natural Language to Visualization Task — arXiv:2112.12926（SIGMOD 2021 首发基准的数据集扩展版）*
- *nvBench 2.0: Resolving Ambiguity in Text-to-Visualization through Stepwise Reasoning — arXiv:2503.12880 (2025)*
- *Automated Data Visualization from Natural Language via LLMs: An Exploratory Study — arXiv:2404.17136*
- *DB-GPT — github.com/eosphoros-ai/DB-GPT*
- *Vanna — github.com/vanna-ai/vanna*
- *WrenAI — github.com/Canner/WrenAI*
