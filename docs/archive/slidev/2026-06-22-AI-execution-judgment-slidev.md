# AI压缩执行力 -> Slidev 演示文稿 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 将文章《AI压缩了执行力，放大了判断力》转为 ~31 张 Slidev + neocarbon 主题 HTML 演示文稿，用于 B站 录屏。

**Architecture:** 单文件 slides.md + package.json -> slidev build -> dist/ SPA。

**Tech Stack:** Slidev 52.0.0, @enyineer/slidev-theme-neocarbon 1.0.8, Node.js >= 20.12.0

**Design Doc:** docs/superpowers/specs/2026-06-22-AI压缩执行力-Slidev设计.md

---

## 文件结构

```
content/ppt/2026-06-22-AI-execution-judgment/
  package.json
  slides.md
  dist/
```

---

### Task 1: 初始化项目

**Files:**
- Create: `content/ppt/2026-06-22-AI-execution-judgment/package.json`

- [ ] Step 1: mkdir -p "content/ppt/2026-06-22-AI-execution-judgment"
- [ ] Step 2: 写入 package.json (name: ppt-ai-execution-judgment, private: true, deps: @slidev/cli@52.0.0, @enyineer/slidev-theme-neocarbon@1.0.8)
- [ ] Step 3: cd content/ppt/2026-06-22-AI-execution-judgment && npm install

---

### Task 2: slides.md frontmatter + 样式

**Files:**
- Create: `content/ppt/2026-06-22-AI-execution-judgment/slides.md`

- [ ] Step 1: 写入 frontmatter (theme: @enyineer/slidev-theme-neocarbon, transition: fade, fonts: PingFang SC)
- [ ] Step 2: 写入 style 块 (--nc-accent:#ff6b35, --nc-success:#22c55e, --nc-danger:#ef4444, svg text font-family)

---

### Task 3: 封面 + 章节标题 (7张)

- [ ] #01 cover: "AI压缩了执行力，放大了判断力"
- [ ] #02 statement: "为什么会用AI的人越来越值钱，不会用的人越来越焦虑"
- [ ] #03 section: "第一章 执行层的差距正在消失"
- [ ] #09 section: "第二章 同一句话，不同价格"
- [ ] #15 section: "第三章 梯子正在被抽掉"
- [ ] #20 section: "第四章 焦虑不是来自未知，来自已知"
- [ ] #25 section: "第五章 判断力会不会也被压缩?"

---

### Task 4: 第一章内容 #04-#08 (5张)

- [ ] #04 quote: 会计用Claude写对账脚本
- [ ] #05 default+NcBarChart: 89% vs 88%
- [ ] #06 default+NcBarChart: 15% -> 28-33%
- [ ] #07 metrics: 放弃率19%/5-7%, 翻盘4%/15%
- [ ] #08 diagram+Mermaid: 碰壁流程图

---

### Task 5: 第二章内容 #10-#14 (5张)

- [ ] #10 quote: 同一个AI努力程度不同
- [ ] #11 comparison: 5动作 vs 12动作
- [ ] #12 comparison: 600词 vs 3200词
- [ ] #13 statement: "People decide what to build"
- [ ] #14 comparison: 模糊指令 vs 精确指令

---

### Task 6: 第三章内容 #16-#19 (4张)

- [ ] #16 quote: 传统白领成长路径
- [ ] #17 comparison: 可编码知识 vs 默会知识
- [ ] #18 quote: Dallas Fed原话
- [ ] #19 default+NcLineChart: 7个月趋势

---

### Task 7: 第四章内容 #21-#24 (4张)

- [ ] #21 quote: 一边疯狂用一边疯狂焦虑
- [ ] #22 default+NcBarChart: 93% vs 58%
- [ ] #23 metrics: 40%焦虑 59%担心 93%使用
- [ ] #24 quote: 越了解AI越焦虑 + 案例

---

### Task 8: 第五章内容 #26-#28 (3张)

- [ ] #26 quote: 那万一AI把判断力也学会了呢
- [ ] #27 comparison: 执行判断(含70%数据) vs 价值判断
- [ ] #28 statement: 你可以让AI写一千个方案

---

### Task 9: 结尾 #29-#31 (3张)

- [ ] #29 quote: Coding agents are not substituting
- [ ] #30 statement: 那个不敢交付的瞬间
- [ ] #31 default: 6个数据来源

---

### Task 10: 构建 + 验证

- [ ] slidev build (从 content/ppt/2026-06-22-AI-execution-judgment/ 目录)
- [ ] npx serve dist -p 3030
- [ ] 浏览器打开 http://localhost:3030, 调至1920x1080
- [ ] 逐张检查: 数据准确性 x31
- [ ] 颜色编码: 绿=默会/正面, 红=负面, 橙=中性
- [ ] 确认动画策略已生效 (保留全部)
- [ ] F12 检查无 console 错误
- [ ] Mermaid 中文渲染正常
