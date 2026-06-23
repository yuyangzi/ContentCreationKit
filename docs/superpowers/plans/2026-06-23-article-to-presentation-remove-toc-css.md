# article-to-presentation 移除冗余TOC CSS 并添加配置禁用导出目录实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构 article-to-presentation 技能，使用 Slidev 原生配置 `export.withToc: false` 禁用导出目录，精简 CSS 只隐藏 TOC 相关元素，消除代码重复。

**Architecture:** 在现有技能文档结构上修改，只调整文档内容，不改变技能整体架构。保持一份权威 CSS 定义在 `references/technical-details.md`，其他文档只引用不重复。

**Tech Stack:** Markdown 文档修改，无代码实现。

---

### Task 1: 在 frontmatter 模板添加 export.withToc: false 配置

**Files:**
- Modify: `.opencode/skills/article-to-presentation/references/technical-details.md:219-234`

- [ ] **Step 1: 读取 frontmatter 模板当前内容**

读取文件第 217-234 行，确认现有内容结构。

- [ ] **Step 2: 在 transition 后 fonts 前添加 export 配置**

在 `transition: fade` 和 `fonts:` 之间插入：

```yaml
# 禁用导出 PDF/PPTX 时自动生成目录页
export:
  withToc: false
```

最终 frontmatter 模板：

```yaml
---
theme: '@enyineer/slidev-theme-neocarbon'
title: '演示文稿标题'
info: |
  ## 副标题信息
  数据来源概述
highlighter: shiki
transition: fade
# 禁用导出 PDF/PPTX 时自动生成目录页
export:
  withToc: false
fonts:
  sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'
  serif: 'Noto Serif SC, serif'
  mono: 'Fira Code, monospace'
  provider: none
---
```

- [ ] **Step 3: 保存修改**

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/article-to-presentation/references/technical-details.md
git commit -m "refactor: add export.withToc: false to frontmatter template"
```

---

### Task 2: 精简「录屏面板隐藏」CSS，只保留TOC相关selector

**Files:**
- Modify: `.opencode/skills/article-to-presentation/references/technical-details.md:145-174`

- [ ] **Step 1: 读取当前完整CSS**

读取第 137-176 行，确认分类说明和完整CSS。

- [ ] **Step 2: 修改分类说明**

更新第 137-141 行：

```markdown
Slidev 在导出和UI层面都会生成目录(TOC)。我们通过配置+CSS组合禁用：
1. 配置：`export.withToc: false` → 导出 PDF/PPTX 不生成目录页
2. CSS：只隐藏UI层面的TOC面板，防止录屏时遮挡内容。覆盖以下：

1. **Slidev 内置TOC面板**：`#slidev-toc`, `.slidev-toc`, `.slidev-toc-list`
2. **通用语义元素**：`.toc`, `.toc-overlay`
3. **属性模糊匹配（兜底）**：`[class*="toc"]`, `[id*="slidev-toc"]`
```

- [ ] **Step 3: 替换完整CSS代码**

```css
/* Hide only TOC (table of contents) panels for clean Bilibili recording */
#slidev-toc,
.slidev-toc,
.slidev-toc-list,
.toc,
.toc-overlay,
[class*="toc"],
[id*="slidev-toc"] {
  display: none !important;
}
```

- [ ] **Step 4: 保存修改**

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/article-to-presentation/references/technical-details.md
git commit -m "refactor: simplify TOC-hiding CSS, only hide TOC elements"
```

---

### Task 3: 更新 SKILL.md，删除内联CSS速查改为引用

**Files:**
- Modify: `.opencode/skills/article-to-presentation/SKILL.md:210-219`

- [ ] **Step 1: 读取当前内容**

读取第 206-226 行，找到"隐藏 Slidev 导航面板"章节。

- [ ] **Step 2: 删除内联CSS，改为引用**

将原：

```
- **隐藏 Slidev 导航面板**（录屏必加）→ 全量 selector 见 [references/technical-details.md](references/technical-details.md)「录屏面板隐藏」章节，速查：
  ```css
  #slidev-overview, #slidev-toc, .slidev-overview, .slidev-toc,
  .slidev-sidebar, .slidev-nav, .slidev-slide-nav, .slidev-nav-overlay,
  .slidev-navigation, .slidev-overview-panel, .slidev-control-layout,
  .nav, .nav-overlay, .toc, .toc-overlay, aside, nav,
  [class*="sidebar"], [class*="toc"], [class*="navigation"],
  [class*="nav-overlay"], [id*="slidev-overview"], [id*="slidev-toc"]
  { display: none !important; }
  ```
```

修改为：

```
- **禁用TOC/目录生成**（录屏必加配置+CSS）：
  - 配置：frontmatter 模板已预置 `export.withToc: false` → 导出 PDF/PPTX 不生成目录页
  - CSS：完整TOC隐藏规则见 [references/technical-details.md](references/technical-details.md)「录屏面板隐藏」章节，自动添加到 `<style>` 块
```

- [ ] **Step 3: 保存修改**

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/article-to-presentation/SKILL.md
git commit -m "refactor: remove inline TOC-hiding CSS from SKILL.md, reference full version"
```

---

### Task 4: 更新 common-pitfalls.md，修正 selector 列表与权威版本一致

**Files:**
- Modify: `.opencode/skills/article-to-presentation/references/common-pitfalls.md:20`

- [ ] **Step 1: 读取 common-pitfalls.md，找到陷阱 #14**

定位到第 20 行左右的"Slidev TOC/导航面板遮挡内容"陷阱。

- [ ] **Step 2: 更新 selector 列表**

将陷阱描述中的 selector 列表更新为精简后的完整列表：

```
#14 | Slidev TOC/导航面板遮挡内容 | 检查 `slides.md` `<style>` 块中是否包含完整 TOC 隐藏 CSS：`#slidev-toc, .slidev-toc, .slidev-toc-list, .toc, .toc-overlay, [class*="toc"], [id*="slidev-toc"] { display: none !important; }`
```

- [ ] **Step 3: 保存修改**

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/article-to-presentation/references/common-pitfalls.md
git commit -m "refactor: update TOC selector list in common-pitfalls.md"
```

---

## 验证

完成所有任务后，验证：

1. ✅ frontmatter 模板已包含 `export.withToc: false`
2. ✅ CSS 只包含 TOC 相关 selector，共 7 个
3. ✅ SKILL.md 已删除内联CSS
4. ✅ common-pitfalls.md selector 列表与权威版本一致
5. ✅ 所有文件没有语法错误，Markdown 链接正常
