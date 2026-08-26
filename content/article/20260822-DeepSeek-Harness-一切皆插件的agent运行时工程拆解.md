# 一切皆插件：DeepSeek Harness 工程拆解

> **导读**：DeepSeek 在 2026-08-13 开源的 dsh（developer preview），把 agent runtime 的每一层——模型适配器、工具注册表、会话日志、沙箱、审批策略、agent loop、UI——都拆成可挂载的插件。本文按"一切皆插件"这条线拆开 dsh 的工程实现，从仓库结构到事件三域，从 Turn/Step 主循环到沙箱与 append-only 日志，最后回答一个工程问题：什么时候该用、什么时候不该用、什么时候该关注它。

---

## 2026-08-13：开源第一天发生了什么

DeepSeek 在这一天把 agent harness 以 developer preview 形式开源，仓库地址 `deepseek-ai/deepseek-harness`，MIT 协议，编号 0.1.0-rc.6，README 在 Developer preview 一节写明警告：**THERE WILL BE COMPATIBILITY-BREAKING CHANGES**。开源数小时 star 数破 3 万，到今天（2026-08-22）仓库 183k stars、20k forks（GitHub 仓库页），而发布节奏目前仍在加速。

但 dsh 不是新模型，也不是又一个 API 客户端。它做的是"把模型包起来让它能动"的那一层——harness。Claude Code、Codex CLI、Cursor Composer 都在做类似的事，但 DeepSeek 把这件事的执行度拉到了另一个位置：连 agent loop 本身都是可替换的插件。官方原文是"There is no privileged core to patch: you extend dsh by mounting a plugin beside the others"。

听起来像是又一句营销口号。但打开仓库看，这不是口号：仓库根目录里 `.agents/` 和 `.claude/` 目录并存，`AGENTS.md` 和 `CLAUDE.md` 同名文件并存，packages 目录下按职责分成数十个 group、组内包平级，`core/` 里是官方文档列出的 6 个核心子系统。Armin Ronacher 第二天在 X 上的评价很能说明社区第一反应："这是我第一次在这个领域看到真正新东西，让我想回头重审我们的某些选择。"

也有不少反对意见。Hacker News 上有人立刻甩出 plugin fatigue："Every product relying on 'community plugins' for their features implies it works fine the 6 first months, then it's a nightmare of incompatible, deprecated, incompatible plugins, with no consistency and no governance." 也有人嫌粗糙：UI 简陋、配置复杂、文档读起来像在啃论文。

还有一件事。`@deepseek-ai/dsh` 在 npm 上存在的前 62 小时里，每个 rc 版本都把 262.3 MiB 的 Claude Code 二进制打进了依赖闭包（来源：Chew Loong Nian 对依赖闭包的逐版本解析，见文末参考来源）。2026-08-12 22:36 UTC 发布的 0.0.1-rc.5，依赖闭包里就有 `@anthropic-ai/claude-agent-sdk` 及其平台原生二进制；0.1.0-rc.2（08-13 09:48 UTC）把这个依赖移除，安装体量随之大幅回落。问题在于 npm 的 access 是 package 级不是 version 级——包从私有转 public 时，registry 上已存在的所有 rc 都自动变成 world-readable。你今天还能 `npm install @deepseek-ai/dsh@0.0.1-rc.5` 装到那个带着 Claude Code 二进制的旧版本。这是开源流程里一次有教育意义的失误：scope public 之前应该清掉旧发布。

我对 dsh 的态度是把它当作一个工程样本认真读，但不会一上来就推荐团队引入。

---

## dsh 仓库长什么样

dsh 是一个大型 TypeScript monorepo。这些 packages 不是层叠的依赖树，而是按职责分组挂在 packages 目录下：

- **核心**（`packages/core/`）：`session`（append-only SessionEvent 日志）、`system-prompt`（提示词片段组装）、`tools`（作用域工具注册表）、`agent`（Agent 接口与 registry）、`agent-loop`（默认 driver）、`scope`（per-agent 作用域注册原语）
- **模型层**（`packages/llm/`）：消息与流词表、模型 adapter 接缝
- **执行环境**：`shell`、`subprocess`、`terminal`（持久 PTY）、`sandbox`、`fs`、`lsp`、`web`（搜索与抓取）
- **Agent 能力**：`subagent`、`skill`、`workflow`、`jobs`、`todo`、`plan`、`goal`
- **会话与数据**：`session-query`、`attachment`、`spill`、`storage`、`settings`、`credentials`
- **人机协作**：`interaction`（审批/权限/ask-user）、`feedback`、`identity`
- **接口层**：`api`（Typert RPC 网关）、`sdk`（进程外 JSON-RPC SDK）、`acp`（Agent Client Protocol 服务端）、`host`/`client`（Web UI 两半）、`hooks`（Claude Code/Codex 协议桥）
- **自我修改**：`extensions`（实时插件检视 + 模型自己写插件并挂载/卸载）

这个列表有一个特点：**几乎每个能力都有一个独立的 ctx 键**。`ctx.sessions`、`ctx.tools`、`ctx.agentLoop`、`ctx.shell`、`ctx.subprocess`、`ctx.sandbox`、`ctx.llm`——没有"特殊"的子系统。这是 Cordis 服务注册模型的核心：每个能力由某个插件提供，任何插件都可以替换某个服务的实现。这种结构最直接的好处是，单个 capability 的演进不会牵动其他 capability，bindings 只发生在 `ctx` 键的层面。

仓库根目录有一个细节值得注意：`AGENTS.md` 和 `CLAUDE.md` 两个文件并存，README 里写明"For agents, follow AGENTS.md"。这意味着 dsh 同时为 Claude Code 和其他 agent 提供工作入口——不只是兼容性宣称，而是根目录就摆了两份入口文件。

---

## Profiles × Bundles × Patch：一切皆插件的"组装方式"

一个运行中的 dsh 不是一坨预编译产物，而是一棵插件树，按三层组合而成：

- **Profile**：命名组合，存在 Harness home 里。它列出 bundle 栈、用户自装的 out-of-tree 插件、以及用户自己的 `cordis.patch.yml` 补丁。`web` 和 `headless` 作为模板 ship。
- **Bundle**：Cordis config rows 加代码的分发格式。它插入什么，上层依然可以 patch。
- **Patch**：针对 row id 替换整段 config 或插入新 row。

加载顺序很关键：profile 列出的每个 bundle 按序应用 → profile 的 `cordis.patch.yml` → home 层 patch → `--patch` 命令行 overlay。后者覆盖前者。

这种结构解决的是"怎么把插件装到合适位置"的问题。默认装一个 plugin 不会污染基础配置，因为它作为新 row 插在 patch 链最上层；要换底层实现只需要在 patch 层指向同一个 row id 给一个新实现。`dsh --profile web --dump-config` 命令会把组合后的实际插件树打印出来——这是排查"为什么我的 plugin 没生效"的最快路径。

```bash
# 打印 web profile 实际生效的插件树
dsh --profile web --dump-config
```

`packages/bundle/base` 是每个 profile 的第一层（model adapters、tools、persistence、sandbox、approval policy、settings、credentials、telemetry），`packages/bundle/web-app` 在它上面加浏览器应用，`packages/bundle/headless` 加无 server 的一次性 runner。这种分层保证了"先有最小可用再加 UI"是默认路径。

---

## 核心包与 ctx 键空间：一切皆插件的"基础字典"

dsh 把所有能力都映射到 `ctx` 键上。最核心的几个：

| Package | 职责 | ctx 键 |
|---------|------|--------|
| `core/session` | append-only `SessionEvent` 日志与内存 store | `ctx.sessions` |
| `core/system-prompt` | prompt-section 与 tool-schema 组装 | `ctx.systemPrompt` |
| `core/tools` | 作用域工具注册表与受保护执行管道 | `ctx.tools` |
| `core/agent` | `Agent` 接口、live registry、`agent/*` 事件 | `ctx.agents` |
| `core/agent-loop` | `Agent` 接口的默认 driver | `ctx.agentLoop` |
| `llm/llm` | 消息与流词表 + adapter 接缝 | `ctx.llm` |

理解 dsh 架构有一把钥匙：底层 Cordis 框架约定每个注册都带一个 disposer（注销器）。注册 Tool 时记录"如何注销这个 Tool"，注册 Prompt section 时记录"如何移除这段 prompt"，挂载 Timer 时记录"如何停止这个 Timer"。组件卸载时，按注册逆序回滚所有 effect。这就是 Cordis 的"时空可组合性"——卸载即回滚，不需要重启进程。dsh 能热装热卸，正是因为每个注册都自带了反向操作。

工程上的体现是：你正在跑一个 dsh 会话，往配置里加一个 plugin，registry 立刻生效；删掉它，注册的服务、监听、提示词片段、tool schema 全部消失，普通插件系统（Node 的 require 缓存、Python 的 sys.modules）很难做到这一点。下面是一个最小 plugin 的样子：

```TypeScript
// 一个最小 dsh 插件：通过 ctx 注册一个 service、一个事件监听，并各自带 disposer
import type { Context } from '@deepseek-ai/dsh'

export function apply(ctx: Context) {
  // 注册 service：tool registry 里有了一个 my-tool
  ctx.tools.register({
    name: 'my-tool',
    schema: { /* JSON schema */ },
    execute: async (args) => { /* ... */ },
  })

  // 监听 capability 事件（waterfall）：拦截所有 fs 读操作
  ctx.on('fs/read', async (req, next) => {
    if (req.path.startsWith('/secret')) {
      return null  // 在 chain 里短路
    }
    return next()   // 否则放行到下游
  })

  // 每次注册都返回一个 disposer；ctx 卸载 plugin 时会按逆序调用
  return () => {
    ctx.tools.unregister('my-tool')
    // listeners 自动回收
  }
}
```

这段代码说明了 dsh 的几件事：plugin 是一个导出 `apply(ctx)` 的模块；service 注册、事件监听都通过 ctx 完成；返回的 disposer 在 unload 时按注册逆序回滚。改这一段，你就能挂到 dsh 上了。

---

## 三种事件域：一切皆插件的"扩展协议"

dsh 把所有事件分成三类，对应三类扩展语义：

- **Session events**（durable）：持久化事件，append 到日志里，broadcast 通过 `session/event`。需要"事实必须穿越 reload"时用。
- **Agent events**（`agent/*`）：携带 live `Agent` 对象——inbox、step、status、request、validation、continuation。要观察或拦截 in-flight 工作时用。
- **Capability events**：`fs/*`、`tools/*`、`telemetry/*`，attach policy 和 adapter 到某个接缝，不导入 loop。

更关键的是事件模式本身也分两类：

- **Waterfall 事件**（`agent/pre-step`、`agent/request`、`llm/stream`、`tools/pre-execute`、`tools/execute`、`tools/post-execute`）：listener 必须调用 `next()` 把控制权传给下一个 listener，否则链断在原地。
- **Serial 事件**（`agent/turn-stopping`）：listener 不调用 `next()`，是一道独立的拦截点。

这套设计的后果是：你能拦截一个请求而不持有 loop。当 `tools/post-execute` 触发时，多个 plugin 可以按顺序改写工具结果，每个 plugin 都只关心自己的一段；上游 plugin 拦截并拒绝某个 step，下游 plugin 感知不到。这是把"中间件"思想贯彻到 agent runtime 的一次尝试。

dsh 还做了一个更狠的事：把"模型可见 = 日志可重建"做成运行时强制不变量，不靠约定。`packages/core/agent-loop/src/invariant.ts` 在每次 LLM dispatch 时断言 outgoing request messages 与 `session.deriveMessages()` 序列化结果完全一致；`packages/core/session/src/surface.ts` 在写入 surface-eligible 事件时如果缺 surface marker 直接抛错。换句话说，框架不会让"模型看到了什么但日志没记"这种事发生。这是约束最强、也最容易被开发者触怒的不变量，但我对它的评价是积极的——它把审计保证从 nice-to-have 提升成架构必然。

---

## Turn 与 Step：一切皆插件的"主循环可替换"

dsh 区分两个粒度：

- **Step**：一次模型请求加上它触发的工具调用
- **Turn**：零或多 step，从收到输入到全部完成

turn 的生命周期是这样的：`turn/start` → claim 下一条输入 → 组装 prompt sections + tool schemas → `agent/pre-step` waterfall（可改写或拒绝）→ 真的进入就把消息 append 为 `user/message` → 从日志 derive 出 model history → `agent/request` waterfall → `llm/stream` waterfall → `assistant/chunk*` → `assistant/message` → 如果有 tool 调用就 `tool/call*` → `tools/pre-execute` / `tools/execute` / `tools/post-execute` waterfall → `tool/result*` → `step/end` → 如果还有未完成的工作或下一条输入进来就 claim 下一 step，否则 `agent/turn-stopping` → `turn/end`。

整个流程里几乎每一段都是可拦截的瀑布流事件。`Agent` 接口是公开协议，`core/agent-loop` 只是这个接口的默认 driver。换一个 driver plugin 就等于换了主循环——多 agent 协作、动态策略切换、自定义停止条件都成了一件挂载的事，不需要 fork 仓库。这与 Codex CLI（loop 写在 Rust 核心里）、Claude Agent SDK（harness-as-library 但 loop 仍固定）形成对照。

---

## Code Mode：5 次往返合并为 1 次

Code Mode（Programmatic Tool Calling，PTC）是四种预设模式里容易被误读的一个。**它不是"Standard 模式专用于 coding"**，而是 Standard 的全部能力加上 Code Mode SDK——模型写一段 TypeScript 程序调用多个工具，`await tools.name(args)`，只把 `print` 或 `return` 的内容送回模型。原本 5 次往返的操作合并为 1 次代码块执行。

工程上值得注意的是 Code Mode 的执行边界：模型生成的代码跑在**独立的 Node worker thread** 里，每次调用都起一个新线程，环境空、heap cap、wall clock cap、硬终止。开发者文档明确说这是 "containment, not a security boundary"——它是隔离不是沙箱，权限级别和 bash 工具一致。如果你要让模型能跑任意代码，要么选 Code Mode 接受这个信任级别，要么让模型用回 Standard Mode 的受保护工具。

这一点和 Minimal 模式形成对照。Minimal 模式只给 `bash` + `str_replace_editor` 两个工具，系统提示只有一句"You are a helpful software engineer assistant"——这是 DeepSeek 官方跑模型 benchmark 的环境，因为变量少、能复现。Standard 是默认全功能 coding agent，Creator 在 Standard 之上加了 runtime 检视、内存中插件实验、preset 创作。四个模式对应不同的信任边界和任务形态，不是同一个 agent 的四档性能。

PTC（Code Mode）的程序化调用是 dsh 里容易被低估的设计——它解决的不是"模型能不能写代码"，而是"上下文窗口在多次工具往返中会被稀释"。一段连续操作如果走 5 次 function calling，每次都把前面所有 tool result 留在 history 里；走 Code Mode 只保留代码块的 return。把"工具调度"和"上下文占用"解耦，这是过去半年 agent 工程里少见的结构性改进。

---

## 沙箱、审批与日志：Model-visible means logged

沙箱在 dsh 里是 fail-closed 的设计，三种策略档位：`read-only` / `workspace-write` / `danger-full-access`。后端实现上 Linux 先探 bubblewrap（更宽松），fallback 到 native Landlock launcher；macOS 用 Seatbelt；Windows 用 ACL restricted-token runner（受限令牌加 ACL 路径限制）。**关键不变量**：请求受限模式但后端不可用 → 抛 `SANDBOX_UNAVAILABLE` 拒绝运行；approval 子系统同样 fail-closed，缺失审批服务时拒绝而非放行；不会静默降级到无保护运行。安全是贯穿配置、执行、审批、日志与恢复的系统约束，不是"权限弹窗里加一道确认"。

审批和执行细节都进 append-only SessionEvent 日志。日志包含：

- system prompt 与 reasoning
- tool calls / results
- subagent scheduling
- context injections
- 权限切换、压缩事件、取消原因

Trajectory 视图按来源检视，resume、fork、search、replay 都从同一条事件流派生。"Model-visible means logged"——任何进入模型请求的内容必须可从日志重建，这条约束是 dsh 的根本承诺。

这条约束带来的工程后果是：当一次任务出错时，你能确切知道模型请求前刚注入了什么、tool result 是否被裁剪过、系统是否自动切换了模型路由、用户是否在流式输出中途改变了方向。Trajectory + fork + replay 让"agent 不可调试"的老问题有了出路。但也有代价——这是 event log 不是 decision ledger，只记录"做了什么"不记录"为什么允许"。

---

## Provider 与兼容层：把竞争对手变成自己的子代理

dsh 的 provider 目录覆盖 Anthropic、OpenAI、AWS Bedrock、Azure、Google Gemini EAP（文档仍叫 Vertex）、DeepSeek 自身 endpoint，加任何 OpenAI-compatible gateway。它不绑定自家模型。

更激进的是子代理 provider：内置 `subagent-claude-code` 和 `subagent-codex`，默认关闭，用户自备安装和登录。还有 `subagent-spawn-in-process`、`subagent-fork-in-process`、`subagent-acp`、`subagent-dsh-sdk`——同一个 `subagent` 工具在本地用 in-process provider，想调 Codex 就换 provider，模型侧 schema 基本不变。

兼容层同样野。MCP client、Agent Client Protocol（ACP）服务端、读 `AGENTS.md` / `CLAUDE.md`、兼容 Claude Code 和 Codex 的 `hooks.json`——`hooks-claude-code` / `hooks-codex` 把外部 hook 协议翻译到 dsh 的类型化拦截点上。**dsh 是把竞争对手变成自己的子代理**——你不用选 dsh 还是 Claude Code，dsh 可以编排 Claude Code 跑子任务，再在主任务里调度 Codex。这套设计的定位不是 Codex 或 Claude Code 的替代品，而是可以套在它们之上的编排层。

---

## 最佳实践：什么时候用、什么时候不要用

1. **要做 harness 本身的二次开发时引入 dsh**。它的价值在"你能换 loop、换 provider、换持久化"，不是"它是个更好用的 coding agent"。如果只是想找一个开箱即用的 coding agent，Claude Code / Codex CLI / OpenCode 的成熟度更高。

2. **需要审计与可回放时优先考虑 dsh**。"Model-visible means logged" 是架构保证而不是约定。当任务失败需要复盘"模型看到了什么"、或者需要 fork 一个会话换个模型重跑同一段，dsh 的 append-only 日志 + replay 是少见的现成方案。

3. **需要跨 harness 编排时把 dsh 当 glue**。subagent-claude-code 和 subagent-codex provider 让你能在 dsh 里直接调度 Claude Code 或 Codex 跑子任务，再在主任务里串起来。如果你已经在用其中一个 harness 又想加一个，用 dsh 当编排层比 fork 另一个项目的 loop 更快。

4. **多 agent 协作探索期用 Creator mode 试原型**。Creator 给模型 runtime 检视 + 内存中插件实验能力，可以现场定义一个 Cordis plugin 挂上去、跑完任务、卸载——这是少见的"边跑边改 harness"的实验台。但模型能实时挂载插件，等于把代码执行权交给模型，**不要在生产环境给不可信 prompt 启用**。

5. **追新特性时钉 commit 而不钉版本**。README 自己写明 "THERE WILL BE COMPATIBILITY-BREAKING CHANGES"，从 0.0.1-rc.5 到 0.1.0-rc.2 再到 0.1.1-rc.2，plugin API 已经多次变动。等稳定前不要把 dsh 当生产 runtime 直接对接业务。

---

## 常见误区：理解 dsh 时容易掉进的三个坑

1. **把"Everything is a Plugin"理解成 VS Code extension 的放大版**。VS Code 把 UI 当插件、命令当插件，但 loop 写死在 core 里，卸载插件时遗留状态需要手动清理。dsh 的关键不在"插件多"，在"每个注册都带 disposer、卸载即回滚"。Cordis 的"时空可组合性"是这个机制的形式化基础。

2. **把 Code Mode（PTC）理解成"为 coding 优化的模式"**。它是 Standard 能力 + 程序化工具调用，**和 coding 没必然关系**。任何需要"多次工具往返合并成一次代码执行"的任务都受益，文件批量处理、批量搜索、多步数据迁移都能用。

3. **把 append-only 日志理解成"普通 transcript"**。大多数 agent 的日志是 best-effort，dsh 的不变量是 runtime-enforced 的——`invariant.ts` 在每次 LLM dispatch 时做序列化一致性校验。这意味着日志不只是"事后能看"，而是"模型此刻看到的内容有且仅有日志里有"。

---

## 写在最后

dsh 是 DeepSeek 把模型层以外的工程判断全部开源的一次尝试。它不是产品发布，是基础设施发布——README 自己写明 developer preview、不接受外部 PR、引导去 GitHub Discussions 或写插件。一个把控制流彻底暴露给插件的运行时，对需要它的人是礼物，对不需要它的人是噪音。

**什么时候用**：你的核心需求是 harness 本身的可替换、可审计、可编排，dsh 提供的是稀缺的工程参考实现。

**什么时候不要用**：你只是想要一个开箱即用的 coding agent；你要生产环境的稳定性；你的团队还不熟悉 TypeScript monorepo + pnpm workspace。dsh 对这些场景都太早。

**什么时候关注**：当"agent 修改自己的 harness"成为某个具体工程问题（harness RSI、动态策略切换、多 harness 编排），dsh 的 plugin 树 + append-only 日志 + 可逆 effect 组合是当前少有的完整开源参考。Cordis 论文（`A Programming Paradigm for Spatiotemporal Composability`）把这些机制的范式基础讲清楚了。

---

*参考来源：*

- GitHub 仓库：[deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)
- 官方架构文档：[DeepSeek Harness Architecture](https://deepseek-harness.github.io/deepseek-harness/en/reference/)
- 官方站点：[DeepSeek Harness developer preview](https://deepseek.com/harness/en)
- 官方 Cordis Primer：[cordis-primer](https://deepseek-harness.github.io/deepseek-harness/en/reference/cordis-primer)
- The New Stack（Frederic Lardinois，2026-08-13）：[DeepSeek open sources an agent harness where everything is a plugin](https://thenewstack.io/deepseek-harness-open-source-plugins/)
- The Register（Thomas Claburn，2026-08-14）：[DeepSeek's innovative harness treats everything as a plug-in](https://www.theregister.com/ai-and-ml/2026/08/14/deepseeks-innovative-harness-treats-everything-as-a-plug-in/5288095)
- VentureBeat（2026-08-13）：[DeepSeek Harness launches as open source rival to Claude Code](https://venturebeat.com/technology/deepseek-harness-launches-as-open-source-rival-to-claude-code-alongside-v4-pro-on-api-with-higher-prices)
- InfoQ（2026-08-20）：[The Open-Sourcing of DeepSeek Harness Opens the Door to Modular, Unbundled AI Agent Infrastructure](https://www.infoq.com/news/2026/08/deep-seek-harness/)
- Developers Digest：[We Read DeepSeek Harness: What 453K Lines of Agent Runtime Looks Like](https://www.developersdigest.tech/blog/deepseek-harness-dsh-first-look)
- Justin3go（2026-08-15）：[DeepSeek Harness In Depth: 90K Stars in Two Days](https://justin3go.com/en/posts/2026/08/15-deepseek-harness-review)
- Medium（kaliarch）：[DeepSeek Harness: When the Agent Loop Itself Becomes a Plugin](https://medium.com/@kaliarch/deepseek-harness-when-the-agent-loop-itself-becomes-a-plugin-7fad0aa9de1c)
- Agent Atlas：[Cordis Explained: How DeepSeek Harness's Plugin Framework Works](https://agentatlas.org/blog/cordis-explained-how-deepseek-harness-plugin-framework-works)
- Cordis 论文仓库：[cordiverse/paper](https://github.com/cordiverse/paper)
- 中文社区：知乎「DeepSeek Harness 项目深度解读」<https://zhuanlan.zhihu.com/p/2071362726442673749>
- 中文社区：知乎「拆解DeepSeek Harness：一个『一切皆插件』的Agent 框架」<https://zhuanlan.zhihu.com/p/2071382525394556113>
- Chew Loong Nian（2026-08-15）：[DeepSeek Cut 262 MiB of Claude Code From Its New Harness](https://medium.com/@chewloongnian/deepseek-cut-262-mib-of-claude-code-from-its-new-harness-the-old-build-is-still-on-npm-5c1c239bbf64)（付费墙，仅摘要可见）
- Hacker News：[DeepSeek Harness developer preview](https://news.ycombinator.com/item?id=49285244)