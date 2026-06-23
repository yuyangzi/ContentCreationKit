# 设计文档：article-to-presentation 技能重构（Reveal.js → Slidev）

## 项目概述

将 `article-to-presentation` 技能从 Reveal.js + 手写 HTML 重构为 Slidev + Markdown 生成模式，利用 `@enyineer/slidev-theme-neocarbon` 主题实现霓虹/赛博/玻璃态视觉风格。

| 属性 | 旧（Reveal.js） | 新（Slidev） |
|------|----------------|--------------|
| 输入 | Markdown 文章 | 不变 |
| 输出 | 单文件 `index.html` | Slidev 项目（`slides.md` + `package.json`）→ `slidev build` → `dist/` SPA |
| 框架 | Reveal.js 5.1.0 CDN | Slidev + Vite + Vue |
| 主题 | 手写 8 变量深色极简 | `@enyineer/slidev-theme-neocarbon` |
| 图表 | 11 个手写 CSS 组件类 | neocarbon 内置 25 组件 + Mermaid 暗黑适配 |
| 实现方式 | AI 生成 500+ 行 HTML | AI 生成 ~200 行 Markdown |
| 审查方式 | Metis+Momus 审查 HTML 计划 | Metis 审查 MD 内容 |
| 验证 | 手动浏览器预览 | `slidev build` → 浏览器打开 `dist/index.html` |

---

## 技术选型

### 框架：Slidev

- GitHub 44k+ stars，为开发者设计的 Markdown 幻灯片工具
- 内置 UnoCSS（原子化 CSS，一行换肤）
- 支持 Mermaid 图表（自动暗黑主题适配）、KaTeX 公式、Monaco 编辑器
- `slidev build` → 产出静态 SPA（`dist/` 文件夹），无需服务器，浏览器直接打开
- 主题系统：npm 安装，一行切换

### 主题：@enyineer/slidev-theme-neocarbon

- **22 种布局**：cover, section, fact, quote, statement, comparison, code, math, diagram, spotlight, browser, end 等
- **25 个组件**：charts, timelines, progress bars, terminals, feature grids, radar charts, heatmaps, flip cards 等
- **电影级动画**：staggered entrances, shimmer highlights, pulsing glows, floating particles
- **全局换肤**：覆盖 `--nc-accent` CSS 变量即可全局换色
- **暗黑专一**：dark-only，高对比度，视觉冲击力强
- **Mermaid 暗黑适配**：自动将 Mermaid 图表的节点、边、标签配色适配暗黑主题
- PDF-ready：`print-color-adjust: exact`

---

## 技能管线变更

### 阶段一：数据提取 + PPT 文案生成（不变）

输入文章 → 提取 5 类内容（核心论点、关键数据、故事线、金句、数据来源）→ 生成 PPT 文案。

### 阶段二：需求确认（微调）

使用 `/before-dev` 逐步确认：
- 目标观众、幻灯片数量、视觉风格（固定 neon-carbon）
- **布局映射覆盖**（可选）：用户可调整"数据对比→comparison"等默认映射
- 不再需要图表选型（neocarbon 组件覆盖），不再使用 visual companion

### 阶段三：设计方案（重写）

技术选型：Slidev + neocarbon 主题

输出内容：
1. **主题配置**：`--nc-accent` 颜色值、字体覆盖（如有需要）
2. **布局映射表**：确认或覆盖默认映射（见下方映射表）
3. **幻灯片结构**：按章节组织，每张幻灯片指定 neocarbon 布局类型
4. **组件选型**：为数据图表指定 neocarbon 组件（charts, progress bars, radar charts 等）

审查：提交设计文档给 **Metis**

### 阶段四：实施计划（重写）

使用 writing-plans 技能编写实现计划。

文件结构：
```
content/ppt/YYYY-MM-DD-<topic>/
├── slides.md           ← Slidev Markdown 文件
└── package.json        ← 依赖（slidev, neocarbon theme）
```

任务拆分：
1. **Task 1**: 初始化 Slidev 项目（`package.json` + 安装依赖）
2. **Task 2**: 配置 neocarbon 主题（frontmatter + `--nc-accent` 覆盖）
3. **Task 3**: 生成封面 + 章节标题幻灯片（cover, section 布局）
4. **Task 4**: 生成数据图表幻灯片（comparison, fact, diagram 布局 + neocarbon 组件）
5. **Task 5**: 生成引用/金句/案例幻灯片（quote, statement 布局）
6. **Task 6**: 生成结尾幻灯片（end 布局）
7. **Task 7**: `slidev build` + 浏览器预览验证

**不再需要**：CSS 组件类、插入锚点、`!important` 约束 — 全部由 neocarbon 主题接管。

### 阶段五：计划审查（简化）

仅提交给 **Metis** 审查（无需 Momus，因为输出是 Markdown 而非 HTML 代码文件）。

审查重点：数据准确性、布局合理性、neocarbon 组件使用是否正确。

### 阶段六：实现（重写）

1. 写入 `slides.md`（AI 生成）
2. 运行 `npm install`
3. 运行 `slidev build`
4. 在浏览器中打开 `dist/index.html` 预览
5. 手动检查数据准确性、布局效果、颜色编码

---

## 布局映射表（预设，阶段二可覆盖）

| PPT 内容类型 | neocarbon 方案 | 具体实现 |
|-------------|---------------|----------|
| 封面主标题 | `cover` 布局 | 全屏大字 + 背景动画（grid + scan lines + gradient） |
| 副标题/数据来源 | `statement` 布局 | 大标题 + 脚注样式的来源列表 |
| 章节分隔 | `section` 布局 | 全屏分隔页 + glow accent line |
| 开场钩子（引用） | `quote` 布局 | 超大引号标记 + 来源标注 |
| 柱状图对比（89% vs 88%） | `default` 布局 + `<NcBarChart />` 组件 | 双柱并排，标签在柱上方，绿色(成功)/橙色(对比) |
| 并排指标卡（放弃率、动作数、输出量） | `metrics` 布局 | 2-3 张指标卡并排，大数字+标签+倍数标注 |
| 左右概念对比（可编码 vs 默会、EN vs CN） | `comparison` 布局 | `::left::` / `::right::` 插槽，暗面 vs 成功色调渐变 |
| 引用/金句（多行大字） | `statement` 布局 | 全屏戏剧性陈述，支持换行高亮 |
| 本质洞察 + 案例 | `quote` 布局 + 内嵌案例卡 | 引用块内嵌 `<div class="case-card">` |
| 数据来源列表 | `default` 布局 | 正文排版，格式化来源列表 |
| 结尾 | `statement` 布局（金句）+ `default` 布局（来源） | 两张幻灯片分别处理 |

### 需要自定义 CSS 辅助的内容类型

以下类型 neocarbon 无原生 1:1 映射，需要少量内联 CSS：

| PPT 内容类型 | 方案 | 说明 |
|-------------|------|------|
| 阶梯图（15%→28%→33%） | `default` + `<NcBarChart />` 3 根柱 | 自定义 height 比例、柱颜色渐变 |
| Before/After 柱对比（33%→19%） | `default` + `<NcBarChart />` grouped 模式 | 每个类别显示前/后两根柱，前浅后深 |
| 流程分叉图（碰壁→放弃/翻盘） | `diagram` 布局 + Mermaid flowchart | `::left::` 文字说明，`::right::` Mermaid `graph TD` |

---

## neocarbon 设计令牌（颜色编码实现）

neocarbon 暴露 5 个语义颜色令牌，**必须**在 `slides.md` 中覆盖以匹配现有颜色编码规则：

```html
<style>
:root {
  --nc-accent:  #ff6b35;   /* 橙色 → 中性强调、主标题高亮 */
  --nc-success: #22c55e;   /* 绿色 → 正面/上升/默会知识 */
  --nc-danger:  #ef4444;   /* 红色 → 负面/下降/警示 */
  --nc-warning: #f59e0b;   /* 琥珀 → 保留，备用 */
  --nc-info:    #3b82f6;   /* 蓝色 → 保留，备用 */
}
</style>
```

### CSS 实用类（用于内联颜色标注）

neocarbon 提供以下类，可直接在 Markdown 中使用（搭配 `::` 插槽或内联 HTML）：

| 类 | 颜色 | 用途 |
|----|------|------|
| `nc-text-success` | 绿色 | 正面数据、默会知识、价值判断 |
| `nc-text-danger` | 红色 | 负面数据、放弃率、下降趋势 |
| `nc-text-accent` | 橙色 | 中性强调、关键数据高亮 |
| `nc-text-muted` | 灰色 | 辅助说明、脚注 |
| `nc-text-dim` | 深灰 | 次要文字 |

### 颜色编码检查清单（实施时必须验证）

- [ ] 默会知识/价值判断：必须用 `nc-text-success`（绿色），**禁止**用 `nc-text-accent`（橙色）
- [ ] 下降/负面数据：必须用 `nc-text-danger`（红色）
- [ ] 中性数据（如 93% 使用率）：用 `nc-text-accent`（橙色），**禁止**标红

---

## neocarbon 组件 API（关键组件）

在 Slidev Markdown 中，neocarbon 组件以 Vue 标签形式调用：

### `<NcBarChart />` — 柱状图

```html
<NcBarChart
  title="AI辅助编码 · 部分成功率"
  :labels="['软件工程师', '其他职业']"
  :data="[89, 88]"
  :colors="['var(--nc-success)', 'var(--nc-accent)']"
  height="280"
/>
```

Props: `title`, `labels` (string[]), `data` (number[]), `colors` (string[]), `height` (number), `horizontal` (boolean)

### `<NcProgress />` — 进度条

```html
<NcProgress value="15" label="新手严格成功率" color="var(--nc-danger)" />
<NcProgress value="33" label="高级严格成功率" color="var(--nc-accent)" />
```

Props: `value` (number, 0-100), `label` (string), `color` (CSS color)

### `metrics` 布局 — 并排指标卡

```markdown
---
layout: metrics
---
::metrics::
<div class="nc-metric">
  <span class="nc-metric-value">19%</span>
  <span class="nc-metric-label nc-text-danger">新手放弃率</span>
</div>
<div class="nc-metric">
  <span class="nc-metric-value">5-7%</span>
  <span class="nc-metric-label nc-text-accent">专家放弃率</span>
</div>
```

---

## B站 录屏特殊要求

### Viewport 配置

Slidev 默认 viewport 由浏览器窗口决定。为确保 1920×1080 录屏效果：

```bash
# 开发时指定窗口大小
slidev --open --port 3030

# 构建后用固定窗口打开
npx serve dist -p 3030
# 浏览器手动调至 1920×1080
```

### 隐藏导航 UI

Slidev 内置导航控件默认显示。录屏前**必须**隐藏：
- 在浏览器 URL 后加 `?showCursor=false`（如果有插件）
- 或使用 Slidev 配置禁用底部导航栏

### 动画控制

neocarbon 默认启用电影级动画（staggered entrances、shimmer、pulse、particles）。B站录屏可能需要：

```html
<style>
/* 降级动画 — 在 slides.md frontmatter 的 <style> 块中 */
.nc-stagger > * { animation: none !important; opacity: 1 !important; }
.nc-shimmer { animation: none !important; }
.nc-particles { display: none !important; }
</style>
```

在阶段二需求确认时询问用户：保留动画 / 降级淡入 / 全部禁用。

### `slidev build` 输出限制

`slidev build` 产出 `dist/` 文件夹（Vite SPA，多个 JS/CSS chunk）。**不能**通过 `file://` 协议直接打开，需要用本地静态服务器：

```bash
npx serve dist -p 3030
# 浏览器打开 http://localhost:3030
```

---

## 环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Node.js | >= 20.12.0 | Slidev v52 最低要求 |
| npm | >= 9 | 包管理 |
| `@slidev/cli` | `52.0.0`（精确版本） | 避免 caret 范围引入 breaking changes |
| `@enyineer/slidev-theme-neocarbon` | `1.0.5`（精确版本） | 低采用度主题，必须锁版本 |

---

## 风险提示

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| neocarbon 仅 3 GitHub star，1 贡献者 | 🟡 中 | 锁精确版本 `1.0.5`；如 npm 包不可用，回退到 Slidev 内置 `default` 主题 + 自定义 CSS |
| `slidev build` 不支持 `file://` 协议 | 🟡 中 | 录屏时用 `npx serve dist` 启动本地服务器 |
| 42% 幻灯片类型无原生 1:1 映射 | 🟡 中 | 自定义 CSS 辅助（阶梯图、before/after 柱对），接受视觉差异 |
| CJK 字体渲染 | 🟢 低 | neocarbon 的 Monaspace Neon 仅覆盖英文；CJK 回退到系统字体，已验证可接受 |
| Slidev 版本升级 breaking changes | 🟢 低 | `package.json` 锁精确版本，手工升级前测试 |

---

## 删除内容清单

从当前 `article-to-presentation` skill 中删除：

| 文件/内容 | 原因 |
|-----------|------|
| `references/technical-details.md` 中的 11 个 CSS 组件模板 | neocarbon 主题接管 |
| `references/technical-details.md` 中的 `!important` 约束 | 不再写 CSS |
| `references/technical-details.md` 中的插入锚点规范 | 不再写 HTML |
| `references/technical-details.md` 中的 Reveal.js 初始化配置 | Slidev 接管 |
| `references/technical-details.md` 中的全屏按钮 HTML/CSS | Slidev 内置 UI |
| `references/common-pitfalls.md` 中的 CSS 特异性陷阱 | 不再适用 |
| `references/common-pitfalls.md` 中的字体显式设置陷阱 | neocarbon 捆绑 Monaspace Neon 字体 |
| `references/common-pitfalls.md` 中的白色闪烁陷阱 | Slidev 内置暗黑加载 |
| SKILL.md 中的 Metis+Momus 并行审查 | 改为仅 Metis |
| SKILL.md 中的 Subagent-Driven Development 引用 | 改为单 agent 生成 MD |
| SKILL.md 中的 7 任务拆分模板 | 改为 7 任务 Slidev 模板 |

### 保留内容

| 内容 | 原因 |
|------|------|
| 六阶段管线骨架 | 流程仍然有效 |
| 数据提取 5 类内容 | 输入处理不变 |
| `/before-dev` 需求确认流程 | 用户交互不变 |
| 颜色编码规则（绿=正面，红=负面，橙=中性，默会=绿色） | 语义规则跨框架适用 |
| 数据来源交叉验证（≥6 个来源） | 数据准确性不变 |
| 常见陷阱中的"数据来源数量矛盾""红色用于中性数据"等 | 内容审查陷阱跨框架适用 |

---

## neo-carbon 主题配置模板

`slides.md` frontmatter 模板：

```yaml
---
theme: '@enyineer/slidev-theme-neocarbon'
title: 'AI压缩了执行力，放大了判断力'
info: |
  ## Anthropic 2026.6 报告数据分析
  23.5万人 · 40万次会话
class: text-center
highlighter: shiki
transition: fade
mdc: true
---
```

`package.json` 模板：

```json
{
  "name": "ai-compressed-execution",
  "private": true,
  "scripts": {
    "build": "slidev build",
    "dev": "slidev --open",
    "export": "slidev export"
  },
  "dependencies": {
    "@slidev/cli": "52.0.0",
    "@enyineer/slidev-theme-neocarbon": "1.0.5"
  }
}
```

---

## 已确认决策

| 问题 | 决策 |
|------|------|
| 框架 | Slidev（替代 Reveal.js） |
| 主题 | `@enyineer/slidev-theme-neocarbon` |
| 输出格式 | `slides.md` + `package.json` → `slidev build` → `dist/` SPA |
| 布局选择 | 预设映射表 + 用户可选覆盖 |
| 数据图表 | neocarbon 25 组件 + Mermaid（不要求像素级精确） |
| 审查 | 仅 Metis（去掉 Momus） |
| 旧 skill 处理 | 直接替换，不保留备份 |
| 视觉 companion | 保留 — 用于确认 neocarbon 动画策略（保留/降级/禁用）和颜色方案 |
| Playwright 验证 | 不需要（Slidev build 产出确定性 HTML） |

---

*设计文档时间：2026-06-22*
