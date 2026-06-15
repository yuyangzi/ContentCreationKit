# Agent Loop：所有 AI 编码工具的「同一个内核」

2026 年初，GitHub 上超过一半的代码是 AI 生成的。74% 的开发者已经在用 AI 编码工具。Cursor 拿到 20 亿美金 ARR，Claude Code 的 NPS 在开发者工具里高得离谱，Codex 顺着 ChatGPT 的渠道冲到了 300 万周活。

但如果你以为这些工具是靠各自的独门秘籍在竞争，那就搞错了。

我花了不少时间研究它们的底层实现——Claude Code、Codex、Cursor、LangGraph、smolagents，甚至翻了一些闭源工具的逆向工程笔记。结果发现了一件有点反直觉的事：**所有 AI 编码工具，底层跑的是同一个循环结构**。

不是"类似"——是同一个。

---

## 一、六行代码的本质

先看最核心的部分。

```python
while True:
    response = llm.invoke(messages + tools)
    if not response.tool_calls:
        break
    for tool_call in response.tool_calls:
        result = execute_tool(tool_call)
        messages.append(result)
```

大概六行。一个 while 循环，调 LLM，检查要不要调用工具，执行工具，把结果塞回消息列表，再来一轮。当 LLM 觉得信息够了、直接返回文字回复时，循环结束。

就是这么简单。

但如果你觉得这是全部，那你很快就会在生产环境摔跟头。这六行代码可能只占一个生产级 Agent 代码量的 5%。剩下的 95% 是围绕它的工程——上下文管理、安全控制、优雅降级、成本约束。

Steve Kinney 花了大量时间翻遍主流框架的源码后说了一句我特别喜欢的话：

> *"The loop is a solved problem. The engineering around the loop—context management, safety controls, graceful degradation, cost containment—is where all the interesting decisions live."*

翻译过来就是：循环本身已经没有秘密了，**秘密全在循环外面**。

那层壳才是决定一个 Agent 能不能跑进生产环境的关键。而这个进化的过程，可以分为三个清晰的段位。

---

## 二、Agent Loop 的三个段位

### Level 1：LLM + Tools + Response

你写个 Python 脚本，调一下 OpenAI API，扔两个工具函数进去。一跑——成了，模型开始调用工具了。完美。

Demo 演示时一片叫好。老板说"下周上线"。

然后问题来了：模型连续调用同一个工具却不推进任务；上下文越积越多，模型开始胡言乱语；遇到 API 报错，模型不知道怎么处理，原地打转。

上线两周，你把它关了。

Level 1 不是不能用——如果你的任务只有一步、没有状态、不需要持久化，它完全够用。但大多数现实任务不是这样的。

### Level 2：Lifecycle Inside the Loop

Level 1 到 Level 2 的跨越，核心是一件事：**记忆进入了循环**。

```
loop:
    context = memory.read()
    response = llm.invoke(context + tools)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = execute(tool_call)
            memory.write(tool_call, result)
```

读在 LLM 调用之前，写在工具执行之后。这个看似微小的变化，把 Loop 从一个"工具调用传输带"变成了"推理引擎"。

这也就是区分 memory-augmented（带个记忆包）和 memory-aware（真正知道并使用记忆）的分水岭。

大多数 AI 应用开发者都停在了 Level 1，觉得自己写了个 Agent。直到他们发现每次对话都像第一次一样，什么也记不住，才意识到 Level 2 的工程投入并不小。

### Level 3：Operations Inside and Outside the Loop

Level 3 才是真正区分玩具和产品的地方。

在这个阶段，Agent Loop 内外都有精心设计的操作在运行。有些是自动化的（Agent 不应该需要决定"要不要加载自己的历史记录"），有些是 Agent 主动触发的（Agent 自己决定什么时候去搜索网络）。

聚焦两个最关键的工程实践：

**第一，Context 压缩。**

每一轮 Loop 都在消耗上下文窗口。工具结果占了 Manus 实测数据的 67.6%——将近七成的 token 消耗在工具返回上。如果不加控制，Agent 跑个十几轮就触顶了。

解决方案是在窗口用到 80% 时就主动触发压缩：把早期对话摘要化，把可重新获取的工具输出替换成一行引用，释放空间给后续推理。Claude Code 的 SDK 在 95% 时自动压缩，但对大多数人来说，80% 更安全。

**第二，循环指纹检测。**

这是我最喜欢的一个机制。对每一轮迭代的 `(tool_name, result_preview)` 做哈希。如果连续三轮指纹完全一样——工具相同，返回结果也差不多——Agent 一定是卡住了。

听起来简单，但有多少系统栽在这上面？某生产环境，Agent 同一个回复重复了 **58 次**，才被人发现。58 次。

不是一次、两次，是 58 次。

除了这两个，Level 3 还需要：最大迭代限制（业界通行的 15-25 步）、优雅终止机制（超过限制时追加"请根据已有信息给出最优答案"，不带工具再调一次 LLM）、成本预算（比如单次运行设 2 美金上限）。

每一个都很无聊，但少一个都可能让你上事故报告。

> *"Most agent failures aren't about the model—they're about what happens when the loop runs without guardrails."*

---

## 三、Hermes Agent：自进化 Loop 的开源范本

前面讲的是理论。现在看一个具体的。

2026 年 2 月，Nous Research 开源了一个叫 Hermes Agent 的 AI 智能体。短短几个月 GitHub 上冲到 4 万星标，中文社区讨论热度极高。我刚开始以为又是个 OpenClaw 的换皮——用了才发现，它做了一个非常不一样的设计决策。

Hermes 的核心机制叫"闭环学习循环"。

**完成任务后，自动生成 Skills。**

以前你用一个 AI Agent 解决了一个复杂问题——比如配置 CI/CD 流程，或者排查了一个生产故障——下次遇到类似问题，一切从零开始。Hermes 的做法是：把解决过程打包成一个可复用的 Skill 文档（Markdown 格式），存起来。下次遇到类似场景，自动加载。

这意味着它的 Loop 不是平面循环，而是一个**学习飞轮**。

来看看记忆是怎么进入循环的（简化的伪代码）：

```
loop:
    # Level 2 的关键：Memory Read before LLM
    context = memory.read(project_knowledge)
    response = llm.invoke(context + tools)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = execute(tool_call)
            # Hermes 的自进化发生在这里
            memory.write(tool_call, result)
            if task_complex_enough:
                skills.create(task_summary)
```

把生成 Skills 的步骤硬编码进了循环里。不是开发者手动触发，不是外挂脚本——**循环自己驱动**。

Hermes 还有一个设计细节让我印象深刻。早期版本（2026 年 3 月之前）的记忆/Skill 提示是直接注入到用户消息里的。结果呢？43% 的用户消息里都夹带了这些"后台提示"，Agent 有时先处理这些提示再响应用户请求，喧宾夺主。

他们在 commit #2235 里修复了这个问题：把记忆/Skill 维护变成一个**后台 Review Agent**——主 Agent 响应完用户后才启动，共享记忆存储，使用相同的模型，零延迟影响。

触发条件是每 10 轮用户对话检查一次记忆，每 10 次以上的工具迭代检查一次 Skills。

> *"Most agents forget what they did last session. Hermes learns from it."*

其他 Agent 在乎的是单次会话的完成度。Hermes 在乎的是**跨会话的能力增长**。这是完全不同的设计哲学。

---

## 四、Loop 之后的下一站

Agent Loop 还有更远的未来吗？

学界已经在思考了。arXiv 上有一篇论文（2605.13850）提出了一个二维分类框架：把 Agent 架构按"认知功能"（感知、记忆、推理、行动、反思、协作、治理）和"执行拓扑"（链式、路由、并行、编排、循环、层次）交叉分析，得到了 28 种命名模式。

另一篇（2604.11378）则从调度理论的角度指出：Agent Loop 本质上是一个单就绪单元调度器——任何时刻只有一个任务在执行，下一个任务的选择由黑盒 LLM 推理决定。他们提出了一个叫 Graph Harness 的方案，把控制流从隐式的上下文提升为显式的有向无环图。

我的判断是：Loop 会一直存在，但它会从隐式控制流逐渐变成**显式图结构**。不是在 Agent 内部加一个 DAG——而是整条任务流水线变成可规划、可检查、可恢复的图。

就像 Linux 的 while 循环不会消失一样，Agent 的 while 循环也不会消失。但围绕它构建的工具、框架、治理层，会越来越厚重，也越来越强。

*"The while loop isn't changing. What's evolving is what we build around it."*

---

写到最后，我想起来 Steve Kinney 提到的一个数据：一个 100 行的 Agent（核心就是 6 行循环加一些工具定义），在 SWE-bench 上跑到了 74-76.8%。专业团队花了一年多时间打造的 SWE-agent，不过 80.9%。

**这六行循环，加上精心设计的工具和工程防护，就能达到专业 Agent 95% 的水平。**

所以如果你正在构建 AI Agent，别急着上框架。从 30 行版本开始。跑起来。然后加安全控制，加上下文管理，加可观测性。等你真的踩过那些坑，再回头看框架——那时的理解深度完全不一样。

说到底，循环是简单的那部分。**让它可靠地工作，才是全部。**
