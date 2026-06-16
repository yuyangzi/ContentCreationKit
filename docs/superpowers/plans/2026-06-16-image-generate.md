# 图片生成技能 (image-generate) 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个 OpenCode 技能，使 AI Agent 能通过火山方舟 Ark 平台调用 Doubao Seedream 4.5 模型，将文本 prompt 生成为图片并保存到 `content/images/` 目录。

**Architecture:** 单文件技能 `.opencode/skills/image-generate/SKILL.md`，包含 YAML frontmatter + Markdown 文档 + 内嵌 Python 脚本。Agent 通过 Bash 工具执行 Python 脚本，调用 OpenAI SDK 兼容接口（Ark 平台），下载图片到本地。同时更新 `.gitignore` 防止图片被提交。

**Tech Stack:** Python 3 + openai SDK (>=1.0) + 火山方舟 Ark API

---

## 文件结构

| 文件 | 操作 | 职责 |
|------|------|------|
| `.opencode/skills/image-generate/SKILL.md` | 创建 | 技能定义（frontmatter + 文档 + 内嵌脚本） |
| `.gitignore` | 修改 | 添加 `content/images/` 条目 |

---

### Task 1: 更新 .gitignore

**Files:**
- Modify: `.gitignore:17`

- [ ] **Step 1: 添加 `content/images/` 到 .gitignore**

在 `.gitignore` 末尾的 `content/WeChat/` 之后追加一行：

```diff
 content/draft/
 content/reference/
 content/WeChat/
+content/images/
```

- [ ] **Step 2: 验证 .gitignore 条目**

```bash
grep -q 'content/images/' .gitignore && echo "✓ .gitignore 条目存在" || echo "❌ 缺失"
```

期望输出: `✓ .gitignore 条目存在`

- [ ] **Step 3: 提交**

```bash
git add .gitignore
git commit -m "chore: add content/images/ to .gitignore"
```

---

### Task 2: 创建 SKILL.md 技能文件

**Files:**
- Create: `.opencode/skills/image-generate/SKILL.md`

- [ ] **Step 1: 创建目录并写入 SKILL.md**

```bash
mkdir -p .opencode/skills/image-generate
```

写入以下内容到 `.opencode/skills/image-generate/SKILL.md`：

```markdown
---
name: image-generate
description: 调用火山方舟 Ark 平台 Doubao Seedream 4.5 模型，将文本 prompt 生成为图片并保存到本地。当用户要求生成图片、将提示词转为图片、或需要为文章生成封面图时使用。
allowed-tools: Bash, Write
---

# 图片生成 (Image Generate)

调用火山方舟 Ark 平台的 Doubao Seedream 4.5 文生图模型，将 prompt 生成为图片并保存到 `content/images/` 目录。

## 触发条件

在以下场景激活此技能：
- 用户提供了 prompt 并要求生成图片
- `/image-prompt` 生成了提示词后，用户说"生成这张图"
- 用户说"调用 seedream 生成封面图"
- `/to-wechat` 完成后需要配图

## 前置依赖

### 1. API Key

需要设置 `ARK_API_KEY` 环境变量。如果未设置，技能会提示用户。

```bash
export ARK_API_KEY='your-api-key'
```

### 2. Python 依赖

需要 `openai >= 1.0`。首次使用时自动检查并安装：

```bash
python3 -c "import openai" 2>/dev/null || pip install --upgrade "openai>=1.0"
```

## 参数

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| prompt | 是 | — | 中文生图提示词 |
| name | 是 | — | 文件名（不含扩展名），如 `ai-agent-roadmap` |
| model | 否 | `doubao-seedream-4-5-251128` | 模型标识 |
| size | 否 | `2K` | 图片尺寸，支持 `1K`/`2K`/`4K` |

## 使用方式

Agent 应通过 Bash 工具执行以下流程：

```bash
# 1. 检查依赖
python3 -c "import openai" 2>/dev/null || pip install --upgrade "openai>=1.0"

# 2. 检查 API Key
if [ -z "$ARK_API_KEY" ]; then
    echo "❌ 请先设置 ARK_API_KEY 环境变量"
    echo "   export ARK_API_KEY='your-api-key'"
    exit 1
fi

# 3. 写入并执行生成脚本
cat > /tmp/image-generate.py << 'PYEOF'
import os
import re
import sys
import urllib.request
from openai import OpenAI

# === 参数解析 ===
if len(sys.argv) < 3:
    print("用法: python3 generate.py <prompt> <name> [model] [size]")
    print("示例: python3 generate.py '一只猫' 'cat-cover'")
    sys.exit(1)

PROMPT = sys.argv[1]
NAME = sys.argv[2]
MODEL = sys.argv[3] if len(sys.argv) > 3 else "doubao-seedream-4-5-251128"
SIZE = sys.argv[4] if len(sys.argv) > 4 else "2K"

# === 文件名清理（防路径遍历） ===
NAME = re.sub(r'[^a-zA-Z0-9_\-\u4e00-\u9fff]', '_', NAME)
NAME = NAME.strip('_') or "untitled"

# === API Key 检查 ===
api_key = os.environ.get("ARK_API_KEY")
if not api_key:
    print("❌ 错误: 未设置 ARK_API_KEY 环境变量")
    print("   请设置: export ARK_API_KEY='your-api-key'")
    sys.exit(1)

# === 调用 API ===
client = OpenAI(
    base_url="https://ark.cn-beijing.volces.com/api/v3",
    api_key=api_key,
)

print(f"🎨 正在生成图片...")
print(f"   Prompt: {PROMPT[:50]}{'...' if len(PROMPT) > 50 else ''}")
print(f"   Model: {MODEL}")
print(f"   Size: {SIZE}")

try:
    response = client.images.generate(
        model=MODEL,
        prompt=PROMPT,
        size=SIZE,
        response_format="url",
        extra_body={"watermark": True},
    )
    image_url = response.data[0].url
except Exception as e:
    print(f"❌ API 调用失败: {e}")
    sys.exit(1)

# === 下载保存（带超时） ===
os.makedirs("content/images", exist_ok=True)
output_path = f"content/images/{NAME}.png"

try:
    with urllib.request.urlopen(image_url, timeout=30) as resp:
        with open(output_path, 'wb') as f:
            f.write(resp.read())
except Exception as e:
    print(f"❌ 图片下载失败: {e}")
    print(f"   URL: {image_url}")
    sys.exit(1)

print(f"✅ 图片已生成: {output_path}")
PYEOF

python3 /tmp/image-generate.py "<prompt>" "<name>" "<model>" "<size>"

# 4. 清理临时文件
rm /tmp/image-generate.py
```

## 调用示例

```bash
# 基本调用
python3 /tmp/image-generate.py "一只坐在窗边的猫" "cat-cover"

# 指定尺寸
python3 /tmp/image-generate.py "星际穿越，黑洞" "interstellar" "doubao-seedream-4-5-251128" "4K"
```

## 输出

- **成功**: `✅ 图片已生成: content/images/{name}.png`
- **失败**: 明确的错误信息 + 退出码非0

## 错误处理

| 错误场景 | 检测方式 | 处理方式 |
|----------|----------|----------|
| `ARK_API_KEY` 未设置 | `os.environ.get()` 返回 None | 提示设置方法，退出 |
| `openai` 包未安装 | `import openai` 失败 | 提示安装命令 |
| 参数不足 | `len(sys.argv) < 3` | 显示用法说明，退出 |
| API 调用失败 | `except Exception` 捕获 | 显示错误信息，退出（不重试） |
| 图片下载失败 | `urllib` 异常 | 显示 URL 和错误，退出 |
| 图片下载超时 | `urlopen(timeout=30)` 超时 | 显示超时错误，退出 |
| 非法文件名 | 正则清理 | 自动替换为 `_` |

## 安全措施

- 文件名清理：仅允许 `[a-zA-Z0-9_\-]` 和中文字符，其余替换为 `_`
- 下载超时：30 秒超时，防止无限挂起
- API Key 保护：仅从环境变量读取，不硬编码
- 临时文件清理：执行完毕后删除 `/tmp/image-generate.py`

## 文件覆盖策略

同名文件已存在时直接覆盖，符合幂等调用场景。

## 与管线的集成

```
/image-prompt     → 生成提示词文本（对话中输出）
/image-generate   → 将提示词转化为实际图片文件
/to-wechat        → 排版时引用 content/images/ 下的图片
```

## 注意事项

- 生成图片需要几秒到几十秒，Agent 应等待脚本完成
- 每次调用只生成一张图片
- 图片格式固定为 PNG
- 图片尺寸 `1K`/`2K`/`4K` 由 Ark 平台定义，非标准像素尺寸
- 水印默认开启，由 Ark 平台在图片上添加
```

- [ ] **Step 2: 验证文件结构**

```bash
ls -la .opencode/skills/image-generate/SKILL.md
```

期望输出: 文件存在且大小 > 0

- [ ] **Step 3: 验证 frontmatter 格式**

```bash
head -5 .opencode/skills/image-generate/SKILL.md
```

期望输出: 包含 `---` 分隔符、`name: image-generate`、`description:`、`allowed-tools:`

- [ ] **Step 4: 提交**

```bash
git add .opencode/skills/image-generate/
git commit -m "feat: add image-generate skill for Doubao Seedream text-to-image"
```

---

### Task 3: 集成验证

- [ ] **Step 1: 验证 .gitignore 条目**

```bash
grep -q 'content/images/' .gitignore && echo "✓ .gitignore 条目存在" || echo "❌ 缺失"
```

期望输出: `✓ .gitignore 条目存在`

- [ ] **Step 2: 验证技能文件可被 OpenCode 发现**

```bash
ls .opencode/skills/image-generate/SKILL.md && echo "✓ 技能文件已创建"
```

期望输出: `✓ 技能文件已创建`

- [ ] **Step 3: 验证文件名清理逻辑（纯 Python 测试，无需 API Key）**

```bash
python3 -c "
import re
# 测试用例
cases = [
    ('../../etc/passwd', '____etc_passwd'),
    ('hello world', 'hello_world'),
    ('test-file_v2', 'test-file_v2'),
    ('中文名称', '中文名称'),
    ('!!!', 'untitled'),
]
for name, expected in cases:
    result = re.sub(r'[^a-zA-Z0-9_\-\\u4e00-\\u9fff]', '_', name).strip('_') or 'untitled'
    assert result == expected, f'FAIL: {name} -> {result}, expected {expected}'
print('✓ 文件名清理逻辑测试全部通过')
"
```

期望输出: `✓ 文件名清理逻辑测试全部通过`

---

## 自审查

- [x] 覆盖所有 spec 需求：参数定义、API 调用、文件保存、安全措施、错误处理、.gitignore
- [x] 无 "TBD" / "TODO" 占位符
- [x] 所有代码步骤包含完整代码，无 "类似 Task N" 引用
- [x] 类型一致性：NAME 清理逻辑在各处一致
- [x] 文件路径精确：所有路径使用项目根目录相对路径