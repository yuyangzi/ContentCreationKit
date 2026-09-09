# DeepSeek Harness 技术深读：一切皆插件的 agent 运行时

## 热度背景分析

2026 年 8 月 13 日，DeepSeek AI 开源了 **DeepSeek Harness（`dsh`）**——一个 MIT 协议、developer preview v0.1 的 agent 运行时。这不是新模型，也不是又一个 API 客户端，而是把"模型包起来让它能动"的那一层基础设施。The New Stack 报道称，开源后仅数小时 repo 就突破 **3.3 万 star** 且仍在快速攀升，Hacker News 讨论当日刷屏，社区插件生态一夜成型。

核心卖点一句话：**Everything is a Plugin**。DeepSeek 把这句话执行得相当彻底——模型适配器、工具注册表、会话日志、沙箱，**连 agent loop 本身都是插件**，每个都可替换。官方文档特意强调"没有需要 patch 的特权核心"，扩展 harness 的方式只是"把插件挂到别的插件旁边"。底层是自研的 **Cordis** 元框架（微内核架构），负责插件挂载、卸载与依赖管理。

值得拆解的技术点：

- **四种预设模式**：Standard（完整工具集：文件系统、shell、web 搜索、子代理、plan 模式）；Code（生成 TypeScript SDK，让模型写程序批量调工具，原本 5 次往返的操作合并成一次调用）；Minimal（只剩 `bash` + `str_replace_editor`，专为 benchmark 模型）；Creator（供开发者定制 preset）
- **append-only 会话日志**：模型看到的一切——系统提示、推理、工具调用、子代理调度、context 注入——都被记录为一条事件流；Trajectory 视图可按来源检视，resume / fork / search / replay 全部基于同一条事件流
- **沙箱**：Linux 用 DeepSeek 自写 Node addon 包裹 Landlock，macOS 用 Seatbelt，Windows 用 ACL restricted-token
- **不绑定自家模型**：provider 目录覆盖 Anthropic、OpenAI、AWS Bedrock、Azure、Google Gemini EAP 与 DeepSeek 自身 endpoint；还内置 Claude Code、Codex 两个子代理 provider（默认关闭，从 PATH 解析二进制）
- **兼容层**：MCP client、Agent Client Protocol、可读 `AGENTS.md`/`CLAUDE.md`、兼容两家的 `hooks.json` bridge

Armin Ronacher 的评价有代表性："这是我第一次在这个领域看到真正新东西，让我想回头重审我们的某些选择。" 值得注意的还有一个反差：DeepSeek 目前**不接受外部 PR**，只引导贡献者去 GitHub Discussions 或写插件。

## 类型标签

- `#DeepSeek` `#AgentHarness` `#Cordis` `#开源框架` `#agent架构` `#技术深读`

## 创作方向建议

1. **技术深读主线（推荐）**：DeepSeek Harness 架构拆解——"agent = model + harness" 分层下，把 loop 变成插件意味着什么；对照 Claude Agent SDK（harness-as-library）、LangGraph（graph-based）、Agent 生产骨架（沙箱/子代理/验证）三篇已有文章，定位 dsh 在坐标系中的位置
2. **append-only 事件流视角**：为什么"模型看到的一切都可从日志重构"是 agent 可观测性/可恢复性的关键设计——呼应已写过的 agent-hook（事件总线/OpenTelemetry）与 agent-checkpoint（断点续跑）技术线
3. **沙箱与安全工程**：Landlock/Seatbelt/Windows ACL 三平台沙箱的实现取舍，以及"默认关闭的 Claude Code/Codex 子代理"背后的供应链安全考量

## 可回溯来源

- GitHub：deepseek-ai/deepseek-harness — https://github.com/deepseek-ai/deepseek-harness
- 官方站点：DeepSeek Harness developer preview — https://deepseek.com/harness/en/
- 官方架构文档 — https://deepseek-harness.github.io/deepseek-harness/en/reference/
- The New Stack（Frederic Lardinois，2026-08-13）：DeepSeek open sources an agent harness where everything is a plugin — https://thenewstack.io/deepseek-harness-open-source-plugins/
- The Register（Thomas Claburn，2026-08-14）：DeepSeek's innovative harness treats everything as a plug-in — https://www.theregister.com/ai-and-ml/2026/08/14/deepseeks-innovative-harness-treats-everything-as-a-plug-in/5288095
- InfoQ（2026-08-20）：The Open-Sourcing of DeepSeek Harness Opens the Door to Modular, Unbundled AI Agent Infrastructure — https://www.infoq.com/news/2026/08/deep-seek-harness/
