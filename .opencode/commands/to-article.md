---
description: 草稿转文章
model: opencode/deepseek-v4-flash-free
---

# 草稿转文章

## 目标

将审核通过的草稿润色为结构完整、可发布的正式文章，并生成多个标题供选择。**润色策略**根据草稿的 `mode` 字段（`deep-tech` / `standard`）自动选择。

## 润色策略

读取草稿 frontmatter 的 `mode` 字段，决定润色策略：

| 模式 | 策略 | 适用 | 改动范围 | 触发模型 |
|------|------|------|----------|----------|
| `deep-tech` | **conservative**（保守） | 深度技术文、数据密集文 | 只改衔接、删冗余、补过渡。**不动**：数据、引用、术语、表格、代码、公式、技术表述 | `deepseek/deepseek-v4-pro`（强制升级） |
| `standard` 或缺失 | **standard**（标准） | 评论文、资讯文、行业分析 | 可调整论证结构、改写段首、调整过渡。可改写但不改事实 | `opencode/deepseek-v4-flash-free` |

如果 mode 字段缺失或为 `standard`，**主动询问用户**选择策略（默认推荐 `standard`）。

## 前置条件

已完成 `/review-draft`，草稿已通过审核

## 输入

- `content/draft/` 目录下的草稿文件（含 frontmatter 的 `mode` 字段）
- 审核意见（如有修改要求）

## 步骤

1. **读取草稿 frontmatter 的 `mode` 字段**，确定润色策略（conservative / standard）
2. 根据审核意见，按当前润色策略润色为正式文章
3. 结合文章内容，给出 3 个爆款标题供用户选择
4. **【conservative 模式强制】润色影响范围自检**
5. 以 `{YYYYMMDD}-{主题名}.md` 的文件名保存到 `content/article/` 目录

### 步骤 4: 润色影响范围自检（conservative 模式强制）

执行 conservative 润色后，**必须**自检以下"不得改动"的元素：

- 数字（百分号、金额、参数量、性能指标）
- 单位（GB、TB、ms、token 等）
- arXiv 编号、URL、DOI
- 代码块（含注释、变量名）
- 表格数据
- 专有名词英文原形（如 MoE、MLA、Muon）
- 首次出现的术语中文翻译

自检流程：

1. 列出本次润色改动的所有具体位置（行号 + 改动前/后）
2. 标记每个改动是否属于"允许范围"（衔接 / 冗余 / 过渡）
3. 如果有任何改动超出允许范围，**回滚该改动**并提示用户
4. 自检通过后再保存到 `content/article/`

## 输出

- `content/article/{YYYYMMDD}-{主题名}.md`：正式文章文件
- 3 个候选标题（在对话中呈现）
- **【conservative 模式】** `content/article/{YYYYMMDD}-{主题名}-changes.md`：润色改动清单，列出所有改动位置 + 改动前/后，供 `review-article` 阶段审计

## 约束

**必须遵守：**

- 标题有吸引力但不过度夸张，符合文章实际内容
- 文章结构完整：引人入胜的开头、有层次的主体、有力的结尾
- **conservative 模式**：不得改动数据 / 引用 / 术语 / 表格 / 代码 / 公式
- **conservative 模式**：必须执行步骤 4 的"润色影响范围自检"
- **conservative 模式**：必须输出 `-changes.md` 改动清单

**禁止操作：**

- 不要使用震惊体、标题党
- 不要使用行业黑话
- 不要新增未经审核的数据和引用
- **conservative 模式**：不要为追求"文笔流畅"重写技术表述
- **conservative 模式**：不要跳过步骤 4 的自检
