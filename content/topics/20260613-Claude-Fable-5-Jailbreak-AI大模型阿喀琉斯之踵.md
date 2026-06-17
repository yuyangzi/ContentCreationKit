# 从 Claude Fable 5 被封说起——jailbreak 为什么是所有大模型的"阿喀琉斯之踵"？

## 主题定位

- **领域**：AI Agent 大模型
- **类型**：技术科普
- **目标读者**：AI 开发者、技术从业者
- **确认时间**：2026-06-13

---

## 热度背景

### 事件概述

2026 年 6 月 9 日，Anthropic 发布其史上最强模型 **Claude Fable 5**（以及面向网络安全的 Mythos 5）。不到 4 天后（6 月 12 日晚 ET），美国政府以国家安全为由，引用出口管制法规，要求 Anthropic **禁止所有外籍人士访问 Fable 5 和 Mythos 5**——包括 Anthropic 自己的外籍员工。Anthropic 被迫对所有用户关闭这两个模型。

### 热度数据

- **知乎**：1087 万热度（全站当日 #1）
- **36氪**：阅读量 1.6 万+
- **NBC News、NDTV、Financial Express** 等国际主流媒体广泛报道
- **掘金**：多篇相关讨论文章登上热榜

### 政府给出的理由——以及另一个 jailbreak

**触发封禁的 jailbreak（由竞争对手向政府报告）**：让 Fable 5 读取一个特定代码库，找出并修复其中的软件漏洞。政府担心外籍人士可利用此能力进行网络攻击。Anthropic 驳斥称这些漏洞都是"已知的、次要的"，且 GPT-5.5 也能做到同样的事。

**另一个 jailbreak（Pliny the Liberator 的"群狼战术"）**：几乎同时，知名 AI 红队黑客 Pliny the Liberator 宣布用"多 Agent 协同攻击"绕过了 Fable 5——手法包括 Unicode 同形异义字替换、长上下文引用追踪、分解-重组法（将敏感问题拆成"无害"的子问题，再拼凑成攻击性知识）。他成功让模型生成栈缓冲区溢出利用代码和冰毒合成路径，并泄露了 Fable 5 的完整 system prompt（~120,000 字符）。Anthropic 回应称 Pliny 拿到的输出实际被独立 classifier 层路由到了较弱的 Opus 4.8 模型。

——两个 jailbreak，一个"温和"（读代码修 Bug），一个"激进"（多 Agent 协同）。政府用前者触发封禁，后者则说明：**jailbreak 的攻击手段远不止一种。**

### Anthropic 的反驳

Anthropic 在官方声明中公开表示不认同这一决定，核心论点：

1. 所谓的 jailbreak 是**窄范围、非通用**的，不影响模型的主体安全性
2. 同等能力在 **OpenAI GPT-5.5 等其他公开模型**中也存在
3. "如果这个标准应用于全行业，**所有前沿模型部署都将停止**"
4. 政府仅提供了"口头证据"，缺乏技术细节和透明度
5. AI 安全应该是**纵深防御**（defense in depth）——监控 + 快速响应，而非追求"完美防线"

### 延伸背景：Anthropic 与五角大楼——这是"前传"

Fable 5 被封不是孤立事件。在此之前的半年里，Anthropic 与美国军方已爆发了一场激烈冲突：

| 时间 | 事件 |
|------|------|
| 2025.07 | 五角大楼授予 Anthropic $200M 合同开发军用 AI |
| 2026.01 | Claude 被用于抓捕委内瑞拉前总统马杜罗的行动——这触发了 Anthropic 对军方用途的警惕 |
| 2026.02.24 | 国防部长 Hegseth 发最后通牒：2 月 27 日前同意**无限制使用**，否则后果自负 |
| 2026.02.26 | CEO Dario Amodei 公开拒绝——两条红线：**全自主武器**（当前技术不够可靠）、**大规模国内监控** |
| 2026.02.27 | 特朗普下令联邦机构停用 Anthropic；Hegseth 将其列为**"供应链风险"**——此前该标签只用于敌对国家实体 |
| 2026.03.09 | Anthropic 起诉联邦政府 |
| 2026.03.26 | 地方法院判 Anthropic 胜诉（认定政府行为属报复性执法） |
| 2026.04.08 | 上诉法院**推翻判决**（理由：正值重大军事冲突期间，不能强迫美军继续使用"不受欢迎的供应商"） |

Hegseth 的原话："We will not employ AI models that won't allow you to fight wars."（我们不会使用不让你打仗的 AI。）

——这意味着：Fable 5 被封时，Anthropic **已经处于与政府的法律战状态**。这次封禁是否为报复升级？留给读者判断。

- 特朗普于 6 月 2 日签署 AI 行政令，要求联邦机构评估最强 AI 模型的国家安全风险——**但明文规定不设强制许可制度**（商务部对 Fable 5 的封禁恰恰突破了这一限制）
- 印度、中国开发者刚通过 Project Glasswing 获得 Mythos 访问权即被掐断

---

## 创作方向建议

### 核心叙事线

1. **引子（10%）**：Fable 5 上线 3 天即被封——AI 史上最快"下架"
2. **什么是 jailbreak？（25%）**：
   - System prompt 注入原理
   - 角色扮演绕过（"假装你是…"）
   - Few-shot 诱导（"我给你几个例子…"）
   - 编码绕过（用代码形式包装恶意请求）
   - 多轮对话累积（逐步引导越过红线）
3. **为什么防不住？（30%）**：
   - Alignment tuning 的矛盾：能力越强越难约束
   - RLHF 只能训练"偏好"而非"消除能力"——模型的能力和知识是训练阶段获得的，RLHF 只是在上面加了一层偏好薄膜
   - 通用 jailbreak vs 非通用 jailbreak：防御的不对称性
   - Anthropic 的纵深防御策略：不是完美防线，而是层层阻截 + 快速响应
    - 为什么"完美 jailbreak 防御"在数学上几乎不可能——这不是 Anthropic 的工程水平问题，而是数学问题。Fawzi et al. (2015) 的"对抗鲁棒性基本极限"定理证明：对高维空间中足够复杂的分类问题，任何分类器都存在对抗性盲区。语言模型本质上是 token-level 的分类器——把 jailbreak 理解为"在离散 token 空间中搜索决策边界盲区"，那么攻击者只需成功一次（找到一个盲区），防御者需要防住所有可能的输入组合。Mahloujifar et al. (2019) 的"强 No Free Lunch 定理"进一步证明：在满足基本曲率条件的任何数据分布上，任何非完美分类器都能以高概率被对抗性愚弄。数学已经给出了答案：不是 Anthropic 不行，是没人行。
4. **这件事意味着什么？（25%）**：
   - AI 安全监管的技术边界：政府是否有能力判断什么是"危险"的能力？
   - 出口管制的武器化：AI 沦为地缘政治工具
   - 对中国开发者的影响：如果最强模型被封，国产替代的紧迫性
   - 一点争议：Anthropic 是"技术良心"还是"商业博弈"？
5. **结尾（10%）**：Fable 5 不会是最后一个。当模型能力越过某个阈值，每一次发布都可能触发地缘政治地震。AI 行业的"古巴导弹危机"才刚刚开始——以后每一次前沿模型发布，安全团队在手忙脚乱修 jailbreak，政府团队在手忙脚乱写禁令，而我们作为开发者，站在中间，看着两边的博弈，思考一个更根本的问题：在这个数学上注定不安全的系统里，"足够安全"的门槛到底在哪？

### 参考来源

**事件来源**：
- [Anthropic 官方声明：暂停 Fable 5/Mythos 5](https://www.anthropic.com/news/fable-mythos-access)
- [Anthropic CEO Dario Amodei 五角大楼声明](https://www.anthropic.com/news/statement-department-of-war)
- [Anthropic RSP v3.1（纵深防御架构细节）](https://www-cdn.anthropic.com/files/4zrzovbb/website/bf04581e4f329735fd90634f6a1962c13c0bd351.pdf)
- [Axios：外资禁令独家报道](https://www.axios.com/2026/06/12/anthropic-trump-mythos-fable-national-security)
- [CBS News：Anthropic-五角大楼冲突](https://www.cbsnews.com/news/anthropic-pentagon-pete-hegseth-feud/)
- [TechPolicy.Press：冲突完整时间线](https://techpolicy.press/a-timeline-of-the-anthropic-pentagon-dispute)
- [NBC News 报道](https://www.nbcnews.com/tech/tech-news/anthropic-suspends-new-ai-models-fable-mythos-government-directive-rcna349901)
- [SecurityWeek：jailbreak 争议](https://www.securityweek.com/anthropic-disputes-fable-5-ai-jailbreak/)
- [知乎热榜讨论](https://www.zhihu.com/question/2049072203191342205)
- [36氪报道](https://www.36kr.com/p/3851015329027336)
- [白宫 AI 行政令原文](https://www.whitehouse.gov/presidential-actions/2026/06/promoting-advanced-artificial-intelligence-innovation-and-security/)

**学术/技术来源**：
- Fawzi et al. "Fundamental limits on adversarial robustness" — 分类器对抗鲁棒性理论上限
- Mahloujifar et al. "Strong No Free Lunch Theorem on adversarial robustness" — 任何分类器都无法逃避对抗性攻击的数学证明
- Anil et al. "Many-shot Jailbreaking" (NeurIPS 2024) — 长上下文 jailbreak 机制
- Zou et al. "Universal and Transferable Adversarial Attacks on Aligned Language Models" (GCG, 2023) — 自动 jailbreak 优化算法
- Anthropic "How we contain Claude" — 安全隔离工程实践

### 差异化价值

- 不做事件复读机，而是**借事件讲懂一个技术概念**
- 从开发者视角出发，讲清楚"为什么这个事技术上无解"
- 结合国内 AI 生态现状，给读者实用性思考

---

## 状态

- [x] 主题确认
- [x] 参考资料审核（2026-06-13，grill-me 7 轮 + 深度搜索 6 方向 20+ 来源）
- [ ] 草拟大纲
- [ ] 撰写正文
- [ ] 审核发布
