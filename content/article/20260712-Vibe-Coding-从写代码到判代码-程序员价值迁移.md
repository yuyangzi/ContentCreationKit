# Vibe Coding 之后：当 AI 写代码，程序员判代码

> 2026 年 7 月，三件事在中文技术社区形成了共振：Vibe Coding 话题在知乎拿下 113 万热度，uv 创始人坦白团队开始不信任他用 AI 写的 PR，Linus Torvalds 在孟买开源峰会上系统性地修正了自己对 AI 编程的立场。三件事指向同一个问题——当 AI 能写出 90% 的代码，剩下 10% 的判断力，才是程序员价值的核心所在。

---

Charlie Marsh 最近遭遇了一场信任危机。

这位 uv 的创始人（Python 生态里最炙手可热的包管理工具，月下载量 1.26 亿，今年 3 月刚被 OpenAI 收购）在 6 月的一期播客里说了两句话。第一句被 InfoQ 做成了标题："我一行代码都没读就发布了。"他用 GPT-5 写了一个内部 Rust linter 工具，没审查就上线了。

他的第二句是："团队现在不信任我的 PR 了。"Marsh 的原话是这样的——以前他提交 PR，同事只需要 minimal review，因为他手写的代码质量摆在那里。现在他用 Claude Code 交上去的东西，"我确实会犯我手写时不会出现的错误"。他甚至承认，有时候早上醒来翻看前一晚提交的 PR，"等等，这代码其实写得挺烂的"。

一个创造了被数百万工程师依赖的工具的人，一个刚被 OpenAI 收购的开发者——连他自己写的 AI 代码，团队都不敢信了。

这不是 Charlie Marsh 一个人的问题。这是 2026 年 AI 编程领域最棘手的问题之一。

## 用得越多，信得越少

Vibe Coding 这个词已经基本退出了主流讨论。

提出者 Andrej Karpathy 自己在 2026 年 2 月弃用了它，换了个新说法叫 "agentic engineering"。他在原推文里承认，vibe coding 只是 "shower thoughts throwaway tweet"——洗澡时的即兴想法，没想到变成了 Collins Dictionary 的 2025 年度词汇。

但现象仍在加速。GitHub 的数据显示，全球新增代码里 AI 生成的占比已经到 41-46%。但 Stack Overflow 2025 年调查里有一个数字更扎眼——只有 33% 的开发者信任 AI 代码的准确性。

绝大多数人在用，只有三分之一相信。

数据更具体。CodeRabbit 分析了 470 个 PR，结论：AI 代码的缺陷密度是人类的 1.7 倍，安全漏洞是 2.74 倍。GitClear 分析了 6.23 亿行代码变更，发现重构量下降了 70%，代码块重复增加了 81%。

这些数字讲的其实是一件事：AI 写得快，写得像，但不写得好。

更微妙的问题出在认知上。METR 在 2025 年做过一个随机对照实验——让资深开发者用 AI 完成复杂任务。结果：实际慢了 19%，但参与者自认为快了 20%。METR 后来在 2026 年 2 月更新说，后续数据因选择偏差不可靠，正在重新设计实验。

连测量 AI 对生产力的真实影响这件事本身，都还没有可靠的结论。

## 提交成本为零，审核成本不变

Marsh 在播客里还有一个更重要的观察。

他说的是开源社区正在面临的困境："提交一个看起来像那么回事的 PR 的成本已经降到了零，但审查和核实它的成本保持不变，而且非常高。"

cURL 的漏洞悬赏计划在今年 1 月关了。创始人 Daniel Stenberg 写了篇博客解释：AI 生成的漏洞报告把确认率从 15% 打到了不足 5%。维护者被海量"看起来像真的一样"的提交淹没，甄别成本远超悬赏本身的价值。

这是 AI 编程的深层悖论：生产代码的效率暴涨，但判断代码好坏的成本一点没降。AI 压缩了"制造"的成本，放大了"甄别"的价值。

Addy Osmani，Google 的工程总监，说过一句很直白的话："AI writes code faster. Your job is still to prove it works."Zig 团队更极端——完全禁止 LLM 写的代码进入项目。

不是他们在反技术。是他们在算一笔账：写代码很少是程序员工作里最值钱的部分。判断力才是。

## Linus 的态度演变

Linus Torvalds 在过去两年里对 AI 的态度经历了多次调整。2024 年 8 月他说 "90% 的 AI 营销是炒作"。2025 年 11 月说 vibe coding 对新人入门是好事。2025 年 12 月开始转向——"I'm a huge believer in using AI to maintain code"。到 2026 年 5 月拉响警报，说安全列表已经失控。然后在 6 月的孟买开源峰会上，给出了他迄今为止最完整的表态。

"我希望它创造的生产力已经超过它消耗的了。"这是他 6 月在孟买说的。注意措辞——不是"它已经超过了"，是"希望它已经超过了"。他对此没有十足把握，但判断方向是正的。

他在 5 月的明尼阿波利斯场说过一句话。"看到有人说 99% 的代码是 AI 写的，我就来气——我保证他们 100% 的代码是编译器生成的，但他们从不这么说。"

这是一个只有 Linus 才能做出的类比。编译器把你的 C 代码翻译成机器码，它产出了 100% 的机器指令，但没有人说软件是"编译器写的"。AI 在编程工具链里的位置，本质上和编译器是一样的——它是翻译层，不是作者。你让编译器生成机器码的时候不会说"我的程序是编译器写的"，那为什么 AI 生成代码的时候要说"我的程序是 AI 写的"？

但他也不是在给 AI 编程唱赞歌。孟买场他抛出了一个更准确的比喻：AI 做的是"创可贴式补丁"。

"它们可能修复了眼前的问题，但同一类 bug 还在走廊里等着，从另一个地方跳出来打你。"

这句话说出了 AI 代码最致命的局限：它擅长修复症状，不理解病因。它能看到这个函数有问题，但看不到设计层面的缺陷——那个让你不得不在七个地方打补丁而不是改一处的结构性问题。LLM 没有系统视野。它不具备工程直觉。

所以 Linus 强调了一个前提：用 AI 找到 bug 之后，你必须让一个人类参与——"人类要充当一种来回的过程"（act as a kind of back-and-forth）。不是 AI 发现 bug 然后人类接受，是 AI 发现线索然后人类判断。

## 判代码比写代码更难

Charlie Marsh 说的是：最懂 AI 工具的人，自己写的 AI 代码也过不了团队的信任关。Linus 说的是：AI 在工具链里的位置和编译器一样重要，但它的产出仍然需要人类的判断力来兜底。数据说的是：用得越多，信得越少，代码在变多，质量在变差。

三条线交汇在同一个点上——程序员最有价值的技能，从来不是敲键盘的速度。

过去几十年，这个行业一直有一种叙事：编程就是写代码。写得越多越厉害，手速越快越值钱。但做过三年以上工程的人大多知道，写代码在真正的工作量里大概只占 20%。剩下的时间你在干什么？

- 理解需求
- 设计架构
- 评估 trade-off
- 读别人写的代码
- 判断哪个方案更不容易在未来爆炸

这些事，没有一个靠"写得快"能解决。

现在 AI 把那个 20% 的效率提升了十倍甚至几十倍——一个原型可以在一个下午跑通，一个内部工具可以"一行代码都不读就发布"。但剩下的 80% 呢？AI 写出来的架构方案你敢不敢直接用？它在七个文件里打了创可贴，你看不看得出来？它建议引入一个新的依赖，你知不知道这个依赖会在半年后的版本更新里炸掉你的 CI？

判断力从来都是程序员最稀缺的资源。AI 只是让这件事变得更明显了。

某种程度上，AI 编程不是在消灭程序员的工作——它是在重新定义"程序员的工作"到底是什么。写完一个循环、调通一个接口、搭起一个 CRUD——这些从来就不是程序员的核心价值，它们只是实现价值的路径。当这些路径被 AI 削平了，那些原本藏在路径下面、不太容易看到的东西就浮上来了。

审美。直觉。对系统复杂性的敬畏。

Linus 在孟买场说过一句话，被他讲 10x 效率时的那股满不在乎盖过去了。"当你有 3500 万行代码的时候，没有人能真正理解全部。"他自己已经不怎么看代码了，他的工作是判断——判断哪条路是错的，判断哪个方向值得走，判断哪个 patch 会引入比它解决的问题更大的麻烦。

3500 万行代码，没有人能读完。但有人必须判断。

这大概就是程序员价值迁移的方向。不是从写代码变成不写代码，是从"写代码"变成"判代码"。你能不能判断 AI 写的代码对不对、好不好、适不适合这个系统——这些问题的答案，决定了你的工作在五年后值多少钱。

Charlie Marsh 的团队不信任他的 PR，不是因为他不厉害了。是因为代码从来就不等于"写得像那么回事"。代码等于"在这个系统的这个位置，做这件事的代价最小且不会带来未来的麻烦"。这后半句，AI 暂时还看不懂。

你看得懂。

---

*参考来源：*

- Andrej Karpathy 原推: https://x.com/karpathy/status/1886192184808149383
- Wikipedia — Vibe Coding: https://en.wikipedia.org/wiki/Vibe_coding
- GitClear — The AI Code Quality Maintainability Gap 2026: https://www.gitclear.com/the_ai_code_quality_maintainability_gap
- CodeRabbit — State of AI vs Human Code Generation: https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
- Stack Overflow 2025 Survey: https://survey.stackoverflow.co/2025/ai
- METR — Uplift Update (Feb 2026): https://metr.org/blog/2026-02-24-uplift-update/
- InfoQ — uv 创始人 Charlie Marsh 访谈: https://www.infoq.cn/article/katE2jJKMX7FaGskhvRL
- The Peterman Pod (原播客): https://youtu.be/Iw65FD4MGgs
- 播客文字稿: https://www.developing.dev/p/openai-eng-and-dev-tools-founder
- OpenAI 收购 Astral 公告: https://openai.com/index/openai-to-acquire-astral/
- InfoQ — Linus Torvalds 2026 访谈全文编译: https://www.infoq.cn/article/11fNtPYf59T76fyQkiPa
- 36氪 — Linus 再谈 AI: https://www.36kr.com/p/3885475579211783
- LWN — Linus Torvalds at OSS India 2026: https://lwn.net/Articles/1073761/
- The New Stack — Torvalds on AI Programming Productivity: https://thenewstack.io/torvalds-ai-programming-productivity/
- OSS India 2026 视频: https://www.youtube.com/watch?v=YKkEe-PxW10
- OSSNA 2026 视频: https://www.youtube.com/watch?v=fi29pfLcW4I
- Veracode — GenAI Security: https://www.veracode.com/
- cURL Bug Bounty 关停公告: https://daniel.haxx.se/blog/2026/01/26/the-end-of-the-curl-bug-bounty/
