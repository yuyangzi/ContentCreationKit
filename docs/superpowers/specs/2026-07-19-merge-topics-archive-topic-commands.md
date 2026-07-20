# 新增 merge-topics / archive-topic 命令

> 把 review-topics 阶段分散的主题合并与主题归档操作升级为独立命令,补全 P2 commands 体系的结构性缺口。

**日期**: 2026-07-19  
**作者**: Sisyphus  
**状态**: Draft  
**预期落地**: 2026-07-22  
**前置 spec**: `2026-07-19-commands-p0-consistency-fix.md` (时间戳/命名规范基础)

---

## 1. 目标

新增 2 个 commands,解决 P2 阶段发现的 2 个操作模式问题:

| 问题 | 现状 | 修复后 |
|------|------|--------|
| 主题合并操作分散 | AGENTS.md 描述合并模式,`review-topics.md` 步骤 6 列为可选项,`find-popular-topics.md` 不提 | 升级为独立命令 `/merge-topics`,明确触发条件、操作流程、命名规范 |
| 主题归档操作无命令 | AGENTS.md 提到归档机制,实际靠手动 `git mv` | 新增 `/archive-topic` 命令,统一单文件与批量归档流程 |

**用户决策(2026-07-19)**:
- merge 后文件名: 取**合并执行当天的日期**
- merge 时 reference 处理: **合并不动 reference**,由后续 `/review-topics` 重做覆盖
- archive 触发方式: **支持批量归档 `--batch` 模式**

---

## 2. 背景与现状证据

### 2.1 主题合并:高频操作但无专门命令

**实际使用证据** (从 session `ses_08767390b` 提取,2026-07-19):
- 一次合并 **4 个 topic** 文件,合并后生成 `20260719-AI内容治理范式转换.md` (用当天日期 20260719)
- 合并后删除原 4 个文件,同步更新 `content/reference/20260719-AI内容治理范式转换-审核记录.md`

**当前痛点**:
- `review-topics.md` 步骤 6 把合并作为可选项,操作细节散落在 AGENTS.md
- `find-popular-topics.md` 完全不提合并
- 没有标准化的合并前置验证、合并方案展示步骤
- LLM 重复发明合并流程,每次实现略有差异

### 2.2 主题归档:完全手动

**实际使用证据** (从 session `ses_086d4141` 提取,2026-07-19):
- 一次操作归档 **3 个文件**:`20260629-AI模型量价螺旋` 删除,`20260718-Agent-Loop` 移到 archive/
- 全部通过 `git rm` + `git mv` 手动执行,在 git 提交阶段执行,不是 topic 管线阶段

**当前痛点**:
- 没有专门命令,流程靠记忆
- 每次 git 提交时临时决定归档哪些
- 容易遗漏已归档的 topic 不参与 find-popular-topics 饱和检查的语义

---

## 3. 新增命令 1: `/merge-topics`

### 3.1 命令文件位置与元数据

- 路径: `.opencode/commands/merge-topics.md`
- 模型: `deepseek/deepseek-v4-pro` (深度分析合并方向)
- 预计行数: 80-110 行

### 3.2 命令结构(规范格式)

**frontmatter**: description、model

**目标**: 将 2 个或以上内容高度重叠的 topic 文件合并为一个,消除重复创作,形成统一主线。

**前置条件**:
- `content/topics/` 目录有 ≥2 个待合并的 topic 文件
- 所有待合并文件**不在** `content/topics/archive/` 内

**输入**: 用户指定的 ≥2 个 topic 文件路径(支持通配符,例: `/merge-topics content/topics/20260719-*.md`)

**加载 Skill(强制)**: `grill-me` (对合并方向做深度拷问),`recursive-research` (补全合并后 topic 缺失的背景信息)

**步骤**:
1. **输入验证**: 验证所有指定文件存在、不在 archive/、数量 ≥2,任一失败则中止
2. **内容读取与去重检测**: 读取所有源 topic,检查内容重叠度(>60% 提示用户确认),列出每个文件的核心论点、关键数据、可回溯来源
3. **合并方向拷问(grill-me 集成)**: 至少完成 3 轮 grill-me,典型问题: 这几个 topic 的核心主线是什么? 哪些数据/案例保留? 哪些应删除? 保留哪个创作方向?
4. **展示合并方案**(等待用户确认): 包括底稿文件、合并后标题、保留内容清单、删除内容清单及理由、合并后时间戳(执行当天 YYYYMMDD)、合并后文件路径
5. **执行合并(用户确认后)**:
   - 新建 `content/topics/{YYYYMMDD}-{合并后主题名}.md`,写入底稿内容 + 补充内容
   - `git rm` 所有源 topic 文件
   - **不动** `content/reference/` 下源文件,由后续 `/review-topics` 重新生成覆盖
   - `ls content/topics/` 验证源文件已删除、合并文件已创建
6. **提示后续步骤**: 建议重新执行 `/review-topics {合并后文件}` 重新生成 reference

**输出**: 合并后新 topic 文件、删除的源文件列表(已在 git 暂存区)、源 reference 文件列表(保留未动)

**必须遵守**:
- 合并后文件时间戳 = **执行合并当天日期**
- 至少完成 3 轮 grill-me 拷问后才能展示合并方案
- 删除源文件必须用 `git rm` 而非 `rm`,保留 git 历史
- reference 文件**不动**

**禁止操作**: 不要自动执行合并、不要修改源 reference 文件、不要把合并后文件保存到 archive/、不要跳过 grill-me

---

## 4. 新增命令 2: `/archive-topic`

### 4.1 命令文件位置与元数据

- 路径: `.opencode/commands/archive-topic.md`
- 模型: `opencode/deepseek-v4-flash-free` (机械归档操作)
- 预计行数: 60-90 行

### 4.2 命令结构(规范格式)

**frontmatter**: description、model

**目标**: 将过期或已被替代的 topic 文件移动到 `content/topics/archive/`,从主话题池中排除,避免 `/find-popular-topics` 重复发现。

**前置条件**: 待归档的 topic 文件存在于 `content/topics/`(不在 archive/ 内)

**输入**: 三种模式

- **模式 1 - 单文件归档(默认)**: `/archive-topic content/topics/20260629-AI模型量价螺旋-...md`
- **模式 2 - 批量归档(`--batch`)**: `/archive-topic --batch content/topics/20260629-*.md content/topics/20260718-Agent-*.md`
- **模式 3 - 自动扫描候选(`--auto`)**: `/archive-topic --auto`,扫描规则 = 有对应 article 且 article 超过 30 天的 topic,作为候选列出

**步骤**:
1. **输入解析**: 解析命令行参数,确定模式
2. **归档前检查**: 每个待归档文件需满足 = 文件存在 / 不在 archive/ / 文件名匹配 `{YYYYMMDD}-{主题名}.md` 格式;任一失败则跳过,记录到跳过清单
3. **对应 article 检查**: 扫描 `content/article/`,查找与待归档 topic 对应的 article;若没有对应 article,提示用户确认
4. **展示待归档清单**(等待用户确认): 待归档文件数、文件列表(路径 + 是否有关联 article)、跳过文件及原因、目标目录
5. **执行归档(用户确认后)**:
   - `git mv` 每个待归档文件到 `content/topics/archive/`
   - `ls content/topics/archive/` 验证
   - `git status` 应显示 rename 而非 delete + add
6. **提示后续影响**: 这 N 个 topic 已从 `/find-popular-topics` 的候选池中排除

**输出**: 归档后的文件位于 `content/topics/archive/`,git status 显示 N 个 rename

**必须遵守**:
- 移动文件必须用 `git mv` 而非 `mv + git add`,保留 rename 关系
- 归档前必须用户确认
- `--auto` 模式只列出候选,不自动归档
- 归档后文件**保留在 archive/**,不删除(支持手动恢复)

**禁止操作**: 不要归档 archive/ 内的文件、不要在 `--auto` 模式自动执行、不要修改归档文件内容、不要同步删除对应的 article/reference

---

## 5. 与现有 commands 的关系

### 5.1 merge-topics 与 review-topics 的边界

| 维度 | `/merge-topics` | `/review-topics` |
|------|-----------------|------------------|
| 目标 | 多个 topic → 1 个 topic | 1 个 topic → 1 个 reference |
| 触发条件 | ≥2 topic 内容重叠 >60% | 单个 topic 内容已确认 |
| 对 reference 的影响 | 不动(由后续 review-topics 覆盖) | 生成 `content/reference/{YYYYMMDD}-{主题名}-v1.md` |
| 典型使用阶段 | 选题发现后、深度研究前 | 选题确认后、创建草稿前 |

**新流程建议**:
```
/find-popular-topics → (若有重叠 → /merge-topics) → /review-topics → /review-reference → /create-draft
```

### 5.2 archive-topic 与 find-popular-topics 的协同

- `archive/` 目录下的文件**不参与** `/find-popular-topics` 的候选发现
- `archive/` 目录下的文件**作为负样本**: 候选主题如果在 archive/ 中已存在,直接跳过
- 此协同关系**已经存在**(README 提及),但缺少显式执行检查,新命令强化这一机制

---

## 6. 验证

实施完成后运行以下检查:

**文件存在性**:
```bash
ls -la .opencode/commands/merge-topics.md     # 期望存在
ls -la .opencode/commands/archive-topic.md    # 期望存在
```

**frontmatter 解析**:
```bash
head -5 .opencode/commands/merge-topics.md   # 期望显示 description 和 model
```

**行数合理**:
```bash
wc -l .opencode/commands/merge-topics.md      # 期望 80-110 行
wc -l .opencode/commands/archive-topic.md     # 期望 60-90 行
```

**关键约束检查**:
```bash
grep "git rm" .opencode/commands/merge-topics.md           # 期望 ≥1
grep "grill-me" .opencode/commands/merge-topics.md         # 期望 ≥2
grep "YYYYMMDD" .opencode/commands/merge-topics.md         # 期望 ≥1
grep "git mv" .opencode/commands/archive-topic.md          # 期望 ≥2
grep -e --batch -e --auto .opencode/commands/archive-topic.md  # 期望 ≥2
```

---

## 7. 影响文件清单

| 文件 | 操作 | 预估行数 |
|------|------|----------|
| `.opencode/commands/merge-topics.md` | 新建 | ~100 行 |
| `.opencode/commands/archive-topic.md` | 新建 | ~80 行 |
| `README.md` | 更新命令参考表(新增 2 行) | +2 行 |
| `AGENTS.md` | 可选,标「高频时可独立使用」 | +1 行 |

**总改动**: 4 个文件,纯新增/补充,不修改现有命令逻辑。

---

## 8. 风险与回滚

**风险**: 低。两个新命令**不修改**任何现有命令或内容文件,只在 `content/topics/` 内移动/合并文件。

**潜在副作用**:
- `/merge-topics` 删除源文件后,如果用户后悔,git revert 可恢复(已合并的 reference 仍需手动重做)
- `/archive-topic --auto` 误判时,可能把还有用的 topic 归档(建议默认用单文件模式)

**回滚方案**:
- 新增命令: `rm .opencode/commands/merge-topics.md archive-topic.md`(本地操作,不影响 git 提交)
- 已合并/归档的文件: `git revert <commit-hash>` 恢复

---

## 9. 不在本 spec 范围

明确排除以下,以保持本 spec 聚焦:

- **P0 commands 一致性修复**(已在 `2026-07-19-commands-p0-consistency-fix.md` 中)
- **P1 深度技术文专项** (create-draft / to-article / review-article 加 deep-tech mode)
- **P3 commands 详细度模板** (建立标准结构)
- **P4 模型重新分配** (to-article / review-article 升到 Pro)
- **`/archive-topic` 对历史归档文件的批量迁移**(暂不处理,需要时单独 spec)
- **`/merge-topics` 的 GUI/可视化界面**(暂不需要,对话流程足够)
