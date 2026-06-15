# MiMo Code vs Claude Code 架构分化 - 审核参考资料

**审核时间**：2026-06-14
**审核方式**：grill-me 逐轮拷问（9 轮） + 深度调研

---

## 一、Grill-Me 审核问答记录

### Q1: 核心观点定位——技术对比还是行业观察？

**问**：标题是"架构分化之战"，但三条主线读下来更像"商业模式分化"。这篇文章的核心论点是"两种架构设计哲学的技术对比"还是"开源 vs 闭源两种商业模式对开发者的影响"？

**答**：**两种架构设计哲学的技术对比**。

**决策影响**：文章聚焦技术架构对比，商业逻辑作为背景而非主线。

---

### Q2: 技术深度——写到哪一层？

**问**：主题文件的技术描述停留在概念层。可选三层深度：架构图层（列对比表）、机制层（讲具体实现和设计取舍）、源码层（引用代码和调用链）。

**答**：**机制层**。

**决策影响**：每个技术维度需要展开到"他们是怎么做的 & 为什么这么做"，不能停留在"Claude Code 有 7 层安全、MiMo Code 有四层记忆"这类标签式描述。

---

### Q3: 三条主线的权重分配

**问**：机制层深度会让主线二（商业逻辑）显得格格不入，主线三（选型建议）体量不足。如何处理？

**答**：**主线一为主干，主线二改为"设计哲学溯源"，去掉主线三**。

**决策影响**：
- 主干是三个技术维度的机制层深度对比
- 设计哲学溯源融入每个维度的 insight 部分（不单独成章）
- 不写开发者选型建议

---

### Q4: 叙事框架——"分化的根因"是什么？

**问**：文章开篇叙事是"同一个问题两种解法"还是"它们根本不是解决同一个问题"？

**答**：**方案 2——先定义各自的核心问题域不同，再展开架构对比**。

**决策影响**：
- Claude Code 的核心问题是：在不可靠的 AI 决策层之上，如何保证安全、可恢复、人类可控？
- MiMo Code 的核心问题是：当任务超过 200 步，模型遗忘上下文、跑偏方向，怎么持续保持目标对齐？
- 开篇需要先建立这个认知前提，否则读者会困惑"为什么 CC 不做四层记忆？"

---

### Q5: 技术对比的维度选择

**问**：主题文件有 5 个对比维度，但"开源/闭源"不是技术维度，"核心关注"太定性。哪些维度能写到机制层？

**答**：**聚焦三个高价值技术维度**：

| 维度 | Claude Code 侧 | MiMo Code 侧 |
|------|---------------|-------------|
| 上下文管理 & 记忆体系 | 压缩机制、CLAUDE.md + auto memory、JSONL 恢复 | 四层记忆、Cycle+Checkpoint+Rebuild、writer subagent |
| 任务编排 & 质量保障 | 模型动态决策、7 层安全钩子 | Dynamic Workflow、Max Mode、Goal 机制 |
| 长期进化能力 | CLAUDE.md 手动维护、遥测数据闭环 | Dream（7 天整理）、Distill（30 天固化） |

**逻辑链**：任务中怎么记 → 任务中怎么不跑偏 → 跨任务怎么越来越聪明。

---

### Q6: 每个维度的展开结构

**问**：怎么避免"A 用 X，B 用 Y"的平铺式对比？

**答**：**三步法**：
1. 先定义各自要解决什么问题（2-3 句）
2. 展开各自的机制设计实现细节（主体，含架构对比图）
3. insight：这个设计意味着什么——为什么 A 不会做 B 的事，反之亦然（2-3 句）

---

### Q7: 文章立场——谁"赢了"？

**问**：主题文件引用了 MiMo Code 的 benchmark 数据（三项优于 CC、200+ 步胜率 65%+）。如何处理这些数据？

**答**：**方案 3——benchmark 是噪音，架构逻辑才是信号**。
- benchmark 数据一笔带过，用"初步测试显示"而非"证明了"
- 核心价值在"理解设计取舍"，不在"谁跑分高"
- 两个工具在各自问题域都是最优解

---

### Q8: "设计哲学溯源"怎么溯源？

**问**：改为"设计哲学溯源"后，从什么角度展开？

**答**：**方案 1+2 结合——团队基因 + 产品定位**：
- Claude Code：Anthropic 的安全文化（Constitutional AI、RSP）→ 7 层安全机制是基因表达
- MiMo Code：罗福莉带队、5 人 2 周、小米"快迭代+开源"文化 → Max Mode、Dream/Distill 是应用层激进创新
- 融入各维度 insight 部分，不单独成章

---

### Q9: 现有材料的机制层充足度

**问**：当前参考材料能否支持机制层深度？还缺什么？

**答**：**启动轻量研究补齐缺口**。关键补充：
- Claude Code：VILA 分析中的压缩实现方式、7 层安全的具体触发逻辑
- MiMo Code：Cycle 的 checkpoint 触发时机、writer 的 11 字段结构、Dream/Distill 的具体产出

（已完成，见下方研究记录）

---

## 二、背景研究记录

### 数据来源

| 来源 | URL | 类型 | 质量 |
|------|-----|------|------|
| MiMo 官方技术博客 | https://mimo.xiaomi.com/zh/blog/mimo-code-long-horizon | 一手 | Tier 2（官方团队博客） |
| InfoQ 深度报道 | https://www.infoq.cn/article/GTYmDTKIy8f79604Jz1V | 二手深度分析 | Tier 2（专业媒体，引用原始论文） |
| VILA 实验室论文 | https://arxiv.org/abs/2604.14228 | 学术论文 | Tier 1（arXiv preprint，源码级分析） |
| MiMo Code GitHub | https://github.com/XiaomiMiMo/MiMo-Code | 开源代码 | Tier 2 |

### Claude Code 关键机制细节（来源：InfoQ 报道 + VILA 论文摘要）

**代码规模与架构概览**：
- v2.1.88 版本：约 1900 个 TypeScript 文件，约 51.2 万行代码
- 仅 1.6% 属于 AI 决策逻辑，其余 98.4% 都是确定性基础设施
- Agent 核心循环只是一个简单的 while 循环
- 真正的工程复杂度在围绕它构建的外围系统

**7 层安全机制（名目已知，但各层具体触发逻辑需从论文原文获取）**：
- hooks、分类器、压缩机制、隔离机制（具体触发时机未在二手材料中详细展开）

**记忆体系**：
- CLAUDE.md：项目级规则、编码约定、构建/测试方式，可版本化，手动维护
- auto memory：对话过程中自动沉淀的记忆
- JSONL session transcript：以 JSONL 格式记录完整会话
- 子 Agent sidechain transcript：子 Agent 完整轨迹写入独立 sidechain，父 Agent 只接收摘要

**任务编排**：
- 模型动态决策：模型看到上下文后决定下一步工具调用
- AgentTool：可委派子 Agent
- 可扩展机制：MCP、skills、hooks
- 停止判断：主 Agent 自行判断是否不再需要工具调用 + 系统条件（max turns、context overflow、hooks、abort）

**设计哲学**：
- 每一项设计选择可追溯到：人的决策权、安全性、可靠性、能力放大和适应性
- 跨层交织的 Harness 难以重新实现：循环易复制，但 hooks、分类器、压缩机制和隔离机制不易复制

### MiMo Code 关键机制细节（来源：小米官方技术博客）

**计算层**：

*Max Mode（并行采样选优）*：
- 每轮并行生成 N 个候选方案（默认 N=5）
- 每个候选独立完成推理和工具调用规划，不实际执行
- 同一模型作为 judge，对比所有候选的推理和行动计划，选最优执行
- 默认 temperature=1，5 次独立采样几乎不会产出相同结果
- 候选收敛时→置信度高；候选差异大时→低温度 judge 选最稳健方案
- SWE-Bench Pro 提升 10-20%，代价约 4-5 倍 token 消耗
- 目前为实验性功能，需手动配置

*Goal 机制（独立完成度验证）*：
- 用户设定自然语言停止条件（如"所有测试通过且代码已提交"）
- Agent 每次尝试终止时，系统自动发起一次独立模型调用审查完整对话历史
- 判断条件是否真正满足；未满足→反馈差距让 Agent 继续；无法完成→判定不可能
- 验证者不参与实际工作，不会产生认同偏差
- 误拦（条件满足但判定未满足）比漏放更常见，整体死循环概率 < 0.5%
- Max Mode 和 Goal 是 test-time compute 的两个正交方向：并行 vs 串行

*Dynamic Workflow（代码化编排）*：
- 主 Agent 生成 JavaScript 脚本，在隔离沙箱中确定性执行
- 脚本通过 `agent()` 派出子 Agent，`parallel()` / `pipeline()` 控制并发
- `if` 不会忘记分支，`for` 不会提前退出，barrier 不会漏掉子 Agent
- 兼容 Anthropic Dynamic Workflow 核心语义
- 扩展：`workflow()` 原语（可复用组合）、日志恢复（中断后从磁盘恢复）、沙箱内文件读写
- 核心洞察：当流程每一步必须执行、分支条件必须精确、重试逻辑必须可靠时，就应用代码而非自然语言保证

**记忆层**：

*Cycle 机制*：
- 窗口有上限，turn 在累积，不干预则到达上限时退化或结束
- checkpoint 在远低于上限处触发（~20%、45%、70% 预算处）
- 每次 checkpoint 是增量更新，没有一次是孤注一掷的总结
- 接近上限时执行 rebuild：切断当前窗口，开启新窗口，用持久化文件重建上下文
- Cycle 没有数量上限——逻辑会话是 cycle 的链，链没有最大长度

*为什么提早提取（不是快满时才压缩）*：
- 第一：模型在高上下文利用率下能力衰减（"lost in the middle"）→ 要求在退化时刻做最关键压缩不划算
- 第二：提取本身需要空间。95% 利用率下已无处思考；30% 利用率下则游刃有余

*Writer subagent*：
- 主 Agent 不维护自己的记忆——提取被完全移出主循环
- 由运行时触发，独立 writer subagent 完成，不与主 Agent 共享注意力或 token 预算
- 写入固定结构 checkpoint 文件（11 个字段）：
  1. 当前意图
  2. 下一步动作
  3. 工作约束
  4. 任务树
  5. 当前工作
  6. 涉及文件
  7. 跨任务发现
  8. 错误与修复
  9. 运行时状态
  10. 设计决策
  11. 杂项笔记
- Single-writer 约束：每个结构化文件只有恰好一个 actor 被允许写入
- 主 Agent 只对结构化文件有读权限，例外是 notes.md（自由格式 scratchpad）
- notes.md：主 Agent 唯一写入通道，writer 在 checkpoint 时读取、路由到结构化字段、清空

*四层记忆*：
1. **Session 记忆**（checkpoint.md）：当前逻辑会话内
2. **Project 记忆**（MEMORY.md）：项目级持久知识，架构决定、用户规则、反复验证过的技术事实
3. **Global 记忆**：用户级偏好，跨项目生效
4. **History**：每个会话的完整 SQLite 轨迹，每条消息、每次工具调用原文存储

四层关系：上层越来越精炼/持久/小，下层越来越完整/庞大/慢。Writer 负责向上提炼，history 负责向下兜底。

*Rebuild 注入*：
- 分层 prompt 注入新窗口，每段独立 token 上限，顺序为：
  任务清单 → session checkpoint → 最近用户消息逐字切片 → 项目记忆 → 全局记忆 → notes → memory 文件路径索引 → tail reminder
- 注入总量控制在约 65K token 以内
- Agent 恢复后直接继续工作，不需重新确认目标或重读已处理文件

**进化层**：

*项目记忆文件设计*：
- Markdown 格式（可审查性优先于检索效率）
- 选择文件而非纯向量数据库的核心原因：用户需要能看到系统记住了什么、删除错误条目、修改过时知识

*Dream（7 天自动整理）*：
- 每 7 天自动触发
- 独立 Agent 读取历史 session 对话和现有记忆文件
- 执行合并、去重、验证路径有效性、压缩
- 将分散记忆收敛为紧凑当前状态，更新全局记忆

*Distill（30 天模式固化）*：
- 每 30 天自动触发
- 独立 Agent 读取历史 session
- 关注流程而非知识：识别反复出现的工作模式
- 固化为可复用 Skill、CLI 命令、自定义 Agent 或 SOP 文档

**Benchmark 数据（备查，文章中使用需加谨慎语言）**：
- MiMo Code + MiMo-V2.5-Pro 在 3 项离线 benchmark 中均优于 Claude Code + Sonnet 4.6
- 真人双盲 AB 测试：576 名开发者、474 个私有仓库、1213 个有明确胜负判定的 AB 配对
- 200 步以内：两者胜率接近 50%
- 200 步以上：MiMo Code 胜率升至 65%+
- ⚠️ 小米团队自述：离线 benchmark 主要衡量单仓库问题一次性解决能力，MiMo Code 的多轮记忆、状态维持、完成验证等优势需在真实多轮开发中体现

---

## 三、修正建议（供审核，不直接修改主题文件）

基于 9 轮 grill-me 共识，以下是需要修正/补充的条目：

### 1. 标题微调

**当前**：`MiMo Code vs Claude Code：AI编程Agent的架构分化之战`

**建议**：`MiMo Code vs Claude Code：两种编程 Agent 的架构路线分化`
- 理由：去掉"之战"（立场已确认为不判断谁赢），"路线"比单纯"分化"更明确表达这是设计路径的根本选择

### 2. 主线二需要重写

当前主线二内容为商业逻辑（Anthropic 为什么闭源、小米为什么开源），需改为"设计哲学溯源"：
- 从团队基因（Anthropic 安全文化 vs 小米快迭代文化）和产品定位（操作系统层 vs 应用实验层）两个角度切入
- 融入三个技术维度的 insight 部分，不单独成章

### 3. 删除主线三

该部分（对开发者的实际意义/选型建议）已被确认删除。

### 4. 对比维度表需调整

当前表格有 5 个维度，建议：
- **删除**"开源状态"行（不是技术维度）
- **删除**"核心关注"行（太定性，改为在各维度第 1 步"问题定义"中自然引入）
- **保留并深化**：记忆体系、任务编排、停止判断
- **新增**：长期进化能力

### 5. Benchmark 数据需加谨慎语言

当前写作建议未提及对 benchmark 数据的处理方式。需标注：
- 这些 benchmark 来自小米官方测试，结论标注"初步测试显示"
- 强调 Agent 评测体系本身不成熟，benchmark 数据仅作参考
- 核心价值在架构设计逻辑对比而非跑分

### 6. 需补充技术细节

基于参考材料，以下机制层信息已足够丰富，可直接写入：
- MiMo Code：Cycle 触发时机（20%/45%/70%）、writer 11 字段结构、rebuild 注入顺序、Dream/Distill 触发周期和产出
- Claude Code：代码规模（1900 文件/51.2 万行）、1.6% AI 逻辑占比、记忆体系四件套的具体分工、任务编排的模型动态决策模式
- **仍缺**：Claude Code 7 层安全机制各层的具体触发时机和实现细节（二手材料仅列出名称）。如需写到机制层深度的安全维度，建议从 VILA 论文原文（arxiv 2604.14228）补充。

### 7. 结构建议

建议的最终文章结构：

```
1. 开篇：它们根本不是解决同一个问题
   - Claude Code 的核心问题域：安全、可恢复、人类可控
   - MiMo Code 的核心问题域：长程任务的记忆连续性与目标对齐
   - 产品定位差异：操作系统层 vs 应用实验层

2. 维度一：上下文管理与记忆体系（任务中怎么记）
   - Claude Code 侧：压缩 + CLAUDE.md + JSONL
   - MiMo Code 侧：Cycle/Checkpoint/Rebuild + 四层记忆 + writer
   - Insight：为什么 CC 不做四层记忆（安全优先 vs 连续性优先）

3. 维度二：任务编排与质量保障（任务中怎么不跑偏）
   - Claude Code 侧：模型动态决策 + 7 层安全钩子
   - MiMo Code 侧：Max Mode + Goal + Dynamic Workflow
   - Insight：信任模型判断 vs 用代码保证流程

4. 维度三：长期进化能力（跨任务怎么越来越聪明）
   - Claude Code 侧：CLAUDE.md 手动维护 + 遥测闭环
   - MiMo Code 侧：Dream + Distill 自动进化
   - Insight：人类外循环进化 vs Agent 自主进化

5. 设计哲学溯源（融入各维度，或作为收尾章节）
   - 安全基因 → 7 层机制
   - 快迭代基因 → 应用层激进创新
```

### 8. 参考来源补充

当前参考来源缺少 VILA 论文的作者/机构标识和摘要。建议补充：
- VILA 实验室（具体机构名待确认）对 Claude Code v2.1.88 的源码级分析
- 论文中是否对 Claude Code 的压缩机制（截断 vs 摘要）有具体描述需核实

---

## 四、资料完整性评估

| 维度 | 机制层细节充足度 | 备注 |
|------|-----------------|------|
| MiMo Code 记忆体系 | ✅ 充足 | 官方博客完整描述 Cycle/Checkpoint/Rebuild/Writer/四层 |
| MiMo Code 任务编排 | ✅ 充足 | Max Mode、Goal、Dynamic Workflow 均有机制级细节 |
| MiMo Code 进化层 | ✅ 充足 | Dream/Distill 触发周期和产出明确 |
| Claude Code 记忆体系 | ✅ 基本充足 | CLAUDE.md、auto memory、JSONL、sidechain 均有说明 |
| Claude Code 安全机制 | ⚠️ 名称级 | 7 层列出但无各层具体触发逻辑 |
| Claude Code 弹性恢复 | ⚠️ 名称级 | 提到恢复逻辑但无具体机制 |
| Claude Code 压缩机制 | ⚠️ 名称级 | 提到但未说明是截断还是摘要 |
| Claude Code 进化能力 | ✅ 充足 | CLAUDE.md 手动维护 + 遥测闭环的逻辑清晰 |

**结论**：三个选定维度的机制层细节基本充足。Claude Code 安全机制的内部细节如需进一步展开，建议获取 VILA 论文全文。

---

## 五、参考资料交叉验证记录（2026-06-14 审核）

### 验证方法

逐条比对主题文件数据与一手来源（GitHub README、MiMo 官方技术博客），二手来源数据标记引用链。

### 验证通过项（一手来源确认）

以下 20 条数据经 GitHub README 或 MiMo 官方博客直接验证，准确无误：

| # | 数据点 | 验证来源 | 状态 |
|---|--------|---------|------|
| 1 | MIT 协议开源 | GitHub README: "Source code is licensed under the MIT License" | ✅ |
| 2 | 基于 OpenCode 构建（Fork） | GitHub README: "MiMoCode is built as a fork of OpenCode" | ✅ |
| 3 | SQLite FTS5 全文本搜索 | GitHub README: "Cross-session memory powered by SQLite FTS5 full-text search" | ✅ |
| 4 | Max Mode（实验性，需手动配置） | GitHub README: "Max Mode... can be enabled via experimental.maxMode in the config" | ✅ |
| 5 | Goal 机制（独立 judge 模型验收） | GitHub README: "/goal command... independent judge model evaluates" | ✅ |
| 6 | Dream（/dream 命令） | GitHub README: "/dream — scans recent session traces, extracts persistent knowledge" | ✅ |
| 7 | Distill（/distill 命令） | GitHub README: "/distill — discovers repeated manual workflows... packages into skills" | ✅ |
| 8 | Checkpoint writer subagent | GitHub README: "maintained automatically by the checkpoint-writer subagent" | ✅ |
| 9 | 罗福莉"14 天、5 个人" | InfoQ 引用罗福莉本人推文（一手来源引用链可追溯） | ✅ |
| 10 | MiMo-V2.5-Pro 模型名称 | 小米官方博客明确使用此名称 | ✅ |
| 11 | 计算/记忆/进化三主线 | 官方博客结构明确以此三章组织 | ✅ |
| 12 | Max Mode: N=5, temperature=1 | 官方博客: "默认 N=5"、"默认使用 temperature=1" | ✅ |
| 13 | Goal: 死循环概率 < 0.5% | 官方博客: "整体死循环概率小于 0.5%" | ✅ |
| 14 | Cycle checkpoint: 20%/45%/70% | 官方博客: "大致在已配置预算的 20%、45%、70%" | ✅ |
| 15 | Writer: 11 字段结构 | 官方博客逐一列出 11 个字段 | ✅ |
| 16 | 四层记忆: Session/Project/Global/History | 官方博客: "Session 记忆 → Project 记忆 → Global 记忆 → History" | ✅ |
| 17 | Rebuild 注入: ~65K tokens | 官方博客: "注入总量也控制在约 65K token 以内" | ✅ |
| 18 | Dream: 每 7 天; Distill: 每 30 天 | 官方博客: "Dream 每 7 天自动触发"、"Distill 每 30 天自动触发" | ✅ |
| 19 | 576 开发者、474 仓库、1213 AB 配对 | 官方博客: "覆盖 576 名开发者、474 个真实私有仓库，共形成 1,213 个... AB 配对" | ✅ |
| 20 | SWE-Bench Pro: 10-20% 提升 | 官方博客: "Max Mode 相比单次采样提升 10-20%" | ✅ |
| 21 | Dynamic Workflow 兼容 Anthropic 语义 | 官方博客: "兼容 Anthropic Dynamic Workflow 的核心语义" | ✅ |

### 二手来源引用链（无法直接验证）

以下数据来自 InfoQ → VILA 论文的二手引用链，论文原文未能直接获取：

| # | 数据点 | 引用链 | 可信度 |
|---|--------|--------|--------|
| 1 | Claude Code v2.1.88: 约 1900 个 TS 文件、51.2 万行代码 | InfoQ ← VILA 论文 arxiv 2604.14228 | ⚠️ 中（InfoQ 是可信媒体，但论文未直接验证） |
| 2 | 仅 1.6% 属于 AI 决策逻辑，98.4% 是确定性基础设施 | 同上 | ⚠️ 中 |
| 3 | 7 层安全机制（hooks、分类器、压缩、隔离等） | 同上 | ⚠️ 中（只确认了 4 层名称，完整 7 层列表未知） |
| 4 | Claude Code 记忆体系: CLAUDE.md、auto memory、JSONL、sidechain | InfoQ 报道 | ⚠️ 低（未与 Anthropic 官方文档交叉验证） |
| 5 | Claude Code 设计哲学: 可追溯到"人的决策权、安全性、可靠性、能力放大和适应性" | InfoQ ← VILA 论文 | ⚠️ 中 |

### 已修正的问题

| 修正项 | 原内容 | 修正后 |
|--------|--------|--------|
| Star 数 | "5.1k GitHub Star" | "超过 5000 GitHub Star（截至 2026-06-12，来源：InfoQ）" |
| Issues 数 | "229个Issues" | "超过 200 个 Issues" |
| 7 层安全 | "7层安全机制：hooks、分类器、压缩机制、隔离机制"（只列 4 个） | "7层安全机制（已知包括：hooks、分类器、压缩机制、隔离机制等）" |
| VILA 数据 | 无引用链说明 | 标注"来源：InfoQ 报道转述，原论文 arxiv 2604.14228" |
| 数据时效 | 无标注 | 顶部增加"数据时效"说明 |

### 待核实项

1. **VILA 论文作者归属**：arxiv 2604.14228 的"VILA实验室"具体机构名称待确认。注意不要与 NVIDIA/MIT 的 VILA 视觉语言模型项目混淆。
2. **Claude Code 记忆体系官方文档**：CLAUDE.md、auto memory、JSONL session transcript 等特性的 Anthropic 官方文档链接待补充。
3. **7 层安全机制完整列表**：VILA 论文原文中 7 层的完整名称和触发逻辑待获取。
