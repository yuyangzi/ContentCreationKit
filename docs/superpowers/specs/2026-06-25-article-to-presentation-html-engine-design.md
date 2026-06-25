# article-to-presentation HTML 引擎重构设计

## 1. 背景与目标

将现有基于 Slidev + neocarbon 的 `article-to-presentation` skill，重构为 **Markdown → AI 内容分析 → Slide DSL → 视觉组件规划 → HTML 模板引擎 → 单文件科技风 HTML 演示文稿** 的管线。

目标视觉风格参考「慢学AI」系列：深色网格背景、高对比强调色、大号数字、组件化信息图、16:9 固定画幅、键盘翻页、底部页码，适用于 B站录屏与公众号视频。

## 2. 核心原则

- **单文件输出**：最终产物为 `slides.html`，所有 CSS/JS/字体引用内联或基于 CDN，可直接 `file://` 打开。
- **无 Node 构建**：渲染引擎用 Python，删除 `@slidev/cli` 与 neocarbon 依赖。
- **组件驱动**：每页幻灯片对应一个明确的 `type` + `visual` 组合，由 LLM 根据内容选择。
- **人可审阅的中间产物**：保留 `PPT文案.md` 与 `PPT设计.md`，新增 `slides.json`（Slide DSL）。
- **录屏优先**：动画以 CSS 为主，稳定、无离线风险、无第三方 CDN 阻塞。

## 3. 整体架构

```text
Markdown 文章
   ↓
parser/markdown_parser.py          # 提取标题、章节、关键数据、金句、来源
   ↓
PPT文案.md（人工可编辑）
   ↓
prompts/slide_prompt.md + LLM①    # 内容拆页
   ↓
slides.json  Slide DSL
   ↓
prompts/visual_prompt.md + LLM②   # 视觉组件规划
   ↓
renderer/html_renderer.py          # Jinja2 模板渲染
   ↓
slides.html                        # 单文件科技风演示文稿
```

## 4. 输出目录

沿用 `content/ppt/YYYY-MM-DD-<topic>/` 约定：

```text
content/ppt/2026-06-25-claude-md-slim/
├── PPT文案.md          # 保留：核心论点、关键数据、故事线、金句、来源
├── PPT设计.md          # 保留：配色、动画档位、布局映射表
├── slides.json         # 新增：Slide DSL
└── slides.html         # 新增：最终单文件演示文稿
```

> `dist/` 目录消失；`slides.md` 被 `slides.json` + `slides.html` 替代。

## 5. Slide DSL 规范

`slides.json` 为一个对象数组，每页一张幻灯片。

```typescript
interface Slide {
  type: 'cover' | 'section' | 'compare' | 'timeline' | 'data' | 'quote' | 'summary' | 'table';
  visual: string;           // 具体视觉组件名
  title?: string;
  subtitle?: string;
  eyebrow?: string;         // 顶部小标签，如 "PROBLEM · 指令稀释"
  badge?: number | string;  // 左上角序号徽章
  data?: any;               // 视觉组件所需数据
  source?: string;          // 数据来源
  transition?: 'fade' | 'none'; // 单页动画开关
}
```

### 5.1 页面类型与视觉组件映射

根据用户提供的截图，定义以下视觉组件：

| 页面类型 | 视觉组件 | 用途 | 参考截图 |
|---------|---------|------|---------|
| `cover` | `hero-split` | 封面：左文右图（标题 + 信息图） | 图 1 |
| `cover` | `hero-center` | 封面：居中标题 + 副标题 | - |
| `section` | `chapter` | 章节分隔页：大序号 + 章节名 | - |
| `compare` | `before-after-metric` | 前后对比：大数字 + 箭头 | 图 3 |
| `compare` | `before-after-cards` | 前后对比：左右卡片 + 中央箭头 | 图 5 |
| `compare` | `three-column-flow` | 三栏概念流：输入 → 核心 → 结果 | 图 2 |
| `table` | `comparison-table` | 三列对照表：类别/重构前/重构后 | 图 8 |
| `data` | `big-number` | 单页大数字强调 | - |
| `data` | `metric-cards` | 并排指标卡（带 A/B/C 徽章） | 图 3 |
| `data` | `bar-chart` | 柱状图（ECharts） | - |
| `data` | `line-chart` | 折线图（ECharts） | - |
| `data` | `area-chart` | 面积图（ECharts） | - |
| `data` | `pie-chart` | 饼图/环形图（ECharts） | - |
| `data` | `doughnut-chart` | 甜甜圈图（ECharts） | - |
| `data` | `radar-chart` | 雷达图（ECharts） | - |
| `data` | `mixed-chart` | 混合图：柱状 + 折线（ECharts） | - |
| `data` | `horizontal-bar-chart` | 条形图（ECharts） | - |
| `layout` | `simple-text` | 纯文本内容页 | - |
| `layout` | `split-text-image` | 左文右图/右图左文 | - |
| `layout` | `full-image` | 全屏图片 + 标题叠加 | - |
| `layout` | `two-column-text` | 双栏文本对比 | - |
| `process` | `vertical-steps` | 垂直步骤流程 | - |
| `process` | `horizontal-steps` | 水平步骤流程 | - |
| `process` | `timeline` | 时间轴 | - |
| `terminal` | `code-terminal` | 终端代码展示（模拟 NcTerminal） | - |
| `quote` | `quote-center` | 居中引用页 | - |
| `quote` | `quote-with-source` | 引用 + 来源 | - |
| `summary` | `summary-list` | 总结清单页 | - |
| `summary` | `key-takeaways` | 要点卡片矩阵 | - |

## 6. 视觉设计系统

### 6.1 画布

- 比例：16:9
- 基准尺寸：1920 × 1080（CSS px，使用 `vw`/`vh` 或 `rem` 缩放）
- 安全边距：左右 80px，上下 60px

### 6.2 颜色

```css
:root {
  --bg: #07111f;
  --bg-grid: rgba(255, 255, 255, 0.03);
  --panel: rgba(20, 26, 42, 0.85);
  --panel-border: rgba(255, 255, 255, 0.08);
  --text-primary: #ffffff;
  --text-secondary: #9aa5b8;
  --text-muted: #5c6b7f;
  --accent-orange: #ff9d3d;
  --accent-blue: #4db6ff;
  --accent-green: #4ade80;
  --accent-purple: #a78bfa;
  --accent-red: #ff6b5c;
  --accent-pink: #e85b7a;
}
```

背景使用 CSS 渐变 + 网格线：

```css
background:
  radial-gradient(circle at 80% 20%, rgba(77, 182, 255, 0.08), transparent 40%),
  linear-gradient(to bottom, #07111f, #0a1525),
  linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
  linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
background-size: 100% 100%, 100% 100%, 40px 40px, 40px 40px;
```

### 6.3 字体

```css
font-family: 'PingFang SC', 'Microsoft YaHei', 'Noto Sans SC', sans-serif;
```

### 6.4 字号层级

| 元素 | 字号 | 字重 |
|------|------|------|
| 封面主标题 | 72px | 700 |
| 页面主标题 | 56px | 700 |
| 大数字 | 96px | 800 |
| 卡片标题 | 28px | 600 |
| 正文 | 24px | 400 |
| 来源/脚注 | 16px | 400 |
| 顶部 eyebrow | 16px | 600，letter-spacing: 0.1em |

## 7. HTML 模板体系

模板使用 Jinja2，每个 `type + visual` 组合对应一个模板文件。

```text
.opencode/skills/article-to-presentation/templates/
├── base.html                  # 整体骨架、CSS、JS 导航
├── cover-hero-split.html
├── cover-hero-center.html
├── section-chapter.html
├── compare-before-after-metric.html
├── compare-before-after-cards.html
├── compare-three-column-flow.html
├── table-comparison-table.html
├── data-big-number.html
├── data-metric-cards.html
├── data-bar-chart.html
├── data-line-chart.html
├── quote-quote-center.html
└── summary-summary-list.html
```

### 7.1 base.html 职责

- 内联完整 CSS（设计系统 + 所有组件样式 + 动画）
- 内联 JS：键盘翻页（←/→）、页码更新、IntersectionObserver 触发动画、数字增长动画
- 遍历 `slides` 数组，渲染 `<section class="slide">` 序列

### 7.2 单页结构

```html
<section class="slide" data-index="0" data-transition="fade">
  <div class="slide-content">
    <!-- 组件模板内容 -->
  </div>
  <div class="slide-footer">
    <span class="source">原文：Steering Claude Code</span>
    <span class="page">1 / 9</span>
  </div>
</section>
```

## 8. 动画与交互

### 8.1 翻页导航

- 键盘：← 上一页，→ 下一页，Home 到首页，End 到末页
- 触屏：左右滑动
- URL hash 同步：`#slide-3`

### 8.2 页面切换动画

默认 `fade`：当前页 opacity 1→0，新页 opacity 0→1，duration 400ms。
可全局或单页设为 `none`。

### 8.3 元素入场动画

通过 `data-animate` 属性 + IntersectionObserver 触发：

```css
[data-animate="fade-up"] {
  opacity: 0;
  transform: translateY(40px);
  transition: all 0.8s cubic-bezier(0.22, 1, 0.36, 1);
}
[data-animate="fade-up"].is-visible {
  opacity: 1;
  transform: translateY(0);
}
```

动画类型：`fade-up`、`fade-left`、`fade-right`、`scale-in`、`count-up`。

### 8.4 数字增长动画

```javascript
function animateNumber(el, target, duration = 1500) {
  const start = performance.now();
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    el.textContent = Math.floor(target * easeOutQuart(p)).toLocaleString();
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}
```

## 9. 图表支持

### 9.1 轻量图表（优先）

柱状图、折线图优先使用 **ECharts 5 CDN**，在 `base.html` 中按需引入：

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/echarts.min.js"></script>
```

> 若 CDN 不可用，降级为纯 CSS/SVG 条形图。

### 9.2 概念图

截图中的「Before/After 卡片 + 箭头」「三栏概念流」「对照表」均为独立模板，不依赖图表库。

## 10. parser 与 prompts

### 10.1 parser/markdown_parser.py

输入：文章 markdown 字符串。
输出：

```python
{
  "title": "怎么给 CLAUDE.md 瘦身？",
  "subtitle": "500 行项目规则拆回正确位置",
  "source": "Steering Claude Code — skills, hooks, subagents and more",
  "sections": [
    {"title": "问题：指令稀释", "content": "..."},
    {"title": "根文件变回项目地图", "content": "..."}
  ],
  "metrics": [{"label": "重构前", "value": 500}, {"label": "重构后", "value": 150}],
  "quotes": [...],
  "sources": [...]
}
```

### 10.2 prompts/slide_prompt.md

指导 LLM 将 `PPT文案.md` 转换为 `slides.json`。要求：
- 每页只表达一个观点
- 必须为每页选择 `type` 和 `visual`
- 输出 JSON，不解释

### 10.3 prompts/visual_prompt.md

指导 LLM 为每页补充 `data`、`colors`、`animations` 等渲染数据。规则：
- 出现「过去/现在/之前/之后/对比」→ `compare-*`
- 出现「步骤/流程/阶段」→ `timeline` 或 `metric-cards`
- 出现「数字/百分比」→ `big-number` 或 `bar-chart`
- 出现「引用/金句」→ `quote-center`

## 11. 命令入口

新增或复用 `/article-to-presentation` 命令（或保留现有触发词）。

```bash
# 从文章生成完整 PPT
python .opencode/skills/article-to-presentation/scripts/generate.py \
  --input content/article/2026-06-25-claude-md-slim.md \
  --output content/ppt/2026-06-25-claude-md-slim/
```

阶段保持 6 阶段框架，但阶段六从 `slidev build` 变为 Python 渲染 + 浏览器预览。

## 12. 迁移策略

### 12.1 保留

- `content/ppt/` 目录结构与命名约定
- `PPT文案.md`、`PPT设计.md` 文件概念
- 6 阶段流程框架
- 深色科技风视觉规范
- 数据验证规则（≥6 来源、一手/二手区分）

### 12.2 删除

- 根 `package.json` 中 `@slidev/cli`、`@enyineer/slidev-theme-neocarbon`、`@playwright/test`
- `npm run slidev:build` 脚本
- `slides.md` 中间格式
- neocarbon 布局/组件 API 与相关 CSS hack
- `references/technical-details.md` 与 `common-pitfalls.md` 中的 Slidev 专用内容
- `content/ppt/2026-06-23-Apple-Core-AI/package.json` 冗余文件

### 12.3 重构

- `SKILL.md`：迁移到 HTML 引擎流程
- 新增 `parser/`、`prompts/`、`templates/`、`renderer/`、`scripts/`
- 输出产物改为 `slides.json` + `slides.html`
- 动画系统从 Slidev transition/v-click 改为 CSS/JS
- 图表从 neocarbon Vue 组件改为 ECharts/纯 CSS
- 更新 `AGENTS.md`、`README.md` 描述

### 12.4 历史产物处理

旧 `docs/superpowers/specs/` 与 `plans/` 中 Slidev 相关文档移动到 `docs/archive/slidev/`。

## 13. 风险与应对

| 风险 | 应对 |
|------|------|
| 旧 PPT 无法再用新引擎复现 | 保留旧 `slides.md` 作为只读参考；新文章走新流程 |
| ECharts CDN 离线不可用 | 降级为纯 CSS/SVG 图表；复杂图表页提示用户联网 |
| LLM 视觉组件选择不准 | `visual_prompt.md` 中给出明确规则；`PPT设计.md` 人工可覆盖 |
| 单文件 HTML 过大 | 图片资源外部化；CSS/JS 压缩；ECharts 按需加载 |
| 动画在录屏中不流畅 | 默认关闭复杂动画；优先使用 opacity/transform 硬件加速 |

## 14. 下一步

本 spec 审核通过后，进入 `/plan-review` 或 `writing-plans` 阶段，产出 `docs/superpowers/plans/2026-06-25-article-to-presentation-html-engine-plan.md` 实施计划。
