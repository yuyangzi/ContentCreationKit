# 2026 AI Agent 学习路线图——阶段三：学会协作（LangGraph + MCP + 多 Agent）

## 主题定位

- **领域**：AI Agent / 大模型应用
- **类型**：深扎技术教程（系列第 4 篇）
- **系列**：2026 AI Agent 学习路线图
- **前置阅读**：[阶段二：搭好手脚](./2026-AI-Agent学习路线图-阶段二-RAG与LangChain-20260614.md)
- **目标读者**：已完成阶段一和阶段二，能独立构建单 Agent 的工程师
- **确认时间**：2026-07-22（更新）

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
3. 分析 MCP Server 的协议交互细节——JSON-RPC 消息流（`tools/list` → `tools/call`）、Transport 层差异（stdio vs Streamable HTTP）、工具发现全流程

---

### 模块三：多 Agent 协作——LangGraph 原生模式（30%）

**单 Agent 的边界在哪？画出边界之后，如何让多个 Agent 在同一张图上协作。**

LangGraph 原生支持三种多 Agent 模式——Supervisor（集中路由）、Hierarchical（层级嵌套）、Swarm（去中心化 Handoff）——全部基于同一套 Graph API，无需引入第三方框架。

| 知识点 | 核心内容 |
|--------|----------|
| Supervisor 模式 | 主 Agent 将子 Agent 作为工具调用——`create_agent` 包装后通过 `@tool` 暴露 |
| Handoff 模式 | 基于状态变量 + `Command(goto=...)` 实现 Agent 间控制权转移 |
| 并行分支 | `Send` API——将一个节点输出映射为 N 个并行子任务，各分支独立执行 |
| 条件合并 | 并行结果收集后，根据置信度决定是直接合并还是触发 Human-in-the-loop |
| 子图与状态隔离 | `StateGraph` 嵌套——每个子 Agent 维护私有 scratchpad，Supervisor 只看最终结果 |
| 多 Agent 常见坑 | 路由失败（Supervisor 选错 Agent）、状态泄漏（子 Agent 意外修改共享状态）、并行分支合并竞态 |
| 何时不该用多 Agent | 单 Agent + 好工具往往比多 Agent 更可靠——不要为了多 Agent 而多 Agent |

**实操项目**：任务分解 Agent 拆分需求 → `Send` API 并行分发给多个专家 Agent → 收集结果后置信度判断 → 高置信度直接合并输出，低置信度触发人工审核。覆盖 Supervisor + 并行分支 + 条件合并 + Human-in-the-loop 四个核心模式。

---

## 技术细节

- **代码框架**：LangGraph（Python）+ MCP Python SDK
- **教程模型**：DeepSeek V4-Flash
- **MCP 工具**：自建 MCP Server + 公开 MCP Server（如 Brave Search MCP）

---

## 创作结构建议

```
1. 引子（5%）：阶段二你的 Agent 只有一个大脑——现在给它更多大脑和标准化的手脚
2. 模块一 LangGraph（30%）：从 Chain 到 Graph 的范式升级
3. 模块二 MCP 协议（30%）：协议原理 → 写 Server → 协议设计哲学深度剖析
4. 模块三 多 Agent 协作（30%）：LangGraph 原生 Supervisor/Hierarchical/Swarm 模式
5. 结尾（10%）：阶段三总结——三步完成从单 Agent 到多 Agent 协作的跃迁
```

---

## 差异化价值

- **MCP 协议设计哲学**：现有中文内容多停留在配置使用层面，缺乏对协议设计决策的深度剖析——为什么是 Streamable HTTP 而非 WebSocket？为什么 Tool/Resource/Prompt 是三重而非两重？OAuth 2.1 集成为什么选择了 Client ID Metadata 而非 DCR？本文逐一拆解
- **2026 年最新演进**：MCP 2026-07-28 规范草案是无状态重构版本——移除 `initialize` 握手、引入 MRTR 替代 SSE 流、TTL 缓存机制。中文社区对此覆盖极少，本文补上
- **LangGraph 全线贯通**：三个模块全部基于 LangGraph——从单 Agent 图编排，到 MCP 工具接入，再到多 Agent 协作——技术栈统一，读者认知负担最小
- **多 Agent 防忽悠**：用 AutoGen 维护模式（2025.10）和 CrewAI 定位原型为案例，讲清楚"框架选型要看定位，不要看 star 数"
- **安全提醒**：MCP 不是银弹，CVE 历史是最好的教学案例

---

## 参考来源

- LangGraph 官方文档（Multi-agent: Subagents / Handoffs / Subgraphs）
- LangGraph "Multi-Agent Workflows" 原始博客（2024.01）
- Lyft 多 Agent 产用案例（2026.05）
- AgentFlow 设计模式库（GitHub）
- MCP 官方规范（modelcontextprotocol.io）+ Design Principles
- MCP Spec PR #206（Streamable HTTP RFC，含"为什么不是 WebSocket"论证）
- MCP Spec Issue #1299（Dickhardt 的 OAuth 架构提案）
- "Exploring the Future of MCP Transports" 博客（2025.12）
- "The 2026-07-28 MCP Specification Release Candidate" 博客（2026.05）
- MCP SEP-2575（Make MCP Stateless）、SEP-2567（Sessionless MCP）、SEP-2322（MRTR）
- AgentMarketCap - MCP 生态报告（2026.04）
- WorkOS - MCP in 2026（2026.03）

---

## 状态

- [x] 主题确认
- [ ] 参考资料审核
- [ ] 草拟大纲
- [ ] 撰写正文
- [ ] 审核发布
