# article-to-presentation Skill 优化设计

**日期**：2026-06-23
**范围**：Skill 本体优化（3 个文件）
**方案**：B — 结构化优化（重组 + 增补，文件数不变）

---

## 一、背景

### 现状

- 主题：`@enyineer/slidev-theme-neocarbon` v1.0.5（文档）/ v1.0.8（实际）
- 布局覆盖：8 种 / neocarbon 22 种（36%）
- 组件记录：3 种（NcBarChart / NcProgress / NcLineChart）/ 25 种可用
- 已知问题：版本号不一致、CJK 排版缺失、click 动画策略粗略、无多配色方案

### 主题评估结论

| 主题 | 判定 | 理由 |
|------|------|------|
| slidev-theme-vibe | ❌ 不推荐 | 无 GitHub 仓库、周下载 9、双栏固定 50/50、4 月静默 |
| slidev-theme-cyberpunk-ide | ❌ 不推荐 | Issue #7 跨栏代码行号崩溃、0 stars、v0.3.0 预 1.0 |
| @enyineer/slidev-theme-neocarbon | ✅ 继续使用 | 已有生产构建验证、25 组件最丰富、CSS 变量可换皮、双栏 4 种变体 |

### 设计决策

| 决策点 | 选择 |
|--------|------|
| 主题 | 沿用 neocarbon（v1.0.8） |
| 范围 | Skill 本体优化，3 个文件 |
| 默认配色 | **霓虹紫**（前沿科技/AI Agent/赛博朋克定位） |
| 备选配色 | 暖橙 + 赛博绿 |
| 默认动画 | 淡入（fade），三档可选 |
| CJK 处理 | 系统字体栈 + provider: none + 行高补丁 |

---

## 二、SKILL.md 改动清单

### 2.1 阶段二「固定值」表 — 新增 2 行

| 维度 | 新增值 |
|------|--------|
| 默认 click 动画 | `clickAnimation: fade` |
| CJK 字体 | `fonts.sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'` / `fonts.provider: none` |

`provider: none` 禁止 Google Fonts CDN 自动请求——国内网络不可达，会阻塞构建。

### 2.2 阶段二「需要确认的维度」— 动画选项细化

现有三档从文字描述改为 frontmatter + CSS 精确配置对照表：

| 档位 | frontmatter | `<style>` CSS | 说明 |
|------|------------|-------------|------|
| 保留全部 | `clickAnimation: fade.up` | 无额外 CSS | staggered/shimmer/particles 全保留 |
| **淡入（默认）** | `clickAnimation: fade` / `transition: fade` | 三段降级 CSS（见下） | 仅 fade，禁用 staggered/shimmer/particles |
| 全部禁用 | `transition: none` | 全禁 CSS（见下） | 纯静态，适合纯旁白 |

现有"动画策略（visual companion 确认）"表替换为上表。

**淡入档三段降级 CSS（完整写法）：**

```css
.nc-stagger > * { animation: none !important; opacity: 1 !important; }
.nc-shimmer { animation: none !important; }
.nc-particles { display: none !important; }
```

**全禁 CSS（完整写法）：**

```css
.nc-stagger > *,
.nc-shimmer,
.nc-particles,
[class*="nc-animate"] { animation: none !important; opacity: 1 !important; }
```

> ⚠️ `clickAnimation` frontmatter 字段需经第七节验证（7.3）。
> 若不生效，改为纯 CSS 降级方案（不写 frontmatter，仅靠 `<style>` 控制）。

### 2.3 阶段三 — 新增配色预设选择步骤

在"1. 主题配置"之前插入：

```
0. **配色预设选择**：从预设库选择基础配色（霓虹紫默认），
   用户可覆盖个别色值。完整预设 → references/technical-details.md「配色预设库」
```

同时更新"1. 主题配置"中的颜色变量默认值为霓虹紫色值。

### 2.4 布局映射表 — 8 → 15 种

新增 7 行：

| PPT 内容类型 | neocarbon 方案 | 示例 |
|-------------|---------|------|
| 趋势数据（多线） | `default` + `<NcLineChart />` | 7 个月会话变化 |
| 流程分叉图 | `diagram` + Mermaid | 碰壁→放弃/翻盘 |
| 终端/CLI 展示 | `default` + `<NcTerminal />` | 部署命令输出 |
| 多步流程 | `default` + `<NcSteps />` | 管线步骤 |
| 金融指标/KPI | `metrics` + `<NcRoiCard />` | ROI 卡片 |
| 浏览器截图 | `browser` 布局 | Web 产品界面 |
| 翻转卡片 | `default` + `<NcFlipCard />` | 术语定义（正/反面） |

### 2.5 阶段四 — 版本号统一

```
@slidev/cli: 52.0.0
@enyineer/slidev-theme-neocarbon: 1.0.8
```

同步「环境要求」段。

### 2.6 阶段六 — slides.md 模板更新

frontmatter 示例更新为：

```yaml
---
theme: '@enyineer/slidev-theme-neocarbon'
title: '演示文稿标题'
clickAnimation: fade
transition: fade
highlighter: shiki
fonts:
  sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'
  serif: 'Noto Serif SC, serif'
  mono: 'Fira Code, monospace'
  provider: none
---
```

`<style>` 块模板统一包含：
- 霓虹紫 5 变量（默认）
- Mermaid CJK 补丁
- TOC 隐藏 CSS
- 对应档位的动画降级 CSS

---

## 三、technical-details.md 改动清单

### 3.1 配色方案 — 重构为「配色预设库」

**位置**：替换现有「配色方案」+「CSS 实用类」+「颜色编码规则」三节。

新结构：

#### 3.1.1 预设 A：霓虹紫（默认）

```css
:root {
  --nc-accent:  #a855f7;   /* 紫 → 中性强调 */
  --nc-success: #22d3ee;   /* 青 → 正面数据 */
  --nc-danger:  #f43f5e;   /* 玫红 → 负面数据 */
  --nc-warning: #fbbf24;
  --nc-info:    #818cf8;
}
```

适用场景：前沿科技、AI Agent、赛博朋克话题。

#### 3.1.2 预设 B：暖橙

```css
:root {
  --nc-accent:  #ff6b35;
  --nc-success: #22c55e;
  --nc-danger:  #ef4444;
  --nc-warning: #f59e0b;
  --nc-info:    #3b82f6;
}
```

适用场景：数据分析、趋势报告、综合科技内容。

#### 3.1.3 预设 C：赛博绿

```css
:root {
  --nc-accent:  #00ff9d;
  --nc-success: #34d399;
  --nc-danger:  #f87171;
  --nc-warning: #fcd34d;
  --nc-info:    #67e8f9;
}
```

适用场景：安全主题、基础设施、运维/SRE 话题。

#### 3.1.4 使用方式

1. 阶段三从三套预设中选基础配色（默认霓虹紫）
2. 用户可逐色覆盖
3. 颜色编码语义不变：success=正面/danger=负面/accent=中性

#### 3.1.5 CSS 实用类 + 颜色编码规则

**保留现有内容**，仅将所有颜色示例更新为霓虹紫默认值：
- `nc-text-success` → 青色（正面）
- `nc-text-danger` → 玫红（负面）
- `nc-text-accent` → 紫色（中性）

### 3.2 新增「CJK 排版」章节

**位置**：插入在「字体」之后、「幻灯片比例」之前。

内容：

1. **frontmatter 字体配置（必须）** — 完整配置段 + 各字段说明（sans/serif/mono 选择逻辑、provider: none 原因）
2. **行高（必须）** — `.slidev-layout { line-height: 1.75; font-size: 24px; }` + CJK 行高原因
3. **Mermaid 中文补丁（必须）** — `svg text` font-family CJK 栈 + 不加的后果
4. **PDF 导出注意（可选）** — `--timeout 60000 --wait 1000`、CI 字体安装提示

### 3.3 新增「Click 动画模板」章节

**位置**：替换现有「动画控制」节，重写为完整版。

内容：

1. **三档策略对照表** — frontmatter + CSS + 适用场景
2. **淡入模式降级 CSS（默认生效）** — 三段选择器禁用 staggered/shimmer/particles
3. **全禁 CSS** — 完整版选择器
4. **v-click 使用示例** — 逐个淡入、嵌套列表 `depth="2"`、定时出现/消失 `[2,4]`
5. **slide 总点击数** — `clicks: N` frontmatter 用途

### 3.4 扩展布局 API 文档

**位置**：现有 8 种布局 API 之后追加 7 种：

1. `browser` — Safari 浏览器截图框架
2. `spotlight` — 全黑聚光灯
3. `<NcTerminal />` — 终端模拟器（逐行输出 + 闪烁光标）
4. `<NcSteps />` — 多步流程指示器（done/active/pending）
5. `<NcFlipCard />` — 3D 翻转卡片（#front / #back 插槽）
6. `<NcLineChart />` — 多线趋势扩展示例（双 Y 轴用例）
7. `<NcHeatmap />` — GitHub 风格热力图

### 3.5 布局映射表 — 补全至 15+ 行

technical-details.md 现有映射表已有 13 行（非 8 行）。此处仅添加**现有表中未包含的新行**。
最终行数取决于实际重叠，预计 15-20 行。
两个文件（SKILL.md / technical-details.md）的映射表内容（PPT 内容类型 + neocarbon 方案）必须完全一致。

---

## 四、common-pitfalls.md 改动清单

### 4.1 新增 4 条陷阱（#17-#20）

**陷阱一览表追加：**

| # | 陷阱 | 后果 | 预防 |
|---|------|------|------|
| 17 | CJK 行高缺失 | 中文汉字上下行挤在一起，可读性下降 | `<style>` 中设置 `.slidev-layout { line-height: 1.75; }` |
| 18 | 配色预设覆盖遗漏 | 选了预设但漏改部分变量，该语义色仍是旧默认值 | 选择预设后完整粘贴整套 5 变量，不要只改单个 |
| 19 | click 动画与 slide 过渡冲突 | `transition: slide-left` + `clickAnimation: fade.up` → 翻页瞬间元素先淡入再位移 | 统一动画方向，不混搭 |
| 20 | font provider 阻塞构建 | Google Fonts CDN 请求超时 → `slidev dev` 卡死数分钟 | frontmatter 设 `fonts.provider: none` |

### 4.2 「审查常见发现」追加 2 段

**配色预设审查：**

- 阶段二选定预设后，检查 `<style>` 中 5 个 CSS 变量是否全部覆盖
- 遗漏任一变量 → 该语义色仍是上次使用的值
- 自定义色值仍遵守语义：success 正面、danger 负面、accent 中性

**Click 动画审查：**

- frontmatter `clickAnimation` 值与 `<style>` 降级 CSS 必须匹配
- 淡入档 → 含 `.nc-stagger`/`.nc-shimmer`/`.nc-particles` 禁用 CSS
- 全禁档 → 含全禁 CSS 块 + `transition: none`
- 复杂幻灯片（3+ v-click）必须显式设 `clicks: N`

### 4.3 「实现完成前检查清单」追加 4 条

```markdown
- [ ] 配色预设 5 变量全部覆盖（或确认使用默认霓虹紫）
- [ ] CJK 行高 ≥ 1.75（`.slidev-layout`）
- [ ] Mermaid 中文补丁生效（`svg text` font-family 含 CJK 字体）
- [ ] `fonts.provider: none` 已设置
```

---

## 五、不改动的部分

| 内容 | 原因 |
|------|------|
| Phase 1 数据提取 | 流程已稳定 |
| Phase 5 Metis 审查流程 | 审查机制不变，只是审查条目在 common-pitfalls 中追加 |
| 文件结构 / 构建命令 | 不变 |
| 整体 6 阶段流程 | 不变 |
| 颜色编码语义规则 | 不变（success=正面/danger=负面/accent=中性） |

---

## 六、风险评估

| 风险 | 等级 | 缓解 |
|------|------|------|
| 默认配色切换导致已有项目不兼容 | 🟢 低 | 配色在 `<style>` 覆盖，不改主题版本 |
| CJK 字体栈在不同平台表现差异 | 🟡 中 | 三级回退：PingFang SC → Microsoft YaHei → Noto Sans SC |
| 新布局 API 文档与实际组件行为不一致 | 🟡 中 | 基于 neocarbon v1.0.8 源码验证，非凭记忆 |
| 新陷阱遗漏重要场景 | 🟢 低 | 基于已有生产构建经验补充，非凭空推测 |
| `clickAnimation` 非真实 Slidev 字段 | 🔴 高 | 实施前验证（见第七节），不存在则降级为 CSS-only 方案 |
| 新增组件在 v1.0.8 中不存在 | 🔴 高 | 实施前验证（见第七节），不存在则标注 ⚠️ 占位 |
| 颜色语义文本未同步（"橙色"→"紫色"） | 🟡 中 | 见第七节 grep 指令 |

---

## 七、验证前置条件（Metis 审查追加）

**以下验证必须在实施任何文件改动之前完成。**

### 7.1 neocarbon v1.0.8 存在性验证

```bash
npm view @enyineer/slidev-theme-neocarbon@1.0.8 version
# 预期输出：1.0.8
```

若不存在 → 使用实际最新版本，spec 中所有 `1.0.8` 引用同步更新。

### 7.2 新增组件存在性验证

```bash
# 安装后检查组件文件
ls node_modules/@enyineer/slidev-theme-neocarbon/components/ | grep -iE "terminal|steps|flip|roi|heatmap"
```

逐个确认：
- `NcTerminal.vue` → 存在？
- `NcSteps.vue` → 存在？
- `NcFlipCard.vue` → 存在？
- `NcRoiCard.vue` → 存在？
- `NcHeatmap.vue` → 存在？

**不存在 → technical-details.md 中该组件文档标注 `⚠️ 需验证 — 基于 README 描述，未经源码确认`。** 写入完整但带警告的文档，而非删除。

### 7.3 `clickAnimation` 字段验证

创建一个最小化测试 `slides.md`：

```yaml
---
theme: '@enyineer/slidev-theme-neocarbon'
clickAnimation: fade
transition: fade
---

# Slide 1

<v-clicks>
- Item A
- Item B
</v-clicks>
```

```bash
npx slidev build
# 检查：exit code 0 且无 "unknown frontmatter" 警告
# 浏览器中检查 v-click 动画是否为 fade 而非默认动画
```

**结果判定：**
- `clickAnimation` 被识别且生效 → spec 保持不变
- `clickAnimation` 被忽略但不报错 → 改为 CSS-only 方案（不写 frontmatter，只在 `<style>` 中通过 CSS 控制）
- `clickAnimation` 报错 → 完全移除该字段，改用 Slidev 原生 `transition` + CSS 降级

### 7.4 `fonts.provider: none` 验证

在 7.3 的测试 slides.md 中加入：

```yaml
fonts:
  sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'
  provider: none
```

构建后用浏览器 DevTools Network 面板确认：**无 `fonts.googleapis.com` 请求**。

### 7.5 颜色语义文本更新范围

实施前执行以下 grep，确定所有需更新的位置：

```bash
grep -n "橙色\|#ff6b35\|nc-text-accent.*橙" .opencode/skills/article-to-presentation/references/technical-details.md
grep -n "1\.0\.5" .opencode/skills/article-to-presentation/
```

所有匹配项按以下规则处理：
- `#ff6b35`（作为默认示例时）→ `#a855f7`
- "橙色"（作为默认配色描述时）→ "紫色"
- `1.0.5` → `1.0.8`
- `#ff6b35`（作为预设 B 暖橙的示例时）→ 保留不变

### 7.6 布局映射行数对齐

- SKILL.md：8 行 → 加 7 行 = **15 行**
- technical-details.md：先 diff 现有 13 行与新 7 行的重叠情况，仅添加**未包含的行**。最终行数可能是 15-20 行。
- 两个文件的映射表内容（PPT 内容类型 + neocarbon 方案两列）必须完全一致。
