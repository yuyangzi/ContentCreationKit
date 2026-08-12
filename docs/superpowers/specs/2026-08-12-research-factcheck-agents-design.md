# research / fact-check 双 Agent 设计文档

**日期**：2026-08-12
**状态**：已批准（brainstorming 完成）
**作者**：Sisyphus + 用户

## 背景与动机

librarian agent（OhMyOpenCode 内置，模型 `qwen-plus-latest`）在 ContentCreationKit 中被大量用于外部数据研究/验证，但存在结构性错配：

1. **模型能力错配** — 数据验证需要强推理（arXiv 编号比对、数据层级辨析、定价页核实），qwen-plus 中端模型经常需要主 agent 二次复核
2. **定位错配** — librarian 原生定位是"代码库理解"（GitHub CLI + Context7 + Web Search），但项目 90% 用途是外部数据研究/验证
3. **验证纪律缺失** — AGENTS.md《数据验证规则》只在主 agent 记得手动塞进 prompt 时才生效
4. **工具未最大化** — 项目配置 8 个 MCP，librarian 只依赖通用 web search，不按任务类型选工具
5. **输出格式不统一** — librarian 自由格式输出，主 agent 需自行重排为结构化清单

## 决策记录

| 决策点 | 结论 |
|--------|------|
| 拆分 | 拆成两个 agent：研究搜集型 + 验证核实型 |
| 命名 | `research`（研究搜集型）/ `fact-check`（验证核实型） |
| 模型 | research → `sxzq-aliyun/aliyun/deepseek-v4-flash`；fact-check → `sxzq-aliyun/aliyun/deepseek-v4-pro` |
| 实现方式 | 方案 A：项目级自定义 agent（`.opencode/agents/`），**不依赖 oh-my-openagent**（模型直接写 frontmatter） |
| librarian 去留 | 保留，仅用于代码库理解场景 |
| 升级点 | 全部采纳：内置验证纪律、工具选择策略、结构化输出协议、多源交叉强制 |
| 验证纪律载体 | 方案 C 混合：关键铁律内嵌 prompt + 完整工作流引用 AGENTS.md 路径 |

## 架构

```
.opencode/agents/research.md     # 研究搜集型 → sxzq-aliyun/aliyun/deepseek-v4-flash
.opencode/agents/fact-check.md   # 验证核实型 → sxzq-aliyun/aliyun/deepseek-v4-pro
```

- 沿用项目现有 agent 模式（同 context-cover.md / visual-cover.md）
- frontmatter 直接写 `model:`，零 oh-my-openagent 依赖
- 4 个命令里的 librarian 引用替换为 research / fact-check
- librarian 保留（代码库理解场景继续用）

## Agent 1：research（研究搜集型）

**frontmatter**：`mode: subagent` + `model: sxzq-aliyun/aliyun/deepseek-v4-flash` + `description`

**服务场景**：`/find-popular-topics`（热点挖掘）、`/tech-research-write`（知识深度研究）

**内置纪律**：

1. **工具选择策略**：
   - 热点挖掘 → TrendsHub（12 平台热榜）+ BingSearch（中文社区）+ 抓原文
   - 知识研究 → Tavily/ExaSearch（深度检索）+ arXiv 优先
   - 跨平台去重归并（同一事件中英文源合并为一条候选）
2. **来源分级**：一手来源（官方博客/论文/定价页）> 权威二手 > 社区讨论；每条候选必须可回溯（URL）
3. **结构化输出协议**：
   - 热点候选表：标题 / 热度信号（⭐⭐⭐⭐⭐）/ 核心钩子（1-2 句卖点）/ 来源
   - 研究摘要：核心概念 / 关键来源（arXiv 编号+链接+日期）/ 最佳实践 / 常见误区 / 最新进展 / 代码示例
4. **不编造**：热度数据必须来自平台数据，禁止估算；找不到来源的候选标记"无来源"而非编造

## Agent 2：fact-check（验证核实型）

**frontmatter**：`mode: subagent` + `model: sxzq-aliyun/aliyun/deepseek-v4-pro` + `description`

**服务场景**：`/review-article`（文章数据验证）、`/review-reference`（参考资料核实）

**内置纪律**（混合载体 C）：

1. **关键铁律内嵌**（自包含）：
   - 6 类错误优先排查：日期错误 / 数字错误 / 来源归属错误 / 产品名错误 / 定价错误 / 不可验证数据
   - 来源分级：一手来源优先
   - "无法独立验证 → 删除，不留待验证标记"
   - 每个数据点 ≥ 2 个独立来源交叉验证
2. **完整工作流引用**：prompt 内指示"按 AGENTS.md《数据验证规则》章节执行完整交叉验证流程"
3. **工具选择策略**：
   - arXiv 编号 → ExaSearch / arxiv.org
   - 商业数据/定价 → Tavily / BraveSearch + 官方定价页
   - 中文来源 → BingSearch 交叉验证
4. **结构化输出协议**：固定清单格式——每条 claim 一行：`claim 原文 → 核实结果（✅/❌/⚠️）→ 证据来源（链接+日期）→ 建议改法`；最终附优先级清单（必须改/建议改/可选改）
5. **多源交叉强制**：单一来源一律标注"未交叉验证"

## 命令替换计划

| 命令 | 原引用 | 新引用 |
|------|--------|--------|
| `/find-popular-topics` | 1 × librarian | 1 × research |
| `/tech-research-write` | 3 × librarian | 3 × research（核心原理/最佳实践/最新进展） |
| `/review-article` | 3 × librarian (deep-tech) | 3 × fact-check（架构/商业数据/叙事） |
| `/review-reference` | 2 × librarian | 2 × fact-check |

命令文件中 `librarian` 措辞同步更新（如"派遣 librarian Agent"→"派遣 fact-check Agent"）。

## 验证计划

1. 两个 agent 文件创建后，先跑真实场景冒烟测试（对已有文章跑 fact-check；对 tech-research-write 跑 research）
2. 确认输出格式符合协议、模型生效、工具可用
3. 通过后再批量替换命令

## 范围边界

**范围内**：
- 创建 `.opencode/agents/research.md` 和 `.opencode/agents/fact-check.md`
- 更新 4 个命令文件中的 librarian 引用
- 冒烟测试验证

**范围外**：
- 删除或改造 librarian agent 本身（保留）
- 修改 oh-my-openagent.json（不依赖）
- 新增 MCP 服务
