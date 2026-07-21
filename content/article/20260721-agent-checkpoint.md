# Agent Checkpoint 机制：为什么"断点续跑"和你想象的不一样

写 Agent 的人大多体会过一种痛：改了一行 prompt，就要把整个流程从头跑一遍。LLM 调用、工具调用、推理链——全重来。如果你的 Agent 有 10 步、每步调一次 GPT-5，一次调试的 token 账单一拉就是六位数。

更糟的是，Agent 不像普通程序那样"崩溃即退出"。它可能在第 7 步卡住、在第 4 步给出错误的中间结论然后继续往下走、在第 9 步耗尽上下文窗口。没有 checkpoint 时，你只能从零重新启动，祈祷这次能走得更远。

一旦给 Agent 加上 checkpoint，你就能从失败的那一步接着跑——不是重放历史，是真正地从状态快照恢复执行。

> **Checkpoint ≠ 代码断点。** 在 LangGraph 里，你用 `interrupt()` 暂停了一个节点的执行，人类审核后调用 `Command(resume=True)`——Agent 不是从 `interrupt()` 的那一行继续，而是**重新执行整个节点**。

这个设计意味着 checkpoint 记录的永远是"super-step 结束时的完整状态"，而不是"某行代码执行到一半的寄存器快照"。理解这一点，有助于理解 Pregel 模型、channel 版本号、pending writes 这些概念。

---

## 痛点：没有 checkpoint，Agent 调试是一件很烧钱的事

没有 checkpoint 的 Agent 开发流程是这样：写代码 → 跑 Agent → 第 N 步出问题 → 修代码 → 从第 1 步重新跑 → 又出问题 → 再修再跑。

每一步重跑都在消耗 LLM token。上一次跑通过的步骤，这一次可能因为模型非确定性走了不同的工具调用路径，产出的中间结果也不同。你修的是一行 prompt，但行为变化可能出现在完全不相干的步骤——因为模型的推理链重组了。

LangGraph 社区里一个常见的场景：调 Agent 的工具选择逻辑时，每次都要等前面 6 步的 RAG 检索、意图识别、工具调度跑完，才能验证第 7 步的改动是否生效。这 6 步消耗的 token 是纯浪费。

checkpoint 解决的就是这个问题——让 Agent 的状态可持久化、可恢复、可回溯。但不是靠"记录每一行代码执行到哪里"，而是靠一种来自大规模图计算领域的设计：**BSP（Bulk Synchronous Parallel，批量同步并行）模型**。

---

## 原理：checkpoint 的数学基础不在 LangGraph，在 Google 2010 年的一篇论文

LangGraph 的 checkpoint 机制不是原创——它继承自 Pregel，Google 在 2010 年 SIGMOD 上发表的 BSP 图计算系统。

### Pregel 的 super-step 三阶段

Pregel 把图计算分成若干个 **super-step**。每个 super-step 严格遵循三个阶段：

1. **Plan（规划）**：根据当前 channel 的版本号变化，计算下一轮需要执行哪些节点
2. **Execute（执行）**：并行运行所有被标记的节点，每个节点读取上游 channel 的数据、产出写给下游 channel
3. **Update（更新）**：把所有节点的输出写入 channel，递增版本号，生成 checkpoint

super-step 之间的边界，是天然的 checkpoint 点。因为所有节点都完成了本轮计算、状态一致、没有"执行到一半"的节点存在。Pregel 的设计哲学是"在 step 之间做快照，不在 step 内部做快照"——这也是为什么 LangGraph 的 `interrupt()` 不会产生一个"半行代码级"的断点。

LangGraph 的运行时核心 `PregelLoop` 完整实现了这个三阶段循环：

```
prepare_next_tasks → execute → apply_writes → create_checkpoint → 循环
```

每一次循环都是一个 super-step。checkpoint 记录的是 `apply_writes` 完成后的完整图状态。

### Checkpoint 的数据模型

一个 checkpoint 在 LangGraph 内部是一个 `TypedDict`，六个字段：

- **`v`**（int）：checkpoint 格式版本号，用于向后兼容
- **`id`**（str）：checkpoint 的唯一标识，ULID 格式，按时间排序
- **`ts`**（str）：ISO 8601 时间戳
- **`channel_values`**（dict）：所有 channel 的当前值，是图状态的完整快照
- **`channel_versions`**（dict）：每个 channel 的版本号，格式为 `{channel_name: version_int}`
- **`versions_seen`**（dict）：每个节点上次执行时看到的各 channel 版本号，格式为 `{node_name: {channel_name: version_int}}`

`channel_versions` 和 `versions_seen` 是调度引擎的核心。判断一个节点是否需要在下一个 super-step 执行的规则很简单：

```
channel_versions[ch] > versions_seen[node][ch]  →  node 需要运行
```

如果某个节点依赖的 channel 版本号比它上次执行时看到的版本号更高，说明这个 channel 在上一个 super-step 被别的节点更新了——当前节点需要重新计算。

这就是一个分布式的"脏标记"机制。不依赖中心化的调度器告诉每个节点"你该跑了"，每个节点自己通过版本号比对就能判断。

### BaseCheckpointSaver 的五个接口

LangGraph 通过 `BaseCheckpointSaver` 抽象了所有 checkpoint 存储后端。五个接口，职责清晰：

- **`put(config, checkpoint, metadata, new_versions)`** ：在 super-step 边界写入完整 checkpoint。`new_versions` 由 PregelLoop 计算——它是本轮所有 channel 的新版本号集合
- **`put_writes(config, writes, task_id, task_path)`** ：在每个节点执行完成后立即调用，写入该节点的**中间输出**（pending writes）。它不等 super-step 结束——这是一种容错设计
- **`get_tuple(config)`** ：按 `thread_id` + `checkpoint_id` 检索一个 checkpoint，返回 `CheckpointTuple`（包含 checkpoint、metadata、parent_config、pending_writes）
- **`list(config, filter, before, limit)`** ：列出某个 thread 的所有 checkpoint，最新在前。这是 Time Travel 的检索入口
- **`delete_thread(thread_id)`** ：删除一个 thread 的所有 checkpoint

`put` 和 `put_writes` 的分离是关键设计决策。`put` 在 super-step 结束时调用，代表"完整快照"；`put_writes` 在每个节点完成时立即调用，代表"部分写入"。如果 super-step 中途崩溃，已经通过 `put_writes` 持久化的中间输出可以用于恢复——不需要重跑已经成功的兄弟节点。

### 两张表的存储模型

大多数 `BaseCheckpointSaver` 的实现（SqliteSaver、PostgresSaver）使用两张表：

**checkpoints 表**：

| 列 | 类型 | 说明 |
|---|---|---|
| `thread_id` | TEXT | 线程标识，主键之一 |
| `checkpoint_ns` | TEXT | checkpoint 命名空间（默认空字符串） |
| `checkpoint_id` | TEXT | ULID，按时间排序 |
| `parent_checkpoint_id` | TEXT | 父 checkpoint 的 ID，构成链表 |
| `checkpoint` | JSONB | 序列化后的 checkpoint 数据（大值溢出到独立 `checkpoint_blobs` 表，该表为 BYTEA） |
| `metadata` | JSONB | CheckpointMetadata（source、step、parents 等） |

**writes 表**：

| 列 | 类型 | 说明 |
|---|---|---|
| `thread_id` | TEXT | 线程标识 |
| `checkpoint_ns` | TEXT | 命名空间 |
| `checkpoint_id` | TEXT | 所属 checkpoint |
| `task_id` | TEXT | 节点 ID |
| `channel` | TEXT | 写入的 channel 名 |
| `value` | BYTEA | 序列化后的写入值 |

writes 表的存在让"部分恢复"成为可能。如果 super-step 里有 5 个节点并行执行，其中 3 个成功、1 个崩溃、1 个还没开始，已有 3 个节点的 writes 持久化——恢复时只需要重跑崩溃和未开始的那两个。

### 一个具体的时间线

假设这个简单图：`START → node_a → node_b → END`

整个运行过程中会产生 **4 个 checkpoint**：

1. **step = -1**，`source = "input"`，`next = ('__start__',)`。这是 PregelLoop 在接受外部输入后创建的第一个 checkpoint——内容就是用户传入的 `input_data`。`channel_versions` 全部初始化为 1
2. **step = 0**，`source = "loop"`，`next = ('node_a',)`。输入被应用到 channel 后创建。`versions_seen['__start__']` 记录了输入 channel 的版本号，PregelLoop 计算后发现 `node_a` 依赖的 channel 版本号高于它见过的版本——所以 `node_a` 被放入 `next`
3. **step = 1**，`source = "loop"`，`next = ('node_b',)`。`node_a` 执行完毕后，它的输出被写入 channel（`channel_versions` 递增），PregelLoop 发现 `node_b` 依赖的 channel 有新版本——`node_b` 进入 `next`。此时的 `channel_values` 包含了 `node_a` 的完整输出
4. **step = 2**，`source = "loop"`，`next = ()`。`node_b` 执行完毕，`next` 为空——图执行结束。这是最终 checkpoint，`channel_values` 包含完整结果

在这 4 个 checkpoint 之间，`put_writes` 被调用 2 次（`node_a` 和 `node_b` 各一次），writes 表里对应有 2 条记录。

序列化方面，LangGraph 默认使用 `JsonPlusSerializer`（基于 `ormsgpack` + JSON），支持绝大多数 Python 原生类型。生产环境中如果 State 包含敏感数据，可以用 `EncryptedSerializer` 包装任意序列化器做透明加密。

---

## 能力：checkpoint 不是存了就好，它能做什么

### 人工介入：interrupt() 和 Command(resume=)

最常用的能力是 **Human-in-the-Loop**（人工介入循环）。在节点里调用 `interrupt()` 暂停执行，等待人类审核后继续：

```Python
# 在 StateGraph 的节点内使用 interrupt
def review_node(state: State) -> State:
    # 先做自动化检查
    if state["risk_score"] > 0.8:
        # 暂停，等待人工审批
        decision = interrupt("风险过高，需要人工审批")
        state["approved"] = decision
    return state

# 外部恢复
config = {"configurable": {"thread_id": "task-123"}}
graph.invoke(input_data, config)           # 在 interrupt() 处暂停
# 人类审核后
graph.invoke(Command(resume=True), config)  # 恢复执行
```

`Command(resume=True)` 恢复后，`review_node` 会**从头重新执行**，而不是从 `interrupt()` 调用之后的那一行继续。也就是说，`interrupt()` 之前的所有代码会再跑一遍。

这意味着两点。第一，`interrupt()` 之前的代码如果有副作用（比如发了一条消息、写了一次数据库），恢复时会再执行一次，需要你自己做幂等处理。第二，`interrupt()` 可以用在循环里——每次循环命中 `interrupt()` 都会产生一个新的暂停点，人类逐一审批。

### Time Travel：回溯和分叉

`get_state_history` 返回一个 thread 的所有 checkpoint 列表，最新在前。你可以：
- **回退到历史状态**：`graph.invoke(None, history[-1].config)` ——从旧 checkpoint 重新执行
- **分叉新分支**：`graph.update_state(old_config, new_values)` ——在旧 checkpoint 基础上修改状态值，LangGraph 会创建一个 `source = "update"` 的新 checkpoint，`parent_checkpoint_id` 指向旧 checkpoint

分叉产生的实际上是一条新的 checkpoint 链。`list()` 方法返回的 checkpoint 列表包含所有分支，你可以通过 `parent_checkpoint_id` 重建执行树。

### 容错：pending writes 的真正价值

回到前面提到的那张 writes 表。假设一个 super-step 里并行跑着 3 个节点：

- `node_a` 完成 → `put_writes` 持久化
- `node_b` 完成 → `put_writes` 持久化
- `node_c` 执行到一半，进程崩溃

恢复时，PregelLoop 调用 `get_tuple()` 拿到最新 checkpoint，发现 `pending_writes` 里已经有 `node_a` 和 `node_b` 的输出。它会把这两个输出应用到 channel 上，更新 `versions_seen`，然后只调度 `node_c` 重新执行。

已经成功的节点正常情况下不会重跑。不是靠"记住哪些节点跑过了"，是直接靠 writes 表里的记录驱动调度决策。

进行完整的故障恢复测试的方法很简单：启动 Agent → 在中间步骤 `kill -9` 进程 → 用同一个 `thread_id` 重新 `invoke` → 验证 Agent 从崩溃点继续而非重头开始。

### 长期记忆：Store API 与 checkpoint 的分工

checkpoint 解决的是**单线程内的状态持久化**——同一个 `thread_id` 的完整执行历史。但如果你的 Agent 需要在多个 thread 之间共享信息，checkpoint 不是答案。

**Store API**（跨线程记忆）解决这个问题：Agent 可以在一个 thread 里写入记忆（`store.put`），在另一个 thread 里通过语义搜索读取（`store.search`）。checkpoint 管"这次任务跑到了哪里"，Store 管"之前所有任务学到了什么"。两者互补，不是替代关系。

arXiv 2604.28138（Crab）提出了语义感知的 checkpoint/restore 运行时，arXiv 2606.06090 则将记忆管理定义为执行状态管理的一种——两者都指向统一的框架。

---

## 实践：选对后端，避开三个坑

### 后端选择

没有"最佳"后端，只有匹配部署拓扑的后端：

- **InMemorySaver**：开发调试用。进程重启数据全丢
- **SqliteSaver**：单机本地持久化。适合个人项目、单进程部署。注意：如果跑在容器里但没有挂持久卷，效果等同于 InMemorySaver
- **AsyncPostgresSaver**：生产环境首选。支持连接池、并发读写。多容器部署（k8s）的默认选择
- **langgraph-redis**（社区维护）：低延迟场景。配合 AOF 持久化避免数据丢失。适合对恢复速度要求极高的场景（实时对话 Agent）
- **自定义 DynamoDB/Cloud Storage**：Serverless 场景。LangGraph 的 `BaseCheckpointSaver` 接口足够简单，实现一个适配层通常不到 200 行代码

关键约束：`checkpointer` 实例必须是**同一个对象**传给 `compile()` 和 `invoke()`。如果你在每次请求里新建一个 `SqliteSaver`，每次的 checkpoint 都写在内存里——换个请求就丢了。

### 五个实践原则

1. **State 保持小而可序列化**。State 里不要放数据库连接、文件句柄、大段二进制数据。序列化开销和存储膨胀会在长对话中放大。实在需要传递大对象时，State 里只存引用（如文件路径、数据库 ID），在节点内部按需加载

2. **thread_id 使用 UUID 或业务 ID 哈希，长度不超过 255 字符**。Postgres 的 btree 索引对超长键的性能退化很明显——单键超过约 2704 字节会触发索引溢出

3. **同 thread_id 避免并发写入**。checkpoint 链本质是单链表，并发写会导致 `parent_checkpoint_id` 冲突。如果需要并行任务，拆成不同 thread_id

4. **设置 checkpoint 清理策略**。如果不设置清理策略，checkpoint 会持续增长。每条消息至少产生一个 super-step，一次对话轻松上百个 checkpoint。不清理的话，几个月后存储成本和检索延迟都会明显上升。LangGraph 1.2 引入了 DeltaChannel 机制（见下文），大幅降低了存储压力，但仍建议设置保留策略

5. **验证故障恢复流程**。不是"相信"它能在崩溃后恢复，而是用 `kill -9` 测试它真的能恢复。在 State 里嵌入 `retry_count`，在 `interrupt()` 之前的副作用做好幂等处理

### 三个常见的坑

**坑一：恢复时传了新的 input**

```Python
# ❌ 错误：重新传了 input_data
graph.invoke(input_data, config)  # 从 input checkpoint 重新开始！

# ✅ 正确：传 None 或 Command
graph.invoke(Command(resume=True), config)  # 从 interrupt 处继续
```

传了新的 `input_data` 会触发 PregelLoop 创建一个新的 `source = "input"` checkpoint——等同于从头开始。

**坑二：InMemorySaver 上生产**

```Python
# ❌ 开发环境跑通了，直接推到生产
graph = builder.compile(checkpointer=InMemorySaver())

# ✅ 生产环境用持久化后端
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
graph = builder.compile(checkpointer=AsyncPostgresSaver(pool))
```

InMemorySaver 在生产环境的表现是：每次部署重启后所有对话状态丢失。用了 SqliteSaver 但没挂持久卷（Docker/K8s 常见配置失误）同理。

**坑三：超长 thread_id**

```Python
# ❌ 把整个对话历史拼进 thread_id
thread_id = f"{user_id}-{session_id}-{timestamp}-{random_suffix}-..."

# ✅ 用短哈希
import hashlib
thread_id = hashlib.sha256(f"{user_id}:{session_id}".encode()).hexdigest()[:16]
```

### DeltaChannel：LangGraph 1.2 的增量存储改进

传统的 checkpoint 机制在每个 super-step 保存完整的 `channel_values`——一条 500 轮对话的 Agent 会话中，第 500 个 checkpoint 存储的是全部 500 轮的状态累积。存储复杂度是 O(N²)。

**DeltaChannel**（LangGraph 1.2+，beta）改变了这个逻辑：每个 checkpoint 只存储**增量**——本 super-step 新增的 channel 值。重建完整状态时，沿着 checkpoint 链从基快照开始，逐增量还原。

效果很直接。实测数据（2026 年 6 月 LangChain 官方博客，DeltaChannel RFC）：500 轮对话的完整快照模式占用约 4GB，DeltaChannel 配合 `snapshot_frequency=50`（每 50 个增量 checkpoint 保存一个完整快照做锚点）降到约 110MB——**约 41 倍**的存储缩减。

DeltaChannel 的 reducer（reducer，增量合并器）在**读取时**运行，而非写入时。这意味着写入 checkpoints 的开销极低——不计算合并，只做追加。读取时的合并操作沿着 checkpoint 链向前查找最近的完整快照，然后逐增量 apply，复杂度 O(增量数量)，而非 O(总 state 大小)。

`snapshot_frequency` 参数控制完整快照的频率。频率越低，存储越省，但重建状态的查找路径越长。50 是一个平衡点——既不会让查找路径超过 100 步，又能在长对话中维持 20 倍以上的压缩比。

与此同时，社区也在探索将 checkpoint 抽象为跨框架的 Agent 状态持久化标准，例如 langmcp（连接 LangGraph checkpointers 的 MCP 服务）[^agent-checkpoint-mcp]，Google 的 A2A 协议也从 Agent 任务生命周期角度探索了类似的概念——两者的驱动力一致：当 Agent 进入多框架协作的生产阶段，checkpoint 不再是 LangGraph 的一个功能，而是 Agent 基础设施的必选项。

---

从 Pregel 的 super-step 到 DeltaChannel 的增量快照，checkpoint 机制的核心思路一脉相承：它不是在"记录代码执行到哪一行"，而是在"记录图计算走到了哪一个一致状态"。这个区分对于一个习惯了代码断点调试的工程师来说不太直觉——但一旦接受了它，Agent 的持久化、恢复、回溯、分岔，全部在同一个模型下变得可解释。

*参考来源：*

- LangGraph Persistence 官方文档：[https://docs.langchain.com/oss/python/langgraph/persistence](https://docs.langchain.com/oss/python/langgraph/persistence)
- LangGraph Checkpointer 接口：[https://docs.langchain.com/oss/python/langgraph/checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers)
- LangGraph Pregel 运行时：[https://docs.langchain.com/oss/python/langgraph/pregel](https://docs.langchain.com/oss/python/langgraph/pregel)
- LangGraph Time Travel：[https://docs.langchain.com/oss/python/langgraph/use-time-travel](https://docs.langchain.com/oss/python/langgraph/use-time-travel)
- LangGraph Checkpoints API 参考：[https://reference.langchain.com/python/langgraph/checkpoints/](https://reference.langchain.com/python/langgraph/checkpoints/)
- Google Pregel 论文：Malewicz, G. et al., "Pregel: A System for Large-Scale Graph Processing", SIGMOD 2010
- arXiv:2604.28138 — Crab: A Semantics-Aware Checkpoint/Restore Runtime for Agent Sandboxes
- arXiv:2511.00628 — AgentGit: A Version Control Framework for Reliable and Scalable LLM-Powered Multi-Agent Systems
- arXiv:2607.08740 — Workflow as Knowledge: Semantic Persistence for LLM-Mediated Workflows
- arXiv:2606.06090 — Beyond Semantic Organization: Memory as Execution State Management for Long-Horizon Agents
- zalt.me — "Checkpoint Ledger: Deep Dive into LangGraph's Persistence Layer" (Dec 2025)：[https://zalt.me/blog/2025/12/checkpoint-ledger-langgraph](https://zalt.me/blog/2025/12/checkpoint-ledger-langgraph)
- vadim.blog — "Durable Execution: Agents That Survive Failure and Resume Where They Left Off" (Jun 2026)：[https://vadim.blog/durable-execution-agents-that-survive-failure-and-resume-where-they-left-off](https://vadim.blog/durable-execution-agents-that-survive-failure-and-resume-where-they-left-off)
- Towards AI — "LangGraph Checkpointing Is Not Free: A Production Postmortem" (Jun 2026)：[https://pub.towardsai.net/langgraph-checkpointing-is-not-free-a-production-postmortem](https://pub.towardsai.net/langgraph-checkpointing-is-not-free-a-production-postmortem)（可能需 Medium 登录）
- [^agent-checkpoint-mcp] langmcp — MCP server for LangGraph checkpointers：[https://github.com/xmassmx/langmcp](https://github.com/xmassmx/langmcp)
