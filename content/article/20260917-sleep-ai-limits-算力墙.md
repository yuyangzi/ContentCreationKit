# 24.7M 对 38.6K：睡眠 AI 的第一道墙

> **导读**：这是「sleep-ai-limits · 四道墙」的第一篇。四道墙是算力、感知、位置、标签，它们合起来把睡眠 AI 挡在了实验室门口。第一篇讲最硬的那道：在打鼾识别这类任务上，算法已经能把准确率做到 95%，却装不进一颗几十 KB 内存的微控制器。障碍来自任务结构、硬件天花板和部署路径三处，而过去六年里，绕过去的方法开始出现。

2017 年，Arm 的研究者给微控制器做了一套关键词唤醒模型，三档资源约束里最小的一档是 DS-CNN，8 位权重加激活占用 38.6 KB，测试准确率 94.4%（arXiv:1711.07128）。差不多同一年，睡眠分期领域的 DeepSleepNet 交出了 82.0% 的五分类准确率，参数量 24.7M。

这两件事在抽象层面是同一类任务：把一段时序信号切成窗口，分到有限的几个类别里。一个跑在几块钱的芯片上，另一个要一台服务器。

落差不只是 24.7M 对 38.6K。它说明了一件更麻烦的事：睡眠 AI 在论文里越做越准，在设备上却越来越放不下。

---

## 睡眠分期为什么比关键词唤醒难

这不是算法水平的问题，是任务结构的问题。

关键词唤醒处理的是一秒钟音频，类别通常只有"唤醒词"和"非唤醒词"两类。睡眠分期处理的是一整夜脑电，按美国睡眠医学会（AASM）的标准分成五类：W（清醒）、N1、N2、N3（深睡）、REM。输入长度差了三个数量级还多，类别数翻倍。

更难的是类别分布。N1 是入睡后的浅睡过渡期，在睡眠中只占个位数百分比（一项雷达睡眠研究的数据里约为 7.3%，Krauss et al., IEEE OJEMB 2026），而它恰恰是人类自己都判不准的一类：一项针对人工评分者间信度的 meta-analysis 给出，N1 的合并 κ 只有约 0.24（Lee et al., J. Clin. Sleep Med. 2022）。AASM 做过一次更大规模的评分者间一致性测试，超过 2500 名评分者对同一批片段做分期，总体与多数票的一致率 82.6%，其中 N3 是 67.4%，N1 只有 63.0%（Rosenberg & Van Hout, J. Clin. Sleep Med. 2013）。

> 天花板不在模型这边，在标注这边。自动模型要学的，是一个连人类专家都只能勉强对齐的标注。

还有一个约束：睡眠不是逐窗口独立的。NREM 和 REM 以大约 90 分钟为周期交替出现，判断某个窗口属于哪一期，上下文往往比窗口本身更重要。DeepSleepNet 用双向 LSTM 处理这个长程依赖，代价是模型膨胀到 24.7M 参数（arXiv:1703.04046；该参数量为第三方对比表口径，原论文未标注）。

长序列、五分类、外加一个占比个位数且标注噪声极大的类别，模型就会往大里长。这是结构性的，换一种架构也很难绕开。

---

## 硬件侧的天花板比想象的矮

再看设备侧。

可穿戴和睡眠监测带常用的，是 Cortex-M4/M7 这一档的微控制器（MCU）。它们的资源大致是这样：

| 芯片 | SRAM | Flash | 主频 | 备注 |
|---|---|---|---|---|
| STM32L4（Cortex-M4） | 40–320 KB | 128 KB–1 MB | 80 MHz | 动态功耗低至 28 µA/MHz |
| STM32H7（Cortex-M7） | 564 KB–1.4 MB | 64 KB–2 MB | 最高 600 MHz | |
| nRF52840（Cortex-M4F） | 256 KB | 1 MB | 64 MHz | BLE 发射峰值 4.8 mA（0 dBm） |
| ESP32-S3（双核 LX7） | 512 KB（内置） | 外接，最高 16 MB | 240 MHz | Wi-Fi 发射 283–340 mA |

（来源：各厂商官方产品页与 datasheet。STM32L4 一行覆盖 L4 系列；L4+ 属另一条产品线，内存上限更高，后文用到的 NUCLEO-L4R5ZI 是 120 MHz 的 L4+ 变体，有 640 KB SRAM / 2 MB Flash）

这些数字看着还行，一两百 KB 内存跑个小模型似乎绰绰有余。问题出在"跑个模型"之外的开销。

TensorFlow Lite for Microcontrollers（TFLite Micro，面向微控制器的推理框架）的 Hello World 示例，模型本身只有 2.5 KB，但把整个应用编译出来，要占 157 KB Flash 和 15 KB RAM；语音关键词示例的模型 20 KB，整个应用要 100 KB Flash 加 37 KB RAM（Silicon Labs 移植文档口径）。

加速库一侧的数字同类。ARM 的 CMSIS-NN（面向 Cortex-M 的神经网络加速库）在论文里报告的最好成绩是吞吐提升 4.6 倍、能效提升 4.9 倍；其 CIFAR-10 演示应用的最大内存占用约 133 KB，采用部分 im2col 省内存（否则约 332 KB）（arXiv:1801.06601）。

换句话说，一颗最低配的 STM32L4 只有 128 KB Flash，连 TFLite Micro 的 Hello World 都装不下。

再看实际能稳定跑在 MCU 上的模型是什么量级。MLPerf Tiny 是专门测边缘 AI 的基准，它的关键词唤醒参考模型就是 Hello Edge 那篇论文里的 DS-CNN：38.6K 个参数，8 位权重加激活占 38.6 KB，官方模型文件 52.5 KB。官方在 NUCLEO-L4R5ZI 参考板（Cortex-M4，标称最高 120 MHz）上实测，推理速度 5.5 次每秒，每次约 7.4 毫焦。

> 38.6K 参数的 DS-CNN，是"能稳定跑在 MCU 上"这条线的现实刻度。连它都只能做到每秒 5.5 次。

现在把这张尺子拿去量睡眠模型。DeepSleepNet 的 24.7M 参数，是这个刻度的 600 多倍。

---

## 打鼾识别：95% 的代价

睡眠 AI 里离 MCU 最近的任务是打鼾识别，因为它只需要音频，不需要电生理信号。

这一类模型的准确率已经很高。2025 年一篇发表在 Sensors 上的工作 ERBG-Net，用 ECA 注意力增强的 ResNet-18 加双向 GRU，在鼾声数据上做到 95.84% 准确率、94.82% 的 F1（DOI:10.3390/s25175483）。

背靠 ResNet-18 的代价很具体：ResNet-18 本身就有 11,689,512 个参数，单次推理 1.81 GFLOPs，FP32 权重文件约 46.8 MB（44.7 MiB，torchvision 权重实测值），加上 BiGRU 之后只会更大。就算把它量化到 8 位，权重仍有约 11.7 MB。

把它和 8 位模型文件 52.5 KB 的 DS-CNN 放在一起：**差了大约 220 倍。**

这就是那道墙的具体形状。不是没有人做出高精度模型，是高精度模型和低成本硬件之间目前还没有桥。

---

## 裂缝一：把参数砍到约 1/1850，精度反而上升

云端部署不是终点。转折在过去六年里出现。

最直接的一组对比来自睡眠分期本身。前面说过，DeepSleepNet 是 24.7M 参数，在 Sleep-EDF-20 上 κ 为 0.76（第三方对比表口径）。2026 年 2 月的一篇工作 ULW-SleepNet，把参数量压到 13,337 个，FLOPs 只有 7.89M，同一个数据集上（多模态 EEG+EOG+EMG 输入）κ 反而升到 0.82（arXiv:2602.23852，已录 ICASSP 2026）。

砍到约 1/1850 的参数量，准确率反而从 82.0% 升到 86.9%。其中一部分增益可能来自新增的 EMG 通道，而不是纯粹因为模型变小。

| 模型 | 年份 | 参数量 | 输入 | Sleep-EDF-20 | 部署 / 备注 |
|---|---|---|---|---|---|
| DeepSleepNet | 2017 | 24.7M | 单通道 EEG | 82.0% / κ 0.76 | 否 |
| TinySleepNet | 2020 | ~1.3M | 单通道 EEG | 85.4% / κ 0.80 | 否 |
| AttnSleep | 2021 | 520K | 单通道 EEG | 84.4% / κ 0.79 | 否 |
| MicroSleepNet | 2023 | 48,226 | 单通道 EEG | 82.8% / κ 0.76 | 手机端 |
| PicoSleepNet | 2025（在线） | 14.0–25.8K | 单通道 EEG | 83.5% | 本体为 SNN |
| ULW-SleepNet | 2026 | 13,337 | EEG+EOG+EMG | 86.9% / κ 0.82 | 否 |

（TinySleepNet、AttnSleep 的参数量为第三方对比表估算，精度与 κ 见原论文；DeepSleepNet 的 κ 同为第三方口径。ULW-SleepNet 为多模态输入，其余各行是单通道 EEG，跨行比较要留意输入差异）

压缩不是靠"砍到刚好不崩"，背后是几套已经成熟的方法。

- **8 位整数量化**：把乘法能耗降到浮点的约 1/20，内存占用减到 1/4，速度提升最多 7.5 倍（arXiv:2508.15008）。
- **脉冲神经网络（SNN）**：换掉密集矩阵乘法，PicoSleepNet 沿这条路线把功耗降了 1480 倍、数据量减了 6.98 倍（IEEE JBHI 30(3), 2026，DOI:10.1109/JBHI.2025.3602502）。
- **手工特征回归**：Fonseca 等人 2023 年在 Scientific Reports 上用光电容积脉搏波加加速度计做四分类，中位 κ 0.638、准确率 77.8%，算法比其团队此前基于心率变异性（HRV）特征的方法快 50 倍（DOI:10.1038/s41598-023-36444-2）。

---

## 裂缝二：换一种硬件

如果模型不肯变小，那就换掉承载它的芯片。

2025 年 2 月，一篇工作把睡眠分期的 Transformer 做成了专用芯片（ASIC），65 纳米工艺，面积 0.754 平方毫米，有效功耗 0.56 毫瓦，权重只有 31,589 个，四分类准确率 82.9%（arXiv:2502.16334）。它不追求跑在通用 MCU 上，而是把模型直接烧进硅片。

另一条路是给 MCU 加一个神经网络加速器。ETH Zürich 的 FEMBA 把脑电基础模型压到 2 位权重、约 2 MB，部署在 GAP9 这颗 RISC-V MCU 上，每 5 秒窗口推理 1.70 秒，能耗 75 毫焦（arXiv:2603.26716）。

也有只做到工艺估算的：SleepLiteCNN 把基于单导联 ECG 的睡眠模型在 8 位量化后压到每次推理 5.48 微焦，但这个数字是 45 纳米工艺下的估算，FPGA 只用来验证资源占用，不是真实流片（arXiv:2508.11664）。

芯片厂商自己也在往这个方向走。意法半导体 2024 年 12 月正式发布的 STM32N6，把 Cortex-M55 内核和一块神经网络加速器放进同一颗芯片，主频 800 MHz。有论文在同一平台上跑关键词唤醒，端到端延迟是毫秒级，在对比的几个平台里能效-延迟积（EDP）最优（arXiv:2509.07051）。MCU 这个品类本身，正在从一个纯 CPU 器件，变成一个带 NPU 的异构平台。

真正把睡眠分期模型放上通用 MCU 的公开案例，目前检索范围内只有一个。2023 年牛津团队的 MorpheusNet，把量化到 8 位的模型压到 50 KB，上传到 Arduino Nano 33 BLE（Cortex-M4），单次推理延迟 1.6 秒（IEEE SMC 2023）。1.6 秒对一个 30 秒的睡眠 epoch 来说够用。

---

## 裂缝三：把数据留在设备上

第三条路不是技术选择，是合规推着走的。

睡眠脑电属于高度敏感的健康数据，多个法域已经把它列入特殊保护：

- 欧盟 GDPR 没有把"神经数据"单独列进第 9 条特殊类别，但睡眠脑电属于健康数据，用于健康或身份识别场景时按健康/生物识别数据归入特殊类别，处理要满足明确同意等条件。
- 美国已经有 5 个州把神经数据纳入敏感数据保护，多数要求选择加入式同意；各州机制并不统一。
- 国内的《个人信息保护法》把医疗健康与生物识别数据划为敏感个人信息，处理需取得单独同意。

监管的压力方向很清楚：原始生理信号最好不要离开设备。这反而给了边缘推理一个新的理由——不是因为快，是因为合规。

一个常见的论证是"本地推理比无线传输更省电"。量级层面的结论有依据（MCU 尺度上通信能耗通常高于一次微型推理），但几份流传较广的 BLE 单包能耗数值口径不一，常被脱离发射功率、连接间隔等配置引用，甚至最常被引的那个出处研究的其实是 LoRa。**关于"传输和本地推理到底谁更省电"，公开数据目前是不完整的**，这笔账要算清楚，还得等更扎实的测量。

---

## 这道墙的现状，和它没解决的部分

把三条裂缝放在一起，方向是清楚的：算力墙正在被绕过，但绕法各不相同。压缩路线证明参数量不是瓶颈，13.3K 参数能拿到 κ 0.82；专用硬件路线证明功耗可以压到毫瓦级；合规路线把隐私变成了本地推理的推力。

不过有几点必须限定。

- **压缩后精度上升，不代表所有任务都能压缩**。ULW-SleepNet 用的是多模态输入（EEG+EOG+EMG），而打鼾识别那条线上，95.84% 的模型至今还背着一个 11.7M 参数的 ResNet-18，没有出现等价的轻量化结果。同一个领域内，压缩的可行性差别很大。
- **唯一的 MCU 案例是孤证**。MorpheusNet 1.6 秒的延迟、50 KB 的体积确实可行，但只有一个团队做出来过一次，没有第三方复现，也没有第二款产品跟进。说"睡眠分期已经能跑在 MCU 上"为时过早。
- **参数量不等于算力需求**。Mamba 类的睡眠分期模型在 2024 年之后集中出现，普遍声称比 Transformer 更高效，但大多不报 FLOPs 与能耗，参数量也只有零星几篇给出（如 MSSC-BiMamba 的 0.47M、GamSleepNet 的 30.86K），"计算效率高"多停留在定性描述。没有完整的数字，就没法判断它们离 MCU 还有多远。
- **无 EEG 路线的精度天花板还在原地**。可穿戴路线（PPG、加速度计）的 κ 普遍在 0.5 到 0.65 之间，而单通道 EEG 的轻量模型已经能做到 0.74 到 0.80；前文提到的 0.82 来自多模态 PSG（EEG+EOG+EMG）输入。把模型装进设备是一回事，装进去之后准不准是另一回事。算力墙被推倒，不意味着精度墙也跟着倒。
- **表格里的精度不能直接横向排比**。这些结果大多来自 Sleep-EDF-20 这类只有 20 段记录的经典小数据集，各论文的训练/测试划分协议也不完全一致，跨行比较要打折看。

> 算力墙的真相是：在 PSG 睡眠分期这条线上，精度已经不是瓶颈，部署才是。而部署这条路，过去六年里第一次出现了多条可走的岔路。

算力墙是四道墙里最硬的一道，也最接近被绕开：更好的芯片和更小的模型正在把它凿开。剩下三道（感知、位置、标签）不全是工程问题，它们要回答的是"到底什么才算对"。

---

*参考来源：*
- Zhang et al., "Hello Edge: Keyword Spotting on Microcontrollers," arXiv:1711.07128, 2017. [https://arxiv.org/abs/1711.07128](https://arxiv.org/abs/1711.07128)
- Supratak et al., "DeepSleepNet," IEEE TNSRE 25(11):1998-2008, 2017. arXiv:1703.04046. [https://arxiv.org/abs/1703.04046](https://arxiv.org/abs/1703.04046)
- Rosenberg & Van Hout, "The AASM inter-scorer reliability program: sleep stage scoring," J. Clin. Sleep Med. 9(1):81-87, 2013. [https://doi.org/10.5664/jcsm.2350](https://doi.org/10.5664/jcsm.2350)
- Krauss et al., "Contactless sleep staging with radar: a transfer learning approach," IEEE Open J. Eng. Med. Biol., 2026. [https://doi.org/10.1109/OJEMB.2026.3667047](https://doi.org/10.1109/OJEMB.2026.3667047)
- Lee et al., "Interrater reliability of sleep stage scoring: a meta-analysis," J. Clin. Sleep Med. 18(1):193-202, 2022. [https://doi.org/10.5664/jcsm.9538](https://doi.org/10.5664/jcsm.9538)
- Wang et al., "ULW-SleepNet," arXiv:2602.23852 (ICASSP 2026). [https://arxiv.org/abs/2602.23852](https://arxiv.org/abs/2602.23852)
- Eldele et al., "An attention-based deep learning approach for sleep stage classification," IEEE TNSRE 29:809-818, 2021. [https://doi.org/10.1109/TNSRE.2021.3076234](https://doi.org/10.1109/TNSRE.2021.3076234)
- Supratak & Guo, "TinySleepNet," EMBC 2020. [https://doi.org/10.1109/EMBC44109.2020.9176741](https://doi.org/10.1109/EMBC44109.2020.9176741)
- Liu et al., "MicroSleepNet," Front. Neurosci. 17:1218072, 2023. [https://doi.org/10.3389/fnins.2023.1218072](https://doi.org/10.3389/fnins.2023.1218072)
- Liu et al., "PicoSleepNet: An Ultra Lightweight Sleep Stage Classification by Spike Neural Network Using Single-Channel EEG Signal," IEEE JBHI 30(3):2681-2693, 2026（在线 2025）. [https://doi.org/10.1109/JBHI.2025.3602502](https://doi.org/10.1109/JBHI.2025.3602502)
- Xu et al., "Non-Contact Screening of OSAHS (ERBG-Net)," Sensors 25(17):5483, 2025. [https://doi.org/10.3390/s25175483](https://doi.org/10.3390/s25175483)
- Kavoosi et al., "MorpheusNet," IEEE SMC 2023. arXiv:2401.10284. [https://arxiv.org/abs/2401.10284](https://arxiv.org/abs/2401.10284)
- Fonseca et al., "A computationally efficient algorithm for wearable sleep staging in clinical populations," Sci. Rep. 13:9182, 2023. [https://doi.org/10.1038/s41598-023-36444-2](https://doi.org/10.1038/s41598-023-36444-2)
- "Vision Transformer Accelerator ASIC for Real-Time Low-Power Sleep Staging," arXiv:2502.16334, 2025. [https://arxiv.org/abs/2502.16334](https://arxiv.org/abs/2502.16334)
- Tegon et al., "FEMBA on the Edge: Physiologically-Aware Pre-Training, Quantization, and Deployment of a Bidirectional Mamba EEG Foundation Model on an Ultra-low Power Microcontroller," arXiv:2603.26716, 2026. [https://arxiv.org/abs/2603.26716](https://arxiv.org/abs/2603.26716)
- "Energy-Efficient Real-Time 4-Stage Sleep Classification at 10-Second Resolution"（模型名 SleepLiteCNN）, arXiv:2508.11664, 2025. [https://arxiv.org/abs/2508.11664](https://arxiv.org/abs/2508.11664)
- Abushahla et al., "Neural Network Quantization for Microcontrollers: A Comprehensive Survey of Methods, Platforms, and Applications," arXiv:2508.15008, 2025. [https://arxiv.org/abs/2508.15008](https://arxiv.org/abs/2508.15008)
- Bartoli et al., "End-to-End Efficiency in Keyword Spotting: A System-Level Approach for Embedded Microcontrollers," arXiv:2509.07051, 2025. [https://arxiv.org/abs/2509.07051](https://arxiv.org/abs/2509.07051)
- Lai et al., "CMSIS-NN: Efficient Neural Network Kernels for Arm Cortex-M CPUs," arXiv:1801.06601, 2018. [https://arxiv.org/abs/1801.06601](https://arxiv.org/abs/1801.06601)
- Banbury et al., "MLPerf Tiny Benchmark," arXiv:2106.07597, 2021. [https://arxiv.org/abs/2106.07597](https://arxiv.org/abs/2106.07597)
- MLPerf Tiny v0.5 reference results, MLCommons. [https://github.com/mlcommons/tiny_results_v0.5](https://github.com/mlcommons/tiny_results_v0.5)
- Silicon Labs, "TensorFlow Lite for Microcontrollers sample apps"（转载 TensorFlow 官方示例；Hello World 157 KB Flash / 15 KB RAM）. [https://docs.silabs.com/machine-learning/2.2.1/aiml-sample-apps](https://docs.silabs.com/machine-learning/2.2.1/aiml-sample-apps)
- STMicroelectronics STM32L4 / STM32H7 / STM32N6 产品页与 datasheet. [https://www.st.com](https://www.st.com)
- Nordic Semiconductor nRF52840 Product Specification v1.9. [https://www.nordicsemi.com](https://www.nordicsemi.com)
- Espressif ESP32-S3 Datasheet v2.2. [https://documentation.espressif.com](https://documentation.espressif.com)
- PyTorch torchvision ResNet 官方文档. [https://pytorch.org/vision/stable/models.html](https://pytorch.org/vision/stable/models.html)
- GDPR 第 9 条（特殊类别个人数据）. [https://gdpr-info.eu/art-9-gdpr/](https://gdpr-info.eu/art-9-gdpr/)
- 美国各州神经数据立法追踪（科罗拉多、加州、蒙大拿、康涅狄格、佛蒙特）, Future of Privacy Forum. [https://fpf.org/wp-content/uploads/2025/08/Neural-Data-State-Tracker-Chart.pdf](https://fpf.org/wp-content/uploads/2025/08/Neural-Data-State-Tracker-Chart.pdf)
- 《中华人民共和国个人信息保护法》第 28、29 条. [https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm](https://www.cac.gov.cn/2021-08/20/c_1631050028355286.htm)
