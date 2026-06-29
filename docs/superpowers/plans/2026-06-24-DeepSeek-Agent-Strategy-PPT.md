# DeepSeek Agent 战略转向 PPT 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the DeepSeek strategic shift article into a 15-slide dark-tech HTML presentation (slides.html) with ECharts-free, CSS-only visuals.

**Architecture:** Python markdown parser extracts structured data → LLM generates Slide DSL (slides.json) using slide_prompt.md + visual_prompt.md → Jinja2 template engine renders single-file HTML.

**Tech Stack:** Python 3.10+, jinja2 (root .venv), Jinja2 templates, 30 HTML fragment templates, CSS-only animations

**Design doc:** `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/PPT设计.md`

---

## Task 1: Generate PPT文案.md via parser

**Files:**
- Script: `.opencode/skills/article-to-presentation/scripts/generate.py`
- Input: `content/article/20260624-DeepSeek全球急招Agent人才-从大模型到Agent的战略转向.md`
- Output: `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/PPT文案.md`

- [ ] **Step 1: Run generate.py to create PPT文案.md**

Run (⚠️ MUST use `.venv/bin/python` for jinja2 dependency):
```bash
.venv/bin/python .opencode/skills/article-to-presentation/scripts/generate.py \
  --input "content/article/20260624-DeepSeek全球急招Agent人才-从大模型到Agent的战略转向.md" \
  --output "content/ppt/2026-06-24-DeepSeek-Agent-Strategy/"
```

Expected: `Written: content/ppt/2026-06-24-DeepSeek-Agent-Strategy/PPT文案.md`

- [ ] **Step 2: Verify PPT文案.md was created with title, sections, metrics, quotes, sources**

Run:
```bash
head -30 "content/ppt/2026-06-24-DeepSeek-Agent-Strategy/PPT文案.md"
```

Expected: Contains title `# DeepSeek 招不到人——AI人才战争进入下半场`, sections, key data, quotes, and data sources.

---

## Task 2: Generate slides.json via LLM (slide_prompt.md)

**Context:** The `slides.json` defines the Slide DSL structure. It must follow the schema in `prompts/slide_prompt.md`.

**Design reference:** `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/PPT设计.md` — 15 slides with type/visual/title/data specified. Must match exactly.

**Prompt reference:** `.opencode/skills/article-to-presentation/prompts/slide_prompt.md`
**PPT文案 input:** `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/PPT文案.md`

**Product:** `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.json`

- [ ] **Step 1: Read PPT文案.md to extract structured content**

Read the generated PPT文案 to get title, sections, key data, quotes, and data sources.

- [ ] **Step 2: Construct slides.json following slide_prompt.md schema**

Use the slide_prompt.md rules to convert each of the 15 slides from the design doc into valid JSON. Each slide must have: `type`, `visual`, `title`, `subtitle` (if applicable), `badge` (if chapter), `data` (matching visual schema), `source`.

Design doc slide map:
1. cover / hero-split — "DeepSeek 招不到人" / "AI 人才战争进入下半场" / eyebrow="战略分析"
2. quote / quote-center — "每天都在面试，缺人缺疯了。" / source="崔添翼 · 前 Jane Street..."
3. section / chapter — badge=1 / "郭达雅出走，Harness 才来"
4. process / timeline — "从出走 to 组建"
5. data / metric-cards — "5 名核心研究员先后离职"
6. compare / before-after-cards — "一个人的判断力"
7. section / chapter — badge=2 / "模型是发动机，Harness 才是整车"
8. compare / before-after-cards — "Model + Harness = Agent"
9. data / metric-cards — "Harness 覆盖什么？"
10. section / chapter — badge=3 / "48 条新闻，一个人都招不到"
11. data / metric-cards — "外面的世界"
12. compare / three-column-flow — "国内三条赛道已开跑"
13. section / chapter — badge=4 / "抢的是知道要做什么的人"
14. data / metric-cards — "崔添翼为什么招不到人？"
15. summary / summary-list — "不是谁会训练，是谁能驯服"

Color rules: green=positive, red=negative, orange=neutral/emphasis, blue=info, purple=concept, cyan=system/ability/tech.

Write the complete slides.json to `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.json`.

---

## Task 3: Enrich slides.json with visual data (visual_prompt.md)

**Context:** Use `prompts/visual_prompt.md` to fill every slide's `data` field with complete content — no empty objects. Each visual type has a specific data schema that must be followed exactly.

**Input:** `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.json` (from Task 2)

**Output:** Same file, with enriched data fields.

**Key data points from the article to embed:**

Slide 4 (timeline — ⚠️ template expects `data.events` with `{date, title, description, color}`, NOT flat strings):
```json
"data": {
  "events": [
    {"date": "2025.10", "title": "郭达雅决定离职", "description": "GRPO 算法发明人，DeepSeek-Coder/V3/R1 核心贡献者", "color": "red"},
    {"date": "2026.03", "title": "郭达雅加入字节，崔添翼加入 DeepSeek", "description": "郭达雅加入字节 Seed 任 Agent 方向负责人；前 Jane Street 量化工程师崔添翼（ACM ICPC 6 次金牌）加入", "color": "orange"},
    {"date": "2026.05", "title": "Harness 团队组建", "description": "从零构建 CodeHarness，内部对标 Claude Code", "color": "green"}
  ]
}
```

Slide 5 (metric-cards — 5 researchers):
- ① 王炳宣 · 基座模型核心 · 去腾讯混元 → red
- ② 罗福莉 · V3 核心 · 传千万年薪去小米 → red
- ③ 魏浩然 · OCR 系列核心 · 去向未公开 → red
- ④ 阮翀 · 多模态核心 · 去元戎启行 → red
- ⑤ 郭达雅 · 代码/推理核心 · 去字节 Seed → orange
- callout: "150 人团队，覆盖 4 条核心技术线"

Slide 6 (before-after-cards):
- before: label="郭达雅想做 Agent" / value="2023年" / desc="方向判断走在公司前面"
- after: label="DeepSeek 紧急转向" / code="2026.05" / desc="郭走后 7 个月，Harness 才组建"
- banner: "顺序是反过来的——人走了，才追。"

Slide 8 (before-after-cards — ⚠️ template expects `after.code` not `after.value`):
- before: label="大模型时代" / value=2023 / desc="训练更大的模型，API 就是产品"
- after: label="Agent 时代" / **code="拼 Harness"** / desc="模型之外的所有基础设施"
- banner: "发动机 vs 整车：不是同一个工程体系"

Slide 9 (metric-cards — 6 components):
- 1 上下文管理 → blue / 2 长期记忆 → purple / 3 Subagent 协同 → cyan / 4 自进化 Agent → green / 5 工具调用与规划 → orange / 6 MCP 协议集成 → blue

Slide 11 (metric-cards — 6 metrics):
- 48 条/周 / 8× 工程师产出 / 470 亿年化营收 / 25 亿 Claude Code / 14.32 亿月活 / Codex 开放接入

Slide 12 (three-column-flow — ⚠️ template supports both `{title, items}` for left/right/center AND `{label, value, description}` for center. Use `{title, items}` uniformly):
- left.title: "消费级 Agent" / left.items: ["微信小微 6.20 灰度上线", "14.32 亿月活用户", "最广泛消费触点"]
- center.title: "金融 Agent" / center.items: ["蚂蚁国际开源 AMP", "全球首个移动端", "Agent 支付框架"]
- right.title: "开发工具" / right.items: ["小米 MiMo Code 开源", "MIT 协议", "AI 编程工具赛道"]
- banner: "三条赛道，没有一条在等 DeepSeek"

Slide 14 (metric-cards — 3 capabilities):
- 🧠 purple 研究品味 / 🔧 cyan 工程能力 / 🎯 orange 产品思维
- callout: "这三种能力在同一个人身上同时出现——极度稀缺"

Slide 15 (summary-list — 6 items):
1. 大模型时代抢研究员 → Agent 时代抢能『驯马』的人
2. Agent = Model + Harness，Harness 才是真正的壁垒
3. 郭达雅的判断走在了公司前面——他离开的理由变成了公司的方向
4. 一周 48 条新闻，Claude Code 已经自己写了 7 个月代码
5. 全员 Agent 写代码——人际协作反而变少了，效率的副作用
6. 这不是有钱就能快起来的事

**Must fix data error:** Slide 6 banner text uses "郭走后 7 个月" (not 8).

- [ ] **Step 1: Read the enriched slides.json and verify all data fields are filled**

Read the slides.json file to check all data fields are complete for each slide.

- [ ] **Step 2: Validate JSON is legal and follows visual schema**

Check:
- All `data` fields non-empty
- Colors match semantic rules
- No emoji in badge fields (use text labels instead)
- Numbers are integers/floats, not strings with % signs
- `source` field present on every slide

---

## Task 4: Render slides.html

**Files:**
- Script: `.opencode/skills/article-to-presentation/renderer/html_renderer.py`
- Input: `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.json`
- Output: `content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.html`

- [ ] **Step 1: Confirm jinja2 is installed in root .venv**

Run:
```bash
.venv/bin/python -c "import jinja2; print('jinja2 OK')"
```

Expected: `jinja2 OK`

- [ ] **Step 2: Render slides.html**

Run:
```bash
.venv/bin/python .opencode/skills/article-to-presentation/renderer/html_renderer.py \
  --slides "content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.json" \
  --output "content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.html"
```

Expected: `Rendered: content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.html`

- [ ] **Step 3: Verify slides.html was created and has correct structure**

Run:
```bash
wc -l "content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.html"
head -5 "content/ppt/2026-06-24-DeepSeek-Agent-Strategy/slides.html"
```

Expected: HTML file with doctype, 15 slide sections, base.html template structure.

---

## Task 5: Browser verification

- [ ] **Step 1: Open slides.html in browser at 1920×1080**

Use Playwright to navigate to the file and take a full-page screenshot.

- [ ] **Step 2: Verify all 15 slides render correctly with content**

Check each slide for BOTH structure AND content:

1. **Cover**: title "DeepSeek 招不到人" visible, subtitle "AI 人才战争进入下半场", right panel shows "50" (not "信息图占位")
2. **Quote**: "每天都在面试" visible, source "崔添翼" visible
3. **S3 chapter**: badge "1" visible, title "郭达雅出走" visible
4. **S4 timeline**: 3 events visible — each with date (2025.10, 2026.03, 2026.05), title, and description text
5. **S5 metric-cards**: 5 cards visible — 王炳宣, 罗福莉, 魏浩然, 阮翀, 郭达雅 — callout text visible
6. **S6 before-after-cards**: left shows "郭达雅想做 Agent", right shows "DeepSeek 紧急转向", banner text visible
7. **S7 chapter**: badge "2" visible, title "模型是发动机"
8. **S8 before-after-cards**: left shows "大模型时代", right shows "拼 Harness" (the `code` field), banner visible
9. **S9 metric-cards**: 6 cards visible — 上下文管理, 长期记忆, Subagent 协同, 自进化 Agent, 工具调用, MCP协议
10. **S10 chapter**: badge "3" visible, title "48 条新闻"
11. **S11 metric-cards**: 6 cards visible — 48条/周, 8×产出, 470亿, 25亿, 14.32亿, Codex
12. **S12 three-column-flow**: 3 columns with content — left: 消费级 Agent + items, center: 金融 Agent + items, right: 开发工具 + items, banner visible
13. **S13 chapter**: badge "4" visible, title "抢的是知道"
14. **S14 metric-cards**: 3 cards visible — 研究品味, 工程能力, 产品思维 — callout visible
15. **S15 summary**: 6 list items visible

- [ ] **Step 3: Visual quality check**

- [ ] Content vertically centered (flex column + justify-content: center)
- [ ] Card gaps: double-column gap 24px, three-column gap 20px
- [ ] Every slide except cover/section/quote has a `#` title
- [ ] Color semantics correct: red=negative, green=positive, orange=neutral, purple=concept, cyan=ability
- [ ] No ECharts dependency (no chart slides used)
- [ ] Page numbers in footer increment correctly
- [ ] Source attribution present on each slide
- [ ] Keyboard navigation (← →) works
- [ ] Slide transitions are fade-up only

- [ ] **Step 4: Verify file:// protocol works**

Check that opening the HTML file directly via `file://` protocol displays correctly without a server.

---

## Task 6: Self-review verification

- [ ] **Step 1: Run lsp_diagnostics on all output files**
- [ ] **Step 2: Verify all 15 slides from design doc are present in slides.json and slides.html**
- [ ] **Step 3: Confirm data accuracy — no remaining "8个月" errors**
- [ ] **Step 4: Content rendering audit** — verify these critical content areas:
  - Cover right panel shows "50 个开放岗位" NOT "信息图占位"
  - Slide 4 timeline has 3 events with visible date + title text per event
  - Slide 8 after panel shows "拼 Harness" text (the `code` field)
  - Slide 12 center column shows "金融 Agent" + its 3 items
  - Slide 6 banner reads "顺序是反过来的——人走了，才追。"
  - All chapter slides (3,7,10,13) show badge number with orange color
