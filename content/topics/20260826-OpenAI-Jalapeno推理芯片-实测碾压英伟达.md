# OpenAI 首颗推理芯片 Jalapeño：实测数据碾压英伟达

## 主题名称
OpenAI 自研推理芯片「Jalapeño」Hot Chips 实测成绩单：每瓦性能反超 GB200/GB300

## 热度背景分析

2026 年 8 月 25 日（Hot Chips 大会）、OpenAI 官方博客《OpenAI and Broadcom unveil LLM-optimized inference chip》公布了首颗自研推理芯片 **Jalapeño** 的首批实测成绩，中英文媒体同步爆发：

- **官方口径**：OpenAI CEO Sam Altman 在 X 上表态「我们造了一颗芯片，速度很快」；总裁 Greg Brockman、硬件负责人 Richard Ho 均公开背书。
- **独立验证**：SemiAnalysis 研究员 Dylan Patel 进入 OpenAI 实验室实测，结论「Jalapeño 把我们此前测过的每一颗英伟达、AMD、谷歌芯片全干趴下了」。
- **媒体覆盖**：TechCrunch、The Verge、Bloomberg、Tom's Hardware、The Register、The Decoder 全球报道；中文侧新智元、机器之心（经 36氪）深度拆解。
- **传播度**：36氪两篇合计阅读 2.4 万+，Dylan Patel 断言「被掀翻的不只是 Blackwell，连 Rubin 也被超越」，网友戏称「墨西哥辣椒」命名引发热议。

**选题价值**：这是「大模型公司自研芯片」从口号到**实测数据拐点**的一篇。此前 7 月已有「大模型公司集体背叛英伟达」的宏观论述，但那是经济账/战略账；本篇聚焦**实测基准数字**——用第三方基准（InferenceX）把英伟达 GB200/GB300 拉下马的硬数据，是对 AGENTS.md 已覆盖「背叛英伟达」主题的**数据级续写**，不重复。

## 核心事实与数据（已交叉验证）

### 芯片与定位
- **Jalapeño**（墨西哥辣椒），OpenAI 首颗「Intelligence Processor」，为 LLM 推理（非训练）而生，专攻模型上线后的运行阶段。
- 与 **Broadcom**（博通）深度合作，Hock Tan/Charlie Kawwas 交付给 Altman/Brockman；合作方另有 Celestica（板卡/机架整合）、Tomahawk 网络芯片。
- **额定功耗 700W**，实际测试工作负载持续功耗 ≤ 550W；GB300 为 1400W。
- 主计算 die 约 840mm²，EUV 光刻机掩模版极限 858mm²，逼近物理天花板。
- 从设计到 Tape-out（流片）仅 **9 个月**（业内常见 18–36 个月）。

### 实测基准（SemiAnalysis 的 InferenceX 基准）
测试模型：GPT-OSS 120B、DeepSeek R1 670B、Kimi K2.5 1T（覆盖中型到万亿参数 MoE，且含外部模型，证明非自家模型专属优化）。

- **每瓦 AI 工作量**：峰值提升 **1.5–1.9×**（三个模型分别 1.9×、1.7×、1.5×）
- **端到端延迟**：降至对比系统的 **1/1.7–1/3.6**
- **高度交互式工作负载**：性能提升 **2.1–4.1×**
- **GPT-OSS 120B** 上：1459 token/s（两 token 间隔 0.69ms），GB200 仅 535 token/s
- **1.65 秒 vs 5.99 秒** 完成任务（Jalapeño vs GB300）
- **Kimi K2.5 1T**：单用户解码速度提高时，每瓦吞吐优势从峰值 1.5× 扩大到最高 **56.1×**
- **DeepSeek R1 670B**：对比系统最佳 TBT 条件下，Jalapeño 每千瓦 12,258 mixed TPS/kW，对比 GB300 的 118，约 **104.3×**
- SemiAnalysis 全口径（供电/散热/网络摊到每芯片）：Jalapeño 每颗 1.125kW，GB200 1.87kW，Vera Rubin 3.3kW；每兆瓦每秒吐 token：Jalapeño ~5300 万 vs GB200 NVL72 ~1000 万
- **每芯片每小时 TCO**：Jalapeño 1.56 美元 vs H100 1.55 美元 vs Vera Rubin 3.61 美元
- 注：Jalapeño 成绩未开投机解码/Token 预测/prefill-decode 分离，而对比芯片跑的都是各自最优配置。SemiAnalysis 估算仅投机解码一项即可再降每 Token 成本 2/3 以上。

### 架构卖点
- 专为 **Agent 工作负载**设计：Prefill 重算力、Decode 重内存带宽，KV Cache 等模型状态可显式放置并保持在本地，同一架构同时优化吞吐与延迟。
- 每瓦 HBM 带宽 22 vs Rubin 11.1 vs GB300 5.71；每瓦 FLOPs 19.1 vs Rubin 19.4（但 Rubin 要烧 1800W+，Jalapeño 仅 700W）。
- B0 步进已在晶圆厂，每瓦性能比 A0 再高约 25%。

### AI 设计芯片的飞轮
- 官方口径：协助开发的是 **GPT-5.3-Codex-Spark**（OpenAI 官方博客原文）。
- 中文报道（机器之心/新智元）称「GPT-Astra（外界所称 GPT-6）」协助——**两处口径不一致，写文章时需以官方博客为准，避免来源归属错误**。
- 新智元：AI 辅助设计使 SIMD 单元面积减 8%、矩阵引擎面积减 10%；Codex 两个月内把三款本不在计划内的开放权重模型爆改到高性能；Attention/MoE 模块 AI 手写实现比人类顶尖专家快 1.5–1.8×。

### 部署与路线图
- 2026 年底开始小批量部署到自有算力（TechCrunch 口径「very small volumes」），2027 年显著放量。
- **Gen 2** 深度开发中，**Gen 3** 成形中；与 Broadcom 2025 年 10 月签了 **10GW 定制加速器**合作（约十座核电机组满发）。
- 效率三档位：Ultra-fast / Fast / Batch。
- OpenAI 明确表示**不摆脱英伟达**，仍将继续大规模部署 NVIDIA 和其他伙伴加速器。
- 同日爆出：数据中心大总管、负责「星际之门」Stargate 的 Chris Malone 离职（新智元报道）——IPO 临近背景下的人事暗流。

## 类型标签
- 产业与商业分析（自研芯片 / 算力成本）
- 模型技术拆解（推理芯片架构）
- AI 基础设施 / 算力经济学

## 创作方向建议

### 方向 A：实测数据碾压（推荐，强新闻属性）
以「OpenAI 第一次做芯片，就把英伟达全系干趴下」为钩子，逐项拆解 InferenceX 实测数字（每瓦 1.5–1.9×、延迟 1/3.6、104.3× TCO 对比），回答「为什么这次不一样」——因为这次有第三方实测硬数据，而非 PPT。

### 方向 B：AI 设计芯片的飞轮（技术深读）
聚焦「模型 → 芯片 → 软件」闭合飞轮：9 个月流片、AI 辅助电路设计、Codex 爆改开放模型。这是对 AGENTS.md「Agent 工程」与「DeepSeek 推理芯片」系列的延伸，讨论软件定义硬件的极限。

### 方向 C：CUDA 护城河之死（战略评论）
SemiAnalysis 的核心判断「CUDA 护城河可能已死」——不是英伟达硬件不行，而是软件起步速度。对比英伟达 Rubin 早一个月流片却无第三方实测。可串联「大模型公司背叛英伟达」主线。

### 方向 D：Agent 经济学（另辟蹊径）
从「Jalapeño 为 Agent 而生」切入：Agent 任务多步延迟累积，每瓦有用的 AI 工作才是关键指标——把芯片话题引向「Agent 规模化成本」，可与 AGENTS.md「Agent 落地大考」「AI 账单到底在买什么」呼应。

## 可回溯来源链接
- OpenAI 官方博客（芯片发布）：https://openai.com/index/openai-broadcom-jalapeno-inference-chip/
- OpenAI 官方博客（首批结果）：https://openai.com/index/jalapeno-first-results/
- OpenAI 官方博客（全栈战略）：https://openai.com/index/the-full-stack-behind-abundant-intelligence/
- TechCrunch（8/25 基准报道）：https://techcrunch.com/2026/08/25/openais-jalapeno-chip-is-built-for-fast-inference-at-scale-benchmarks-show/
- SemiAnalysis（Dylan Patel，付费墙部分内容）：https://newsletter.semianalysis.com/p/openai-jalapeno-better-than-nvidia
- 36氪/新智元：https://www.36kr.com/p/3955585236057474
- 36氪/机器之心：https://www.36kr.com/p/3955555203447945
- The Register：https://www.theregister.com/systems/2026/08/25/openais-upcoming-jalapeno-chip-looks-like-itll-be-an-inference-beast/5292052
- Altman 推文：https://x.com/sama/status/2092339694210040187

## 数据验证备注
- 所有基准数字均来自 OpenAI 官方博客 + 36氪两篇（新智元/机器之心）交叉，关键数字（每瓦 1.5–1.9×、104.3×、TCO 1.56 美元等）三方一致。
- **注意「设计辅助模型」名称不一致**：OpenAI 官方博客 = GPT-5.3-Codex-Spark；中文媒体 = GPT-Astra/GPT-6。写文章时以官方为准，或标注「媒体报道称 GPT-Astra」。
- 新智元报道的「Chris Malone 离职」为单源（新智元），写文章前建议再交叉验证，或弱化处理。
- 「10GW」「9 个月」「840mm² die」等有官方/多源支撑。
