---
description: 合并多个高度重叠的 topic 文件
model: deepseek/deepseek-v4-pro
---

# 合并主题

## 目标

将 2 个或以上内容高度重叠的 topic 文件合并为一个,消除重复创作,形成统一主线。

## 前置条件

- 已完成 `/find-popular-topics`,`content/topics/` 目录有 ≥2 个待合并的 topic 文件
- 所有待合并文件**不在** `content/topics/archive/` 内(归档文件不能被合并)

## 输入

- 用户指定的 ≥2 个 topic 文件路径(支持通配符,例:`/merge-topics content/topics/20260719-*.md`)

## 加载 Skill(强制)

- `grill-me`:对合并方向做深度拷问,至少 3 轮
- `recursive-research`:补全合并后 topic 缺失的背景信息

## 步骤

### 1. 输入验证

- 验证所有指定文件存在
- 验证所有文件不在 `content/topics/archive/`
- 验证文件数量 ≥ 2
- 任一验证失败则中止并提示错误

### 2. 内容读取与去重检测

- 读取所有源 topic 文件
- 检查内容重叠度:任意两个文件核心叙事点重叠 >60%,提示用户确认合并
- 列出每个文件的核心论点、关键数据、可回溯来源

### 3. 合并方向拷问(grill-me 集成)

使用 `grill-me` skill,一轮问一个关键问题,典型问题:

- 这几个 topic 的核心主线是什么?(决定合并后标题)
- 哪些文件的数据/案例可以保留?哪些应删除?
- 合并后保留哪个创作方向?

至少完成 3 轮 grill-me 后才能进入下一步。

### 4. 展示合并方案

向用户展示以下内容(等待用户确认):

| 项 | 内容 |
|----|------|
| 底稿文件 | 从源文件中选 1 个作为底稿(推荐选最完整或最新的),其他文件的关键数据作为补充 |
| 合并后标题 | 由 grill-me 拷问后确定的核心主线命名 |
| 保留内容 | 列出每个源文件中将被保留到合并文件的具体章节 |
| 删除内容 | 列出每个源文件中将被丢弃的具体章节及丢弃理由 |
| 合并后时间戳 | 取**执行合并当天的日期**(YYYYMMDD) |
| 合并后文件路径 | `content/topics/{YYYYMMDD}-{合并后主题名}.md` |

### 5. 执行合并(用户确认后)

按以下顺序操作:

1. **新建合并文件**:`content/topics/{YYYYMMDD}-{合并后主题名}.md`,写入底稿内容 + 补充内容
2. **删除源文件**:`git rm` 所有源 topic 文件
3. **不动 reference 文件**:`content/reference/` 下源文件**保留不动**,由后续 `/review-topics` 阶段重新生成覆盖
4. **验证**:`ls content/topics/` 确认源文件已删除、合并文件已创建

### 6. 提示后续步骤

- 提示用户:「合并完成。下一步建议重新执行 `/review-topics {合并后文件}`,重新生成 reference 文件覆盖老的多个 reference」
- 提示用户:「如不需要重做 reference,可跳过 review-topics 直接进入 /create-draft」

## 输出

- 合并后的新 topic 文件:`content/topics/{YYYYMMDD}-{合并后主题名}.md`
- 删除的源文件列表(已在 git 暂存区)
- 源 reference 文件列表(**保留**,**未动**)

## 约束

**必须遵守**:

- 合并后文件时间戳 = **执行合并当天日期**(不是最早源文件日期,也不是底稿日期)
- 至少完成 3 轮 grill-me 拷问后才能展示合并方案
- 删除源文件必须用 `git rm` 而非 `rm`,保留 git 历史可追溯
- reference 文件**不动**,由后续 review-topics 重做覆盖

**禁止操作**:

- 不要自动执行合并,必须等用户明确确认
- 不要修改源 reference 文件
- 不要把合并后文件保存到 `content/topics/archive/`
- 不要跳过 grill-me 直接展示合并方案
