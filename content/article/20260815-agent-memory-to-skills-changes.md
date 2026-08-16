# 润色改动清单：Agent 记忆到技能（conservative 模式）

- 草稿：`content/draft/20260815-agent-memory-to-skills.md`
- 文章：`content/article/20260815-agent-memory-to-skills.md`
- 模式：conservative（deep-tech）
- 日期：2026-08-16

## 改动清单

| # | 位置（草稿行号） | 改动前 | 改动后 | 类别 |
|---|---|---|---|---|
| 1 | L3（导读） | 整段导读为单段 blockquote | 拆为两段（"…这个判断是错的。" 结束第一段，"技能库解决的是另一件事…"起第二段） | 衔接 |
| 2 | L34 | …这组数据上把所有 baseline **全**压了下去。 | …这组数据上把所有 baseline **都**压了下去。 | 冗余 |
| 3 | L101 | Voyager 的 skill 库无限增长，2026 年 Skill Shadowing 论文… | Voyager 的 skill 库无限增长，**而** 2026 年 Skill Shadowing 论文… | 衔接 |
| 4 | L160 | **把**三个项目的实践、**结合** Agent Skills 综述（arXiv:2602.12430）的归纳，整理成 5 条… | **结合**三个项目的实践**与** Agent Skills 综述（arXiv:2602.12430）的归纳，整理成 5 条… | 衔接 |

**说明**

- 改动 #1：导读单段过长，拆为两段提升可读性；未改任何措辞。
- 改动 #2："所有…全" 双重强调冗余，改 "都" 去掉重复；未改数值（3.3×/2.3×/15.3× 不变）。
- 改动 #3：补 "而" 衔接前后两句对比关系；未改数据（几十/两百 不变）。
- 改动 #4：修正原句语法残缺（"把…结合…归纳" 双动词杂糅），改为 "结合…与…的归纳"；未改 arXiv 编号与措辞。

## 润色影响范围自检（conservative 强制）

自检项：数字、单位、arXiv 编号、URL、DOI、代码块、表格数据、专有名词英文原形、术语中文翻译。

| 元素 | 是否改动 | 检查结果 |
|---|---|---|
| 数字（93%、73%、3.3×、2.3×、15.3×、100 tokens/skill、<500、+36.8%、15.7%、+21%、6.7 个百分点、+16.2pp、≈0、63.2k、+8.8pp、21%、60–120、200+、26.4%、≤40、55,315、1,184、4、5、7、150、90%、202、50、100 等全部数字） | 否 | 未改动 |
| 单位（tokens、×、pp、%、GB/MB、top-5/top-k 等） | 否 | 未改动 |
| arXiv 编号（2305.16291、2308.10144、2409.07429、2304.03442、2504.19413、2602.12670、2603.29919、2604.05333、2608.03874、2605.24050、2309.02427、2602.12430、2602.02474、2605.13716、2608.12720） | 否 | 未改动 |
| URL / 链接（arxiv.org、anthropic.com/engineering、docs.letta.com） | 否 | 未改动 |
| 代码块（Python SkillManager、YAML mem0 description） | 否 | 未改动 |
| 表格数据（四个系统对比表） | 否 | 未改动 |
| 专有名词英文原形（Voyager、ExpeL、AWM、Generative Agents、Claude Skills、Letta、Mem0、SkillOps、MemSkill、ERSkill、ContinualSkillBench、SkillsBench、procedural memory、in-context learning、progressive disclosure、undertrigger、pushy、critic、reflection、shadowing、CoALA、PPO、MemFS、ALFWorld、TerminalBench 2.0、Antiy CERT、ClawHavoc、ClawHub、OpenClaw、CrewAI、Anthropic、Mem0 等） | 否 | 未改动 |
| 术语中文翻译（自动课程、技能库、迭代提示机制、新颖性搜索、渐进披露、技能爆炸、程序性记忆 等） | 否 | 未改动 |

**结论**：本次共 4 处改动，全部属于允许范围（衔接 ×3、冗余 ×1），未改动任何数据、引用、术语、表格、代码、公式。无超范围改动，无需回滚。

---

## review-article 阶段修改（2026-08-16）

审查命令产出 8 节检查报告，本轮执行全部修正建议。

### 修改清单（共 10 处）

| # | 位置 | 改动前 | 改动后 | 类别 | 优先级 |
|---|------|--------|--------|------|--------|
| 1 | L3（导读第一段） | 上一篇《向量检索不是记忆》里**我们走过一遍** | 前一篇《向量检索不是记忆》**讨论过** | 作者隐身 | 必须改 |
| 2 | L11 | **我自己的判断是**：技能库这条路… | **更准确的判断是**：技能库这条路… | 作者隐身 | 必须改 |
| 3 | L36 | 把**所有** baseline 都压了下去 | 在实验对比的各 baseline 中**全面领先** | 弱化绝对 | 必须改 |
| 4 | L241 | 2026 年 7 月**我们说**"向量检索不是记忆" | 2026 年 7 月**那篇文章指出**"向量检索不是记忆" | 作者隐身 | 必须改 |
| 5 | L184 | 但 ContinualSkillBench 那个核心问题还悬着：**技能库到底有没有让 agent 变强？** | 但 ContinualSkillBench 提出的核心命题仍然值得审视：**技能库是否真的提升了 agent 的基础能力。** | 设问修辞 | 建议改 |
| 6 | L150 | GitHub 63.2k stars | GitHub 63.2k stars**（截至 2026 年 8 月）** | 数据时效 | 建议改 |
| 7 | L167-168 | Anthropic 官方明确："Without network isolation…" | Anthropic 官方**（*Claude Code Sandboxing*）**明确："Without network isolation…" | 来源标注 | 建议改 |
| 8 | L168 | ALFWorld 上 +8.8pp 成功率 | ALFWorld**（文本具身智能任务基准）**上 +8.8pp 成功率 | 术语精确 | 建议改 |
| 9 | L231 | 是中期变量 | **可能成为**中期变量 | 弱化绝对 | 建议改 |
| 10 | 参考来源 L258 | [docs.letta.com](https://docs.letta.com) | [letta.com/blog/skill-learning](https://www.letta.com/blog/skill-learning) | 来源精确 | 必须改 |
| 11 | L70 | 这是整个机制**能跑通的守门人** | 这是整个机制**运转的关键闸门** | 措辞微调 | 可选改 |

### 修改影响范围自检

| 元素 | 是否改动 | 说明 |
|------|---------|------|
| 数字/单位 | 否 | 仅追加"截至 2026 年 8 月"时间锚，63.2k 数值不变 |
| arXiv 编号 | 否 | 全部 15 个编号未改动 |
| URL / 链接 | 是（1 处） | Letta 参考链接从 docs.letta.com 改为具体 blog 页，来源更精确 |
| 代码块 | 否 | 未改动 |
| 表格数据 | 否 | 未改动 |
| 专有名词英文原形 | 否 | 未改动 |
| 术语中文翻译 | 否 | ALFWorld 补充中文说明，非翻译改动 |

**结论**：本轮修改共 11 处，其中必须改 5 处、建议改 5 处、可选改 1 处。核心数据、引用、技术结论均未改动，修改集中在 StyleRule 合规性与表述精确性。