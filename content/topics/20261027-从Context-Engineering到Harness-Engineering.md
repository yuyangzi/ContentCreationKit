# 从 Context Engineering 到 Harness Engineering：三代术语演进与两个新失败模式

## 类型标签

`#上下文工程` `#Harness` `#Agent工程` `#长程任务` `#ContextInertia` `#FightingtheWeights` `#术语演进`

## 主线

2026 年 10 月 24 日，Drew Breunig（O'Reilly《The Context Engineering Handbook》作者、Cmpnd 联合创始人）在 Linux Foundation 旗下 AGNTCon 大会发表演讲《Context Fails & Fixes》，整理成《The State of Context Engineering》一文。10 月 25 日登上 Hacker News，检索时 263 分、64 条评论（Algolia API，2026-10-27 实查）。文章给出一条清晰的三代演进线：2023 prompt engineering → 2025 context engineering → 2026 harness engineering。名字换了三代，靶心没变——把组装上下文的工作，从概率性的模型调用一步步挪进确定性的代码。而当行业目标转向"让模型自己驱动 harness 跑长程任务"，两个新的失败模式浮出水面。

## 第一部分：三代演进，一个不变的靶心

| 年份 | 术语 | 含义 |
|------|------|------|
| 2023 | Prompt Engineering | 选对词和示例，从单次模型调用里要到想要的输出 |
| 2025 | Context Engineering | 动态地把正确信息装进上下文窗口 |
| 2026 | Harness Engineering | 设计脚手架、编排和工具，从 Agent 应用里要到想要的输出 |

Breunig 的总结："我们只是把越来越多组装上下文的工作，从概率性模型调用挪到了确定性代码。"六项战术（context augmentation、tool loadout、context quarantine、context pruning、context summarization、context offloading）拼进 agent loop 大约只要 16 行改动——"真正不简单的是我们的语言"。

### 2024：长上下文承诺与四种失败模式

"RAG is dead"时代的承诺是把整个互联网塞进上下文。Gemini 1.5 的百万 token 窗口、Llama 4 Scout 的千万 token 窗口都没能兑现"塞进去就解决"。Breunig 归纳了四种失败模式：

- **Context poisoning**：错误信息进入上下文后被反复引用。典型案例：Gemini 2.5 玩《宝可梦 FireRed》时，"给守卫拿茶"这个任务在权重里，污染了上下文——模型花了数小时找茶，进 to-do 列表后就再也出不来
- **Context distraction**：上下文越长，模型越盯着上下文、越忽略基座知识。Camassa & Shiller 的论文《Do as I Say, Not as I Do》（arXiv 2605.20382）显示：反例示例累积会持续侵蚀指令遵循率，Opus 4.6 撑得久一些，但同样会倒下
- **Context confusion**：无关信息拉低回答质量
- **Context Clash**：新信息与工具互相冲突

还有埋在 Gemini 2.5 技术报告附录里的观察：上下文显著超过 10 万 token 后，Agent 开始重复历史动作而不是综合新计划——"我确信市场部的人从没读过附录"。

### 2026：长程任务成为新坐标

METR 的长程任务时长曲线：GPT-5 约 3.4 小时 → Gemini 3.1 约 6.4 小时 → Opus 4.6 约 12 小时（均为带 harness 的成绩）。行业叙事从"把上下文做大装下一切"变成"教会模型驱动 harness、管理自己的上下文"。

## 第二部分：两个新失败模式

### Fighting the Weights（对抗权重）

模型被训练成特定工具与环境的使用者，对训练分布之外的工具存在偏见。小模型（Haiku、Luna 一类）用 Playwright MCP 常在第一次调用时翻车再自我纠正。更直观的证据是 Claude Code 的 system prompt：关于"并行工具调用"的叮嘱重复出现 7 次、4 次、3 次、2 次——"当你打开 prompt 看到重复和全大写，多半是在 fighting the weights"。

### Context Inertia（上下文惯性）

模型对上下文里的某个假设、子任务或目标过度聚焦，在应该停止之后仍然继续推进。Breunig 称这个问题"上周同时被四方独立记录"：

- Anthropic：Memento（针对长程运行中"agent 固着于错误想法"的缓解设计）
- Microsoft Research：Fork-and-Flush（Jack Cai、Christos Ziakas）
- Stanford：Stateless Language Agents（Qizheng Zhang）
- UC Berkeley：Scaling Discovery Requires Forgetting（Shangyin Tan）

这两个失败模式的共性：它们都出现在"模型驱动 harness 跑长程"的新范式里，是长程 Agent 的原生故障，不是单次调用的 prompt 问题。

## 热度背景

- HN 263 分、64 条评论（Algolia API 2026-10-27 实查），10-25 提交
- 原文是 AGNTCon（MCPCon North America 同场）现场演讲转写，O'Reilly 新书《The Context Engineering Handbook》作者署名
- Austen Allred 等 AI 圈大 V 转发解读，多个二次解读站点跟进（检索信号）

## 创作方向建议

1. **三代术语消亡史 + Harness 深读**（推荐）：以 prompt→context→harness 为主线，讲清"确定性代码吃掉概率性调用"这一条不变的工程规律，收尾落在两个新失败模式——与已发的 agent-harness、agent-context-management 形成系列呼应
2. **Context Inertia 专文**：四方同周发表是罕见信号，说明长程 Agent 的"固着故障"已成公认问题；可与 checkpoint、断点续跑、记忆管理文章串成"长程任务如何不跑偏"专题
3. **Fighting the Weights 的工程含义**：system prompt 里的重复与全大写是诊断信号，harness 工程师如何在不改模型的前提下绕过训练偏见

## 可回溯来源

- 原文（Drew Breunig，2026-10-24）：https://www.dbreunig.com/2026/10/24/the-state-of-context-engineering.html
- Hacker News 讨论（263 分 / 64 评论）：https://news.ycombinator.com/item?id=50235780
- 《Do as I Say, Not as I Do》（arXiv 2605.20382）：https://arxiv.org/abs/2605.20382
- Breunig 前作《Context Inertia》（2026-10-14）：https://www.dbreunig.com/2026/10/14/context-inertia.html
- Breunig 前作《Don't Fight the Weights》（2025-11-11）：https://www.dbreunig.com/2025/11/11/don-t-fight-the-weights.html

## 交叉参考

- `content/article/20260723-agent-harness.md` — 已发 harness 生产骨架，本主题补"术语演进 + 新失败模式"视角
- `content/article/20260809-agent-context-management.md` — 上下文管理的既有梳理，本篇是其 2026 年更新版框架
- `content/article/20260717-Claude Code记忆系统-减法哲学.md` — 减法哲学与 context pruning / summarization 同源
- `content/article/20260726-agent-memory-management.md` — 记忆三层进化，与 compaction、quarantine 呼应
- `content/topics/20261012-Agent信任危机-从benchmark打脸到权限失控.md` — 其 2026-10-27 更新区块的 compaction 论文与本篇"新失败模式"直接相关
