# The Agentic Web：WebMCP、Serverless Agents 与浏览器作为 AI Agent 运行时

## 主题名称

The Agentic Web：WebMCP、Serverless Agents 与浏览器作为 AI Agent 运行时

## 热度背景分析

AI Agent 正在从聊天产品和 IDE 插件，进入 Web、云函数、CI/CD、操作系统和开发工具链等基础设施层。近期多个信号集中出现：Chrome 启动 WebMCP origin trial，Azure Functions 发布 Serverless Agents Runtime，GitLab、CircleCI、Windows 等平台也在把 Agent 能力嵌入软件开发与系统安全流程。

这说明 Agent 的竞争正在从「哪个模型更聪明」转向「谁能成为 Agent 的运行时和工具协议」。如果网页、云函数、CI/CD、操作系统都开始为 Agent 暴露结构化接口，那么软件系统的人机交互方式会发生根本变化：Agent 不再主要依赖模拟点击、解析像素、猜测 DOM 状态来操作软件，而是通过标准化、可授权、可审计的工具调用直接完成任务。

WebMCP 是这条线里最值得展开的入口。过去我们让 Agent 操作网页，常见方案是 Playwright、Puppeteer、Selenium 或各类 RPA 工具：它们能跑，但本质仍是在复刻人的浏览行为，依赖选择器、页面布局、加载时序和脚本注入，遇到动态页面、复杂权限、反自动化机制或 UI 改版就容易变脆。WebMCP 的想法更激进一些，它不是让 Agent 更像人一样点按钮，而是让网页把 JavaScript 函数、HTML 表单、DOM 可操作能力以浏览器原生协议暴露给 Agent，网页开始拥有面向智能体的第二套接口。

这也带来一个更大的问题：WebMCP 和 MCP（Model Context Protocol）到底是什么关系？一种理解是，MCP 更像 Agent 访问文件、工具、数据库和外部服务的通用工具协议，而 WebMCP 试图把类似的工具暴露逻辑带进浏览器和网页上下文里。它们不一定是竞争关系，更可能是在不同运行时里解决同一个问题：让 Agent 从「看见界面再猜动作」转向「理解工具再执行任务」。

可回溯信号包括：

- Chrome for Developers：Google 发布 WebMCP origin trial，让网站可以将 JavaScript 函数和 HTML 表单暴露为浏览器 AI Agent 可调用的结构化工具。
- WebDeveloper.com：WebMCP 被描述为让浏览器 Agent 直接调用 JavaScript 函数和 HTML 表单的工具接口。
- InfoQ 中文：Chrome 推出 WebMCP 标准提案，强调它可能成为浏览器原生 Web 智能体协议。
- InfoQ：Azure Functions 推出 Serverless Agents Runtime，支持以 `.agent.md` 等方式定义 Agent，并连接 MCP 工具服务器。
- InfoQ：GitLab 19.0 将 Agentic AI 嵌入 Secrets、Merge Requests、供应链安全等流程。
- InfoQ：CircleCI 推出 Chunk Sidecars，将 CI 验证能力直接带入 AI Coding 工作流。
- InfoQ：Windows 平台安全围绕 AI Agent 展开，微软试图把 Windows 定位成可信 Agent 操作系统。
- 中文 InfoQ 也已跟进 Google 为 AI Agent 打造下一代基础设施等话题。
- ChatForest 的 AI builder 月度日志也把 WebMCP 放进 2026 年 6 月 AI Builder 生态变化里，说明它已经进入开发者雷达。

## 受众关注点

- WebMCP 是什么？它和 MCP、浏览器插件、传统 API 有什么区别？
- 它解决了 Playwright、Puppeteer、Selenium 这类网页自动化方案的哪些痛点：不稳定、性能损耗、选择器脆弱、权限边界模糊，还是可审计性不足？
- 浏览器为什么可能成为 AI Agent 的关键运行时，而不只是一个被 Agent 操作的普通应用？
- 如果网页主动暴露可调用工具，前端开发是否需要像设计人类 UI 一样，为 Agent 设计 DOM 能力、表单能力和工具描述？
- WebMCP 和 MCP 的关系是什么：浏览器版 MCP、互补协议，还是未来会被统一进更大的 Agent 工具体系？
- Serverless Agents 和传统云函数有什么不同？为什么云厂商要把 Agent 定义、工具连接和任务执行放进函数运行时？
- Agent 进入 GitLab、CircleCI、Windows，是否意味着软件工程工具链会被重构？
- 对 RPA、爬虫、网页自动化行业的冲击是什么？如果浏览器原生支持 Agent 调用工具，UiPath、Automation Anywhere 以及大量基于脚本和选择器的自动化方案会不会被迫上移到流程编排、安全治理和企业集成层？
- 兼容性问题会怎样发展：Firefox、Safari、Edge 是否会跟进，还是 WebMCP 会先变成 Chrome 生态内的实验性能力？
- 安全问题如何处理：谁授权 Agent 调用工具、提交代码、访问页面数据，调用记录如何回滚、审计和隔离？

## 创作方向建议

建议写成一篇面向开发者的技术深度文章，重点解释「Agentic Web」这条基础设施线，而不是只介绍某个产品发布。WebMCP 可以作为文章开场，因为它足够具体：浏览器正在从「人类访问网页的窗口」变成「Agent 执行任务的运行时」。但文章不应停在 Chrome 的标准提案上，而要顺势把 Serverless Agents、Agentic CI/CD、Windows Agent 安全这些信号串起来。

推荐标题方向：

> 《Web 正在为 AI Agent 改写接口：从 WebMCP 到 Serverless Agents 的基础设施竞赛》

核心论点可以是：AI Agent 真正落地的关键，不是让模型学会像人一样点击网页，而是让软件系统为 Agent 暴露可理解、可授权、可审计的工具接口。WebMCP、MCP、Serverless Agents、Agentic CI/CD，本质上都是在给 Agent 建运行时。

可采用的结构：

1. 从 WebMCP 讲起：为什么「让 Agent 点按钮」不是长期方案，Playwright、Puppeteer 和 RPA 的脆弱性在哪里。
2. WebMCP 的本质：网页从人类 UI 变成同时服务人和 Agent 的双接口系统，JavaScript 函数、HTML 表单和 DOM 能力开始被包装成工具。
3. MCP 关系问题：WebMCP 不是孤立协议，而是 Agent 工具体系向浏览器运行时延伸的一个样本。
4. Serverless Agents：云函数从执行函数变成托管任务型智能体，Agent 定义、工具连接、事件触发会被云平台原生吸收。
5. 开发工具链的 Agent 化：GitLab、CircleCI、Windows 为什么都在抢入口，因为 Agent 真正进入生产流程后，代码、CI、密钥、供应链和操作系统权限都会变成运行时问题。
6. 自动化行业的再分层：传统 RPA、爬虫、网页自动化不会立刻消失，但底层点击和脚本能力可能被浏览器原生协议吞掉，价值会转向流程建模、企业权限、安全审计和跨系统编排。
7. 标准与兼容性：WebMCP 如果只有 Chrome 支持，它更像生态试验；如果 Firefox、Safari、Edge 跟进，它才可能成为 Agentic Web 的基础标准。
8. 安全与权限：Agent 时代的软件接口必须可授权、可回滚、可审计，否则「可调用」本身就会变成风险放大器。
9. 对开发者的影响：未来前端、后端、DevOps 都要考虑「Agent 可操作性」，软件接口不再只面向人和程序，也面向带目标、带权限、会连续行动的智能体。

文章重点可以放在「接口形态变化」而不是「浏览器功能更新」。我会把 WebMCP 看成一个信号：当网页开始主动告诉 Agent「我能做什么」时，Web 的语义层就不再只服务 SEO、可访问性和人类交互，它还会服务自动任务执行。这一步如果走通，浏览器厂商、云厂商、DevOps 平台和操作系统厂商争夺的就不是一个功能入口，而是谁来定义 Agent 与软件世界之间的协议边界。

## 来源线索

- Chrome for Developers：Join the WebMCP origin trial https://developer.chrome.com/blog/ai-webmcp-origin-trial
- WebDeveloper.com：WebMCP Lets Browser Agents Call JavaScript Functions and HTML Forms as Tools https://webdeveloper.com/news/google-webmcp-chrome-149-origin-trial
- InfoQ：Azure Functions Ships Serverless Agents Runtime at Build 2026 https://www.infoq.com/news/2026/06/azure-functions-serverless-agent/
- InfoQ：GitLab 19.0 Embeds Agentic AI in Secrets, Merge Requests, and Supply Chain Security https://www.infoq.com/news/2026/06/gitlab-19-agentic-ai/
- InfoQ：CircleCI Introduces Chunk Sidecars to Bring CI Validation Directly Into AI Coding Workflows https://www.infoq.com/news/2026/06/circleci-chunk-sidecars/
- InfoQ：Windows Platform Security and the Race to Secure AI Agents https://www.infoq.com/news/2026/06/windows-security-agents/
- InfoQ 中文：Chrome 推出 WebMCP 标准提案 https://www.infoq.cn/article/wCUdx4sZt94siodQI7u0
- InfoQ 中文：Google 想为 AI Agent 打造下一个 Kubernetes https://www.infoq.cn/article/jNsfjJuAJjDzGYS51jHC
- ChatForest：Builders Log June 2026 AI Builder Calendar https://chatforest.com/builders-log/june-2026-ai-builder-calendar/
