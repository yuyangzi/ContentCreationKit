# PPT 设计文档

## 基本信息

- **文章**: DeepSeek 招不到人——AI人才战争进入下半场
- **主题**: 战略分析型 — DeepSeek 从大模型到 Agent 的战略转向
- **目标观众**: 泛科技爱好者 + 技术人员（混合）
- **幻灯片数量**: 15 张
- **动画策略**: 淡入（仅 fade-up 入场；允许章节徽章和对比数字的 data-count 计数动画——不影响核心视觉稳定性）
- **色彩主题**: 科技蓝紫（默认配色）
- **比例**: 16:9（1920×1080）

## 叙事结构

四章递进：

| 章节 | 叙事功能 | 页数 |
|------|----------|------|
| 引子 | 抛出问题："缺人缺疯了" | 1-2 |
| 第一章 · 郭达雅出走 | 因果链：人走 → 才组建 | 3-6 |
| 第二章 · 模型 vs Harness | 核心比喻：产业转型 | 7-9 |
| 第三章 · 竞争格局 | 外部压力：每周48条 | 10-12 |
| 第四章 · 人才转型 | 内部困境：招不到人 | 13-15 |

## 幻灯片结构

### Slide 1 — Cover
- **type**: `cover`
- **visual**: `hero-split`
- **title**: "DeepSeek 招不到人"
- **subtitle**: "AI 人才战争进入下半场"
- **eyebrow**: "战略分析"
- **data.before**: {value: 50, label: "个开放岗位（BOSS直聘）"}
- **data.after**: ["研究员", "工程师", "产品经理"]

### Slide 2 — 开场钩子
- **type**: `quote`
- **visual**: `quote-center`
- **data.quote**: "每天都在面试，缺人缺疯了。"
- **data.source**: "崔添翼 · 前 Jane Street 量化工程师 / ACM ICPC 6 次金牌 / DeepSeek Harness 负责人"

### Slide 3 — 章节分隔
- **type**: `section`
- **visual**: `chapter`
- **badge**: 1
- **data.color**: "orange"
- **title**: "郭达雅出走，Harness 才来"

### Slide 4 — 时间轴（关键事件）
- **type**: `process`
- **visual**: `timeline`
- **title**: "从出走 to 组建"
- **data.events**: [
    {date: "2025.10", title: "郭达雅决定离职", description: "GRPO 算法发明人，DeepSeek-Coder/V3/R1 核心贡献者", color: "red"},
    {date: "2026.03", title: "郭达雅加入字节，崔添翼加入 DeepSeek", description: "郭达雅加入字节 Seed 任 Agent 方向负责人；前 Jane Street 量化工程师崔添翼（ACM ICPC 6 次金牌）加入", color: "orange"},
    {date: "2026.05", title: "Harness 团队组建", description: "从零构建 CodeHarness，内部对标 Claude Code", color: "green"}
  ]

### Slide 5 — 核心研究员流失
- **type**: `data`
- **visual**: `metric-cards`
- **title**: "5 名核心研究员先后离职"
- **data.cards**: [
    {badge: "①", color: "red", title: "王炳宣", description: "基座模型核心 · 去腾讯混元"},
    {badge: "②", color: "red", title: "罗福莉", description: "V3 核心 · 传千万年薪去小米"},
    {badge: "③", color: "red", title: "魏浩然", description: "OCR 系列核心 · 去向未公开"},
    {badge: "④", color: "red", title: "阮翀", description: "多模态核心 · 去元戎启行"},
    {badge: "⑤", color: "orange", title: "郭达雅", description: "代码/推理核心 · 去字节 Seed"}
  ]
- **callout**: "150 人团队，覆盖 4 条核心技术线"

### Slide 6 — 判断走在公司前面
- **type**: `compare`
- **visual**: `before-after-cards`
- **title**: "一个人的判断力"
- **data.before**: {label: "郭达雅想做 Agent", value: "2023年", description: "方向判断走在公司前面"}
- **data.after**: {label: "DeepSeek 紧急转向", code: "2026.05", description: "郭走后 7 个月，Harness 才组建"}
- **data.banner**: "顺序是反过来的——人走了，才追。"

### Slide 7 — 章节分隔
- **type**: `section`
- **visual**: `chapter`
- **badge**: 2
- **data.color**: "orange"
- **title**: "模型是发动机，Harness 才是整车"

### Slide 8 — 核心公式
- **type**: `compare`
- **visual**: `before-after-cards`
- **title**: "Model + Harness = Agent"
- **data.before**: {label: "大模型时代", value: 2023, description: "训练更大的模型，API 就是产品"}
- **data.after**: {label: "Agent 时代", code: "拼 Harness", description: "模型之外的所有基础设施"}
- **data.banner**: "发动机 vs 整车：不是同一个工程体系"

### Slide 9 — Harness 六大组件
- **type**: `data`
- **visual**: `metric-cards`
- **title**: "Harness 覆盖什么？"
- **data.cards**: [
    {badge: "1", color: "blue", title: "上下文管理", description: "会话状态与记忆"},
    {badge: "2", color: "purple", title: "长期记忆", description: "跨会话持久化"},
    {badge: "3", color: "cyan", title: "Subagent 协同", description: "Multi-Agent 编排"},
    {badge: "4", color: "green", title: "自进化 Agent", description: "自我迭代机制"},
    {badge: "5", color: "orange", title: "工具调用与规划", description: "Function Calling"},
    {badge: "6", color: "blue", title: "MCP 协议集成", description: "标准化接口层"}
  ]

### Slide 10 — 章节分隔
- **type**: `section`
- **visual**: `chapter`
- **badge**: 3
- **data.color**: "orange"
- **title**: "48 条新闻，一个人都招不到"

### Slide 11 — 行业关键数据
- **type**: `data`
- **visual**: `metric-cards`
- **title**: "外面的世界"
- **data.cards**: [
    {badge: "48", color: "orange", title: "条/周", description: "Agent 产品/研究/融资新闻数"},
    {badge: "8×", color: "green", title: "工程师产出", description: "Claude Code 团队人均季度产出"},
    {badge: "470", color: "green", title: "亿美元年化营收", description: "Anthropic 5 个月从 90 亿→470亿"},
    {badge: "25", color: "blue", title: "亿美元", description: "Claude Code 单品年化营收"},
    {badge: "14.32", color: "purple", title: "亿月活", description: "微信小微灰度上线"},
    {badge: "Open", color: "orange", title: "Codex 开放接入", description: "第三方模型直连，国产兼容"}
  ]

### Slide 12 — 国内 Agent 三赛道
- **type**: `compare`
- **visual**: `three-column-flow`
- **title**: "国内三条赛道已开跑"
- **data.left**: {title: "消费级 Agent", items: ["微信小微 6.20 灰度上线", "14.32 亿月活用户", "最广泛消费触点"]}
- **data.center**: {title: "金融 Agent", items: ["蚂蚁国际开源 AMP", "全球首个移动端", "Agent 支付框架"]}
- **data.right**: {title: "开发工具", items: ["小米 MiMo Code 开源", "MIT 协议", "AI 编程工具赛道"]}
- **data.banner**: "三条赛道，没有一条在等 DeepSeek"

### Slide 13 — 章节分隔
- **type**: `section`
- **visual**: `chapter`
- **badge**: 4
- **data.color**: "orange"
- **title**: "抢的是知道要做什么的人"

### Slide 14 — 三种稀缺能力
- **type**: `data`
- **visual**: `metric-cards`
- **title**: "崔添翼为什么招不到人？"
- **data.cards**: [
    {badge: "🧠", color: "purple", title: "研究品味", description: "知道什么问题值得解决"},
    {badge: "🔧", color: "cyan", title: "工程能力", description: "实现到生产级别"},
    {badge: "🎯", color: "orange", title: "产品思维", description: "理解用户到底要什么"}
  ]
- **callout**: "这三种能力在同一个人身上同时出现——极度稀缺"

### Slide 15 — 总结
- **type**: `summary`
- **visual**: `summary-list`
- **title**: "不是谁会训练，是谁能驯服"
- **data.items**: [
    "大模型时代抢研究员 → Agent 时代抢能『驯马』的人",
    "Agent = Model + Harness，Harness 才是真正的壁垒",
    "郭达雅的判断走在了公司前面——他离开的理由变成了公司的方向",
    "一周 48 条新闻，Claude Code 已经自己写了 7 个月代码",
    "全员 Agent 写代码——人际协作反而变少了，效率的副作用",
    "这不是有钱就能快起来的事"
  ]

## 配色策略

沿用默认科技蓝紫主题：
- 背景: `#07111f`（深空蓝黑）
- 面板: `rgba(20, 26, 42, 0.85)` 半透明
- 强调色: `#ff9d3d`（橙色——标题/中性强调）
- 红色: 负面/流失/警告（离职研究员用）
- 绿色: 正面/增长（Anthropic 数据用）
- 紫色: 概念/能力（Harness 组件/稀缺能力用）
- 蓝色: 信息/路径（常规内容用）
- 青色: 系统/能力/技术术语（Subagent 协同、工程能力用）

## 来源标注

每页 footer 标注来源，主要参考：
- SCMP, 晚点LatePost, 36氪, Fortune, IT之家
