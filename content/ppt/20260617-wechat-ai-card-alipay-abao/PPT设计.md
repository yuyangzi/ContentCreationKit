# PPT设计：微信AI专属卡、支付宝阿宝与超级App的Agent化

## 0. 配色预设

**选择：霓虹紫（预设 A）** — 前言科技/AI Agent/赛博朋克话题，与文章调性完全吻合。

```css
:root {
  --nc-accent:  #a855f7;   /* 紫 → 中性强调、主标题高亮 */
  --nc-success: #22d3ee;   /* 青 → 正面数据、上升/优势 */
  --nc-danger:  #f43f5e;   /* 玫红 → 负面数据、下降/警示 */
  --nc-warning: #fbbf24;   /* 琥珀 → 保留 */
  --nc-info:    #818cf8;   /* 靛蓝 → 保留 */
}
```

颜色编码规则：
- 增长/正面/优势 → `nc-text-success`（青）
- 下降/负面/短板 → `nc-text-danger`（玫红）
- 中性强调/关键数据 → `nc-text-accent`（紫）
- 辅助说明/脚注 → `nc-text-muted`（灰）

---

## 1. 主题配置

| 维度 | 值 |
|------|-----|
| 主题 | `@enyineer/slidev-theme-neocarbon` |
| 过渡动画 | `transition: fade` |
| 动画策略 | **降级（仅 fade）**：禁用 staggered/shimmer/particles |
| CJK字体 | `PingFang SC, Microsoft YaHei, Noto Sans SC` |
| 字体provider | `none` |
| TOC | 禁用（`export.withToc: false` + CSS隐藏） |

---

## 2. 布局映射表

| # | 内容类型 | neocarbon布局 | 说明 |
|---|----------|--------------|------|
| 1 | 封面 | `cover` | "微信AI专属卡、支付宝阿宝与超级App的Agent化" |
| 2 | 开场叙事反差 | `quote` | 引用媒体叙事 → 抛出反向观点 |
| 3/6/11/15/20/26 | 章节分隔 | `section` | 5章 + 结尾章标题 |
| 4 | 时间线三列 | `default` + Mermaid | 2023年腾讯/阿里/字节时间线 |
| 5/10/19/25 | 核心判断/金句 | `statement` | 每章的核心观点提炼 |
| 7 | 微信专属卡4特征 | `default` + `<NcSteps />` | 4步产品特征流程 |
| 8/12/21 | 左右概念对比 | `comparison` | 直接授权vs专属卡 / 阿宝vs资产 / 旧流量vs新流量 |
| 9 | 安全架构三层 | `default` + Mermaid | 主账户隔离→余额控制→支付确认 |
| 13 | 官方原话引用 | `quote` | "管钱不交给AI" |
| 14 | 双重动机分析 | `default` | 合规+品牌两段文字 |
| 16 | 5大技术限制 | `default` + `<NcSteps />` | Skill改造要求 |
| 17 | 关键规则引用 | `quote` | "文字链引回原页面...用多了会降权" |
| 18 | 小程序vs Skill时代 | `comparison` | 两列对比 |
| 22 | 三方MAU柱状图 | `default` + `<NcBarChart />` | 豆包3.45亿/千问1.66亿/元宝5735万 |
| 23 | 优劣势矩阵 | `default` | 三列文字对比表 |
| 24 | 三方战略路径 | `default` + Mermaid | 流程图 |
| 27 | 27000+数据指标 | `metrics` | AI小程序数量+个人开发者占比 |
| 28 | 外部评价引用 | `quote` | 网易订阅"一场比小程序更大的收编" |
| 30 | 结尾高潮金句 | `spotlight` | 聚光灯强调核心结论 |
| 31 | 数据来源 | `default` | 参考来源列表 |

---

## 3. 幻灯片结构（31张）

### 封面（1张）
| # | 布局 | 内容 |
|---|------|------|
| 1 | cover | **标题**：微信AI专属卡、支付宝阿宝与超级App的Agent化<br>**副标题**：一场2023年就已开始的"主动换芯" |

### 引子（1张）
| # | 布局 | 内容 |
|---|------|------|
| 2 | quote | > 媒体把这两件事并称为"反击豆包"。但我把过去三年的Time line摊开比对之后，得到的判断完全相反。<br>— 这不是反击，是换芯 |

### 第一章 · 三年前的布局（3张）
| # | 布局 | 内容 |
|---|------|------|
| 3 | section | 第一章 · 三年前那场没被注意的会议 |
| 4 | default + Mermaid | 2023年时间线：阿里云峰会通义千问（4月）→ 马化腾"几百年不遇的工业革命"（5月）→ 支付宝内部"如何走向智能化"会议（下半年） |
| 5 | statement | 腾讯和阿里对AI的投入与转型，早就已经开始。产品是预先架构好的，到时间点拿出来而已。 |

### 第二章 · 微信AI专属卡（4张）
| # | 布局 | 内容 |
|---|------|------|
| 6 | section | 第二章 · 微信AI专属卡：先搭架构，再出产品 |
| 7 | default + NcSteps | 4步产品特征：① 子账户完全隔离 ② 充多少花多少 ③ 三道安全机制 ④ 随时暂停提现 |
| 8 | comparison | ::left:: 简单做法：直接授权AI调主账户<br>::right:: 微信做法：单独开卡、单独转钱、单独管理、笔笔确认 |
| 9 | default + Mermaid | 安全机制三层架构图：主账户隔离 → 余额自主控制 → 每笔支付确认 |
| 10 | statement | 微信在给AI划一块"保留地"。保留地里AI可以跑、可以花钱；保留地外，主账户不动、人格不让。|

### 第三章 · 支付宝阿宝（4张）
| # | 布局 | 内容 |
|---|------|------|
| 11 | section | 第三章 · 支付宝阿宝：把"管钱"明确踢出AI范围 |
| 12 | comparison | ::left:: 阿宝Tab：对话助手 + 调用上万种服务<br>::right:: 资产Tab：独立账本 + 用户完全掌控 |
| 13 | quote | > "管钱"这件事，支付宝没有交给AI，而是用一个独立的"资产"页面呈现给用户。<br>— 上证报中国证券网 |
| 14 | default | 双重动机：<br>🛡️ 合规：支付宝在监管视野里分量更重，资金管理权不能交AI模型决策<br>🏦 品牌：二十年"放心存钱"心智是护城河，不能为追AI风口动摇 |

### 第四章 · Skill协议（5张）
| # | 布局 | 内容 |
|---|------|------|
| 15 | section | 第四章 · 小程序变Skill：协议层的预谋 |
| 16 | default + NcSteps | 5大改造要求：① SKILL分包independent:true ② mcp.json≤24KB ③ SKILL.md≤16KB ④ 原子接口隔离运行 ⑤ 原子组件不滚动 |
| 17 | quote | > 文字链引回原页面，被定义为"兜底手段，用多了会降权"。<br>— 微信开放文档（翻译版） |
| 18 | comparison | ::left:: 小程序时代：开发者做产品，用户找服务<br>::right:: Skill时代：开发者供能力，AI安排服务 |
| 19 | statement | 微信主动把服务闭环留在AI对话里。开发者从"做产品的人"变成"提供能力的供应商"。 |

### 第五章 · 三方卡位战（5张）
| # | 布局 | 内容 |
|---|------|------|
| 20 | section | 第五章 · 三方卡位战：各有底牌，各有短板 |
| 21 | default + NcBarChart | 三方MAU对比：豆包 3.45亿（青=最高）/ 千问 1.66亿（紫=中性）/ 元宝 5735万（紫=中性，距豆包约6倍差距） |
| 22 | default | 三列矩阵：<br>字节：流量最强 / 缺支付·缺社交<br>阿里：生态最强 / MAU约豆包一半<br>腾讯：关系链最强 / AI助手晚起步 |
| 23 | comparison | ::left:: 过去：人找服务 — 用户搜App打开用<br>::right:: 现在：AI安排服务 — 用户说话AI调Skill |
| 24 | default + Mermaid | 三方战略路径对比图 |
| 25 | statement | 三家都不是被动反应，而是各自基于自己的位置在主动卡位。豆包是攻方，腾讯阿里是守方加攻方。 |

### 第五章补充（生态冲击，3张）
| # | 布局 | 内容 |
|---|------|------|
| 26 | default | **第五章（续）· 流量规则的颠覆**<br>过去十年的小程序逻辑：人找服务<br>Skill协议：AI安排服务 — 开发者第一次失去"被用户主动选中"的环节 |
| 27 | metrics | 27000+ AI小程序加入「成长计划」<br>个人开发者占比超七成 |
| 28 | quote | > 一场比小程序更大的"收编"。<br>— 网易订阅 2026.6.12 |

### 结尾（3张）
| # | 布局 | 内容 |
|---|------|------|
| 29 | section | 结尾 · 被换的"芯"不是技术，是身份 |
| 30 | spotlight | 换芯不是App自己换，是App加上它生态里的所有开发者一起换。<br><span style="color: var(--nc-danger)">但开发者没有投票权。</span> |
| 31 | default | 数据来源：新浪科技/财联社/晚点LatePost/IT之家/智东西/经济观察报/36氪/虎嗅/QuestMobile/AppGrowing 等14个来源交叉验证 |

---

## 4. 实施注意事项

### NcBarChart 数值归一化（幻灯片 21）

原始 MAU 数值达亿级，柱状图 Y 轴需归一化。采用百万单位：

```html
<NcBarChart
  title="三方AI助手 MAU 对比"
  :labels="['豆包 3.45亿', '千问 1.66亿', '元宝 5735万']"
  :data="[345, 166, 57.35]"
  :colors="['var(--nc-success)', 'var(--nc-accent)', 'var(--nc-accent)']"
  height="300"
/>
```

颜色编码：豆包=正面(success)，千问=中性(accent)，元宝=中性(accent)

### CSS 必须项（`<style>` 块中）

1. **CJK 行高**：`.slidev-layout { line-height: 1.75; font-size: 24px; }`
2. **default 布局居中**：`.slidev-layout.default { display: flex !important; flex-direction: column !important; justify-content: center !important; padding: 3rem 4rem !important; }`
3. **Mermaid 中文补丁**：`svg text { font-family: 'PingFang SC','Microsoft YaHei',sans-serif !important; }`
4. **动画降级**：禁用 staggered/shimmer/particles（B站录屏）
5. **TOC 隐藏**：`#slidev-toc, .slidev-toc, .slidev-toc-list, .toc, .toc-overlay, [class*="toc"], [id*="slidev-toc"] { display: none !important; }`

### 幻灯片 22 三列布局

neocarbon 无原生三列布局。使用 `default` + flexbox：

```html
<div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 2rem;">
  <div>
    <h3 style="color: var(--nc-success)">字节豆包</h3>
    <p>流量最强（MAU 3.45亿）<br>缺支付 · 缺社交</p>
  </div>
  <div>
    <h3 style="color: var(--nc-accent)">阿里千问</h3>
    <p>生态最强（打通闭环）<br>MAU约豆包一半</p>
  </div>
  <div>
    <h3 style="color: var(--nc-accent)">腾讯微信</h3>
    <p>关系链最强（MAU 14.32亿）<br>AI助手晚起步</p>
  </div>
</div>
```

---

## 5. 动画配置

选择 **淡入降级** 档位：

- `transition: fade`（frontmatter）
- CSS 降级：禁用 staggered/shimmer/particles
- 使用 `<v-clicks>` 控制列表逐条出现

```css
/* 动画降级 CSS（B站录屏清理） */
.neon-stagger > * { animation: none !important; opacity: 1 !important; }
.shimmer, .shimmer-text, [class*="shimmer"] { animation: none !important; background: none !important; }
.particles, .particle, [class*="particle"] { display: none !important; }
```

---

## 5. 确认清单

- [x] 配色：霓虹紫（预设A）
- [x] 动画：仅fade过渡
- [x] 幻灯片：31张（25-35档位内）
- [x] 目标观众：泛科技爱好者
- [x] 故事风格：观点输出为主
- [x] 布局映射：8种布局覆盖31张幻灯片
- [x] 数据来源：14个来源交叉验证
