# article-to-presentation HTML 引擎重构实施计划

## 目标

将 `.opencode/skills/article-to-presentation/` 从 Slidev/neocarbon 架构迁移为纯 Python HTML 模板引擎，输出单文件 `slides.html`，支持多页切换、多种布局与图表。

依赖 spec：`docs/superpowers/specs/2026-06-25-article-to-presentation-html-engine-design.md`

---

## 阶段一：清理与脚手架

### 任务 1.1 归档旧 Slidev 文档

- 创建 `docs/archive/slidev/`
- 移动以下文件（保留 git 历史）：
  - `docs/superpowers/specs/2026-06-22-article-to-presentation-skill更新设计.md`
  - `docs/superpowers/specs/2026-06-22-article-to-presentation-slidev-design.md`
  - `docs/superpowers/specs/2026-06-22-AI压缩执行力-Slidev设计.md`
  - `docs/superpowers/specs/2026-06-22-AI压缩执行力PPT设计.md`
  - `docs/superpowers/specs/2026-06-22-AI压缩执行力PPT文案.md`
  - `docs/superpowers/specs/2026-06-22-PPT显示优化设计.md`
  - `docs/superpowers/specs/2026-06-23-article-to-presentation-optimization-design.md`
  - `docs/superpowers/specs/2026-06-23-article-to-presentation-remove-toc-css.md`
  - `docs/superpowers/plans/2026-06-22-AI-execution-judgment-slidev.md`
  - `docs/superpowers/plans/2026-06-23-Apple-Core-AI-PPT.md`
  - `docs/superpowers/plans/2026-06-23-superapp-agentize-ppt.md`
  - `docs/superpowers/plans/2026-06-23-超级App换芯-PPT实施计划.md`
  - `docs/superpowers/plans/2026-06-23-article-to-presentation-optimization.md`
  - `docs/superpowers/plans/2026-06-23-article-to-presentation-remove-toc-css.md`
  - `docs/superpowers/plans/20260623-从AGI到ASI-ppt-implementation-plan.md`
  - `docs/superpowers/plans/2026-06-24-deepseek-agent-recruitment-slides.md`

### 任务 1.2 清理冗余文件

- 删除 `content/ppt/2026-06-23-Apple-Core-AI/package.json`
- 保留旧 `slides.md` 和 `dist/` 作为历史产物，不删除

### 任务 1.3 创建 skill 目录结构

```text
.opencode/skills/article-to-presentation/
├── SKILL.md
├── references/
│   └── README.md
├── parser/
│   ├── __init__.py
│   └── markdown_parser.py
├── prompts/
│   ├── slide_prompt.md
│   └── visual_prompt.md
├── renderer/
│   ├── __init__.py
│   └── html_renderer.py
├── templates/
│   ├── base.html
│   ├── cover-hero-split.html
│   ├── cover-hero-center.html
│   ├── section-chapter.html
│   ├── compare-before-after-metric.html
│   ├── compare-before-after-cards.html
│   ├── compare-three-column-flow.html
│   ├── table-comparison-table.html
│   ├── data-big-number.html
│   ├── data-metric-cards.html
│   ├── data-bar-chart.html
│   ├── data-line-chart.html
│   ├── data-area-chart.html
│   ├── data-pie-chart.html
│   ├── data-doughnut-chart.html
│   ├── data-radar-chart.html
│   ├── data-mixed-chart.html
│   ├── data-horizontal-bar-chart.html
│   ├── layout-simple-text.html
│   ├── layout-split-text-image.html
│   ├── layout-full-image.html
│   ├── layout-two-column-text.html
│   ├── process-vertical-steps.html
│   ├── process-horizontal-steps.html
│   ├── process-timeline.html
│   ├── terminal-code-terminal.html
│   ├── quote-quote-center.html
│   ├── quote-quote-with-source.html
│   ├── summary-summary-list.html
│   └── summary-key-takeaways.html
├── scripts/
│   └── generate.py
└── assets/
    └── (可选：bg-grid.svg, glow.svg — 优先内联)
```

---

## 阶段二：核心引擎实现

### 任务 2.1 parser/markdown_parser.py

输入：markdown 字符串。
输出：Python dict，含 `title`、`subtitle`、`sections`、`metrics`、`quotes`、`sources`。

实现要点：
- 使用 `markdown` 库解析 AST 或正则提取
- 提取 `#` 标题、`##` 章节、列表、引用块
- 识别数字模式作为 metrics 候选
- 输出可序列化为 `PPT文案.md` 的结构

### 任务 2.2 prompts/slide_prompt.md

指导 LLM 根据 `PPT文案.md` 生成 `slides.json`。

必须包含：
- 每页一个观点
- 可选 type/visual 清单
- 输出 JSON 格式样例
- 禁止解释

### 任务 2.3 prompts/visual_prompt.md

指导 LLM 根据 `slides.json` 补充 `data`、`colors`、`animations`。

必须包含：
- 视觉组件选择规则
- 颜色语义（正面/负面/中性）
- 动画类型说明
- 输出 JSON 格式样例

### 任务 2.4 renderer/html_renderer.py

- 使用 Jinja2 加载 `templates/`
- 渲染 `base.html`，注入 `slides` 数组
- 每个 slide 根据 `type` + `visual` 选择模板
- 生成单文件 `slides.html`
- 提供 CLI：`python -m renderer.html_renderer --slides slides.json --output slides.html`

### 任务 2.5 templates/base.html

- 内联完整 CSS（设计系统 + 14 个组件 + 动画）
- 内联 JS（翻页、动画触发、数字增长、hash 同步）
- 遍历 slides 渲染 `<section class="slide">`
- 底部 footer：来源 + 页码

### 任务 2.6 组件模板

先实现 6 个高优先级模板（覆盖截图）：
1. `cover-hero-split.html`
2. `compare-before-after-metric.html`
3. `compare-before-after-cards.html`
4. `compare-three-column-flow.html`
5. `table-comparison-table.html`
6. `data-metric-cards.html`

后续再补全：
7. `cover-hero-center.html`
8. `section-chapter.html`
9. `data-big-number.html`
10. `data-bar-chart.html`
11. `data-line-chart.html`
12. `quote-quote-center.html`
13. `summary-summary-list.html`

### 任务 2.7 scripts/generate.py

主入口脚本：

```bash
python .opencode/skills/article-to-presentation/scripts/generate.py \
  --input content/article/2026-06-25-claude-md-slim.md \
  --output content/ppt/2026-06-25-claude-md-slim/
```

步骤：
1. 读取输入 markdown
2. 调用 parser 生成 `PPT文案.md`
3. 调用 LLM①（slide_prompt）生成 `slides.json`
4. 调用 LLM②（visual_prompt）丰富 `slides.json`
5. 调用 renderer 生成 `slides.html`

---

## 阶段三：Skill 文档重写

### 任务 3.1 重写 SKILL.md

- 更新 frontmatter description
- 替换 6 阶段流程为 HTML 引擎流程
- 更新 When to Use / When NOT to Use
- 更新输出路径与文件结构
- 更新构建/预览命令（从 `slidev build` 改为 Python 脚本 + 浏览器打开 `slides.html`）

### 任务 3.2 重写 references/README.md

- 说明新 references 结构
- 列出模板清单与数据 schema
- 说明常见陷阱（JSON 格式、模板名称、颜色语义）

---

## 阶段四：根项目更新

### 任务 4.1 更新 package.json

- 删除 `@slidev/cli`
- 删除 `@enyineer/slidev-theme-neocarbon`
- 删除 `@playwright/test`
- 删除 `slidev:build` 脚本
- 若不再需要，删除整个 `package.json` 或保留为空（视其他依赖而定）

### 任务 4.2 重新生成 package-lock.json

- 运行 `npm install` 或删除 `package-lock.json`（若 `package.json` 无依赖）

### 任务 4.3 更新 AGENTS.md

- 修改 `content/ppt/` 描述
- 删除 `npm run slidev:build` 说明
- 更新 `article-to-presentation` 技能描述

### 任务 4.4 更新 README.md

- 更新技能描述
- 更新目录树说明
- 更新技术栈
- 删除 Slidev/neocarbon 相关引用

---

## 阶段五：验证

### 任务 5.1 功能验证

- 用一篇现有文章（如 `AI压缩了执行力`）测试生成流程
- 检查 `slides.html` 可直接浏览器打开
- 检查键盘翻页、页码、动画正常
- 检查 1920×1080 下无布局溢出

### 任务 5.2 回归检查

- 确认旧 `content/ppt/` 目录未被破坏
- 确认 `npm run slidev:build` 不再存在
- 确认 `package.json` 无 Slidev 依赖

### 任务 5.3 文档一致性

- spec、plan、SKILL.md、AGENTS.md、README.md 描述一致
- 无 Slidev/neocarbon 残留引用

---

## 交付物清单

| 文件 | 说明 |
|------|------|
| `docs/superpowers/specs/2026-06-25-article-to-presentation-html-engine-design.md` | 设计文档（已完成） |
| `docs/superpowers/plans/2026-06-25-article-to-presentation-html-engine-plan.md` | 本计划 |
| `.opencode/skills/article-to-presentation/SKILL.md` | 新 skill 定义 |
| `.opencode/skills/article-to-presentation/parser/markdown_parser.py` | Markdown 解析器 |
| `.opencode/skills/article-to-presentation/prompts/*.md` | LLM prompts |
| `.opencode/skills/article-to-presentation/renderer/html_renderer.py` | HTML 渲染器 |
| `.opencode/skills/article-to-presentation/templates/*.html` | Jinja2 模板 |
| `.opencode/skills/article-to-presentation/scripts/generate.py` | 主入口 |
| `package.json` / `package-lock.json` | 移除 Slidev 依赖 |
| `AGENTS.md` / `README.md` | 更新描述 |

---

## 执行顺序

```
阶段一 → 阶段二（2.1–2.7 可并行） → 阶段三 → 阶段四 → 阶段五
```

阶段二内部优先级：
1. `base.html` + CSS/JS 骨架
2. `html_renderer.py`
3. 6 个高优先级组件模板
4. `markdown_parser.py`
5. prompts
6. `generate.py`
7. 剩余 7 个模板
