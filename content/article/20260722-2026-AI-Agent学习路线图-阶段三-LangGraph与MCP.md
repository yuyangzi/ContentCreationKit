---
mode: deep-tech
---

# 从链到图：当 Agent 学会协作——LangGraph 状态机与 MCP 协议拆解

> **导读**：从单Agent的ReAct循环到多Agent协同工作，2026年的技术栈给出了三条主线——LangGraph用图式状态管理取代链式编排，MCP用标准化协议终结工具调用的碎片化，多Agent协作模式从实验走向生产。但标准化引入复杂度，协作引入新的失败模式。本文是系列第三篇，拆解这三个模块的底层逻辑和已知的坑。

## 2026年，Agent学会了协作

2026年7月28日，MCP（Model Context Protocol，模型上下文协议）规范发布了一份代号"RC"的草案更新。

这份草案做了协议设计中少见的事——删掉初始化握手（initialize handshake）、引入无状态会话、用MRTR（Multiplexed Resumable Task Request，多路复用可恢复任务请求）替代SSE（Server-Sent Events，服务器推送事件）。

一个18个月前还被质疑"是否有必要"的协议，此刻已被OpenAI、Google、Microsoft、Apple、AWS五家采纳（来源：MCP 2026-07-28 RC公告），然后推倒重来。

我在2025年初开始碰MCP，体验很诚实——想法好，实现还早。但到了2026年中，生态密度完全不同了：9700万月下载量（来源：MCP官方2025年12月数据），超过10,000个公开MCP Server，Linux基金会旗下的Agentic AI Foundation于2025年12月9日接管项目治理。

LangGraph也在悄悄变成默认选项。Klarna用它在生产环境支撑8500万用户规模的客服系统（来源：Rephrase.it对Klarna LangGraph架构的分析）。37,688个GitHub Star和约6800万月PyPI下载量放在那里（来源：GitHub / PyPI Stats），不是靠营销撑起来的。

这就是"2026 AI Agent学习路线图"第三篇的核心问题：跑通了ReAct循环（阶段一），搭完了RAG和工具调用链路（阶段二）之后，如何让Agent学会协作——和工具协作、和人类协作、和彼此协作。

三个层面的"协作"，对应三个技术模块：

- Agent和工具的协作 → MCP（标准化工具协议）
- Agent和人的协作 → LangGraph的Human-in-the-loop（人在回路中）和Checkpointing（检查点）
- Agent和Agent的协作 → 多Agent编排模式（Supervisor/Handoff/Swarm/Parallel）

---

## 从链到图：为什么Agent需要状态机

LangGraph的核心洞察可以追溯到Yao等人2022年的ReAct论文（arXiv 2210.03629），这篇论文奠定了"推理+行动"交替循环（Reasoning and Acting loop）的基础。但ReAct只定义了步骤内的模式——思考、行动、观察、重复——它没有告诉你怎么管理跨步骤的状态。

这就是LangGraph介入的地方。

LangGraph把Agent抽象成一个有状态的图（Stateful Graph）。三个核心概念：

State（状态）是贯穿整个执行过程的共享数据结构，每经过一个Node（节点），State被更新一版。Node是执行单元——可以是一次LLM调用，一次工具调用，或者一段自定义逻辑。Edge（边）决定Node之间的流转——可以是有条件的分支（conditional edge），也可以是固定顺序（direct edge）。

一个典型的LangGraph工作流看起来不像流水线，更像电路图。Agent思考完之后，可能直接去调用工具，也可能触发人工审核，或者回到思考步骤重新规划。这些回路和分支，用链式结构（LangChain最初的Chain抽象）表达起来很别扭——链的假设是"A→B→C一定按这个顺序走完"。

但Agent不是这样工作的。它能走回头路。它能在中途暂停等待人类确认。它能在几条路径之间动态选择。这些行为本质上是一个状态机——而图是表达状态机的自然方式。

一个最简的 LangGraph 工作流长这样：

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import AnyMessage


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def agent(state: AgentState) -> dict:
    response = llm.bind_tools([search_web]).invoke(state["messages"])
    return {"messages": [response]}


builder = StateGraph(AgentState)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode([search_web]))
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")
graph = builder.compile()
```

这短短十几行代码包含了 LangGraph 的核心抽象——State 承载上下文，Node 执行逻辑，Conditional Edge 控制流转。`tools_condition` 是内置的路由函数：如果最后一条消息包含 `tool_calls`，自动跳到 tools 节点；否则结束。

LangGraph实现这些能力靠两个关键机制：Checkpointing（检查点）和Human-in-the-loop（人在回路中）。

Checkpointing在每次状态更新后自动保存快照，这意味着你可以在多数执行点暂停、回退到历史状态，或者从之前的某个点重新分支。

Human-in-the-loop是在特定Node上插入中断点（interrupt），当执行到达这个节点时暂停，等待人类批准或修改后再继续。

Lyft的案例能说明这种设计在实际场景中的价值。他们用LangGraph和LangSmith搭建了一套客户支持Agent平台，核心架构就是Human-in-the-loop——Agent自动处理常见问题，但当置信度低于阈值或涉及退款/补偿等高敏感操作时，自动转给人工客服。

人工客服看到的不是一个冷冰冰的上下文窗口，而是完整的执行历史——Agent已经做了什么尝试、拿到了什么结果、卡在哪里。

这种"上下文连续性"是链式架构原生无法提供的，因为在链式架构里，每一步的输出只被下一步消费，在中间插入人类等于打断整个链（来源：LangChain官方博客，Lyft案例）。

Human-in-the-loop 的代码实现依赖两个原语——`interrupt()` 暂停执行，`Command(resume=...)` 恢复执行：

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command


def approval_node(state: AgentState) -> Command:
    # suspend and wait for human input
    decision = interrupt({
        "question": "是否批准此操作？",
        "context": state["messages"][-1].content,
    })
    if decision.get("approved"):
        return Command(goto="execute")
    return Command(goto="respond")


graph = builder.compile(checkpointer=MemorySaver())

# 第一次执行：遇到 interrupt 暂停
config = {"configurable": {"thread_id": "session-1"}}
stream = graph.stream_events({"messages": [msg]}, config, version="v3")

# 程序检查 stream.interrupted，获取中断信息，等待人工响应
# 确认后恢复执行
graph.stream_events(Command(resume={"approved": True}), config)
```

`interrupt()` 在节点内暂停并把决策权暴露给调用方；`checkpointer` 保证了状态不会丢失——即使程序重启，恢复执行时 Agent 也能从断点继续。这就是 Lyft 案例中"人工客服看到完整执行历史"的底层机制。

Klarna的规模更能说明问题——8500万用户，高峰期每秒数百个客服Agent并发。他们的架构用LangGraph的子图（Subgraph）模式把不同业务线（退款、订单查询、账户管理）封装成独立的子状态机，由顶层路由Agent分发（来源：Rephrase.it对Klarna LangGraph架构的分析）。

LangGraph的学习曲线不低。State的类型定义、Conditional Edge的签名、Checkpointing的持久化配置——这些概念需要花时间建立直觉。但一旦你理解了这个模型，你会发现大多数Agent问题本质上是状态管理问题，而图是表达状态转移最自然的抽象。

---

## 工具调用的"通用语言"

如果说LangGraph解决的是Agent内部的组织结构问题，MCP解决的则是一个更底层的问题——Agent如何发现自己能使用什么工具，又如何调用它们。

在MCP出现之前，工具调用的标准做法是Function Calling（函数调用）——LLM输出一个结构化的JSON对象，指定要调用的函数名和参数，宿主程序解析这个JSON然后执行对应的函数，把结果送回LLM。这个过程的问题是：工具的schema（模式定义）是写死在代码里的硬编码，Agent无法在运行时发现一个新工具——它只能用开发者提前注册好的那几个函数。

MCP把这个问题上升了一个抽象层级。它不是在模型层面定义工具，而是在传输层面（transport layer）定义一个标准化的客户端-服务器协议：MCP Server暴露工具、资源（Resource）和提示模板（Prompt），MCP Client通过JSON-RPC 2.0协议（一种轻量级远程过程调用协议）发现并调用它们。

这里的概念对比值得展开：

| 维度 | MCP | Function Calling |
|------|-----|-----------------|
| 层级 | 基础设施/传输层 | 模型能力层 |
| 协议 | JSON-RPC 2.0 | 结构化JSON请求 |
| 工具发现 | 运行时动态（tools/list） | 编译时/硬编码schema |
| 供应商 | 模型无关 | 模型特定（OpenAI/Anthropic各有差异） |
| 安全模型 | OAuth 2.1授权（Bearer/Client ID Metadata） | 无标准授权机制 |
| 生态 | 10,000+公开Server | 每个应用独立实现 |

来源：Prefect官方博客 MCP vs Function Calling对比分析

落实到代码层面，一个 MCP Server 暴露工具、一个 MCP Client 发现并调用工具，长这样：

```python
# server.py —— MCP Server 暴露工具和资源
from mcp.server import MCPServer

mcp = MCPServer("Demo")

@mcp.tool()
def search_web(query: str) -> str:
    """搜索网络"""
    return f"搜索结果: {query}"

@mcp.resource("weather://{city}")
def get_weather(city: str) -> str:
    """获取城市天气"""
    return f"{city}: 晴天, 25°C"
```

```python
# client.py —— MCP Client 在运行时发现并调用工具
from mcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        # 运行时发现工具——不需要硬编码 schema
        tools = await client.list_tools()
        # 调用工具
        result = await client.call_tool("search_web", {"query": "AI Agent"})
        print(result.structured_content)  # {'result': '搜索结果: AI Agent'}
```

这就是 MCP 的核心价值——`search_web` 的定义和调用是完全解耦的。Server 端加了新工具，Client 端无需改代码，`list_tools()` 运行时会自动发现。对比 Function Calling 的"编译时硬编码 schema"，这个区别是结构性的。

MCP的传输层演进本身就是一篇值得读的故事。最初的实现基于SSE，但SSE的单向推送、连接不可恢复、HTTP/1.1-only等限制在生产环境中暴露了大量问题。

2025年3月的PR #206引入Streamable HTTP（可流式HTTP）作为替代——它支持双向通信、连接恢复、HTTP/2多路复用，并且不需要客户端保持持久连接。

2026年7月的RC草案更进一步：用MRTR替代SSE，实现真正的任务级多路复用和断点续传。

为什么选择Streamable HTTP而不是WebSocket？PR #206的论证值得细看：WebSocket要求全双工长连接，对MCP这种"大部分时间是请求-响应、偶尔需要服务端推送"的通信模式来说是过度设计。Streamable HTTP在HTTP框架内通过分块传输编码（chunked transfer encoding）实现流式响应，不需要额外的连接管理开销。

OAuth 2.1身份验证的选择同样有设计考量：社区最早讨论使用DCR（Dynamic Client Registration，动态客户端注册），但MCP生态系统主要由预先配置的已知客户端组成，DCR的动态注册能力增加了不必要的复杂度和攻击面。

Issue #1299（由Dickhardt提出）最终确定采用OAuth 2.1 Client ID Metadata方案——客户端在授权前通过metadata endpoint声明自己的身份和能力，而非动态注册。

工具的发现机制是MCP的另一个精妙之处。

ToolLLM（arXiv 2307.16789）在2023年证明了LLM在16,000+真实API上的工具选择能力，但它的实验设定有一个前提——所有API的schema都是预先整理好的。

MCP做的事情是把这个"预先整理"变成标准化的运行时协议：MCP Server启动时暴露tools/list端点，Client在运行时动态获取可用工具列表。Agent不需要提前知道有哪些工具，它可以在需要时向MCP Server查询。

这种"延迟发现"（lazy discovery）让Agent的工具体系具备了真正的可扩展性——加一个新工具不需要改Agent的代码，只需要启动一个新的MCP Server。

但灵活性有其代价。MCP的30+已披露CVE（2026年1-2月期间）中，CVE-2025-6514是一个CVSS 9.6的远程代码执行漏洞，攻击路径通过mcp-remote组件的SSE解析。沙箱隔离已经不是最佳实践——是硬性要求。

---

## 当个体需要组成团队

MCP解决的是Agent调用工具的问题。更复杂的问题是Agent之间的互调用。

这催生了两个互补的协议：MCP（Agent-to-Tool）和A2A（Agent-to-Agent）。Google在2025年4月提出的Agent-to-Agent Protocol（A2A，智能体间协议）定位于Agent之间的水平通信，而MCP定位于Agent到工具的垂直集成。MCP是Agent的"手"，A2A是Agent的"同事"。

| 维度 | MCP (Agent-to-Tool) | A2A (Agent-to-Agent) |
|------|---------------------|----------------------|
| 方向 | 垂直（Agent↔工具） | 水平（Agent↔Agent） |
| 通信模式 | 请求-响应/流式 | 任务委托+异步通知 |
| 状态管理 | 无状态会话（2026 RC） | 有状态任务跟踪 |
| 协议 | JSON-RPC 2.0 | gRPC + 标准数据模型 |
| 治理 | Linux Foundation AAIF | Linux Foundation AAIF |
| 适用场景 | 工具调用/数据访问 | 多Agent任务分配 |

来源：KodeKloud A2A vs MCP对比分析

两个协议现在都归Linux Foundation的AAIF（Agentic AI Foundation）管理，这种治理的统一消除了一个风险——厂商用不同协议分割生态。

在LangGraph中实现多Agent协作，有几个经过生产验证的模式：

Supervisor（监督者）模式是最直观的——创建一个顶层Agent，它把子Agent注册为工具（通过create_agent + @tool），然后根据用户意图路由到对应的子Agent。这种模式适合"任务类型明确"的场景，比如客服系统中按问题类型分发的路由Agent。缺点也明显：Supervisor是单点瓶颈，而且子Agent之间无法直接通信。

Handoff（移交）模式通过状态变量（State）和Command(goto=...)实现Agent之间的控制权转移。AgentA在处理过程中检测到"这个任务更适合AgentB"，就更新State中的路由标记，系统自动跳转到AgentB的Node。Handoff比Supervisor更灵活，但调试难度更大——你需要追踪状态在多个Agent之间的转移路径。

Swarm（群集）模式更进一步，去掉中心化的监督者，每个Agent自主决定下一步交给谁处理。这种模式在OpenAI的实验性框架Swarm（2025年3月已归档）中被提出，后来被LangGraph等框架吸收。Swarm的优势是去中心化和可扩展，代价是行为难以预测——当每个Agent都有自主转发权时，系统的收敛性很难保证。

Send API是LangGraph的另一个强力特性——它把一个Node的输出Map到N个并行的子任务。

比如用户问"帮我比一下iPhone 17 Pro和三星S26 Ultra的拍照"，一个Supervisor Agent可以把这条指令并行发给"iPhone Agent"和"三星Agent"，两个子Agent分别查询各自的产品信息，结果汇总后再由Supervisor做对比。

这不是简单的并发调用——每个子Agent有自己的独立State和Checkpointing，可以在自己的执行路径上暂停和恢复。

Subgraph（子图）模式把Agent的封装性推到极致。你可以把一个完整的Agent定义为一个独立的StateGraph，然后作为Node嵌入到父图中，子图内部的状态对父图完全透明（private scratchpad）。这让复杂的Agent系统可以模块化构建——每个团队独立开发和测试自己的子Agent，然后通过定义好的Subgraph接口集成。

回到框架选择的现实。2026年7月的Agent框架格局：

| 框架 | Stars | 状态 | 定位 |
|------|-------|------|------|
| LangGraph | 37k | 活跃（v1.2.9, 2026.07.10） | 企业级生产 |
| CrewAI | 55k | 活跃 | 快速原型开发 |
| OpenAI Agents SDK | 28k | 活跃 | OpenAI原生生态 |
| Microsoft Agent Framework | 新 | 活跃（v1.0, 2026.04） | Azure企业级 |
| AutoGen | 59k | 维护模式（2025.10起） | 学术实验，**不推荐新项目** |
| OpenAI Swarm | 21k | 已归档（2025.03） | 实验性质 |

来源：AgenticWire Agent Framework Status 2026

AutoGen以2023年的论文（arXiv 2308.08155）首次系统化论证了多Agent对话框架，59k Star说明社区兴趣巨大，但Microsoft在2025年10月将其转为维护模式，核心团队转入新的Microsoft Agent Framework。

这个故事揭示了一个常见模式：学术先行验证概念，工业界落地时推倒重来。多Agent协作的理论吸引力巨大——"让专业Agent各自负责自己擅长的部分"——但生产环境的残酷之处在于，每多一个Agent，你就多了一个可能的故障点。一条经验法则正在形成：能用单个Agent加好工具解决的问题，通常不应拆成多Agent系统。

多Agent应该被视为最后的手段，而不是默认的架构选择。它的适用条件比直觉判断更苛刻——只有当任务本身具有天然的子任务边界、子任务之间的信息依赖足够低时，多Agent架构才开始正向贡献。

---

## 局限性与权衡

标准化有标准化的代价。

MCP的安全面已经不是一个"未来需要关注的问题"，而是眼下就需要处理的现实。

30+已披露CVE中包括CVSS 9.6级别的远程代码执行漏洞，攻击面来自mcp-remote组件的SSE解析路径。这意味着任何暴露MCP Server的系统，如果不做沙箱隔离，安全风险极高。

这不是MCP独有的问题（任何接受外部输入的协议都会面临类似风险），但MCP的协议复杂度（JSON-RPC、流式传输、工具schema解析）把攻击面放大了。

多Agent系统的可靠性是一个反直觉的事实。单个Agent加一套好工具，在大多数场景下比精心编排的Supervisor-Swarm架构更可靠。

这不是说多Agent没用——Klarna和Lyft的生产案例证明它在正确场景下可以工作——而是说多Agent有它的边界条件，而这些条件在大多数开发场景中并不满足。

每增加一个Agent，系统的非确定性就扩大一圈，而LLM的非确定性已经是生产环境中最大的不可控变量。

LangGraph的学习曲线实实在在。State类型系统、Conditional Edge的签名规则、Checkpointing的持久化策略——这些概念相互耦合，理解一个需要先理解另一个。它的文档目前仍以英文为主，虽然中文社区已经产出了多个独立指南和视频课程，但官方文档的翻译覆盖率还不能让中文读者完全脱离英文源阅读。

MCP的传输层迁移正在制造真实的痛苦。SSE被官方标记为deprecated，Streamable HTTP成为推荐选项，但生态中大量MCP Server和SDK还是基于SSE实现。2026年7月的RC草案引入MRTR后，这个迁移路径变得更长。那些在2025年率先接入MCP的团队，现在面临"重写传输层"和"留在旧版本"之间的选择——两个选项各有明显的代价。

---

我们讲过ReAct循环给Agent装上了"思考-行动"的引擎，RAG给Agent接入了外部知识，现在LangGraph和MCP给Agent搭建了协作的骨架——和工具协作、和人协作、和彼此协作。

但关键问题在于：当一个Agent系统拥有数十个MCP Server提供的数百个工具、由LangGraph编排成多层Subgraph、每层都有Human-in-the-loop检查点——这个系统的行为还"可理解"吗？

阶段一的核心是"让Agent能做正确的事"。阶段二的核心是"让Agent知道更多的事"。阶段三的核心不是"让Agent协作"，而是"让Agent的协作出问题时有迹可循"。

协作关过了之后，就该追究这个问题了。

*参考来源：*

- ReAct论文 (Yao et al., 2022)：[https://arxiv.org/abs/2210.03629](https://arxiv.org/abs/2210.03629)
- AutoGen论文 (Wu et al., 2023)：[https://arxiv.org/abs/2308.08155](https://arxiv.org/abs/2308.08155)
- ToolLLM论文 (Qin et al., 2023)：[https://arxiv.org/abs/2307.16789](https://arxiv.org/abs/2307.16789)
- LangGraph多Agent文档：[https://docs.langchain.com/oss/python/langchain/multi-agent](https://docs.langchain.com/oss/python/langchain/multi-agent)
- MCP规范（2026草案）：[https://modelcontextprotocol.io/specification/draft/](https://modelcontextprotocol.io/specification/draft/)
- MCP设计原则：[https://modelcontextprotocol.io/specification/draft/architecture#design-principles](https://modelcontextprotocol.io/specification/draft/architecture#design-principles)
- PR #206 (Streamable HTTP)：[https://github.com/modelcontextprotocol/modelcontextprotocol/pull/206](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/206)
- Issue #1299 (OAuth)：[https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1299](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1299)
- MCP传输层演进：[https://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/](https://blog.modelcontextprotocol.io/posts/2025-12-19-mcp-transport-future/)
- MCP 2026-07-28 RC公告：[https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/)
- 为什么MCP弃用SSE：[https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http/](https://blog.fka.dev/blog/2025-06-06-why-mcp-deprecated-sse-and-go-with-streamable-http/)
- LangGraph多Agent工作流博客：[https://www.langchain.com/blog/langgraph-multi-agent-workflows](https://www.langchain.com/blog/langgraph-multi-agent-workflows)
- Lyft案例：[https://www.langchain.com/blog/lyft-built-a-self-serve-ai-agent-platform-for-customer-support-with-langgraph-and-langsmith](https://www.langchain.com/blog/lyft-built-a-self-serve-ai-agent-platform-for-customer-support-with-langgraph-and-langsmith)
- Klarna生产规模：[https://rephrase-it.com/blog/langgraph-at-scale-what-klarna-shows](https://rephrase-it.com/blog/langgraph-at-scale-what-klarna-shows)
- AgentFlow设计模式：[https://github.com/zdjiangfdu/AgentFlow-langgraph-design-patterns](https://github.com/zdjiangfdu/AgentFlow-langgraph-design-patterns)
- MCP生态统计：[https://agentscamp.com/guides/mcp/mcp-ecosystem-statistics](https://agentscamp.com/guides/mcp/mcp-ecosystem-statistics)
- MCP企业采纳（2026.07）：[https://andrew.ooo/answers/mcp-model-context-protocol-enterprise-adoption-july-2026/](https://andrew.ooo/answers/mcp-model-context-protocol-enterprise-adoption-july-2026/)
- Agent框架状态2026：[https://www.agenticwire.news/article/ai-agent-framework-status-2026](https://www.agenticwire.news/article/ai-agent-framework-status-2026)
- MCP vs Function Calling：[https://www.prefect.io/resources/mcp-vs-function-calling](https://www.prefect.io/resources/mcp-vs-function-calling)
- A2A vs MCP：[https://kodekloud.com/blog/a2a-vs-mcp-agent-communication-protocols-explained-for-devops/](https://kodekloud.com/blog/a2a-vs-mcp-agent-communication-protocols-explained-for-devops/)
