---
theme: '@enyineer/slidev-theme-neocarbon'
title: '豆包烧钱、Seedance赚钱，字节AI的两个世界'
info: |
  ## 字节AI战略分析
  数据来源：火山引擎FORCE大会、晚点LatePost、36氪、腾讯研究院、Citi Innovation Lab、SCMP、CNBC等13家机构
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

# 豆包烧钱、Seedance赚钱<br>字节AI的两个世界

<span class="nc-text-muted">2026.06 · 火山引擎FORCE大会</span>

---
layout: quote
---

> 同一个公司。同一个AI赛道。两个世界。

— 覆盖两端的平行故事

---
layout: section
---

# 第一章<br>被免费喂大的两亿用户

---
layout: default
---

# 豆包的两亿用户

<div style="display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-top:1.5rem;">

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">2亿+</span>
  <span class="nc-metric-label">豆包DAU</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">180万亿</span>
  <span class="nc-metric-label">日均Token调用</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-danger"><100万</span>
  <span class="nc-metric-label">日收入（元）</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-danger">数千万</span>
  <span class="nc-metric-label">日算力成本（元）</span>
</div>

</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:2rem;">数据来源：火山引擎FORCE大会 · 晚点LatePost</span>

---
layout: default
---

# Token增长1000倍

<NcLineChart
  title="Token调用量增长趋势（日均·万亿）"
  :labels="['发布初期', '2025', '2026.06']"
  :datasets="[
    { label: '日均Token（万亿）', data: [0.18, 30, 180], color: '#a855f7' }
  ]"
/>

<div style="margin-top:1rem;">

<v-clicks>

- 日均Token调用量：**180万亿**（FORCE大会最新数据）
- 较发布时增长 **1000倍**
- 用户越多，推理成本越高——亏得越多

</v-clicks>

</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:1.5rem;">数据来源：火山引擎FORCE大会 2026.06.23</span>

---
layout: default
---

# 付费订阅上线 · 市场的反弹

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 5月4日 · 三档定价

- **68元/月** — 基础版
- **200元/月** — 专业版
- **500元/月** — 旗舰版

<span class="nc-text-accent">💡 500元档本质是价格锚定——让68元显得合理</span>

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 市场反应

<span class="nc-text-danger" style="font-size:1.3em;">**"豆包，笨还收费"**</span> 登上热搜

MAU当月减少 <span class="nc-text-danger" style="font-size:1.5em;">**610万**</span>

反弹烈度超出预期

</div>

</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:2rem;">数据来源：36氪 2026.06.23</span>

---
layout: default
---

# 中国AI用户付费现状

<NcBarChart
  title="付费率 & 消费区间（%）"
  :labels="['已付费用户', '月消费30-100元', '意愿支付均值']"
  :data="[9.8, 44.7, 48.3]"
  :colors="['#a855f7', '#818cf8', '#f43f5e']"
  height="280"
/>

<div style="margin-top:1rem;">
<span class="nc-text-accent">💡</span> 500元档本质是<span class="nc-text-accent">价格锚定</span>——让68元突然显得合理。但中国用户意愿支付均值只有<span class="nc-text-danger">48.3元</span>。
</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:1.5rem;">腾讯研究院 2012样本 · Citi Innovation Lab 1800样本 · 2026.03</span>

---
layout: default
---

# 付费能力对比 · 中美差距

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### ChatGPT Pro · $200/月

- 占美国月收入中位数 <span class="nc-text-success" style="font-size:1.5em;">**~3%**</span>
- 约1450元人民币
- 市场已逐渐接受此定价

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 豆包 500元/月

- 占中国月收入中位数 <span class="nc-text-danger" style="font-size:1.5em;">**~16%**</span>
- 按购买力调整：<span class="nc-text-danger" style="font-size:1.5em;">**5倍**</span> 于美国
- 中国消费者相对负担远超美国

</div>

</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:2rem;">数据来源：CNBC 2026.05.28 · 36氪</span>

---
layout: default
---

# 工具应该免费 · 中国互联网的默认规则

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 规则

<v-clicks>

- **工具类软件** → 默认免费
- **娱乐消费** → 打赏/游戏充值另算
- **AI助手？** → 工具，应该免费

</v-clicks>

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 结果

<v-clicks>

- **迁移成本为零** → 5分钟下载，1分钟登录
- 今天嫌豆包贵 → 明天切千问/Kimi/DeepSeek
- <span class="nc-text-danger">用户没有沉没成本，平台没有定价权</span>

</v-clicks>

</div>

</div>

---
layout: section
---

# 第二章<br>消费者看不见的利润机器

---
layout: default
---

# Seedance 的利润机器

<div style="display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-top:1.5rem;">

<div class="nc-metric">
  <span class="nc-metric-value nc-text-success">~20亿$</span>
  <span class="nc-metric-label">年化营收</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-success">~70%</span>
  <span class="nc-metric-label">毛利率</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-success">10亿+</span>
  <span class="nc-metric-label">月收入（元）</span>
</div>

</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:2rem;">数据来源：晚点LatePost · 外部传言偏高（谭待辟谣），方向确认</span>

---
layout: default
---

# 两个世界的对比 · 冰火两重天

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### C端 · 豆包

<span class="nc-text-danger" style="font-size:1.3em;">**日亏数千万**</span>

- 2亿DAU养不起自己
- 用户最多 → 亏得最多
- 免费模式撞上推理成本墙

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### B端 · Seedance

<span class="nc-text-success" style="font-size:1.3em;">**毛利~70%**</span>

- 企业客户愿意付费
- 利润机器的核心引擎
- MoE架构成本优势明显

</div>

</div>

---
layout: default
---

# 视频模型为何能赚钱

<v-clicks depth="2">

- **MoE架构让推理成本可控**
  - 2000亿参数，每次只激活一部分
  - 底座是成本优势
- **企业刚需**
  - 广告素材、电商展示、影视预演
  - 每一环都是明确的生产预算
- **版权壁垒**
  - AI生成内容的版权归谁？
  - Seedance搭了AI版权平台——企业选型的关键筹码

</v-clicks>

---
layout: default
---

# Seedance 2.5 功能矩阵

<span class="nc-text-muted">火山引擎FORCE大会预告 · 2026.06.23</span>

<NcSteps
  :steps="[
    { title: '30秒原生视频', status: 'done' },
    { title: '50参考素材', status: 'done' },
    { title: '无损局部编辑', status: 'done' },
    { title: '音视频天然同步', status: 'done' },
    { title: '3D白模预演', status: 'done' },
    { title: 'AI版权平台', status: 'done' },
  ]"
/>

<div style="margin-top:1.5rem;">
<span class="nc-text-accent">定位：</span> 生成工具 → 生产平台。企业级视频制作的工作流组件，不是消费级玩具。
</div>

---
layout: default
---

# 火山引擎MaaS增长

<NcBarChart
  title="营收增长路径（亿元）"
  :labels="['2025实际', '2026目标']"
  :data="[15, 150]"
  :colors="['#818cf8', '#22d3ee']"
  height="280"
/>

<div style="text-align:center;margin-top:0.5rem;">
  <span class="nc-text-accent">49.5%</span> 中国公有云MaaS份额（IDC）
  <br>
  <span class="nc-text-success" style="font-size:1.2em;">10倍增长</span> — 不是自然增长，而是战略校准信号
</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:1.5rem;">数据来源：36氪 2026.06.23</span>

---
layout: default
---

# 版权壁垒与增速隐忧

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 版权护城河

首批合作 **周星驰三部IP**：

- 《喜剧之王》
- 《食神》
- 《长江七号》

对企业：**版权合规 > 模型性能**

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### ⚠️ 增速放缓

<span class="nc-text-danger">**隐忧**</span>

- 谭待：外部传言"偏高"
- 前有Google Veo
- 后有多家国内视频模型
- 先发窗口不会一直开着

</div>

</div>

---
layout: section
---

# 第三章<br>成本才是破局点

---
layout: default
---

# 豆包2.1 定价体系

<div style="display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-top:1.5rem;">

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">6元</span>
  <span class="nc-metric-label">输入（百万Token）</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">30元</span>
  <span class="nc-metric-label">输出（百万Token）</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">1.2元</span>
  <span class="nc-metric-label">缓存（百万Token）</span>
</div>

</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:2rem;">豆包2.1定价 · 火山引擎FORCE大会 2026.06.23</span>

---
layout: default
---

# 成本暴砍80%

<NcBarChart
  title="综合成本对比（相对指数）"
  :labels="['Opus 4.6-4.8系列', '豆包2.1']"
  :data="[100, 20]"
  :colors="['#f43f5e', '#22d3ee']"
  height="280"
/>

<div style="text-align:center;margin-top:0.5rem;">
综合成本较Opus系列低近 <span class="nc-text-success" style="font-size:1.3em;">**80%**</span>
</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:1.5rem;">数据来源：36氪《字节掀桌，豆包2.1成本暴砍80%》 2026.06.23</span>

---
layout: quote
---

> 模型能力到了一定程度，<span class="nc-text-success">**降本之后才能创造价值**</span>。

— 谭待，36氪专访 2026.06.23

---
layout: default
---

# 豆包2.1 技术指标

<v-clicks>

- **编程能力** — 追平Claude Opus 4.7
- **Agent评测** — 超过Opus 4.7 和 GPT-5.5
- **芯片设计** — 18小时自主完成 **1303行** RTL代码
- 商业意义：能力追上 → 成本砍下 → 飞轮转起

</v-clicks>

<NcTerminal
  title="芯片设计案例 · 18小时自主完成"
  :lines="[
    '# Step 1: 架构分析',
    '$ AI Agent 分析芯片设计需求',
    '✓ 架构方案确定',
    '# Step 2: RTL代码生成',
    '$ AI Agent 生成寄存器传输级代码',
    '✓ RTL代码生成：1303行',
    '# Step 3: 仿真验证',
    '$ 运行仿真测试套件',
    '✓ 仿真验证全部通过',
  ]"
/>

---
layout: default
---

# 两条路径趋同 · B端企业服务

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### Anthropic 路径

- 估值 **$9650亿**
- ARR **$470亿**
- Claude Code **$25亿**/年
- 高定价API
- 企业客户为核心

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 字节 路径

- MaaS目标 **150亿¥** (≈$21亿)
- C端免费烧规模
- B端视频模型造血
- 豆包2.1成本对齐

</div>

</div>

<div style="text-align:center;margin-top:1.5rem;">
<span class="nc-text-accent" style="font-size:1.2em;">**两条路径趋同——B端企业服务**</span>
</div>

---
layout: section
---

# 第四章<br>流量到技术的转身

---
layout: default
---

# 字节的战略投入

<div style="display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-top:1.5rem;">

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">2000亿+</span>
  <span class="nc-metric-label">2026 AI资本开支（元）</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-danger">↓70%+</span>
  <span class="nc-metric-label">2025净利润同比变化</span>
</div>

</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:2rem;">南华早报 · 第一财经 · 梁汝波："爬AI这座山是最优先的事"</span>

---
layout: default
---

# 战略校准信号

<v-clicks>

- **资源重分配** — 从C端豆包向B端企业服务倾斜
- **火山引擎** — 15亿 → 150亿：不是自然增长，是战略校准
- **高管赴Anthropic参观** → 回来后成本砍80%
- **谭待说"上牌桌"** — 字节在学：怎么从企业钱包里挣出AI的成本

</v-clicks>

---
layout: default
---

# 付费 vs 免费 · 两个世界的用户

<NcBarChart
  title="AI消费意愿对比（%）"
  :labels="['已付费·感知提效', '已付费·增加消费', '免费·增加消费']"
  :data="[65.1, 61.2, 27.5]"
  :colors="['#22d3ee', '#22d3ee', '#a855f7']"
  height="280"
/>

<div style="margin-top:1rem;">
<span class="nc-text-accent">反直觉结论：</span> 免费用户其实不知道自己需要AI。付过费之后反而明白了。
</div>

<span class="nc-text-muted" style="display:block;text-align:center;margin-top:1.5rem;">腾讯研究院 2026.03 · 2012样本</span>

---
layout: statement
---

# 免费是蜜糖还是毒药？

# 都不是。<br><span class="nc-text-success">它是一个阶段。</span>

---
layout: default
---

# 数据来源

<div style="display:flex; gap:1.5rem; margin-top:1rem;">

<div style="flex:1;">

### 一手来源

1. 火山引擎FORCE大会 (2026.06.23)
2. 腾讯研究院调研 (2026.03) — 2012样本
3. Citi Innovation Lab调研 (2026.03) — 1800样本

</div>

<div style="flex:1;">

### 二手来源

4. 晚点LatePost《字节跳动的AI账本》
5. 36氪《豆包2.1成本暴砍80%》
6. 36氪《专访火山引擎谭待》
7. 36氪《Agent 18小时芯片设计》
8. 36氪《集体涨价，大模型开始找你要钱》
9. 36氪《首次付费是AI消费爆发引爆点》
10. 南华早报《Will China pay for AI?》
11. 第一财经 — 字节净利润下降70%
12. CNBC《Anthropic tops OpenAI》
13. Sixth Tone《Bot for Profit》

</div>

</div>

---
layout: default
---

# 2亿用户被一个成本黑洞养着

退不回去，也赚不回来。

豆包2.1砍了80%成本，编程追平前沿，Agent跑18小时芯片设计。

<div style="margin-top:1.5rem;font-size:1.5rem;">
<span class="nc-text-accent">这可能是免费阶段最后一个版本的豆包。</span>
</div>

<div style="margin-top:2rem;">
<span class="nc-text-muted">谭待在FORCE大会上：</span>
</div>

> 模型跨过生产级质变点，飞轮才真正转起来。

<style>
/* ============================================
   配色预设：霓虹紫（预设A）
   ============================================ */
:root {
  --nc-accent:  #a855f7;
  --nc-success: #22d3ee;
  --nc-danger:  #f43f5e;
  --nc-warning: #fbbf24;
  --nc-info:    #818cf8;
}

/* ============================================
   视觉质量修复
   ============================================ */

/* CJK 行高 */
.slidev-layout {
  line-height: 1.75;
  font-size: 24px;
}

/* 1. 强制 default 布局内容垂直居中 */
.slidev-layout.default {
  display: flex !important;
  flex-direction: column !important;
  justify-content: center !important;
  padding: 3rem 4rem !important;
}
.slidev-layout.default > *:first-child {
  margin-top: 0 !important;
}

/* 2. 确保 flex 容器有顶部呼吸空间 */
.slidev-layout.default [style*="display:flex"],
.slidev-layout.default [style*="display: flex"] {
  margin-top: 1.5rem;
}

/* 3. 内容宽度限制 */
.slidev-layout.default ul,
.slidev-layout.default ol,
.slidev-layout.default p {
  max-width: 85%;
}

/* ============================================
   Mermaid 中文补丁
   ============================================ */
svg text {
  font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important;
}

/* ============================================
   动画降级 — 淡入档（禁用 staggered/shimmer/particles）
   ============================================ */
.nc-stagger > *,
[class*="stagger"],
.nc-shimmer,
[class*="shimmer"],
.nc-particles,
[class*="particles"] {
  animation: none !important;
  opacity: 1 !important;
  transform: none !important;
}

/* ============================================
   录屏面板隐藏 — 仅 TOC
   ============================================ */
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
