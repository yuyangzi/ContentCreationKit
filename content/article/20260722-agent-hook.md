# Agent Hook：在概率推理之上，为 AI 代理叠加确定性控制

> 一个 Agent 在生产环境跑了三个月，token 消耗每月涨 40%，某个工具调用偶尔静默失败，永远找不到是哪个环节出了问题——而你连一个能插手的接口都没有。

我最早用 LangChain 做 Agent 的时候，写过这样一个"调试器"：在每个可能的调用点前面加 `print()`。LLM 调用之前 print，工具执行之后 print，Agent 思考步骤前后也 print。用了一段时间，发现如果 Agent 链有五层深度，三个工具来回调，终端里刷出来的日志就像有人拿脸在键盘上滚了一遍。

这种事大多数 Agent 开发者迟早会遇到。Agent 的执行过程是个黑盒——输入一段话，它自己在那儿想、搜、调工具、再想、再搜，最后吐一个结果。你看不到中间发生了什么、有没有调用不该调的工具、token 消耗到底是哪一步最多。

Hook 机制解决的，就是这个"看不见"和"拦不住"的问题。

---

## 没有 Hook 的时代：你只能猜

先回到最原始的场景。假设你用最直接的方式写了一个 Agent：把 prompt 塞给 OpenAI API，拿到返回的工具调用，执行工具，把结果再塞回去，循环到 Agent 觉得可以停了。

这个过程里，你能知道的只有两件事：你给了什么输入，最后拿到了什么输出。中间每一步——模型想了什么、工具执行了多久、有没有异常——大多无从得知。

有几种典型的事故会在这种架构下发生：

第一个，**token 消耗失控**。Agent 工作得很好，但你不知道它每次任务到底调了多少次模型。生产环境跑了一个月，一看账单翻了三倍，排查只能靠猜。因为它可能在某个环节反复重试（模型给出的工具调用参数不对，工具返回错误，模型换种写法再试，反复四五次）——而你很难察觉到这个循环的存在。

第二个，**工具调用静默失败**。Agent 调用了一个搜索 API，返回了空结果或者部分结果，Agent 没检测到异常，基于不完整的信息继续推理，最终给出一个看起来自洽但方向全错的结论。你事后复盘时，连"它到底搜了什么、搜到了什么"都看不到。

第三个，**安全边界失守**。Agent 有一个发送邮件的工具，设计意图是只让它在用户确认后调用。但因为没 hook 点，你只能在系统 prompt 里写"请勿在未经用户确认的情况下调用 send_email"。模型大部分时候遵守，偶尔忽略。这种事发生在 prompt 层面靠概率约束是不够的，但你又没有别的手段。

这三个问题的共同本质是：Agent 执行过程缺少**可插拔的拦截点**。你不能插进去看一眼，也不能插进去拦一下。

这里有一个关键认识：LLM 的输出是概率性的，不可靠的。你需要一个确定性的层叠在上面——这个层不负责"聪明"，只负责"规则"。Hook 就是这个确定性的层。

---

## 第一批解法：观察者模式的回调

LangChain 在 2023 年给出的第一个答案，就是回调系统（Callback System）。

它的设计思想很直接：把 Agent 执行过程抽象为一组**生命周期事件**——LLM 调用开始、LLM 调用结束、工具调用开始、工具调用结束、链开始、链结束、错误、重试。你不需要知道框架内部怎么跑的，只需要在这些事件点上注册你的处理函数。

[Zylos Research 在 2026 年 3 月的一篇分析](https://zylos.ai/research/2026-03-27-ai-agent-hooks-middleware-runtime-behavior-control)把它归类为**事件驱动的观察者模式**——框架是发布者（Publisher），它按固定节奏发布事件；你的回调处理器是订阅者（Subscriber），接收事件并执行自定义逻辑。关键特征是：**订阅者只能观察，不能修改执行流**。

LangChain 的 `BaseCallbackHandler` 是一个基类，继承了六个 Mixin：

| Mixin | 监听的事件 | 做什么 |
|-------|-----------|--------|
| `LLMManagerMixin` | `on_llm_start/end/error`, `on_llm_new_token` | 追踪模型调用、流式输出 |
| `ChainManagerMixin` | `on_chain_start/end/error`, `on_agent_action/finish` | 追踪链的启动和结束 |
| `ToolManagerMixin` | `on_tool_start/end/error` | 追踪工具调用 |
| `RetrieverManagerMixin` | `on_retriever_start/end/error` | 追踪文档检索 |
| `CallbackManagerMixin` | 回调注册 | 管理器自身 |
| `RunManagerMixin` | `on_text`, `on_retry`, `on_custom_event` | 通用事件 |

每个事件携带一个 `run_id` 和 `parent_run_id`，所有事件天然构成一棵执行树。这个设计让 tracing 变得非常简单——你不需要自己拼父子关系，框架在触发事件时就把链路搭好了。

用起来大概是这样的：

```Python
from langchain_core.callbacks import BaseCallbackHandler

class SimpleLogger(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, *, run_id, **kwargs):
        print(f"[LLM Start] {run_id}, Prompt: {prompts[0][:50]}...")

    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"[Tool Start] {serialized['name']}, Input: {input_str}")

    def on_llm_end(self, response, **kwargs):
        token_usage = (response.llm_output or {}).get("token_usage", {})
        print(f"[LLM End] Tokens: {token_usage}")

handler = SimpleLogger()
# chain 可以是任意 LangChain Runnable（如 LLMChain、AgentExecutor 等）
chain.invoke({"input": "..."}, config={"callbacks": [handler]})
```

这在当时解决了一个实在的痛点：你终于能"看见" Agent 内部在干什么了。不需要在每个节点插 `print()`，不需要事后翻日志猜执行路径。日志、监控、成本追踪，这些需求在回调出现之前基本靠框架魔改和 monkey-patch。

LangSmith、LangFuse、Weights & Biases 这些可观测性平台，底层全都建立在 LangChain 的回调总线上。`LangChainInstrumentor().instrument()` 这一行代码背后，就是注册了一个 OTel 适配器到回调管理器上，自动把每个事件转为 OpenTelemetry Span。

---

## 能看，不能动：回调的边界

回调解决了"看见"的问题。但生产环境跑久了，你很快会发现另一类需求是回调无法满足的。

来看看这些场景：

**权限与预算拦截**。你的 Agent 挂了 20 个工具，但某些任务——比如面向外部用户的服务——它只能使用其中 5 个。同时你想对每个用户设定每日 token 配额，超限时自动切换低成本模型或直接拦截。这两类需求都需要在调用前检查并阻断。

**PII 脱敏**。用户输入可能包含手机号、身份证号、邮箱。你希望在 prompt 送进 LLM 之前，自动识别并脱敏。

**人工审批门控**。Agent 要发送邮件、执行数据库写入、调用支付接口——这些操作你需要人工看一眼再放行。

这些需求的共同特征是：你需要的不是"看见"，而是**修改或阻断**。

而回调做不到这一点。回调是观察者——它接收事件，可以记录、可以上报、可以报警，但它不能修改事件携带的数据，不能阻止事件对应操作的执行。回调里返回 `False` 不会让工具调用中止，回调里修改 `prompts` 不会改变 LLM 实际收到的输入。

[DZone 2026 年 6 月的一篇分析](https://dzone.com/articles/middleware-gap-in-ai-agent-frameworks)把这个问题定性为"中间件差距"（Middleware Gap）：

| 能力 | 中间件 | 回调 |
|------|--------|------|
| 修改 system prompt | 是 | 否 |
| 动态过滤工具列表 | 是 | 否 |
| 转换消息历史 | 是 | 否 |
| 取消模型调用 | 是 | 否 |
| 跨轮次追踪状态 | 是 | 部分 |
| 观察输出 | 是 | 是 |

这个差距不是实现上的疏忽，而是架构约束。观察者模式的设计前提就是"订阅者不改变被观察对象的状态"。要突破这个约束，需要一种新的抽象。

---

## AgentMiddleware：从观察到干预

2026 年 3 月，LangChain 在 1.0 版本的 `create_agent` 中引入了一个新的抽象：`AgentMiddleware`。它不再是回调的演进版，而是一套完全不同的设计哲学。

[官方博客](https://www.langchain.com/blog/how-middleware-lets-you-customize-your-agent-harness)是这样定位它的："中间件让你可以在 Agent 利用 LLM 的动态推理能力的同时，叠加确定性的业务策略。"

中间件的灵感来源是 Web 框架的中间件模式——Express 和 Koa 的洋葱模型。如果你写过 Koa，对这个模式不会陌生：请求从最外层中间件进入，逐层向内传递，到达核心（LLM 调用或工具执行），然后响应逐层向外返回。

AgentMiddleware 定义了五个钩子点：

| 钩子 | 触发时机 | 能做什么 |
|------|----------|----------|
| `before_agent` | Agent 启动时，仅一次 | 加载记忆、校验输入 |
| `before_model` | 每次 LLM 调用前 | 裁剪历史、PII 脱敏、动态过滤工具 |
| `wrap_model_call` | 包裹整个 LLM 调用 | 缓存、重试、模型回退、动态工具选择 |
| `after_model` | 每次 LLM 响应后 | 人工审批、输出校验、结果转换 |
| `after_agent` | Agent 结束时，仅一次 | 清理、通知、持久化 |

还有 `wrap_tool_call` 包裹工具执行，用于审批门控和沙盒。

关键不是多了几个钩子，而是这些钩子的**组合方式**。多个中间件按注册顺序组合成洋葱结构：

```
[before_agent_1] → [before_agent_2] → [before_model] → [wrap_model_call] → LLM → [after_model] → [after_agent_2] → [after_agent_1]
```

`before_*` 按注册顺序进入，`after_*` 逆序展开。`wrap_*` 从最外层开始嵌套。

来看一个实际的例子。假设你要实现三个需求：PII 脱敏、成本追踪、人工审批。怎么写：

```Python
from langchain.agents import create_agent
from langchain.agents.middleware import (
    PIIMiddleware,
    HumanInTheLoopMiddleware,
    SummarizationMiddleware,
    ModelRetryMiddleware,
)

agent = create_agent(
    model="gpt-4o",
    tools=[search_tool, email_tool, db_tool],  # 示意：实际的工具对象需预先定义
    middleware=[
        PIIMiddleware("email", strategy="redact"),
        PIIMiddleware("phone", strategy="redact"),
        SummarizationMiddleware(
            model="gpt-4o-mini",
            trigger=("tokens", 8000),
            keep=("messages", 4),
        ),
        ModelRetryMiddleware(max_retries=3, backoff_factor=2),
        HumanInTheLoopMiddleware(
            interrupt_on={"send_email": True, "db_write": True}
        ),
    ],
)
```

执行时发生了什么：

1. 用户输入先经过 `PIIMiddleware` 的 `before_agent`，手机号和邮箱被替换为 `[REDACTED]`
2. 进入 `SummarizationMiddleware` 的 `before_model`，如果对话历史超过 8000 token，自动用 `gpt-4o-mini` 压缩
3. `wrap_model_call` 由 `ModelRetryMiddleware` 包裹——LLM 调用失败时自动重试，退避 2s → 4s → 8s
4. Agent 决定调用 `send_email`，`HumanInTheLoopMiddleware` 的 `wrap_tool_call` 拦截住，弹出审批
5. 所有步骤中，回调系统继续工作，把事件流推送给 LangSmith

这里有一个重要的设计选择：**中间件运行在 `create_agent` 编译出的 LangGraph 图内部**，不是外部附加层。这意味着中间件可以访问和修改 Agent 的运行时状态（state），可以在 `before_agent` 中通过 `can_jump_to=["end"]` 直接终止整个执行流程。

这也解释了为什么回调无法实现中间件的功能：回调在运行时图的外部观察事件，中间件在图内部参与执行。

LangChain 1.0 预置了五类中间件：

- `SummarizationMiddleware`：token 阈值监测 + 历史压缩
- `HumanInTheLoopMiddleware`：工具调用前的人工中断
- `PIIMiddleware`：检测和脱敏
- `ModelRetryMiddleware`：指数退避重试
- `ShellToolMiddleware`：shell 资源生命周期管理

---

## 生态位：其他框架怎么做的

在 LangChain 演进的同时，其他 Agent 框架也在各自的 Hook 系统上做出了不同的设计选择。这些选择的差异，本质上反映了对"Agent 应该如何被控制"这个问题的不同回答。

**CrewAI 选择了一条更简单的路径——装饰器式 Hook**：

```Python
from crewai import CrewBase
from crewai.hooks import before_llm_call, after_tool_call, LLMCallHookContext, ToolCallHookContext

@CrewBase
class MyCrew:
    @before_llm_call
    def add_system_context(self, context: LLMCallHookContext):
        context.messages.insert(0, {
            "role": "system",
            "content": "当前用户等级: VIP"
        })

    @after_tool_call
    def validate_result(self, context: ToolCallHookContext):
        if context.tool_result is None:
            return "工具返回空结果，请换一种方式重试"
```

CrewAI 的钩子可以直接修改上下文对象——`context.messages` 和 `context.tool_input` 是可变的。而且钩子返回值会影响执行：`@before_llm_call` 返回 `False` 会阻断 LLM 调用；`@after_tool_call` 返回字符串会替换工具结果。这种设计对简单场景非常友好，但全局注册机制的副作用是多个钩子的执行顺序依赖于注册先后，组合起来不够透明。

**OpenAI Agents SDK 采用了双作用域设计**——`RunHooks` 跨越整个 `Runner.run()`（包括 Agent 移交），`AgentHooks` 附加到特定 Agent 实例。两个作用域共享相同的事件签名（`on_agent_start`、`on_llm_start`、`on_tool_start` 等），但都是纯观察者模式，不能修改或阻断。它的核心价值在于**移交（handoff）感知**——当 Agent A 把控制权移交给 Agent B 时，`on_handoff` 事件同时传递给两个作用域，这是多 Agent 协作场景下的关键能力。

**LlamaIndex 和 AutoGen 选择了差异更大的路径**。LlamaIndex 在 v0.10.20 后从 `CallbackManager` 迁移到 `instrumentation` 模块，用 `Dispatcher` 实现层级事件传播（类似 Python logging 的冒泡机制），并把 `Event`（单点时刻）和 `Span`（持续操作）分离，让 tracing 语义更清晰。AutoGen v0.4 则走消息总线路线——Agent 之间通过消息传递而非直接调用，`intervention_handler.on_send` 可以在消息发送前拦截工具调用，天然支持分布式多 Agent 系统，但代价是中间件的组合顺序变得不可预测。

有一个值得单独讨论的框架是 **Vercel AI SDK 7（2026 年发布）**，它在 Agent 接口上直接内置了生命周期回调。`onStart` → `onStepStart` → `onToolExecutionStart` → `onToolExecutionEnd` → `onStepEnd` → `onEnd` 的事件序列，加上 `toolApproval` 中断机制，以及 `WorkflowAgent` 支持进程重启后恢复，把 Hook 的语义从框架层提升到了接口规范层。

---

## 三个你一定要知道的坑

不论用哪个框架的 Hook，有三类问题是反复出现的事故源头。

### 坑一：同步回调阻塞异步 event loop

这是影响最大的性能问题，波及范围也最广。

LangChain 的 `StdOutCallbackHandler` 默认同步运行，底层的 `BaseCallbackManager` 使用 `ThreadPoolExecutor(max_workers=1)`。当并发超过 15 时，这个单线程队列开始拥塞。基准测试数据显示：20 并发时 p95 延迟从 320ms 暴涨到 4.8 秒——增长了 12 到 15 倍（[Markaicode SGLang + LangChain 基准测试](https://markaicode.com/stack/sglang-langchain-stack/)）。

根因不是回调逻辑重，而是队列在等。所有回调处理排队等一个 worker 线程，而这个 worker 线程又被下一个 LLM 调用依赖——因为框架要等回调处理完才继续。

修复方案三选一：设置 `LANGCHAIN_CALLBACKS_WORKERS=4` 环境变量；所有生产回调继承 `AsyncCallbackHandler` 而非 `BaseCallbackHandler`；在不需要回调的路径上把 `model.callbacks` 置空。

### 坑二：在回调中做同步 I/O

这是一个逻辑正确但工程错误的选择。

你在 `on_llm_end` 里调了 `requests.post("https://api.cost-tracker.com", json=data)`。看起来没问题——数据确实需要上报。但 `requests.post` 是同步的，这意味着每次 LLM 调用都要等这个 HTTP 请求完成才能返回。如果你的成本追踪 API 响应时间是 200ms，那每次 Agent 调用就被无意义地加了 200ms 延迟。

正确做法：回调只做内存队列的 enqueue。一个独立的 `BatchSpanProcessor` 在后台线程批量 flush。上报延迟不影响 Agent 关键路径。

### 坑三：混淆 Callback 和 Middleware 的能力边界

这与其说是坑，不如说是一种常见的框架误用。

你需要阻断某个工具调用，于是在 `BaseCallbackHandler.on_tool_start` 中写了逻辑。它不 work——回调不能阻断执行。你需要的是 `AgentMiddleware.wrap_tool_call`。

反过来，你只是想做日志输出，却写了一个完整的 `AgentMiddleware`——这当然可以 work，但复杂度远超需求。一个 `StdOutCallbackHandler` 就够了。

经验法则是：**观察用回调，修改用中间件**。需要读数据、做统计、推送到外部平台——回调；需要改 prompt、过滤工具、阻断执行则交给中间件。

---

## 把 Hook 用好：五条实践准则

这些准则来自生产环境的反复验证，不是理论推演。

**一、用 instrumentor 替代手写 tracing handler。** `LangChainInstrumentor().instrument()` 一行代码接入 OpenTelemetry，比你手动管理 `run_id` 拼树健壮得多。手写 handler 容易在并行调用时把 `parent_run_id` 搞混——Langfuse 的 [Issue #3491](https://github.com/langfuse/langfuse/issues/3491) 就是一个典型案例：全局单例 callback handler 在 asyncio 并行调用时，`run_id → span` 映射出现竞态，导致 `KeyError`。只在需要**业务特有信号**时才自定义 handler。

**二、控制基数爆炸。** 三个最常见的基数地雷：把用户原始输入作为 span attribute（PII 风险 + 聚合失效）；每个 retriever chunk 单独建 span（50 chunks × 千次查询 = 数百万唯一 attribute 值）；把 request ID 嵌入 span name（每个 span name 唯一，聚合查询完全失效）。用 JSON 数组替代单个 chunk span，用 `gen_ai.input.messages` 作为 opt-in 属性而非默认开启。

**三、尾部分段采样，而非头部采样。** 深度 Agent 链通常产生每请求 20 到 100 个 span。如果只在头部 1% 采样，你会丢失 99% 的失败链路。正确的策略是：100% 保留所有 ERROR 链路；100% 保留低 eval 分数链路；100% 保留超过延迟或成本阈值的链路；其余 5% 到 20% 均匀采样。这个逻辑可以放在高流量的 collector 端执行。

**四、HITL 中断前后提防 double-execution。** LangGraph 的 `interrupt()` 在 resume 时**整个 node 从头重执行**。如果你在 `interrupt()` 之前调了外部 API 或发了通知，resume 时会再执行一次。把审批逻辑放在独立 node 里，有副作用的操作放在 `interrupt()` 之后。

**五、中间件组合时注意顺序。** 在洋葱模型中，`before_*` 钩子的执行顺序就是策略的执行顺序。把 PII 脱敏放在日志记录之前，脱敏后的内容不会出现在日志中。反过来，先记录日志再脱敏，原始手机号就泄露到日志系统里了。这不是框架的 bug，是你自己编排的策略链。

---

Agent Hook 的演进，本质上是一个"确定性控制层"逐步侵入"概率性推理引擎"的过程。2023 年的回调只能看，2026 年的中间件可以拦、可以改、可以跳。这个趋势不太可能停在框架层——AWS AgentCore Gateway 已经把 Hook 下沉到了网络基础设施层，MCP 协议虽然还没有原生的拦截机制（这是一个会持续很久的争议点），但 Agent Protocol、A2A、OpenTelemetry GenAI 语义约定已经在标准化不同层次的控制点。

无论这些基础设施怎么演变，那条经验法则不会变：想让 Agent 做什么，靠 prompt；不想让 Agent 做什么，靠 hook。

---

*参考来源：*
- Zylos Research, "AI Agent Hooks and Middleware: Runtime Behavior Control", 2026-03-27. https://zylos.ai/research/2026-03-27-ai-agent-hooks-middleware-runtime-behavior-control
- DZone, "The Middleware Gap in AI Agent Frameworks", 2026-06. https://dzone.com/articles/middleware-gap-in-ai-agent-frameworks
- LangChain Blog, "How Middleware Lets You Customize Your Agent Harness", 2026-03. https://www.langchain.com/blog/how-middleware-lets-you-customize-your-agent-harness
- LangChain, "Custom Middleware Documentation". https://docs.langchain.com/oss/python/langchain/middleware/custom
- LangChain Callbacks Source Code. https://github.com/langchain-ai/langchain/blob/master/libs/core/langchain_core/callbacks/base.py
- CrewAI, "Execution Hooks Documentation". https://docs.crewai.com/en/learn/execution-hooks
- OpenAI Agents SDK, "Lifecycle Reference". https://openai.github.io/openai-agents-python/ref/lifecycle/
- LlamaIndex, "Instrumentation Module Documentation". https://developers.llamaindex.ai/python/framework/module_guides/observability/instrumentation/
- AutoGen, "Tool Use with Intervention". https://microsoft.github.io/autogen/0.4.9/user-guide/core-user-guide/cookbook/tool-use-with-intervention.html
- Vercel AI SDK 7, "Building Agents". https://ai-sdk.dev/v7/docs/agents/building-agents
- Markaicode, "SGLang + LangChain Performance Benchmark". https://markaicode.com/stack/sglang-langchain-stack/
- Langfuse, "Issue #3491: LangchainCallbackHandler KeyError in parallel async calls". https://github.com/langfuse/langfuse/issues/3491
- OpenTelemetry, "GenAI Observability in 2026". https://opentelemetry.io/blog/2026/genai-observability
