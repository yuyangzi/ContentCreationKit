# AI Agent 的 Human-in-the-Loop 设计：从审批疲劳到分层防御

2026年5月，Anthropic 工程博客披露：Claude Code 用户对权限提示的批准率大约 93%（Anthropic Engineering, 2026.05）。换句话说，Agent 每弹 100 次确认框，用户点 93 次"允许"、7 次"拒绝"。这 7 次拒绝分散在大量低风险操作中，真正危险的（读到一半的 shell 脚本里藏着 `rm -rf /`）很少有机会被单独拦截。Anthropic 稍早的一项研究显示，使用超过 750 个 session 的老用户中，大约 40% 直接开启了全自动批准模式，连确认框都省了（Anthropic, 2026.02）。

> Anthropic 的结论很直白："The more approvals a user sees, the less attention they pay to each, becoming over time much less diligent in their supervision."

Human-in-the-Loop（HITL，人机闭环）这个概念本身没有问题——让 Agent 在关键决策点暂停，等待人类审批、修正或拒绝。问题是，当"每一小步"都变成"关键时刻"，人类就不再是安全阀，而是审批流水线上的一颗螺丝。审批疲劳的成因与缓解路径，是整件事的核心。

---

## 审批疲劳的三个信号

审批疲劳不是主观感受，它有三条可观测的硬指标。

- **审批延迟坍缩**：当用户从读完提示、思考风险、再点确认，退化到肌肉记忆式的回车（每次审查耗时不到 1 秒），说明审查已经变成过场
- **通过率趋近 100%**
- **拒绝率趋近零**

这三条信号同时出现，意味着 HITL 在形式上还在，在实质上已经失效。

更隐蔽的风险是点击穿透疲劳（clickthrough fatigue，也有文献称 clickthrough vulnerability）——攻击者不需要绕过审批系统，只需要把一次恶意操作混在大量无害操作中。以 93% 的通过率计算，恶意操作有 93% 的概率被直接放行。正如 tianpan.co 在 2026 年 6 月的一篇文章里指出的：把所有操作都交给人类审批，等于把安全责任转嫁给了最疲劳的那一环。

---

## 从"审批一切"到"分层防御"

问题的根源不是人类不够认真，而是 HITL 的默认策略错了。给所有操作一个统一的审批门槛，等于在说"我分不清哪些操作危险、哪些操作安全"，于是把分类工作外包给了已经疲劳的人类。

正确的方向是让系统自己做好分类，只把人类真正需要介入的决策推上来。

Digital Applied 在 2026 年的一篇文章里把 Agent 操作按风险分成四档：

- T1：只读或内部操作，自动执行加日志
- T2：可逆写入，自动执行加日志
- T3：外部可逆操作，进入审查队列
- T4：不可逆或高代价操作，强制审批

这套分类的工程意义在于，它把大多数可逆或只读操作从审批链上摘掉，剩下的人类端才需要真正审视——不是"Agent 要读哪个文件"这种程度的问题，而是"Agent 要删哪个数据库"这种级别。

---

## 异步架构：审批不应该阻塞 Agent

分层分类解决了"审什么"，但还有一个问题：怎么审。传统的同步审批（Agent 暂停，弹出确认框，等人类点完继续）在工程上代价很高。以 AWS API Gateway 为例的 29 秒硬超时、Serverless 的执行时长上限，都让同步等待在工程上代价不菲。

异步架构的做法是：Agent 执行到需要审批的节点时，中断当前状态，返回 202 Accepted，将审批请求推入外部队列。人类在审批端（Web、Slack、移动端）做出决定后，通过 webhook 回调 resume 端点，Agent 从断点恢复执行。

LangGraph 给了这个模式一个很干净的 API 表达。`interrupt()` 在图的任意节点把状态持久化到 Checkpointer（Postgres、SQLite 或 Redis），然后暂停。外部通过 `Command(resume=payload)` 在同一个 `thread_id` 上恢复：

```Python
from langgraph.types import interrupt, Command
from typing import Literal

def approval_node(state: ApprovalState) -> Command[Literal["proceed", "cancel"]]:
    decision = interrupt({
        "question": "Approve this action?",
        "details": state["action_summary"],
        "risk_level": state["risk_level"],
        "payload_hash": state["payload_hash"],
    })
    return Command(goto="proceed" if decision else "cancel")
```

`interrupt()` 不只是暂停——它把当时的状态快照写进 Checkpointer，这意味着审批端可以随时调出完整的上下文，而不是只看一行 `DELETE FROM users` 就做决定。resume 时传入的 payload 会替换中断点的返回值，Agent 拿到这个值继续走后续逻辑。

OpenAI Agents SDK 则走了另一条路：`@tool` 装饰器的 `needs_approval` 回调。它在工具调用层面做拦截，而不是在图的节点层面：

```Python
from agents.decorators import tool

async def needs_approval(_ctx, params, _call_id) -> bool:
    return "Oakland" in params.get("city", "")

@tool(needs_approval=needs_approval)
async def get_temperature(city: str) -> str:
    return f"The temperature in {city} is 20° Celsius"
```

两种思路的差异体现了框架对 HITL 的定位不同。LangGraph 把审批当作图中的一个节点，状态管理是框架原生能力。OpenAI Agents SDK 把审批当作工具调用前的过滤器，状态持久化需要开发者自己处理。

---

## 五层防御：HITL 只是其中一层

把 HITL 放在一个更大的防御架构里看，它只是第四层。Changkun's Blog 在 2026 年的一篇文章里梳理了一套五层模型：

1. 确定性策略门（allow/deny lists）：不经过模型，不经过人类，规则直接判
2. 宪法自评：Agent 按自身宪法原则（constitutional principles）评估自己的输出
3. AI 监督者：处理 Agent 自评后仍不确定的情况
4. Human-in-the-Loop：不可逆或新颖的操作
5. 审计追踪 + 事后复核：操作留痕，事后可追溯

这个架构的隐含前提是：前面三层能拦住绝大多数决策，HITL 只处理前三层都搞不定的边缘情况。这不是说人类不重要——恰恰相反，正是因为人类重要，才不应该把人类的注意力浪费在机器能自动判断的事情上。

在 HITL 之上还有两个概念：HOTL（Human-on-the-Loop，监督加否决，异常时介入）和 HOOTL（Human-out-of-the-Loop，不实时参与，事后审计）。这三分法在行业实践中被广泛采用，Lazaros 等人 2026 年 Entropy 期刊的学术综述则给出了更细的五分类体系。三者不是互斥的——同一个系统里，T4 操作走 HITL，T3 走 HOTL，T1 和 T2 走 HOOTL。

---

## 三个容易被忽略的工程细节

HITL 的陷阱不只是"人类疲劳"这种表面问题，还有几个藏在代码层面但杀伤力不小的细节。

**Payload 完整性（hash pinning）。** 审批时看到的 payload 和执行时用的 payload 可能不是同一份。工程上的常见做法是：在审批时刻对 payload 做 hash，执行时重新校验，不匹配就回滚。没有这个机制，审查者批准的是 A，执行的是 B——攻击者只需要在审批窗口和执行窗口之间替换 payload。

**幂等（CAS 模式）。** webhook 会重试，人类会双击。如果 resume 端点没有幂等保护，一次审批可能触发两次执行。工程上常用的幂等方案是 Compare-and-Swap（比较并交换）：`UPDATE ... WHERE status = 'awaiting_approval' RETURNING id`，或者在 Redis 里用 `SET NX`。状态机保证从"等待审批"到"已批准"的转换只发生一次。

**子 Agent 绕过陷阱。** 这是一个真实出过的 bug：父 Agent 的审批层拦截了所有工具调用，但子 Agent 通过独立的 tool binding 绕过了这一层。Production Notes 在 2026 年 6 月记录了这个问题。修复方向是：所有 tool binding（不管来自哪个 Agent）都走同一个治理中间件（governance middleware），审批层不依赖"调用者是谁"来做判断。

---

## 框架对比：HITL 的实现方式

不同框架对 HITL 的支持程度差异很大。以下对比基于 2026 年中各框架的稳定版本：

| 框架 | HITL 机制 | 状态持久化 | 异步支持 |
|------|----------|-----------|---------|
| LangGraph | `interrupt()` + `Command(resume=)` | 原生 Checkpointer | 原生异步 |
| OpenAI Agents SDK | `needs_approval` + RunState | 手动序列化 | 手动 |
| CrewAI | `human_input=True` / `@human_feedback` | Flow state + webhook | webhook（Enterprise） |
| AutoGen | UserProxyAgent 阻塞 | 内存（阻塞 team） | 仅同步阻塞 |
| Semantic Kernel | AutoFunctionInvocationFilter | Kernel state | 基于过滤器 |

LangGraph 在异步长时暂停场景下占优，核心原因是它的 Checkpointer 把状态管理变成了框架能力而非开发者负担。异步支持也不是锦上添花——在生产环境里，一个同步阻塞的审批会把整个 Agent 管道卡住，直到人类喝完咖啡回来。Google ADK、Microsoft Agent Framework 等框架也提供了各自的异步 HITL 能力，实现路径不同，各有侧重。

---

## 毕业阶梯：操作如何挣出自己的"免审权"

除了静态的风险分级，还可以给操作设计一套"毕业阶梯"（Graduation Ladder，类似工业界的 Progressive Autonomy / Autonomy Ladder 思路）：操作不是永远被锁在某个风险等级里，满足条件后可以降级。降级条件大致包括：

- 长期累计执行，无安全事故
- 回滚率保持低位
- 运行足够长时间，行为稳定
- 不涉及策略变更或合同约束
- 回滚操作可快速完成且有文档记录

这套机制的价值在于，它让 HITL 从"一刀切"变成了"动态调整"——操作越可靠，越少占用人类注意力。同时它把"可回滚"当作降级的前置条件：如果一个操作在降级后出了问题，系统能快速恢复，而不是让人类去救火。

批准按钮的防误触是另一个值得留意的细节：给 Approve 按钮加短暂的 hover 延迟，防止误触。太短等于没加，太长又回到审批疲劳，需要取"手比脑快"和"脑比手快"之间的临界值。

---

## 理论根基：从 corrigibility 到 interruptibility

HITL 不是一个工程上的临时补丁，它在 AI 安全理论里有更深的根基。

Soares 等人在 2015 年提出了 corrigibility（可纠正性）的概念：一个 AI 系统应该配合人类对它的修改或关机，而不是发展出阻止这些操作的目标。四年后，Orseau 和 Armstrong（2016）把这个问题推进到更具体的层面，提出了 interruptibility（可中断性）：一个被中断的 Agent 不应从"被中断"这件事中学到"下次要避免被中断"的激励。换句话说，Agent 不应该因为你点了暂停就学会以后不再让你暂停。

这两条线的理论共同指向一个安全原则：Agent 架构应允许外部干预，且干预行为本身不应改变 Agent 的策略模型。LangGraph 的 `interrupt()` 机制实现了前一半（可以在任意节点暂停），但后一半"不被中断所激励"目前更多是训练层面的问题，框架层面还没有成熟的方案。

更近期的研究在往"Agent 知道自己不知道"的方向推进。Ren 等人在 CoRL 2023 上提出的 KNOWNO 框架，让 Agent 在不确定性超过阈值时主动求助，而不是硬着头皮猜一个可能出错的答案。这和 Anthropic 观测到的"Claude Code 在复杂任务上主动暂停的频率超过人类打断的频率"是一脉的思路——Agent 的自我感知能力，是 HITL 从"被迫暂停"走向"主动协作"的关键。

还有一个原则值得注意：最小权限原则（Principle of Least Privilege，也可表述为 Minimal Footprint）。Agent 不应获取超出即时任务所需的资源。如果 Agent 当前的任务是"查看今日天气"，它就不应该持有数据库写入权限。权限最小化减少了需要审批的操作数量，也缩小了审批疲劳的覆盖面。

---

2026 年是 HITL 从设计理念走向工程规范的一年。EU AI Act 第 14 条要求所有高风险 AI 系统具备 meaningful human oversight（有意义的人类监督），高风险义务原定 2026 年 8 月进入执法阶段（经 Digital Omnibus 修正案，Annex III 通用高风险系统推迟至 2027 年 12 月，Annex I 受监管产品中的 AI 推迟至 2028 年 8 月）。与此同时，arXiv 上 2604.04918 号论文（2026 年 4 月）通过 48 名参与者的实证研究比较了四种 Agent 监督策略，其中三种来自既有系统：Action Confirmation（Anthropic Claude Computer Use，每步审批）、Risk-Gated（OpenAI Operator，仅高风险升级）、Supervisory Co-Execution（Microsoft Magentic-UI，计划层审查），第四种是论文提出的 Structurally Enriched。三种对照策略分别回答了"审什么"的不同理解——是审每一步操作、审高风险操作，还是审整体计划。

但 93% 这个数字背后，HITL 的真正困境不是"人类不够"，而是"不该让人类做的事，就不该交给人类"。审批更多不会更安全，审批更少但更准才会。Agent-as-a-Judge 正在快速工业化（用模型审查模型），但同态偏见和模型合谋风险也随之而来，人类校准仍然是必选项，至少在那些"模型说没问题但我总觉得不对劲"的决策上。

HITL 不是让人类更忙，是让人类只做 AI 做不了的决定。

*参考来源：*

- Anthropic Engineering: How we contain Claude across products (2026.05): [https://www.anthropic.com/engineering/how-we-contain-claude](https://www.anthropic.com/engineering/how-we-contain-claude)
- Anthropic: Measuring AI agent autonomy in practice (2026.02): [https://www.anthropic.com/research/measuring-agent-autonomy](https://www.anthropic.com/research/measuring-agent-autonomy)
- Anthropic Engineering: Claude Code auto mode (2026): [https://www.anthropic.com/engineering/claude-code-auto-mode](https://www.anthropic.com/engineering/claude-code-auto-mode)
- Soares et al., Corrigibility (2015): [https://intelligence.org/files/Corrigibility.pdf](https://intelligence.org/files/Corrigibility.pdf)
- Orseau & Armstrong, Safely Interruptible Agents (2016): [https://intelligence.org/files/Interruptibility.pdf](https://intelligence.org/files/Interruptibility.pdf)
- Ren et al., Robots That Ask For Help: Uncertainty Alignment for Large Language Model Planners (CoRL 2023, 提出 KNOWNO 框架): [https://arxiv.org/abs/2307.01928](https://arxiv.org/abs/2307.01928)
- Lazaros et al., Human-in-the-Loop Artificial Intelligence: A Systematic Review of Concepts, Methods, and Applications (Entropy 28(4), 377, 2026): [https://doi.org/10.3390/e28040377](https://doi.org/10.3390/e28040377)
- arXiv:2604.04918, Comparing Human Oversight Strategies for Computer-Use Agents (2026.04): [https://arxiv.org/abs/2604.04918](https://arxiv.org/abs/2604.04918)
- Production Notes: The HITL Paradox — When Human Approval Makes Agents Worse (2026.06): [https://productionnotes.dev/blog/hitl-paradox](https://productionnotes.dev/blog/hitl-paradox)
- Tian Pan: Approval Fatigue: How Human-in-the-Loop Gates Decay Into Rubber Stamps (2026.06): [https://tianpan.co/blog/2026-06-25-approval-fatigue-how-human-in-the-loop-gates-decay-into-rubber-stamps](https://tianpan.co/blog/2026-06-25-approval-fatigue-how-human-in-the-loop-gates-decay-into-rubber-stamps)
- Changkun Ou: Confirmation Fatigue and the Protocol Gap in Agentic AI Oversight (2026): [https://changkun.de/blog/ideas/human-in-the-loop-agents](https://changkun.de/blog/ideas/human-in-the-loop-agents)
- Digital Applied: Human-in-the-Loop Escalation Design for AI Agents (2026.06): [https://www.digitalapplied.com/blog/human-in-the-loop-escalation-design-ai-agents-2026](https://www.digitalapplied.com/blog/human-in-the-loop-escalation-design-ai-agents-2026)
- Waxell.ai: Human-in-the-Loop vs Human-on-the-Loop (2026): [https://waxell.ai/blog/human-in-the-loop-vs-human-on-the-loop-ai-agents](https://waxell.ai/blog/human-in-the-loop-vs-human-on-the-loop-ai-agents)
- LangGraph Documentation: interrupt() and Command(resume=): [https://langchain-ai.github.io/langgraph/](https://langchain-ai.github.io/langgraph/)
- OpenAI Agents SDK Documentation: needs_approval: [https://openai.github.io/openai-agents-python/](https://openai.github.io/openai-agents-python/)
- EU AI Act, Article 14: Human Oversight: [https://eur-lex.europa.eu/](https://eur-lex.europa.eu/)