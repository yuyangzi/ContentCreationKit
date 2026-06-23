# article-to-presentation Skill 优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化 article-to-presentation skill 的 3 个文件：默认霓虹紫配色、CJK 排版指南、Click 动画三档精确配置、布局映射扩展。

**Architecture:** 纯文档修改（Markdown），无代码逻辑。每个 task 修改一个文件，task 间通过 grep 验证交叉引用一致性。

**Tech Stack:** Slidev + neocarbon v1.0.8 主题、Markdown 文档

**Spec:** `docs/superpowers/specs/2026-06-23-article-to-presentation-optimization-design.md`

---

## 文件清单

| 文件 | 操作 | 改动量 |
|------|------|--------|
| `.opencode/skills/article-to-presentation/references/common-pitfalls.md` | Modify | 追加 ~50 行（4 陷阱 + 2 审查段 + 4 检查项） |
| `.opencode/skills/article-to-presentation/references/technical-details.md` | Modify | 重组 ~150 行 + 新增 ~200 行（预设库/CJK/动画/7 布局 API） |
| `.opencode/skills/article-to-presentation/SKILL.md` | Modify | 修改 ~30 行 + 新增 ~50 行（固定值/动画/布局映射/版本号/模板） |

---

## Task 0: 验证前置条件

**Files:**
- Read: `.opencode/skills/article-to-presentation/references/technical-details.md`（确认行号）
- Read: `content/ppt/2026-06-22-AI-execution-judgment/package.json`（确认版本）

- [ ] **Step 1: 确认 neocarbon v1.0.8 存在**

Run:
```bash
npm view @enyineer/slidev-theme-neocarbon@1.0.8 version
```
Expected: `1.0.8`

若失败 → 运行 `npm view @enyineer/slidev-theme-neocarbon versions --json` 找到最新版本，后续任务中所有 `1.0.8` 替换为实际版本。

- [ ] **Step 2: 确认新增组件在 v1.0.8 中存在（免安装）**

使用 `npm pack --dry-run` 直接查询包 tarball 内容，无需安装 node_modules：

Run:
```bash
npm pack @enyineer/slidev-theme-neocarbon@1.0.8 --dry-run --registry https://registry.npmmirror.com 2>&1 \
  | grep -iE "components/.*(terminal|steps|flip|roi|heatmap)"
```

Expected: 应看到 5 行，每行列出一个 `.vue` 文件（如 `package/components/NcTerminal.vue`）。

**实际调查结果**（Metis 审查已完成）：5 个组件**全部存在**于 v1.0.8 tarball 中 ✅。
布局 `spotlight` 和 `browser` 也存在 ✅。

若命令失败（网络问题），回退为：
```bash
cd content/ppt/2026-06-22-AI-execution-judgment \
  && npm install --registry https://registry.npmmirror.com \
  && ls node_modules/@enyineer/slidev-theme-neocarbon/components/ | grep -iE "terminal|steps|flip|roi|heatmap"
```

- [ ] **Step 3: 验证 `clickAnimation` frontmatter 字段**

Run:
```bash
# 先用 npm pack 检查源码中是否定义了 clickAnimation 相关逻辑
npm pack @enyineer/slidev-theme-neocarbon@1.0.8 --dry-run --registry https://registry.npmmirror.com 2>&1 \
  | grep -iE "clickAnimation|animation"
```

**实际调查结果**（Metis 审查已完成）：`clickAnimation` **不是 neocarbon 或 Slidev 的标准 frontmatter 字段** ❌。

**结论 → 直接采用 CSS-only 方案**：
- **不写** `clickAnimation` frontmatter
- 动画完全靠 `<style>` CSS 控制（三段降级 / 全禁 CSS）
- `transition: fade` 保留（Slidev 原生支持）

**影响的具体位置及修改方式：**
1. **Task 2 Step 3**（frontmatter 模板）：删除 `clickAnimation: fade` 行，改为注释 `# neocarbon 不支持 clickAnimation；v-click 动画由 <style> CSS 控制`
2. **Task 2 Step 6**（Click 动画配置章节）：三档策略表的 `frontmatter` 列删除 `clickAnimation` 引用，仅保留 `transition: fade`
3. **Task 3 Step 1**（固定值表）：删除 `clickAnimation: fade` 行
4. **Task 3 Step 2**（动画策略表）：同上处理 frontmatter 列
5. **Task 3 Step 6**（slides.md 模板）：删除 `clickAnimation: fade`

> ⚠️ Task 2/3 执行时，上述位置必须按此结论调整。执行者以本 Step 的结论为准。

- [ ] **Step 4: 扫描所有需更新的旧值**

Run:
```bash
grep -rn "1\.0\.5" .opencode/skills/article-to-presentation/
grep -rn "#ff6b35" .opencode/skills/article-to-presentation/
grep -rn "橙色" .opencode/skills/article-to-presentation/references/technical-details.md
```

记录每个匹配的行号，用于 Task 2 Step 3 和 Task 3 Step 2。

- [ ] **Step 5: 汇总 Task 0 结论**

将 Step 1-4 的结果记录在内存中，传递给后续 Task。Task 0 不产生文件改动，**无需 commit**。

**已知结论**（Metis 审查已提前验证）：
- neocarbon v1.0.8 ✅ 存在（npm 唯一版本）
- 5 个新组件 ✅ 全部存在
- `spotlight` / `browser` 布局 ✅ 存在
- `clickAnimation` frontmatter ❌ 不存在 → Task 2/3 采用 CSS-only 方案

---

## Task 1: 修改 common-pitfalls.md

**Files:**
- Modify: `.opencode/skills/article-to-presentation/references/common-pitfalls.md`（末尾追加）

- [ ] **Step 1: 在陷阱一览表末尾追加 4 行**

在文件第 21 行（最后一条陷阱 `| 16 |` 行）之后追加：

```markdown
| 17 | **CJK 行高缺失** | 中文汉字上下行挤在一起，可读性下降 | `<style>` 中设置 `.slidev-layout { line-height: 1.75; font-size: 24px; }` |
| 18 | **配色预设覆盖遗漏** | 选了预设但漏改部分变量，该语义色仍是旧默认值 | 选择预设后完整粘贴整套 5 变量（accent/success/danger/warning/info），不要只改单个 |
| 19 | **click 动画与 slide 过渡冲突** | `transition: slide-left` + `clickAnimation: fade.up` → 翻页瞬间元素先淡入再位移，视觉撕裂 | 统一动画方向：要么全 fade，要么全 slide，不混搭 |
| 20 | **font provider 阻塞构建** | Google Fonts CDN 请求超时 → `slidev dev` 或 `slidev build` 卡死数分钟 | frontmatter 设 `fonts.provider: none` |
```

- [ ] **Step 2: 在「审查常见发现」部分追加 2 段**

在 `### 布局语法` 段之前（约第 34 行）之前插入：

```markdown
### 配色预设

- **阶段二选定预设后，检查 `<style>` 中 5 个 CSS 变量是否全部覆盖**
- 遗漏任一变量 → 该语义色仍是上次使用的值，视觉上与预设不协调
- 自定义色值仍遵守语义：success 正面、danger 负面、accent 中性
- **检查**：搜索 `--nc-accent`、`--nc-success`、`--nc-danger`、`--nc-warning`、`--nc-info` 在 `<style>` 中是否全部出现

### Click 动画

- **frontmatter `clickAnimation` 值与 `<style>` 降级 CSS 必须匹配**
- 淡入档 → 含 `.nc-stagger > *`/`.nc-shimmer`/`.nc-particles` 禁用 CSS
- 全禁档 → 含全禁 CSS 块 + `transition: none`
- 复杂幻灯片（3+ v-click）必须显式设 `clicks: N`
- **检查**：搜索 frontmatter 中的 `clickAnimation` 或 `transition: none`，确认与 `<style>` 中的动画 CSS 一致
```

- [ ] **Step 3: 在「实现完成前检查清单」末尾追加 4 条**

在最后一个 `- [ ]` 项（第 67 行 `## 章节标题在正确的 slide 位置`）之后追加：

```markdown
- [ ] 配色预设 5 变量全部覆盖（或确认使用默认霓虹紫）
- [ ] CJK 行高 ≥ 1.75（`.slidev-layout`）
- [ ] Mermaid 中文补丁生效（`svg text` font-family 含 CJK 字体）
- [ ] `fonts.provider: none` 已设置
```

- [ ] **Step 4: 验证 common-pitfalls.md 改动**

Run:
```bash
grep -c "^|" .opencode/skills/article-to-presentation/references/common-pitfalls.md
```
Expected: `>= 22`（原 18 行 [1 header + 1 separator + 16 数据] + 新增 4 行陷阱）

Run:
```bash
grep -c "^\- \[ \]" .opencode/skills/article-to-presentation/references/common-pitfalls.md
```
Expected: `>= 17`（原 13 + 新增 4）

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/article-to-presentation/references/common-pitfalls.md
git commit -m "docs(skill): common-pitfalls 新增 4 条陷阱（CJK/配色遗漏/动画冲突/网络阻塞）"
```

---

## Task 2: 修改 technical-details.md

**Files:**
- Modify: `.opencode/skills/article-to-presentation/references/technical-details.md`

本任务按文件从上到下的顺序修改，避免行号漂移。

### 2a: 重构配色方案（第 3-39 行）

- [ ] **Step 1: 替换「配色方案」为「配色预设库」**

将第 3 行 `## 配色方案` 到第 39 行（`**严格禁止**` 行的末尾）替换为：

```markdown
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
```

> 注意：Task 0 Step 3 若确认 `clickAnimation` 不存在，上文中不需要改动（此处仅涉及配色，不涉及动画）。

### 2b: 更新字体章节（第 43-54 行）

- [ ] **Step 2: 替换「字体」章节**

将第 43 行 `## 字体` 到第 55 行（`---` 分隔符之前）替换为：

```markdown
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
```

### 2c: 更新 frontmatter 模板（第 70-87 行区域，行号因 2b 偏移后调整）

- [ ] **Step 3: 替换 Slidev 配置模板的 frontmatter 示例**

找到 `### frontmatter（\`slides.md\` 顶部）` 小节，将其中的 yaml 代码块替换为：

```yaml
---
theme: '@enyineer/slidev-theme-neocarbon'
title: '演示文稿标题'
info: |
  ## 副标题信息
  数据来源概述
highlighter: shiki
clickAnimation: fade
transition: fade
fonts:
  sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'
  serif: 'Noto Serif SC, serif'
  mono: 'Fira Code, monospace'
  provider: none
---
```

并在「关键字段」说明中追加：

```markdown
- `clickAnimation: fade`：v-click 默认动画预设（可选 `fade.up`/`none`，详见 CJK 动画模板章节）
- `fonts.provider: none`：禁止 Google Fonts CDN 自动请求
- `transition: fade`：幻灯片过渡动画（可选 `none` 禁用）
```

> Task 0 Step 3 若确认 `clickAnimation` 不存在 → 将 `clickAnimation: fade` 改为注释行 `# clickAnimation 字段不存在于 neocarbon，动画仅靠 <style> CSS 控制`。

### 2d: 更新 package.json 模板中的版本号

- [ ] **Step 4: 将 `1.0.5` 替换为 `1.0.8`**

将 `package.json` 代码块中的：

```json
"@enyineer/slidev-theme-neocarbon": "1.0.5"
```

替换为：

```json
"@enyineer/slidev-theme-neocarbon": "1.0.8"
```

> 若 Task 0 Step 1 确认 v1.0.8 不存在，则使用实际最新版本。

### 2e: 追加新布局 API 文档

- [ ] **Step 5: 在现有 8 种布局 API 之后追加新布局/组件文档**

在 `### \`default\` — 正文（自由布局）` 小节末尾（约第 244 行区域）之后、`---` 分隔符之前，追加：

```markdown
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
```

然后根据 Task 0 Step 2 的组件存在性结果，追加组件文档。**存在的组件直接写文档；不存在的加 ⚠️ 标注。**

以下以组件全部存在为例（不存在时在该组件文档第一行添加 `> ⚠️ 需验证 — 基于 README 描述，未经源码确认。请安装后检查 \`node_modules/@enyineer/slidev-theme-neocarbon/components/\` 确认。`）：

```markdown
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
```

### `<NcLineChart />` — 多线趋势扩展示例（双 Y 轴风格）

> 补充现有 `<NcLineChart />` API（技术细节 L290-306）的进阶用法。

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

### 2f: 替换动画控制章节

- [ ] **Step 6: 替换「动画控制」为「Click 动画配置」**

找到 `## 动画控制` 章节（约第 360 行区域），替换到下一个 `---` 之前：

```markdown
## Click 动画配置

### 三档策略（阶段二确认）

| 档位 | frontmatter | `<style>` CSS | 适用 |
|------|------------|-------------|------|
| 保留全部 | `clickAnimation: fade.up`（若有） | 无额外 CSS | 现场演示 |
| **淡入（默认）** | `clickAnimation: fade`（若有）/ `transition: fade` | 三段降级 CSS（见下） | B站录屏 |
| 全部禁用 | `transition: none` | 全禁 CSS（见下）+ `transition: none` | 纯旁白 |

> 若 neocarbon 不支持 `clickAnimation` frontmatter，忽略该列。动画仅靠 `<style>` CSS 控制。

### 淡入模式降级 CSS（默认生效）

```css
.nc-stagger > * { animation: none !important; opacity: 1 !important; }
.nc-shimmer { animation: none !important; }
.nc-particles { display: none !important; }
```

### 全禁 CSS

```css
.nc-stagger > *,
.nc-shimmer,
.nc-particles,
[class*="nc-animate"] { animation: none !important; opacity: 1 !important; }
```

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
```

### 2g: 扩展布局映射表

- [ ] **Step 7: 补全布局映射表**

在现有布局映射表（第 385 行区域「## 布局映射表（完整版）」）的表格末尾追加新行。

现有 13 行（封面/副标题/章节/引用/柱状图/指标卡/对比/金句/洞察+案例/趋势数据/流程分叉图/数据来源/结尾）。

以下 6 行是现有 13 行表中没有的，追加：

```markdown
| 终端/CLI 展示 | `default` + `<NcTerminal />` | 部署命令输出 |
| 多步流程 | `default` + `<NcSteps />` | 管线步骤展示 |
| 金融指标/KPI | `metrics` + `<NcRoiCard />` | ROI 卡片 |
| 浏览器截图 | `browser` 布局 | Web 产品界面 |
| 翻转卡片 | `default` + `<NcFlipCard />` | 术语定义（正/反面） |
| 聚焦核心洞察 | `spotlight` 布局 | "判断力 = 护城河" |
```

> 最终 technical-details.md 映射表 = 13 + 6 = **19 行**。SKILL.md = 8 + 7 = **15 行**（更精炼的子集）。两张表的重叠行内容必须完全一致。

### 2h: Cross-reference 自检

- [ ] **Step 8: 验证 technical-details.md 改动**

Run:
```bash
grep -c "#a855f7" .opencode/skills/article-to-presentation/references/technical-details.md
```
Expected: `>= 2`（预设 A 默认 + 其他位置可能出现）

Run:
```bash
grep "1\.0\.5" .opencode/skills/article-to-presentation/references/technical-details.md
```
Expected: **无输出**（全部替换为 1.0.8）

Run:
```bash
grep -c "^### \`" .opencode/skills/article-to-presentation/references/technical-details.md
```
Expected: `>= 13`（原 8 布局 API + 新增 browser/spotlight/NcTerminal/NcSteps/NcFlipCard + NcHeatmap/NcRoiCard）

- [ ] **Step 9: Commit**

```bash
git add .opencode/skills/article-to-presentation/references/technical-details.md
git commit -m "feat(skill): technical-details 新增霓虹紫预设/CJK排版/动画模板/7种布局API"
```

---

## Task 3: 修改 SKILL.md

**Files:**
- Modify: `.opencode/skills/article-to-presentation/SKILL.md`
- Read (reference): `.opencode/skills/article-to-presentation/references/technical-details.md`（确保布局映射表一致）

本任务按文件从上到下的顺序修改。

### 3a: 阶段二固定值表新增 2 行

- [ ] **Step 1: 在固定值表追加 2 行**

在第 56 行（`| 翻页 | 键盘纯手动 |`）之后插入：

```markdown
| 默认 click 动画 | `clickAnimation: fade`（若 neocarbon 支持）|
| CJK 字体 | `fonts.sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'` / `fonts.provider: none` |
```

### 3b: 替换动画策略表

- [ ] **Step 2: 替换阶段二「动画策略」小节**

将第 66-74 行（`### 动画策略（visual companion 确认）` 到 `| 全部禁用 | 纯静态，适合画外音旁白聚焦 |`）替换为：

```markdown
### 动画策略（visual companion 确认）

neocarbon 默认电影级动画（staggered entrances、shimmer、pulse、particles）。B站录屏需确认动画档位：

| 档位 | frontmatter | `<style>` CSS | 说明 |
|------|------------|-------------|------|
| 保留全部 | `clickAnimation: fade.up` | 无额外 CSS | staggered/shimmer/particles 全保留，视觉最炫但录屏可能有动画噪音 |
| **淡入（默认）** | `clickAnimation: fade` / `transition: fade` | 三段降级 CSS | 仅 fade，禁用 staggered/shimmer/particles |
| 全部禁用 | `transition: none` | 全禁 CSS | 纯静态，适合画外音旁白聚焦 |

三段降级 CSS（写入 slides.md `<style>` 块）：
```css
.nc-stagger > * { animation: none !important; opacity: 1 !important; }
.nc-shimmer { animation: none !important; }
.nc-particles { display: none !important; }
```

> 若 neocarbon 不支持 `clickAnimation` frontmatter（Task 0 验证），忽略该列。动画仅靠 `<style>` CSS 控制。完整 CSS 模板 → [references/technical-details.md](references/technical-details.md)「Click 动画配置」章节。
```

### 3c: 阶段三新增配色预设步骤 + 更新颜色默认值

- [ ] **Step 3: 在阶段三输出内容中插入配色预设步骤**

将第 89 行 `1. **主题配置**：...` 替换为：

```markdown
0. **配色预设选择**：从预设库选基础配色（默认霓虹紫），用户可覆盖个别色值。完整预设 → [references/technical-details.md](references/technical-details.md)「配色预设库」
1. **主题配置**：`--nc-accent`、`--nc-success`、`--nc-danger` 颜色值（默认紫/青/玫红）
```

### 3d: 更新布局映射表（8 → 15 行）

- [ ] **Step 4: 替换阶段三「默认布局映射」表**

将第 94-107 行（`### 默认布局映射` 到 `完整映射 + 组件 API + 设计令牌 → 详见 [references/technical-details.md]`）替换为：

```markdown
### 默认布局映射

| PPT 内容类型 | neocarbon 方案 | 示例 |
|-------------|---------|------|
| 封面主标题 | `cover` 布局 | "AI压缩了执行力，放大了判断力" |
| 章节分隔 | `section` 布局 | "第一章 · 执行层的差距" |
| 开场钩子（引用） | `quote` 布局 | "同一个AI，对不同的人'努力程度'不一样" |
| 柱状图对比 | `default` + `<NcBarChart />` | 89% vs 88% |
| 趋势数据（多线） | `default` + `<NcLineChart />` | 7 个月会话变化 |
| 并排指标卡 | `metrics` 布局 | 放弃率、动作数、词数 |
| 左右概念对比 | `comparison` 布局（`::left::`/`::right::`） | 可编码 vs 默会 |
| 金句（多行大字） | `statement` 布局 | "你可以让AI写一千个方案..." |
| 数据来源列表 | `default` 布局 | 6 个来源 + 链接 |
| 流程分叉图 | `diagram` + Mermaid | 碰壁→放弃/翻盘 |
| 终端/CLI 展示 | `default` + `<NcTerminal />` | 部署命令输出 |
| 多步流程 | `default` + `<NcSteps />` | 管线步骤展示 |
| 金融指标/KPI | `metrics` + `<NcRoiCard />` | ROI 卡片 |
| 浏览器截图 | `browser` 布局 | Web 产品界面 |
| 翻转卡片 | `default` + `<NcFlipCard />` | 术语定义（正/反面） |
| 聚焦核心洞察 | `spotlight` 布局 | "判断力 = 护城河" |

完整映射 + 组件 API + 设计令牌 → 详见 [references/technical-details.md](references/technical-details.md)
```

### 3e: 版本号统一

- [ ] **Step 5: 更新环境要求中的版本号**

将第 140 行：

```markdown
- `@enyineer/slidev-theme-neocarbon` 精确版本 `1.0.5`
```

替换为：

```markdown
- `@enyineer/slidev-theme-neocarbon` 精确版本 `1.0.8`
```

### 3f: 更新阶段六 slides.md 模板

- [ ] **Step 6: 更新阶段六「写入 slides.md」的 CSS 模板**

将第 170-177 行（`AI 生成全部幻灯片 Markdown。关键点：` 到 CSS 代码块结束）替换为：

```markdown
AI 生成全部幻灯片 Markdown。关键点：
- 颜色令牌在 `<style>` 块中覆盖（默认霓虹紫预设，详见 references/technical-details.md）
- CJK 行高 + Mermaid 中文补丁 + TOC 隐藏 + 动画降级 CSS 均在同一个 `<style>` 块中
- **必须**包含以下完整 `<style>` 块：

```css
:root {
  --nc-accent:  #a855f7;   /* 霓虹紫默认 */
  --nc-success: #22d3ee;
  --nc-danger:  #f43f5e;
  --nc-warning: #fbbf24;
  --nc-info:    #818cf8;
}
/* CJK 行高 */
.slidev-layout { line-height: 1.75; font-size: 24px; }
/* Mermaid 中文补丁 */
svg text { font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important; }
/* 隐藏 Slidev 导航面板 — 录屏时遮挡内容 */
.slidev-sidebar, .slidev-nav, .slidev-slide-nav,
.slidev-navigation, .slidev-toc, .slidev-overview-panel,
aside, nav.slidev-nav,
[class*="sidebar"], [class*="toc"], [class*="navigation"],
#slidev-nav, .slidev-layout-nav { display: none !important; }
/* 动画降级（淡入档） */
.nc-stagger > * { animation: none !important; opacity: 1 !important; }
.nc-shimmer { animation: none !important; }
.nc-particles { display: none !important; }
```
```

### 3g: 更新手动验证中的颜色描述

- [ ] **Step 7: 更新颜色编码检查清单的默认色值描述**

将第 195 行：

```markdown
  - [ ] 中性数据（如 93% 使用率）：`nc-text-accent`（橙色），**不是** 红色
```

替换为：

```markdown
  - [ ] 中性数据（如 93% 使用率）：`nc-text-accent`（紫色），**不是** 红色
```

### 3h: Cross-reference 自检

- [ ] **Step 8: 验证 SKILL.md 改动**

Run:
```bash
grep "1\.0\.5" .opencode/skills/article-to-presentation/SKILL.md
```
Expected: **无输出**

Run:
```bash
grep -c "^|" .opencode/skills/article-to-presentation/SKILL.md | head -1
```
Expected: 布局映射表区域 `>= 17`（header + 15 行数据 + 分隔行）

Run:
```bash
grep "#a855f7" .opencode/skills/article-to-presentation/SKILL.md
```
Expected: 至少 1 行匹配（`<style>` 模板中）

Run:
```bash
grep "provider: none" .opencode/skills/article-to-presentation/SKILL.md
```
Expected: 至少 1 行匹配（固定值表中）

- [ ] **Step 9: Commit**

```bash
git add .opencode/skills/article-to-presentation/SKILL.md
git commit -m "feat(skill): SKILL.md 霓虹紫默认/CJK字体/动画三档/布局映射15种/v1.0.8"
```

---

## Task 4: 跨文件一致性终验

**Files:**
- Read: 全部 3 个修改过的文件

- [ ] **Step 1: 版本号一致性**

Run:
```bash
grep -rn "1\.0\.[0-9]" .opencode/skills/article-to-presentation/ | grep -v node_modules
```
Expected: 所有 `--nc-accent` 主题包版本引用为 `1.0.8`（或 Task 0 确认的实际版本），无残留 `1.0.5`。

- [ ] **Step 2: 霓虹紫变量一致性**

Run:
```bash
grep -rn "#a855f7" .opencode/skills/article-to-presentation/
grep -rn "#22d3ee" .opencode/skills/article-to-presentation/
grep -rn "#f43f5e" .opencode/skills/article-to-presentation/
```
Expected: 三值均在 technical-details.md（预设定义）和 SKILL.md（`<style>` 模板）中出现。

- [ ] **Step 3: CJK 字体栈一致性**

Run:
```bash
grep -n "PingFang SC" .opencode/skills/article-to-presentation/SKILL.md .opencode/skills/article-to-presentation/references/technical-details.md .opencode/skills/article-to-presentation/references/common-pitfalls.md
```
Expected: 至少 4 处匹配（SKILL.md 固定值表、SKILL.md 模板、technical-details 配置、common-pitfalls 提及）。

- [ ] **Step 4: 布局映射表行数一致性**

**策略**：映射表行的特征是 `| <PPT 内容类型> | \`layout\` 或 \`default\` +`。用锚定模式只匹配映射表数据行：

Run:
```bash
# SKILL.md 映射表数据行（排除 header + separator）
awk '/^### 默认布局映射/,/^完整映射/' .opencode/skills/article-to-presentation/SKILL.md \
  | grep -c "^| \*\*.*\*\*\|^[^|]\+| [a-z]\|^[^|]\+| \`"
# 预期：16（8 原有 + 8 新增）
echo "---"
# technical-details.md 映射表数据行
awk '/^## 布局映射表/,/^$/' .opencode/skills/article-to-presentation/references/technical-details.md \
  | grep -c "^|"
# 预期：>= 20（1 header + 1 separator + 19 数据行）
```

若 awk 不可用，改用手工核对：
```bash
# 备用：提取 PPT 内容类型列去重后计数
grep -oE "^[^|]+\|[^|]+\|" .opencode/skills/article-to-presentation/SKILL.md \
  | grep -vE "^\| (PPT|维度|档位|选项|数据类型|类|依赖|Prop)" \
  | grep -vE "^\|[-]+\|" | wc -l
```

Expected: SKILL.md 映射表区域 16 行（8 + 8 新增），technical-details.md 映射表区域 19 数据行（13 + 6 新增）。SKILL.md 是 technical-details 的精炼子集——重叠行的内容（PPT 内容类型 + neocarbon 方案）必须一字不差。

- [ ] **Step 5: 最终 commit**

```bash
# 若以上检查有差异，修复后 commit
git add .opencode/skills/article-to-presentation/
git commit -m "fix(skill): cross-reference consistency after optimization"
```

若无需修复 → 跳过此 step。
