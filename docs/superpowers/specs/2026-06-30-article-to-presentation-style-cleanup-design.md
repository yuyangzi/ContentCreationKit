# Article-to-Presentation 样式系统清理

- **日期**: 2026-06-30
- **作者**: Sisyphus（基于与用户的 brainstorming 对话）
- **状态**: 设计已确认，待 spec 审查
- **影响范围**: `.opencode/skills/article-to-presentation/` + 2 个 agent 定义 + 1 个 design spec 文档

## 背景

`article-to-presentation` 技能在演进过程中形成了样式层面的新旧混用：

- 眉标（eyebrow）CSS 别名：`slide-kicker`（canonical）和 `eyebrow`（legacy）在 `base.html:137-146` 共享同一规则块，27 个 HTML 模板分裂成两组——13 个用新名、14 个仍用旧名。
- 数据键 `slide.eyebrow` 在全部 27 个模板中未迁移到 `slide.kicker`，与 CSS 类名方向相反。
- `layout-split-text-image.html:17` 的图像圆角为 `12px`，与其他元素的 `8px` 标准偏离。
- `table-comparison-table.html:19-20` 的 `<td>` 圆角为 `10px`，也是离群值。
- `layout-two-column-text.html` 与 `compare-three-column-flow.html` 共有 5 处内联样式的 `<h3>` 栏目标题，无对应 CSS 类。

本设计目标：彻底收口 eyebrow 别名（CSS 类 + 数据键）、统一圆角到 8px、提取栏目标题为 `.column-title` 类。不涉及 Python 逻辑改动——`renderer/html_renderer.py` 是 key-agnostic 的，不显式映射 eyebrow 字段。

## 目标与非目标

### 目标
1. 删除 `base.html` 中的 `.eyebrow` CSS 别名，仅保留 `.slide-kicker`
2. 14 个模板的 `class="eyebrow"` 改为 `class="slide-kicker"`
3. 27 个模板的 `{{ slide.eyebrow }}` 改为带 fallback 的 `{{ slide.kicker }}` 表达式，以兼容存量 slides.json
4. 同步更新外部文件（agent prompt、SKILL.md、design spec、test fixture）
5. `layout-split-text-image.html` 图像圆角 12px → 8px
6. `table-comparison-table.html` `<td>` 圆角 10px → 8px
7. 新增 `.column-title` / `.column-title--lg` CSS 类，提取 5 处内联 `<h3>`

### 非目标
- **不**重命名 `cover-title` / `cover-subtitle`（它们是清晰的语义命名，非新旧混用）
- **不**重命名 `item-title` 为 `card-title`（风格偏好，非债）
- **不**改动 `terminal-code-terminal.html` 的终端栏标题（14px，语义不同）
- **不**改 `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/PPT设计.md`（历史产物）
- **不**改 `docs/superpowers/plans/2026-06-24-DeepSeek-Agent-Strategy-PPT.md`（历史 plan 示例）
- **不**改动任何 Python 代码（renderer / parser / validator / generate.py）
- **不**引入 CSS 变量统一 radius（YAGNI，本次只收口离群值）

## 详细设计

### 1. eyebrow → kicker 统一

#### 1.1 CSS 层（`templates/base.html:137-146`）

**现状**：
```css
.slide-kicker,
.eyebrow {
  display: inline-block;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-orange);
  margin-bottom: 14px;
}
```

**目标**：
```css
.slide-kicker {
  display: inline-block;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-orange);
  margin-bottom: 14px;
}
```

#### 1.2 HTML 模板层（27 个文件）

两类改动同时应用到所有 27 个模板：

| 改动 | 适用范围 |
|------|---------|
| `class="eyebrow"` → `class="slide-kicker"` | 14 个模板（图表/表格/分栏/终端/全图组） |
| `{{ slide.eyebrow \| default('') }}` → `{{ slide.kicker \| default(slide.eyebrow \| default('')) }}` | 全部 27 个模板 |

**fallback 表达式的作用**：过渡期兼容。当 visual-cover / context-cover agent 已切换输出 `kicker` 字段，但仍有存量 slides.json 使用 `eyebrow` 字段时，模板先读 `kicker`，为空则回退到 `eyebrow`。1-2 个版本后可移除 fallback。

**完整的 27 个模板清单**（按字母序）：

1. `compare-before-after-cards.html`
2. `compare-before-after-metric.html`
3. `compare-three-column-flow.html`
4. `cover-hero-center.html`
5. `cover-hero-split.html`
6. `data-area-chart.html`（同时改 class）
7. `data-bar-chart.html`（同时改 class）
8. `data-big-number.html`
9. `data-doughnut-chart.html`（同时改 class）
10. `data-horizontal-bar-chart.html`（同时改 class）
11. `data-line-chart.html`（同时改 class）
12. `data-metric-cards.html`
13. `data-mixed-chart.html`（同时改 class）
14. `data-pie-chart.html`（同时改 class）
15. `data-radar-chart.html`（同时改 class）
16. `layout-full-image.html`（同时改 class）
17. `layout-simple-text.html`
18. `layout-split-text-image.html`（同时改 class）
19. `layout-two-column-text.html`（同时改 class）
20. `process-horizontal-steps.html`
21. `process-timeline.html`
22. `process-vertical-steps.html`
23. `section-chapter.html`
24. `summary-key-takeaways.html`
25. `summary-summary-list.html`
26. `table-comparison-table.html`（同时改 class）
27. `terminal-code-terminal.html`（同时改 class）

#### 1.3 外部文件同步

| 文件 | 行 | 改动 |
|------|----|------|
| `.opencode/skills/article-to-presentation/tests/test_template_rendering.py` | 19 | fixture `"eyebrow": "Agent Workflow"` → `"kicker": "Agent Workflow"` |
| 同上 | 27 | fixture `"eyebrow": "Context"` → `"kicker": "Context"` |
| 同上 | 36 | `self.assertIn("class=\"slide-kicker\"", html)` 保留不变（已经是新名） |
| `.opencode/skills/article-to-presentation/SKILL.md` | 136 | schema 文档 `eyebrow` → `kicker` |
| `.opencode/agents/context-cover.md` | 31 | 示例 JSON 键 `eyebrow` → `kicker` |
| `.opencode/agents/visual-cover.md` | 30 | 示例 JSON 键 `eyebrow` → `kicker` |
| `.opencode/agents/visual-cover.md` | 70 | 示例 JSON 键 `eyebrow` → `kicker` |
| `docs/superpowers/specs/2026-06-25-article-to-presentation-html-engine-design.md` | 61 | TS 类型字段 `eyebrow?: string` → `kicker?: string` |
| 同上 | 160 | 排版表 `顶部 eyebrow` → `顶部 kicker` |

### 2. 圆角统一

| 文件 | 行 | 现状 | 目标 |
|------|----|------|------|
| `templates/layout-split-text-image.html` | 17 | `border-radius: 12px` | `border-radius: 8px` |
| `templates/table-comparison-table.html` | 19 | `border-radius: 10px` | `border-radius: 8px` |
| `templates/table-comparison-table.html` | 20 | `border-radius: 10px` | `border-radius: 8px` |

不引入 `--radius-sm` CSS 变量。YAGNI——只有 2 处离群值需要收口，未来若新增 radius 需求再考虑变量化。

### 3. 内联 `<h3>` 提取为 `.column-title`

#### 3.1 新增 CSS 类（`templates/base.html`，放在 `.item-title` 附近）

```css
.column-title {
  font-size: 24px;
  font-weight: 700;
  line-height: 1.28;
  color: var(--text-secondary);
  margin-bottom: 24px;
}
.column-title--lg {
  font-size: 28px;
  margin-bottom: 20px;
}
```

**实施时注意**：

1. **弹性的 margin-bottom**：`.column-title`（三栏，24px）使用 24px；`.column-title--lg`（双栏，28px）使用 20px，分别对齐当前内联值。
2. **动态颜色**：`layout-two-column-text.html` 的 `<h3>` 使用 Jinja2 模板变量控制颜色（`color: var(--accent-{{ slide.data.left.color | default('red') }})`），此属性不能提取到静态 CSS 类。实施后该模板应保留颜色为内联样式，其他属性由 CSS 类接管：
   ```html
   <h3 class="column-title column-title--lg" style="color: var(--accent-{{ slide.data.left.color | default('red') }});">
   ```
3. **`compare-three-column-flow.html`** 的颜色为静态 `var(--text-secondary)`，可直接由 `.column-title` 的 `color` 属性覆盖，无需保留内联样式。

#### 3.2 模板替换（5 处）

| 文件 | 行 | 现状 | 目标 |
|------|----|------|------|
| `templates/layout-two-column-text.html` | 8 | `<h3 style="font-size: 28px; margin-bottom: 20px; color: var(--accent-{{ slide.data.left.color \| default('red') }});">` | `<h3 class="column-title column-title--lg" style="color: var(--accent-{{ slide.data.left.color \| default('red') }});">` |
| `templates/layout-two-column-text.html` | 12 | `<h3 style="font-size: 28px; margin-bottom: 20px; color: var(--accent-{{ slide.data.right.color \| default('green') }});">` | `<h3 class="column-title column-title--lg" style="color: var(--accent-{{ slide.data.right.color \| default('green') }});">` |
| `templates/compare-three-column-flow.html` | 9 | `<h3 style="font-size: 24px; margin-bottom: 24px; color: var(--text-secondary);">` | `<h3 class="column-title">` |
| `templates/compare-three-column-flow.html` | 19 | `<h3 style="font-size: 24px; margin-bottom: 24px; color: var(--text-secondary);">` | `<h3 class="column-title">` |
| `templates/compare-three-column-flow.html` | 35 | `<h3 style="font-size: 24px; margin-bottom: 24px; color: var(--text-secondary);">` | `<h3 class="column-title">` |

### 4. 风险与回滚

| 风险 | 缓解 |
|------|------|
| 存量 slides.json 用 `eyebrow` 字段，agent 改为 `kicker` 后渲染空 | 模板用 `{{ slide.kicker \| default(slide.eyebrow \| default('')) }}` 过渡 |
| 遗漏某处 eyebrow 引用 | 已用 3 个并行 explore agent 覆盖整个 skill 目录 + agents/ + docs/ + content/；改动前用 grep 二次校验 |
| 内联 `<h3>` 提取后视觉差异 | 实施时逐属性比对，生成的测试 slides.html 在浏览器中视觉验证 |
| 测试失败 | test fixture 同步更新；运行 pytest 确认 |

**回滚策略**：所有改动通过 git 回滚即可，无数据迁移、无破坏性 Python 变更。

## 验证清单

- [ ] `pytest .opencode/skills/article-to-presentation/tests/` 通过
- [ ] `grep -ri "eyebrow" .opencode/skills/article-to-presentation/` 仅剩模板中的 fallback 表达式 `default(slide.eyebrow ...)`
- [ ] `grep -ri "eyebrow" .opencode/agents/` 无匹配
- [ ] `grep -ri "eyebrow" docs/superpowers/specs/2026-06-25-article-to-presentation-html-engine-design.md` 无匹配
- [ ] 生成包含以下布局的测试 slides.html：cover-hero-center、section-chapter、layout-split-text-image、layout-two-column-text、compare-three-column-flow、data-bar-chart、table-comparison-table、terminal-code-terminal、summary-key-takeaways
- [ ] 浏览器视觉验证：眉标位置、栏目标题字号、图像圆角、表格单元格圆角无回归
- [ ] `lsp_diagnostics` 在所有改动文件上无新增 error

## 影响文件总览

> 注：圆角修复与内联 `<h3>` 提取涉及的 4 个模板已包含在 27 个 HTML 模板内，不重复计数。

| 类别 | 文件数 | 说明 |
|------|--------|------|
| HTML 模板（含圆角修复 + 内联 h3 提取） | 27 | eyebrow → kicker（class + 数据键）；其中 2 个含圆角修复，2 个含 h3 提取 |
| CSS（base.html） | 1 | 删除 `.eyebrow` 别名 + 新增 `.column-title` 类 |
| 测试 | 1 | test_template_rendering.py |
| 文档 | 1 | SKILL.md |
| Agent prompt | 2 | context-cover.md、visual-cover.md |
| Design spec | 1 | 2026-06-25-article-to-presentation-html-engine-design.md |
| **合计** | **33** | |

## 后续命令

- spec 审查：`/plan-review docs/superpowers/specs/2026-06-30-article-to-presentation-style-cleanup-design.md`
- 通过后进入实施计划编写（writing-plans）
