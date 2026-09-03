# 润色改动清单 — 20260903-Agent事务性与可靠性

**模式**：conservative（保守润色）
**改动总数**：6 处，全部属于允许范围（衔接 / 冗余 / 笔误 / 口语化措辞 / 标题定稿）
**超出允许范围的改动**：0 处，无需回滚

## 逐项清单

| # | 行号 | 改动前 | 改动后 | 类型 | 允许？ |
|---|------|--------|--------|------|--------|
| 1 | 3 | `概念空白—— checkpoint` | `概念空白——checkpoint` | 笔误（破折号后多余空格） | ✅ |
| 2 | 7 | `表现恰好一次…表现至少一次` | `表现为恰好一次…表现为至少一次` | 语法衔接 | ✅ |
| 3 | 11 | `这两个东西大多数时候重叠` | `这两件事大多数时候重叠` | 口语化措辞（非技术表述） | ✅ |
| 4 | 140 | `从 niche 方案变成` | `从小众方案变成` | 删英文行话（StyleRule） | ✅ |
| 5 | 144 | `这是确定性强放的必然要求` | `这是确定性运行的必然要求` | 病句修正（不改变技术含义） | ✅ |
| 6 | 1 | `# Agent 事务性：当 checkpoint 靠不住时，你的 Agent 还剩下什么` | `# Agent 事务性：当 checkpoint 靠不住时，如何保证一致性` | 标题定稿（用户指定） | ✅ |

## 影响范围自检（conservative 强制项）

对照草稿与成稿 diff，以下受保护元素逐项核验**均未被改动**：

- 数字：1.2.9 / 1.15.2 / 1.x / 10.6% / 11.7% / 45/71 / 63/71 / 3 亿美元 / 50 亿美元 / 4 种 / 79% / 42% / N 次 / 2026 年 8 月 4 日 / 8 月 14 日 / 2026-06-13 / 2026-06-15 / 2026-08-29 ✅
- 单位：token、GB 类无；ms 无 ✅
- arXiv 编号：2608.03836 / 2608.29381 / 2608.13900 / 2606.15376 / 2604.23283 / 2606.17182 / 2503.11951 / 2503.13657 / 2601.06112 / 2608.02645 / 2608.01710 / 2607.27834 / 2602.23193 ✅
- URL / DOI：参考来源 17 条链接全部原样保留 ✅
- 代码块：τ 形式化定义、可逆性分层（Idempotent ⊂ Reversible ⊂ Compensable ⊂ Irreversible）✅
- 表格：5 框架 × 5 能力横评表原样保留（含 ✅/⚠️/❌ 与批注文字）✅
- 公式：`INSERT ... ON CONFLICT (key) DO NOTHING`、`invoke(None, config)`、`{workflowRunId}:{stepId}`、`runtime.heartbeat()` ✅
- 专有名词英文原形：MoE 类无；ACID、SOTA、MTPO、2PL、OCC、Saga、OCC、fencing token、checkpoint、superstep、Durable Execution、watchdog/heartbeat、TLA+ ✅
- 术语中文翻译（首次出现）：恰好一次（exactly-once）、至少一次（at-least-once）、语义原子性/一致性/隔离/持久性、持久执行、幂等/可逆/可补偿/不可逆 ✅
- 事实性论断：未增、未删、未改（含"五个主流框架""实测全崩"等表述均保留原样，交由 review-article 复核）

## 备注

- 导读称论文验证"五个主流框架"，正文第 5 行实测列举 LangGraph / CrewAI / pydantic-graph 三个。二者口径可能不一致，属数据/事实层面问题，conservative 模式不触碰，**建议 review-article 阶段核实 RESUME CONTRACT 实际覆盖框架数量**。
- 未新增任何数据、引用或事实表述（review-article 阶段修正除外，见下）。

---

# review-article 修正记录（2026-09-03，用户批准执行）

依据：3 个并行 fact-check（arXiv/技术细节、商业数据、叙事审查）+ LangGraph 官方文档直接仲裁。**驳回** fact-check-3 的 8.1（其称 retry_on 与文档相反——官方原文 "retries on any exception **except** ValueError/TypeError/RuntimeError..."，证明文章原表述正确）。

## 必须改（4，全部执行）

1. §4 MTPO 全称：杜撰的 "Multi-Agent Transaction Processing with Ordering" → 论文原文 **Monotonic Trajectory Pre-Order（单调轨迹预序）**
2. §5 原"实测里还有更隐蔽的问题"段：**来源归属错误**（ADK/MAF 的 checkpoint_id、fencing token、三 executor 重跑实为 Diagrid 发现，RESUME CONTRACT 不测 ADK/MAF）→ 整段移入 §1 并标注 Diagrid 出处；ADK 修正为 `invocation_id`；"三 executor 重跑"限定 MAF
3. §2 "两类断层"归属：RESUME CONTRACT → **Safe to Resume**（五种失败模式的分类学）；**删除**无法溯源的"不保存 LLM 内部的置信度、推理链、工具选择原因"（RESUME CONTRACT 全文无此内容）
4. 首节框架列表：补全五个（LlamaIndex Workflows 2.22.2、AutoGen AgentChat 0.7.5），与导读"五个"一致；正文改述方法为"确定性、不依赖 LLM 的 harness"（论文原话）

## 删除（无法验证/未被引用）

- 参考来源中正文从未引用的 5 条：ReliabilityBench (2601.06112)、Verified Tool Calls (2608.02645)、Beyond Single-Use Tokens (2608.01710)、MemTxn (2607.27834)、ESAA (2602.23193)
- "几乎换不回加速"外的绝对化："会导致整个系统卡死"→ 论文实测值"阻塞触碰重叠状态的 Agent、每轮死锁 0.81 次"；"最务实的落地框架"→"综合上述研究的务实分层"；"默认基座之一"→"重要选项"；"实测全崩"→"实测无一一致"；"不是 corner case"→ 区分真实复现（deer-flow）与构造场景（其余）

## 事实修正（建议改，全部执行）

- §1 表数据源：改为"Diagrid 2026 年 2–3 月横评系列（两篇）+ LangGraph 官方 checkpointer 文档（per-task writes）"
- §3："Agent 之间的语义污染"→"失败状态污染后续执行"（论文消融为单 Agent 内）；ACID-Agent 补"初步结果、仅数据 Agent 场景"；消融补"限 Environment 域"
- §4：MTPO 三件事补"通知-重判"核心机制；补第二前提"LLM 误判率约 5%"（论文实测）；"大多数工具 API 不具备"改为作者现实观察句式；Revisable by Design 补原语境（流式修订理论）
- §6：retry_on 清单加"等"；§7：Vercel Workflow DevKit → "Vercel Workflow SDK（原名 Workflow DevKit）"（2026-04 更名）；补 activity 卸载的工程解法
- 79%/42% 数据：从结尾移至 §2 Safe to Resume 首次出现处，保留"（第三方引述）"标注
- 术语首现注解：superstep、fencing token、Saga、幂等键、upsert、TLA+、MTPO 中文名
- 参考标题按官方补全：Resume Means Resume 全名、Safe to Resume（补 "of Agent Execution"）、SagaLLM（补 "for Multi-Agent LLM Planning"）、MAST（官方标题无 MAST，改为 "Why Do Multi-Agent LLM Systems Fail?（MAST 失败分类学）"）

## 叙事调整（建议/可选改，执行）

- §1"先拉一个全景"、§2"讲起"句压缩、结尾排比后新增实践落点（幂等键+提交边界），避免与导读同义复读
- §5 删除 Diagrid 段后新增过渡"形式化验证在这条线上不止一家"

## 核实通过、未改动项（摘要）

13→8 个正文引用 arXiv 编号全部真实、日期正确；六个性质/五种模式/三攻击对应关系/四语义定义/τ 形式化/10.6%/11.7%/45→63/71/Temporal 3亿@50亿/MAF 归属/MCP Tasks durable handles/Pydantic AI 4 种/DBOS/LangGraph 故障层工程表述（retry_on、run_timeout/idle_timeout、heartbeat、invoke(None,config)）均与一手来源一致，原样保留。
