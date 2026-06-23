# PPT文案：苹果在 AI 时代的真正护城河 — 低调的 Core AI

> 来源文章：content/article/20260623-Apple-Core-AI框架深度解读-设备端大模型时代来临.md
> 生成日期：2026-06-23
> 幻灯片预估：30-35 张

---

## 核心论点

苹果在 WWDC 2026 上发布了 Core AI 框架，作为设备端大模型推理的新基座。这不是单纯的技术升级，而是一套延续苹果"垂直整合"战略的基础设施布局：消费端开放合作（Gemini 知识蒸馏），基础架构端垂直自研（Core AI + Apple Silicon 深度耦合）。开发者多了一个框架，但这个框架直接决定了未来十年 AI App 在苹果设备上的性能和迁移成本。

---

## 故事线（6 章）

### 第一章：WWDC 2026 的双层叙事

**核心**：苹果将 AI 叙事劈成两层——消费者看得到的（Siri AI）和开发者绕不开的（Core AI），后者低调到只在主题演讲给了几分钟。

**幻灯片规划**：

| # | 幻灯片内容 | 数据类型 | 建议布局 |
|---|-----------|----------|---------|
| 1 | 封面：Apple Core AI | 标题 | cover |
| 2 | WWDC 2026 的两层叙事 | 引子 | quote |
| 3 | 消费者层：Siri AI 升级（Gemini 蒸馏、Foundation Models、Liquid Glass） | 列表 | default |
| 4 | 开发者层：Core AI 框架发布 | 列表 | default |

**数据点**：
- WWDC 2026 日期：6 月 8 日
- Session 325/326 为核心技术内容

---

### 第二章：双轨 AI 战略 — 开放合作 × 垂直自研

**核心**：苹果在消费者端靠合作补齐模型能力（Gemini 蒸馏 → Foundation Models），在开发者端垂直自研（Core AI + Apple Silicon），建了一条别人无法复制的护城河。

**幻灯片规划**：

| # | 幻灯片内容 | 数据类型 | 建议布局 |
|---|-----------|----------|---------|
| 5 | 章节：双轨 AI 战略 | 章节标题 | section |
| 6 | Federighi 的澄清："我们使用 Google Assistant 数量为零" | 引用 | quote |
| 7 | 消费端：合作补齐——利用 Gemini/Claude 前沿模型做知识蒸馏 | 列表 | default |
| 8 | 开发者端：垂直自研——Core AI 深耦合 Apple Silicon | 列表 | comparison |
| 9 | 历史的重演：WebKit (iOS 唯一)、Metal (GPU 原生入口) | 类比 | default |

**数据点**：
- 来源：Federighi 主题演讲第二天表态（Apple Newsroom）
- Gemini 为当前首选蒸馏源，ChatGPT、Claude 在备选名单

---

### 第三章：Core AI 技术深潜

**核心**：Core AI 的设计思路——让训练好的模型变成原生二进制产物，像编译 App Extension 一样。关键在 AOT 编译（设备端零 JIT 卡顿），以及 Apple Silicon 的底层加速。

**幻灯片规划**：

| # | 幻灯片内容 | 数据类型 | 建议布局 |
|---|-----------|----------|---------|
| 10 | 章节：Core AI 技术深潜 | 章节标题 | section |
| 11 | 一句话核心：模型 → 原生二进制 | 陈述 | statement |
| 12 | 三步流程：PyTorch → `.aimodel` → `xcrun coreai-build` → `.aimodelc` | 流程 | default + NcSteps/Mermaid |
| 13 | AOT 编译：延迟在开发端吃掉，设备端零 JIT | 对比 | comparison |
| 14 | Metal 4 自定义内核 + `TorchMetalKernel` | 技术亮点 | default + NcTerminal |
| 15 | 统一内存架构：CPU/GPU/ANE 共享内存池 | 架构 | diagram |
| 16 | Swift 三概念：AIModel + InferenceFunction + NDArray | API | default |
| 17 | API 一致性：3B 视觉模型到 70B 推理模型同一套调用 | 非技术洞察 | quote |

**数据点**：
- PyTorch → `torch.export.export()` → `coreai_torch.TorchConverter()` → `save_asset()` → `.aimodel`
- `xcrun coreai-build --platform iOS` → `.aimodelc`
- `ComputeUnitKind` 枚举：CPU / GPU / Neural Engine / 默认全给
- Metal 4 随 macOS Tahoe (2025) 发布
- Swift API：`AIModel` / `InferenceFunction(fileNamed:)` / `NDArray`
- 来源：Apple Developer Session 325/326、Core AI 官方文档

---

### 第四章：70B 本地运行的现实边界

**核心**：70B 大模型确实能在苹果设备上跑，但"苹果设备"不等于"iPhone"——70B Q4 量化后约 40-46GB 内存占用，只有 M4/M3 Max 64GB+ 和 M2 Ultra 工作站级别 Mac 才跑得动。

**幻灯片规划**：

| # | 幻灯片内容 | 数据类型 | 建议布局 |
|---|-----------|----------|---------|
| 18 | 章节：70B 本地运行的真实边界 | 章节标题 | section |
| 19 | 70B Q4 内存占用 ~40-46GB（权重 + KV Cache + 运行时） | 关键数字 | metrics |
| 20 | 设备分级金字塔：iPhone / iPad Pro / Mac 工作站 | 分级 | diagram |
| 21 | 性能基准：7B/13B/70B 在 M4 Max/M2 Ultra 上的 tok/s | 数值对比 | default + NcBarChart |
| 22 | 12-18 tok/s 意味着什么？聊天的可用对话体验 | 定性说明 | default |
| 23 | 混合精度推理：FP16 / INT8 / INT4 自动选择 | 技术点 | default |

**数据点**：
- 70B + Q4 量化后内存占用：~40-46 GB
- iPhone 物理上限：12 GB
- iPad Pro (64GB max)：理论上可行
- M4 Max 64GB+ / M3 Max 64GB+ / M2 Ultra 192GB：可行
- 7B Q4 on M4 Max：~87 tok/s (MLX)，50-60 tok/s (llama.cpp)
- 13B Q4 on M4 Max：~38 tok/s
- 70B Q4 on M3 Max/M4 Max：12-18 tok/s
- 70B Q4 on M2 Ultra (800 GB/s)：14-18 tok/s
- 来源：llama.cpp / Ollama / MLX 社区实测数据（框架发布仅15天，官方基准尚未发布）

---

### 第五章：Core ML 的九年与三层框架分工

**核心**：Core ML 从 2017 到 2026 经历了六次大版本，最终在推理层面被 Core AI 取代。新体系下 Core ML 退守经典 ML、Core AI 主攻神经网络、MLX 面向研究——苹果选择的不是"合并"而是"分层"。

**幻灯片规划**：

| # | 幻灯片内容 | 数据类型 | 建议布局 |
|---|-----------|----------|---------|
| 24 | 章节：Core ML 的九年与三层框架 | 章节标题 | section |
| 25 | Core ML 进化时间线：2017-2026 | 时间线 | default + NcSteps |
| 26 | 新三框架分工：Core ML / Core AI / MLX | 对比 | comparison |
| 27 | 分层优于合并——车间类比 | 洞察 | quote |

**数据点**：
- 2017：Core ML + iOS 11 发布
- 2018 Core ML 2：模型量化，体积缩小 75%
- 2019 Core ML 3：开放 ANE，支持设备端训练
- 2021 ML Program 格式：MLShapedArray, .mlpackage
- 2023 MLX 发布（独立开源，面向研究）
- 2025 Foundation Models 框架（仅供苹果自用）
- 2026 Core AI 发布
- 来源：Apple Developer 官方文档、InfoQ 报道

---

### 第六章：生态锁定的底层逻辑

**核心**：苹果的竞争哲学从来不是"提供更多选项"，而是"让离开的成本趋近于无穷大"——芯片-框架-分发的铁三角。Core AI 延续这一逻辑，但变量比以往任何时候都多（Google AI Edge SDK、高通 NPU）。

**幻灯片规划**：

| # | 幻灯片内容 | 数据类型 | 建议布局 |
|---|-----------|----------|---------|
| 28 | 章节：生态锁定的底层逻辑 | 章节标题 | section |
| 29 | 苹果铁三角：芯片 × 框架 × 分发 | 架构 | diagram |
| 30 | 不是围墙花园，是地基花园 | 核心洞察 | spotlight |
| 31 | 竞争变量：Google AI Edge SDK / 高通 Snapdragon NPU | 对比 | comparison |
| 32 | 时序问题：为什么 Core AI 现在开放？ | 分析 | default |
| 33 | 终局：几十万个 App 的 AI 集成能力，入口不再是 Siri 对话框 | 展望 | statement |

**数据点**：
- 来源：InfoQ、MacRumors、Apple Newsroom
- App Store 分发权、Swift 语言锁定、Metal 图形垄断的先例
- 竞争变量：Google AI Edge SDK (Android)、高通 Snapdragon NPU

---

## 数据来源（完整列表）

| # | 来源 | 类型 | 用途 |
|---|------|------|------|
| 1 | [InfoQ：Apple Launches Core AI](https://www.infoq.com/news/2026/06/apple-core-ai-wwdc/) | 二手（媒体） | Core AI 发布细节、框架概述 |
| 2 | [Apple Developer：WWDC 2026 Session 325/326](https://developer.apple.com/videos/play/wwdc2026/324/) | 一手（官方） | 技术细节、AOT 编译流程、API 设计 |
| 3 | [Apple Developer：Core AI 官方文档](https://developer.apple.com/documentation/coreai/) | 一手（官方） | API 参考、ComputeUnitKind |
| 4 | [Blake Crosley：Core AI - Run Models on Apple Silicon](https://blakecrosley.com/blog/core-ai-run-models-apple-silicon) | 二手（开发者） | 实操体验、性能推测 |
| 5 | [maxrave.dev：Core AI 分析](https://maxrave.dev/articles/coreai-models-makes-apples-on-device-ai-stack-feel-more-buildable-for-real-app-teams) | 二手（开发者） | 开发者视角分析 |
| 6 | [MacRumors：Apple AI and Developer Tool Updates](https://www.macrumors.com/2026/06/09/apple-outlines-major-ai-and-developer-tool-updates) | 二手（媒体） | 发布会新闻汇总 |
| 7 | [Apple Newsroom：WWDC 2026 发布](https://www.apple.com/newsroom/2026/06/apple-unveils-next-generation-of-apple-intelligence-siri-ai-and-more/) | 一手（官方） | Siri AI、双轨战略 |
| 8 | 少数派：WWDC 2026 发布会回顾、iOS 27 具透 | 二手（中文媒体） | 中文社区解读 |
| 9 | llama.cpp / Ollama / MLX 社区实测数据 | 一手（社区） | 性能基准数据（非 Core AI 官方） |

**数据准确声明**：性能数据（7B/13B/70B tok/s）来自 llama.cpp、Ollama 和 MLX 框架在相同 Apple Silicon 芯片上的实测，非 Core AI 官方基准。Core AI 发布仅 15 天，尚未发布官方性能数据。

---

## 附录：金句与关键引用

1. "苹果在 AI 时代的真正护城河——不是模型产不产得出，而是产出的模型能不能在自家硬件上跑到最优"
2. "让开发者把训练好的模型变成一个苹果设备上的原生二进制产物，就像编译一个 App extension 一样"
3. "你不一定非要用 Core AI，但它是唯一能在 Apple Silicon 上跑到最优的那一个"
4. "芯片-框架-分发"的铁三角
5. "不是围墙花园，是地基花园：你可以在花园里种任何东西，但土是苹果的"
6. "苹果几乎从不在'提供选项'上竞争，它在'选项越少越好'上构建优势"
7. "当几十万个 App 的 AI 集成能力成为日常，没人在乎模型是蒸馏了 Gemini 还是 ChatGPT"
8. "3B 参数的视觉模型到 70B 参数的推理模型，Swift 层调用方式一样——API 一致性本身就是维护成本"
