# 常见陷阱

## 陷阱一览

| # | 陷阱 | 后果 | 预防 |
|---|------|------|------|
| 1 | **neocarbon 布局语法错误** | `comparison` 布局漏写 `::left::`/`::right::` 插槽 → 内容不显示或布局崩溃 | 检查每个布局的必需插槽：`comparison` 需 `::left::`/`::right::`，`metrics` 需 `::metrics::`，`diagram` 需 `::left::`/`::right::` |
| 2 | **组件 props 绑定缺失** | `<NcBarChart labels="..." />` 漏写 `:` 前缀 → 数组 props 被当作字符串，图表不渲染 | 数组/数字 props 必须用 `:` 前缀：`:labels`, `:data`, `:colors`, `:datasets` |
| 3 | **颜色编码违规（默会知识用橙色）** | 默会知识/价值判断写了 `nc-text-accent`（橙色）而非 `nc-text-success`（绿色）→ 违反颜色语义 | 严格对照颜色编码规则，默会知识/价值判断**必须**绿色 |
| 4 | **红色用于中性数据** | 中国 93% AI使用率标红 → 被误解为负面数据 | 红色仅用于下降/负面。中性数据用 `nc-text-accent`（橙色）或 `nc-text-muted`（灰色） |
| 5 | **`slidev build` 不支持 `file://`** | 直接用浏览器打开 `dist/index.html` → 空白页或 JS 加载失败 | 始终用本地服务器：`npx serve dist -p 3030` |
| 6 | **动画干扰录屏** | neocarbon 默认 staggered entrances + shimmer + particles 在录屏中产生视觉噪音 | 在阶段二确认动画策略，阶段六实施前检查 `<style>` 中的动画降级 CSS 是否已生效 |
| 7 | **Mermaid 中文文本渲染异常** | Mermaid 节点中的中文在某些字体下显示为方框 | 在 `<style>` 中添加 `svg text { font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important; }` |
| 8 | **数据来源数量矛盾** | PPT文案、设计文档、实现三处来源数量不一致 | 统一三方数据来源，至少 6 个来源交叉验证 |
| 9 | **复制粘贴数据错误** | 复制柱状图 HTML 到另一张幻灯片时忘记改 `:data` 值 | 逐张核查每张幻灯片的数据值，确保与文案一致 |
| 10 | **幻灯片排序未验证** | 章节标题出现顺序错误（第三章在第二章前），肉眼粗略浏览不易发现 | 逐张检查章节标题在正确的 slide 位置 |
| 11 | **CJK 字体回退异常** | 中文文字在 neocarbon 中出现粗细不均或字形回退 | 在 frontmatter 中设置 `fonts.sans: 'PingFang SC, Microsoft YaHei, sans-serif'` |
| 12 | **`<style>` 块位置错误** | 颜色令牌覆盖 CSS 写在 `<style>` 块外部 → 不生效 | 颜色令牌和动画控制 CSS 必须写在 `slides.md` 的 `<style>` 块内（不拘位置，建议在末尾） |
| 13 | **中文目录名导致构建失败** | `slidev build` 对 URL 编码的中文路径处理异常 → vite 报错 | 目录名只用 ASCII：`AI-execution-judgment` 而非 `AI压缩执行力` |
| 14 | **Slidev TOC 面板遮挡内容** | 右侧导航目录面板在录屏时覆盖幻灯片内容 → 画面不完整 | 在 `<style>` 中添加 `.slidev-toc, .slidev-nav, .slidev-menu { display: none !important; }` |
| 15 | **npm 安装慢（国内网络）** | `npm install` 耗时数分钟甚至超时 → 阻塞流程 | 使用镜像：`npm install --registry https://registry.npmmirror.com` |
| 16 | **`npx serve` 配置不当** | 目录列表泄露 / 端口冲突 / 路径错误 → 多次重启 | 固定命令：`npx serve dist -p 3030 --no-clipboard`，从 `dist/` 目录启动，不是项目根目录 |
| 17 | **CJK 行高缺失** | 中文汉字上下行挤在一起，可读性下降 | `<style>` 中设置 `.slidev-layout { line-height: 1.75; font-size: 24px; }` |
| 18 | **配色预设覆盖遗漏** | 选了预设但漏改部分变量，该语义色仍是旧默认值 | 选择预设后完整粘贴整套 5 变量（accent/success/danger/warning/info），不要只改单个 |
| 19 | **click 动画与 slide 过渡冲突** | `transition: slide-left` + `clickAnimation: fade.up` → 翻页瞬间元素先淡入再位移，视觉撕裂 | 统一动画方向：要么全 fade，要么全 slide，不混搭 |
| 20 | **font provider 阻塞构建** | Google Fonts CDN 请求超时 → `slidev dev` 或 `slidev build` 卡死数分钟 | frontmatter 设 `fonts.provider: none` |

---

## 审查常见发现

### 颜色编码

- **默会知识/价值判断必须用 `nc-text-success`（绿色）**。是审查中最常见的错误——AI agent 倾向用 `nc-text-accent`（橙色）来"强调"价值判断，这违反了颜色语义。
- **红色仅用于负面**。93% 的 AI 使用率是事实性数据，不能标红。
- **检查**：遍历 `slides.md`，搜索 `nc-text-danger` 和 `nc-text-success` 的每次使用，确认上下文匹配颜色语义。

### 配色预设

- **阶段二选定预设后，检查 `<style>` 中 5 个 CSS 变量是否全部覆盖**
- 遗漏任一变量 → 该语义色仍是上次使用的值，视觉上与预设不协调
- 自定义色值仍遵守语义：success 正面、danger 负面、accent 中性
- **检查**：搜索 `--nc-accent`、`--nc-success`、`--nc-danger`、`--nc-warning`、`--nc-info` 在 `<style>` 中是否全部出现

### Click 动画

- **`<style>` 中的动画降级 CSS 必须与档位匹配**
- 淡入档 → 含 `.nc-stagger > *`/`.nc-shimmer`/`.nc-particles` 禁用 CSS
- 全禁档 → 含全禁 CSS 块 + `transition: none`
- 复杂幻灯片（3+ v-click）必须显式设 `clicks: N`
- **检查**：搜索 frontmatter 中的 `transition: none`，确认与 `<style>` 中的动画 CSS 一致

### 布局语法

- **`comparison` 必须含 `::left::` 和 `::right::`**。漏写则左右内容不区分。
- **`metrics` 必须含 `::metrics::`**。每张指标卡用 `<div class="nc-metric">` 包裹。
- **`diagram` 必须含 `::left::` 和 `::right::`**。右侧放 Mermaid，左侧放文字说明。

### 组件调用

- **数组 props 加 `:`**：`:labels`, `:data`, `:colors`, `:datasets`
- **颜色值用 CSS 变量**：`:colors="['var(--nc-success)', 'var(--nc-accent)']"`
- **`<NcBarChart />` 的 `data` 接收百分比数值**（0-100），不是小数

### B站录屏准备

- **构建前确认动画策略**：检查 `<style>` 块中的动画降级 CSS
- **构建后验证**：`npx serve dist -p 3030` → 浏览器打开 → F12 检查无 console 错误

---

## 实现完成前检查清单

- [ ] 所有数据点正确（对照 PPT 文案逐条核对）
- [ ] 颜色编码一致（绿=正面/默会，红=负面，橙=中性）
- [ ] `nc-text-success` 用于默会知识/价值判断（**不是** `nc-text-accent`）
- [ ] `nc-text-danger` 仅用于负面/下降（**不是**中性数据）
- [ ] 动画策略已实施（保留/降级/禁用，按阶段二确认）
- [ ] 数据来源数量一致（文案/计划/实现三方统一，≥6 个）
- [ ] 目录名纯 ASCII（无中文字符）
- [ ] Slidev TOC 面板隐藏 CSS 已添加
- [ ] `slidev build` 成功，无错误
- [ ] `npx serve dist -p 3030` 后浏览器可正常打开（**不是** `file://`）
- [ ] 1920×1080 分辨率下每张幻灯片内容完整（无 TOC 遮挡）
- [ ] 无 console 错误
- [ ] 章节标题在正确的 slide 位置
- [ ] 配色预设 5 变量全部覆盖（或确认使用默认霓虹紫）
- [ ] CJK 行高 ≥ 1.75（`.slidev-layout`）
- [ ] Mermaid 中文补丁生效（`svg text` font-family 含 CJK 字体）
- [ ] `fonts.provider: none` 已设置
