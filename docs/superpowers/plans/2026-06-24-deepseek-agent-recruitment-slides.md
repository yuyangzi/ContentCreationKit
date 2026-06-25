# DeepSeek Agent 人才战争 PPT — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 27-slide Slidev + neocarbon presentation from the article "DeepSeek 招不到人——AI人才战争进入下半场" for Bilibili video recording.

**Architecture:** Single `slides.md` file driving Slidev with `@enyineer/slidev-theme-neocarbon` theme. All dependencies in root `package.json`. Output: `dist/` SPA served via `npx serve` for local preview at 1920×1080.

**Tech Stack:** Slidev 52.0.0, neocarbon theme 1.0.8, Vue components (NcRoiCard, NcSteps), Mermaid diagrams, custom flex CSS layouts.

**Design Source:** `/Users/zero/GitHubProject/ContentCreationKit/content/ppt/20260624-deepseek-agent-recruitment/PPT设计.md`
**Article Source:** `/Users/zero/GitHubProject/ContentCreationKit/content/article/20260624-DeepSeek全球急招Agent人才-从大模型到Agent的战略转向.md`

---

### Task 0: Pre-flight — Confirm Environment & Directory

**Files:**
- Verify: `package.json` (root)
- Verify: `node_modules/@slidev/cli`, `node_modules/@enyineer/slidev-theme-neocarbon`
- Create: `content/ppt/20260624-deepseek-agent-recruitment/` (exists from Phase 1)

- [ ] **Step 1: Verify Node.js version**

Run: `node --version`
Expected: v20.12.0 or higher

- [ ] **Step 2: Verify slidev and neocarbon installed**

Run: `ls node_modules/@slidev/cli node_modules/@enyineer/slidev-theme-neocarbon`
Expected: Both directories exist with no errors

If missing, run: `npm install --registry https://registry.npmmirror.com`

- [ ] **Step 3: Verify PPT directory exists**

Run: `ls content/ppt/20260624-deepseek-agent-recruitment/`
Expected: PPT文案.md and PPT设计.md present

---

### Task 1: Write slides.md — Frontmatter + Style Block

**Files:**
- Write: `content/ppt/20260624-deepseek-agent-recruitment/slides.md`

Write the complete `slides.md` with frontmatter, all 27 slides, and the `<style>` block. Since this is a single large file, we compose it in sections.

- [ ] **Step 1: Write frontmatter and opening slides (Slides 1-5)**

Write the file header with frontmatter configuration and Chapter 1 slides:

```markdown
---
theme: '@enyineer/slidev-theme-neocarbon'
title: 'DeepSeek 招不到人——AI人才战争进入下半场'
info: |
  ## DeepSeek 招不到人
  从大模型到Agent的战略转向
  数据来源: SCMP, 晚点LatePost, 36氪, Fortune, Lenny's Newsletter 等13个来源
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

# DeepSeek 招不到人

AI人才战争进入下半场

<span class="nc-text-muted">2026年6月 · 从大模型到Agent的战略转向</span>

---
layout: quote
---

> 每天都在面试，缺人缺疯了。

— 崔添翼，DeepSeek Harness 部门负责人

---
layout: default
---

# 三类岗位，全线招人

<div style="display:flex; gap:1.2rem; margin-top:1.5rem;">

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 🔬 研究员

<span class="nc-text-muted">实习 · 全职</span>

定义问题：上下文管理、长期记忆、Subagent 协同

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### ⚙️ 工程师

<span class="nc-text-muted">实习 · 全职</span>

实现能力：技术架构、系统选型、生产级部署

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 📋 产品经理

<span class="nc-text-muted">全职</span>

连接一切：研究员、工程师、开源社区、用户

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">工作地点：北京 · 杭州 | 一轮笔试 + 三轮面试 | 崔添翼亲自终面</span>

---
layout: default
---

# 一个多月没招满

<div style="display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-top:1.5rem;">

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">~50</span>
  <span class="nc-metric-label">BOSS直聘开放岗位</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-danger">1+</span>
  <span class="nc-metric-label">月连续招聘未满</span>
</div>

<div class="nc-metric">
  <span class="nc-metric-value nc-text-accent">3</span>
  <span class="nc-metric-label">类岗位同步开放</span>
</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">不是常规补员——Harness 团队从零组建</span>

---
layout: section
---

# 第一章 · 缺人缺疯了
```

- [ ] **Step 2: Write Chapter 2 slides (Slides 6-10)**

Append to slides.md:

```markdown
---
layout: statement
---

# 判断走在公司前面

<span class="nc-text-muted">郭达雅离开的理由，变成了公司后来押注的方向</span>

---
layout: default
---

# 郭达雅：GRPO 发明人

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; display:flex; align-items:center; justify-content:center;">
  <div style="text-align:center;">
    <div class="nc-metric-value nc-text-accent" style="font-size:3rem;">38,000+</div>
    <div class="nc-metric-label">学术引用</div>
  </div>
</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 技术贡献

- **GRPO 算法**发明人
- DeepSeek-Coder、V3、R1 核心贡献者
- 负责代码智能和推理方向

### 学术背景

- 中山大学博士
- 微软亚洲研究院联合培养

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">字节薪资总包"近亿元"（四年归属，字节官方否认该数字）— 晚点LatePost</span>

---
layout: default
---

# 出走时间线

<div style="display:flex; gap:1.5rem; margin-top:1.5rem; text-align:center; align-items:flex-start;">

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
  <div class="nc-text-accent" style="font-size:2rem; font-weight:bold;">2025.10</div>
  <div style="margin-top:0.5rem;">郭达雅决定离职</div>
</div>

<div style="font-size:2rem; align-self:center; margin-top:1rem;">→</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
  <div class="nc-text-accent" style="font-size:2rem; font-weight:bold;">2026.03</div>
  <div style="margin-top:0.5rem;">正式离开，加入字节<br><span class="nc-text-muted" style="font-size:0.9rem;">Seed团队Agent方向负责人</span></div>
</div>

<div style="font-size:2rem; align-self:center; margin-top:1rem;">→</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">
  <div class="nc-text-accent" style="font-size:2rem; font-weight:bold;">2026.05</div>
  <div style="margin-top:0.5rem;">崔添翼加入<br>组建 Harness 团队</div>
</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">顺序是反过来的：有人因Agent优先级不够先走，公司才紧急组建团队</span>

---
layout: default
---

# 五个人的离开

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 基座模型 & 推理

- <span class="nc-text-danger">王炳宣</span> — 基座模型核心 → 腾讯混元
- <span class="nc-text-danger">罗福莉</span> — V3 核心贡献 → 小米（未确认）
- <span class="nc-text-danger">郭达雅</span> — 代码智能和推理 → 字节

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### OCR & 多模态

- <span class="nc-text-danger">魏浩然</span> — OCR 系列核心 → 未公开
- <span class="nc-text-danger">阮翀</span> — 多模态核心 → 元戎启行首席科学家

<br>

<span class="nc-text-muted">DeepSeek ~150-160 人 | 极度扁平：仅两层</span>

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">五人覆盖四条核心技术线</span>

---
layout: section
---

# 第二章 · 出走与到来
```

- [ ] **Step 3: Write Chapter 3 slides (Slides 11-15)**

Append to slides.md:

```markdown
---
layout: spotlight
---

# Model + Harness = Agent

<span class="nc-text-muted">做大模型和做Agent，已经不是同一件事</span>

---
layout: default
---

# Harness 六要素

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

- <span class="nc-text-accent">上下文管理</span>
- <span class="nc-text-accent">长期记忆</span>
- <span class="nc-text-accent">Subagent 协同</span>

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

- <span class="nc-text-accent">自进化 Agent</span>
- <span class="nc-text-accent">工具调用与规划</span>
- <span class="nc-text-accent">MCP 协议集成</span>

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">模型之外的所有基础设施</span>

---
layout: default
---

# 发动机 vs 整车

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 🏎️ 发动机 = 模型

- 训练、推理、Scaling Law
- 大模型时代的核心竞争力
- 产品就是 API

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 🚗 整车 = Agent

- 方向盘、变速箱、刹车、悬挂
- Agent 时代的工程体系
- 产品需要在真实环境里跑

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">你造出了最好的发动机，不代表你造得出能上路的车</span>

---
layout: default
---

# 三类岗位分工

<NcSteps
  :steps="[
    { title: '研究员：定义问题', status: 'active' },
    { title: '工程师：实现能力', status: 'pending' },
    { title: '产品经理：连接社区', status: 'pending' },
  ]"
/>

<div style="margin-top:1.5rem; text-align:center;">
  <span class="nc-text-muted">研究 → 工程 → 产品 → 社区 · Agent 基础设施的完整研发链</span>
</div>

---
layout: section
---

# 第三章 · 什么是 Harness
```

- [ ] **Step 4: Write Chapter 4 slides (Slides 16-20)**

Append to slides.md:

```markdown
---
layout: default
---

# 外面的世界：一周 48 条

<div style="display:flex; justify-content:center; gap:1.5rem; flex-wrap:wrap; margin-top:1.5rem;">

<NcRoiCard label="Agent 产品/模型/研究" value="48条" trend="up" color="#a855f7" />

<NcRoiCard label="工程师产出" value="8x" trend="up" color="#22d3ee" />

<NcRoiCard label="Anthropic 年化营收" value="$47B" trend="up" color="#22d3ee" />

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">Agentic.ai News 2026年6月第三周 · 不是"最近很热"，是每周48条</span>

---
layout: default
---

# Anthropic 的降维打击

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### Claude Code

- <span class="nc-text-accent">AI 编写已持续 >7 个月</span>
- 创始人 Boris Cherny 2025.11 起未手写代码
- 管理"数百到数万"个 AI agents
- <span class="nc-text-success">单品年化营收 ~$2.5B</span>

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 副作用

- Fortune: 工作变成了"<span class="nc-text-danger">lonely experience</span>"
- 全员用 agent 写代码，人际协作变少
- "coding is no longer the bottleneck"

<br>
<span class="nc-text-muted">Anthropic 估值 $965B（Series H） · 链上隐含 $1.2T</span>

</div>

</div>

---
layout: default
---

# 国内三线并进

<div style="display:flex; gap:1.2rem; margin-top:1.5rem;">

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 微信小微 Agent

<span class="nc-text-success">6月20日 灰度上线</span>

<span class="nc-text-accent" style="font-size:1.5rem;">14.32亿</span> 月活用户

消费级 Agent

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 蚂蚁 AMP 协议

<span class="nc-text-success">已开源</span>

全球首个移动端

Agent 支付框架

金融 Agent

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 小米 MiMo Code

<span class="nc-text-success">MIT 协议开源</span>

AI 编程工具

开发工具赛道

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">消费级 · 金融 · 开发工具 — 三条赛道同时发力</span>

---
layout: default
---

# 竞争逻辑变了

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 🏔️ Anthropic

- Claude Code >7月 AI 编写
- 产出 <span class="nc-text-success">8x</span>
- 年化营收 <span class="nc-text-success">$47B</span>
- 生态成熟，工程积累深厚

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 🏃 DeepSeek

- 2026年5月 <span class="nc-text-danger">才开始组建 Harness</span>
- 开源品牌 + 技术影响力
- 核心人才 <span class="nc-text-danger">5人已离职</span>
- 从头追赶，时间窗口紧迫

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">不是"竞争对手也在做"，是"竞争对手已经把东西做出来了"</span>

---
layout: section
---

# 第四章 · 竞争白热化
```

- [ ] **Step 5: Write Chapter 5 slides (Slides 21-24)**

Append to slides.md:

```markdown
---
layout: default
---

# 三种稀缺能力

<div style="display:flex; gap:1.2rem; margin-top:1.5rem;">

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 🧠 研究品味

知道什么问题值得解决

判断研究方向的直觉

不是多读论文就能有的

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### ⚡ 工程能力

把方案实现到生产级别

系统能跑、能迭代

能服务真实用户

</div>

<div style="flex:1; padding:1.5rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 🎯 产品思维

理解用户到底要什么

连接技术与需求

定义产品方向

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">三种能力在同一个人身上同时出现——极度稀缺</span>

---
layout: default
---

# 两个时代的竞争逻辑

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### 大模型时代

- 竞争主体：<span class="nc-text-accent">谁能训练最大的模型</span>
- 只需要顶尖的研究员
- 懂架构、懂训练、懂 Scaling Law
- 不需要产品经理
- 产品就是 API

</div>

<div style="flex:1; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

### Agent 时代

- 竞争主体：<span class="nc-text-accent">Agent 要跑在真实环境里</span>
- 需要一个团队
- 既懂研究又懂工程还懂产品
- 三层接口太紧密
- 不会产品化的研究员做不了 Agent

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">抢的不是"会写代码的人"，是"知道要做什么的人"</span>

---
layout: default
---

# 2023 年就想做 Agent

<div style="max-width:80%; margin:1.5rem auto; padding:2rem; background:rgba(255,255,255,0.03); border-radius:12px; border:1px solid rgba(255,255,255,0.06);">

> 郭达雅知道这件事重要，但当时没有人给他资源。

<br>

<span class="nc-text-accent">等他走了，DeepSeek 才发现不对。</span>

<br>

Agent 不是"以后再说"的事——是现在就必须做的事。

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">方向判断走在公司战略前面</span>

---
layout: section
---

# 第五章 · 人才新定义
```

- [ ] **Step 6: Write Ending slides (Slides 25-27)**

Append to slides.md:

```markdown
---
layout: statement
---

# 不是"谁会训练"
# 是"谁能驯服"

<span class="nc-text-muted">能把模型套上 Harness，让它真的能干活</span>

---
layout: quote
---

> 这件事，不是有钱就能快起来的。

— 但崔添翼还在面试，外面一周 48 条

---
layout: default
---

# 数据来源

<div style="display:flex; gap:1.5rem; margin-top:1.5rem;">

<div style="flex:1; font-size:0.85rem;">

**一手来源：**

1. SCMP（2026.06.23）
2. SCMP（2026.05.19）
3. Fortune（2026.06.23）
4. Lenny's Newsletter（2026.06.21）
5. 36氪 · 量子位
6. IT之家（2026.06.20）
7. 崔添翼 X 账号

</div>

<div style="flex:1; font-size:0.85rem;">

**一手来源（续）：**

8. BusinessWire（2026.04.28）
9. PANews
10. Digg（2026.06.21）
11. Agentic.ai News

<br>

**二手来源：**

12. 晚点LatePost（2026.04.16）
13. PCNow（2026.04.21）

</div>

</div>

<span class="nc-text-muted" style="display:block; text-align:center; margin-top:2rem;">共 13 个来源 · 交叉验证 · 一手标注</span>
```

- [ ] **Step 7: Append `<style>` block to slides.md**

Append the complete CSS block at the end:

```html
<style>
/* ============================================
   视觉质量修复
   ============================================ */

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

/* 2. flex 容器顶部呼吸空间 */
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
   主题配色 — 霓虹紫（预设 A）
   ============================================ */
:root {
  --nc-accent:  #a855f7;
  --nc-success: #22d3ee;
  --nc-danger:  #f43f5e;
  --nc-warning: #fbbf24;
  --nc-info:    #818cf8;
}

/* ============================================
   CJK 字体
   ============================================ */
.slidev-layout { line-height: 1.75; font-size: 24px; }

/* ============================================
   Mermaid 中文补丁
   ============================================ */
svg text { font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important; }

/* ============================================
   动画降级 — 淡入档位
   ============================================ */
.slidev-layout [class*="stagger"] { animation: none !important; opacity: 1 !important; }
.slidev-layout [class*="shimmer"] { animation: none !important; opacity: 1 !important; }
.slidev-layout [class*="particle"] { animation: none !important; opacity: 1 !important; }

/* ============================================
   录屏面板隐藏（仅 TOC）
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
```

---

### Task 2: Build and Preview

**Files:**
- Build: `content/ppt/20260624-deepseek-agent-recruitment/slides.md` → `dist/`

- [ ] **Step 1: Build slides**

Run: `npx slidev build content/ppt/20260624-deepseek-agent-recruitment/slides.md`
Expected: Exit code 0, `dist/` directory created under `content/ppt/20260624-deepseek-agent-recruitment/`

- [ ] **Step 2: Serve for preview**

Run: `npx serve content/ppt/20260624-deepseek-agent-recruitment/dist -p 3030 --no-clipboard`
Expected: "Serving!" message with http://localhost:3030

- [ ] **Step 3: Open in browser**

Navigate to http://localhost:3030 in browser. Set viewport to 1920×1080. Fullscreen (F11).

---

### Task 3: Manual Verification

- [ ] **Visual Quality Checklist (all 27 slides)**

| # | Check | Pass? |
|---|-------|-------|
| 1 | 内容垂直居中 — 无下半屏大面积空白 | ☐ |
| 2 | 卡片顶部边距 — 不紧贴标题 | ☐ |
| 3 | 每张 default 幻灯片有 `#` 标题 | ☐ |
| 4 | 卡片间距 — 双栏 1.5rem / 三栏 1.2rem | ☐ |
| 5 | NcTerminal 不适用（本文未使用） | ☐ |

- [ ] **Color Encoding Checklist**

| # | Check | Pass? |
|---|-------|-------|
| 1 | 默会知识/价值判断 → `nc-text-success`（青），非 `nc-text-accent` | ☐ |
| 2 | 下降/负面数据 → `nc-text-danger`（玫红） | ☐ |
| 3 | 中性数据 → `nc-text-accent`（紫），非红色 | ☐ |
| 4 | NcRoiCard color 使用十六进制（`#22d3ee`, `#f43f5e`, `#a855f7`） | ☐ |

- [ ] **Prohibited Pattern Scan**

Run verification commands:

```bash
# No comparison layout
grep -n "layout: comparison" content/ppt/20260624-deepseek-agent-recruitment/slides.md
# Expected: no output

# No ::metrics:: slot
grep -n "metrics::" content/ppt/20260624-deepseek-agent-recruitment/slides.md
# Expected: no output

# No CSS vars in component props (check for var(-- in non-style context)
grep -n "colors.*var(--" content/ppt/20260624-deepseek-agent-recruitment/slides.md
# Expected: no output

# Every default slide has heading
grep -c "^#" content/ppt/20260624-deepseek-agent-recruitment/slides.md
# Expected: 27+ headings (cover, section, quote, statement, spotlight layouts don't need explicit # in body)

# No gap:2rem
grep -n "gap:.*2rem" content/ppt/20260624-deepseek-agent-recruitment/slides.md
# Expected: no output
```

- [ ] **Data Accuracy Checklist**

| # | Data Point | Slide | Article Line | Match? |
|---|-----------|-------|-------------|--------|
| 1 | 38,000+ 引用 | 7 | 行 17 | ☐ |
| 2 | ~150-160 人 | 9 | 行 39 | ☐ |
| 3 | 48条/周 | 16 | 行 76 | ☐ |
| 4 | 8x 产出 | 16 | 行 80 | ☐ |
| 5 | $9B→$47B | 16 | 行 82 | ☐ |
| 6 | >7月 AI编写 | 17 | 行 78/111 | ☐ |
| 7 | 14.32亿月活 | 18 | 行 86 | ☐ |
| 8 | 2025.10→2026.3→2026.5 | 8 | 行 22-25 | ☐ |
| 9 | 五名离职人员 | 9 | 行 31-36 | ☐ |
| 10 | 13个来源 | 27 | 行 132-144 | ☐ |
