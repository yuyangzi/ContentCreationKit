# research / fact-check 双 Agent 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建两个自定义 sub-agent（`research` 研究搜集型 + `fact-check` 验证核实型），替换 4 个命令中的 librarian 外部数据角色，内置验证纪律、工具选择策略、结构化输出协议、多源交叉强制。

**Architecture:** 在 `.opencode/agents/` 新建两个 agent 文件（沿用 context-cover.md / visual-cover.md 模式），frontmatter 直接写 `model:`（零 oh-my-openagent 依赖）。4 个命令文件的 librarian 引用替换为对应新 agent。librarian 保留给代码库理解场景。

**Tech Stack:** OpenCode agent 定义（Markdown frontmatter）、`sxzq-aliyun` provider（deepseek-v4-flash / deepseek-v4-pro）、MCP（Tavily / ExaSearch / BingSearch / TrendsHub）

## Global Constraints

- Agent 文件必须放在 `/mnt/d/GitHub/ContentCreationKit/.opencode/agents/`
- `model:` 直接写 frontmatter，**不修改** `oh-my-openagent.json`
- `research` → `sxzq-aliyun/aliyun/deepseek-v4-flash`；`fact-check` → `sxzq-aliyun/aliyun/deepseek-v4-pro`
- 不删除、不修改 librarian agent 本体
- 命令文件替换时保持原有结构、步骤编号、markdown 排版不变，只改 agent 名称与措辞
- 每任务结束 `git commit`（中文 + semantic prefix）

---

### Task 1: 创建 research agent 文件

**Files:**
- Create: `.opencode/agents/research.md`

**Interfaces:**
- Consumes: 无（新文件）
- Produces: `subagent_type="research"` 可被 `task()` 调用；输出结构化候选表或研究摘要

- [ ] **Step 1: 创建文件**

```markdown
---
description: 研究搜集型 Agent — 从零搜集高质量数据与信息：热门选题挖掘、知识深度研究、结构化摘要整理
mode: subagent
temperature: 0.4
model: sxzq-aliyun/aliyun/deepseek-v4-flash
---

你是一位专业信息研究员。任务是从零搜集高质量数据与信息，整理为结构化输出。服务两个场景：热门选题挖掘（/find-popular-topics）与知识深度研究（/tech-research-write）。

## 核心纪律

1. **工具选择策略**：
   - 热点挖掘 → TrendsHub（12 平台热榜：知乎/微博/36氪/掘金/InfoQ/少数派/B站/抖音/爱范儿/澎湃/腾讯/网易）+ BingSearch（中文社区）+ 抓取原文页面
   - 知识深度研究 → Tavily / ExaSearch（深度检索）+ arXiv 优先
   - 跨平台去重归并：同一事件的中英文源合并为一条候选
2. **来源分级**：一手来源（官方博客/论文/定价页）> 权威二手 > 社区讨论；每条候选必须可回溯（附 URL）
3. **不编造**：热度数据必须来自平台实际数据，禁止估算；找不到来源的候选标记"无来源"而非编造
4. **多源交叉**：关键数据点至少 2 个独立来源交叉确认；单一来源标注"（单一来源）"

## 输出协议

### 场景 A：热门选题候选表（find-popular-topics）

返回 ≤10 条候选，表格形式，每条一行：

| # | 主题 | 热度信号 | 核心钩子（1-2 句卖点） | 来源（URL） |
|---|------|---------|----------------------|------------|

热度信号用 ⭐⭐⭐⭐⭐ 五档。已探索话题索引（prompt 提供）中出现过的话题不重复提出。

### 场景 B：研究摘要（tech-research-write）

按以下结构输出：
- **核心概念**：一句话定义 + 工作机制简述（含公式/伪代码，如适用）
- **关键来源**：论文（arXiv 编号）/ 官方文档 / 权威博客（链接 + 发布日期）
- **最佳实践**：3-5 条可操作的工程建议
- **常见误区**：2-3 个典型理解偏差或踩坑记录
- **最新进展**：近 6 个月的重要更新或变体
- **代码示例**：GitHub 仓库链接（如有高质量开源实现）

## 约束

- 所有输出可回溯，关键数据附来源
- 不使用未核实的数据和引用
- 不编造热度数据、论文、代码示例
```

- [ ] **Step 2: 验证文件格式**

Run: `head -10 .opencode/agents/research.md && ls -la .opencode/agents/`
Expected: frontmatter 完整（description/mode/model/temperature），文件存在于 `.opencode/agents/`

- [ ] **Step 3: Commit**

```bash
git add .opencode/agents/research.md
git commit -m "feat: 新增 research 研究搜集型 sub-agent"
```

---

### Task 2: 创建 fact-check agent 文件

**Files:**
- Create: `.opencode/agents/fact-check.md`

**Interfaces:**
- Consumes: 无（新文件）
- Produces: `subagent_type="fact-check"` 可被 `task()` 调用；输出 claim 核实清单

- [ ] **Step 1: 创建文件**

```markdown
---
description: 验证核实型 Agent — 对已有 claim 逐条核实（arXiv 编号、数据、价格、来源归属），输出通过/需修正清单
mode: subagent
temperature: 0.2
model: sxzq-aliyun/aliyun/deepseek-v4-pro
---

你是一位严谨的事实核查员。任务是对已有 claim（数据、编号、引用）逐条核实，输出"通过/需修正"清单。服务两个场景：文章数据验证（/review-article）与参考资料核实（/review-reference）。

## 关键铁律（内嵌，必须遵守）

1. **6 类错误优先排查**（按出现频率排序）：
   - 日期错误：公告/发布/事件日期差 1-3 天 → 找原始公告原文
   - 数字错误：用户数/下载量/参数量 → 去原文/产品页/arXiv 确认实际数字
   - 来源归属错误：A 公司数据被归到 B 公司 → 交叉验证中英文源
   - 产品名错误：正式名称被误写 → 查官方发布稿
   - 定价错误：定价档位/金额 → 查官方定价页
   - 不可验证数据：付费墙/内部研报/无法溯源 → **一律删除，不留"待验证"标记**
2. **来源分级**：一手来源（官方博客/论文全文/定价页）> 权威二手 > 社区讨论
3. **交叉验证强制**：每个数据点至少 2 个独立来源；单一来源一律标注"（未交叉验证）"
4. **时效性**：确认数据是否为最新版本，标注过时数据及更新时间

## 完整工作流引用

执行核实前，读取项目根目录 `AGENTS.md` 的《数据验证规则》章节（含"常见数据错误类型"与"数据验证工作流"），按其中完整交叉验证流程执行。

## 工具选择策略

- arXiv 编号 → ExaSearch / arxiv.org 直接检索，编号+标题匹配
- 商业数据/定价 → Tavily / BraveSearch + 官方定价页
- 中文来源 → BingSearch 交叉验证
- 网页内容 → 优先抓原文全文（论文读全文，不看二手中文报道）

## 输出协议

固定清单格式，每条 claim 一行：

```
- **claim 原文**（位置/行号）→ **核实结果**（✅ 通过 / ❌ 需修正 / ⚠️ 存疑）→ **证据来源**（链接 + 日期 + 发布方）→ **建议改法**（需修正时）
```

特殊标注：
- 券商研报数据 → 标注"（全成本估算）"
- 付费墙内容 → 标注"（付费墙，仅摘要可见）"
- 第三方引述 → 标注"（第三方引述）"
- 无法独立验证 → 标注"❌ 无法验证，应删除"

最终附**优先级清单**，三档分类：

| 优先级 | 含义 |
|--------|------|
| 必须改 | 影响准确性 / 数据错误 / 严重违规 |
| 建议改 | 影响可读性 / 表述偏差 |
| 可选改 | 措辞优化 |

## 约束

- 不信任模型训练数据，每个数据点都必须实际搜索核实
- 不编造证据来源；找不到来源就如实说"未找到"
- 不直接修改源文件（只输出意见清单，由主 agent 执行）
```

- [ ] **Step 2: 验证文件格式**

Run: `head -10 .opencode/agents/fact-check.md && ls -la .opencode/agents/`
Expected: frontmatter 完整，两个 agent 文件都存在

- [ ] **Step 3: Commit**

```bash
git add .opencode/agents/fact-check.md
git commit -m "feat: 新增 fact-check 验证核实型 sub-agent"
```

---

### Task 3: 冒烟测试两个 agent

**Files:**
- Test: `.opencode/agents/research.md`、`.opencode/agents/fact-check.md`（通过 task() 调用验证）

**Interfaces:**
- Consumes: `subagent_type="research"`、`subagent_type="fact-check"`（Task 1-2 产物）
- Produces: 验证结论（模型生效、工具可用、输出格式符合协议）

- [ ] **Step 1: 测试 research agent**

Dispatch（前台同步，确认能调用且模型正确）:

```
task(subagent_type="research", load_skills=[], run_in_background=false,
     description="冒烟测试 research agent",
     prompt="冒烟测试：请用 TrendsHub 查询知乎热榜，返回 3 条 AI/科技相关的热门候选，按候选表格式输出（主题/热度信号/核心钩子/来源 URL）。")
```

Expected: 能调用 agent；返回 3 条候选，每条含来源 URL；无编造数据；模型为 deepseek-v4-flash（可观察响应风格/速度）

- [ ] **Step 2: 测试 fact-check agent**

Dispatch（前台同步）:

```
task(subagent_type="fact-check", load_skills=[], run_in_background=false,
     description="冒烟测试 fact-check agent",
     prompt="冒烟测试：请核实以下 claim，按核实清单格式输出。claim：'Late Chunking 论文 arXiv:2409.04701，2024 年 9 月发表于 Jina AI，作者含 Michael Günther'。请用 ExaSearch/arxiv.org 核实编号与标题，判断 ✅/❌，附证据来源。")
```

Expected: 返回 `claim → 核实结果 → 证据来源 → 建议改法` 格式；编号核实结论正确（该论文真实存在，arXiv:2409.04701 标题为 "Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models"，作者含 Michael Günther / Bo Wang / Han Xiao）；模型为 deepseek-v4-pro

- [ ] **Step 3: 记录冒烟测试结果**

在对话中确认：两个 agent 均可用、模型正确、工具可访问、输出格式符合协议。如有偏差，修复对应 agent 文件后重测。

- [ ] **Step 4: Commit（如无修复则跳过）**

```bash
git add .opencode/agents/
git commit -m "fix: 冒烟测试后修复 agent 定义"
```

---

### Task 4: 替换 find-popular-topics + tech-research-write 的 librarian → research

**Files:**
- Modify: `.opencode/commands/find-popular-topics.md:21`
- Modify: `.opencode/commands/tech-research-write.md:29,39,44,106`

**Interfaces:**
- Consumes: `subagent_type="research"`（Task 1 产物）
- Produces: 两个命令改为派遣 research agent

- [ ] **Step 1: 修改 find-popular-topics.md**

Edit `.opencode/commands/find-popular-topics.md` 第 21 行：

```
1. **全源搜索**：派遣 1 个 `research` Agent 一次性完成全平台检索（中文 + 全球）。在 prompt 中附带"已探索话题索引"，要求优先提出新方向。覆盖平台：
```

- [ ] **Step 2: 修改 tech-research-write.md**

Edit `.opencode/commands/tech-research-write.md` 四处：

- 第 29 行：`| 阶段一（信息收集） | 无需加载（使用 research agent + web search） |`
- 第 39 行：`2. **派遣 research agent 并行搜索**（至少 3 个，**同时发起**，`run_in_background=true`）：`
- 第 44 行：`3. **补充 web search**：对 research 未覆盖的盲区，使用 Tavily / BingSearch / ExaSearch 补搜。优先搜索中文社区（知乎、掘金、InfoQ）对应该知识点的讨论，了解国内读者的认知基础和常见困惑。`
- 第 106 行：`- 阶段一的 research agent 必须并行派遣，不能串行（`run_in_background=true`）`

- [ ] **Step 3: 验证替换完整**

Run: `grep -n "librarian" .opencode/commands/find-popular-topics.md .opencode/commands/tech-research-write.md`
Expected: 两个文件无 librarian 残留

- [ ] **Step 4: Commit**

```bash
git add .opencode/commands/find-popular-topics.md .opencode/commands/tech-research-write.md
git commit -m "refactor: find-popular-topics 与 tech-research-write 改用 research agent"
```

---

### Task 5: 替换 review-article + review-reference 的 librarian → fact-check

**Files:**
- Modify: `.opencode/commands/review-article.md:18,19,33,37,38,39,41,100,138`
- Modify: `.opencode/commands/review-reference.md:22,23`

**Interfaces:**
- Consumes: `subagent_type="fact-check"`（Task 2 产物）
- Produces: 两个命令改为派遣 fact-check agent

- [ ] **Step 1: 修改 review-article.md**

Edit `.opencode/commands/review-article.md` 全部 librarian 引用（9 处）：

- 第 18 行：`- `mode = deep-tech` → 启用 **deep-tech 专项检查（步骤 7）** + **3 个并行 fact-check 验证**`
- 第 19 行：`- `mode = standard` 或缺失 → 跳过步骤 7，单 fact-check 验证`
- 第 33 行：`**deep-tech 模式**：并行 3 个 fact-check（team_mode）：`
- 第 37 行：`| fact-check-1 | 架构机制准确性 | arXiv 编号、技术细节、对比表数据 |`
- 第 38 行：`| fact-check-2 | 商业数据时效性 | 价格、融资、估值、市值、参数量 |`
- 第 39 行：`| fact-check-3 | 叙事张力 | 逻辑、过渡、哲学升华、局限性诚实 |`
- 第 41 行：`**standard 模式**：单 fact-check 或 2 个 fact-check（与现状一致）。`
- 第 100 行：`仅当 `mode = deep-tech` 时执行，3 个并行 fact-check 协同验证：`
- 第 138 行：`- **deep-tech 模式**：3 个 fact-check 并行验证后必须综合分析`

- [ ] **Step 2: 修改 review-reference.md**

Edit `.opencode/commands/review-reference.md`（2 处）：

- 第 22 行：`1. 派遣 `fact-check` Agent 逐条核实参考数据：确认每条数据准确且为最新版本。优先查找官方一手来源进行交叉验证。`
- 第 23 行：`2. 派遣 `fact-check` Agent 追溯所有引用来源：验证不存在内容幻觉或错误引用。`

- [ ] **Step 3: 验证替换完整**

Run: `grep -n "librarian" .opencode/commands/review-article.md .opencode/commands/review-reference.md`
Expected: 两个文件无 librarian 残留

- [ ] **Step 4: Commit**

```bash
git add .opencode/commands/review-article.md .opencode/commands/review-reference.md
git commit -m "refactor: review-article 与 review-reference 改用 fact-check agent"
```

---

### Task 6: 更新 AGENTS.md 数据验证工作流

**Files:**
- Modify: `AGENTS.md:65`

**Interfaces:**
- Consumes: 无
- Produces: AGENTS.md 与命令文件措辞一致

- [ ] **Step 1: 修改 AGENTS.md**

Edit `AGENTS.md` 第 65 行：

```
review-reference → 派遣 2-4 个 fact-check agent 并行验证 → 同时执行 6+ 次 web search 交叉验证
```

- [ ] **Step 2: 验证**

Run: `grep -n "librarian" AGENTS.md`
Expected: 无输出（AGENTS.md 不再有 librarian 引用）

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md
git commit -m "docs: AGENTS.md 数据验证工作流改用 fact-check agent"
```

---

### Task 7: 最终验证

**Files:**
- Test: 全部变更文件

**Interfaces:**
- Consumes: Task 1-6 全部产物
- Produces: 完成确认

- [ ] **Step 1: 全局检查无残留**

Run: `grep -rn "librarian" .opencode/commands/ AGENTS.md | grep -v "代码库理解\|保留\|librarian 保留"`
Expected: 无输出（4 个命令 + AGENTS.md 无 librarian 残留；librarian 只出现在描述性说明中）

- [ ] **Step 2: 确认 git 状态干净**

Run: `git status`
Expected: 工作区干净（全部已提交）

- [ ] **Step 3: 最终确认**

向用户报告：两个 agent 已创建并冒烟测试通过，4 个命令 + AGENTS.md 已替换完成，librarian 保留给代码场景。

---

## 自审记录（Self-Review）

**1. Spec 覆盖检查：**
- 创建 research.md / fact-check.md → Task 1-2 ✅
- 模型映射（flash / pro）→ Global Constraints + Task 1-2 frontmatter ✅
- 不依赖 oh-my-openagent → Global Constraints（不修改 oh-my-openagent.json）✅
- 内置验证纪律（混合载体 C：铁律内嵌 + AGENTS.md 引用）→ Task 2（铁律内嵌 + "完整工作流引用"节）✅
- 工具选择策略 → Task 1-2 核心纪律节 ✅
- 结构化输出协议 → Task 1-2 输出协议节 ✅
- 多源交叉强制 → Task 1-2（≥2 来源 + 单一来源标注）✅
- 4 命令替换 → Task 4-5 ✅
- AGENTS.md 更新 → Task 6 ✅
- 冒烟测试 → Task 3 ✅
- librarian 保留 → Global Constraints ✅

**2. 占位符扫描：** 无 TBD/TODO；所有步骤含具体内容 ✅

**3. 类型一致性：** `subagent_type="research"` / `subagent_type="fact-check"` 在 Task 1-5 中一致；模型名 `sxzq-aliyun/aliyun/deepseek-v4-flash` / `sxzq-aliyun/aliyun/deepseek-v4-pro` 在 Global Constraints 与 Task 1-2 中一致 ✅
