---
title: "Agent 正在从进程变成服务：DeepSeek Super-agent 的架构取舍"
date: 2026-11-11
topic: DeepSeek Super-agent 双层架构 存算分离 BYOM
mode: deep-tech
---

# Agent 正在从进程变成服务：DeepSeek Super-agent 的架构取舍

> **导读**：2026 年 10 月 31 日，DeepSeek 产品部发布《Super-agent 设计探索：迈向更自主的 Agent 系统》，同一天把 MIT 许可的原型仓库放上 GitHub。原文的判断是，限制生产力进一步提升的瓶颈正在转向人的注意力。
>
> 这篇拆三层：单 Session 的天花板卡在哪里，Router 与 Worker 的拆分真正承诺了什么，以及那组消融实验能证明和不能证明的部分。

10 月 31 日，DeepSeek 产品部在微信公众号发布《Super-agent 设计探索：迈向更自主的 Agent 系统》（内容源于 Harness 团队），同一天把原型仓库 `dsh-superagent-prototype` 放上 GitHub，MIT 许可，开源时只有一个 commit。

原文的核心结论是，限制生产力进一步提升的瓶颈，正在转向人的注意力。

## 单 Session 的天花板不是模型能力

原文给 Super-agent 提了四个特征：连续、高效、主动、持久。

- 连续（Continuity）：用户在 IM、GitHub 评论这些熟悉界面里跟它交互，始终感觉只有一个 Agent 在，不必去想"某个 Session 的上下文里有没有这条信息"
- 高效（Efficiency）：不必等上一条命令跑完就能接住下一条，同时并行推进多个复杂任务
- 主动（Proactivity）：持续观察环境事件，主动推进值得处理的事，不需要介入时保持安静
- 持久（Persistence）：始终在线，直接接入真实工作环境，长期运行遇到异常能自动恢复

单个 ReAct Loop（推理与行动交替的循环）无法同时支持这四个特征，底层需要一套相应的架构。

原文给出的依据只有内部观察：一个人通常只能同时跟进 3 到 5 个活跃 Session。这个数字没有外部数据源，属于单方自述。不过它指向的结构问题很清楚：一条新消息进来，正在跑的循环就得停；上下文里塞进越来越多无关事件；想并行只能多开窗口，再由人负责在几个窗口之间搬运上下文。

这三件事都很难靠提示词修掉。问题不在模型，而在跑模型的那个进程：它被绑死在一台开着的机器上，也绑死在某一个上下文里。

## Router 与 Worker 的双层拆分

Super-agent 的第一层改动是拆成两个角色。

Router 层是全局的序点（Sequence Point）、协调点和记忆，不执行具体任务，甚至可以不配 Bash 工具。Worker 层彼此上下文隔离，挂载完整的执行工具，通常配置能力最强的模型。Worker 不直接对人说话，它的推理过程和工具调用不外露，统一向 Router 汇报，由 Router 对用户回复。

双层结构容易让人联想到一堆 Agent 互相商量，但原文明确写了，同层 Worker 之间通常不需要直接通信。它们各自订阅对应的 Thread（事件流），就会收到相同的事件通知，冲突靠各自发现来解决，少数跨任务协同由 Router 中转。多 Agent 之间那种自由对话，恰恰是这套设计刻意砍掉的东西。

事件本身被称为 Trigger，群聊消息、PR 评论、CI 结果都算。过滤分两级：程序层的确定性规则先判（来源、群组范围、白名单），语义层再由模型按提示词判断。

原型里有一段代码把这个顺序写得很直白，位于 `src/policy.ts`：

```typescript
gate(trigger: Trigger, thread, tickets) {
  if (!trigger.human) return machineGate(trigger)
  const allowed = allowedSender(settings, trigger.actor)
  const scope = listened(sources, trigger.source, trigger.meta)
  ...
  if (allowed && trigger.addressed) {
    return { admissible: true, strength: 'explicit', ... }
  }
  const cell = admissionCell(!!allowed, !!trigger.addressed)!
  // 只有 Source 能观测到该范围内的全部消息时，未 @ 的消息才查准入表
  const receivable = trigger.addressed || (scope.listened && scope.observed)
  const admission = receivable ? admissionOf(settings, trigger.source, row, cell) : 'ignore'
  ...
}
```

消息来自不在白名单的人、没有 @ 到 Agent、来源不在监听范围，这三个确定性条件先判掉。模型研判只在边界情况接手，而且要过几道硬约束：

1. 每条启用规则恰好判一次，多判少判直接报错
2. 必须有意图证据
3. 判定为"推断"时，在非自动模式下降级成只记录不执行

**授权判断的第一层必须确定性。** 有了确定性的 `gate()`，模型那一层的输出才有对照物，出问题时才能分清是规则错了还是研判错了。

事件路由上还有一个省钱的细节。已订阅某个 Thread 的后续事件由程序直通 Worker，绕过 Router。原文的消融实验显示这个机制不提升速度，但去掉它会让 Router 的决定数增加约 30%，读缓存 token 从 2323 万涨到 3177 万。

另一个细节是 Router 的批处理：事件密集涌入、Router 开始排队时，积压的多条 Trigger 会自动合并，在下一次 LLM 调用里一起注入。合并进同一次请求后，Prefill（预填充）阶段并行计算，单次请求耗时的增长远慢于批量大小。

原文压测把触发速率从每分钟约 1 条提到约 40 条，平均 batch 从 1.0 涨到 2.8，单次请求耗时只从 2.5 秒涨到 3.9 秒，单个决定分摊的推理时间反而从 6.4 秒降到 1.6 秒。

## 真正的新承诺在计算、状态与环境的分离

四特征里，高效和主动是循环常驻的推论，连续和持久才是硬的：它们不是交互体验问题，是系统形态问题。

原文借用了计算机系统的存算分离类比：

> 分两步解耦这三者的绑定：第一步先将推进 Agent Loop 的计算与持久化的会话状态分离，第二步再将云端的 Agent Loop 与重状态的执行环境解耦。

第一步，把 Agent Loop 放进云端无状态弹性容器，Session 状态存数据库。容器可以水平扩展、重启、替换，连续性由存储保障。这一步解决的是设备休眠或离线时 Agent 跟着停摆。

第二步更反直觉：让重状态的执行环境留在原地，端侧只部署一个不保存 Session 状态的轻量 daemon（守护进程），只负责执行命令和回传结果。

原文明确否掉了另外两条路。在云端启动沙箱、拉取代码、重建环境，技术上成本很高还容易遗漏信息；要求用户放弃本地环境迁到云上工作，迁移成本太高。它的推论是，既然难以复制的是环境本身，就不必让环境跟着 Agent Loop 上云。

这套思路与 Anthropic 在《Scaling Managed Agents》里提的"脑手分离"是同一条路线，都是让 harness（把模型包成可执行 Agent 的工程骨架）保持无状态、把 Session 日志存在 harness 之外。

原文自己点出了差别：Anthropic 那篇描述的是托管服务，讨论按需创建的沙箱和客户 VPC 内的资源；DeepSeek 首先要接入的是用户日常使用、可能间歇在线的个人机器，原文把它叫作 BYOM（Bring Your Own Machine）。

落到原型上，这一步的实现很朴素。整个系统只有一个 SQLite 库，用 Node 内置的 `node:sqlite`，不依赖 postgres、redis 等外部存储与消息中间件，队列由同一 SQLite 库落盘实现。启动时先抢状态目录的文件锁，防止两个进程同时写；库开 WAL（预写日志），`synchronous=FULL`，文件权限 0600。

调度靠一张 `effect` 表和每 2 秒一次的 pass 循环：命令在事务里入队，commit 之后才执行，同 kind 同 key 只保留一行，失败按指数退避。Worker 槽位默认 3 个，人工消息可以额外占一槽，且唤醒优先于启动。

状态机更能说明解耦到了什么程度，`src/core/stage.ts` 里这个函数不存储任何状态，只做推导：

```typescript
export function ticketStage(ticket: Ticket): TicketStage {
  if (ticket.ended) return { stage: 'ended' }
  if (ticket.delivery) return { stage: 'person', action: 'delivery' }
  if (ticket.attention) return { stage: 'person', action: 'answer' }
  const assignment = latestAssignment(ticket)
  const report = assignment?.report?.state
  if (report === 'ready') return { stage: 'person', action: 'review' }
  if ((report === 'blocked' || report === 'failed') && waitsForPerson(ticket)) {
    return { stage: 'person', action: report }
  }
  if (!assignment || assignment.state === 'pending') return { stage: 'working', action: 'queued' }
  if (report === 'waiting' || assignment.state === 'ended') return { stage: 'idle' }
  return { stage: 'working' }
}
```

一张 Ticket 现在处于什么阶段，不看执行它的 Session 是什么状态，而是看它在等谁。等人工验收是 `person`，排队中 `working`，跑完了 `idle`。原型的领域模型文档（`docs/001-domain.md`）把这一点列进拒绝实现的概念：Ticket 的状态不跟随 Session 状态。

这就是解耦的真实含义，也解释了第一步为什么能先落地：Agent 的生命周期与某台机器的开机时间脱钩，也与某一个进程的存活状态脱钩。

## 消融实验证明的是调度，不是质量

原文第 7 节的消融实验，是全文唯一一组硬数据。

负载约 300 条消息，其中约 20 条是工作请求，其余是闲聊、跟进、叫停和 CI 消息，每种方案重复 5 次。编码工作由一个只消耗时间的工具代替，时间轴按 1/4 缩放，模型调用耗时为真实值。基线是单 Session 加 Subagent 工具。

结果是，Super-agent 的任务完成时间中位数从 20.4 分钟降到 12.4 分钟，P95（最慢那 5% 请求的耗时）从 29.5 分钟降到 15.7 分钟。代价是读缓存 token 从 605 万涨到 2323 万，接近四倍。

同一张表里还有一组对照：单 Session 配"优先委派"的提示词，中位数从 20.4 降到 13.8 分钟，P95 却几乎没动，还是 29.0 分钟。

> 提示词能买来中位数，买不到长尾。

基线用的中性提示下，模型在 5 次运行里一次都没调用 Subagent，被新消息反复打断，P95 冲到 29.5 分钟；换成"优先委派"后，5 次里有 4 次真的委派了，剩下 1 次它判断工作量小选择自己做，于是长尾还在。双层的价值不在于平均更快，在于把"自己做还是交出去"这个判断从模型的自由裁量变成了结构约束。

这组数字全部由官方自报，负载是合成的，编码工作是耗时替身，时间轴缩放过，没有第三方复现。对照组是单 Session 加 Subagent 工具，DeepSeek 原文全文未提 Claude Code，实验里也没有这个对照组。它证明的是调度形态有效，不是任务完成得更好。消融实验只测了效率类指标，连续与持久没有量化验证。

## 没解决的部分比解决的部分更值得看

原文第 8 节列了四类开放问题：双层架构如何扩展、脱离 Session 之后如何协作、上下文边界如何划分并做 A2A（Agent-to-Agent）协作、安全与隐私如何保障。下面三点在工程上相当硬。

安全边界是首要的一条。原型文档把话说得很直白：Worker 以操作者的 OS 用户身份跑命令，权限档位是 `danger-full-access`；`docs/003` 写道，这些 wrapper 和目录只建立默认值，不构成安全边界，Worker 仍然可以用绝对路径执行程序。建议的缓解措施是用独立的 OS 账号，而不是靠系统自身隔离。

原文对风险的判断也直接：一旦云端的 Agent Loop 被服务端入侵或提示词注入攻破，它连接的全部端侧设备都面临被控制的潜在风险。凭据那条更要命，只要端侧环境里的凭据能进入模型上下文，正常执行过程中也可能泄露，所以需要一套让 Agent 完全不接触凭据也能使用凭据的机制，原文称这一机制仍待设计。

长程记忆是第二条。原文承认，当运行周期拉长到跨月甚至更长，长程记忆会成为制约可扩展性的主要瓶颈。这一点和"持久"这个特征直接冲突：能一直在线，不等于一直记得。

中途介入是第三条。原文说当前设计主要处理了任务发起与结果验收两端，用户想在后台执行过程中随时介入、接管、实时协同，产品形态还没定。

治理成本是另一层开销，不在原文的开放问题里。原型默认的接纳模式是 observe，推断类候选只记录不执行（明确请求在任何模式下都生效）；放开自动执行需把模式切到 auto，且发起请求者须在白名单内；原文那条 IM 单次回复不超过 100 词的硬规则（声称验证过，未附数据）。团队一旦上线这套东西，真正花时间的多半不是架构，是每天调提示词、把噪音改短改严、把不合适的自动行为关掉。

## 四家系统在同一个问题上分了岔

把 Super-agent 和主流 harness 摆在一起，可核查的差异主要落在三处。

状态存在哪：

- Claude Code 把 Session 连续写入本地 transcript 文件，靠 `--resume` 续接
- Codex 在云端给每个任务一个 VM，现行文档写该 VM 状态最多可恢复 7 天
- OpenHands 把事件逐条写进 `persistence_dir`
- LangGraph 用 checkpointer（检查点保存器）按 super-step（图的一次执行步）落快照，以 `thread_id` 为键
- Super-agent 是一个 SQLite 库

隔离放在哪：

- Codex 和 OpenHands 把隔离做进系统内部，OpenHands 官方文档还专门写明，共享 sandbox 时另一个会话不是安全边界（Enterprise 文档）
- Claude Code 的沙箱是可选的，默认关闭，只覆盖 shell 命令
- LangGraph 在其持久化与中断文档中未见执行隔离机制，隔离由使用者在节点代码里自己解决
- Super-agent 把执行环境整体推到系统之外

谁决定何时停下来问人：

- Claude Code 用 hooks 在生命周期点拦截，`PreToolUse` 能直接 block，默认问人靠权限系统
- Codex 是 sandbox mode 乘 approval policy 两个旋钮
- OpenHands 用 confirmation policy 决定哪些动作需批准，agent 停在 `WAITING_FOR_CONFIRMATION` 状态等人确认
- LangGraph 是 `interrupt()`，恢复时从节点开头重跑
- Super-agent 是确定性 `gate()` 加模型研判，默认只观察

三处里，真正拉开距离的是第二处。**其余四家都把隔离放在系统内部，要么自己造，要么交给使用者造；DeepSeek 是唯一把隔离整体推到系统边界的。** 这不是疏忽，是 BYOM 的代价：省掉重建环境的成本，就得把安全责任交回操作者。问题定义不同，云端沙箱要保证租户之间互不干扰，本地机器要保证不打断人已有的工作。

## 如果你的团队要照着做

这套设计能直接搬走的是前两步，第三步要等触发密度到量。

第一步是把 Session 状态外置，不是拆双层。让 Agent Loop 无状态、状态进数据库，这一步不需要改循环，收益最大成本最低，也直接解决"合上电脑就断"。

第二步加直通和两级过滤。确定性规则先判掉大多数噪音，已订阅的后续事件绕过 Router。消融数据说得很清楚，这一步买的是成本不是速度，但它决定了 Router 会不会在消息一多时就排队。

第三步才是拆 Router 和 Worker。原文自己的压测把触发速率拉到每分钟约 40 条，单次请求耗时随批量增长很缓，还没碰到单 Router 的吞吐上限；也正因如此，原文认为在团队当前规模下不必水平切分 Router，因为切分粒度越细，全局上下文的连续性损失越大。

这个数字可以当粗略刻度用。**双层的收益集中在触发密集的场景；触发稀疏时先做前两步就够了。**

回头看，这套设计没有提出新理论，原文自己也这么说。它做的是把前面那个“跑模型的进程”，改成一台随时可替换、状态在库里、环境在本地、有人盯着才动手的常驻服务。四个特征里只有连续和持久是新的承诺，高效和主动是它们的推论（状态外置、循环常驻之后，并行与主动推进才有可能）。

真正被重新定义的是责任边界。以前一个 Agent 出了事，关掉终端就结束了；现在它一直在线，接着你的 GitHub 账号和你的机器，于是"什么时候该安静"从一个提示词技巧，变成了必须写进系统结构的东西。原型文档里那句 "right help at the right time, and nothing at any other time"。

*参考来源：*

- 《Super-agent 设计探索：迈向更自主的 Agent 系统》，DeepSeek 产品部，2026-10-31：[全文镜像](http://www.uml.org.cn/ai/202611023.asp?artid=27640)（镜像转载日期 11-02） / [英文全译](https://offloop.org/learn/exploring-deepseek-super-agent-design)
- 开源原型 dsh-superagent-prototype（MIT）：[GitHub](https://github.com/deepseek-ai/dsh-superagent-prototype)
- 原型设计文档：[Philosophy](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/main/docs/000-philosophy.md) / [Domain model](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/main/docs/001-domain.md) / [Architecture](https://github.com/deepseek-ai/dsh-superagent-prototype/blob/main/docs/007-architecture.md)
- Anthropic, Scaling Managed Agents with stable interfaces, 2026-04-08：[Link](https://www.anthropic.com/research/managed-agents)
- Claude Code 文档：[Sessions](https://code.claude.com/docs/en/sessions) / [Sandboxing](https://code.claude.com/docs/en/sandboxing) / [Hooks](https://code.claude.com/docs/en/hooks)
- OpenAI Codex 文档：[Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments) / [Agent approvals & security](https://learn.chatgpt.com/docs/agent-approvals-security)
- OpenHands 文档：[Runtime Architecture](https://docs.openhands.dev/openhands/usage/architecture/runtime) / [Conversation Persistence](https://docs.openhands.dev/sdk/guides/convo-persistence)
- LangGraph 文档：[Checkpointers](https://docs.langchain.com/oss/python/langgraph/checkpointers) / [Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts)
