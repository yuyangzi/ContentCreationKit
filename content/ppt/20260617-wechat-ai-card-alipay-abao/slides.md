---
theme: '@enyineer/slidev-theme-neocarbon'
title: '微信AI专属卡、支付宝阿宝与超级App的Agent化'
info: |
  ## 一场2023年就已开始的"主动换芯"
  数据来源：新浪科技/财联社/晚点LatePost/IT之家/智东西/经济观察报/36氪/虎嗅/QuestMobile/AppGrowing 等14个来源
highlighter: shiki
transition: fade
export:
  withToc: false
fonts:
  sans: 'PingFang SC, Microsoft YaHei, Noto Sans SC'
  serif: 'Noto Serif SC, serif'
  mono: 'Fira Code, monospace'
  provider: none
---

---
layout: cover
---

# 微信AI专属卡、支付宝阿宝与超级App的Agent化

一场2023年就已开始的"主动换芯"

<div class="nc-text-muted" style="margin-top: 1rem;">
2026年6月 · 超级App Agent化深度分析
</div>

---
layout: quote
---

> 媒体把这两件事并称为"反击豆包"。但我把过去三年的时间线摊开比对之后，得到的判断完全相反。

— 这不是反击，是换芯

---
layout: section
---

# 第一章
## 三年前那场没被注意的会议

---
layout: default
---

# 2023年 · 三家AI战略启动

```mermaid
timeline
    title 2023年 AI 战略启动时间线
    4月 : 阿里云峰会<br>发布通义千问
    5月 : 马化腾"几百年不遇<br>的工业革命"
    下半年 : 支付宝内部会议<br>"如何走向智能化"
```

<div class="nc-text-muted" style="text-align:center; margin-top: 1rem;">
同一时间段：豆包刚刚公测，DAU破亿还要再等两年多
</div>

---
layout: statement
---

# 腾讯和阿里对AI的投入与转型，<br>早就已经开始。

产品是预先架构好的，到时间点拿出来而已。

---
layout: section
---

# 第二章
## 微信AI专属卡：先搭架构，再出产品

---
layout: default
---

# AI专属卡四大产品特征

<NcSteps
  :steps="[
    { title: '子账户完全隔离', status: 'done' },
    { title: '充多少花多少·无默认限额', status: 'done' },
    { title: '三道安全机制·笔笔确认', status: 'done' },
    { title: '随时暂停·提现回零钱', status: 'done' },
  ]"
/>

<div class="nc-text-muted" style="text-align:center; margin-top: 1.5rem;">
来源：微信支付官方发布稿 · 新浪科技 · 财联社
</div>

---
layout: comparison
---

::left::

## 简单做法

直接授权AI调主账户

设个限额就完事

<br>

*"跟上AI时代"*

::right::

## 微信做法

另开一张专属卡

单独充钱 · 单独管理

专门发给AI智能体用

<br>

*"专款专用，笔笔确认"*

---
layout: default
---

# 安全机制三层架构

```mermaid
graph TD
    A[🔒 微信支付主账户] -->|"完全隔离<br>类比亲属卡模式"| B[💳 AI专属卡子账户]
    B --> C[💰 余额自主控制<br>充多少花多少]
    C --> D[✅ 每笔支付确认<br>用户本人授权]
    D --> E[⏸️ 随时暂停/提现]

    style A fill:#a855f7,stroke:#7e22ce,color:#fff
    style B fill:#22d3ee,stroke:#0891b2,color:#000
    style C fill:#818cf8,stroke:#4f46e5,color:#fff
    style D fill:#22d3ee,stroke:#0891b2,color:#000
    style E fill:#a855f7,stroke:#7e22ce,color:#fff
```

---
layout: statement
---

# 微信在给AI划一块"保留地"。

保留地里AI可以跑、可以花钱、可以代用户决策；

保留地外，主账户不动、人格不让、关系链不开放。

---
layout: section
---

# 第三章
## 支付宝阿宝：把"管钱"明确踢出AI范围

---
layout: comparison
---

::left::

## 🗣️ 阿宝 Tab

对话助手

调用上万种服务

叫车 · 外卖 · 酒店 · 挂号

*可发起支付，需本人确认*

::right::

## 📊 资产 Tab

独立账本

用户完全掌控

"管钱不交给AI"

*阿宝只做"哨兵"角色*

---
layout: quote
---

> "管钱"这件事，支付宝没有交给AI，而是用一个独立的"资产"页面呈现给用户。

— 上证报中国证券网 实测报道

---
layout: default
---

# 双重动机：为什么边界做得这么死

<div class="grid grid-cols-2 gap-8" style="margin-top: 2rem;">

<div>

### 🛡️ 合规压力

支付宝在监管视野里的分量比微信支付还要重

资金管理权一旦交给AI模型决策，整个金融监管框架都要重新对齐

</div>

<div>

### 🏦 品牌承诺

二十年"放心存钱"心智是真正的护城河

不能为了追AI风口动摇这块根基

> "你敢付，我敢赔" — 蚂蚁支付宝事业群总裁 李俊

</div>

</div>

---
layout: section
---

# 第四章
## 小程序变Skill：协议层的预谋

---
layout: default
---

# 五条技术限制 · 逼开发者拆成能力单元

<NcSteps
  :steps="[
    { title: 'SKILL分包 independent:true · 最多30个', status: 'done' },
    { title: 'mcp.json 声明Schema · ≤24KB', status: 'done' },
    { title: 'SKILL.md 业务流程 · ≤16KB', status: 'done' },
    { title: '原子接口函数 · 隔离环境运行', status: 'done' },
    { title: '原子组件卡片渲染 · 不能滚动', status: 'done' },
  ]"
/>

<div class="nc-text-muted" style="text-align:center; margin-top: 1rem;">
来源：微信开放文档
</div>

---
layout: quote
---

> 文字链引回原页面，被定义为"兜底手段，用多了会降权"。

— 微信开放文档（翻译版）

<span class="nc-text-muted" style="display:block; margin-top:1rem;">微信主动把服务闭环留在AI对话里</span>

---
layout: comparison
---

::left::

## 小程序时代

开发者做产品

用户搜索 → 找到打开使用

靠留存和广告变现

**人找服务 · 品牌可见**

::right::

## Skill 时代

开发者供能力

用户说话 → AI调Skill

品牌在用户端彻底消失

**AI安排服务 · 只剩接口**

---
layout: statement
---

# 微信主动把服务闭环留在AI对话里。

开发者从"做产品的人"变成"提供能力的供应商"。

---
layout: section
---

# 第五章
## 三方卡位战：各有底牌，各有短板

---
layout: default
---

# 三方AI助手 MAU 对比

<NcBarChart
  title="MAU 对比（百万）"
  :labels="['豆包 3.45亿', '千问 1.66亿', '元宝 5735万']"
  :data="[345, 166, 57.35]"
  :colors="['var(--nc-success)', 'var(--nc-accent)', 'var(--nc-accent)']"
  height="300"
/>

<div class="nc-text-muted" style="text-align:center; margin-top: 12px;">
数据来源：公开数据 / QuestMobile 2026.03
</div>

---
layout: default
---

# 三家优劣势矩阵

<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 2rem; margin-top: 2rem;">

<div>

### <span style="color: var(--nc-success)">字节豆包</span>

**优势**<br>
流量最强<br>
MAU 3.45亿 · DAU破亿<br>
2025投流约4.35亿

**短板**<br>
缺支付<br>
缺社交关系链<br>
被主流App限制

</div>

<div>

### <span style="color: var(--nc-accent)">阿里千问</span>

**优势**<br>
生态执行力最强<br>
支付宝·淘宝·高德·飞猪<br>
ACT协议已在跑

**短板**<br>
MAU 1.66亿<br>
约豆包一半

</div>

<div>

### <span style="color: var(--nc-accent)">腾讯微信</span>

**优势**<br>
社交关系链最强<br>
微信合并MAU 14.32亿<br>
Skill私有协议

**短板**<br>
元宝MAU 5735万<br>
距豆包约6倍差距

</div>

</div>

---
layout: comparison
---

::left::

## 过去：人找服务

用户搜App打开用

开发者靠留存和广告变现

流量分配规则决定一切

**人在前面，AI在后台**

::right::

## 现在：AI安排服务

用户说话，AI调Skill

开发者失去"被用户主动选中"的环节

流量从人找服务变成AI安排服务

**AI在前面，人在后面**

---
layout: default
---

# 三方战略路径对比

```mermaid
graph LR
    subgraph 字节
    A1[豆包<br>MAU 3.45亿] -->|攻方| A2[打通抖音商城<br>生活服务闭环]
    end

    subgraph 阿里
    B1[千问<br>MAU 1.66亿] -->|守+攻| B2[串起支付宝·淘宝<br>高德·飞猪矩阵]
    end

    subgraph 腾讯
    C1[元宝<br>MAU 5735万] -->|守+攻| C2[Skill协议筑墙<br>受控接入开放]
    end

    style A1 fill:#22d3ee,stroke:#0891b2,color:#000
    style B1 fill:#a855f7,stroke:#7e22ce,color:#fff
    style C1 fill:#a855f7,stroke:#7e22ce,color:#fff
```

---
layout: statement
---

# 三家都不是被动反应，<br>而是各自基于自己的位置在主动卡位。

豆包是攻方，腾讯阿里是守方加攻方。

---
layout: default
---

# 第五章（续）· 流量规则的颠覆

过去十年的小程序逻辑：人找服务。开发者做一个产品，用户搜出来点进去用，靠留存和广告变现。

Skill协议把这个模型直接翻过来：

<br>

<div style="text-align:center; font-size: 1.3em;">

**用户对AI说一句话 → AI决定调哪个Skill**

</div>

<br>

<div class="nc-text-accent" style="text-align:center; font-size: 1.1em;">
开发者第一次失去了"被用户主动选中"的环节。
</div>

---
layout: metrics
---

::metrics::

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">27000+</span>
  <span class="nc-metric-label">AI小程序加入「成长计划」</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">超七成</span>
  <span class="nc-metric-label">个人开发者占比</span>
</div>

<div class="nc-text-muted" style="text-align:center; margin-top: 2rem; width: 100%;">
数据来源：36氪 2026年6月
</div>

---
layout: quote
---

> 一场比小程序更大的"收编"。

— 网易订阅 2026.6.12

<span class="nc-text-muted" style="display:block; margin-top:1rem;">
小程序当年收编了独立App · 现在Skill再收编一次 · 剥掉品牌和用户关系 · 只留接口能力
</span>

---
layout: section
---

# 结尾
## 被换的"芯"不是技术，是身份

---
layout: spotlight
---

# 换芯不是App自己换，<br>是App加上它生态里的所有开发者一起换。

<span style="color: var(--nc-danger); font-size: 1.3em;">但开发者没有投票权。</span>

---
layout: default
---

# 数据来源

<div style="font-size: 0.7em; line-height: 1.8; columns: 2; column-gap: 2rem;">

- 新浪科技 — 微信AI专属卡官方发布
- 财联社 / 36氪 — AI专属卡上线报道
- 晚点LatePost — 阿宝项目立项独家
- IT之家 — 阿宝官宣邀测 · AI接入工具箱
- 智东西 — 阿宝实测 · 资产隔离原文
- 经济观察报 — 阿宝产品分析
- 上证报中国证券网 — "管钱不交给AI"
- 36氪 — 监管视角 · 成长计划数据
- 虎嗅 / 硅星人 — 小程序Skill化深度报道
- QuestMobile — 元宝MAU 5735万
- AppGrowing — 豆包投流成本估算
- 微信开放文档 — 小程序MCP/SKILL规范
- 公开数据 — 各平台MAU数据
- 腾讯股东大会 — 马化腾AI表态

</div>

<div class="nc-text-muted" style="text-align:center; margin-top: 2rem;">
以上 14 个来源交叉验证
</div>


<style>
/* ===== 配色预设：霓虹紫 ===== */
:root {
  --nc-accent:  #a855f7;
  --nc-success: #22d3ee;
  --nc-danger:  #f43f5e;
  --nc-warning: #fbbf24;
  --nc-info:    #818cf8;
}

/* ===== CJK 字体优化 ===== */
.slidev-layout {
  line-height: 1.75;
  font-size: 24px;
}

/* ===== default 布局内容垂直居中 ===== */
.slidev-layout.default {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  padding: 3rem 4rem !important;
}
.slidev-layout.default ul,
.slidev-layout.default ol,
.slidev-layout.default p {
  max-width: 85%;
}

/* ===== Mermaid 中文补丁 ===== */
svg text {
  font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif !important;
}

/* ===== B站录屏：动画降级（仅fade，禁用复杂动画） ===== */
.neon-stagger > * {
  animation: none !important;
  opacity: 1 !important;
}
.shimmer, .shimmer-text, [class*="shimmer"] {
  animation: none !important;
  background: none !important;
}
.particles, .particle, [class*="particle"] {
  display: none !important;
}

/* ===== 录屏面板：隐藏TOC ===== */
#slidev-toc,
.slidev-toc,
.slidev-toc-list,
.toc,
.toc-overlay,
[class*="toc"],
[id*="slidev-toc"] {
  display: none !important;
}
</style>
