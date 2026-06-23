---
theme: '@enyineer/slidev-theme-neocarbon'
title: 'AI压缩了执行力，放大了判断力'
info: |
  ## 数据来源
  Anthropic · Dallas Fed · KPMG/墨尔本大学 · 澎湃新闻 · Soul研究院 · 虎嗅
highlighter: shiki
transition: fade
fonts:
  sans: 'PingFang SC, Microsoft YaHei, sans-serif'
  serif: 'Noto Serif SC, serif'
  mono: 'Monaspace Neon, Fira Code, monospace'
---

<style>
:root {
  --nc-accent:  #ff6b35;
  --nc-success: #22c55e;
  --nc-danger:  #ef4444;
  --nc-warning: #f59e0b;
  --nc-info:    #3b82f6;
}
svg text { font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important; }

/* 录屏模式：隐藏导航和侧边栏 */
.slidev-sidebar, .slidev-nav, .slidev-slide-nav,
.slidev-navigation, .slidev-toc, .slidev-overview-panel,
aside, nav.slidev-nav,
[class*="sidebar"], [class*="toc"], [class*="navigation"],
#slidev-nav, .slidev-layout-nav,
.slidev-v-click-hidden { display: none !important; }

/* 只保留翻页按钮，但不遮挡内容 */
.slidev-layout { z-index: 1; }
</style>

# ============================
# 封面
# ============================

---
layout: cover
---

# AI压缩了执行力，放大了判断力

为什么会用AI的人越来越值钱，不会用的人越来越焦虑

<span class="nc-text-muted">数据来源：Anthropic 2026.6 · Dallas Fed · KPMG</span>

---
layout: statement
---

# 执行力↓　判断力↑

<span class="nc-text-muted">23.5万人 · 40万次真实会话 · 7个月追踪</span>

# ============================
# 第一章 · 执行层的差距正在消失
# ============================

---
layout: section
---

# 第一章 · 执行层的差距正在消失

---
layout: quote
---

> 一个从没写过Python的会计，用Claude写对账脚本，成功率跟程序员差不多。

— Anthropic 分析 40 万次真实会话

---
layout: default
---

# 部分成功率：几乎一样

<NcBarChart
  title="「至少部分成功」会话占比"
  :labels="['软件工程师', '其他职业']"
  :data="[89, 88]"
  :colors="['var(--nc-success)', 'var(--nc-accent)']"
  height="280"
/>

<span class="nc-text-muted">差距仅 1%——执行层的差异正在被压平</span>

---
layout: default
---

# 严格成功率：差距拉大

<NcBarChart
  title="严格验证成功会话占比"
  :labels="['新手', '中级', '高级']"
  :data="[15, 28, 33]"
  :colors="['var(--nc-danger)', 'var(--nc-accent)', 'var(--nc-accent)']"
  height="280"
/>

<span class="nc-text-muted">*"the gains come mostly from competence, not mastery"* — Anthropic</span>

---
layout: metrics
---

::metrics::
<div class="nc-metric">
  <span class="nc-metric-value nc-text-danger">19%</span>
  <span class="nc-metric-label">新手遇到问题直接放弃</span>
</div>
<div class="nc-metric">
  <span class="nc-metric-value nc-text-success">5-7%</span>
  <span class="nc-metric-label">专家放弃率</span>
</div>
<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">4%</span>
  <span class="nc-metric-label">新手翻盘概率</span>
</div>
<div class="nc-metric">
  <span class="nc-metric-value nc-text-success">15%</span>
  <span class="nc-metric-label">专家翻盘概率</span>
</div>

---
layout: diagram
---

::left::
#### 差距不在"会不会写代码"

在"碰到问题后能不能搞定"

- AI让本来就知道自己要什么的人变得极强
- 让不知道自己在做什么的人更快地撞墙

::right::
```mermaid
graph TD
  A["AI报错 / 输出不对"] --> B{"新手"}
  A --> C{"专家"}
  B --> D["放弃 19%"]
  B -.-> E["翻盘 4%"]
  C --> F["放弃 5-7%"]
  C --> G["翻盘 15%"]

  style D fill:#ef4444,color:#fff
  style G fill:#22c55e,color:#fff
```

# ============================
# 第二章 · 同一句话，不同价格
# ============================

---
layout: section
---

# 第二章 · 同一句话，不同价格

---
layout: quote
---

> 同一个AI，对不同的人"努力程度"不一样。

— 因为指令质量

---
layout: comparison
---

::left::
### 新手
每指令 **5** 个动作
输出 **600** 词

模糊指令 · 无验收标准 · 跑两步就撞墙

::right::
### <span class="nc-text-success">专家</span>
每指令 **12** 个动作
输出 **3,200** 词

<span class="nc-text-success">精确指令 · 约束清楚 · 知道什么算"对了"</span>

动作链 <span class="nc-text-accent">2x</span>　输出量 <span class="nc-text-accent">5x</span>

---
layout: comparison
---

::left::
### 新手一条指令
<span style="font-size:2.5em">600</span> 词

"你帮我写个对账脚本"

::right::
### <span class="nc-text-success">专家一条指令</span>
<span class="nc-text-success" style="font-size:2.5em">3,200</span> 词

"这个脚本要处理三种异常情况，金额字段是 string 类型要先转，输出格式要跟财务系统对齐——你先读一下现有的 CSV 结构再动手"

---
layout: statement
---

> "People decide what to build, and the agent decides how to build it."

— Anthropic

---
layout: comparison
---

::left::
### 新手：人帮AI干活
"帮我写个对账脚本"

<span class="nc-text-muted">模糊 → 跑两步就撞墙</span>

::right::
### <span class="nc-text-success">专家：AI帮人干活</span>
"处理三种异常，金额转 string，对齐财务系统格式"

<span class="nc-text-success">精确 → 跑得又快又远</span>

# ============================
# 第三章 · 梯子正在被抽掉
# ============================

---
layout: section
---

# 第三章 · 梯子正在被抽掉

---
layout: quote
---

> 传统白领成长路径：毕业做执行——写周报、做PPT、跑数据——三五年后开始独立做判断。

问题在于：AI正在让那些"边干边学"的入门岗位变得不经济。

---
layout: comparison
---

::left::
### <span class="nc-text-danger">被替代</span>
<span style="font-size:2em">可编码的知识</span>

手册 · 模板 · 流程
能被写成文字的东西

AI 正在快速吃掉

::right::
### <span class="nc-text-success">被放大</span>
<span class="nc-text-success" style="font-size:2em">默会知识</span>

靠经验积累 · 说不清楚但会用
"见过足够多烂摊子才知道怎么办"

Dallas Fed 2026.2

---
layout: quote
---

> Firms are going to find that AI is making this method of employee development cost-ineffective, at least in the short run.

— Dallas Fed

---
layout: default
---

# AI协作模式正在迁移

<NcLineChart
  title="会话类型占比变化（7个月）"
  :labels="['Oct', 'Nov', 'Dec', 'Jan', 'Feb', 'Mar', 'Apr']"
  :datasets="[
    { label: '修复代码', data: [33, 30, 27, 25, 22, 20, 19], color: 'var(--nc-danger)' },
    { label: '写新代码', data: [10, 12, 14, 16, 18, 19, 20], color: 'var(--nc-success)' },
    { label: '数据分析', data: [10, 11, 13, 15, 17, 19, 20], color: 'var(--nc-accent)' },
  ]"
/>

<span class="nc-text-muted">从"帮我改bug" → "帮我从头完成一件事"</span>

# ============================
# 第四章 · 焦虑不是来自未知，来自已知
# ============================

---
layout: section
---

# 第四章 · 焦虑不是来自未知，来自已知

---
layout: quote
---

> 一边疯狂用AI，一边疯狂焦虑。

这不是悖论，这是同一件事的两面。

---
layout: default
---

# 中国AI使用率全球领先

<NcBarChart
  title="职场AI应用率"
  :labels="['中国', '全球平均']"
  :data="[93, 58]"
  :colors="['var(--nc-accent)', '#6b7280']"
  height="280"
/>

<span class="nc-text-muted">KPMG/墨尔本大学 · 47个国家 · 约4.8万人 · 2025</span>

---
layout: metrics
---

::metrics::
<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">40%</span>
  <span class="nc-metric-label">年轻人有AI焦虑</span>
</div>
<div class="nc-metric">
  <span class="nc-metric-value nc-text-danger">59%</span>
  <span class="nc-metric-label">担心被替代</span>
</div>
<div class="nc-metric">
  <span class="nc-metric-value nc-text-success">93%</span>
  <span class="nc-metric-label">却还在疯狂使用</span>
</div>

---
layout: quote
---

> 越了解AI，人越焦虑。不是因为怕工具太强，是因为工具让那些曾经看起来"我也能做"的工作变得透明了——你清楚地看见了自己到底在哪个环节创造价值。

<br>

**案例**：广告公司策略总监，团队裁了1/3。客户直接拿AI方案来确认方向——他只需要说"行"或"不行"。工作量没变少，对判断力要求更高了。

# ============================
# 第五章 · 判断力会不会也被压缩？
# ============================

---
layout: section
---

# 第五章 · 判断力会不会也被压缩？

---
layout: quote
---

> 那万一AI把判断力也学会了呢？

这个担忧需要分层。

---
layout: comparison
---

::left::
### <span class="nc-text-accent">执行判断</span>
"这段代码性能够不够"
"这个清洗步骤对不对"

基于规则和可验证的标准

目前 <span class="nc-text-accent">70%</span> 的规划决策仍由人做出
但这一比例正在下降

<span class="nc-text-muted">AI正在快速逼近</span>

::right::
### <span class="nc-text-success">价值判断</span>
"这个功能值不值得做"
"决策错了最坏结果能不能承担"

基于经验、直觉、对业务的理解
无数具体场景里熬出来的直觉

<span class="nc-text-success">只有时间能磨</span>

---
layout: statement
---

# 你可以让AI写一千个方案

# 但最后拍板说"就用这个"的是人

<span class="nc-text-muted">签字的那个、担责任的那个、出了问题被叫进办公室的那个</span>

# ============================
# 结尾
# ============================

---
layout: quote
---

> Coding agents are not substituting for domain expertise—the more understanding a worker brings to an agent, the more quality work the agent is able to do.

— Anthropic

---
layout: statement
---

# 如果你的工作能被AI做完

# 有哪个决定你仍然不敢交给它？

<span class="nc-text-success">那个不敢交付的瞬间，至少目前来看，还是你守得住的东西</span>

---
layout: default
---

# 数据来源

1. **Anthropic** — Agentic coding and persistent returns to expertise (2026-06-16)
2. **Dallas Fed** — AI is simultaneously aiding and replacing workers (2026-02-24)
3. **KPMG/墨尔本大学** — Trust, attitudes and use of AI: Global study (2025)
4. **澎湃新闻·对齐Lab** — 2025年人工智能公众态度追踪调查报告
5. **Soul研究院** — 2025 Z世代AI使用报告 (2025-04)
6. **虎嗅** — 中国人的AI焦虑，又领先了 (2026-05-08)