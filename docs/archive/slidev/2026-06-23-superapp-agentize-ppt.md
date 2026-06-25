# 超级App Agent化 PPT 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 `2026-06-23-超级App换芯-PPT设计.md` 生成 31 张 neocarbon 主题 slides.md 并构建为 SPA

**Architecture:** 单个 `slides.md` 文件包含 frontmatter + 31 张幻灯片 + `<style>` 块。使用 `@enyineer/slidev-theme-neocarbon` 主题，配色霓虹紫（预设A），淡入动画。依赖由项目根 `package.json` 统一管理。

**Tech Stack:** Slidev 52.0.0, neocarbon 1.0.8, Mermaid, Chart.js (via neocarbon)

---

## 前置检查

- [x] 目录 `content/ppt/superapp-agentize/` 已创建
- [x] 根 `node_modules/` 已安装 `@slidev/cli` 和 `@enyineer/slidev-theme-neocarbon`

---

### Task 1: 编写 slides.md 完整文件

**Files:**
- Create: `content/ppt/superapp-agentize/slides.md`

这是主任务——基于设计文档一次性生成完整的 31 张幻灯片。使用 `deep` category，因为需要理解文章叙事结构、颜色编码语义、neocarbon API，在单一文件中保持一致性。

**任务范围：**
- frontmatter 配置（theme, transition, fonts）
- `<style>` 块（配色变量、动画降级、CJK行高、Mermaid补丁、隐藏导航面板）
- Slides 1-4: 序章（cover, quote, statement, default）
- Slides 5-8: 三年前的布局（section, default（NcLineChart 时间线）, quote, statement）
- Slides 9-13: 微信AI专属卡（section, default, metrics, quote, statement）
- Slides 14-18: 支付宝阿宝（section, default, quote, quote, statement）
- Slides 19-23: 协议层的预谋（section, quote, default, quote, statement）
- Slides 24-27: 三方卡位战（section, comparison, default, statement）
- Slides 28-31: 流量颠覆+结尾（section, default, quote, default（数据来源））

**颜色编码规则（严格执行）：**
- 正面/增长/默会知识 → `nc-text-success`（青色）
- 负面/下降/警示/身份丢失 → `nc-text-danger`（玫红）
- 中性数据强调（如 MAU 14.32亿、27000小程序）→ `nc-text-accent`（紫色）
- 脚注/来源 → `nc-text-muted`（灰色）

**必须使用的布局/组件：**
- `cover`（Slide 1）, `section`（6次）, `quote`（7次）, `statement`（5次）, `comparison`（1次）, `metrics`（1次）, `default`（9次）, `diagram`（0-1次）
- `<NcLineChart />`（Slide 6 时间线）, `<NcBarChart />`（三方MAU对比）
- Mermaid flowchart（协议改造流程，可选）

**CSS 必须包含：**
```css
/* 配色 */
:root {
  --nc-accent: #a855f7;
  --nc-success: #22d3ee;
  --nc-danger: #f43f5e;
  --nc-warning: #fbbf24;
  --nc-info: #818cf8;
}
/* CJK */
.slidev-layout { line-height: 1.75; font-size: 24px; }
svg text { font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important; }
/* 动画降级 - 淡入模式 */
.nc-stagger > * { animation: none !important; opacity: 1 !important; }
.nc-shimmer { animation: none !important; }
.nc-particles { display: none !important; }
/* 隐藏导航面板 - 录屏必加 */
.slidev-sidebar, .slidev-nav, .slidev-slide-nav,
.slidev-navigation, .slidev-toc, .slidev-overview-panel,
aside, nav.slidev-nav,
[class*="sidebar"], [class*="toc"], [class*="navigation"],
#slidev-nav, .slidev-layout-nav { display: none !important; }
```

**数据点对照表（逐条核对）：**
| 数据 | 颜色 | 位置 |
|------|------|------|
| 豆包 MAU 3.45亿 | nc-text-accent | Slide 25 |
| 千问 MAU 1.66亿 | nc-text-accent | Slide 25 |
| 元宝 MAU 5735万 | nc-text-accent | Slide 25 |
| 微信 MAU 14.32亿 | nc-text-accent | Slide 25 |
| 豆包投流 ~4.35亿 | nc-text-accent | Slide 25 |
| 27000+ AI小程序 | nc-text-accent | Slide 29 |
| 个人开发者超七成 | nc-text-danger | Slide 29 |
| "短路化" / "身份归零" | nc-text-danger | Slide 30 |
| "早就开始的换芯" / 战略先行 | nc-text-success | 各章 |

---

### Task 2: slidev build + 本地预览

**Files:**
- Input: `content/ppt/superapp-agentize/slides.md`
- Output: `content/ppt/superapp-agentize/dist/`

- [ ] **Step 1: Build**

```bash
npx slidev build content/ppt/superapp-agentize/slides.md
```
Expected: exit code 0, `dist/` 目录生成

- [ ] **Step 2: 启动本地服务器预览**

```bash
npx serve content/ppt/superapp-agentize/dist -p 3030 --no-clipboard
```
Expected: `http://localhost:3030` 可访问

- [ ] **Step 3: 手动验证（不自动化，需人工）**
  - 浏览器打开 http://localhost:3030
  - 调至 1920×1080，F11 全屏
  - 键盘方向键翻页，确认 31 张幻灯片全部正常渲染
  - 颜色编码检查：正面数据=青色，负面=玫红，中性=紫色
  - Mermaid 图表中文正常显示（无方框）
  - 无导航面板显示
