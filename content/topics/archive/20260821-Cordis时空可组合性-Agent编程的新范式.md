# Cordis 时空可组合性：Agent 编程的新范式

## 热度背景分析

DeepSeek Harness 底层是一个叫 **Cordis** 的插件元框架，其设计思想来自 DeepSeek 团队（Yifan Shi、Wei Zhang、Tianyi Cui）的一篇论文《**A Programming Paradigm for Spatiotemporal Composability**》。这是本次开源真正的理论内核——Harness 是应用，Cordis 是范式。

论文提出两个维度：

- **时间可组合（temporal composability）**：组件被卸载时，其产生的一切效应也随之回滚。在一个"持续被修改、几乎无人监督"的系统里，组件随时出现又消失，必须保证移除一个插件不会留下残留状态、不需要强制重启
- **空间可组合（spatial composability）**：组件之间能声明并管理依赖关系。VS Code 的 extension 虽然能声明依赖，但很少被真正使用；Cordis 把插件依赖作为一等公民

落到工程上，Cordis 是一个微内核：kernel 只负责插件的挂载、卸载与依赖解析，每个能力（工具、LLM 适配器、文件访问、agent loop）都是挂在共享 context 上的插件。每个注册都要求带 disposer，卸载时按注册的逆序回滚。

这个范式在内容管线里的价值：它直接续写本仓库已经写过的"编程范式从 Loop 转向 Graph"线（`20260726-AI又造新词-Graph替代Loop`），但给出了另一个更激进的答案——不是把控制流画成图，而是把**整个运行时都变成可卸载/可重组装的插件**。agent loop 不再是一个固化的循环，而是插件树上可以被替换的一个节点。对应的还有 `20260718-Agent-Loop工程`（loop 停止条件）、`20260721-agent-checkpoint`（断点续跑）等已有技术线，Cordis 的"时间可组合 = 回滚效应"与之形成理论呼应。

值得深挖的张力点：append-only 会话日志与"卸载即回滚"之间的关系——事件流是只能追加的不可变事实，插件卸载是可变运行时，两者如何在一个系统里共存；以及"一切皆插件"是否会重蹈当年微内核/插件化过度抽象的覆辙（灵活到失控），还是 agent 时代确实需要这种无监督动态重组。

## 类型标签

- `#Cordis` `#编程范式` `#时空可组合性` `#DeepSeek` `#agent架构` `#技术深读`

## 创作方向建议

1. **范式深读主线（推荐）**：从 Loop 到 Graph 再到 Plugin——agent 编程范式的第三次迁移；讲清"时间可组合（卸载回滚）+ 空间可组合（依赖管理）"为什么是"无监督持续修改"系统的必要条件
2. **Cordis 机制拆解**：微内核 + 共享 context + 可逆 effect（`ctx.effect()` 返回 disposer）+ 类型化事件（broadcast / waterfall short-circuit / serial），对照 VS Code extension 模型的不足
3. **哲学层**：把"软件"从静态编译产物重新定义为"可动态重组的组件森林"，agent 时代需要的是运行时而非框架——呼应已写的"知识编译优于知识检索"（Karpathy 那条 Gist）

## 可回溯来源

- Cordis 论文：A Programming Paradigm for Spatiotemporal Composability — https://github.com/cordiverse/paper
- Cordis 仓库 — https://github.com/cordiverse/cordis
- 官方 Cordis Primer — https://deepseek-harness.github.io/deepseek-harness/en/reference/cordis-primer
- 官方 Cordis Tutorial — https://deepseek-harness.github.io/deepseek-harness/en/develop/cordis-tutorial/
- The Register（2026-08-14，论文与作者信息）— https://www.theregister.com/ai-and-ml/2026/08/14/deepseeks-innovative-harness-treats-everything-as-a-plug-in/5288095
- InfoQ（2026-08-20，微内核架构分析）— https://www.infoq.com/news/2026/08/deep-seek-harness/
