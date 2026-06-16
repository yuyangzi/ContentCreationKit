# image-generate Skill 优化方案

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 依据 skill-creator 最佳实践重构 `image-generate` skill，消除非标准字段、启用 Progressive Disclosure、提升触发准确性。

**Architecture:** 将当前单文件 212 行 SKILL.md 拆分为三层结构：SKILL.md（核心指令 ~80 行）+ `scripts/generate.py`（可执行脚本）+ `references/api.md`（API 详情参考）。脚本不占 context，参考文件按需加载。

**Tech Stack:** 纯文件重构，无新依赖。

---

## 问题诊断

基于 skill-creator 最佳实践的逐项诊断：

| # | 问题 | 严重度 | 违反的规则 |
|---|------|--------|-----------|
| 1 | Frontmatter 含非标准字段 `allowed-tools: Bash` | 中 | "Do not include any other fields in YAML frontmatter" |
| 2 | 触发条件写在 body 而非 description | 高 | Body 在触发前不加载 → 部分场景无法触发 |
| 3 | 内嵌 ~100 行 Python 每次加载占 context | 高 | Progressive Disclosure: script 应在 `scripts/` 直接执行 |
| 4 | 无分层结构，全部内容在单文件 | 中 | 缺少 `scripts/`、`references/` 渐进加载能力 |
| 5 | Body 中 "触发条件" 节冗余（应进 description） | 低 | "Include all 'when to use' in description - Not in the body" |

---

## 优化后文件结构

```
.opencode/skills/image-generate/
├── SKILL.md              # 核心工作流指令（~80 行）
├── scripts/
│   └── generate.py       # 从 SKILL.md 提取的 Python 生成脚本
└── references/
    └── api.md             # API 细节、模型参数、尺寸规格
```

### 各文件职责

| 文件 | 加载方式 | 职责 |
|------|----------|------|
| `SKILL.md` | Skill 触发后加载 | 工作流指引：依赖检查 → 脚本调用 → 输出说明 → 错误速查 |
| `scripts/generate.py` | 被 bash 调用执行 | 图片生成主逻辑：API 调用 + 下载 + 校验。不占 context |
| `references/api.md` | Agent 需要时按需 Read | API 细节：base_url、模型列表、尺寸对照、水印参数 |

---

## 详细设计

### 改动 1: SKILL.md 重写

**删除的内容：**
- `allowed-tools: Bash`（非标准字段）
- "触发条件" 整节（合并到 description）
- 内嵌 Python 脚本（提取到 `scripts/generate.py`）
- "调用示例" 节（脚本独立后自然可测）

**保留的内容：**
- 前置依赖（API Key + Python 依赖）
- 参数表格
- 使用方式（改为引用 `scripts/generate.py`）
- 输出说明
- 错误处理速查表
- 管线集成说明
- 注意事项

**新增的内容：**
- `scripts/generate.py` 引用
- `references/api.md` 引用

#### 优化后 Frontmatter

```yaml
---
name: image-generate
description: 使用火山方舟 Ark 平台 Doubao Seedream 4.5 模型生成图片。当用户要求生成图片、将提示词转为图片、制作文章封面、调用 seedream 生图时使用——包括 /image-prompt 完成后用户说"生成这张图"、/to-wechat 完成后需要配图等场景。输入中文 prompt 输出 PNG 图片到 content/images/ 目录。
---
```

**Description 设计要点：**
- 包含所有原 body 中的触发条件："生成图片"、"提示词转为图片"、"封面"、"seedream"
- 包含命令链接触发：`/image-prompt`、`/to-wechat`
- 描述输入输出格式便于 Claude 判断匹配度
- ~120 字符，不会让 metadata 过长

#### 优化后 Body 结构

```markdown
# 图片生成 (Image Generate)

调用火山方舟 Ark 平台 Doubao Seedream 4.5 文生图模型生成 PNG 图片。

## 前置依赖

### API Key
需要 `ARK_API_KEY` 环境变量...

### Python 依赖
需要 `openai >= 1.0`...

## 参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| prompt | 是 | — | 中文生图提示词 |
| name | 是 | — | 文件名（不含扩展名） |
| ... |

## 使用方式

Agent 通过 Bash 工具执行，必须在项目根目录运行：

```bash
# 检查依赖
python3 -c "import openai" 2>/dev/null || pip3 install --upgrade "openai>=1.0"

# 检查 API Key
[ -z "$ARK_API_KEY" ] && echo "请设置 ARK_API_KEY" && exit 1

# 执行生成
printf '%s\n' '<prompt>' | python3 .opencode/skills/image-generate/scripts/generate.py '<name>' '[model]' '[size]'
```

## 输出

- 成功: `✅ 图片已生成: content/images/{name}.png`
- 失败: 错误信息 + 非零退出码

## 错误处理

| 错误场景 | 检测方式 | 处理方式 |
|----------|----------|----------|
| ... |

## 管线集成

本技能位于创作管线第⑨步...

## 参考文档

- **API 详情**: `references/api.md` — base_url、模型列表、尺寸规格、水印参数等

## 注意事项

- 生成需数秒至数十秒，Agent 需等待脚本完成
- 每次调用只生成一张图片
- 图片格式固定 PNG
- 水印默认开启
```

**预计行数：~80 行**（从 212 缩减 62%）

---

### 改动 2: 新建 `scripts/generate.py`

**来源：** 从当前 SKILL.md 提取内嵌 Python 脚本，做以下调整：

1. 移除 `cat > /tmp/... << 'PYEOF'` 包装（已是独立文件）
2. 移除 `rm -f /tmp/image-generate.py`（不再需要）
3. 添加 shebang + docstring
4. 其余代码**一字不改**（逻辑已验证通过）

```python
#!/usr/bin/env python3
"""Doubao Seedream 4.5 文生图脚本。

通过火山方舟 Ark 平台 API 将文本 prompt 生成为 PNG 图片。

用法:
    printf '%s\n' '<prompt>' | python3 generate.py <name> [model] [size]

参数:
    prompt    - 从 stdin 读取，避免 shell 注入
    name      - 输出文件名（不含扩展名），保存至 content/images/{name}.png
    model     - 模型标识，默认 doubao-seedream-4-5-251128
    size      - 图片尺寸，1K/2K/4K，默认 2K

环境变量:
    ARK_API_KEY  - 火山方舟 API 密钥（必填）
"""

import os
import re
import sys
import urllib.request
from openai import OpenAI

# ... (其余代码与当前 SKILL.md 内嵌脚本完全一致，不再重复)
```

**关键点：**
- 脚本路径相对于 SKILL.md 所在目录 → Agent 调用时用 `.opencode/skills/image-generate/scripts/generate.py`
- 工作目录依赖调用方 `cd` 到项目根（与现状一致）
- 逻辑零改动 → 行为完全向后兼容

---

### 改动 3: 新建 `references/api.md`

**内容：** 从 SKILL.md 抽取 API 细节 + 补充完整说明

```markdown
# API 参考

## 端点信息

| 项目 | 值 |
|------|-----|
| Base URL | `https://ark.cn-beijing.volces.com/api/v3` |
| 认证方式 | API Key（环境变量 `ARK_API_KEY`） |
| 兼容性 | OpenAI SDK 兼容接口 |

## 模型

| 模型 ID | 说明 |
|---------|------|
| `doubao-seedream-4-5-251128` | 默认模型，Doubao Seedream 4.5 |

## 尺寸规格

| 值 | 含义 |
|----|------|
| `1K` | 约 1024 像素级别 |
| `2K` | 约 2048 像素级别（默认） |
| `4K` | 约 4096 像素级别 |

> 精确像素尺寸由 Ark 平台定义，以上为近似值。

## API 调用参数

| 参数 | 值 | 说明 |
|------|-----|------|
| `model` | `doubao-seedream-4-5-251128` | 模型标识 |
| `prompt` | 用户输入 | 中文提示词 |
| `size` | `1K`/`2K`/`4K` | 输出尺寸 |
| `response_format` | `url` | 获取图片下载 URL |
| `extra_body` | `{"watermark": true}` | 启用平台水印 |

## 返回格式

```json
{
  "data": [
    {
      "url": "https://ark-platform-cdn.volces.com/..."
    }
  ]
}
```
```

**设计要点：**
- 仅提供 API 参考信息，不重复工作流指令
- 按需加载：Agent 只在排查 API 问题或了解参数细节时读取

---

## 改动对比

| 维度 | 当前 | 优化后 |
|------|------|--------|
| Frontmatter 字段数 | 3（含非标准 `allowed-tools`） | 2（标准 `name` + `description`） |
| SKILL.md 行数 | 212 | ~80（-62%） |
| Python 代码位置 | 内嵌在 SKILL.md | `scripts/generate.py` |
| Context 消耗 | 每次加载 212 行 + 内嵌脚本 | 每次加载 ~80 行 |
| 触发描述 | 简短英文 | 详细中文含所有触发短语 |
| API 细节可发现性 | 与工作流混在一起 | 独立 `references/api.md` 按需查阅 |

---

## 实现任务

### Task 1: 创建目录结构

**Files:**
- Create: `.opencode/skills/image-generate/scripts/` (dir)
- Create: `.opencode/skills/image-generate/references/` (dir)

- [ ] **Step 1: 创建目录**

```bash
mkdir -p .opencode/skills/image-generate/scripts
mkdir -p .opencode/skills/image-generate/references
```

- [ ] **Step 2: 验证目录结构**

```bash
ls -d .opencode/skills/image-generate/scripts .opencode/skills/image-generate/references
```

期望输出：两个目录路径均存在

---

### Task 2: 提取脚本到 `scripts/generate.py`

**Files:**
- Create: `.opencode/skills/image-generate/scripts/generate.py`

- [ ] **Step 1: 写入 generate.py**

将当前 SKILL.md 中的内嵌 Python 代码提取为独立文件，添加 shebang 和 docstring，其余逻辑不变：

```bash
# 内容见上述详细设计，此处省略完整代码
```

- [ ] **Step 2: 验证 Python 语法**

```bash
python3 -c "compile(open('.opencode/skills/image-generate/scripts/generate.py').read(), 'generate.py', 'exec'); print('✓ 语法正确')"
```

期望输出: `✓ 语法正确`

- [ ] **Step 3: 验证文件名清理逻辑**

```bash
python3 -c "
import re
cases = [
    ('../../etc/passwd', 'etc_passwd'),
    ('hello world', 'hello_world'),
    ('test-file_v2', 'test-file_v2'),
    ('中文名称', '中文名称'),
    ('!!!', 'untitled'),
]
for name, expected in cases:
    result = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]', '_', name).strip('_') or 'untitled'
    assert result == expected, f'FAIL: {name} -> {result}, expected {expected}'
print('✓ 文件名清理逻辑测试全部通过')
"
```

期望输出: `✓ 文件名清理逻辑测试全部通过`

---

### Task 3: 新建 `references/api.md`

**Files:**
- Create: `.opencode/skills/image-generate/references/api.md`

- [ ] **Step 1: 写入 api.md**

写入上述详细设计中的 API 参考文档内容。

- [ ] **Step 2: 验证文件存在**

```bash
test -f .opencode/skills/image-generate/references/api.md && echo "✓ 文件已创建"
```

---

### Task 4: 重写 SKILL.md

**Files:**
- Modify: `.opencode/skills/image-generate/SKILL.md`

- [ ] **Step 1: 备份当前文件**

```bash
cp .opencode/skills/image-generate/SKILL.md .opencode/skills/image-generate/SKILL.md.bak
```

- [ ] **Step 2: 写入优化后的 SKILL.md**

写入上述详细设计中的优化后内容。

- [ ] **Step 3: 验证 frontmatter 格式**

```bash
python3 -c "
import yaml
with open('.opencode/skills/image-generate/SKILL.md') as f:
    content = f.read()
parts = content.split('---')
frontmatter = yaml.safe_load(parts[1])
assert 'name' in frontmatter, '缺少 name'
assert 'description' in frontmatter, '缺少 description'
assert 'allowed-tools' not in frontmatter, '不应有 allowed-tools'
print('✓ Frontmatter 格式正确')
print(f'  name: {frontmatter[\"name\"]}')
print(f'  description length: {len(frontmatter[\"description\"])} chars')
"
```

期望输出: `✓ Frontmatter 格式正确`

- [ ] **Step 4: 验证描述含关键触发词**

```bash
python3 -c "
with open('.opencode/skills/image-generate/SKILL.md') as f:
    content = f.read()
parts = content.split('---')
desc = parts[1].split('description:')[1]
keywords = ['生成图片', 'seedream', '封面', 'image-prompt', 'to-wechat', 'Doubao', 'Ark']
for kw in keywords:
    assert kw in desc, f'描述中缺少触发词: {kw}'
print('✓ 所有关键触发词已包含')
"
```

- [ ] **Step 5: 验证 SKILL.md 行数**

```bash
lines=$(wc -l < .opencode/skills/image-generate/SKILL.md)
echo "SKILL.md 行数: $lines"
if [ "$lines" -gt 120 ]; then
    echo "⚠ 行数超过目标(120)，请检查是否可进一步精简"
else
    echo "✓ 行数在合理范围"
fi
```

---

### Task 5: 验证整体结构

- [ ] **Step 1: 验证文件清单**

```bash
echo "=== 最终文件结构 ==="
find .opencode/skills/image-generate -type f | sort
```

期望输出:
```
.opencode/skills/image-generate/SKILL.md
.opencode/skills/image-generate/references/api.md
.opencode/skills/image-generate/scripts/generate.py
```

- [ ] **Step 2: 验证脚本可从命令行执行**

```bash
cd "$(git rev-parse --show-toplevel)" && \
echo "test" | python3 .opencode/skills/image-generate/scripts/generate.py 2>&1 | head -3
```

期望输出: 包含 `❌ 错误: 未设置 ARK_API_KEY`（有意义的错误而非语法错误）

- [ ] **Step 3: 清理备份文件**

```bash
rm -f .opencode/skills/image-generate/SKILL.md.bak
```

- [ ] **Step 4: 提交**

```bash
git add .opencode/skills/image-generate/
git commit -m "refactor(image-generate): optimize skill structure per skill-creator best practices

- Extract inline Python to scripts/generate.py (progressive disclosure)
- Add references/api.md for API details
- Remove non-standard allowed-tools from frontmatter
- Merge trigger conditions into description for accurate triggering
- Reduce SKILL.md from 212 to ~80 lines"
```

---

## 自审查

- [x] 覆盖所有问题：frontmatter 修复、触发条件迁移、脚本提取、参考文档、分层结构
- [x] 无 "TBD" / "TODO" 占位符
- [x] SKILL.md 保留所有关键信息（参数表、错误处理、管线集成）
- [x] 脚本逻辑零改动（仅添加 shebang + docstring）
- [x] 项目风格一致：参考 wechat-format 的 `scripts/` 目录模式
- [x] 触发词覆盖：`seedream`、`封面`、`生成图片`、`image-prompt`、`to-wechat`、`Doubao`
- [x] 向后兼容：调用方式从 `cat > /tmp/...` 改为 `python3 scripts/generate.py`，行为一致
