## 2026-06-25

- article-to-presentation HTML 引擎重构：方案设计与实现
  - /before-dev 分析 Gamma/Manus Slides 架构，propose 3 方案
  - 保留/删除/重构清单输出，spec 写入 docs/superpowers/specs/
  - 用户 4 张慢学AI截图确认多页/多布局/图表需求，接受 ECharts CDN
  - 完整实现 29 个模板、parser、renderer、prompts、generate.py
  - 删除 @slidev/cli / neocarbon 依赖，归档旧 Slidev 文档
  - 更新 AGENTS.md / README.md
  - 验证渲染成功（/tmp/test-slides.html 16KB）
  - CHUNK: HTML 引擎重构 spec + plan

- article-to-presentation 流程优化：砍 plan 和 Playwright，纳入 agent
  - 读取 ses_101085e69ffe7n5PkguWhnIxP2 分析实际执行流程
  - 发现 Metis 审查耗时 ~6min，占流程一半
  - 三项决策：context-cover + visual-cover 串行、validate_slides.py 替代审查、阶段二缩为 1 问
  - SKILL.md 重写为 4 阶段简化流程
  - context-cover.md / visual-cover.md 更新精确 data schema + 陷阱警告
  - 创建 validate_slides.py（33 条 schema 规则）
  - 删除 prompts/ 目录（合并到 agents），更新 references/README.md
  - CHUNK: validate_slides.py 校验脚本

## 2026-06-22

- AI压缩执行力 PPT: 从 Reveal.js 设计到 Slidev 方案转型
  - 开始实现 31 页 PPT 设计文档，visual companion 确认了 4 组图表选型
  - grill-me 解决 10 项歧义：CDN 加载、手动翻页、系统字体栈、阶梯图而非进度条等
  - Metis 分析发现 11 个歧义和多个 AI agent failure modes
  - 实施计划编写（7 Task 顺序构建），Momus 拒绝因路径不在 .omo/plans/
  - 5 个修复：font-family、颜色错误、!important 超限、逐张测试、插入锚点
  - CHUNK: PPT 实施计划（7 Task, Playwright 验收）
  - CHUNK: PPT 设计终版 spec（25 项已确认决策）

- article-to-presentation skill 重构：剔除 Playwright 验证
  - 用户要求删除 Playwright 逐张截图验证，改为纯手动审查
  - SKILL.md 和 common-pitfalls.md 更新，playwright-verification.md 删除

- article-to-presentation skill 重构：Reveal.js → Slidev + neocarbon
  - 嫌手写 HTML 太重，想要霓虹/赛博视觉风格
  - 选型对比 Slidev(vibe/cyberpunk-ide/neocarbon) → 最终选 neocarbon（22 布局+25 组件）
  - 新工作流：文章 → 提取数据 → /before-dev → 生成 slides.md + slidev build
  - Metis 审查发现 3 个致命问题：布局映射大范围错误、42% 幻灯片无覆盖、颜色编码机制空白
  - 修复 spec：更正映射表、补充 neocarbon 设计令牌和组件 API、增加 metrics 布局
  - CHUNK: Slidev 技能设计 spec（含布局映射表、组件 API、设计令牌）

- article-to-presentation skill 实现：三个文件全部重写
  - SKILL.md（182 行）、technical-details.md（401 行）、common-pitfalls.md（71 行）
  - 删除 11 个 CSS 组件模板、Reveal.js 配置、!important 约束、Momus 审查
  - 新增 neocarbon 8 布局 API、3 组件 API、5 色设计令牌、动画控制

- session-log 驱动 skill 迭代（ses_10ffdd91cffelj24szm74YDTVB）
  - 读取实际使用会话，总结 7 个实践经验
  - 更新 SKILL.md：优先复用文案、中文目录名警告、TOC 隐藏 CSS、国内镜像
  - 新增 common-pitfalls：中文目录/导航遮挡/npm 慢/serve 配置（12→16 条）