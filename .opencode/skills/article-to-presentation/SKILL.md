---
name: article-to-presentation
description: "将内容文章转为 Slidev HTML 演示文稿（B站视频录制用）。触发条件：用户要求把文章转为 PPT、演示文稿、幻灯片、或 B站视频素材。"
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
**输出**：PPT文案文档（`content/ppt/YYYY-MM-DD-<topic>/PPT文案.md`）

⚠️ **优先复用**：如果 `content/ppt/YYYY-MM-DD-<topic>/` 下已存在同名 PPT 文案，先读取复用——不要重新生成。仅当缺失或不完整时才从头提取。

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
| 文件 | `slides.md` → `slidev build` → `dist/` SPA；依赖在项目根目录 `package.json` 统一管理 |
| 图表 | neocarbon 25 组件 + Mermaid |
| 翻页 | 键盘纯手动 |
| CJK 字体 | `fonts.sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'` / `fonts.provider: none` |

### 需要确认的维度

| 维度 | 选项 |
|------|------|
| 目标观众 | 技术人员 / 职场白领 / 泛科技爱好者 / 混合 |
| 故事风格 | 数据驱动 / 叙事型 / 观点输出 / 混合 |
| 幻灯片数量 | 15-20 / 25-35 / 40-50 |

### 动画策略（visual companion 确认）

neocarbon 默认电影级动画（staggered entrances、shimmer、pulse、particles）。B站录屏需确认动画档位：

| 档位 | frontmatter / CSS 配置 | 说明 |
|------|-------------|------|
| 保留全部 | `transition: fade`，无额外 CSS | staggered/shimmer/particles 全保留，视觉最炫但录屏可能有动画噪音 |
| **淡入（默认）** | `transition: fade` + 三段降级 CSS | 仅 fade，禁用 staggered/shimmer/particles |
| 全部禁用 | `transition: none` + 全禁 CSS | 纯静态，适合画外音旁白聚焦 |

三段降级 CSS + 全禁 CSS 完整模板 → [references/technical-details.md](references/technical-details.md)「Click 动画配置」章节。

> neocarbon 不支持 `clickAnimation` frontmatter。动画仅靠 `<style>` CSS 控制。

### 布局映射覆盖（可选）

默认映射表 → 详见 [references/technical-details.md](references/technical-details.md)。用户可逐项覆盖。

确认后输出：`content/ppt/YYYY-MM-DD-<topic>/PPT设计.md`

---

## 阶段三：设计方案

技术选型：Slidev + neocarbon 主题

输出内容：
0. **配色预设选择**：从预设库选基础配色（默认霓虹紫），用户可覆盖个别色值。完整预设 → [references/technical-details.md](references/technical-details.md)「配色预设库」
1. **主题配置**：`--nc-accent`、`--nc-success`、`--nc-danger` 颜色值（默认紫/青/玫红）
2. **动画策略**：保留/降级/禁用
3. **布局映射表**：确认或覆盖默认映射（见下方）
4. **幻灯片结构**：按章节组织，每张幻灯片指定 neocarbon 布局 + 组件

### 默认布局映射

5 个最常用布局（速查）：

| PPT 内容类型 | neocarbon 方案 | 示例 |
|-------------|---------|------|
| 封面主标题 | `cover` 布局 | "AI压缩了执行力，放大了判断力" |
| 章节分隔 | `section` 布局 | "第一章 · 执行层的差距" |
| 开场钩子（引用） | `quote` 布局 | "同一个AI，对不同的人'努力程度'不一样" |
| 柱状图对比 | `default` + `<NcBarChart />` | 89% vs 88% |
| 左右概念对比 | `comparison` 布局（`::left::`/`::right::`） | 可编码 vs 默会 |

完整 19 种映射 + 组件 API + 设计令牌 → [references/technical-details.md](references/technical-details.md)「布局映射表（完整版）」章节

审查：提交设计文档给 **Metis**

---

## 阶段四：实施计划

使用 writing-plans 技能编写实现计划。

### 文件结构

```
content/ppt/YYYY-MM-DD-<topic>/
├── slides.md           ← Slidev Markdown（AI 生成）
└── dist/               ← slidev build 输出（gitignore）
```

> 依赖统一放在项目根目录 `package.json` + `node_modules/`，不在每个 PPT 目录单独初始化。

### 任务拆分

| # | 任务 | 执行方式 | category / 说明 |
|---|------|---------|-----------------|
| 1 | 创建 PPT 目录 + 确认根依赖就绪 | **主流程** | 创建 `content/ppt/YYYY-MM-DD-<topic>/` 目录，确认根 `node_modules/` 已安装（见"项目初始化"章节） |
| 2 | 编写 `slides.md` frontmatter + CSS 样式 | **主流程** | 颜色语义决策 + 骨架结构 |
| 3 | 封面 + 章节标题幻灯片（`cover`, `section`） | **主流程** | 模板化输出，不派发子代理 |
| 4 | 数据图表幻灯片（`metrics`, `comparison`, `default` + 组件） | **主流程** | 布局映射 + 颜色编码 + 组件 props 语法 |
| 5 | 引用/金句/案例/结尾幻灯片 + 数据来源（`quote`, `statement`, `spotlight`） | **主流程** | 需理解文章论点的语境 |
| 6 | `slidev build` + 本地服务器预览 + 手动验证 | **主流程 bash** | 纯 CLI 命令，不依赖认知推理。`npx slidev build` 在主流程直接执行 |

### 环境要求

- Node.js >= 20.12.0
- `@slidev/cli` 精确版本 `52.0.0`
- `@enyineer/slidev-theme-neocarbon` 精确版本 `1.0.8`

### npm 包策略

依赖统一由项目根目录 `package.json` 管理，每个 PPT 目录不需要独立 `package.json`。

```bash
# 根目录 package.json 包含：
# @slidev/cli: 52.0.0
# @enyineer/slidev-theme-neocarbon: 1.0.8

# 首次使用：在项目根执行一次
npm install --registry https://registry.npmmirror.com

# 后续使用：检查 root node_modules 已有依赖即可
ls node_modules/@slidev/cli node_modules/@enyineer/slidev-theme-neocarbon
```

> ⚠️ WSL 环境下 `rm -rf node_modules` 可能因深层嵌套目录报 `ENOTEMPTY` 错误。如需清理，用 `find . -name node_modules -exec rm -rf {} + 2>/dev/null`。

---

## 阶段五：计划审查

仅提交给 **Metis** 审查。

审查重点：数据准确性、布局映射合理性、neocarbon 组件使用、颜色编码合规。

常见审查发现 → 详见 [references/common-pitfalls.md](references/common-pitfalls.md)

### Metis 审查失败降级策略

Metis 调用可能因基础架构问题（API 超时、模型不可用等）失败。按以下顺序降级：

1. **重试 1 次**：临时故障，重试通常可恢复
2. **转 Momus 审查**：不同的审查视角，侧重计划完整性和可执行性
3. **输出审查问题列表，用户人工确认**：跳过自动审查，但将审查重点清单输出到对话中供用户逐项确认

> 审查失败 ≠ 计划有问题。基础架构错误不应阻塞流程。

---

## 阶段六：实现

### 项目初始化（主流程 Task 1）

1. 创建 PPT 目录（**⚠️ 目录名必须纯 ASCII，中文会导致 `slidev build` 失败**）
2. 确认项目根目录 `node_modules/` 已安装 `@slidev/cli` 和 `@enyineer/slidev-theme-neocarbon`：
   ```bash
   ls node_modules/@slidev/cli node_modules/@enyineer/slidev-theme-neocarbon
   ```
   如缺失，在根目录执行一次 `npm install --registry https://registry.npmmirror.com`

### 写入 slides.md

AI 生成全部幻灯片 Markdown。关键点：
- **必须**在 `slides.md` 末尾包含 `<style>` 块
- 完整 CSS 模板 + 顺序 → [references/technical-details.md](references/technical-details.md)「Slidev 配置模板」+「Click 动画配置」章节

要点速查：
- 5 个 `--nc-*` 变量（默认霓虹紫，详见「配色预设库」章节）
- CJK 行高 `.slidev-layout { line-height: 1.75; font-size: 24px; }`
- Mermaid 中文补丁 `svg text { font-family: 'PingFang SC',... }`
- **禁用TOC/目录生成**（录屏必加配置+CSS）：
  - 配置：frontmatter 模板已预置 `export.withToc: false` → 导出 PDF/PPTX 不生成目录页
  - CSS：完整TOC隐藏规则见 [references/technical-details.md](references/technical-details.md)「录屏面板隐藏」章节，自动添加到 `<style>` 块
- **内容垂直居中**（`default` 布局内容偏上需修正）→ 完整 CSS 见 [references/technical-details.md](references/technical-details.md)「内容居中」章节，速查：
  ```css
  .slidev-layout.default {
    display: flex !important; flex-direction: column !important;
    justify-content: center !important; padding: 3rem 4rem !important;
  }
  ```
- 动画降级 CSS 按档位选择（详见「Click 动画配置」章节）

### 构建与预览（主流程 Task 6）

`slidev build` 在主流程用 `bash` 直接执行，不派发子代理（构建依赖环境状态，子代理无法保证环境一致）。

```bash
# 在项目根目录执行，指定 slides.md 路径
npx slidev build content/ppt/YYYY-MM-DD-<topic>/slides.md
# 或先 cd 到 PPT 目录（npx 会向上查找 node_modules）
cd content/ppt/YYYY-MM-DD-<topic> && npx slidev build

# 预览
npx serve content/ppt/YYYY-MM-DD-<topic>/dist -p 3030 --no-clipboard
# 打开 http://localhost:3030
# ⚠️ 不能直接用 file:// 打开 — CORS 策略阻止 JS 加载
```

### 手动验证

- 浏览器调至 1920×1080，全屏 F11
- 键盘左右方向键翻页，检查所有 31 张幻灯片
- 颜色编码检查清单：
  - [ ] 默会知识/价值判断：`nc-text-success`（绿色），**不是** `nc-text-accent`
  - [ ] 下降/负面数据：`nc-text-danger`（红色）
  - [ ] 中性数据（如 93% 使用率）：`nc-text-accent`（紫色），**不是** 红色
  - [ ] 所有数据点对照 PPT 文案逐条核对
  - [ ] 数据来源数量一致（文案/计划/实现三方统一，≥6 个）

---

## 参考文件索引

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| [references/technical-details.md](references/technical-details.md) | neocarbon 布局/组件 API、设计令牌、映射表、Slidev 配置模板 | 阶段三/四/六 |
| [references/common-pitfalls.md](references/common-pitfalls.md) | 常见陷阱、审查发现、检查清单 | 阶段五审查时 |
