# Commands P0 一致性修复

> 修 3 个 P0 一致性 bug,让 commands 体系内部完全统一。  
> 范围：纯文档层，不动现有 40+ 个文件名。

**日期**: 2026-07-19  
**作者**: Sisyphus  
**状态**: Draft  
**预期落地**: 2026-07-20

---

## 1. 目标

| Bug | 现状 | 修复后 |
|-----|------|--------|
| **#1 StyleRule 数量** | 主体 5 条,但 3 处文档说 6 类高频违规 | 升级主体为 6 条 |
| **#2 commands 时间戳占位符** | 4 个 commands 用 `{时间戳}-{主题名}.md` 占位符 | 统一为 `{YYYYMMDD}-{主题名}.md` |
| **#3 reference 命名空间** | reference 输出后缀混乱(无后缀 / `-审核记录` 混用) | 新文件用 `-v{N}.md` 后缀 |

**用户决策(2026-07-19)**:  
- Bug #1: 把「破折号打断」从 §4 抽出来升级为独立 §6  
- Bug #2/#3: 只改 commands 规范文本,不动现有文件名

---

## 2. 现状证据

### 2.1 StyleRule 数量描述

| 文件 | 行 | 描述 |
|------|----|------|
| `StyleRule.md` | 全文 | 5 条主体(§1-§5) |
| `AGENTS.md` | 84-92 | 列 5 条 |
| `AGENTS.md` | 122-130 | 6 类高频违规(其中「破折号过载」与 StyleRule §4 子项重复) |
| `README.md` | 32 | 6 类高频违规 |
| `README.md` | 48 | 6 条 |
| `README.md` | 282 | 列 5 条(与第 48 行冲突) |
| `review-draft.md` | 全文 | 5 个检查节 |

### 2.2 `{时间戳}` 占位符(共 8 处)

| 文件 | 行 |
|------|-----|
| `to-article.md` | 25, 29 |
| `review-topics.md` | 25, 41 |
| `create-draft.md` | 28, 32 |
| `to-wechat.md` | 31, 42, 43, 44 |

历史决策:`docs/superpowers/plans/2026-06-21-find-popular-topics-optimization.md` 第 28 行已规定 `{YYYYMMDD}-{中文主题名}.md`,但只改了 `find-popular-topics.md`,其他 4 个 commands 遗漏。

### 2.3 reference 文件命名(实际观察)

```
content/reference/20260716-AI短剧泡沫破裂前夜-审核记录.md
content/reference/20260719-AI内容治理范式转换-审核记录.md
content/reference/20260719-Kimi-K3.md
content/reference/20260718-Agent-Loop工程.md
```

`-审核记录` 后缀与无后缀混用,无法区分「参考资料」与「修正记录」。

---

## 3. 改动清单

### 改动 A:StyleRule 升级到 6 条

#### A1. `StyleRule.md`

- 删除 §4 行 69-70 的「破折号打断」子项
- 在 §5 之后新增 §6 破折号约束(核心:一段最多 1 处破折号打断)

```markdown
---

## 6. 破折号约束

**核心原则**:深度技术分析等长文中,**一个段落最多出现一处破折号打断**。超过即「破折号过载」,破坏阅读节奏。

**判断标准**:
- 3-5 行短段落 → 0 处破折号为最佳
- 超过 6 行长段落 → 最多 1 处
- 超过 1 处 → 改用括号 `(XX)` 安静补充,或重新断句

**典型**:
- ❌ `K2 世代——K2、K2.5、K2.6——共享同一架构——1 万亿参数`(3 处打断)
- ✅ `K2 世代(K2、K2.5、K2.6)共享同一架构,1 万亿参数`
```

#### A2. `review-draft.md`

- 标题「StyleRule 五条规则」→「StyleRule 六条规则」(行 10)
- 在 §5 列表化之后、§6 综合检查之前,新增 §6 破折号约束检查清单
- 原 §6 综合检查 → §7 综合检查

```markdown
### 6. 破折号约束 (StyleRule §6)

**核心**:一段最多一处破折号打断。超过即「破折号过载」。

逐项检查:
- [ ] **单段破折号数**:单段 `——XX——` 不超过 1 处
- [ ] **括号替代**:能用 `(XX)` 安静补充时不强行用破折号
- [ ] **断句重写**:超过 1 处改为重新断句或拆分
- [ ] **判断标准**:从段首读到段尾被破折号打断超过 1 次?重写。
```

#### A3. `AGENTS.md`

- 行 84-92 的 5 条列表新增第 6 条「破折号约束」
- 行 122 章节开头加一句说明:「破折号过载」已升级为 §6 主体规则
- 行 129「破折号过载」项加注释指向 StyleRule §6

#### A4. `README.md`

- 行 32「6 类高频违规」→「6 条核心规则」
- 行 142 同上
- 行 282 列出的 5 条 → 6 条(新增「破折号约束」)

### 改动 B:commands `{时间戳}` 占位符替换

8 处精确文本替换 `{时间戳}-{主题名}.md` → `{YYYYMMDD}-{主题名}.md`:

| 文件 | 行 | 操作 |
|------|----|------|
| `to-article.md` | 25, 29 | 替换 |
| `review-topics.md` | 25, 41 | 替换 |
| `create-draft.md` | 28, 32 | 替换 |
| `to-wechat.md` | 31, 42, 43, 44 | 替换 |

注:`{文章名}` 与 `{主题名}` 同义,统一为 `{主题名}`。

### 改动 C:reference 命名规范

#### C1. `review-topics.md` 输出约定

行 25「文件名为 `{YYYYMMDD}-{主题名}.md`」 → 「文件名为 `{YYYYMMDD}-{主题名}-v1.md`(N=1,2,3...)」。

新增「reference 命名空间说明」段(放在步骤 4 之后):

```markdown
**reference 命名空间说明**:
- `review-topics` 输出 → `{YYYYMMDD}-{主题名}-v1.md`(初次审核问答)
- `review-reference` 输出 → 同名文件,版本号升级为 `-v2.md`、`-v3.md`...
- 老文件(`-审核记录` 后缀)保留不动,不强制迁移
```

#### C2. `review-reference.md` 输出约定

行 28-30 现有「修正意见清单」输出 + 步骤 4「经确认后可更新 reference/ 下的资料文件」,**明确说明**经用户确认后用 `-v{N+1}.md` 命名,原 `-v{N}.md` 保留。

---

## 4. 验证

实施完成后运行以下检查:

```bash
# Bug #1 验证:StyleRule 数量一致性
grep -c "^## [0-9]" StyleRule.md     # 期望 6
grep "六条" review-draft.md          # 期望 ≥1
grep "六条" README.md                 # 期望 ≥1

# Bug #2 验证:commands 占位符统一
grep -r "{时间戳}" .opencode/commands/  # 期望 0 行
grep -r "{YYYYMMDD}" .opencode/commands/  # 期望 8+ 行

# Bug #3 验证:reference 命名说明
grep "{YYYYMMDD}-{主题名}-v1" review-topics.md  # 期望 ≥1
grep "{YYYYMMDD}-{主题名}-v{N+1}" review-reference.md  # 期望 ≥1
```

---

## 5. 影响文件清单

| 文件 | 改动类型 |
|------|---------|
| `StyleRule.md` | 升级到 6 条 |
| `AGENTS.md` | 同步列表到 6 条 + 加注释 |
| `README.md` | 同步描述到 6 条 |
| `review-draft.md` | 章节从 5 节增到 6 节 |
| `to-article.md` | 占位符 2 处替换 |
| `review-topics.md` | 占位符 2 处替换 + reference 命名说明 |
| `create-draft.md` | 占位符 2 处替换 |
| `to-wechat.md` | 占位符 4 处替换 |
| `review-reference.md` | reference 输出命名约定 |

**不动**:
- 现有 40+ 个文件名(用户决策)
- `oh-my-openagent.json`
- `opencode.jsonc.bak`
- 内容文件

---

## 6. 风险与回滚

**风险**:极低,纯文档层。不影响运行时行为,不影响 git history。

**回滚**:`git revert <commit-hash>` 即可,9 个文件改动可一次性 revert。

**潜在副作用**:
- 升级到 6 条 StyleRule 后,`review-draft` 命令输出会变长(每个审核周期多 1 节检查)
- commands 占位符替换后,LLM 读取 prompts 时理解的命名空间更明确(正向影响)

---

## 7. 后续工作(本 spec 不包含)

- P1 深度技术文专项(create-draft / to-article / review-article 加 deep-tech mode)
- P2 合并/归档命令(/merge-topics / /archive-topic 新增)
- P3 commands 详细度模板(建立标准结构)
- P4 模型重新分配(to-article / review-article 升到 Pro)
