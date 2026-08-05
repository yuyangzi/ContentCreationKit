# 当界面不再持久：生成式 UI 如何改写 Agent 与人的交互边界

> **导读**：上一篇文章讲了 AG-UI 协议——Agent 后端和前端的通信标准。但协议只是管道。管道里流的是什么？当 Agent 不仅能发文本，还能发组件描述、发完整界面时，"通信"这个词本身就不够用了。本文讨论生成式 UI 的架构哲学：三种控制模式、短暂性界面的意义、以及这对前端开发范式意味着什么。

---

2025 年 6 月，Andrej Karpathy 在推特上回应了一个 LLM 的 GUI 演示，附了一句耐人寻味的评价："像一辆无马车厢——它在新的范式里精确地复制了旧的界面。"他要说的不是这个 Demo 做得不好，而是我们正处在一个尴尬的过渡期：Agent 已经能动态生成界面了，但这些界面看起来还是我们熟悉的样子（按钮、表单、图表），和三十年前的 GUI 没什么区别。

这正是生成式 UI 这个领域的核心张力所在。技术能力已经越过了临界点，但我们对"界面应该长什么样"的想象，仍然被旧范式的引力牢牢抓住。

---

## 聊天框的尽头

上一篇文章讨论 AG-UI 协议时提到一个现象：大多数 Agent 应用把聊天窗口当作唯一的交互界面。Agent 执行工具、读写文件、生成代码——所有这些活动的结果都被硬塞进一个聊天气泡里，用 Markdown 渲染。

这不是设计选择，是技术债。LLM 默认输出文本，前端默认渲染文本，两者之间没有中间地带。于是信息被迫坍缩成线性文字流——哪怕是需要表格对比的数据、需要可视化的趋势、需要分步确认的操作流程。

Google Research 在 2025 年 11 月发表的论文 *Generative UI: LLMs are Effective UI Generators* 里做了一个实验：让用户对比 AI 生成的纯 Markdown 回答和 AI 生成的交互式 HTML 界面。结果不太令人意外——用户对 HTML 界面的偏好率高达 83%。

83% 不是一个需要精细解读的数字。它说的是一句大白话：当信息本身具有结构时，用结构化界面呈现天然比用纯文本好。表格比段落更擅长对比，图表比数字更擅长趋势，表单比指令更擅长引导操作。聊天框的问题不在于它"不够好"，而在于它在很多场景里往往就是错误的媒介。

于是生成式 UI 要回答的问题变得清晰了：**当 Agent 不只是"回答问题"，而是"完成任务"时，它需要什么形态的界面与之匹配？**

---

## 三种模式：控制权如何重新分配

CopilotKit 在 2026 年的开发者指南里提出了一个实用的分类框架，把生成式 UI 按"谁控制什么"切成了三种模式。Open-UI 在同年 6 月的状态报告里进一步把这个框架提炼为两个独立维度：**传输**（UI 出现在哪张画布上）和**生成**（Agent 输出什么来填充这张画布）。

但先不谈技术维度，先从直觉上理解这三种模式的区别。

### 静态模式：Agent 选组件，前端决定一切

这是最保守的一端。前端团队把所有可能用到的组件提前建好（图表、表单、审批卡片、进度面板），Agent 的任务只是从目录里挑一个、填上数据。Agent 不决定布局，不决定样式，甚至不决定"这个场景该用什么组件"——它只是给某个已注册的工具调用返回一个组件选择。

你在 CopilotKit 里用 `useFrontendTool` 做的事，就是这个模式。工程上它几乎零风险：没有代码生成，没有沙箱，没有安全审计的额外负担。代价是每出现一个新的答案形态，就需要一个新组件——目录靠 PR 增长，不靠 prompt。

这种模式适合答案形态有界的场景：客服面板、财务仪表盘、预设的工作流审批。一旦布局空间是开放的，它的约束就会变成瓶颈。

### 声明式模式：Agent 编排布局，前端执行渲染

这是当前大多数生产系统实际落地的地方。Agent 不直接输出 HTML/CSS/JS，而是输出一个结构化的 UI 描述（A2UI 的 JSON 树、Open-JSON-UI 的组件 spec、OpenUI Lang 的面向行 DSL），前端收到后，用自己的组件库和设计系统渲染成真实界面。

控制权的分配在这里变得微妙。**前端团队仍然拥有设计系统**（颜色、间距、字体、品牌调性），所有这些都不由 Agent 决定。**但 Agent 拥有布局权**，它决定这个场景应该用卡片还是表格、数据应该横排还是纵排、是否需要交互控件。

这种"我定规则、你定编排"的分工，是 2026 年生成式 UI 的主流平衡点。它的安全性来自一个简单的事实：Agent 只能渲染组件目录里存在的组件。组件目录就是权限模型——不存在的组件，Agent 编不出来。

Google 的 A2UI 走这条路。Agent 输出 `createSurface`、`updateComponents`、`updateDataModel` 三种消息，渲染器按目录映射执行。Vercel 的 json-render 也走这条路，但它的不同之处在于同一套 spec 机制可以渲染到不同目标（Web 仪表盘、邮件、PDF 甚至终端界面）。

这意味着格式选择不只是工程偏好，它是成本选择。每省一个 token 的格式语法，就省一份模型推理的钱——在服务数百万次 UI 生成请求的规模下，这是财务报表上看得见的一行。

### 开放式模式：Agent 写界面，前端做容器

这是最激进的一端。没有组件目录，没有 schema 约束。Agent 直接输出完整的 HTML/CSS/JS，前端在一个沙箱化的 iframe 里渲染它。Google Gemini 的 Dynamic View 是这个模式的生产旗舰，CopilotKit 的 `useComponent` 加 LangGraph Agent 也能做到（Agent 生成 Three.js 的 3D 场景、D3 的力学模拟、算法可视化的完整交互页面）。

自由度的代价跟着就来了。生成的 HTML 不继承应用的设计令牌，视觉一致性需要额外处理。沙箱隔离了安全风险，但也隔离了与宿主应用的数据交互。延迟更高——一份完整页面的 token 量远高于声明式 spec。输出在不同运行之间还有波动，同样的 prompt，两次生成的界面可能不一样。

Open-UI 提出了一个聪明的混合方案：在声明式目录里注册一个 `GeneratedView` 组件，它的唯一 prop 是一段 Agent 生成的 HTML 字符串。正常情况下走目录约束的声明式路径，只有在遇到目录真的覆盖不了的布局时才打开这个"逃生舱口"。安全审计也只需要盯这一个组件。

三种模式不是互斥的选项，而是一个连续光谱。大多数生产系统在光谱上占据不止一个点。

### 一图胜千言：三种模式的实际形态

拿"季度销售数据查询"这个场景来看三种模式是怎么落地的。一个用户在聊天框里对 Agent 说"帮我看看 Q1 各区域的销售情况"，Agent 后端执行了数据查询工具。三种模式的输出长这样：

**静态模式**：前端提前注册了一个 `RevenueChart` 组件，Agent 只是通过工具调用触发它，填上数据：

```JavaScript
// Agent 后端返回的工具调用
{ "toolCall": "render_ui", "component": "RevenueChart",
  "props": { "regions": ["华东","华南","华北","西部"],
             "revenue": [120, 95, 80, 45] } }

// 前端直接用预定义的 React 组件渲染
// <RevenueChart regions={...} revenue={...} />
```

**声明式模式**：Agent 输出一份 A2UI 的组件描述，告诉前端"用 Card 包裹，里面放一个 Heading 和一个 BarChart，数据从 `/data/series` 路径读"：

```JSON
{"createSurface": "s1", "rootId": "c0"}
{"updateComponents": [
  {"id":"c0","kind":"Card","children":["c1","c2"]},
  {"id":"c1","kind":"Heading","props":{"text":"Q1 各区域营收"}},
  {"id":"c2","kind":"BarChart","props":{"dataPath":"/data/series"}}
]}
{"updateDataModel": {
  "/data/series": [{"region":"华东","value":120}, ...]
}}
```

**开放式模式**：Agent 直接吐出一段完整的 HTML，前端把它丢进一个沙箱化的 iframe 渲染。代码可能是 200 行，也可能是 2000 行——前端不管里面是什么，只管把它隔离好。

三种模式的 token 开销差距在规模上会被放大。以 Open-UI 的基准测试为例：七个常见场景（简单表格到电商产品页），声明式 DSL（OpenUI Lang）总共消耗 4,800 token，而等效的 JSON spec 格式（json-render）消耗 10,180 token，多了 112%。如果是开放式模式直接输出 HTML，token 量还要再翻 5 到 10 倍。在每分钟服务数千次 UI 生成请求的场景下，格式选择就是成本选择。

---

## 最佳实践

基于社区讨论和生产部署经验，以下五条是当前可操作的工程建议：

1. **从声明式开始，不要一上来就开放式。** 组件目录约束不是限制，是安全基座。Agent 只能选择目录里的组件，意味着你不需要审计"Agent 可能生成什么奇怪的代码"。目录就是权限模型。

2. **注册组件时，描述比 schema 重要。** Agent 是通过文字描述理解"这个组件能干什么"的，不是通过 TypeScript 类型。组件注册时写清楚它的用途、适用场景和不该被使用的场景。一个模糊的组件描述比没有这个组件更危险。

3. **状态反馈循环不可跳步。** 用户与生成组件的每次交互（筛选、切换、编辑）都需要回写 Agent 上下文。没有反馈循环，Agent 的下一次响应基于的是过期状态。这比组件渲染本身更容易被忽视，但后果更严重。

4. **元数据优于原始数据。** Agent 的任务是决定"用什么组件渲染"，不是"把完整数据集吐出来"。让 Agent 输出渲染指令（组件名 + 数据引用路径），由客户端自行获取真实数据。这既省 token，也避免了 Agent 把数据编错的风险。

5. **"逃生舱口"集中管理。** 如果你需要开放式生成（Agent 输出原始 HTML），把它封装成目录里的一个 `GeneratedView` 组件，而不是让整个应用切换到开放模式。安全审计只需要盯这一个组件，Agent 的默认路径仍然走目录约束。

---

## 常见误区

1. **"AG-UI、A2UI、MCP Apps 是竞争关系，三选一。"** 这是最常见的误解。它们处于协议栈的不同层——AG-UI 负责传输，A2UI 和 MCP Apps 定义载荷格式。同一个 Agent 可以通过 AG-UI 管道输出 A2UI 载荷给自己的应用，同时通过 MCP Apps 向外部分发。大多数生产系统三者同时用。

2. **"生成式 UI 等于让 LLM 直接输出 HTML。"** 开放式 HTML 生成确实存在，但它不是唯一的、也不该是默认的模式。声明式生成（Agent 编排组件目录）在 2026 年的生产采用率明显高于开放式——它更安全、更省 token、更容易保证视觉一致性。

3. **"生成式 UI 是前端工程师的替代品。"** 正好相反。它把前端工程师的工作从"写每个页面的 JSX"推向了"设计 Agent 能安全使用的组件目录、建立验证流水线、管理前后端状态同步"——不是更少的工作，是更上游的工作，这需要比传统前端更深的设计系统和架构能力。

---

## 短暂性的哲学：当界面用完就消失

前面讨论的是"怎么生成"，但更深层的问题是：**这些被生成出来的界面，应该活多久？**

传统 UI 的世界观里，界面是建筑物。你花几个月设计、开发、测试，然后它上线，稳定运行，成为产品的一部分。用户学习它，习惯它，依赖它。持久性是默认假设。

生成式 UI 翻转了这个假设。Agent 为一个特定任务生成了界面（比较三个航班、可视化一组销售数据、生成一个审批表单），任务完成，界面溶解，下一个任务催生下一个界面。

Google 论文把这种模式叫做"无限短暂界面"（infinite ephemeral interfaces）：每个用户意图都获得一个定制的、用完即弃的界面。Karpathy 说的"无马车厢"之所以贴切，是因为我们现在生成的短暂界面还在模仿持久界面的样子——但它的本质已经不同了。一架在机场现造、飞完就拆的飞机，和波音 747 不是同一种东西，哪怕它们长得有点像。

设计界对这个概念的反应比工程界更早。Nielsen Norman Group 在 2024 年就提出了"结果导向设计"（outcome-oriented design）的概念：设计师的角色从"画组件"变成"定义约束和护栏"——哪些信息必须展示、哪些可以展示、哪些绝对不能展示。界面不再是最终交付物，界面变成了 AI 在约束条件下即时组装的临时产物。

"短暂界面"在学术上可以追溯到 2013 年。Döring、Sylvester 和 Schmidt 在论文 *A Design Space for Ephemeral User Interfaces* 里讨论过用易逝材料（水、火、肥皂泡）构建的界面——这些界面不是为了持久，而是在当下的交互瞬间有意义。当时这还是一种实验艺术，没有 AI 什么事。现在 AI 把这个概念从材料实验推向了软件工程的日常。

但短暂性不只是哲学概念，它有具体的工程含义。

一个临时生成的航班对比表需要和应用的视觉语言保持一致，但如果你为每个任务都从头生成 HTML，品牌一致性天然得不到保证——这就是为什么声明式模式（Agent 只能用既定组件库编排）比开放式模式在生产中更受欢迎。短暂不能以牺牲可信度为代价。

用户与生成组件的每次交互都需要回写 Agent 的上下文窗口，这正是前面最佳实践里说的状态反馈循环。生成式 UI 在设计层面的问题是"短暂性的哲学"，在工程层面的问题却是"分布式状态同步"——Agent 的世界模型和用户看到的界面必须保持同步，这是短暂性落到工程上的真正代价。

---

## 前端工程师变成了什么

如果 Agent 能选组件、编排布局、甚至写界面了，前端工程师的价值在哪？

这个问题在 2025-2026 年的社区讨论里反复出现，回答也在逐渐收敛。一致的方向是：**前端工程师的角色向上移动了。**

Brad Frost（Atomic Design 的作者）在 2025 年底的一次讨论中把这个转变说得很直白：设计系统以前是给人用的文档，现在它需要变成**机器可读的基础设施**。Agent 需要一个清晰的组件目录，每个组件有明确的 schema、使用示例和约束条件。Agent 不会猜你希望它用什么字号，它只会用你注册给它的东西。

这就是新的前端工作：不是写单个页面的 JSX，而是**设计 Agent 能安全使用的组件目录**。组件要足够通用以覆盖大多数场景，又要足够约束以防止 Agent 做出奇怪的组合。目录太大会降低 Agent 选择正确的概率，目录太小会限制 Agent 的表达能力——这个平衡本身就是一种新的设计技能。

验证流水线也跟着变了。传统 CI 跑的是 lint、单元测试、E2E。Agent 生成的 UI 需要额外一层验证：

- schema 校验：输出的 JSON 结构合法吗
- 组件白名单：引用的组件存在吗
- 渲染器兼容性：不同渲染目标的行为一致吗
- Agent 的恢复能力：客户端拒绝一个布局时，Agent 能不能给出降级方案

状态管理的位置也变了。传统的 SPA 里，状态在前端。Agent 驱动的应用里，状态需要在前端和 Agent 上下文之间双向流动。CopilotKit 的 shared state、AG-UI 的 STATE_DELTA 事件、A2UI 的 updateDataModel——这些机制解决的是同一个问题：让 Agent 的世界模型和用户看到的界面保持同步。

有一种说法把这个转型总结得很到位：**从写 UI 变成引导 UI 的生成**。听起来像降级，其实是升级——你不是在做更少的事，你是在做更上游的事。

---

## 协议栈：管道和载荷的分工

理解生成式 UI 的架构，需要把"谁来运"和"运什么"分开。

AG-UI 是管道。它定义了一套标准化的事件类型（`TEXT_MESSAGE_CONTENT`、`TOOL_CALL_START`、`STATE_DELTA` 等），让 Agent 后端能把各种输出事件流式推给前端。它是传输层，不关心事件里装的是文本还是 UI 描述。

A2UI、Open-JSON-UI、MCP Apps 是载荷。它们定义 UI 描述的具体格式——JSON 树、组件 spec、iframe 资源引用。管道不关心载荷是什么，载荷不负责传输。

这个分层的妙处在于互操作性。同一个 Agent 可以用 AG-UI 管道，同时输出 A2UI 载荷给自己的应用，输出 MCP Apps 载荷给 ChatGPT——管道不变，载荷根据目标宿主切换。

截至 2026 年 6 月，支持 AG-UI 集成的框架已覆盖大部分主流 Agent 生态：LangGraph、CrewAI、Google ADK、Microsoft Agent Framework、Claude Agent SDK、LlamaIndex 等。OpenAI Agent SDK 和 AWS Bedrock Agents 的集成也在推进中。据 CopilotKit 官方自述，已有超过 10% 的财富 500 强公司在用它做 Agent 的 UI 层（该数据为厂商自报，未见独立第三方统计）。

MCP Apps 则在解决另一个问题：如果你的 Agent 需要出现在别人的宿主里（比如 ChatGPT 或 Claude Desktop），你怎么把界面送进去？答案是 `ui://` 资源引用：MCP 工具的返回结果里带一个 UI 资源的 URI，宿主在沙箱化的 iframe 里渲染它。这种方式和 AG-UI 不是竞争关系——同一个 Agent 可以同时通过 AG-UI 连接自有应用、通过 MCP Apps 分发到外部宿主。

---

"生成式 UI"听起来像一个终结态——界面的终极形态。但实际上，2026 年的生成式 UI 更像一个中间态。我们正在把 AI 的能力嫁接到现有的 UI 范式上，出来的产物（生成的表单、动态的图表、临时的仪表盘）仍然在模仿"持久界面"的样子。

真正值得问的不是"Agent 能不能生成 UI"，而是"当 Agent 能生成 UI 之后，我们还需要'UI'这个概念吗"。也许未来的交互形态根本不会走"界面"这条路——可能是纯语音、可能是空间手势、可能是某种我们还没有名字的东西。生成式 UI 作为概念，本身可能就是马车在想象汽车时能画出的最远的图景。

但在这个过渡期里，理解它的架构哲学仍然重要。不是因为当前的方案是最终答案，而是因为它暴露了旧范式裂缝的位置——持久性不再是默认假设，控制权正在重新分配，前端工程师的工作内容正在从"我写什么界面"变成"我让 Agent 用什么语言描述界面"。

而协议栈的分层（管道和载荷的分离、传输和生成的独立决策）是这场过渡里最稳固的工程洞察。不管你用不用 AG-UI、选不选 A2UI，理解了"把通信和内容分开"，就理解了生成式 UI 架构的一半。

---

*参考来源：*

- Google Research, "Generative UI: LLMs are Effective UI Generators", arXiv:2604.09577（2026.02 上 arXiv，官网首发 2025.11）— [https://generativeui.github.io](https://generativeui.github.io)
- CopilotKit, "The Developer's Guide to Generative UI in 2026" — [https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026](https://www.copilotkit.ai/blog/the-developer-s-guide-to-generative-ui-in-2026)
- Open-UI (Thesys), "The State of Generative UI in 2026: Transports, Formats, and Tradeoffs", 2026.06 — [https://www.openui.com/blog/state-of-generative-ui-report](https://www.openui.com/blog/state-of-generative-ui-report)
- sunpeak, "MCP Apps vs A2UI: Which Agent UI Standard Should You Use?", 2026.06 — [https://sunpeak.ai/blogs/mcp-apps-vs-a2ui](https://sunpeak.ai/blogs/mcp-apps-vs-a2ui)
- Nielsen Norman Group, "Generative UI and Outcome-Oriented Design", 2024.03 — [https://www.nngroup.com/articles/generative-ui](https://www.nngroup.com/articles/generative-ui)
- Karpathy, A., Twitter/X, 2025.06.19 — [https://x.com/karpathy/status/1935779463536755062](https://x.com/karpathy/status/1935779463536755062)
- Döring, T., Sylvester, A., & Schmidt, A., "A Design Space for Ephemeral User Interfaces", 2013
- Brad Frost + Chromatic, "Agentic Design Systems in 2026" — [YouTube](https://www.youtube.com/watch?v=Vg78K3t9KYc)
- Medium (iSolutions), "Ephemeral UI in AI-Generated, On-Demand Interfaces", 2025.03 — [https://isolutions.medium.com/ephemeral-ui-in-ai-generated-on-demand-interfaces-81dbc8cd4579](https://isolutions.medium.com/ephemeral-ui-in-ai-generated-on-demand-interfaces-81dbc8cd4579)
- Google Cloud, "What is Generative UI? Building Agent-Powered Interfaces" — [https://cloud.google.com/discover/generative-ui](https://cloud.google.com/discover/generative-ui)
- MarkTechPost, "Beyond the Chatbox: Generative UI, AG-UI, and the Stack Behind Agent-Driven Interfaces", 2026.01 — [https://www.marktechpost.com/2026/01/29/beyond-the-chatbox-generative-ui-ag-ui-and-the-stack-behind-agent-driven-interfaces](https://www.marktechpost.com/2026/01/29/beyond-the-chatbox-generative-ui-ag-ui-and-the-stack-behind-agent-driven-interfaces)
- Towards AI, "The Fluid Interface: A Paradigm Shift to Agent-Driven Experience" — [https://pub.towardsai.net/the-fluid-interface](https://pub.towardsai.net/the-fluid-interface)
- Roger Wong, "Generative UI and the Ephemeral Interface", 2025.11 — [https://rogerwong.me/2025/11/generative-ui-and-the-ephemeral-interface](https://rogerwong.me/2025/11/generative-ui-and-the-ephemeral-interface)
