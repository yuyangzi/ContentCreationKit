# article-to-presentation 参考文档

本目录保留与 HTML 演示文稿引擎相关的参考信息。旧 Slidev/neocarbon 相关文档已归档到 `docs/archive/slidev/`。

Agent 定义（prompts）已移至 `.opencode/agents/context-cover.md` 和 `.opencode/agents/visual-cover.md`。

## 目录

- `../SKILL.md` — 技能主文档与完整工作流程
- `../../.opencode/agents/context-cover.md` — context-cover agent（内容拆页）
- `../../.opencode/agents/visual-cover.md` — visual-cover agent（视觉填充）
- `../templates/` — Jinja2 HTML 模板（29 个）
- `../parser/markdown_parser.py` — Markdown 解析器
- `../renderer/html_renderer.py` — HTML 渲染器
- `../renderer/validate_slides.py` — Schema 自动校验
- `../scripts/generate.py` — 一键生成入口

## 模板清单

| 模板文件 | type | visual | 用途 |
|---------|------|--------|------|
| `cover-hero-split.html` | cover | hero-split | 左文右图封面 |
| `cover-hero-center.html` | cover | hero-center | 居中标题封面 |
| `section-chapter.html` | section | chapter | 章节分隔 |
| `compare-before-after-metric.html` | compare | before-after-metric | 前后大数字对比 |
| `compare-before-after-cards.html` | compare | before-after-cards | 前后卡片对比 |
| `compare-three-column-flow.html` | compare | three-column-flow | 三栏概念流 |
| `table-comparison-table.html` | table | comparison-table | 三列对照表 |
| `data-big-number.html` | data | big-number | 单页大数字 |
| `data-metric-cards.html` | data | metric-cards | 指标卡 |
| `data-bar-chart.html` | data | bar-chart | 柱状图（ECharts） |
| `data-line-chart.html` | data | line-chart | 折线图（ECharts） |
| `data-area-chart.html` | data | area-chart | 面积图（ECharts） |
| `data-pie-chart.html` | data | pie-chart | 饼图（ECharts） |
| `data-doughnut-chart.html` | data | doughnut-chart | 甜甜圈图（ECharts） |
| `data-radar-chart.html` | data | radar-chart | 雷达图（ECharts） |
| `data-mixed-chart.html` | data | mixed-chart | 混合图（ECharts） |
| `data-horizontal-bar-chart.html` | data | horizontal-bar-chart | 条形图（ECharts） |
| `layout-simple-text.html` | layout | simple-text | 纯文本内容 |
| `layout-split-text-image.html` | layout | split-text-image | 左文右图 |
| `layout-full-image.html` | layout | full-image | 全屏图片 |
| `layout-two-column-text.html` | layout | two-column-text | 双栏文本 |
| `process-vertical-steps.html` | process | vertical-steps | 垂直步骤 |
| `process-horizontal-steps.html` | process | horizontal-steps | 水平步骤 |
| `process-timeline.html` | process | timeline | 时间轴 |
| `terminal-code-terminal.html` | terminal | code-terminal | 终端代码 |
| `quote-quote-center.html` | quote | quote-center | 居中引用 |
| `quote-quote-with-source.html` | quote | quote-with-source | 引用 + 来源 |
| `summary-summary-list.html` | summary | summary-list | 总结清单 |
| `summary-key-takeaways.html` | summary | key-takeaways | 要点矩阵 |

## 颜色语义

- `orange`：中性强调、标签、封面高亮
- `blue`：信息/规则/路径
- `green`：正面/增长/成功/重构后
- `purple`：概念/Skill/子代理
- `red`：负面/下降/重构前/警告
- `pink`：安全/个人/敏感
- `cyan`：代码/技术术语

## 常见陷阱

1. **context-cover 选择了不存在的 type+visual 组合**：用 `validate_slides.py` 在渲染前检查。
2. **visual-cover data schema 不匹配模板**：严格对照 `.opencode/agents/visual-cover.md` 中的 schema。
3. **ECharts CDN 离线**：图表页需联网，离线时图表不渲染。
4. **数字未动画**：大数字必须用 `data-count` 属性，JS 自动触发数字增长。
5. **目录名含中文**：`content/ppt/` 子目录名建议纯 ASCII。
