# 技术细节

## 配色预设库

### 预设 A：霓虹紫（默认）

适用场景：前沿科技、AI Agent、赛博朋克话题。

在 `slides.md` 的 `<style>` 块中设置：

```html
<style>
:root {
  --nc-accent:  #a855f7;   /* 紫 → 中性强调、主标题高亮 */
  --nc-success: #22d3ee;   /* 青 → 正面数据、上升/默会知识 */
  --nc-danger:  #f43f5e;   /* 玫红 → 负面数据、下降/警示 */
  --nc-warning: #fbbf24;   /* 琥珀 → 保留 */
  --nc-info:    #818cf8;   /* 靛蓝 → 保留 */
}
</style>
```

### 预设 B：暖橙

适用场景：数据分析、趋势报告、综合科技内容。

```html
<style>
:root {
  --nc-accent:  #ff6b35;   /* 橙色 → 中性强调 */
  --nc-success: #22c55e;   /* 绿色 → 正面/上升 */
  --nc-danger:  #ef4444;   /* 红色 → 负面/下降 */
  --nc-warning: #f59e0b;   /* 琥珀 → 保留 */
  --nc-info:    #3b82f6;   /* 蓝色 → 保留 */
}
</style>
```

### 预设 C：赛博绿

适用场景：安全主题、基础设施、运维/SRE 话题。

```html
<style>
:root {
  --nc-accent:  #00ff9d;   /* 霓虹绿 → 中性强调 */
  --nc-success: #34d399;   /* 翠绿 → 正面/上升 */
  --nc-danger:  #f87171;   /* 浅红 → 负面/下降 */
  --nc-warning: #fcd34d;   /* 金黄 → 保留 */
  --nc-info:    #67e8f9;   /* 天蓝 → 保留 */
}
</style>
```

### 使用方式

1. 阶段三从三套预设中选基础配色（默认霓虹紫）
2. 用户可逐色覆盖（如只改 `--nc-accent` 其余保留默认）
3. 颜色编码语义不变：success=正面/danger=负面/accent=中性

### CSS 实用类（内联颜色标注）

| 类 | 颜色（霓虹紫默认） | 用途 |
|----|---------------------|------|
| `nc-text-success` | 青色 | 正面数据、默会知识、价值判断 |
| `nc-text-danger` | 玫红 | 负面数据、下降趋势 |
| `nc-text-accent` | 紫色 | 中性强调、关键数据 |
| `nc-text-muted` | 灰色 | 辅助说明、脚注 |
| `nc-text-dim` | 深灰 | 次要文字 |

### 颜色编码规则

| 数据类型 | 颜色（霓虹紫默认） | 实现 |
|----------|---------------------|------|
| 增长/正面/默会知识 | 青色 | `nc-text-success` 或 `var(--nc-success)` |
| 下降/负面 | 玫红 | `nc-text-danger` 或 `var(--nc-danger)` |
| 中性/强调 | 紫色 | `nc-text-accent` 或 `var(--nc-accent)` |

**严格禁止**：红色用于中性数据（如 93% 使用率）；默会知识/价值判断用紫色代替青色。

---

## 字体

neocarbon 捆绑 Monaspace Neon（英文等宽）。CJK 回退到系统字体栈。

### frontmatter 字体配置（必须）

```yaml
fonts:
  sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'
  serif: 'Noto Serif SC, serif'
  mono: 'Fira Code, monospace'
  provider: none
```

关键字段说明：
- `sans`：CJK 三级回退栈 — PingFang SC（macOS）→ Microsoft YaHei（Windows）→ Noto Sans SC（Linux/CI）
- `mono`：仅放拉丁字体 — CJK 等宽字体在代码块中字形扭曲
- `provider: none`：禁止 Slidev 自动请求 Google Fonts CDN — 国内网络不可达，阻塞构建

### CJK 行高（必须在 `<style>` 块中设置）

```css
.slidev-layout { line-height: 1.75; font-size: 24px; }
```

CJK 文字需要 1.7+ 行高（拉丁 1.5 够用），否则上下行汉字会挤在一起。长段落（如 quote 布局中的引用文本）用 `line-height: 1.8`。

### Mermaid 中文补丁（必须在 `<style>` 块中设置）

```css
svg text { font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important; }
```

不加此补丁 → Mermaid 节点中文在部分浏览器显示为方框。

### PDF 导出注意（可选）

如需 `slidev export --format pdf`：
- CI 环境需预装 `fonts-noto-cjk` + locale `zh_CN.UTF-8`
- 增加 `--timeout 60000 --wait 1000` 确保动画渲染完成
- 本地开发通常不需要此步骤

---

## 幻灯片比例与录屏配置

- 目标：1920 × 1080（16:9）
- Slidev 默认使用浏览器窗口大小
- `slidev build` 产出 `dist/` SPA（**不能**通过 `file://` 直接打开）
- 录屏时使用 `npx serve dist -p 3030` → `http://localhost:3030`
- 浏览器手动调至 1920×1080，隐藏地址栏/书签栏

---

## 录屏面板隐藏（仅TOC）

Slidev 在导出和UI层面都会生成目录(TOC)。我们通过配置+CSS组合禁用：
1. 配置：`export.withToc: false` → 导出 PDF/PPTX 不生成目录页
2. CSS：只隐藏UI层面的TOC面板，防止录屏时遮挡内容。覆盖以下：

1. **Slidev 内置TOC面板**：`#slidev-toc`, `.slidev-toc`, `.slidev-toc-list`
2. **通用语义元素**：`.toc`, `.toc-overlay`
3. **属性模糊匹配（兜底）**：`[class*="toc"]`, `[id*="slidev-toc"]`

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

> 放在 `slides.md` 的 `<style>` 块中，紧跟动画降级 CSS 之后。

---

## Slidev 配置模板

### frontmatter（`slides.md` 顶部）

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

关键字段：

- `theme`：必须为 `'@enyineer/slidev-theme-neocarbon'`
- `transition: fade`：幻灯片过渡动画（可选 `none` 禁用）
- `highlighter: shiki`：代码高亮引擎（内置，无需额外依赖）
- `fonts.provider: none`：禁止 Google Fonts CDN 自动请求

### `package.json`

```json
{
  "name": "ppt-project",
  "private": true,
  "scripts": {
    "build": "slidev build",
    "dev": "slidev --open",
    "export": "slidev export"
  },
  "dependencies": {
    "@slidev/cli": "52.0.0",
    "@enyineer/slidev-theme-neocarbon": "1.0.8"
  }
}
```

**注意**：版本为精确版本（无 `^`），避免 caret 范围引入 breaking changes。

### 环境要求

| 依赖 | 版本 |
|------|------|
| Node.js | >= 20.12.0 |
| npm | >= 9 |

---

## neocarbon 布局 API

### `cover` — 封面

```markdown
---
layout: cover
---
# 主标题

副标题或数据来源
```

### `section` — 章节分隔

```markdown
---
layout: section
---
# 章节名称
```

全屏分隔页，居中标题 + accent 下划线。

### `quote` — 引用

```markdown
---
layout: quote
---
> 引用文本内容

— 来源标注
```

超大引号标记 + 径向辉光。来源用 `—` 开头。

### `comparison` — 左右对比

```markdown
---
layout: comparison
---
::left::
左侧内容（暗面背景）

::right::
右侧内容（成功色调渐变）
```

使用 `::left::` / `::right::` 插槽分隔。

### `statement` — 金句/陈述

```markdown
---
layout: statement
---
# 核心陈述或金句

<span class="nc-text-muted">副标题或脚注</span>
```

全屏戏剧性陈述，支持换行高亮。多行金句（如"你可以让AI写一千个方案..."）使用此布局。

### `metrics` — 并排指标卡

```markdown
---
layout: metrics
---
::metrics::
<div class="nc-metric">
  <span class="nc-metric-value nc-text-danger">19%</span>
  <span class="nc-metric-label">新手放弃率</span>
</div>
<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">5-7%</span>
  <span class="nc-metric-label">专家放弃率</span>
</div>
```

每张卡使用 `.nc-metric` 包裹，`.nc-metric-value` 显示大数字，`.nc-metric-label` 显示标签。

### `diagram` — 图表分屏

```markdown
---
layout: diagram
---
::left::
图表说明文字

- 数据趋势解读
- 关键发现

::right::
```mermaid
graph TD
  A[碰壁] --> B{新手}
  A --> C{专家}
  B --> D[放弃 19%]
  C --> E[翻盘 15%]
```
```

**注意**：`diagram` 是分屏布局——左侧放文字说明，右侧放 Mermaid 图表。**不是**全屏图表。

### `default` — 正文（自由布局）

用于嵌入 neocarbon 组件或自定义内容：

```markdown
---
layout: default
---
# 幻灯片标题

<NcBarChart
  title="AI辅助编码 · 部分成功率"
  :labels="['软件工程师', '其他职业']"
  :data="[89, 88]"
  :colors="['var(--nc-success)', 'var(--nc-accent)']"
/>

<span class="nc-text-muted">数据来源：Anthropic 2026.6</span>
```

### `browser` — 浏览器截图展示

```markdown
---
layout: browser
props:
  url: 'https://example.com/dashboard'
---
![dashboard](/screenshots/dashboard.png)
```

模拟浏览器窗口，URL 栏显示 `props.url`。适合展示 Web 产品截图、数据平台界面。

### `spotlight` — 聚焦聚光灯

```markdown
---
layout: spotlight
---
# 唯一重要的那句话

<span class="nc-text-muted">脚注或来源</span>
```

全黑背景 + 聚光灯光锥，聚焦居中标题。适合章节高潮、核心洞察、转折点。

### `<NcTerminal />` — 终端模拟器

```html
<NcTerminal
  title="部署命令"
  :lines="[
    '$ npm run build',
    '✓ Build successful',
    '$ npx serve dist -p 3030',
    '→ Local: http://localhost:3030',
  ]"
/>
```

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 否 | 终端标题栏 |
| `lines` | string[] | 是 | 逐行显示的终端内容 |

逐行显示终端输出，带闪烁光标效果。用于展示部署步骤、CLI 工具输出。

### `<NcSteps />` — 多步流程

```html
<NcSteps
  :steps="[
    { title: '提取数据', status: 'done' },
    { title: '生成文案', status: 'done' },
    { title: '设计方案', status: 'active' },
    { title: '实现构建', status: 'pending' },
  ]"
/>
```

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `steps` | object[] | 是 | 步骤数组，每项含 `title`（string）和 `status`（`done`/`active`/`pending`） |

水平步骤指示器。`done`=绿色勾, `active`=accent 高亮, `pending`=灰色。

### `<NcFlipCard />` — 翻转卡片

```html
<NcFlipCard>
  <template #front>
    <h3>默会知识</h3>
  </template>
  <template #back>
    <p>靠经验积累、说不清楚但会用的知识</p>
  </template>
</NcFlipCard>
```

使用 Vue 具名插槽 `#front` / `#back`。3D 翻转卡片，正面概念/背面解释。适合术语定义、案例对比。

### `<NcHeatmap />` — GitHub 风格热力图

```html
<NcHeatmap
  title="AI 使用频率（周）"
  :data="{ 'Mon': 12, 'Tue': 19, 'Wed': 25, 'Thu': 22, 'Fri': 18, 'Sat': 8, 'Sun': 5 }"
/>
```

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 否 | 图表标题 |
| `data` | object | 是 | 键值对，key 为标签，value 为数值 |

GitHub 贡献热力图风格，适合展示频率、活跃度、时间分布数据。

### `<NcRoiCard />` — 金融指标卡片

```html
<NcRoiCard
  label="年化收益"
  value="23.5%"
  trend="up"
  color="var(--nc-success)"
/>
```

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `label` | string | 是 | 指标名称 |
| `value` | string | 是 | 指标值（含单位） |
| `trend` | string | 否 | `up` / `down` / `flat`，显示趋势箭头 |
| `color` | string | 否 | 文字颜色（CSS 颜色值） |

KPI / ROI 指标展示卡片，适合金融、商业数据。

### `<NcLineChart />` — 多线趋势扩展示例（双 Y 轴风格）

> 补充现有 `<NcLineChart />` API 的进阶用法。

当两组数据量级差距大时（如百分比 vs 绝对数量），将数据集分组渲染：

```html
<NcLineChart
  title="AI 使用深度 × 焦虑指数（2025）"
  :labels="['Q1', 'Q2', 'Q3', 'Q4']"
  :datasets="[
    { label: '使用深度（小时/周）', data: [5, 12, 22, 35], color: 'var(--nc-accent)' },
    { label: '焦虑指数（0-100）', data: [30, 45, 62, 78], color: 'var(--nc-danger)' },
  ]"
/>
```

> neocarbon `<NcLineChart />` 基于 Chart.js，**不原生支持双 Y 轴**。
> 若需真正的双 Y 轴，建议用 CSS 标注两组数据量级（如本例：左轴小时 / 右轴指数），
> 或使用 `default` 布局 + Mermaid 自定义折线图。

---

## neocarbon 组件 API

组件以 Vue 标签在 Markdown 中调用。**关键**：必须使用 `:` 前缀绑定非字符串 props（`:labels`, `:data`, `:colors` 等数组/数字）。

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

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `title` | string | 否 | 图表标题 |
| `labels` | string[] | 是 | X 轴标签 |
| `data` | number[] | 是 | 数据值（百分比 0-100 或绝对数值） |
| `colors` | string[] | 否 | 柱颜色（CSS 颜色值），默认使用主题色 |
| `height` | number | 否 | 图表高度（px），默认 240 |
| `horizontal` | boolean | 否 | 水平柱状图 |

### `<NcProgress />` — 进度条

```html
<NcProgress value="15" label="新手严格成功率" color="var(--nc-danger)" />
<NcProgress value="33" label="高级严格成功率" color="var(--nc-accent)" />
```

| Prop | 类型 | 必填 | 说明 |
|------|------|------|------|
| `value` | number | 是 | 百分比值（0-100） |
| `label` | string | 否 | 进度条标签 |
| `color` | string | 否 | 进度条颜色（CSS 颜色值） |

### `<NcLineChart />` — 折线图

用于趋势数据（如 7 个月变化）：

```html
<NcLineChart
  title="会话类型变化（7个月）"
  :labels="['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr']"
  :datasets="[
    { label: '修复代码', data: [33, 30, 27, 25, 22, 20, 19], color: 'var(--nc-danger)' },
    { label: '写新代码', data: [10, 12, 14, 16, 18, 19, 20], color: 'var(--nc-success)' },
    { label: '数据分析', data: [10, 11, 13, 15, 17, 19, 20], color: 'var(--nc-accent)' },
  ]"
/>
```

| Prop | 类型 | 说明 |
|------|------|------|
| `title` | string | 图表标题 |
| `labels` | string[] | X 轴标签 |
| `datasets` | object[] | 数据集数组，每项包含 `label`, `data`, `color` |

---

## 自定义 CSS 辅助（无原生映射的内容类型）

以下类型 neocarbon 无 1:1 原生支持，需在 `slides.md` 的 `<style>` 块中添加少量 CSS：

### 阶梯图（3 根依次增高柱）

```html
<NcBarChart
  title="严格验证成功率"
  :labels="['新手', '中级', '高级']"
  :data="[15, 28, 33]"
  :colors="['var(--nc-danger)', 'var(--nc-accent)', 'var(--nc-accent)']"
/>
```

### Before/After 柱对比

```html
<NcBarChart
  title="修复代码占比变化"
  :labels="['修复代码']"
  :data="[19]"
  :colors="['var(--nc-danger)']"
/>
<div class="nc-text-muted" style="text-align:center; margin-top: 8px;">
  33% → <span class="nc-text-danger">19%</span>（7个月）
</div>
```

用单个柱 + 文字标注 before/after 值。

### Mermaid 流程图（分叉路径）

```mermaid
graph TD
  A[🤖 AI报错 / 输出不对] --> B{新手}
  A --> C{专家}
  B --> D[放弃 19%]
  B -.-> E[翻盘 4%]
  C --> F[放弃 5-7%]
  C --> G[翻盘 15%]

  style D fill:#ef4444,color:#fff
  style G fill:#22c55e,color:#fff
```

放在 `diagram` 布局的 `::right::` 插槽中。

---

### v-click 使用示例

**逐个淡入（默认 fade，无需写修饰符）：**

```markdown
<v-clicks>
- 第一点
- 第二点
- 第三点
</v-clicks>
```

**嵌套列表逐层展开：**

```markdown
<v-clicks depth="2">
- 大类 A
  - 细节 1
  - 细节 2
- 大类 B
  - 细节 3
</v-clicks>
```

**指定出现/消失时机：**

```markdown
<v-click="[2, 4]">第 2 次点击出现，第 4 次消失</v-click>
```

### slide 总点击数

复杂幻灯片用 frontmatter 显式指定总点击数，防止 Slidev 自动计算出错：

```markdown
---
clicks: 5
---
```
