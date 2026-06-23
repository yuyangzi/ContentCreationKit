# 设计文档：Apple Core AI 演示文稿

> 基于文章：content/article/20260623-Apple-Core-AI框架深度解读-设备端大模型时代来临.md
> PPT文案：docs/superpowers/specs/2026-06-23-Apple-Core-AI-PPT文案.md
> 生成日期：2026-06-23

---

## 1. 基本配置

| 维度 | 值 |
|------|-----|
| 使用场景 | B站视频录屏（1920×1080, 16:9） |
| 框架 | Slidev + @enyineer/slidev-theme-neocarbon v1.0.8 |
| 文件 | content/ppt/2026-06-23-Apple-Core-AI/slides.md |
| 构建 | slidev build → dist/ SPA |
| 图表 | neocarbon 组件 + Mermaid |
| 翻页 | 键盘纯手动 |
| 幻灯片总数 | 33 张 |

### 配色方案 — 霓虹紫（预设 A）

```css
:root {
  --nc-accent:  #a855f7;   /* 紫 — 中性强调、主标题高亮 */
  --nc-success: #22d3ee;   /* 青 — 正面数据、价值判断 */
  --nc-danger:  #f43f5e;   /* 玫红 — 负面数据、下降/警示 */
  --nc-warning: #fbbf24;   /* 琥珀 — 保留 */
  --nc-info:    #818cf8;   /* 靛蓝 — 保留 */
}
```

### 动画策略 — 淡入（默认）

- frontmatter: `transition: fade`
- 三段降级 CSS（禁用 staggered/shimmer/particles）

---

## 2. 布局映射表

| # | 幻灯片内容 | neocarbon 方案 | 说明 |
|---|-----------|---------------|------|
| 1 | 封面：Apple Core AI | `cover` 布局 | 主标题 + 副标题 + 数据来源脚注 |
| 2 | "苹果把AI叙事劈成两层" | `quote` 布局 | 开场钩子引用 |
| 3 | 消费者层：Siri AI 升级 | `default` 布局 | 列表：Gemini蒸馏 / Foundation Models / Liquid Glass |
| 4 | 开发者层：Core AI 框架 | `default` 布局 | 列表：Session 325/326 / AOT编译 / Metal 4 |
| 5 | 章节：双轨 AI 战略 | `section` 布局 | "第二章·开放合作 × 垂直自研" |
| 6 | Federighi 的澄清 | `quote` 布局 | "我们使用Google Assistant数量为零" |
| 7 | 消费端：合作补齐 | `default` 布局 | 列表：Gemini蒸馏 / ChatGPT/Claude备选 |
| 8 | 开发者端：垂直自研 | `comparison` 布局 | 左：消费端合作 / 右：开发者端自研 |
| 9 | 历史的重演 | `default` 布局 | WebKit / Metal / Core AI 类比 |
| 10 | 章节：Core AI 技术深潜 | `section` 布局 | "第三章·模型变成原生二进制" |
| 11 | 一句话核心 | `statement` 布局 | "让模型变成原生二进制产物" |
| 12 | 三步流程 | `default` + `<NcSteps />` | PyTorch→.aimodel→.aimodelc flow |
| 13 | AOT vs JIT 编译 | `comparison` 布局 | 左：传统JIT / 右：苹果AOT |
| 14 | Metal 4 + 自定义内核 | `default` + `<NcTerminal />` | TorchMetalKernel 代码示例 |
| 15 | 统一内存架构 | `diagram` + Mermaid | CPU/GPU/ANE 共享内存池 |
| 16 | Swift API 三概念 | `default` 布局 | AIModel / InferenceFunction / NDArray |
| 17 | API 一致性的工程意义 | `quote` 布局 | "3B到70B，同一套调用" |
| 18 | 章节：70B 的真实边界 | `section` 布局 | "第四章·不是所有苹果设备都叫Mac" |
| 19 | 70B 内存占用 | `metrics` 布局 | 40-46GB 数字卡片 |
| 20 | 设备分级金字塔 | `diagram` + Mermaid | iPhone→iPad Pro→Mac工作站 |
| 21 | 性能基准对比 | `default` + `<NcBarChart />` | 7B/13B/70B tok/s 柱状图 |
| 22 | 12-18 tok/s 意味着什么 | `default` 布局 | 流式对话体验说明 |
| 23 | 混合精度推理 | `default` + `<NcBarChart />` | FP16/INT8/INT4 选择逻辑 |
| 24 | 章节：Core ML 九年 | `section` 布局 | "第五章·三层框架的必然分工" |
| 25 | Core ML 时间线 | `default` + `<NcSteps />` | 2017→2026 六次大版本 |
| 26 | 新三框架分工 | `comparison` 布局 | Core ML / Core AI / MLX 对比 |
| 27 | 分层优于合并 | `quote` 布局 | "焊装车间和涂装车间不用同一套设备" |
| 28 | 章节：生态锁定的逻辑 | `section` 布局 | "第六章·地基花园" |
| 29 | 苹果铁三角 | `diagram` + Mermaid | 芯片×框架×分发 |
| 30 | 不是围墙花园 | `spotlight` 布局 | "土是苹果的" 核心洞察 |
| 31 | 竞争变量 | `comparison` 布局 | Google AI Edge SDK vs Apple Core AI |
| 32 | 时序问题 + 终局展望 | `default` 布局 | 为什么 Core AI 现在开放？ |
| 33 | 结尾金句 | `statement` 布局 | "几十万个App的AI集成能力" |

---

## 3. 颜色编码规则

| 数据类型 | 颜色 | CSS 类 |
|----------|------|--------|
| 正面数据、价值判断、苹果优势 | 青色 | `nc-text-success` |
| 负面数据、下降趋势、性能瓶颈 | 玫红 | `nc-text-danger` |
| 中性强调、关键数字、技术名词 | 紫色 | `nc-text-accent` |
| 辅助说明、数据来源、脚注 | 灰色 | `nc-text-muted` |

**关键校验**（严格检查）：
- [x] 40-46GB 内存占用 → 中性数据 → `nc-text-accent`（非红色）
- [x] 12-18 tok/s 速度 → 中性数据（非瓶颈，仅是现状）→ `nc-text-accent`
- [x] 统一内存架构 → 正面（苹果优势）→ `nc-text-success`
- [x] AOT 编译消除 JIT 卡顿 → 正面 → `nc-text-success`
- [x] iPhone 12GB 上限 → 限制说明 → `nc-text-danger`
- [x] 数据来源标注 → 均使用 `nc-text-muted`

---

## 4. 幻灯片结构概览

```
第一组（Slide 1-4）:  开场 — WWDC双层叙事
第二组（Slide 5-9）:  第二章 — 双轨AI战略
第三组（Slide 10-17）: 第三章 — Core AI技术深潜
第四组（Slide 18-23）: 第四章 — 70B真实边界
第五组（Slide 24-27）: 第五章 — Core ML九年
第六组（Slide 28-33）: 第六章 — 生态锁定
```

---

## 5. 数据来源一致性检查

| 检查项 | 结果 |
|--------|------|
| 数据来源数量 | 9 个（≥6 ✅） |
| 一手来源（官方） | Apple Developer Sessions, Core AI Docs, Apple Newsroom |
| 二手来源（媒体/社区） | InfoQ, MacRumors, Blake Crosley, maxrave.dev, 少数派, llama.cpp/MLX社区 |
| 性能数据标注"非官方基准" | ✅（明确标注来自 llama.cpp/Ollama/MLX 社区实测） |
| 文案/设计/实现三方统一 | ✅ 待实现时逐条核对 |
