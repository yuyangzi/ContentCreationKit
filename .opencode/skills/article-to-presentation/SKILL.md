---
name: article-to-presentation
description: "将内容文章转为可用于B站视频录制的HTML演示文稿(Slidev + neocarbon主题)。触发条件: 用户要求将文章/文案转为PPT、演示文稿、幻灯片、或B站视频素材。流程: 数据提取→生成PPT文案→/before-dev(需求确认+visual companion动画策略)→设计方案→Metis审查→实施计划→实现(slides.md生成+slidev build)"
---

# 文章转HTML演示文稿

将一篇内容文章转化为霓虹/赛博/玻璃态风格的HTML演示文稿，用于B站视频录制。

技术栈：Slidev + `@enyineer/slidev-theme-neocarbon` 主题。AI 代理生成 Markdown，主题接管视觉。

## 核心流程

```
文章 → 提取数据+生成PPT文案 → /before-dev(需求确认+visual companion动画策略)
  → 设计方案(布局映射+组件选型) → Metis审查 → 实施计划
  → 实现(slides.md生成 + slidev build + 预览)
```

每个阶段有明确产出和审查点，不可跳过。

---

## 阶段一：数据提取 + PPT文案生成

**输入**：文章（MD/TXT/URL）
**输出**：PPT文案文档（`docs/superpowers/specs/YYYY-MM-DD-<topic>-PPT文案.md`）

⚠️ **优先复用**：如果 `docs/superpowers/specs/` 下已存在同名 PPT 文案，先读取复用——不要重新生成。仅当缺失或不完整时才从头提取。

提取内容：
1. **核心论点** — 文章想传达什么
2. **关键数据** — 所有可量化的数字、百分比、趋势
3. **故事线** — 章节划分和叙事结构（通常 4-6 章）
4. **金句** — 适合独立展示的引用或警句
5. **数据来源** — 每个数据的出处（必须 6 个以上来源交叉验证）

生成PPT文案时，按章节组织，每章标明幻灯片内容、数据图表类型。

**要求**：每个数据点标注来源，区分一手数据（原始报告）和二手数据（媒体报道）

---

## 阶段二：需求确认

使用 `/before-dev` 命令，逐步确认。

### 固定值（不询问，直接应用）

| 维度 | 值 |
|------|-----|
| 使用场景 | B站视频录屏 |
| 框架 | Slidev + `@enyineer/slidev-theme-neocarbon` |
| 文件 | `slides.md` + `package.json` → `slidev build` → `dist/` SPA |
| 图表 | neocarbon 25 组件 + Mermaid |
| 翻页 | 键盘纯手动 |

### 需要确认的维度

| 维度 | 选项 |
|------|------|
| 目标观众 | 技术人员 / 职场白领 / 泛科技爱好者 / 混合 |
| 故事风格 | 数据驱动 / 叙事型 / 观点输出 / 混合 |
| 幻灯片数量 | 15-20 / 25-35 / 40-50 |

### 动画策略（visual companion 确认）

neocarbon 默认电影级动画（staggered entrances、shimmer、pulse、particles）。B站录屏需确认：

| 选项 | 说明 |
|------|------|
| 保留全部 | 视觉最炫，但录屏可能有动画噪音 |
| 降级为淡入 | 禁用 staggered/shimmer/particles，保留 fade |
| 全部禁用 | 纯静态，适合画外音旁白聚焦 |

### 布局映射覆盖（可选）

默认映射表 → 详见 [references/technical-details.md](references/technical-details.md)。用户可逐项覆盖。

确认后输出：`docs/superpowers/specs/YYYY-MM-DD-<topic>-PPT设计.md`

---

## 阶段三：设计方案

技术选型：Slidev + neocarbon 主题

输出内容：
1. **主题配置**：`--nc-accent`、`--nc-success`、`--nc-danger` 颜色值（默认橙/绿/红）
2. **动画策略**：保留/降级/禁用
3. **布局映射表**：确认或覆盖默认映射（见下方）
4. **幻灯片结构**：按章节组织，每张幻灯片指定 neocarbon 布局 + 组件

### 默认布局映射

| PPT 内容类型 | neocarbon 方案 |
|-------------|---------------|
| 封面主标题 | `cover` 布局 |
| 章节分隔 | `section` 布局 |
| 开场钩子（引用） | `quote` 布局 |
| 柱状图对比 | `default` + `<NcBarChart />` |
| 并排指标卡 | `metrics` 布局 |
| 左右概念对比 | `comparison` 布局（`::left::`/`::right::`） |
| 金句（多行大字） | `statement` 布局 |
| 数据来源列表 | `default` 布局 |

完整映射 + 组件 API + 设计令牌 → 详见 [references/technical-details.md](references/technical-details.md)

审查：提交设计文档给 **Metis**

---

## 阶段四：实施计划

使用 writing-plans 技能编写实现计划。

### 文件结构

```
content/ppt/YYYY-MM-DD-<topic>/
├── slides.md           ← Slidev Markdown（AI 生成）
├── package.json        ← 依赖（精确版本）
└── dist/               ← slidev build 输出（gitignore）
```

### 任务拆分

1. **Task 1**: 初始化项目（`package.json` + `npm install`）
2. **Task 2**: 编写 `slides.md` frontmatter（主题配置、颜色令牌、动画策略）
3. **Task 3**: 生成封面 + 章节标题幻灯片（`cover`, `section`）
4. **Task 4**: 生成数据图表幻灯片（`metrics`, `comparison`, `default` + 组件）
5. **Task 5**: 生成引用/金句/案例幻灯片（`quote`, `statement`）
6. **Task 6**: 生成结尾幻灯片 + 数据来源
7. **Task 7**: `slidev build` + 本地服务器预览 + 手动验证

### 环境要求

- Node.js >= 20.12.0
- `@slidev/cli` 精确版本 `52.0.0`
- `@enyineer/slidev-theme-neocarbon` 精确版本 `1.0.5`

---

## 阶段五：计划审查

仅提交给 **Metis** 审查。

审查重点：数据准确性、布局映射合理性、neocarbon 组件使用、颜色编码合规。

常见审查发现 → 详见 [references/common-pitfalls.md](references/common-pitfalls.md)

---

## 阶段六：实现

### 项目初始化

1. 创建目录（**⚠️ 目录名必须纯 ASCII，中文会导致 `slidev build` 失败**）
2. 写入 `package.json`（精确版本）
3. 安装依赖：

```bash
# 国内用户用镜像加速
npm install --registry https://registry.npmmirror.com
```

### 写入 slides.md

AI 生成全部幻灯片 Markdown。关键点：
- 颜色令牌在 `<style>` 块中覆盖 `--nc-accent`/`--nc-success`/`--nc-danger`
- 动画控制 CSS 在同一个 `<style>` 块中
- **必须**在 `<style>` 中添加 Slidev TOC 面板隐藏（录屏时遮挡内容）：

```css
/* 隐藏 Slidev 导航面板 — 录屏时遮挡内容 */
.slidev-toc, .slidev-nav, .slidev-menu { display: none !important; }
```

### 构建与预览

```bash
npx slidev build
npx serve dist -p 3030 --no-clipboard
# 打开 http://localhost:3030
# ⚠️ 不能直接用 file:// 打开 — CORS 策略阻止 JS 加载
```

### 手动验证

- 浏览器调至 1920×1080，全屏 F11
- 键盘左右方向键翻页，检查所有 31 张幻灯片
- 颜色编码检查清单：
  - [ ] 默会知识/价值判断：`nc-text-success`（绿色），**不是** `nc-text-accent`
  - [ ] 下降/负面数据：`nc-text-danger`（红色）
  - [ ] 中性数据（如 93% 使用率）：`nc-text-accent`（橙色），**不是** 红色
  - [ ] 所有数据点对照 PPT 文案逐条核对
  - [ ] 数据来源数量一致（文案/计划/实现三方统一，≥6 个）

---

## 参考文件索引

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| [references/technical-details.md](references/technical-details.md) | neocarbon 布局/组件 API、设计令牌、映射表、Slidev 配置模板 | 阶段三/四/六 |
| [references/common-pitfalls.md](references/common-pitfalls.md) | 常见陷阱、审查发现、检查清单 | 阶段五审查时 |
