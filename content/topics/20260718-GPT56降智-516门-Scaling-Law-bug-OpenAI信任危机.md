# 从GPT-5.6降智到516门到Scaling Law bug：OpenAI的信任危机从产品蔓延到理论

## 热度背景

2026年7月初，OpenAI遭遇双重信任危机：

**事件一：GPT-5.5被曝"暗中降智"**。用户发现模型思考到第516个token时突然中断，越困难的问题越容易触发。用户质疑OpenAI是否在"暗中降智"以控制推理成本。这种"思考到一半就断"的行为模式，让付费用户感到被欺骗。

**事件二：Scaling Law原始论文曝出严重缺陷**。据报道，支撑过去数年AI大模型军备竞赛的理论基石——Scaling Law的原始论文存在关键bug。如果该论文确实存在方法论上的根本缺陷，意味着行业在"越大越好"的路线上投入的数万亿算力可能部分"白烧"了。

两件事叠加在同一周发生——从产品体验到理论根基，OpenAI的核心叙事遭受罕见质疑。

## 类型标签

- 行业事件
- 技术争议
- 大模型

## 创作方向建议

1. **技术解剖**：GPT-5.5"516限制"是巧合还是有意设计？推理成本控制与用户体验的博弈
2. **深层追问**：Scaling Law如果真的存在bug，对AI行业意味着什么？还有哪些"先验假设"我们从未认真质疑过？
3. **行业影响**：如果Scaling Law崩溃，那些押注Scaling的公司（OpenAI、Google、Anthropic）将如何调整策略？
4. **商业模式**：当"智力"成为可动态调节的云资源，订阅模型的用户付费购买的到底是什么？"灯泡隐喻"——型号固定，亮度旋钮握在平台手里

## 来源链接

- 36Kr - 新智元：《GPT-5.5突遭暗中降智，思考一到516就断，越难越翻车》https://www.36kr.com/p/3883304315891717
- 36Kr - 新智元：《OpenAI塌房，Scaling law原作曝bug，万亿算力全白烧》https://www.36kr.com/p/3883301202440198
- GitHub Issue #30364（516现象原始分析）：https://github.com/openai/codex/issues/30364
- Diogo Almeida 博文（Scaling Law bug一手来源）：https://www.completeskeptic.com/p/scaling-laws-honestly
- Tibo Sottiaux 回应（X/Twitter）：https://x.com/thsottiaux/status/2076495156757577895
- 知乎热议

## 2026-07-15 更新

**GPT-5.6 Sol"降智"争议再起**。7月9日GPT-5.6发布后，Max推理档位一度带来"远超预期的怪物"级表现，但仅一周后用户集体发现模型"变笨"——推理深度被剥掉，模型不再肯往深里挖。

社区用户通过"模型指纹"技术发现，OpenAI内部从未公开的推理预算参数"juice value"被从960砍到128（降幅87%），同时上下文窗口从372k退回272k。OpenAI Codex负责人Tibo回应称"没有降智，只是实验"，团队在调查用量增长原因时临时调整了推理强度，现已恢复。

但争议核心不在于"是否恢复"，而在于：**AI模型从此没有"固定智力"了**。订阅一个模型，更像是买了一只灯泡——型号固定，但亮度旋钮一直握在平台手里。juice value这个参数，决定了模型愿意在一个任务上花多少心思，而用户完全看不见。

这是GPT-5.5"516限制"事件的延续与升级——从"思考到一半就断"到"平台可以随时调整你的推理预算"，OpenAI的信任危机从产品体验蔓延到了商业模式底层。

**来源**：36Kr - 新智元：《GPT-5.6 Sol一夜变笨，思考预算960砍到128，没智力固定的模型了？》https://www.36kr.com/p/3896320634685318

## 2026-07-18 更新

### 大空头万字檄文 + Brockman 集权 + IPO 倒计时：OpenAI 的多重风暴

7月中旬，OpenAI的信任危机从产品层面蔓延到金融层面，三条线索同时指向同一个问题：这家公司值$8520亿吗？

**线索一：大空头发表1.5万字长文，标题直指"OpenAI必将崩溃"**

36氪头条报道，一位知名做空者发表万字长文，系统性论证OpenAI商业模式不可持续。核心论点包括：ChatGPT市场份额首次跌破50%（Sensor Tower数据）、企业客户续费率下滑、推理成本居高不下。文章引发全球股市讨论——"AI泡沫论"找到了最具体的靶标。

**线索二：Brockman 全面集权，IPO 压力下的组织收缩**

Fidji Simo（产品与商业负责人）因慢性病（POTS）于7月10日退出。Greg Brockman（OpenAI联合创始人兼总裁）接管了ChatGPT产品、企业团队、市场拓展和算力运营——基本掌控了公司除研究外的全部业务线。OpenAI已于6月8日秘密提交IPO申请，估值$8520亿。但在市场份额跌破50%、信任危机持续发酵的背景下，这个估值面临严峻考验。

**线索三：信任危机的"三级跳"**

回顾过去一个月：GPT-5.5"516限制"（产品体验降级）→ GPT-5.6 juice value从960砍到128（推理预算暗调）→ Scaling Law论文被曝bug（理论根基动摇）。现在加上了大空头做空和IPO前夕的权力集中——OpenAI的信任危机正在从产品、理论、金融三个层面同时加压。

**来源**：
- [36氪："OpenAI必将崩溃，全球股市恐遭清算"，大空头1.5万字长文引争论](https://www.36kr.com/p/3899383821305476)
- [CNBC: OpenAI power consolidates under co-founder Greg Brockman ahead of IPO](https://www.cnbc.com/2026/07/10/openai-power-consolidates-under-co-founder-greg-brockman-ahead-of-ipo.html)
- [Seeking Alpha: OpenAI's Greg Brockman steps out of the shadows as IPO nears](https://seekingalpha.com/news/4598693-openai-s-greg-brockman-steps-out-of-the-shadows-as-ipo-nears)
