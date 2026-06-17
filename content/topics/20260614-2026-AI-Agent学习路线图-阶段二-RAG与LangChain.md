# 2026 AI Agent 学习路线图——阶段二：搭好手脚（RAG + LangChain + 第一个 Agent）

## 主题定位

- **领域**：AI Agent / 大模型应用
- **类型**：深扎技术教程（系列第 3 篇）
- **系列**：2026 AI Agent 学习路线图
- **前置阅读**：[阶段一：理解 Agent 的运行时心脏](./2026-AI-Agent学习路线图-阶段一-运行时心脏-20260614.md)
- **目标读者**：已完成阶段一，理解 Function Calling 和 Agent Loop 的工程师
- **确认时间**：2026-06-14

---

## 本阶段定位

**一句话**：给 Agent 装上"知识手脚"——能检索外部知识（RAG）、能用 LangChain 快速搭建原型、能独立完成一个多工具调用的单 Agent。

**为什么不能跳过**：没有 RAG，Agent 只能靠训练数据回答问题；不懂 LangChain 基础，无法理解社区 90% 的教程和面试题。

---

## 三模块布局

```
RAG 检索增强生成（40%）→ LangChain 六大模块（35%）→ 构建第一个单 Agent（25%）
```

### 模块一：RAG 检索增强生成（40%）

**给 LLM 装上外部记忆。**

| 知识点 | 核心内容 |
|--------|----------|
| RAG 为什么是 Agent 的标配 | LLM 知识截止日期 + 幻觉问题 → 外部检索补充事实 |
| Chunking 策略 | 固定长度 vs 语义分割 vs 递归分割，各自的召回率影响 |
| 向量检索原理 | Embedding 模型选择、相似度计算（余弦/欧氏/点积）、向量数据库选型 |
| 关键词检索（BM25） | 与向量检索互补，精确匹配场景不可替代 |
| Hybrid Search | 向量 + 关键词混合检索，RRF（Reciprocal Rank Fusion）融合策略 |
| Rerank 模型 | 粗排 → 精排，提升检索精度 |
| RAG 常见坑 | 检索到无关文档、chunk 过小丢失上下文、Embedding 模型未对齐领域 |

**实操项目**：用 LangChain 搭建一个文档问答 Agent——上传 PDF → Chunking → 存入向量数据库 → 检索 → LLM 回答。

---

### 模块二：从 Mini Loop 到 LangChain Agent（20%）

**定位：用 2026 年当前 LangChain API 重构你在阶段一写的 Agent Loop。**

> ⚠️ LangChain 1.x 重大 API 变更（验证于 2026-06-14）：`create_react_agent`（langgraph.prebuilt）、`RunnableWithMessageHistory`、`AgentExecutor`、`ConversationBufferMemory`、`LLMChain` 均已废弃。当前版本 `langchain==1.3.9`、`langgraph==1.2.5`。

| 知识点 | 旧 API（已废弃） | 当前 API（2026-06） |
|--------|-----------------|---------------------|
| Agent 创建 | ~~`create_react_agent`（langgraph.prebuilt）~~ | `from langchain.agents import create_agent` |
| 对话记忆 | ~~`RunnableWithMessageHistory`~~ | `checkpointer=InMemorySaver()`（直接传参给 `create_agent`） |
| 链式调用 | ~~`LLMChain`~~ | LCEL：`prompt \| model \| StrOutputParser()` |

**Memory 正确做法**（不需要额外包装）：
```python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(model=..., tools=[...], checkpointer=InMemorySaver())
agent.invoke({"messages": [...]}, {"configurable": {"thread_id": "user-123"}})
```

**关键认知**：`create_agent` 底层就是你在阶段一写的 while 循环 + finish_reason 检查。你花两天写的 100 行代码，它用一行封装了——但你现在知道里面在干什么。

**不讲的内容**：
- Models、Prompts（阶段一的上下文工程已覆盖基础）
- Indexes、VectorStores（已并入模块一 RAG 部分）

---

### 模块三：构建第一个单 Agent（25%）

**三合一实战项目：天气查询 + 数据库检索 + API 调用。**

| 组件 | 实现 | 学到的技能 |
|------|------|-----------|
| 天气查询 Tool | 调用公开天气 API | 外部 API 工具封装 |
| 数据库检索 Tool | SQLite + 自然语言转 SQL | RAG + 结构化数据混合查询 |
| API 调用 Tool | 调用任意 REST API | 通用工具模式 |
| 对话记忆 | ConversationBufferMemory | 多轮对话中保持上下文 |
| 错误处理 | Tool 调用失败 → 降级策略 | 生产级鲁棒性 |

**最终效果**：一个能从数据库查数据、能调外部 API、能在多轮对话中记住上下文的单 Agent。

---

## 技术细节

- **代码框架**：LangChain 1.3.9 + LangGraph 1.2.5（Python）
- **依赖锁定**：`langchain==1.3.9` `langgraph==1.2.5` `langchain-openai==1.3.2` `chromadb==1.5.9` `sentence-transformers`
- **教程模型**：DeepSeek V4-Flash（via ChatOpenAI with custom base_url）
- **向量数据库**：ChromaDB（轻量，适合学习）
- **构建目标**：可运行的 Python 脚本，不是 Jupyter Notebook 片段

---

## 创作结构建议

```
1. 引子（5%）：Agent 只有推理能力，没有"知道"能力——RAG 解决这个问题
2. 模块一 RAG（35%）：从原理到代码，完整搭建文档问答系统
3. 模块二 LangChain 六大模块（30%）：逐一讲解，每个模块有可运行的代码片段
4. 模块三 构建第一个单 Agent（25%）：三合一实战，整合 RAG + API 调用
5. 结尾（5%）：阶段二总结 + 预告阶段三（LangGraph + MCP + 多 Agent）
```

---

## 差异化价值

- **RAG 的坑地图**：不只讲怎么搭，重点讲什么时候会失败、为什么失败
- **LangChain 清醒教学**：讲清楚它解决了什么问题、引入了什么问题——不是无脑吹
- **从阶段一递进**：读者已经理解原生 Function Calling，现在看 LangChain 封装会"恍然大悟"
- **三合一实战**：不是三个独立 demo，是一个 Agent 同时使用三种工具

---

## 参考来源

- LangChain 官方文档（注意 1.x 版本 API 变更）
- ChromaDB 文档
- Datawhale Hello-Agents 第 6-8 章（框架开发、自建框架、记忆与检索）
- ai-agents-from-zero 第 03-04 节（核心开发框架、企业级 RAG/Agent 实战）

---

## 状态

- [x] 主题确认
- [ ] 参考资料审核
- [ ] 草拟大纲
- [ ] 撰写正文
- [ ] 审核发布
