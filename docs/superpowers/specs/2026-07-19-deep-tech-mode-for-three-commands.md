# create-draft / to-article / review-article 追加 deep-tech 模式

> 让 3 个核心命令对深度技术分析文做专项优化。  
> deep-tech 模式 = writer-style 技术深读骨架 + 深度分析技巧 + 显式局限性 + 哲学升华。

**日期**: 2026-07-19  
**作者**: Sisyphus  
**状态**: Draft  
**预期落地**: 2026-07-23  
**前置 spec**: 2026-07-19-commands-p0-consistency-fix.md

---

## 1. 目标

| 问题 | 现状 | 修复后 |
|------|------|--------|
| create-draft 缺技术文指引 | 只说加载 3 个 skill,没指定模式 | deep-tech 模式加 5 条必含清单 |
| to-article 润色破坏技术准确性 | 一刀切润色对技术文危险 | 引入 conservative / standard 策略 |
| review-article 详细度不足 | 41 行,远低于 review-draft 111 行 | 升到同等详细度,加 deep-tech 专项检查 |

**用户决策(2026-07-19)**:
- deep-tech 触发: 命令启动时主动询问(交互式)
- to-article 润色: 模式驱动策略切换,deep-tech 强制 conservative
- review-article: 升到 review-draft 同等详细度

---

## 2. deep-tech 模式定义

观察 `content/article/20260719-Kimi-K3.md`(169 行)的实际特征,deep-tech 模式精确定义:

| 维度 | 来源 | 必含元素 |
|------|------|----------|
| 骨架 | writer-style 技术深读 | 引用论文/arXiv、术语解释链、横向对比、章节式结构、参考来源列表 |
| 技巧 | writer-style 深度分析 | 结论先行、设问推进(克制,2-3 处)、观点驱动、留余味结尾 |
| 诚实 | Kimi K3 经验 | 显式局限性节、不能用"全面升级"等绝对词 |
| 升华 | Kimi K3 经验 | 至少一段总结性 insight(技术判断 + 行业判断) |

**与 writer-style 两种模式的关系**: 不是简单选其一,而是融合两者的特定元素。

---

## 3. 改造点 1: create-draft.md

**frontmatter 新增 mode 询问指引**(放在目标段之后):

> 命令启动时,主动询问:「这篇文章是深度技术分析文吗?」  
> 是 → 启用 deep-tech 模式,记录到草稿 frontmatter 的 mode 字段  
> 否 → 默认通用模式

**加载 skill 调整**:

| 模式 | 加载 skill |
|------|-----------|
| 通用 | humanizer + writer-style(默认技术深读) + content-research-writer |
| deep-tech | humanizer + writer-style(技术深读+深度分析融合) + content-research-writer + recursive-research |

**deep-tech 必含清单**(在步骤 4 之后新增步骤 5):

- arXiv 引用: 每个核心机制至少 1 个 arXiv 编号
- 技术对比: 至少 1 个横向对比表
- 术语解释链: 首次出现的专业术语必须括号解释
- 数据/基准: 关键性能数据带来源
- 局限性节: 独立的"局限性"或"权衡"小节
- 参考来源: 文末完整列出 *参考来源* 段

**约束段补充**:
- 必遵守: deep-tech 模式禁止使用"全面升级"等绝对词
- 禁止: 不要在 deep-tech 模式省略局限性节

---

## 4. 改造点 2: to-article.md

**润色策略概念引入**(新增「## 润色策略」段):

| 策略 | 适用 | 改动范围 | 触发 |
|------|------|----------|------|
| conservative | 深度技术文、数据密集文 | 只改衔接/冗余/过渡,不动数据/引用/术语/表格/代码/公式 | deep-tech 模式默认 |
| standard | 评论文、资讯文 | 可调整论证结构、改写段首 | 通用模式默认 |

**frontmatter 新增读取指引**:

> 读取草稿 frontmatter 的 mode 字段(由 create-draft 写入):  
> - mode = deep-tech → 强制 conservative  
> - mode 为空 → 询问用户,默认推荐 standard

**步骤 1 改写**:

旧: 根据审核意见和文章标准,将草稿润色为正式文章。

新: 根据审核意见,按当前润色策略(deep-tech 默认 conservative / 通用默认 standard)润色为正式文章。conservative 模式下,**不得改动**以下元素: 数字、百分号、单位、arXiv 编号、URL、代码块、表格数据、专有名词英文原形、首次出现的术语中文翻译。润色完成后执行"润色影响范围自检"。

**新增步骤 4: 润色影响范围自检**(conservative 模式强制):

1. 列出本次润色改动的所有位置(行号 + 改动前/后)
2. 标记每个改动是否属于"允许范围"
3. 任何超出范围的改动 → 回滚并提示用户
4. 自检通过后再保存

**输出段补充**:

conservative 模式输出: 除正式文章外,**附上润色改动清单** `content/article/{YYYYMMDD}-{主题名}-changes.md`,列出所有改动位置 + 改动前/后,供 review-article 审计。

**模型调整(重要)**:

| 模式 | 模型 |
|------|------|
| conservative | deepseek/deepseek-v4-pro(强制升级) |
| standard | opencode/deepseek-v4-flash-free(保持) |

理由: 当前 flash-free 对技术文润色风险过高,conservative 必须升 Pro。

**约束段补充**:
- 必遵守: conservative 模式不得改动数据/引用/术语/表格
- 禁止: 不要为追求"文笔流畅"重写技术表述

---

## 5. 改造点 3: review-article.md

**目标段重写**:

旧: 审核文章中的内容和数据是否正确且是最新。

新: 模仿 review-draft 的逐条检查结构,对文章进行 6 个 StyleRule 维度 + 1 个 deep-tech 专项检查 + 1 个综合段,产出可执行的修改清单。

**模型调整(重要)**:

- 升级到 `deepseek/deepseek-v4-pro`(与 review-draft 一致)
- 支持 team_mode 并行: deep-tech 模式默认 3 个并行 librarian:
  - librarian-1: 架构机制准确性(arXiv 编号、技术细节、对比表)
  - librarian-2: 商业数据时效性(价格、融资、估值、市值)
  - librarian-3: 叙事张力(逻辑、过渡、哲学升华、局限性诚实)
- 通用模式保持单 librarian 或 2 个 librarian

**步骤从 2 步扩展为 8 步**:

步骤 1-6 依次为 StyleRule §1-§6 逐条检查(继承 review-draft 模式),每项含原文位置 + 例证 + 通过/需修改。

**步骤 7: deep-tech 专项检查**(deep-tech 模式强制):

- arXiv 编号准确性: 可在 arxiv.org 检索到,标题匹配
- 技术对比公平性: 不抬高自家贬低对手
- 哲学升华空洞性: 不空喊口号,有具体技术判断
- 局限性诚实度: 显式承认短板,不回避核心争议
- 术语精确性: 中文翻译准确,英文原形保留
- 参考来源完整性: 文末 *参考来源* 段,链接有效
- 数据/基准可追溯: 关键数字首次出现标源

**步骤 8: 综合检查**(继承 review-draft):

- 数据真实性未过时
- 上下文结构合理,前后逻辑正确
- 给具体位置 + 例证

**输出段重写**:

旧: 审核结果清单,每项检查附带具体例证。

新: 8 个检查节按顺序呈现,每项附"通过 / 需修改 / N/A"。需修改项必须给具体位置(行号或引用)+ 例证 + 建议改法。最终附 1 段"修改优先级清单",按"必须改 / 建议改 / 可选改"三档分类。

**约束段补充**:
- 必遵守: deep-tech 模式必须完成步骤 7 的所有 7 个子项
- 必遵守: 8 个检查节不能跳过
- 禁止: 不要笼统说"已通过",必须给具体判断

---

## 6. team_mode 集成的具体实现

**当前 oh-my-openagent.json 配置**: team_mode.enabled=true, max_parallel_members=4, librarian 模型 opencode/deepseek-v4-flash-free。

**deep-tech 模式行为**: review-article 阶段默认启用 3 个并行 librarian,每个加载不同 prompt context(见 §5)。综合结果由主对话 agent 汇总。**不修改** oh-my-openagent.json 配置(保留可配置性)。

**通用模式行为**: 保持单 librarian 或 2 个 librarian(与现状一致)。

---

## 7. 验证

**文件存在与 frontmatter**:
```bash
head -3 .opencode/commands/create-draft.md    # 期望 description、model
head -3 .opencode/commands/to-article.md      # 期望 description、model  
head -3 .opencode/commands/review-article.md  # 期望 description、model
```

**deep-tech 必含清单检查**:
```bash
grep -c "deep-tech" .opencode/commands/create-draft.md    # 期望 ≥3
grep -c "conservative" .opencode/commands/to-article.md  # 期望 ≥3
grep -c "步骤 7" .opencode/commands/review-article.md     # 期望 ≥1
```

**模型升级检查**:
```bash
grep "deepseek-v4-pro" .opencode/commands/review-article.md  # 期望 ≥1
grep "deepseek-v4-pro" .opencode/commands/to-article.md      # 期望 ≥1
```

**行数提升**:
```bash
wc -l .opencode/commands/review-article.md  # 期望 ≥100(原 41 行)
```

---

## 8. 影响文件清单

| 文件 | 改动 |
|------|------|
| `.opencode/commands/create-draft.md` | 加 mode 询问 + deep-tech 必含清单 + 4 个 skill 强制 |
| `.opencode/commands/to-article.md` | 加润色策略 + 步骤 4 自检 + 模型按模式切换 |
| `.opencode/commands/review-article.md` | 全面重写,8 步检查 + team_mode 并行 |

**总改动**: 3 个文件,核心命令重写级别。

---

## 9. 风险与回滚

**风险**: 中。to-article 模型升级到 Pro 会**增加 API 成本**(deep-tech 模式每篇文章多约 30-50% token)。review-article team_mode 并行也会增加 librarian 调用次数。

**潜在副作用**:
- deep-tech 模式如果误判,所有规则强制开启会让简单技术博客过度形式化
- to-article 改动清单 -changes.md 会在 archive 时需要单独处理

**回滚方案**: git revert 3 个文件的 commit 即可。

---

## 10. 不在本 spec 范围

明确排除:

- P0 commands 一致性修复(独立 spec)
- P2 merge-topics / archive-topic(独立 spec)
- P3 commands 详细度模板(通用结构改造,与 deep-tech 正交)
- writer-style skill 自身的 deep-tech 模式定义(本 spec 在 commands 层指引,writer-style skill 文件本身不动)
- 自定义 deep-tech agent 类型(不修改 oh-my-openagent.json)
