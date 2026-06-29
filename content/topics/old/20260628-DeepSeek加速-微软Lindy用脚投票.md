# DeepSeek 又快了 85%，微软和硅谷创业公司正在用脚投票

**日期**: 2026-06-28
**类型**: [热点] [技术突破] [行业信号]
**热度**: ⭐⭐⭐⭐⭐

## 热度背景

- **信号一**：DeepSeek 联合北京大学 6 月 27 日发布 DSpark 推理加速框架，梁文锋署名，全量开源。单用户生成速度提升 60-85%（V4-Flash）/ 57-78%（V4-Pro），已在 V4 生产线上运行。
- **信号二**：微软 6 月 16 日披露 Copilot Cowork 评估接入 DeepSeek V4，Charles Lamanna 直言"有些用户一周跑几百个任务，成本太高了，无限套餐扛不住"。Opus 4.8 定价 $25/百万 output token，DeepSeek V4 Pro $0.87，差距约 29 倍。
- **信号三**：旧金山 AI 创业公司 Lindy 已从 Anthropic 迁部分工作负载到 DeepSeek，省下数百万美元。

三件事指向同一个趋势：DeepSeek 正在从中国开源黑马变成全球 AI 基础设施级玩家——不只因为它便宜，还因为它在持续加速，性价比差距在拉大而不是缩小。

## 核心关注点

1. **DSpark 推理加速的工程价值**：85% 提速不是模型迭代，是推理引擎优化——半自回归架构 + 置信度调度把无效校验的算力省出来重新分配。同样的模型、同样的硬件、跑出更多 token。每 token 实际成本进一步下降。
2. **微软的经济账**：Copilot Cowork 从无限套餐转向按量计费，同时评估 DeepSeek 作为低成本引擎。微软在一个产品里铺了 OpenAI + Anthropic + Cowork 1 + DeepSeek 四条线——这是"模型从信仰变成零件"的范式转变，不涉及地缘政治维度。
3. **已有企业用钱包投票**：Lindy 迁移案例 + Ramp 数据显示 DeepSeek 登顶美国企业"trending vendors"榜首 + OpenRouter 超 60% token 流量走中国模型。
4. **"基础设施级"的证据链**：云厂商全线接入（Azure/AWS/GCP/阿里云/华为云）、中间层托管生态成型（DeepInfra/Together AI/Fireworks/SOC2 级 Atlas Cloud）、新加坡选 Qwen 而非 Llama 做国家模型。

## 创作方向

- **主线叙事**：DSpark 发布（开头，技术澄清"快的不是模型"）→ 微软 29 倍成本账 + Lindy 已迁移（中段）→ "基础设施级"正在成形（收尾）
- **差异化** vs 已发布文章《中国开源模型全球崛起》（6.20）：DSpark 是新信息、Lindy 是新案例、"加速拉大差距"是新角度
- **不写**：地缘政治风险（保持正面叙事纯净，留到后续文章）

## 来源链接

### DSpark
- [GitHub: DeepSpec 项目](https://github.com/deepseek-ai/DeepSpec)
- [36氪 - 梁文锋署名论文，生成速度大涨 85%](https://www.36kr.com/p/3871187114448133)
- [知乎 - 如何评价 DeepSeek 发布 DSpark？](https://www.zhihu.com/question/2054255700407055156)

### 微软 + DeepSeek
- [Axios - Microsoft explores DeepSeek for Copilot Cowork](https://www.axios.com/2026/06/16/microsoft-copilot-cowork-tokenmaxxing-cowork)（一手信源）
- [36氪 - 微软也烧不起 Token，该 DeepSeek 上位了](https://www.36kr.com/p/3863453656110342)
- [Pandaily - Microsoft Can't Afford Unlimited Token Either](https://pandaily.com/microsoft-deepseek-token-cost-ai-jun2026)

### 定价
- [Anthropic 官方定价](https://www.anthropic.com/pricing)
- [DeepSeek API 定价](https://api-docs.deepseek.com/quick_start/pricing)

### 行业信号
- [TechRepublic - Chinese AI models cost and risk](https://www.techrepublic.com/article/news-chinese-ai-models-cost-risk/)（Lindy 案例）
- [Chosun - Chinese Open-Source AI Gains Traction](https://www.chosun.com/english/industry-en/2026/06/24/77XSK4BYYNBBDGMUAB3E2CRLYA/)（OpenRouter 60%+、新加坡选 Qwen）
- [VentureBeat - DeepSeek shattering token moat](https://venturebeat.com/infrastructure/how-deepseeks-radical-architecture-is-shattering-silicon-valleys-token-moat)（企业自建推理栈调查）
