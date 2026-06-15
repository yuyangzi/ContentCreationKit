# 2026 AI Agent 学习路线图——阶段三：学会协作（LangGraph + MCP + 多 Agent）

## 主题定位

- **领域**：AI Agent / 大模型应用
- **类型**：深扎技术教程（系列第 4 篇）
- **系列**：2026 AI Agent 学习路线图
- **前置阅读**：[阶段二：搭好手脚](./2026-AI-Agent学习路线图-阶段二-RAG与LangChain-20260614.md)
- **目标读者**：已完成阶段一和阶段二，能独立构建单 Agent 的工程师
- **确认时间**：2026-06-14

---

## 本阶段定位

**一句话**：从单 Agent 进入多 Agent 世界——用 LangGraph 管理复杂状态、用 MCP 标准化工具接入、让多个 Agent 协作完成单人搞不定的任务。

**为什么不能跳过**：2026 年 Agent 已经从"单打独斗"进入"团队协作"。MCP 是 Agent 工具集成的标准协议（被 OpenAI/Google/微软/Cursor 全面采纳），LangGraph 是有状态编排的事实方案。

---

## 三模块布局

```
LangGraph 图编排（35%）→ MCP 协议（35%）→ 多 Agent 协作（30%）
```

### 模块一：LangGraph 图编排（35%）

**从 Chain（链式）到 Graph（图式）——Agent 工作流的状态机升级。**

| 知识点 | 核心内容 |
|--------|----------|
| 为什么 LangChain Chain 不够用 | 链式调用是"一条线"，复杂 Agent 需要分支、循环、条件跳转 |
| Graph 核心概念 | State（共享状态）、Node（处理节点）、Edge（条件/无条件边） |
| 状态管理 | TypedDict State、状态读写、节点间状态传递 |
| 条件路由 | `add_conditional_edges`——根据 LLM 输出决定下一步走哪个节点 |
| Human-in-the-loop | `interrupt_before` / `interrupt_after`——关键节点暂停等待人工确认 |
| Checkpointing | 状态快照——Agent 执行到一半挂了，能从快照恢复 |
| Streaming | 节点级流式输出，实时看到 Agent 的思考过程 |

**实操项目**：用 LangGraph 重构阶段二的单 Agent——从 Chain 变成 Graph，加入条件路由和 Human-in-the-loop。

**关键对比**（贯穿全文）：
- 阶段一的 Agent Loop 是**隐式循环**（while 循环 + finish_reason 判断）
- LangGraph 的 Graph 是**显式状态机**（Node → Edge → Node，状态全程可见）

---

### 模块二：MCP 协议（35%）

**2026 年 Agent 工具集成的标准协议——不理解 MCP 等于不理解 HTTP。**

| 知识点 | 核心内容 |
|--------|----------|
| MCP 是什么、为什么出现 | 解决 Agent 工具的"巴别塔问题"——每个工具都有自己的接入方式 |
| 三元组架构 | Tool（可调用的函数）、Resource（可读取的数据）、Prompt（可复用的模板） |
| Server/Client 架构 | MCP Server 暴露能力 → MCP Client（Agent）发现并调用 |
| Transport 层 | stdio（本地进程通信）、SSE/Streamable HTTP（远程服务） |
| 2026 年生态现状 | 9700 万月下载、10000+ 公共 MCP Server、Linux 基金会托管 |
| 安全性注意 | 2026 年 1-2 月 30+ CVE（含 CVSS 9.6 RCE），沙箱化部署是必须的 |
| 与 Function Calling 的关系 | MCP 是工具发现和标准化层，Function Calling 是工具执行层——互补而非替代 |

**实操项目**：
1. 写一个最简单的 MCP Server（返回天气数据）
2. 用 Claude Code / Cursor 连接这个 MCP Server
3. MCP Server + LangGraph Agent 集成

---

### 模块三：多 Agent 协作（30%）

**当一个问题太复杂，一个 Agent 搞不定时——拆分、委托、协作。**

| 知识点 | 核心内容 |
|--------|----------|
| 多 Agent 的三种协作模式 | 顺序流水线、并行分工、辩论/投票 |
| CrewAI 入门 | Role/Goal/Backstory 定义 Agent 角色 → Task 分配 → Crew 编排 |
| Agent 间通信 | 结构化消息传递、共享状态（State）、避免循环依赖 |
| 多 Agent 常见坑 | 信息丢失（电话游戏效应）、死循环互相调用、角色越界 |
| 何时不该用多 Agent | 单 Agent + 好工具往往比多 Agent 更可靠——不要为了多 Agent 而多 Agent |

**实操项目**：Research Agent + Writer Agent 协作——Research Agent 搜索资料 → Writer Agent 整合成报告。

---

## 技术细节

- **代码框架**：LangGraph（Python）+ CrewAI + MCP Python SDK
- **教程模型**：DeepSeek V4-Flash
- **MCP 工具**：自建 MCP Server + 公开 MCP Server（如 Brave Search MCP）

---

## 创作结构建议

```
1. 引子（5%）：阶段二你的 Agent 只有一个大脑——现在给它更多大脑和标准化的手脚
2. 模块一 LangGraph（30%）：从 Chain 到 Graph 的范式升级
3. 模块二 MCP 协议（30%）：协议原理 → 写 Server → 连 Agent
4. 模块三 多 Agent 协作（30%）：CrewAI 实战 → 协作模式 → 避坑指南
5. 结尾（5%）：阶段三总结 + 预告阶段四（企业级实战）
```

---

## 差异化价值

- **MCP 深度讲解**：2026 年中文教程中，系统讲 MCP 的内容极少——这是差异化锚点
- **LangGraph vs 自建 Loop 对比**：阶段一自建 Agent Loop → 阶段三 LangGraph，读者理解"框架解决什么问题"
- **多 Agent 防忽悠**：讲清楚什么时候单 Agent 更好——不为了炫技堆复杂度
- **安全提醒**：MCP 不是银弹，CVE 历史是最好的教学案例

---

## 参考来源

- LangGraph 官方文档
- MCP 官方规范（modelcontextprotocol.io）
- CrewAI 文档
- AgentMarketCap - MCP 生态报告（2026.04）
- WorkOS - MCP in 2026（2026.03）

---

## 状态

- [x] 主题确认
- [ ] 参考资料审核
- [ ] 草拟大纲
- [ ] 撰写正文
- [ ] 审核发布
