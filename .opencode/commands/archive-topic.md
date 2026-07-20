---
description: 归档过期或已被替代的 topic 文件
model: opencode/deepseek-v4-flash-free
---

# 归档主题

## 目标

将过期或已被替代的 topic 文件移动到 `content/topics/archive/` 子目录,从主话题池中排除,避免 `/find-popular-topics` 重复发现。

## 前置条件

- 待归档的 topic 文件存在于 `content/topics/`(不在 archive/ 内)
- 用户确认归档原因

## 输入

支持三种模式:

### 模式 1:单文件归档(默认)

```bash
/archive-topic content/topics/20260629-AI模型量价螺旋-...md
```

### 模式 2:批量归档(--batch)

```bash
/archive-topic --batch content/topics/20260629-*.md content/topics/20260718-Agent-*.md
```

### 模式 3:自动扫描候选(--auto)

```bash
/archive-topic --auto
```

扫描规则:有对应 article 且 article 文件超过 30 天的 topic,作为候选列出,等用户挑选。

## 步骤

### 1. 输入解析

- 解析命令行参数,确定模式(单文件 / --batch / --auto)
- 验证文件路径合法

### 2. 归档前检查

对每个待归档文件执行:

- [ ] 文件存在于 `content/topics/`
- [ ] 文件**不在** `content/topics/archive/`(避免重复归档)
- [ ] 文件名匹配 `{YYYYMMDD}-{主题名}.md` 格式
- 任一检查失败则跳过该文件,记录到「跳过清单」

### 3. 对应 article 检查(可选提示)

- 扫描 `content/article/` 目录,查找与待归档 topic 对应的 article
- 如果找到对应 article(文件名匹配 topic 名),记录对应关系
- 如果**没有**对应 article,提示用户:「该 topic 没有对应 article,确认归档?」

### 4. 展示待归档清单

向用户展示以下信息(等待用户确认):

| 字段 | 内容 |
|------|------|
| 待归档文件数 | N 个 |
| 文件列表 | 每个文件的路径 + 是否有关联 article |
| 跳过文件 | 检查失败的文件列表及原因 |
| 目标目录 | `content/topics/archive/` |

### 5. 执行归档(用户确认后)

按以下顺序操作:

1. **移动文件**:`git mv` 每个待归档文件到 `content/topics/archive/`
2. **验证**:`ls content/topics/archive/` 确认所有文件已就位
3. **git status 检查**:`git status` 应显示 N 个 rename 而非 delete + add

### 6. 提示后续影响

- 提示用户:「归档完成。这 N 个 topic 已从 `/find-popular-topics` 的候选池中排除」
- 如果是 --auto 模式,提示:「下次执行 `/find-popular-topics` 时,这些归档文件将作为负样本,不再被推荐」

## 输出

- 归档后的文件位于 `content/topics/archive/`
- git status 显示 N 个 rename 操作

## 约束

**必须遵守**:

- 移动文件必须用 `git mv` 而非 `mv + git add`,保留 rename 关系(git 不会丢失历史)
- 归档前必须用户确认(展示清单后等待)
- --auto 模式只列出候选,不自动归档
- 归档后文件**保留在 archive/**,不删除(支持手动恢复)

**禁止操作**:

- 不要归档 `content/topics/archive/` 内的文件(已是归档状态)
- 不要在 --auto 模式自动执行归档
- 不要修改归档文件的内容
- 不要同步删除对应的 article / reference 文件
