# 图片生成技能设计文档

**日期**: 2026-06-16  
**状态**: 已审查，待实现  
**关联**: `/image-prompt` 命令，`/to-wechat` 命令

---

## 1. 背景与动机

ContentCreationKit 创作管线目前覆盖从选题到公众号排版的完整流程，但配图环节止步于 `/image-prompt` 命令生成提示词文本。用户拿到提示词后需手动打开其他工具（如 Midjourney、ComfyUI）生成图片，流程断裂。

本技能填补管线最后一环：将 AI 生成的提示词直接转化为实际图片文件，保存到本地，供 `/to-wechat` 排版时引用。

## 2. 目标

创建一个 OpenCode 技能，使 AI Agent 能够自主调用火山方舟 Ark 平台的 Doubao Seedream 4.5 模型，将文本 prompt 生成为图片并保存到本地文件系统。

**非目标**：
- 不支持批量生成（每次调用生成一张图片）
- 不支持图片后处理（裁剪、调色等）
- 不替代 `/image-prompt` 的提示词生成功能

## 3. 技能规格

### 3.1 基本信息

| 属性 | 值 |
|------|-----|
| 文件路径 | `.opencode/skills/image-generate/SKILL.md` |
| 技能名称 | `image-generate` |
| 允许工具 | `Bash`, `Write` |
| 调用方式 | AI Agent 自主调用 |

### 3.2 触发条件

Agent 在以下场景应触发此技能：
- 用户提供了 prompt 并要求生成图片
- `/image-prompt` 生成了提示词后，用户说"生成这张图"
- 用户说"调用 seedream 生成封面图"
- `/to-wechat` 完成后需要配图

### 3.3 工作流程

```
┌─────────────┐
│ 1. 依赖检查  │  检查 openai 包是否安装，ARK_API_KEY 是否设置
└──────┬──────┘
       │
┌──────▼──────┐
│ 2. 参数准备  │  收集 prompt(必填), name(必填), model(可选), size(可选)
└──────┬──────┘
       │
┌──────▼──────┐
│ 3. API 调用  │  通过 OpenAI SDK 兼容接口调用 Ark 平台
└──────┬──────┘
       │
┌──────▼──────┐
│ 4. 下载保存  │  从响应 URL 下载图片 → content/images/{name}.png
└──────┬──────┘
       │
┌──────▼──────┐
│ 5. 结果确认  │  输出文件路径，确认生成成功
└─────────────┘
```

### 3.4 参数定义

| 参数 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `prompt` | 是 | — | 中文生图提示词 |
| `name` | 是 | — | 文件名（不含扩展名），如 `ai-agent-roadmap` |
| `model` | 否 | `doubao-seedream-4-5-251128` | 模型标识 |
| `size` | 否 | `2K` | 图片尺寸，支持 `1K`/`2K`/`4K` |

**固定参数**（不暴露给用户）：
- `response_format`: `url`
- `watermark`: `true`
- `sequential_image_generation`: `disabled`
- `stream`: `false`

### 3.5 API 接口

**平台**: 火山方舟 Ark  
**端点**: 通过 OpenAI SDK 兼容接口调用  
**Base URL**: `https://ark.cn-beijing.volces.com/api/v3`  
**模型**: `doubao-seedream-4-5-251128`  
**认证**: `ARK_API_KEY` 环境变量

### 3.6 输出

- **文件**: `content/images/{name}.png`
- **控制台输出**: `✓ 图片已生成: content/images/{name}.png`
- **错误输出**: 明确的错误信息和解决建议

### 3.7 依赖

| 依赖 | 安装方式 | 用途 |
|------|----------|------|
| `openai >= 1.0` | `pip install --upgrade "openai>=1.0"` | 调用 Ark API |
| `ARK_API_KEY` | 环境变量 / `opencode.jsonc` | API 认证 |

## 4. 技术方案

### 4.1 为什么用 OpenAI SDK 而非 curl

- Ark 平台提供 OpenAI 兼容接口，SDK 调用更简洁
- 自动处理重试、超时、错误码解析
- 和项目现有 Python 生态一致
- 代码量更少，可维护性更好

### 4.2 核心脚本

```python
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
    print("   或在 opencode.jsonc 中添加环境变量配置")
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
```

### 4.3 错误处理

| 错误场景 | 检测方式 | 处理方式 |
|----------|----------|----------|
| `ARK_API_KEY` 未设置 | `os.environ.get()` 返回 None | 提示设置方法，退出 |
| `openai` 包未安装 | `import openai` 失败 | 提示安装命令 |
| 参数不足 | `len(sys.argv) < 3` | 显示用法说明，退出 |
| API 调用失败 | `except Exception` 捕获所有 API 异常 | 显示错误信息，退出（不重试，避免浪费额度） |
| 图片下载失败 | `urllib` 异常 | 显示 URL 和错误，退出 |
| 图片下载超时 | `urlopen(timeout=30)` 超时 | 显示超时错误，退出 |
| 非法文件名 | 正则清理非安全字符 | 自动替换为 `_` |

### 4.4 安全措施

| 措施 | 实现方式 |
|------|----------|
| 路径遍历防护 | `re.sub(r'[^a-zA-Z0-9_\-\\u4e00-\\u9fff]', '_', NAME)` 过滤特殊字符 |
| 下载超时 | `urllib.request.urlopen(url, timeout=30)` |
| API Key 保护 | 仅从环境变量读取，不硬编码 |
| 临时文件清理 | Agent 执行完毕后删除临时脚本文件 |

### 4.5 文件覆盖策略

同名文件已存在时直接覆盖（不提示、不备份），符合幂等调用场景。

### 4.6 .gitignore 更新

图片为生成产物，不应提交到仓库。需在 `.gitignore` 中添加：

```
content/images/
```

(在已有的 `content/draft/` 等条目旁)

### 4.7 安装检查

技能启动时，Agent 应执行：

```bash
# 检查 openai 包
python3 -c "import openai" 2>/dev/null || pip install --upgrade "openai>=1.0"

# 检查 API Key
if [ -z "$ARK_API_KEY" ]; then
    echo "❌ 请先设置 ARK_API_KEY 环境变量"
    exit 1
fi
```

## 5. 与现有管线的集成

### 5.1 与 `/image-prompt` 的关系

```
/image-prompt          → 生成提示词文本（对话中输出）
/image-generate        → 将提示词转化为实际图片文件
```

两个命令独立调用，不自动串联。Agent 在 `/image-prompt` 完成后，如果用户要求生成图片，再调用本技能。

### 5.2 与 `/to-wechat` 的关系

`/to-wechat` 生成的 HTML 排版文件可以引用 `content/images/` 目录下的图片。Agent 在排版时可以自动将 `content/images/` 中的图片嵌入 HTML。

### 5.3 管线位置

```
⑧ /image-prompt  →  ⑨ /image-generate (本技能)  →  ⑦ /to-wechat (排版时引用图片)
```

## 6. 文件结构

```
.opencode/skills/image-generate/
└── SKILL.md              # 技能定义文件
```

单文件技能，无需额外脚本文件。SKILL.md 内包含完整的 Python 脚本，Agent 执行时通过 Bash 工具写入临时文件并执行。

## 7. 测试计划

### 测试用例

| # | 场景 | 输入 | 预期结果 |
|---|------|------|----------|
| 1 | 正常生成 | prompt="一只猫", name="test-cat" | `content/images/test-cat.png` 存在且为有效 PNG |
| 2 | API Key 缺失 | ARK_API_KEY 未设置 | 提示错误，退出码非0 |
| 3 | 指定 model | model="doubao-seedream-4-5-251128" | 使用指定模型 |
| 4 | 指定 size | size="1K" | 生成 1K 尺寸图片 |
| 5 | 中文 prompt | prompt="星际穿越，黑洞" | 正常生成并保存 |
| 6 | 目录不存在 | content/images/ 不存在 | 自动创建目录 |
| 7 | 文件名清理 | name="../../etc/passwd" | 保存为 `content/images/____etc_passwd.png` |
| 8 | .gitignore | 检查 .gitignore | `content/images/` 条目存在 |
| 9 | 缺少参数 | 只传 1 个参数 | 显示用法说明，退出 |

### 验证方式

```bash
# 测试文件名清理
python3 -c "
import re
name = '../../etc/passwd'
name = re.sub(r'[^a-zA-Z0-9_\-]', '_', name).strip('_')
assert name == '____etc_passwd', f'Expected ____etc_passwd, got {name}'
print('✓ 文件名清理测试通过')
"

# 验证 .gitignore
grep -q 'content/images/' .gitignore && echo "✓ .gitignore 条目存在"

# 验证生成的文件是有效 PNG
file content/images/test-cat.png | grep -q 'PNG image data' && echo "✓ 文件为有效 PNG"
```

## 8. 自审查

- [x] 无 "TBD" 或 "TODO" 占位符
- [x] 参数定义与脚本实现一致
- [x] 错误处理覆盖所有已知场景
- [x] 与现有技能风格一致（frontmatter + Bash 工具 + 内嵌脚本）
- [x] 非目标明确列出，避免范围蔓延
- [x] 依赖清单完整（openai >= 1.0, ARK_API_KEY）