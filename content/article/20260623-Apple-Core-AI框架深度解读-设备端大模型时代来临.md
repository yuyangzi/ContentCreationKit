# 苹果的双轨 AI 战略：当所有人盯着 Siri，真正的变化发生在开发者工具链上

> **导读**：WWDC 2026 上，苹果发布了一个新框架叫 Core AI，正式承接了运行九年的 Core ML。它在主题演讲里几乎只字未提，核心内容藏在 Platforms State of the Union 和开发者 session 里。但如果你关注的是苹果在 AI 时代的真正护城河——不是模型产不产得出，而是产出的模型能不能在自家硬件上跑到最优——那这场发布会最值得看的就是这个东西。

6 月 8 日的 WWDC 主题演讲，苹果用一种相当刻意的方式把自己的 AI 叙事劈成了两层。

第一层，消费者看得到的：Siri AI 全面升级，基于 Gemini 技术蒸馏训练出的自研 Foundation Models，iOS 27 的 Liquid Glass 设计语言。媒体狂欢的素材全在这一层。CNET 说这是"Siri 十年来最大升级"，The Verge 称苹果"终于追上了 AI 助手赛道"。

第二层，消费者看不到但开发者绕不开的：Core AI，一个全新的设备端推理框架，承接 Core ML 在神经网络推理领域的位置，成为苹果 AI 基础设施的新基座。这一层在主题演讲里只给了几分钟，核心内容藏在 Platforms State of the Union 和两场编号 325/326 的开发者 session 里。

苹果不是忘了宣传。它是故意的。

如果 Core AI 出现在通稿里，注意力会被分散；如果它完全不出现，开发者会炸锅。所以发布会当天它存在了，但只以最低调的方式——刚好够让应该知道的人知道。

---

## 双轨 AI 战略：开放合作与垂直自研的并行逻辑

把 Siri AI 和 Core AI 放在一起看，才能理解苹果在 AI 上的真实布局。

Siri AI 的技术路线，说到底是"用自己的硬件跑别人的模型能力"。Federighi 在主题演讲第二天特意澄清了一句："我们使用的 Google Assistant 数量为零。"这听起来像撇清关系，但实质更值得玩味——苹果不是把 Gemini 模型嵌进系统，而是用 Gemini 前沿模型的输出做知识蒸馏，训练出为 Apple Silicon 定制的 Foundation Models。

这件事的意义不在技术上有多高明，而在战略上有多清醒：苹果在消费者端的 AI 能力，可以靠合作补齐。谁家模型强就用谁家的来蒸馏，Gemini 现在是首选，ChatGPT 和 Claude 也在备选名单里。消费者不在乎底层模型是谁，他们在乎 Siri 能不能听懂话。

但开发者端不行。

开发者端的 AI 基础设施如果也依赖第三方，那苹果整个生态的护城河就没了。你的 App 里的 AI 能力是跑在苹果框架上还是跑在别人的 SDK 上，决定了这些 App 在未来五年里迁移到其他平台的成本。Core AI 的价值不在于它能做什么，在于**只有它能做**：第三方框架在苹果设备上在可预见的范围内跑不出同一套硬件上的最优效率，因为没有人比苹果更了解自己的芯片。

这就是双轨 AI 战略的本质：消费端开放合作，补上模型能力的短板；基础架构端垂直自研，建一个别人无法复制的护城河。

坦白说，这种策略在苹果历史上反复出现。Safari 的浏览器引擎从来不是最快的，但 WebKit 在 iOS 上只有一个。Metal 的图形 API 不是行业标准，但它是唯一能直接调用 Apple GPU 原生指令的入口。Core AI 在做同一件事。它不一定是设备端推理框架里功能最全的那个，但它会和 Apple Silicon 的耦合最深。

---

## Core AI 到底做了什么？

这件事需要从技术层面讲清楚，否则很容易把它理解成"又一个模型部署框架"。

Core AI 的核心设计思路可以用一句话概括：**让开发者把训练好的模型变成一个苹果设备上的原生二进制产物，就像编译一个 App extension 一样。**

整个过程分两步。第一步是转换：开发者在自己的 Mac 上，把 PyTorch 模型通过 `torch.export.export()` 导出，再经由 `coreai_torch.TorchConverter()` 这个 Python API 转成 Core AI 的中间表示，最后调用 `save_asset()` 存为一个 `.aimodel` 文件。听起来就是几个命令行的事。

第二步才是关键，AOT（Ahead-of-Time）编译。开发者用 `xcrun coreai-build` 命令行工具，指定目标平台（`--platform iOS` 或 `--platform macOS`），把这个 `.aimodel` 文件提前编译为 `.aimodelc`。编译过程包含 segment、plan、optimize compute 这些最耗时的步骤，全部在开发者的 Mac 上完成。产出的 `.aimodelc` 文件打包进 App，用户下载安装后，设备端只需要做一层很薄的 device-specific specialization（把编译结果绑定到具体的芯片型号和 OS 版本）。

这个设计在移动端推理框架里是不多见的。大部分框架的编译发生在设备端：用户打开 App，第一次用到 AI 功能的时候，框架开始做 JIT 编译，卡个三五秒。苹果把这个延迟直接吃掉，让开发者在发布前就把锅甩完了。

这还没算 Apple Silicon 的底层加速。Core AI 预置了一套针对 Transformer 架构深度优化后的算子，包括 Scaled Dot Product Attention 等注意力机制的常见实现。同时 Metal 4（2025 年随 macOS Tahoe 发布）开放了自定义 GPU 内核能力，开发者可以通过 `TorchMetalKernel` 编写自己的算子，这在 Core ML 时代是完全不可能的。

硬件调度上，`ComputeUnitKind` 枚举给了三种选择：跑在 CPU 上、跑在 GPU 上、跑在 Neural Engine 上，默认是全给。框架自动根据当前负载和芯片状况决定哪些算子放哪块计算单元。这背后是苹果独有的统一内存架构在兜底：CPU、GPU、ANE 共享同一个内存池，数据不需要来回搬运。

---

## Swift 侧的能力暴露

对习惯了 Swift 的 iOS 开发者来说，Core AI 的 API 设计相当克制。核心就三个概念：

`AIModel` 加载编译好的模型文件；`InferenceFunction` 执行推理；`NDArray` 管理多维张量输入输出。KV Cache 的状态管理直接暴露在 API 层面：如果你要跑一个有状态的多轮对话模型，不需要自己维护缓存结构。

这里有一个容易被忽略的细节：Core AI 的 Swift 接口默认不区分模型架构类型。不管底层跑的是 3B 参数的视觉模型还是 70B 参数的推理模型，Swift 层的调用方式是一样的。这对生产级 App 的工程意义远大于技术炫技——做架构抽象的人都知道，API 一致性本身就是在降低维护成本。

---

## 70B 参数跑在本地：这件事的真实边界

但有必要说清楚一件事，也是一些报道含糊其辞的地方。

70B 参数的大语言模型确实可以在苹果设备上跑，但"苹果设备"不等于"iPhone"。70B 模型在 Q4 量化下，实际内存占用大约 40 到 46 GB，这包括了模型权重、KV Cache 和运行时开销。意味着能跑这个规模的设备仅限于 M4 Max 64GB 以上、M3 Max 64GB 以上，或者 M2 Ultra 192GB 这些工作站级别的 Mac。iPad Pro 如果配置拉满 64GB 内存，理论上也在可行区间。

iPhone 的物理上限是 12GB 内存，在实际应用中跑 3B 到 7B 参数的模型已经触及天花板。

性能方面，Core AI 官方还没有发布任何基准数据——框架发布到现在才 15 天。但可以参考的是同一批 Apple Silicon 芯片在 llama.cpp、Ollama 和 MLX 上的实测数据：7B Q4 在 M4 Max 上约 87 tokens/秒（MLX 框架，llama.cpp 约 50-60），13B Q4 约 38，而 70B Q4 在 M3 Max/M4 Max 上大约 12 到 18 tokens/秒。M2 Ultra 192GB 在同样 70B Q4 上因更高的内存带宽（800 GB/s）反而更快，约 14 到 18 tokens/秒。

这些数字说明了两件事：一，大模型在苹果设备上确实跑得动，不是营销噱头；二，生成速度离"实时流畅对话"还有一段路。12 到 18 tokens/秒意味着用户问一句话，要等好几秒才看到完整回复。在聊天场景里这不是大问题，但对需要流式输出的交互类型来说，体验会打折。

苹果自己清楚这个 trade-off。在开发者 session 里，他们花了不少篇幅讲混合精度推理，框架会根据当前设备的芯片能力，在 FP16、INT8、INT4 之间自动选择精度。重点不是跑多快，而是"跑得起来"本身就是一个信号：苹果在告诉开发者，你别再等云端 API 了，先把模型搬下来再说。

---

## Core ML 的九年

Core AI 与 Core ML 的关系必须讲清。这不只是一个旧框架的谢幕。

Core ML 2017 年随 iOS 11 首次发布时，移动端机器学习还是个很"小"的命题。让手机识别图片里的猫，用到的模型参数量以百万计。所以 Core ML 的设计哲学天然偏向"传统机器学习模型"——决策树、SVM、表格特征工程。ANE（Apple Neural Engine）在 A11 芯片上已经有了，但当时不对开发者开放。

之后八年多的时间里，Core ML 经历了至少六次大版本迭代：

- **2018 — Core ML 2**：模型量化，体积缩小 75%
- **2019 — Core ML 3**：首次开放 ANE 作为计算目标，支持设备端训练
- **2021 — ML Program 格式**：`MLShapedArray` 和 `.mlpackage` 登场，底层架构从静态图走向动态图
- **2023 — MLX 发布**：苹果 ML 研究团队独立发布开源 Apple Silicon 原生数组框架，专为 LLM 训练和微调设计。这不是 Core ML 的分叉，而是一条完全独立的技术路线，目标受众是研究人员而非 App 开发者
- **2025 — Foundation Models 框架**：为 Apple Intelligence 提供设备端模型 API，但仅供苹果自己使用

到这时，开发者在苹果生态里做 ML 已经是三框架并行：Core ML 负责经典模型，Foundation Models 框架负责苹果自有的设备端模型，MLX 给研究员玩。每个都解决一部分问题，但没有人能用一个框架搞定所有事。

Core AI 在 2026 年的出现，本质上是把这些分散的路径在推理层面统一了起来。但苹果没有选择"合并"——他们选择了分层。

---

## 三层框架的必然分工

新的架构体系下，三个框架各退一步明确了边界：

**Core ML** 退守经典机器学习——决策树、表格特征工程、传统分类器。苹果官方确认 Core ML 进入维护模式，不再添加新功能，但存量模型通过兼容层继续可用。推荐做法是把模型重新编译为 Core AI 格式以获得现代硬件的性能。

**Core AI** 主攻神经网络和 Transformer 架构——大语言模型、视觉模型、推理模型。这是现在和未来十年 App 里 AI 能力的主力框架。

**MLX** 继续独立在苹果机器学习研究团队手里，面向研究人员做自定义权重的训练和微调。不走生产部署路线，也不走 Core AI 的统一推理路线。

这个分工比"统一框架"的叙事更值得注意。苹果在做的事不是把摊子收拢，而是让不同阶段的任务各自有最合适的工具——就像一个汽车工厂不会让焊装车间和涂装车间用同一套设备。对开发者来说，框架之间的边界清楚了，选型就不需要纠结。但对苹果来说，这个三件套意味着任何人想在苹果设备上用第三方框架复制出同样的性能组合都极难，因为你离硅芯片越近的优化，越只能靠苹果自己提供的这套东西。

---

## 开发者圈子的真实反应

框架发布只有两周，开发者社区的反馈还处于早期阶段，但已经能看出几条线。

积极的一面是共识：PyTorch 模型的转换流程比 Core ML 时代简化了不止一个数量级。InfoQ 报道里引述开发者原话，"让高性能 LLM 更容易接入"。零 token 成本的本地推理，没有 API 调用费，没有延迟，这个卖点对做数据敏感类 App 的团队确实有吸引力。

疑虑也集中在几个关键点上。最突出的是缺乏官方性能基准：框架发布了，但苹果没有提供任何跑分数据，开发者只能靠第三方在 llama.cpp 和 MLX 上的实测去推测 Core AI 的性能表现。其次，三层框架的边界在文档里写清楚了，但在实际开发中哪些该用 Core ML、哪些该用 Core AI，新入门的开发者需要一段学习曲线。还有一个时间窗口的压力：iOS 27 秋季发布，从 WWDC 到正式版上线只有大约十周，对于计划集成 Core AI 的团队来说，时间不宽裕。

最被提到的一点是区域限制。Siri AI（基于 Gemini 的新版 Siri）在中国大陆全平台不可用，在欧盟则因 DMA 限制不会登陆 iOS/iPadOS 27，但 macOS 27 不受影响——Apple Intelligence 本身自 2025 年 4 月起已在欧盟可用。这意味着依赖 Foundation Models 框架提供设备端模型 API 的应用在中国市场会受影响。Core AI 框架本身的区域限制目前没有明确的官方声明，但在 EU 的 Digital Markets Act 框架下，开发者社区已经在讨论 region-based feature flags 的必要性。

---

## 生态锁定的底层逻辑

把所有这些技术细节拼在一起，苹果的真正意图其实很清楚。

不是做最强的模型。不是做最全的框架。是让开发者在苹果设备上构建 AI 功能的时候，**除了 Core AI 没有更好的选择**。

这套逻辑在过去十五年里被验证了太多次。App Store 的分发权、Swift 的语言锁定、Metal 的图形垄断——苹果几乎从不在"提供选项"上竞争，它在"选项越少越好"上构建优势。Core AI 延续了同一套剧本：框架免费、性能顶级、迁移成本趋近于零，前提是你留在苹果生态里。

但这一次，竞争变量比以往任何时候都多。Google 的 AI Edge SDK 在 Android 上也有设备端推理能力，高通 Snapdragon 的 NPU 算力在纸面上不输 Apple Silicon 的 ANE。苹果的优势不在任何一个单项上，而是在"芯片-框架-分发"这个铁三角的耦合深度上。这种耦合是开源框架和第三方芯片厂商短期内难以企及的。

问题在于，耦合越深，生态就越封闭。当一个 App 的 AI 核心能力深度依赖 Core AI 的 AOT 编译和 Metal 4 自定义内核时，把它移植到 Android 上就不仅仅是重写框架调用的问题——整个推理栈需要重新设计。这意味着苹果在 AI 时代建的不是"围墙花园"，而是"地基花园"：你可以在花园里种任何东西，但土是苹果的。

---

## 一个开放的问题

Core AI 发布两周后，这件事最值得关注的不是技术细节本身，而是一个时序问题：苹果选择了在 Apple Intelligence 上线一年后、Siri AI 接入 Gemini 蒸馏能力的同时，把设备端推理框架向全体开发者开放。

这个时序不是偶然的。

消费者侧的 AI 体验——Siri 对话、图像生成、智能摘要——苹果已经用合作模式跑通了。下一个阶段需要的不再是更好的 AI 助手，而是更多 App 把 AI 当做默认能力而非附加功能。当健康 App 在本地分析你的心电图数据不需要上云、当笔记 App 在你的 Mac 上脱机生成摘要、当相机 App 实时翻译路牌上的文字——当这些成为日常，苹果生态的 AI 入口就不再是 Siri 一个对话框，而是几十万个 App 的集成能力。

那时候，没人在乎模型是蒸馏了 Gemini 还是 ChatGPT。用户只知道"在 iPhone 上这些事都能做"。而这个体验的基石，是 Core AI。

*参考来源：*
- InfoQ：Apple Launches Core AI for Apple-Silicon Optimized On-Device Generative AI：[https://www.infoq.com/news/2026/06/apple-core-ai-wwdc/](https://www.infoq.com/news/2026/06/apple-core-ai-wwdc/)
- Apple Developer：WWDC 2026 - Core AI 介绍（Session 325/326）：[https://developer.apple.com/videos/play/wwdc2026/324/](https://developer.apple.com/videos/play/wwdc2026/324/)
- Apple Developer：Core AI 官方文档：[https://developer.apple.com/documentation/coreai/](https://developer.apple.com/documentation/coreai/)
- Blake Crosley：Core AI - Run Models on Apple Silicon：[https://blakecrosley.com/blog/core-ai-run-models-apple-silicon](https://blakecrosley.com/blog/core-ai-run-models-apple-silicon)
- maxrave.dev：Core AI Models Makes Apple's On-Device AI Stack Feel More Buildable：[https://maxrave.dev/articles/coreai-models-makes-apples-on-device-ai-stack-feel-more-buildable-for-real-app-teams](https://maxrave.dev/articles/coreai-models-makes-apples-on-device-ai-stack-feel-more-buildable-for-real-app-teams)
- MacRumors：Apple Outlines Major AI and Developer Tool Updates：[https://www.macrumors.com/2026/06/09/apple-outlines-major-ai-and-developer-tool-updates](https://www.macrumors.com/2026/06/09/apple-outlines-major-ai-and-developer-tool-updates)
- Apple Newsroom：Apple unveils next generation of Apple Intelligence, Siri AI, and more：[https://www.apple.com/newsroom/2026/06/apple-unveils-next-generation-of-apple-intelligence-siri-ai-and-more/](https://www.apple.com/newsroom/2026/06/apple-unveils-next-generation-of-apple-intelligence-siri-ai-and-more/)
- 少数派：WWDC 2026 发布会回顾、iOS 27 具透
