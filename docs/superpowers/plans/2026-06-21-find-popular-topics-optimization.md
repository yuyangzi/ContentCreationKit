# `/find-popular-topics` 命令优化 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use `subagent-driven-development` or `executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重写 `.opencode/commands/find-popular-topics.md` 的命令定义，实现搜索合并、饱和检查、话题分类、单次候选表、增量更新、文件命名规范化和归档机制。

**Architecture:** 所有变更集中在命令定义文件（过程指令文档），不涉及代码改动。通过修改该文件的步骤描述、约束条件和输出规范，指导 Sisyphus 在下次执行 `/find-popular-topics` 时遵循新的优化流程。

**Tech Stack:** 命令定义 Markdown，无代码/脚本变动。

---

## 文件结构

| 文件 | 操作 | 说明 |
|------|------|------|
| `.opencode/commands/find-popular-topics.md` | 重写 | 优化后的命令定义，覆盖全部 6 项变更 |
| `content/topics/archive/` | 创建 | 目录创建（不涉及代码，由命令步骤指引） |

### 变更对照

| 原内容 | 新内容 | 替换方式 |
|--------|--------|----------|
| 步骤 1-2：2 个 librarian 分步搜索+深度研究 | 步骤 1-2：1 个 librarian 合并搜索，附带饱和检查 | 替换 |
| 步骤 3：brainstorming 逐条讨论 | 步骤 3-4：单次候选表 + 批量标记 | 替换 |
| 步骤 4：保存文件 | 步骤 5-6：文件写入 + 增量更新 | 替换 |
| 约束："不要一次性抛出多个话题" | 删除此约束 | 移除 |
| 输出：`{时间戳}-{主题名}.md` | 输出：`{YYYYMMDD}-{中文主题名}.md` | 替换 |

---

### Task 1: 重写 `.opencode/commands/find-popular-topics.md`

**Files:**
- Modify: `.opencode/commands/find-popular-topics.md`（全文重写）

- [ ] **Step 1: 读取当前文件内容，确认变更基线**

当前文件 40 行，需要全文替换。

- [ ] **Step 2: 写入新的命令定义文件**

新的完整内容如下。在 Description 字段后依次替换目标/前置条件/输入/步骤/输出/约束/禁止操作段落。

```markdown
---
description: 查找内容创作的热门主题
---

# 查找热门主题

## 目标

在各大内容平台上挖掘当前高热度的话题，结合用户指定的方向筛选出适合创作的候选主题。支持话题自动分类、饱和检测、增量更新。

## 前置条件

（无）

## 输入

- （可选）用户指定的创作方向或领域

## 步骤

1. **饱和检查**：读取 `content/topics/` 目录下的所有 `.md` 文件名（排除 `old/` 中的过期文件），按文件名解析话题标题，构建"已探索话题索引"列表。该索引将传递给下一阶段的搜索 Agent。

2. **全源搜索**：派遣 1 个 `librarian` Agent 一次性完成全平台检索（中文 + 全球）。在 prompt 中附带"已探索话题索引"，要求优先提出新方向。覆盖平台：
   - 中文平台：知乎热搜、微博热搜、36氪热榜、掘金热榜、InfoQ 资讯、少数派热榜、B站科技榜、抖音热搜、爱范儿快讯、澎湃热榜、腾讯新闻热点
   - 全球平台：BraveSearch（web/news/video）、Tavily Search、The Verge、9to5Mac、BBC News 等
   - 每条候选自动标注类型标签：`[热点]`（时效 < 2 周，事件驱动）、`[趋势]`（活跃 2-4 周，发展阶段）、`[范式]`（持续 > 1 月，底层变化）
   - Agent 自动做跨平台去重归并（同一事件的中英文源合并为一条候选）
   - 返回 ≤ 10 条候选，每条包含：标题、热度信号（⭐⭐⭐⭐⭐）、类型标签、核心钩子（1-2 句卖点）

3. **候选匹配**：候选到齐后，对比饱和检查阶段构建的"已探索话题索引"。高度相似命中的候选自动标记为 `[更新]`（来源于已有话题文件），其余标记为 `[新建]`。

4. **一次性展示候选表**：将所有候选以表格形式一次性展示给用户，每条一行。用户回复格式：`1 要 2 [更新] 3 跳过`。三种标记含义：
   - `要` — 新建 topic 文件
   - `[更新]` — 增量追加到已有话题文件（追加 `## {YYYY-MM-DD} 更新` 区块，文件名时间戳同步更新为当前日期）
   - `跳过` — 放弃此候选

5. **批量写入**：根据用户的标记结果，执行写入：
   - `要` 的候选 → 新建 `{YYYYMMDD}-{中文主题名}.md` 到 `content/topics/`
   - `[更新]` 的候选 → 读取已有文件 → 在文件尾追加 `## {YYYY-MM-DD} 更新` 区块 + 新内容 → 文件名时间戳同步更新

## 输出

- `content/topics/{YYYYMMDD}-{中文主题名}.md`：包含主题名称、热度背景分析、类型标签、创作方向建议、可回溯的来源链接

## 约束

**必须遵守：**

- 话题来源须可回溯，优先抓取原文页面内容而非摘要
- 与用户讨论时一次只展示一个候选表（≤ 10 条）
- 已存在的话题不要重复创建新文件，改为增量追加

**禁止操作：**

- 不要编造话题热度数据
```

验证要点：
- 所有步骤从 1 到 5 逻辑连贯：饱和检查 → 搜索 → 匹配 → 展示 → 写入
- 旧文件中的"不要一次性抛出多个话题让用户选择"已删除
- 文件命名格式已统一为 `{YYYYMMDD}-{中文主题名}.md`
- 增量更新逻辑描述清晰（追加 `## {YYYY-MM-DD} 更新` 区块）
- 归档机制已体现（饱和检查排除 `old/` 目录）

- [ ] **Step 3: 验证文件内容**

```bash
cat .opencode/commands/find-popular-topics.md
```

检查：
- YAML frontmatter 正确（`---` 闭合）
- 所有步骤序号连续 1→5
- 文件命名格式为 `{YYYYMMDD}-{中文主题名}.md`
- 无旧约束残留（"不要一次性抛出多个话题"已被移除）
- 新增了 `[热点]/[趋势]/[范式]` 自动分类和增量更新规则

- [ ] **Step 4: 创建 content/topics/archive/ 目录**

```bash
mkdir -p content/topics/archive
```

- [ ] **Step 5: 提交**

```bash
git add .opencode/commands/find-popular-topics.md content/topics/archive/
git commit -m "feat: 优化 /find-popular-topics 命令 — 合并搜索、饱和检查、单次候选表、增量更新"
```

提交后验证：
```bash
git log --oneline -3
```