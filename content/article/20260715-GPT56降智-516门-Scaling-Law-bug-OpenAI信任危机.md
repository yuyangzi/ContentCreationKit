# 你买的"智力"，平台随时能调暗

> 2026年7月，OpenAI 经历了从产品到理论的一次罕见连环打击：GPT-5.6 Sol 被曝推理预算从 960 砍到 128，GPT-5.5 的"516断" bug 时隔数月仍无官方回应，就连支撑整个行业"越大越好"信仰的 Scaling Law 原始论文也被挖出方法论缺陷。三件事放在一起看，指向同一个问题——当"智力"成为平台手里可动态调节的旋钮，用户买的到底是什么？

---

日本一家 AI 开发团队的早上通常从检查代码库开始。7月13日，他们发现的不是 bug，而是一种更诡异的东西：前两天还"聪明得吓人"的 GPT-5.6 Sol Max，突然变笨了。同一个提示词，两天前输出一份条理清晰的六步方案，今天只给了三段泛泛的概述。

团队在社群里一问，发现不是个案。

---

## 那把看不见的旋钮

GPT-5.6 Sol 是 OpenAI 在 7 月 9 日发布的旗舰推理模型，定价 $5/百万输入 token、$30/百万输出 token。发布头几天，社区评价是"要求 10 分，稳定交出 12-13 分"，有人直接称它为"远超预期的怪物"。

三天后，怪物萎了。

一位代号 ns123abc 的用户用一种叫"模型指纹"的技术找到了原因。方法不复杂——在系统提示词的 `Valid Channels` 段里藏一个变量名，然后观察返回结果。他发现了一个从未被 OpenAI 公开过的内部参数：**juice value**（推理预算）。发布当天，Sol Max 的 juice value 是 960；到了 7 月 12 日，变成了 128。降幅 87%。

不只是 Max 档位。整个 Sol 系列的推理预算都被砍了一刀：

| Sol 档位 | 旧值 | 新值 |
|---------|:---:|:---:|
| Max | 960 | 128 |
| Xhigh | 128 | 40 |
| High | 40 | 16 |
| Medium | 16 | 8 |
| Low | 8 | 4 |

与此同时，Codex 客户端显示的可用上下文从 372k 降到了 272k。

OpenAI Codex 负责人 Thibault Sottiaux（Tibo）在 X 上回应了。他说"没有降智，只是好事"——四点解释：

1. 推理效率优化上线，用户多了约 10% 的用量配额
2. 上下文上限降回 272k 是因为 372k 导致计费异常，临时回退
3. juice value 的调整是为了搞清楚额外用量从何而来而做的"实验"，已恢复
4. 修复了多 agent 与 auto-review 中 agent 创建超出预期的 bug

"已恢复"这个说法社区反应冷淡。Tibo 声称恢复后，仍有用户测到 128。没有独立的对照实验——同一模型快照、同一任务、只改 juice value——来真正验证这件事。

FixlationAI 的评价更直白：你原来的 Extra High，现在得拧到 Max 才能获得同样的效果。各档位整体下调了一档。

---

## 516 的死结

如果 juice value 事件是第一次让用户明确感知到"模型智力可以随时调整"，那 GPT-5.5 "516门"就是一次持续时间更长、波及面更广的前奏。

GPT-5.5 在处理复杂任务时，推理 token 会极其频繁地精确卡在 **516**。次级集中点出现在 1034（516×2）、1552（516×3）。当 token 停在 516 时，模型会跳过中间推理步骤，直接输出 final_answer——且大概率是错的。

GitHub Issue #30364 对 390,195 条响应、865 个会话做了扫描，数据触目惊心：

- GPT-5.5 占总响应量的 19.3%，却占了精确 516 事件的 82.0%
- GPT-5.5 中推理达到或超过 516 的响应里，有 44.0% 被精确截断在 516
- 非 GPT-5.5 模型的基线只有 1.3%，GPT-5.5 的异常倍率是 **33.6 倍**

趋势方面，2 月份 516 事件只占 0.11%，5 月份飙升到 53.30%。不是线性的，而是突然恶化，说明这不是一个静态 bug，而是某种基础设施变更在逐步部署。

多位开发者独立复现了这个问题。bentoner 写了一个叫 codex-516-hook 的检测工具，20 次 Codex 运行中 18 次命中 516（命中率 90%），但裸 API 端 0 次。这个对比说明问题不在模型本体，而在 Codex 服务层。NickalasLight 追踪了 57,813 条 GPT-5.5 记录，516 命中率从 5 月的 26.7% 升至 7 月初的 48.1%。

社区主流判断认为这是 continuous batching 的技术 bug——推理被分入固定大小的约 512 token 批次槽位，溢出即截断。516/1034/1552 的"梳齿"分布符合量化的批次边界，不是故意降智。

但有一个细节比 bug 本身更值得注意：**截至 7 月 15 日，OpenAI 对此没有一句官方回应。** Issue #30364 只有自动 bot 贴的标签，没有任何员工评论。

与此同时，OpenAI 的帮助文档承认存在静默降级政策：Plus 用户每 3 小时 160 条后、Pro 用户在"heavy thinking"模式下受容量限制时，系统会静默切换到更便宜的 mini/instant 模型——无弹窗、无标签变化、无视觉提示。

一个 bug 五个月不回应，外加白纸黑字的静默降级政策，你很难不把它们放在一起看。

---

## 桌子的第三条腿也在摇晃

如果说 GPT-5.5 和 GPT-5.6 的争议还停留在产品层面，那第三件事直接动摇了桌子本身。

7 月 4 日，Diogo Almeida 发了一篇博文，指出 2020 年那篇著名的 Scaling Law 论文存在根本性方法论缺陷。Scaling Laws for Neural Language Models（Kaplan et al., OpenAI, 2020）——就是那篇告诉行业"模型越大，性能越好"、直接点燃了过去四年大模型军备竞赛的论文——有三重问题：

1. 所有模型无论大小，都用约 130B token 训练。小模型"过饱"，大模型"饥荒"，在控制变量法下这种固定 token 预算本身就是偏差。
2. 余弦学习率衰减至零，人为造成了性能平台期。大模型其实远未饱和，但学习率衰减让它看起来饱和了。
3. 论文声称"不受学习率影响"——在固定 token 上限下的确如此，但这句话不适用于 Scaling Law 想描述的无限数据场景。

Diogo 坦言："我当时也在 OpenAI 做 LLM 优化，也没看出这个 bug。"

这篇文章在 36Kr 翻译后被冠以"万亿算力全白烧"的标题。这个说法有渲染成分。行业从 2022 年 DeepMind 的 Chinchilla 论文之后就已经修正了参数与数据的配比方向——Chinchilla 发现 N_opt ∝ C^0.50（参数和数据等比例增长），而不是 Kaplan 论文的 C^0.73（堆参数优先）。GPT-3 的 175B 参数配 300B token 确实"虚胖"了，Chinchilla 自己用 70B 参数配 1.4T token 在同等算力下全面超越了 Gopher 的 280B 参数配 300B token。

真正的浪费集中在 2020 到 2022 年。但真正的问题不是浪费了多少钱，而是——**如果这么好几年、这么多顶级研究者、这么多投入，连 Scaling Law 这么基础的结论都站歪了，那还有多少"先验假设"我们从未认真质疑过？**

---

## 不是一家之过

OpenAI 不是唯一在做这件事的。

Anthropic 在今年 3-4 月被曝 Claude Code 默认推理强度从 high 降至 medium，据第三方社区测试，推理深度出现明显下降。同时触发了缓存 bug 和系统提示词限制。4 月 23 日 Anthropic 发布了一份 postmortem 承认三重原因，重置配额并道歉。

Google 的 Gemini 在近期经历了多次静默变更——加上计算上限、重构订阅层级、强制替换旧模型——通常不公开承认。

这些不是孤立的"坏消息"。它们是 AI SaaS 模式的结构性产物。推理成本是模型公司最大的运营支出，订阅收入却是固定的。当用量增长超过预期，平台的应对方向不外乎两个：涨价，或降本。"降本"最直接的手段之一，就是把智力旋钮往回拧一点——只要拧得不至于让太多用户察觉。

但问题不止于省钱。

---

## AI 模型正在变成灯泡

你买了一款型号固定的灯泡——比如 GPT-5.6 Sol，规格写在包装上，标价清晰。但亮度旋钮不在你手里。平台可以根据自己的运营需求，随时调亮或调暗。前天还是 960 流明，今天只有 128 了。型号没变，包装没变，亮度和昨天不一样了。

juice value 就是这个旋钮。它决定了模型愿意在一个任务上花多少心思去推理。而用户完全看不见它的存在——如果不是有人用"模型指纹"去探测，这件事可能永远不会暴露。

更深层的焦虑在这里：**用户付费购买的不是一个固定的"智力"，而是一件动态定价的体验。** 你为 Pro 订阅付了 $200/月，你得到的不是一个"聪明的模型"，而是一个"可能聪明、也可能被限流的模型"。你的实际体验取决于平台的成本压力、负载情况、以及实验策略——这些因素跟你的需求毫无关系，却决定了你拿到的推理质量。

这不仅仅是透明度的缺失。这是信任机制的断裂。传统软件卖的是功能——功能是固定的，买的时候就知道它是什么。AI 模型卖的是能力——能力正在变得动态可调，你很难确定今天拿到的是昨天那个版本，还是打了折扣的版本。

当"智力"可以被动态调配，用户买的到底是什么？这个问题没有简单的答案。但可以肯定的是——如果平台不主动回答，用户迟早会用自己的方式去回答。

---

## 参考来源

- GPT-5.6 官方发布公告 — https://openai.com/index/gpt-5-6/
- Tibo Sottiaux 回应（X/Twitter）— https://x.com/thsottiaux/status/2076495156757577895
- FixlationAI 对 GPT-5.6 Sol 推理预算下调的指控 — https://x.com/FixlationAI/status/2076469274441380349
- Zvi Mowshowitz 分析 — https://thezvi.substack.com/p/better-call-sol-the-workhorse
- explainx.ai 技术分析 — https://explainx.ai/blog/gpt-5-6-sol-thinking-budget-banked-reset-tibo-july-2026
- GPT-5.5 516 现象 GitHub Issue #30364 — https://github.com/openai/codex/issues/30364
- 36Kr/新智元：《GPT-5.5突遭暗中降智，思考一到516就断，越难越翻车》— https://www.36kr.com/p/3883304315891717
- 36Kr/新智元：《OpenAI塌房，Scaling law原作曝bug，万亿算力全白烧》— https://www.36kr.com/p/3883301202440198
- 36Kr/新智元：《GPT-5.6 Sol一夜变笨，思考预算960砍到128，没智力固定的模型了？》— https://www.36kr.com/p/3896320634685318
- Diogo Almeida 博文：Scaling Laws, Honestly — https://www.completeskeptic.com/p/scaling-laws-honestly
- Lilian Weng 博文：Scaling Laws, Carefully — https://lilianweng.github.io/posts/2026-06-24-scaling-laws/
- Kaplan et al. 2020 原始论文 — https://arxiv.org/abs/2001.08361
- Chinchilla / Hoffmann et al. 2022 — https://arxiv.org/abs/2203.15556
- explainx.ai GPT-5.5 深度分析 — https://explainx.ai/blog/gpt-5-5-codex-reasoning-token-clustering-bug-2026
- SourceFeed 深度报道 — https://sourcefeed.dev/a/the-516-token-cliff-inside-gpt-55s-silent-reasoning-regression
- Hacker News 讨论 — https://news.ycombinator.com/item?id=48789428
- Anthropic 事后分析（2026.04.23）— https://www.anthropic.com/engineering/april-23-postmortem
- WIRED Tibo 专访（2026年6月11日）— https://www.wired.com/story/model-behavior-interview-with-openai-codex-lead-tibo-sottiaux/
- TechnoLynx: AI-as-a-Service 结构性缺陷分析 — https://www.technolynx.com/post/3-ways-how-ai-as-a-service-burns-you-bad
- Arize AI: AI Model Subsidies Ending — https://arize.com/blog/ai-model-subsidies-ending-llm-inference-costs/
