# DeepSeek全球急招Agent人才：从大模型到Agent基础设施的战略转向

**创作方向**：AI产业竞争 / 人才市场
**选题角度**：DeepSeek Harness部门大规模招聘——从大模型竞争转向Agent基础设施争夺
**类型标签**：[趋势] 活跃 2-4 周，发展阶段
**目标读者**：AI从业者、技术管理者、投资人、求职者
**发布渠道**：微信公众号

---

## 核心钩子

DeepSeek Harness部门负责人崔添翼在线直呼"缺人缺疯了"——一口气开放研究员、工程师、产品经理三大岗位，持续一个多月没招够。这背后不仅是人才争夺战，更是DeepSeek从大模型竞争转向Agent基础设施的战略信号。核心代码智能研究员郭达雅因Agent方向优先级不够而离职出走字节后，DeepSeek紧急组建Harness团队全力押注Agent赛道——但动作是不是已经晚了？

---

## 热度背景分析

2026年6月22日，量子位报道DeepSeek Harness部门负责人崔添翼再次在线直聘，一次性放出三个岗位：Harness研究员（实习/全职）、Harness工程师（实习/全职）、Harness产品经理（全职）。崔添翼表示自己"每天都在面试，以及各种地方贴小广告"。

关键时间线：
1. **2025年10月**：郭达雅决定离职——核心原因是他看好Agent方向，但当时DeepSeek内部Agent优先级不高，重心在基座模型突破
2. **2026年3月**：郭达雅正式离开DeepSeek，加入字节跳动Seed团队担任Agent方向负责人之一；同月，前Jane Street量化工程师崔添翼加入DeepSeek
3. **2026年5月**：DeepSeek正式组建Harness团队，资深研究员陈德力在X上公开确认正在"从零构建CodeHarness"，内部对标Claude Code
4. **2026年6月**：崔添翼在线直呼"缺人缺疯了"，Harness团队持续招聘一个月仍未招满

---

## 核心分析

### 1. Harness是什么？为什么重要？

> "如果Agent是汽车，模型是发动机，那Harness就是方向盘、变速箱、刹车。"

DeepSeek提出公式：**Model + Harness = Agent**。

Harness涵盖Agent开发中模型之外的所有基础设施：
- 上下文管理（Context Engineering）
- 长期记忆（Memory）
- Subagent与Multi-Agent协同
- 自进化Agent
- 工具调用（Tool Use）
- 规划（Planning）
- MCP协议集成

这意味着DeepSeek认识到：**单纯做大模型不够，Agent时代的竞争优势在于Harness层——谁能提供最好的Agent基础设施，谁就能定义Agent生态。**

### 2. 三类岗位背后的战略布局

**研究员（新增岗位）**：负责"定义问题"
- 上下文管理怎么做？长期记忆怎么设计？Subagent怎么配合？
- 提出评测方法，构建基准数据，从Harness角度优化Agent智能水平
- **任职要求极高**：2年以上科研经验、CS领域论文发表、AI Agent高强度用户

**工程师**：负责"实现能力"
- 参与技术架构与选型，开发Harness产品
- 与研究员配合，保证系统能跑、能迭代、能服务真实用户

**产品经理**：负责"连接"
- 连接研究员、工程师、开源社区和用户
- 定义产品方向，管理社区反馈

这三个岗位构成了一条完整的Agent基础设施研发链——**研究→工程→产品→社区**。

### 3. 人才战背后：AI竞争进入下半场

> "大模型上半场，大家抢的是研究员。下半场，Agent阶段，需要能把研究、工程、产品、用户需求揉到一块的复合型团队。"

DeepSeek的招聘公告暴露了一个行业级问题：
- **会用模型的人很多，能驯马（做Harness）的人很稀缺**
- Agent人才需要的不是单一技能，而是"研究品味+工程能力+产品思维"的复合能力
- 崔添翼连招了一个多月也没招够，说明这类人才供给严重不足

**更重要的背景**：郭达雅的出走并非孤立事件。过去一年中，DeepSeek已有至少5名核心研究员离职——王炳宣（基座模型，去腾讯）、罗福莉（V3核心，去小米）、魏浩然（OCR系列，去向未公开）、阮翀（多模态，去元戎启行）、郭达雅（代码智能/推理，去字节）。五个人覆盖了基座模型、推理、OCR、多模态四条核心技术主线。而郭达雅因Agent方向优先级不够出走、DeepSeek随后紧急组建Harness团队全力押注——这个转折本身就构成了一则行业寓言：**顶级人才的方向判断跑在了公司战略前面。**

### 4. 竞争格局：DeepSeek的Agent战略是不是晚了？

2026年6月第三周，全球Agent产品单周爆发48条，基础设施军备竞赛全面打响：

- **Claude Code / Anthropic**：Claude Code已进入"loop engineering"阶段，工程团队每季度产出是此前的8倍，持续快速迭代
- **OpenAI**：Codex已开放第三方模型接入，国产模型可通过兼容接口直连
- **Google Cloud**：Agent Sandbox + Agent Substrate + Agent Executor 三层架构，每秒300沙箱
- **Microsoft Azure**：Serverless Agents Runtime，`.agent.md`定义部署
- **微信**：小微Agent已灰度上线（2026年6月20日起），14.32亿用户基数，由微信自研WeLM驱动（部分调用DeepSeek）
- **蚂蚁**：AMP协议已开源（2026年4月），全球首个专为移动端设计的Agent支付框架，覆盖18亿Alipay+用户账户

DeepSeek的优势：开源模型社区影响力、技术品牌、对Agent基础设施的深度理解。
DeepSeek的风险：核心人才持续流失、Harness团队起步偏晚（竞品已产品化数年）、产品化能力待验证。

---

## 创作方向建议

### 主角度：AI人才战争的下半场——从"谁能训练最大模型"到"谁能驯服最好的Agent"

以DeepSeek招聘为切入点，分析AI行业人才需求的结构性变化：
- **双线叙事**：DeepSeek个例（郭达雅出走→紧急组建Harness→崔添翼招不到人）→ 行业全局（全球单周48条Agent产品新闻、各大厂Agent基础设施密集发布、小米/华为/快手一周开源三件套）→ 回到DeepSeek的Harness公式
- 核心论点：大模型时代竞争主体是"谁能训练最大模型"→只需要顶尖研究员；Agent时代需要"研究品味+工程能力+产品思维"的复合型团队→这类人全球稀缺
- 结合吴恩达"1-10人精英小队"观点，讨论AI时代什么样的人最值钱

### 备用角度

- **角度二**：DeepSeek的Agent野心——Model + Harness = Agent 公式能否成为行业标准？
- **角度三**：出走与回归——DeepSeek人才流动折射的中国AI竞争

---

## 可回溯来源

1. **SCMP**：DeepSeek's Harness team races to recruit talent in booming AI agent market（2026.06.23）
   https://www.scmp.com/tech/big-tech/article/3358077/

2. **SCMP**：DeepSeek recruits former Jane Street engineer to catch up on AI agents, revenue race（2026.05.19）
   https://www.scmp.com/tech/big-tech/article/3354113/

3. **晚点LatePost**：DeepSeek 95后研究员郭达雅近亿元年薪入职字节（2026.04.16）
   https://finance.sina.com.cn/wm/2026-04-16/doc-inhuszrw2763097.shtml

4. **36氪**：DeepSeek缺Agent人才缺疯了，负责人各种贴广告
   https://www.36kr.com/p/3863982620923141

5. **Digg**：DeepSeek AI Agent Harness Team Hiring
   https://digg.com/tech/u87bzwhz

6. **PANews**：Everything Beyond the Model Is Harness: DeepSeek Enters the Fray
   https://www.panewslab.com/en/articles/019eede8-f90e-746d-929c-82a7c608db11

7. **PCNow**：DeepSeek第一批核心研究员相继离职（2026.04.21）
   https://pcnow.cc/p/3zZp57b693.html

8. **Fortune**：Anthropic engineering leader says Claude Code made employees' work a 'lonely experience'（2026.06.23）

9. **IT之家**：微信AI助手"小微"灰度上线（2026.06.20）
   https://www.ithome.com/0/966/534.htm

10. **BusinessWire**：Ant International Launches Open-Sourced Agentic Mobile Protocol（2026.04.28）

11. **崔添翼X账号**：招聘原始信息
    https://x.com/tianyi/status/2068652453797724562

12. **DeepSeek招聘链接**：
    - Harness研究员：https://app.mokahr.com/su/mCyA8
    - Harness工程师：https://app.mokahr.com/su/JNKdF
    - Harness产品经理：https://app.mokahr.com/su/1RZuJ
