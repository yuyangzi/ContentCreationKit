# DeepSeek 把推理速度又提了 85%，微软和硅谷公司已经开始算账了

> **导读**：6 月 27 日，DeepSeek 联合北京大学发布了 DSpark 推理加速框架，单用户生成速度提升 60-85%，已部署到生产环境。同一个月，微软 Copilot Cowork 披露正在评估接入 DeepSeek V4，旧金山 AI 创业公司 Lindy 已完成迁移。三件事指向同一个趋势：DeepSeek 不是更便宜了——它是更便宜的同时还在加速，性价比差距在拉大而不是缩小。

6 月 27 日，DeepSeek 联合北京大学发了一篇论文。作者名单里有梁文锋。DSpark 推理加速框架，全量开源，MIT 许可，已在 DeepSeek V4 生产线上运行。

DSpark 提速的关键不在模型能力，在推理引擎。同样的模型、同样的硬件，跑出更多 token。半自回归架构一次性产出全部候选位置的隐藏状态，置信度调度把 GPU 算力优先分配给存活概率最高的 token——原本浪费在无效校验上的算力，被省下来重新分配。

数值上，单用户生成速度提升 60-85%（V4-Flash）/ 57-78%（V4-Pro）；引擎吞吐量提升 51% 以上（高并发场景可达数倍）。两个数字叠加，意味着同一套硬件能服务更多并发请求，每 token 的实际成本进一步下降。

DeepSeek 的定价本来就低——V4 Pro 的 output 端每百万 token 只要 $0.87（今年 5 月 22 日永久降价 75% 之后的数字）。DSpark 让生成加速。在 Agent 时代，这是一个本来已经在性价比上碾压所有人的选手，又踩了一脚油门。

---

## 微软的成本账

6 月 16 日，微软 Copilot Cowork 正式 GA，同时宣布了两件事：从无限套餐转向按用量计费，以及正在评估接入 DeepSeek V4 作为低成本引擎。微软 Copilot 负责人 Charles Lamanna 的原话：

> We have users who do hundreds of tasks a week, which is great — they're way productive — but the consequence is the costs can go very high.

翻译一下：无限套餐扛不住了。有些用户一周跑几百个任务，token 消耗把成本直接打到了账单上。

微软当前在 Copilot Cowork 里铺了至少三条模型线：OpenAI GPT 系列、Anthropic Claude 系列、以及微软自研的 Cowork 1。现在第四条线——DeepSeek V4——正在评估中。"评估"意味着尚未最终拍板，预计数周内公布结果。但信号已经足够强了。

做一个简单的成本对比。微软当前的主力模型之一是 Anthropic Opus 4.8，output 端定价 $25/百万 token。DeepSeek V4 Pro 是 $0.87。差距约 29 倍。如果用 Anthropic 6 月 9 日刚发布、最顶级的 Fable 5（$50/百万 output），差距拉到 57 倍。

这是在同一个产品里、同一批用户、同一个任务场景下的成本差异。Copilot Cowork 的用户不会关心跑的是哪个模型——他们只关心任务完成得快不快、准不准、花不花得起。当几个模型在某些任务上表现接近、价格却差了近 30 倍，经济账本身就会推动路由切换。

---

## 有人在用钱包投票了

如果说微软还在评估阶段，旧金山 AI 创业公司 Lindy 已经出手了。

Lindy 做 AI 助手，之前大量依赖 Anthropic 的模型。今年，他们把部分工作负载从 Anthropic 迁到了 DeepSeek，用美国云服务商托管、数据不出境，省下了数百万美元。

这件事的价值不在金额本身——数百万美元对微软来说是零头。价值在于 Lindy 的迁移理由不是仇视 Anthropic 或追捧开源，就是一个纯粹的成本计算。同样的任务、足够的表现、便宜 29 倍。企业预算不会跟算术过不去。

Lindy 不是个例。OpenRouter 的数据显示，最近一周 60%+ 的 token 流量走的是中国模型——不是实验性调用，是实际生产消耗。Ramp 追踪的数万家美国企业首次直接付款数据里，DeepSeek 登顶 2026 年 6 月"trending software vendors"榜首。VentureBeat Q1 2026 AI 基础设施调查显示，企业自管推理栈（Triton/vLLM/Ray/K8s）的采用率从 11.3% 跳到 17.9%——这些基础设施管道正在为开源模型铺路。

坦白讲，"正在"这个词很重要。DeepSeek 在美国企业中的实际渗透率仍然只有约 0.1%（截至 2026 年 4 月 Ramp AI 指数，同期 Anthropic 34.4%，OpenAI 32.3%）。Ramp 的 trending 榜首反映的是新增趋势，不是存量份额。0.1% 到 34% 之间还有很长的路。

但从另一个角度看：正因为基数极低，每一个新增案例——不管是 Lindy 这样的创业公司还是微软这样的巨头在评估——传递的信号都远大于当前的数字。

---

## 一个正在成形的基础设施级玩家

DSpark 选择全量开源——训练代码、模型权重、评估脚本、DeepSpec 框架全部 MIT 许可放上 GitHub。这不是慈善。这是用开源吸引社区贡献、形成生态绑定，让推理层留在 DeepSeek 技术栈里。

同一时间它也开源了 DFlash 和 Eagle3 两种基线推测解码方法的训练代码。DeepSeek 正在变成推测解码（speculative decoding）领域的标准基准框架。

云厂商这边全线到齐：Azure AI Foundry、AWS Bedrock/SageMaker、Google Vertex AI——三大云都已上线 DeepSeek 模型。中间层托管生态也在成型：DeepInfra、Together AI、Fireworks AI，以及聚合了全行业模型的 OpenRouter。

这已经不是某一个模型的问题了。它正在变成一个平台。

DSpark 踩的正是这一脚油门。别人在拼模型能力的时候，DeepSeek 在拼推理成本——而且它把这套加速框架开源了，等于对全行业说：你用我的引擎，成本还能再降。这不只是产品竞争，是生态竞争。

---

有一个缺口不能回避：多国政府对 DeepSeek 有安全禁令，至今没有独立第三方安全审计。微软还没拍板，最终可能选择不用。

但即便把这些约束全部考虑进去，趋势仍然指向同一个方向。当 DSpark 让本已最便宜的方案再快 85%，当 Lindy 和 Ramp 的数据显示企业真的在用钱包做选择，当微软在一个产品里给 DeepSeek 留了位置——性价比差距不会自己消失。

这件事最让人玩味的地方在于：它不是中国模型"崛起"的叙事。它是全球 AI 基础设施正在经历的价格重估——而加速这场重估的，是一个正在变得更快的开源推理引擎。

*参考来源：*
- DSpark 论文 - DeepSeek × 北京大学：[GitHub DeepSpec 项目](https://github.com/deepseek-ai/DeepSpec)
- 36氪 - 梁文锋署名论文，生成速度大涨 85%：[https://www.36kr.com/p/3871187114448133](https://www.36kr.com/p/3871187114448133)
- Axios - Microsoft explores DeepSeek for Copilot Cowork：[https://www.axios.com/2026/06/16/microsoft-copilot-cowork-tokenmaxxing-cowork](https://www.axios.com/2026/06/16/microsoft-copilot-cowork-tokenmaxxing-cowork)
- Anthropic 官方定价：[https://www.anthropic.com/pricing](https://www.anthropic.com/pricing)
- DeepSeek API 定价：[https://api-docs.deepseek.com/quick_start/pricing](https://api-docs.deepseek.com/quick_start/pricing)
- TechRepublic - Chinese AI models cost and risk（Lindy 案例）：[https://www.techrepublic.com/article/news-chinese-ai-models-cost-risk/](https://www.techrepublic.com/article/news-chinese-ai-models-cost-risk/)
- Chosun - Chinese Open-Source AI Gains Traction（OpenRouter 60%+、新加坡国家模型选型）：[https://www.chosun.com/english/industry-en/2026/06/24/77XSK4BYYNBBDGMUAB3E2CRLYA/](https://www.chosun.com/english/industry-en/2026/06/24/77XSK4BYYNBBDGMUAB3E2CRLYA/)
- VentureBeat - DeepSeek shattering token moat（企业自建推理栈调查）：[https://venturebeat.com/infrastructure/how-deepseeks-radical-architecture-is-shattering-silicon-valleys-token-moat](https://venturebeat.com/infrastructure/how-deepseeks-radical-architecture-is-shattering-silicon-valleys-token-moat)
- Ramp AI Index（DeepSeek trending vendors 榜首、0.1% 渗透率数据）
