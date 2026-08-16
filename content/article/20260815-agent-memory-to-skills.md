# 当 Agent 开始"长本事"：从记忆到可复用技能的进化路径

> **导读**：前一篇《向量检索不是记忆》讨论过 Agent 记忆系统的三层进化——Storage、Reflection、Experience。procedural memory（程序性记忆，即"怎么做的"知识）是最后一层，也是最容易被误解的一层：很多人以为给 agent 接上一个技能库就等于给它装了"长期记忆"，但这个判断是错的。
>
> 技能库解决的是另一件事：把一次成功的轨迹变成可复用的程序性单元。2023 年 Voyager 在 Minecraft 里把它做成了可执行代码库，2025 年 Anthropic 把它做成了开放标准，2026 年 8 月 ContinualSkillBench 抛出一个让人警醒的问题：技能库真的在让 agent 变强吗？这篇文章走完机制、工程、反思三段旅程。

2026 年 8 月，一个叫 ContinualSkillBench 的基准测试（arXiv:2608.03874）悄悄上线。研究者构建了横跨五个领域的连续任务序列，对比"会维护技能库的 agent"和"纯靠 in-context learning（把示例塞进当前提示窗口学习）的 agent"。预印本的结论写得很克制：in-context learning 和显式技能维护的平均表现相当，能力提升更多来自对前文上下文和反馈的适应，而非真正的可复用技能抽象。

这件事让 2025 年押注 Agent Skills 赛道的人心里一紧。Anthropic 在 2025 年 10 月发布 Claude Skills，同年 12 月 18 日将其升级为开放标准；Devin 在 2026 年把仓库级技能发现做成了默认能力；国内 SkillHub、阿里云 OpenSearch 几乎同时上线技能管理 API。ContinualSkillBench 的结论意味着这条赛道的基础假设被直接拷问。

更准确的判断是：技能库这条路没有被高估，但被严重误解。它的位置不在"让 agent 变强"，而在"让一次成功的经验变得可复用"。这两件事看起来像同一件事，实际上指向两条不同的工程路径。

本文分三段：机制（Voyager 范式怎么把经历变成能力）、工程（Anthropic Skills 和 Letta 怎么把它塞进生产系统）、反思（什么时候该上技能库，什么时候不该上）。

---

## 一、机制：Voyager 范式怎么把"经历"变成"能力"

### 1.1 一篇论文，三个组件

2023 年 5 月，NVIDIA、加州理工和 UT Austin 的一支团队把一篇论文挂上 arXiv（2305.16291），让 GPT-4 进了 Minecraft。

这篇 Voyager 论文之所以重要，不是因为它做出了一个能在 Minecraft 里活下来的 agent，而是它把"agent 怎么从经验里长出能力"这件事拆成了三个可以独立分析的组件：

1. **Automatic Curriculum（自动课程）**：以"尽可能发现多样事物"为总目标，用 GPT-4 基于 agent 当前状态（背包、装备、附近方块、生物群系、血量/饥饿、位置）、已完成/失败任务列表，自底向上持续提议下一个任务。本质是 in-context 形式的 novelty search（新颖性搜索：奖励"没见过的事物"而不是"完成度"）。消融实验显示换成随机课程，发现物品数下降 93%。

2. **Skill Library（技能库）**：一个持续增长的向量数据库，存储"可执行代码形式的复杂行为"。每个 skill 是一个 JavaScript 函数（如 `craftStoneShovel()`、`combatZombieWithSword()`），具备三个性质：
   - temporally extended（时间上可扩展，能完成多步子任务）
   - interpretable（可解释，代码就是文档）
   - compositional（可组合，多个 skill 可以拼接出更复杂的 skill）
   
   消融实验显示移除技能库，agent 后期会出现能力平台期（platformed，无法解锁新科技）。

3. **Iterative Prompting Mechanism（迭代提示机制）**：以代码为动作空间，通过三类反馈迭代改进程序：环境反馈（`bot.chat()` 输出的中间进度，比如"我需要 7 个铁锭才能做铁胸甲"）、执行错误（JavaScript 解释器报错 trace）、自验证（另一个 GPT-4 实例充当 critic，判定任务是否完成；失败时还给出改进建议）。每轮"执行→反馈→再生成"循环，直到自验证通过或达到 4 轮上限。4 轮未通过则换任务，失败任务记录进课程上下文供后续决策参考。消融实验显示移除自验证，**发现物品数下降 73%**——三类反馈里最关键的一环。

Voyager 在 3.3× 更多独特物品、2.3× 更长移动距离、解锁科技树里程碑快 15.3× 这组数据上，在实验对比的各 baseline 中全面领先。重点是，**技能库作为 procedural memory 的一种工程实现，极早就在长周期任务上跑通了**。

### 1.2 Skill Library 的数据结构

```python
class SkillManager:
    """Voyager 风格的可执行技能库：描述用于检索，代码用于执行"""
    def __init__(self, retrieval_top_k=5):
        self.skills = {}                        # 技能名 → {code, description}
        self.vectordb = Chroma(...)             # 向量索引：description → skill name
        self.retrieval_top_k = retrieval_top_k  # 每次检索返回 top-5

    def add_new_skill(self, program_name, program_code):
        # 只有 critic 判定任务成功才调用此方法（沉淀时机受验证守门）
        if program_name in self.skills:
            self.vectordb.delete(ids=[program_name])  # 同名覆盖
        # 描述由 LLM 独立生成，专供检索用——代码与描述分离
        skill_description = self.llm.describe(program_code)
        self.vectordb.add_texts(
            texts=[skill_description], ids=[program_name],
            metadatas=[{"name": program_name}]
        )
        self.skills[program_name] = {
            "code": program_code, "description": skill_description
        }

    def retrieve_skills(self, query):
        k = min(self.vectordb.count(), self.retrieval_top_k)
        if k == 0: return []
        docs = self.vectordb.similarity_search(query, k=k)
        # 检索的是 description，返回的是可执行代码
        return [self.skills[doc.metadata["name"]]["code"] for doc in docs]
```

这个数据结构的精妙之处在于**"代码"和"描述"分离**。代码是给 Minecraft 解释器执行的，描述是给 LLM 检索用的——两边各司其职。`add_new_skill` 的调用条件被严格约束（critic 判定 success=True），这是整个机制运转的关键闸门。

### 1.3 转化流程：5 步完成一次"记忆→技能"

把上述组件串起来，Voyager 完成一次"经历→能力"转化的流程是：

1. **课程提议任务**：Automatic Curriculum 根据当前状态 + 已完成/失败历史，提议下一个任务
2. **检索相关技能**：用任务建议 + 环境反馈的 embedding 查库，取 top-5 注入 prompt
3. **迭代生成代码**：GPT-4 生成 → 执行 → 收集环境反馈/执行错误 → 再生成，循环
4. **自验证守门**：critic GPT-4 判断成功/失败；失败给 critique 继续迭代，最多 4 轮
5. **沉淀为技能**：验证通过 → LLM 生成描述 → embedding 索引 → 写入 Skill Library

失败经验不会被直接沉淀为 skill。失败轨迹通过三类反馈进入下一轮代码生成；4 轮仍失败则放弃该任务，失败记录进课程上下文供后续决策参考。**只有 critic 通过的代码才进技能库**——这是 Voyager 和绝大多数后续 skill library 范式共享的"沉淀守门条件"。

### 1.4 学术同侪：技能的可执行性梯度

Voyager 不是孤例。同期的 ExpeL（arXiv:2308.10144）、2024 年的 AWM（arXiv:2409.07429，ICML 2025 收录）、更早的 Generative Agents（arXiv:2304.03442，UIST '23）都在解决同一个问题——从经验里长出可复用的东西，产物形态却差别很大：

| 系统 | 产物形态 | 转化机制 | 检索方式 | 验证机制 |
|------|---------|---------|---------|---------|
| **Voyager** | 可执行 JS 代码 | 实时 + critic 守门 | 向量 top-5 | **自验证 critic**（最严格） |
| **ExpeL** | NL 规则 + insights | 离线归纳 + 投票 | kNN 轨迹 | importance count 投票软淘汰 |
| **AWM** | 工作流 + 占位符 | LM 归纳 | 全量注入 | LM 评估器 |
| **Generative Agents** | 反思树（认知层） | 阈值 150 触发 | 加权混合 | 无验证 |

四者构成一条"可执行性梯度"——Voyager 的产物能直接执行、组合；ExpeL 的产物是自然语言规则，能指导决策但不可直接执行；AWM 是半抽象动作序列；Generative Agents 的反思只是"信念层"，不直接指导动作。

这条梯度的工程含义很清楚：**可执行性越强，沉淀的门槛越高**。Voyager 的 critic 守门最严，因为 JavaScript 错了就崩；Generative Agents 的反思几乎无门槛，因为它影响的是 agent 的"想法"而不是"动作"。门槛低不等于没用，但门槛低意味着你得自己设计质量过滤——否则低质量的反思会塞满库。

---

## 二、工程：把技能库塞进生产系统

学术范式能跑通不意味着能上生产。Voyager 的 skill 库无限增长，而 2026 年 Skill Shadowing 论文（arXiv:2605.24050）的实验数据显示，库规模从几十个扩到两百个左右时通过率不升反降。Voyager 的离线 Minecraft 环境不会撞上生产环境的高并发、多用户、外部 API 演化等问题。

工业界三年里摸索出一套可用的工程方案。三个项目代表了三种不同思路。

### 2.1 Anthropic Skills：把技能做成开放标准

2025 年 10 月，Anthropic 发布 Claude Skills（agentskills.io 规范，2025-12-18 升级为开放标准）。核心设计叫"渐进披露"（progressive disclosure）：

- **Level 1：metadata**（name + description）常驻 context，约 100 tokens/skill。模型启动时只看这一层判断"该不该触发"
- **Level 2：SKILL.md 正文**——触发后才加载全文，<500 行
- **Level 3：references/scripts/assets**——按需加载，脚本可直接执行不进 context

这套设计直接解决了技能库的"路由成本"问题。Anthropic 官方文档里有一句很直接的话："The description is critical for skill selection: Claude uses it to choose the right Skill from potentially 100+ available Skills"。**description 写不好，skill 基本不会被触发**。

Anthropic 同时给出了一个反直觉的工程建议——描述要"略 pushy"（pushy 即语气上主动推销自己）。原因是模型有"欠触发"（undertrigger）倾向，描述写得保守就不会被选中。官方 skill-creator 文档里给了一个示范：

> "Make sure to use this skill whenever the user mentions dashboards, data visualization, or internal metrics, even if they do not explicitly ask for a dashboard."

工程团队最该记住的描述写法（来自 Mem0 的 SKILL.md 规范）：

```yaml
name: mem0
description: >
  Mem0 Platform SDK for adding persistent memory to AI applications.
  TRIGGER when: user mentions "mem0", "MemoryClient", "memory layer",
  "remember user preferences", "persistent context", "personalization"...
  DO NOT TRIGGER when: user asks about CLI commands, terminal usage,
  or Vercel AI SDK (use mem0-vercel-ai-sdk).
```

"TRIGGER when" 和 "DO NOT TRIGGER when" 是显式写出来的触发词和排除词。这种写法在 Anthropic 官方和开源社区里是事实标准。一个常见反例是"helper""utils""documents"这种泛化命名，检索时大多候选近似等价，选择退化为随机。

### 2.2 Letta：最完整的"技能进化"实现

Letta（前身 MemGPT）在 2025 年 12 月公开了 Skill Learning 机制，TerminalBench 2.0 上的对照数据是 **+36.8% 相对提升**（15.7% 绝对）。这套机制值得拆开看，因为它代表了"技能进化"四个字最完整的实现：

- **reflection 子代理**后台运行，审查 agent 完成的每条轨迹
- **沉淀五操作**：`update > extend > deprecate > split > create`（优先修改现有 skill 而非新建）
- **双源学习**：轨迹本身 + verifier 失败文本反馈。论文数据：轨迹学习约 +21% 相对提升，加上失败反馈再贡献 6.7 个百分点
- **MemFS git 追踪**：所有 memory 和 skill 都进 git，可回滚、可同步

关键在优先级排序——`update > extend > deprecate > split > create`。这条顺序背后的逻辑是"先复用、再细分、最后才新建"，恰好是 Voyager（只 create）和 Letta（五操作）最核心的差异。Voyager 那种只增不删的库会撞上 skill shadowing，Letta 的 deprecate 机制是解药。

Letta 的 reflection 子代理还有一条隐含规则："Skills are not the default... Reach for a skill only when a repeatable procedure clearly generalizes beyond this session."——**技能不是默认选项**，只有当一个流程明确能跨会话复用时才沉淀成 skill。这条规则和 SkillsBench（Anthropic 基准，arXiv:2602.12670）的实证一致：人工策展的技能平均 +16.2pp，自生成技能收益≈0。

### 2.3 Mem0：技能之前的记忆底座

Mem0（arXiv:2504.19413，ECAI 2025）严格说不算 skill library 系统，而是"记忆层基础设施"——它解决的是上一篇文章讨论的 Storage 层。但把它放进本文是因为它示范了"技能之前的工程基线"该长什么样：多信号检索（语义 embedding + BM25 关键词 + 实体匹配并行打分），GitHub 63.2k stars（截至 2026 年 8 月）。Mem0 在自己的 `skills/` 目录里提供结构化 SKILL.md 范本，是目前 description 工程化做得比较完善的开源范例（前面那段 TRIGGER/DO-NOT-TRIGGER 就是从 Mem0 拿来的）。

把三个项目放在一起看，工业界的共识是这样的：

- **Anthropic Skills** 解决"技能怎么被发现"——渐进披露
- **Letta** 解决"技能怎么被维护"——五操作 + reflection
- **Mem0** 解决"技能之前的数据底座"——多信号检索

三个项目刚好对应了技能库工程的三个缺口。

### 2.4 关键工程决策

结合三个项目的实践与 Agent Skills 综述（arXiv:2602.12430）的归纳，整理成 5 条生产验证过的工程建议：

1. **description 是路由层，不是文档层**。~100 tokens/skill 常驻预算，模型有欠触发倾向，写法公式："what + when + 关键词 + 排除条款 + 略 pushy"
2. **沉淀必须过质量门**。SkillsBench 已验证自生成技能收益有限、策展技能提升显著；Letta 证明"轨迹+失败反馈"双源更有效（+36.8%）
3. **检索采用两阶段**：向量召回缩小候选 + LLM 最终裁决。Graph-of-Skills 等工作验证了结构化检索在大规模库上的优势
4. **沙箱是文件系统 + 网络双隔离**。Anthropic 官方（*Claude Code Sandboxing*）明确："Without network isolation, a compromised agent could exfiltrate SSH keys; without filesystem isolation, a compromised agent could escape the sandbox"。2026 年初 ClawHavoc 供应链攻击中，Antiy CERT 确认 1,184 个恶意技能渗入 OpenClaw 的 ClawHub 技能市场，验证了这条警告不是过度防御
5. **维护层是独立组件**。SkillOps 论文（arXiv:2605.13716）显示库维护在 ALFWorld（文本具身智能任务基准）上 +8.8pp 成功率，零额外 task-time LLM 调用。merge（合并）/ retire（废弃）/ repair（修复）三操作是事实标准

### 2.5 避坑：规模化的三大陷阱

技能库从 demo 走到生产的路上有三个最容易踩的坑。

**坑一：技能爆炸（Skill Explosion）。** Skill Shadowing 论文（arXiv:2605.24050）的实验显示，平铺向量检索在库规模约 60–120 个技能时出现退化拐点，200+ 时通过率下降 21%。退化的主因不是"context 变大了"，而是"选错技能"——论文把退化效应拆解为 shadowing（选择失败）和 context overhead 两种，实测前者显著、后者≈0。解药是依赖感知检索（Graph-of-Skills 论文 arXiv:2604.05333 用 reverse-weighted Personalized PageRank 补齐技能前置链），以及独立的 merge/retire 维护层。

**坑二：description 缺失或糟糕。** SkillReducer 论文（arXiv:2603.29919）对 55,315 个公开 skill 的分析：26.4% 的 skill 缺失或描述过短（≤40 tokens），直接破坏路由机制。description 是决定"这个 skill 值不值得被加载"的唯一信号——误触发一个数千 token 的大 skill 会直接推高成本。解药是按 2.1 节的写法公式 + 2-3 个真实 prompt 做触发测试（"该触发时触发、不该触发时不触发"）。

**坑三：把"知识"当"技能"沉淀。** CrewAI 官方明确区分："Skills are NOT tools... If the agent needs to follow a process, use a skill. If the agent needs to reference data, use knowledge"。事实和偏好该进 memory（Mem0 管），原子动作该做成 tool（function calling 管），**技能库不是代码或文档的 dump，只有"可重复的多步流程"才进 skill**。把公司文档全做成 skill 的人，技能库最后会膨胀到几 MB，每个 skill 的 description 都退化。

---

## 三、反思：技能库真的有效吗？

但 ContinualSkillBench 提出的核心命题仍然值得审视：技能库是否真的提升了 agent 的基础能力。

### 3.1 质疑派：ContinualSkillBench 的拷问

ContinualSkillBench 的设计很有针对性——它专门测"agent 是否真的进化了能力"，而不是"agent 是否积累了更多可复用单元"。对照组是"in-context learning 模式"：同样的轨迹不进技能库，而是塞进当前会话的 prompt。

实验数据显示，技能维护的收益随模型能力差异很大：

1. **强模型上收益有限**——GPT-4 / Claude Opus 这类基础能力够强的模型，技能库对最终通过率的贡献不显著
2. **弱模型上可能反而有害**——能力较弱的模型积累出"更大更碎"的技能集，检索精度下降，反而拖累决策

这组数据并不是说"技能库没用"，而是说"技能库解决的问题不是让 agent 变强"。强模型本来就能在 in-context 里做好；弱模型无法从混乱的技能库里筛选出有用的那一条。**技能库的位置在中间地带——它帮的是"经验从一次性变成可复用"这件事，而不是"agent 的基础能力"。**

### 3.2 反向证据：Skill Shadowing

Skill Shadowing 论文（arXiv:2605.24050）从另一个角度提供了反向证据。研究者把一个技能库从 0 扩到 202 个技能，过程中持续观察 agent 通过率：

- 库从 0 扩到 ~50：通过率持续上升
- 库从 ~50 扩到 ~100：上升趋缓
- 库从 ~100 扩到 202：通过率**下降 21%**

退化的根因被精确归因：**选错技能（shadowing）**。每个候选技能被错误选中的概率随候选集规模增长，shadowing 的成本超过"找到正确技能"的收益。context 膨胀（把所有 skill 都塞进 prompt）的贡献几乎为 0。

这组数据对工程团队的启示很直接：**技能库不是"越多越好"的资源池，而是"少而精"的能力仓库**。扩容之前先优化单 skill 的命中率；扩容之后维护层就是必需品。

### 3.3 重新判断"什么时候有效"

把前面的分析合起来，能给出一个判断框架。技能库在以下三种场景里最有效：

1. **领域内有大量重复模式，且模式可被 LLM 自动归纳**——代码助手、SQL 生成、文档处理这类任务，单次成功的代码片段提炼成 skill 后能被反复调用
2. **基础模型能力已经够用，工程重点在"调用一致性"**——比如客服 agent 已经能用 GPT-4 处理 90% 的对话，剩下的工程重点是让同样的输入稳定触发同样的流程
3. **存在"质量门"机制**——critic 守门、verifier 验证、人工策展（SkillsBench 数据 +16.2pp 来自人工策展）三选一至少要有一个，否则自生成技能会污染库

反过来，下面三种场景里技能库大概率是负收益：

1. **基础模型还不够强**——弱模型无法利用好的 skill，反而被噪声技能干扰
2. **任务高度多样化，没有重复模式**——检索召回率天然低，每次都触发错技能
3. **流程一次性**（比如一次性数据迁移、一次性报表生成）——沉淀成 skill 没有复用场景。Letta 的"Reach for a skill only when a repeatable procedure clearly generalizes beyond this session" 就是给这种情况画的边界

判断要不要上技能库的快速 checklist：你的任务里"成功的轨迹"是否能被 LLM 自动归纳成可复用单元？如果不能，别上。如果能，再看是否有 critic 守门——没有也别上。

### 3.4 开放问题：记忆与技能会不会融合

2026 年 2 月的 MemSkill 论文（arXiv:2602.02474）提出了一个有意思的方向——把"记忆操作本身"也变成可进化的技能库。controller 选技能、executor 构造记忆、designer 从难例精炼/新增技能，整个流程走 PPO（Proximal Policy Optimization，一种强化学习算法）训练闭环。如果这条路走通，"记忆怎么记"和"技能怎么用"会变成同一层抽象。

类似的趋势还有 ERSkill（arXiv:2608.12720）——把检索行为编码为可执行技能，agent 的"怎么检索"和"怎么执行任务"在同一个库里管。这条路线目前还在论文阶段，2026 年下半年可能会有开源框架出现。

这条路线如果真的跑通，procedural memory 和 skill library 这两个在 CoALA 框架里分属不同象限的东西，会在工程上合并成一层。这对一线开发者是远期问题，但对做技术路线规划的团队可能成为中期变量。

---

## 结语：技能不是记忆的升级品

回到开头的判断。技能库这条路没有被高估，但被严重误解——很多人把"技能库"当成"记忆系统的最后一站"，以为它能把 agent 从"记不住东西"升级到"能记住东西还能用上"。这个判断是错的。

技能库解决的是另一件事：**让一次成功的经验变得可复用**。它不解决"agent 的基础能力"，不解决"知识的新鲜度"，不解决"流程的自动化"。它解决的是"我刚才这段代码是对的，下次遇到类似任务我能不能直接调出来"。这个价值真实存在，但价值的位置不在"让 agent 变强"，而在"降低重复劳动的边际成本"。

把这个判断和上一篇文章放在一起看就更清楚。2026 年 7 月那篇文章指出"向量检索不是记忆"，因为记忆有写入路径。今天这篇文章说"技能库不是 code dump"，因为技能库有验证守门。两句话的共同点是：**不把"看起来像"等同于"是"**。向量检索看起来像记忆但不是；技能库看起来像 code dump 但不是。把这些"看起来像"的混淆剥开，剩下的工程问题才真正变得可解。

下一个值得追的问题是 3.4 节提到的记忆-技能融合。如果这条路在 2027 年跑通，procedural memory 和 skill library 的边界会被改写——那时候再回看 2023 年的 Voyager，可能会像今天回看 2017 年的 Transformer 一样：它打开了一扇门，但门后面的样子和它最初设想的不一样。

*参考来源：*
- Wang et al. "Voyager: An Open-Ended Embodied Agent with Large Language Models", [arXiv:2305.16291](https://arxiv.org/abs/2305.16291)
- Zhao et al. "ExpeL: LLM Agents Are Experiential Learners", [arXiv:2308.10144](https://arxiv.org/abs/2308.10144)
- Wang et al. "Agent Workflow Memory", [arXiv:2409.07429](https://arxiv.org/abs/2409.07429) (ICML 2025)
- Park et al. "Generative Agents: Interactive Simulacra of Human Behavior", [arXiv:2304.03442](https://arxiv.org/abs/2304.03442) (UIST '23)
- Chhikara et al. "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory", [arXiv:2504.19413](https://arxiv.org/abs/2504.19413) (ECAI 2025)
- Li et al. "SkillsBench: Benchmarking How Well Agent Skills Work", [arXiv:2602.12670](https://arxiv.org/abs/2602.12670)
- Liu et al. "SkillReducer: Optimizing LLM Agent Skills for Token Efficiency", [arXiv:2603.29919](https://arxiv.org/abs/2603.29919)
- Liu et al. "Graph-of-Skills: Dependency-Aware Structural Retrieval for Massive Agent Skills", [arXiv:2604.05333](https://arxiv.org/abs/2604.05333)
- Guan et al. "ContinualSkillBench", [arXiv:2608.03874](https://arxiv.org/abs/2608.03874)
- Song & Wei. "More Skills, Worse Agents? Skill Shadowing", [arXiv:2605.24050](https://arxiv.org/abs/2605.24050)
- Anthropic. "Equipping agents for the real world with Agent Skills", [anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
- Anthropic. "Claude Code Sandboxing", [anthropic.com/engineering/claude-code-sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)
- Letta. "Skill Learning: Building Agents that Get Better with Experience", [letta.com/blog/skill-learning](https://www.letta.com/blog/skill-learning)
- Sumers et al. "Cognitive Architectures for Language Agents (CoALA)", [arXiv:2309.02427](https://arxiv.org/abs/2309.02427)
- Xu & Yan. "Agent Skills for Large Language Models: Architecture, Acquisition, Security, and the Path Forward", [arXiv:2602.12430](https://arxiv.org/abs/2602.12430)
- Liu et al. "MemSkill", [arXiv:2602.02474](https://arxiv.org/abs/2602.02474)
- Zhang et al. "SkillOps", [arXiv:2605.13716](https://arxiv.org/abs/2605.13716)
- Chen et al. "ERSkill: Skill-Guided Adaptive Memory Retrieval", [arXiv:2608.12720](https://arxiv.org/abs/2608.12720)