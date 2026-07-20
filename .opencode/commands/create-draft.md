---
description: 创建草稿
model: deepseek/deepseek-v4-pro
---

# 创建草稿

## 目标

基于确认的主题和参考资料，生成一篇以中文为主、自然耐读的文章草稿。支持 **deep-tech 模式**（深度技术分析文专项）。

## 模式询问（命令启动时）

命令启动时，**主动询问用户**：

> 「这篇文章是深度技术分析文吗？」

- **是** → 启用 deep-tech 模式，记录到草稿 frontmatter 的 `mode: deep-tech` 字段
- **否** → 默认通用模式，记录 `mode: standard`（或省略）

用户选择会被 `to-article` / `review-article` 阶段读取以决定润色策略与检查项。

## 前置条件

已完成 `/review-reference`，参考资料已确认

## 输入

- 确认的创作主题
- `content/reference/` 目录下的参考文件
- 上下文会话中讨论的创作方向

## 加载 Skill（强制）

| 模式 | 加载 skill |
|------|------------|
| **通用**（mode = standard） | `humanizer` + `writer-style`（默认技术深读模式）+ `content-research-writer` |
| **deep-tech**（mode = deep-tech） | `humanizer` + `writer-style`（**技术深读 + 深度分析融合模式**）+ `content-research-writer` + `recursive-research` |

## 步骤

1. 总结上下文信息，读取用户提供的文件内容
2. 加载对应模式下的 skill（见上表）
3. 确保草稿数据真实可追溯，不使用待核实的数据和引用
4. 生成中文文章草稿
5. **【deep-tech 模式】必含清单**（见下节）
6. 以 `{YYYYMMDD}-{主题名}.md` 的文件名保存到 `content/draft/` 目录

## deep-tech 模式必含清单

启用 deep-tech 模式时，生成的草稿**必须包含**以下 6 项元素（缺一项即视为不合格）：

- [ ] **arXiv 引用**：每个核心机制至少 1 个 arXiv 编号（如 `arXiv 2603.15031`）
- [ ] **技术对比**：至少 1 个横向对比表（自家 vs 同行 / 旧版 vs 新版 / 论文方法 A vs 论文方法 B）
- [ ] **术语解释链**：首次出现的专业术语必须括号解释或上下文注释（如 "AttnRes（Attention Residuals，注意力残差）"）
- [ ] **数据/基准**：关键性能数据带来源（官方博客 / 独立测评 / 论文 / arXiv 摘要）
- [ ] **局限性节**：必须有独立的"局限性"、"权衡"或"尚未解决"小节，显式承认短板
- [ ] **参考来源**：文末完整列出 `*参考来源：*` 段（链接、标题、发布方、日期）

deep-tech 模式 = **writer-style 技术深读骨架** + **深度分析技巧**（结论先行、设问推进、留余味结尾）+ **显式局限性** + **哲学升华**（至少一段总结性 insight）。

## 输出

- `content/draft/{YYYYMMDD}-{主题名}.md`：完整的文章草稿文件
- 草稿 frontmatter 包含 `mode` 字段（`deep-tech` 或 `standard`），供后续阶段读取

## 约束

**必须遵守：**

- 草稿在正式和口语之间取得平衡，避免 AI 腔
- 不使用未完全核实的数据和引用
- **deep-tech 模式**：禁止使用"全面升级"、"完美解决"、"彻底击败"等绝对词
- **deep-tech 模式**：禁止省略局限性节
- **deep-tech 模式**：每个核心机制必须有 arXiv 编号或同等强度的论文/官方博客引用

**禁止操作：**

- 不要编造案例、数据或引用来源
- 不要使用模板化的连接词结构（首先/其次/最后/综上所述）
- **deep-tech 模式**：不要为追求"文笔流畅"弱化技术细节
- **deep-tech 模式**：不要把"局限性节"写成辩护式说明（"虽然...但..."句式堆叠）
