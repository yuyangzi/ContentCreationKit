# DeepSeek 招不到人——AI人才战争进入下半场

> **导读**：DeepSeek Harness部门负责人崔添翼在线直呼"缺人缺疯了"——一口气开放研究员、工程师、产品经理三类岗位，连续一个多月没招满。这背后不是简单的扩招，而是DeepSeek从大模型竞争向Agent基础设施的战略转向。

2026年6月22日，量子位报道了一条看似常规的招聘新闻：DeepSeek Harness部门负责人崔添翼再次在线直聘。这不是他第一次发帖——从5月开始，他已经在各种渠道"贴小广告"了。

"每天都在面试，"他在X上说，"缺人缺疯了。"

岗位有三类：Harness研究员（实习和全职）、Harness工程师（实习和全职）、Harness产品经理（全职）。工作地点北京和杭州。一轮笔试加三轮面试，崔添翼自己就是终面。

连续一个多月没招满——这件事本身就值得琢磨。BOSS直聘上DeepSeek当前开放约50个岗位，Harness团队占了其中相当一部分，说明这不是常规人员补充，而是一个新团队在从零组建。

---

## 郭达雅出走，Harness才来

郭达雅——DeepSeek-Coder、V3、R1的核心贡献者，GRPO算法的发明人，引用超38,000次。中山大学博士，与微软亚洲研究院联合培养。在DeepSeek负责代码智能和推理方向。

2025年10月，郭达雅决定离职。据晚点报道，核心原因不是钱——虽然他的字节薪资总包"近亿元"（四年归属，含现金、期权和豆包股），但字节副总裁李亮公开否认了这个数字。更深层的原因在于方向：他想做Agent，但当时DeepSeek内部的优先级不在这里。

:::timeline[郭达雅离职前后]
2025年10月: 郭达雅决定离职
2026年3月: 他正式离开，加入字节跳动Seed团队担任Agent方向负责人之一，职级L8。同月，前Jane Street量化工程师崔添翼（ACM ICPC亚洲区域赛6次金牌）加入DeepSeek
2026年5月: DeepSeek正式组建Harness团队。资深研究员陈德里在X上公开确认，正在"从零构建CodeHarness"，内部对标Claude Code
:::

顺序是反过来的。不是先有Harness团队再有人离开，而是有人因为Agent优先级不够先走，公司才紧急组建了这个团队。

郭达雅不是孤例。过去一年，DeepSeek至少5名核心研究员离职：

- **王炳宣**——基座模型核心作者，去腾讯混元
- **罗福莉**——V3核心贡献者，据媒体报道被雷军以千万年薪挖至小米（小米及本人未确认）
- **魏浩然**——OCR系列核心作者，去向未公开
- **阮翀**——多模态核心贡献者，去元戎启行任首席科学家
- **郭达雅**——代码智能和推理核心贡献者，去字节

五个人覆盖了基座模型、推理、OCR、多模态四条核心技术线。

以DeepSeek约150到160名正式员工的体量、极度扁平的组织（仅两层——梁文锋和研究员，决策自下而上，梁文锋深度参与技术讨论但不是一人拍板），核心人员的流失对特定技术线的研发节奏会有阶段性影响。

> [!important] 判断走在公司前面
> 郭达雅的案例尤为特别。从结果回看，他的方向判断走在了公司战略前面——他离开的理由，恰好变成了公司后来押注的方向。

---

## 模型是发动机，Harness才是整车

DeepSeek在招聘公告里写了一个公式：**Model + Harness = Agent**。

这句话不是在玩文字游戏。它在表达一个正在形成的产业共识——做大模型和做Agent，已经不是同一件事。

Harness涵盖的是什么？模型之外的所有基础设施：

- 上下文管理
- 长期记忆
- Subagent和Multi-Agent协同
- 自进化Agent
- 工具调用与规划
- MCP协议集成

> [!tip] 理解 Harness
> 做个类比：Agent是汽车，模型是发动机。你造出了最好的发动机，不代表你造得出能上路的车。方向盘、变速箱、刹车、悬挂——这些不是发动机的附属品，是另一套工程体系。

:::steps[Harness团队三大岗位]
研究员负责"定义问题"——上下文管理怎么做？长期记忆怎么设计？Subagent怎么配合？任职要求是2年以上科研经验、CS领域论文发表，并且是AI Agent的高强度用户
工程师负责"实现能力"——技术架构和选型，和研究员配合保证系统能跑、能迭代、能服务真实用户
产品经理负责"连接"——连接研究员、工程师、开源社区和用户，定义产品方向，管理社区反馈
:::

研究→工程→产品→社区。这是Agent基础设施的完整研发链。问题是，能做全链条的人，太少了。

---

## 48条新闻，一个人都招不到

崔添翼在面试的时候，外面是这样的：2026年6月第三周，Agentic.ai News单周追踪了48条Agent产品、模型和研究新闻。不是"最近很热"——是每周48条，每一条都是产品发布、迭代或融资。

Anthropic这边，Claude Code已经进入"loop engineering"阶段。创始人Boris Cherny从2025年11月起就没手写过代码，管理着"数百到数万"个AI agents。

工程负责人Fiona Fung说，工程师每季度产出是此前的8倍——"coding is no longer the bottleneck"。Fortune同期发了篇文章说Claude Code让员工的工作变成了"lonely experience"——全员用agent写代码，人际协作反而变少了。这不是降温，是副作用。

几个数字：Anthropic公司总营收年化运行率从90亿美元涨到470亿美元，只用了5个月。其中Claude Code单品年化营收约25亿。公司估值也一路攀升——链上Pre-IPO隐含估值一度到1.2万亿美金，5月官宣的Series H估值是9650亿。

OpenAI Codex已经开放第三方模型接入，国产模型可通过兼容接口直连。

国内呢？微信小微Agent 6月20日起灰度上线，14.32亿月活用户。蚂蚁国际开源了AMP协议，全球首个移动端Agent支付框架。小米MiMo Code以MIT协议开源——三个动作，覆盖了消费级Agent、金融Agent和开发工具三条赛道。

---

## 抢的不是"会写代码的人"，是"知道要做什么的人"

回到最开始的问题：崔添翼为什么招不到人？

不是因为市场上没有AI人才。过去两年，会用模型的人太多了——写prompt的、搭RAG的、做fine-tune的。但Harness要的不是会用模型的人。

> [!important] 三种稀缺能力
> 研究品味——知道什么问题值得解决；工程能力——能把方案实现到生产级别；产品思维——理解用户到底要什么。这三种能力在同一个人身上同时出现——以目前的供给来看，极度稀缺。

更关键的是，AI行业的竞争逻辑变了。

:::compare[大模型时代 vs Agent时代]
大模型时代: 竞争主体是"谁能训练最大的模型" | Agent时代: Agent要跑在真实环境里
只需要顶尖的研究员——懂架构、懂训练、懂scaling law | 需要一个团队，里面的人既懂研究又懂工程还懂产品
不需要产品经理，因为产品就是API | 这三层之间的接口太紧密——做研究的人不理解工程约束，方案根本没法部署
:::

所以崔添翼三类岗位同时招，一个多月招不满——不是DeepSeek要求太高，是市面上根本就没什么符合条件的人。

有个细节：郭达雅2023年就想做Agent了。他知道这件事重要，但当时没有人给他资源。等他走了，DeepSeek才发现不对——Agent不是"以后再说"的事，是现在就必须做的事。于是紧急组队，全力押注。

问题是，已经晚了多久？Claude Code由AI编写已持续超过7个月。Fiona Fung说产出8倍。微信小微已经灰度上线。这些不是"竞争对手也在做"，是"竞争对手已经把东西做出来了"。

DeepSeek的优势在于开源社区的影响力和技术品牌——这个确实在。但Harness不是靠品牌能追的。它需要大量工程实践和产品化经验的堆积——这些东西，不是多招几个研究员能解决的。

---

## 不是"谁会训练"，是"谁能驯服"

大模型时代抢研究员。Agent时代抢的是能"驯马"的人——能把模型套上Harness，让它真的能干活。

这场竞争的结果不取决于谁家的模型跑分更高。取决于谁先建起了能让模型稳定运行的Agent基础设施。GKE Agent Sandbox每秒三百个沙箱也好，Claude Code一个月迭代几千次也好，微信小微直接触达14亿用户也好——到最后比的不是模型，是Harness。

DeepSeek知道了这件事，正在追。但崔添翼还在面试，而外面的世界，一周48条。

> [!warning]
> 这件事，不是有钱就能快起来的。

---

*参考来源：*

- SCMP：[DeepSeek's Harness team races to recruit talent in booming AI agent market](https://www.scmp.com/tech/big-tech/article/3358077/)（2026.06.23）
- SCMP：[DeepSeek recruits former Jane Street engineer to catch up on AI agents, revenue race](https://www.scmp.com/tech/big-tech/article/3354113/)（2026.05.19）
- 晚点LatePost：[DeepSeek 95后研究员郭达雅近亿元年薪入职字节](https://finance.sina.com.cn/wm/2026-04-16/doc-inhuszrw2763097.shtml)（2026.04.16；字节官方否认该数字）
- 36氪：[DeepSeek缺Agent人才缺疯了，负责人各种贴广告](https://www.36kr.com/p/3863982620923141)
- PCNow：[DeepSeek第一批核心研究员相继离职](https://pcnow.cc/p/3zZp57b693.html)（2026.04.21）
- Fortune：[Anthropic engineering leader says Claude Code made employees' work a 'lonely experience'](https://fortune.com/)（2026.06.23）
- Lenny's Newsletter：[Building the most AI-pilled engineering team — Fiona Fung 访谈](https://www.lennysnewsletter.com/)（2026.06.21）
- IT之家：[微信AI助手"小微"灰度上线](https://www.ithome.com/0/966/534.htm)（2026.06.20）
- 36氪：[实测微信小微](https://36kr.com/p/3865697138283521)（2026.06.24）
- BusinessWire：[Ant International Launches Open-Sourced Agentic Mobile Protocol](https://www.businesswire.com/)（2026.04.28）
- PANews：[Everything Beyond the Model Is Harness: DeepSeek Enters the Fray](https://www.panewslab.com/en/articles/019eede8-f90e-746d-929c-82a7c608db11)
- Digg：[DeepSeek AI Agent Harness Team Hiring](https://digg.com/tech/u87bzwhz)（2026.06.21）
- 崔添翼 X 账号：[招聘原始信息](https://x.com/tianyi/status/2068652453797724562)
