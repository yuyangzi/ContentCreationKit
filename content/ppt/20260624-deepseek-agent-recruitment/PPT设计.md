# PPT设计：DeepSeek 招不到人——AI人才战争进入下半场

> 源文章：20260624-DeepSeek全球急招Agent人才
> 幻灯片数量：27 张 | 目标观众：泛科技爱好者 | 故事风格：观点输出 | 动画：淡入

---

## 0. 配色预设

**选择：预设 A — 霓虹紫（默认）**

适用场景：前沿科技、AI Agent、赛博朋克话题 — 与本文主题高度契合。

```css
:root {
  --nc-accent:  #a855f7;   /* 紫 → 中性强调、主标题高亮、关键数据 */
  --nc-success: #22d3ee;   /* 青 → 正面数据、上升趋势、默会知识 */
  --nc-danger:  #f43f5e;   /* 玫红 → 负面数据、下降/警示、竞争压力 */
  --nc-warning: #fbbf24;   /* 琥珀 → 保留 */
  --nc-info:    #818cf8;   /* 靛蓝 → 保留 */
}
```

**颜色编码规则**：
| 数据类型 | 颜色 | 文字类 | 图表类 |
|----------|------|--------|--------|
| 增长/正面/优势 | 青 #22d3ee | nc-text-success | #22d3ee |
| 下降/负面/警示 | 玫红 #f43f5e | nc-text-danger | #f43f5e |
| 中性/强调/关键 | 紫 #a855f7 | nc-text-accent | #a855f7 |

---

## 1. 主题配置

- `transition: fade`
- CJK 字体: `PingFang SC, Microsoft YaHei, Noto Sans SC` / `provider: none`
- 幻灯片比例: 16:9 (1920×1080)
- `export.withToc: false`

---

## 2. 动画策略

**档位：淡入（录屏推荐）**

- `transition: fade` — 保留幻灯片间 fade 过渡
- 三段降级 CSS — 禁用 staggered/shimmer/particles 动画
- `<v-clicks>` 逐条淡入正常工作

```css
/* 动画降级：禁用 staggered/shimmer/particles，仅保留 fade */
.slidev-layout [class*="stagger"] { animation: none !important; opacity: 1 !important; }
.slidev-layout [class*="shimmer"] { animation: none !important; opacity: 1 !important; }
.slidev-layout [class*="particle"] { animation: none !important; opacity: 1 !important; }
```

---

## 3. 布局映射表（每张幻灯片）

### 第一章：缺人缺疯了（5 张）

| # | 标题 | 布局 | 核心组件 | 视觉重点 |
|---|------|------|----------|----------|
| 1 | 封面：「DeepSeek 招不到人」 | `cover` | — | 全屏标题 + 副标题 |
| 2 | 开场钩子 | `quote` | — | 超大引号：崔添翼「缺人缺疯了」 |
| 3 | 「三类岗位，全线招人」 | `default` | 三栏 flex 卡片 | 研究员（实习+全职，定义问题）/ 工程师（实习+全职，实现能力）/ 产品经理（全职，连接社区） |
| 4 | 「一个多月没招满」 | `default` | 指标卡 flex 容器 | ~50个岗位 / 笔试+3轮面试 / 连续一个多月 |
| 5 | 「第一章」 | `section` | — | 章节分隔：缺人缺疯了 |

### 第二章：郭达雅出走，Harness才来（5 张）

| # | 标题 | 布局 | 核心组件 | 视觉重点 |
|---|------|------|----------|----------|
| 6 | 「判断走在公司前面」 | `statement` | — | 全屏金句 |
| 7 | 「郭达雅：GRPO发明人」 | `default` | 双栏 flex（左 NcRoiCard + 右文字卡片） | 引用38,000+（指标卡）/ GRPO算法发明人 + 中山大学博士 MSRA联培（文字卡） |
| 8 | 「出走时间线」 | `default` | 自定义 flex 时间线（三节点+箭头） | 2025.10（决定离职）→ 2026.03（正式离开 崔添翼加入）→ 2026.05（组建Harness） |
| 9 | 「五个人的离开」 | `default` | 双栏卡片(3+2) | 五人覆盖四条核心技术线 |
| 10 | 「第二章」 | `section` | — | 章节分隔：出走与到来 |

### 第三章：模型是发动机，Harness才是整车（5 张）

| # | 标题 | 布局 | 核心组件 | 视觉重点 |
|---|------|------|----------|----------|
| 11 | 「Model + Harness = Agent」 | `spotlight` | — | 聚光灯核心公式 |
| 12 | 「Harness 六要素」 | `default` | 双栏卡片(3+3) | 上下文管理/长期记忆/Subagent/自进化/工具调用/MCP |
| 13 | 「发动机 vs 整车」 | `default` | 双栏自定义flex | 类比：模型=发动机 / Harness=整车 |
| 14 | 「三类岗位分工」 | `default` | NcSteps | 研究员→工程师→产品经理→社区 完整链条 |
| 15 | 「第三章」 | `section` | — | 章节分隔：什么是Harness |

### 第四章：外面的世界一周48条（5 张）

| # | 标题 | 布局 | 核心组件 | 视觉重点 |
|---|------|------|----------|----------|
| 16 | 「一周48条」 | `default` | NcRoiCard×3 | 48条/周 / 8x产出 / $9B→$47B |
| 17 | 「Anthropic 的降维打击」 | `default` | NcRoiCard 对比 | Claude Code >7月AI编写 / Fortune "lonely experience" |
| 18 | 「国内三线并进」 | `default` | 三栏卡片 | 微信小微(14亿MAU)/蚂蚁AMP/小米MiMo |
| 19 | 「竞争逻辑变了」 | `default` | 双栏自定义flex | Anthropic vs DeepSeek：基础设施差距 |
| 20 | 「第四章」 | `section` | — | 章节分隔：竞争白热化 |

### 第五章：抢的不是"会写代码的人"（4 张）

| # | 标题 | 布局 | 核心组件 | 视觉重点 |
|---|------|------|----------|----------|
| 21 | 「三种稀缺能力」 | `default` | 三栏卡片 | 研究品味/工程能力/产品思维 三角形架构 |
| 22 | 「大模型时代 vs Agent 时代」 | `default` | 双栏自定义flex | 两个时代的竞争逻辑对比 |
| 23 | 「2023年就想做Agent」 | `default` | 引用卡片 | 郭达雅细节：方向判断走在公司前面 |
| 24 | 「第五章」 | `section` | — | 章节分隔：人才新定义 |

### 结尾（3 张）

| # | 标题 | 布局 | 核心组件 | 视觉重点 |
|---|------|------|----------|----------|
| 25 | 「不是谁会训练，是谁能驯服」 | `statement` | — | 全屏金句 |
| 26 | 「这件事，不是有钱就能快起来的」 | `quote` | — | 收官引用 |
| 27 | 「数据来源」 | `default` | 文字列表 | 13个来源汇总，分一手/二手标注 |

---

## 4. 幻灯片结构总览

```
cover (1) → quote (2) → default×2 (3-4) → section (5)
  → statement (6) → default×2 (7-8) → default (9) → section (10)
  → spotlight (11) → default×2 (12-13) → default (14) → section (15)
  → default×3 (16-18) → default (19) → section (20)
  → default×2 (21-22) → default (23) → section (24)
  → statement (25) → quote (26) → default (27)
```

**布局统计**：
- `cover`: 1
- `section`: 5（每章一个）
- `quote`: 2（开场钩子 + 收官）
- `statement`: 2（金句页×2）
- `spotlight`: 1（核心公式）
- `default`: 16（数据图表、卡片、对比）

**组件使用**：
- NcRoiCard: ×5（Slide 7 人物指标 ×1 / Slide 16 数据指标 ×3 / Slide 17 标杆对比 ×1）
- NcSteps: ×1（Slide 14 岗位流程）
- 自定义 flex 时间线: ×1（Slide 8 出走时间线）
- 双栏/三栏卡片 flex: ×~9（对比、列表、分组、岗位卡片）
- NcTerminal: 不使用（本文无代码/CLI场景）

**Flex gap 规范**：双栏 `gap: 1.5rem`，三栏 `gap: 1.2rem`。所有 flex 容器含 `margin-top: 1.5rem`。

**禁止使用**：
- `comparison` 布局 → 全部改用 `default` + 自定义 flex
- `::metrics::` slot → 全部改用 flex 容器 + nc-metric
- 图表颜色使用 CSS 变量 → 全部使用十六进制值（`#22d3ee`、`#f43f5e`、`#a855f7`）

**数据精确度标注**：
- Slide 18 微信小微 MAU：卡片显示"14.32亿月活"，底部 `nc-text-muted` 小字标注精确值
