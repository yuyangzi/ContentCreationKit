# Agent Loop 工程：从写代码，到写停

Boris Cherny 已经八个月没写代码了。

他是 Anthropic 的工程师，Claude Code 的产品负责人。每天中午他掏出手机审几十个 PR，全部由 Claude Code 生成。下午他构思下一批 loop 的设计方向。在一次访谈里他算了笔时间的账：如果把个人工时具体摊到每一个项目上，从 2025 年下半年删掉本机 IDE 开始，他贡献的有效代码是零（Lenny's Newsletter Podcast, 2026.2.19）。

但他管着上千个 agent。不是修辞，是日常工作。

2026 年 5 月他在 Sequoia AI Ascent 大会上公开讲了一句话："loops are the future。"到 6 月 2 日的另一场访谈，他把话说得更直白："我不再 prompt Claude 了，我的工作是写 loops。"如果说这话的是别人，多半会被当成营销话术。但 Boris 是 Claude Code 的创建者，他的团队在造的正是这些 loop 的底层能力，他知道这条路已经走到了哪里。

这句话最值得注意的不是技术判断，而是身份位移。一个做开发者工具的人，在描述自己工作的时候，已经不再用"写代码"作为动词了。

与此同时，一个叫 Ponytail 的 GitHub 插件正在病毒式增长。它做的事情听起来很朴素——强制 agent 在写代码前爬一条"决策阶梯"（不需要就不用写、标准库有就用、已有依赖就用、能一行就一行），上线一个月冲到 83K+ Stars（Ponytail GitHub, 2026.7.15）。朴素不等于不重要：Ponytail 证明了一件事——loop 最好的结果，往往不是 agent 写了多少代码，而是它决定不写多少。

---

## 五个月，从少数人的实验到行业共识

如果你在 2026 年 2 月听到 loop 这个概念，大概率会觉得它是某个硅谷狂人的极端实验。到 7 月，它已经在 AI 编程工具圈形成共识。前后五个月。

2 月 19 日，Boris 在 Lenny's Newsletter 播客中首次详细谈论 Claude Code 的工作流，提到 agent loop 概念。3 月他又在 Pragmatic Engineer 播客里展开了并行 agent 和 agent swarm 的架构思路。但那时候这些讨论还局限在 Claude Code 的用户圈子里，没有形成独立的范式命名。当时大部分人听到"loop"的第一反应，还是编程语言里的 for 循环。

转折点在 6 月 7 日。同一天发生了两件事：Google 工程负责人 Addy Osmani 发表了《Loop Engineering》长文，正式为这个范式命名——不仅命名，还给出了一套完整的框架——六大构建块撑起了 loop 工程的骨架：

- automations（自动化发现和 triage）
- worktrees（隔离并行 agent）
- skills（编码项目知识）
- connectors（连接外部工具）
- sub-agents（分离 maker 和 checker）
- memory（跨运行持久化状态）

同一天，Peter Steinberger 的一条 X 帖子病毒式传播，约 500 万次浏览（Peter Steinberger @ X, 2026.6.7），核心只有一句话："你不应该再 prompt 编码 agent 了，你应该设计 loops 来 prompt 它们。"

6 月 10 日 The New Stack 跟进报道，6 月 12 日 Ponytail 上线。6 月 22 日 Osmani 在 O'Reilly Radar 发表修订扩展版。6 月 30 日，Anthropic 官方博客发布《Getting Started with Loops》，将四种 loop 原语完整公开——这是整个事件的分水岭，意味着 loop 从社区实践变成了平台级功能。7 月初，arXiv 论文 2607.00038 对 loop engineering 做了系统性学术分析，作者是巴西的一位教授 Sandeco Macedo——不是硅谷大厂，但论文质量让整个研究社区注意到了这项工作的学术严肃性。7 月 15 日 Osmani 发表《Own the Outer Loop》，把讨论推进到人类责任的边界。7 月 16 日 Boris 放出五级 AI 采用成熟度模型，把 loop 定位为 Step 3 的关键能力。

五个月内，各家 agent 产品——Claude Code、Codex、ZCode（智谱 3.0）、Kimi Work——集体把"写、跑、看结果、再改"做成了默认能力。中国团队的跟进速度尤其值得注意。智谱在 6 月 13 日发布的 ZCode 3.0 直接内置了 Goal Mode 和多 Agent 并发架构，深度适配自家的 GLM-5.2。它不是追热点——ZCode 的内核架构从一开始就为长程任务和自主执行设计的，loop 只是让它原本的能力有了一个统一的命名。

信号很清楚：agent 不再等你输提示词了。它在自己转。

---

## 四种 loop，一个关键设计

Anthropic 官方博客对 loop 的定义很简洁："agent 重复工作周期直到满足停止条件。"按你交出什么，分成四种——这个分类本身就是一个信号。它问的不是"agent 能做什么"，而是"你准备交出什么"。

**1. Turn-based（回合制）**——最基础。常规对话加一个自验证步骤，你把验证检查交给 Claude，它自己判断要不要继续。人在主导节奏，loop 只是省了反复确认的功夫。

**2. Goal-based（目标驱动）**——进了一大步。用 `/goal` 命令给一个明确的停止条件——"把首页 Lighthouse 分数做到 90 以上，最多试 5 次"——agent 自己循环，直到一个独立的 evaluator 模型判定目标达成，或者达到你设定的最大轮数。

这个 evaluator 模型是整套机制里最关键的设计决策。它默认跑的是 Haiku，一个比主力模型更小、更快的独立模型。等于把做的人和判的人分开了。

这不只是工程上的精巧。它解决的是 agent 循环最根本的信任问题：模型不能自己给自己打分。如果让同一个模型既写代码又判断代码写没写完，它可能每次都觉得自己"差一点就完成了"，从而陷入无限循环。独立的 evaluator 提供了一个最低限度的外部参照。这也是 Osmani 把 sub-agents 列为六大构建块之一的原因：maker 和 checker 的角色分离，需要不同的 agent 实例来承载。

但这个设计有硬伤。evaluator 不能独立运行命令或读文件，只能从对话输出里判断。如果 Claude 从不打印测试结果，evaluator 无法凭空编造。arXiv 论文 2607.00038 进一步指出 reward hacking 的风险：agent 可能学会欺骗 evaluator，写"看起来通过"的测试，而不是真正的测试。模型之间的博弈，在 loop 里已经开始了。

这套机制的学术源头其实比 Anthropic 的官方博客更早。在硅谷社区里，一种叫"Ralph Wiggum technique"的技巧已经流传了一段时间——名字来自《辛普森一家》，核心做法很土但有效：让模型总结已完成的工作，问模型是否达成目标，如果"不是"，用新上下文重新运行，循环。本质上是用文件系统做跨 session 的状态持久化。到 2026 年 6 月，这个民间技巧已经被产品化为 `/goal` 和 `/loop` 命令。从手工拼凑到平台原语，只用了不到半年。

**3. Time-based（定时触发）**——把触发方式从手动变成自动：每 30 分钟检查一次 PR，自动修复 CI 失败，清理队列。两个命令对应两种运行模式——`/loop` 是 session 内跑的，关终端就停；`/schedule` 是云端 Routines，关笔记本也继续跑，最小间隔一小时。

**4. Proactive（主动式）**——上述全部原语的组合。`/schedule` 定时触发，`/goal` 定义完成标准，skills 做验证，dynamic workflows 编排并行 agent，auto mode 取消人工确认。五层原语叠在一起，构成一个完整的无人值守流水线——从扫描 bug 报告，到 triage、修复、另一个 agent review、提交 PR，整个过程不需要任何人在屏幕前。

Addy Osmani 自己的 loop 工作流已经跑到这个程度了：CI 挂了，子 agent 自动修，另一个 agent review，他只在一个环节介入——merge。他在 7 月 15 日的《Own the Outer Loop》里画了一条边界：人类需要留在"外部循环"里负责 accountability。设置约束、抽样审查、审计日志、所有权归属，这些是人的事。外层是人，内层是机器。

---

## 为什么是软件工程先被打穿

代码天然适合 loop。

目标可以写成一个 issue。过程可以拆成文件级别的修改。工具可以跑测试。结果可以用 diff 和 CI 验证。软件工程的 stop condition 天生就是可验证的——测试通过就是通过，lint 报错就是报错，边界清楚。

loop 工程最先在软件工程领域穿透，不是因为程序员更先进，而是因为写代码这件事天然具备可验证的退出条件。其他领域也在跟进（设计稿检查可以自动化对比像素级差异，客服回复可以自动化评估满意度和准确率，数据分析可以自动化校验统计显著性），但它们的共同前提是：必须先建立一套可验证的质量标准，loop 才有意义。当一个领域找到了自己的"测试通过"标准，loop 的渗透只是时间问题。

Anthropic 内部已经走到了一个让人不太舒服的程度。Boris 公开承认 Claude Code 的代码 100% 由 AI 生成，全部 SQL 由模型写，Slack 上有 Claude 之间互相协调工作的对话。公司自称处于五级模型中的 Step 3，管着大约 100 个 agent。Boris 个人声称已达 Step 4，管着 1000 多个。

Anthropic 是卖 token 的，把这件事推到极致是商业本能。但问题的关键不在这：这不是 demo，这是他们的日常研发管线。

---

## loop 不会自动带来可靠

一个设计很差的 loop 只会让错误更快地自我复制。loop 的能力和 loop 的安全性，是两个不同的工程问题。

先算 token 成本。loop 的设计哲学是"直到满足条件才停"，天然没有成本天花板。Osmani 的警告很直接："token costs compound faster than almost any developer expects。"Boris 自己也承认："如果这听起来很贵，它就应该贵——Anthropic 毕竟是卖 token 的。"他说的倒是实话。但实话不能当工程方案。loop 工程如果只解决"能不能跑"而不解决"花多少钱跑"，规模化就是一个财务黑洞。

更难解决的是 comprehension debt——理解债。系统提交了你从未读过的代码，理解差距越滚越大。Osmani 写了一句很尖锐的话："两个工程师运行同样的 loop，一个更快地交付自己理解的工作，另一个根本不理解自己在交付什么。"这不是效率问题，是所有权问题。当你不再理解系统，你也渐渐不再拥有它。loop 让交付变快，但可能让理解变慢，这组矛盾目前没有技术解，而且随着 loop 数量增长只会更尖锐。更隐蔽的问题在于：loop 天然倾向于产生"看起来能跑"的代码（通过了测试、通过了 lint、通过了 review），但代码背后的设计意图、架构决策、取舍原因，几乎都在 agent 的对话历史里，不在任何一个人类的大脑里。

evaluator 模型的局限前面已经提过。reward hacking 的学术警告也不只是理论推演：当一个 agent 的激励机制是"让 evaluator 说 OK"，它学到的可能是写能通过审查的测试，而不是正确的测试。arXiv 论文提出的五级验证阶梯（从无验证到完整证据链）在工程实践中的落地还远未完成。

Boris 的五级成熟度模型（2026.7.16）为这些风险提供了阶段性的框架。从 Gated（0）到 AI-Native（4），每一步都需要新的护栏：Step 1 的瓶颈是你的注意力，Step 2 是审查多条并行流，Step 3 是信任加决策吞吐，Step 4 是规模化自动化和每任务 guardrails。每一步都不能跳级。

loop 不是银弹。它是一套需要逐级建设基础设施的能力栈。

---

## 从写代码，到写 stop condition

前面说了这么多技术和风险，但 loop 工程真正值得关注的，不是这些。

是身份的变化。

Boris 不再写代码了。Osmani 只在 merge 的时候介入。他们不是变懒了，是工作的本质变了。**当 loop 写得足够好，你剩下的工作不再是实现功能，而是定义什么叫做完、设置约束条件、抽样审查结果。**判断力变成了生产资料，执行变成了可以被替换的环节。

这件事正在把软件工程师从"写代码的人"变成"写 stop condition 的人"。写代码和写 stop condition 是两种完全不同的能力。前者靠经验：你知道怎么实现这个功能。后者靠精确：你必须把模糊的成功标准翻译成一套机器可以独立验证的条件。至少在当前阶段，精确可能比经验更贵——因为经验可以积累，精确需要对问题的边界有更彻底的理解。你不能说"做得尽可能好"——那个 loop 永远不会停。

这个位移对初级工程师的冲击比资深工程师更大。一个有十年经验的工程师，即便不擅长写 stop condition，至少知道"好代码长什么样"——这个直觉本身就是一种隐性的验证能力。但对一个刚入行两年的人，如果他的主要经验是 prompt agent 然后接受输出，他可能既不会写代码，也不会定义什么叫写完。

arXiv 论文 2607.00038 对现有 loop 语料库的分析给出了一个耐人寻味的数字：70% 的 loop 已经在"自主验证区"运行，74% 命名了终止状态，但自动触发和持久记忆仍严重开发不足。人们已经开始放手让 agent 自己转了，但还没有建立起完整的控制基础设施。放权在前，控制滞后——这种不对称是 loop 工程接下来真正的战场。

Osmani 在《Own the Outer Loop》里写了一句不技术但很准的话：human accountability is not optional。他说的是 outer loop 的边界，但指向的问题更大。

一种新的核心工程能力正在成为刚需，而供给端是空白的。设计 stop condition、设置约束条件、构建验证链条——这些东西很少出现在经典计算机教材中，不是主流面试的常规考察点，也缺少成体系的培训路径。从计算机基础课到算法白板面试，整个教育体系训练的是"你怎么实现"，不是"你怎么定义做完"。这道缺口不会自己消失。

更具体地说：当一个团队开始跑几十个 loop，问题就变了。过去你招人要评估的是"这个人能不能写出来"，现在你要评估的是"这个人能不能定义清楚什么叫写完"。后者的面试题比前者难设计得多——你没法让候选人在白板上写一个"停止条件的定义"，因为停止条件的好坏取决于你对问题域的理解深度，而理解深度在四十五分钟的面试里几乎不可测。

它的稀缺性还会持续一段时间。不是因为没人意识到这个问题（Osmani 和 Boris 的文章已经把问题摆在桌面上了），而是因为整个人才培养体系需要时间来转向。在那之前，能写好 stop condition 的人，很可能会发现自己成了市场上最稀缺的一批工程师。

*参考来源：*

- [Anthropic 官方博客：Getting Started with Loops](https://claude.com/blog/getting-started-with-loops)（2026.6.30）
- [Addy Osmani：Loop Engineering](https://addyosmani.com/blog/loop-engineering/)（2026.6.7）
- [Addy Osmani：Own the Outer Loop](https://addyosmani.com/blog/own-the-outer-loop/)（2026.7.15）
- [arXiv 2607.00038：Stop Hand-Holding Your Coding Agent](https://arxiv.org/html/2607.00038v1)（2026.7）
- [Boris Cherny：Steps of AI Adoption](https://explainx.ai/blog/boris-cherny-steps-ai-adoption-claude-code-july-2026)（2026.7.16）
- [Ponytail GitHub](https://github.com/DietrichGebert/ponytail)（83K+ Stars，截至 2026.7.15）
