# image-generate 技能 .env 自动加载 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修改 `.opencode/skills/image-generate/SKILL.md`，在 Python 内嵌脚本中添加 `load_env()` 函数，自动从项目根目录加载 `.env` 文件。

**Architecture:** 在 heredoc 内的 Python 脚本中新增 `load_env()` 函数（零外部依赖），在参数解析后、API Key 检查前调用。同时更新前置说明和错误处理表。

**Tech Stack:** Python 标准库（`os`、`subprocess`），无额外依赖。

---

### Task 1: 更新「前置依赖」说明 - .env 自动加载

**Files:**
- Modify: `.opencode/skills/image-generate/SKILL.md:21-27`

- [ ] **Step 1: 修改前置依赖说明，添加 .env 自动加载的支持说明**

将原来只要求设置 `ARK_API_KEY` 环境变量的说明，改为同时说明可以从 `.env` 文件自动加载。

改动内容：

```markdown
### 1. API Key

需要设置 `ARK_API_KEY` 环境变量，或将其写入项目根目录的 `.env` 文件。

技能启动时会自动从项目根目录的 `.env` 文件加载环境变量。如 `.env` 不存在或无法读取，则仅依赖已设置的 shell 环境变量。

设置方式（任选其一）：

```bash
# 方式一：export 环境变量
export ARK_API_KEY='your-api-key'

# 方式二：写入 .env 文件（技能自动加载）
echo "ARK_API_KEY='your-api-key'" >> .env
```
```

- [ ] **Step 2: 验证 Markdown 格式正确**

Read `.opencode/skills/image-generate/SKILL.md` lines 19-37, verify no broken code fences.

---

### Task 2: 在 Python heredoc 中添加 `load_env()` 函数

**Files:**
- Modify: `.opencode/skills/image-generate/SKILL.md` — 在 heredoc 内 Python 脚本的 import 之后、业务逻辑之前插入 `load_env()` 函数

- [ ] **Step 1: 确定插入位置**

SKILL.md 中 heredoc 的边界是：
```
cat > /tmp/image-generate.py << 'PYEOF'
```
和
```
PYEOF
```

需要在整个导入块的最后（`from openai import OpenAI` 之后）、`# === 参数解析 ===` 之前插入 `load_env()` 函数。

- [ ] **Step 2: 插入 `load_env()` 函数**

在 Python 脚本（heredoc 内部）的 import 块之后添加：

```python
def load_env():
    """从项目根目录加载 .env 文件（如有），不覆盖已存在的环境变量。
    
    如 .env 不存在或无法读取，静默跳过（仍依赖已设置的环境变量）。
    加载所有变量，不限于 ARK_API_KEY。
    重复 key 时优先采用先出现者（因 key not in os.environ 检查）。
    """
    # 定位项目根目录
    try:
        import subprocess
        root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        ).stdout.strip()
    except Exception:
        root = os.getcwd()

    env_path = os.path.join(root, ".env")
    if not os.path.isfile(env_path):
        return  # .env 不存在，静默跳过

    # 读取并解析 .env，任何 I/O 错误都静默回退
    try:
        with open(env_path, encoding="utf-8-sig") as f:  # utf-8-sig 兼容 Windows BOM
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                if "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip()
                # 剥掉行内注释（# 之前的部分）
                inline_comment = val.find(" #")
                if inline_comment >= 0:
                    val = val[:inline_comment].strip()
                # 剥掉引号
                if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                    val = val[1:-1]
                # 仅当未设置时才写入（先出现者获胜）
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:
        pass  # 任何 I/O 错误（权限、编码等）静默跳过
```

- [ ] **Step 3: 在参数解析后添加 `load_env()` 调用**

在 Python 脚本的 `# === 参数解析 ===` 块之后（SIZE = ... 赋值之后）、`# === 文件名清理 ===` 之前，插入：

```python
# === 加载 .env 环境变量 ===
load_env()
```

- [ ] **Step 4: 验证 Python 语法**

运行以下命令验证 heredoc 中的 Python 代码语法正确：

```bash
# 从 SKILL.md 提取 heredoc 内的 Python 代码并检查语法
python3 -c "
import re
with open('.opencode/skills/image-generate/SKILL.md') as f:
    content = f.read()
# 提取 PYEOF heredoc 区域
# 注意：heredoc 分隔符在 SKILL.md 中是 << 'PYEOF'，正则需要匹配末尾引号
match = re.search(r"cat > /tmp/image-generate\.py << 'PYEOF'\n(.+?)\nPYEOF", content, re.DOTALL)
if not match:
    print('❌ 未找到 heredoc')
    exit(1)
code = match.group(1)
# 编译检查语法
compile(code, '<skills>', 'exec')
print('✅ Python 语法检查通过')
"
```

---

### Task 3: 更新错误处理表

**Files:**
- Modify: `.opencode/skills/image-generate/SKILL.md` — 错误表（约第 172-183 行）

- [ ] **Step 1: 在错误处理表中追加 .env 相关行**

在现有错误表末尾插入：

```
| `.env` 不存在 | `os.path.isfile()` 返回 False | 静默跳过，依赖已有环境变量 |
| `.env` 权限不足 | `open()` 抛出 `PermissionError` 或被 try/except 捕获 | 静默跳过，依赖已有环境变量 |
| `.env` 编码异常 | `open(encoding="utf-8-sig")` 抛出 `UnicodeError` | 被 try/except 捕获，静默跳过 |
| `.env` 格式错误 | 行内无 `=` | 跳过该行，继续解析 |
| 行内注释 | 检测值中的 ` #` | 截断 ` #` 之后的内容 |
```

- [ ] **Step 2: 验证 Markdown 表格格式**

Read SKILL.md 中错误处理表，确认表格对齐、不缺少行。

---

### Task 4: 运行 11 个验证场景

> ⚠️ 所有场景都在项目根目录执行（`cd "$(git rev-parse --show-toplevel)"`）。
> ⚠️ 每个场景独立验证，场景间不依赖。前置设置/后置清理在每个场景内完成。
> ⚠️ 所有场景共享同一个 `/tmp/image-generate.py`（由 Step 0 提取一次即可）。

- [ ] **Step 0: 从修改后的 SKILL.md 提取 heredoc 到 /tmp/image-generate.py**

在运行任何场景前，需要先写出测试用的 Python 脚本：

```bash
cd "$(git rev-parse --show-toplevel)"
python3 -c "
import re
with open('.opencode/skills/image-generate/SKILL.md') as f:
    content = f.read()
match = re.search(r\"cat > /tmp/image-generate\.py << 'PYEOF'\n(.+?)\nPYEOF\", content, re.DOTALL)
if not match:
    print('❌ 未找到 heredoc')
    exit(1)
with open('/tmp/image-generate.py', 'w') as out:
    out.write(match.group(1))
print('✅ 已写出 /tmp/image-generate.py')
"
```

- [ ] **Step 1: 备份用户现有 .env（所有场景共享）**

```bash
# 在项目根目录执行
cd "$(git rev-parse --show-toplevel)"
# 备份现有 .env（如有）
if [ -f .env ]; then
    cp .env .env.bak.testing
    echo "✅ 已备份 .env → .env.bak.testing"
else
    echo "ℹ️ .env 不存在，无需备份"
fi
```

- [ ] **Step 2: 场景 1 - 成功路径**

```bash
cd "$(git rev-parse --show-toplevel)"
unset ARK_API_KEY
echo 'ARK_API_KEY=test-key-123' > .env
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：通过 key 检查，到达 API 调用（报 API 错误而非"未设置"）
```

- [ ] **Step 3: 场景 2 - .env 缺失**

```bash
cd "$(git rev-parse --show-toplevel)"
unset ARK_API_KEY
mv .env .env.scenario2 2>/dev/null || true
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：报"未设置 ARK_API_KEY"
mv .env.scenario2 .env 2>/dev/null || true
```

- [ ] **Step 4: 场景 3 - 环境变量优先**

```bash
cd "$(git rev-parse --show-toplevel)"
export ARK_API_KEY=prefer-me
echo 'ARK_API_KEY=wrong' > .env
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：使用 prefer-me（到达 API 调用）
unset ARK_API_KEY
```

- [ ] **Step 5: 场景 4 - 引号处理**

```bash
cd "$(git rev-parse --show-toplevel)"
echo 'ARK_API_KEY="quoted-key"' > .env
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：提取 quoted-key（到达 API 调用）
```

- [ ] **Step 6: 场景 5 - 注释+空行**

```bash
cd "$(git rev-parse --show-toplevel)"
printf '# comment line\n\nARK_API_KEY=after-comment\n' > .env
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：跳过注释和空行，提取 after-comment（到达 API 调用）
```

- [ ] **Step 7: 场景 6 - export 前缀**

```bash
cd "$(git rev-parse --show-toplevel)"
echo 'export ARK_API_KEY=exported-key' > .env
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：提取 exported-key（到达 API 调用）
```

- [ ] **Step 8: 场景 7 - 行内注释**

```bash
cd "$(git rev-parse --show-toplevel)"
echo 'ARK_API_KEY=val # comment' > .env
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：值为 val（不含 # comment），到达 API 调用
```

- [ ] **Step 9: 场景 8 - 权限错误**

```bash
cd "$(git rev-parse --show-toplevel)"
echo 'ARK_API_KEY=cant-read' > .env
chmod 000 .env
unset ARK_API_KEY
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：不崩溃，回退到"未设置"
chmod 644 .env
```

- [ ] **Step 10: 场景 9 - BOM 编码**

```bash
cd "$(git rev-parse --show-toplevel)"
# 用 Python 写一个带 BOM 的 .env
python3 -c "
with open('.env', 'w', encoding='utf-8-sig') as f:
    f.write('ARK_API_KEY=bom-key\n')
"
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：正确解析 bom-key（到达 API 调用）
```

- [ ] **Step 11: 场景 10 - 非 git 目录**

```bash
cd "$(git rev-parse --show-toplevel)"
mkdir -p /tmp/test-no-git
echo 'ARK_API_KEY=no-git-key' > /tmp/test-no-git/.env
cd /tmp/test-no-git
echo 'test prompt' | python3 /tmp/image-generate.py 'test-image'
# 预期：回退到 os.getcwd()，找到 .env，到达 API 调用
cd "$(git rev-parse --show-toplevel)"
rm -rf /tmp/test-no-git
```

- [ ] **Step 12: 场景 11 - 加载所有变量（不仅限于 ARK_API_KEY）**

```bash
cd "$(git rev-parse --show-toplevel)"
cat > .env << 'EOF'
ARK_API_KEY=test-all-vars-key
MY_CUSTOM_VAR=hello-world
ANOTHER_VAR=42
EOF
# 用一个简单的 Python 脚本来验证所有变量都被加载
python3 -c "
import sys
sys.path.insert(0, '/tmp')
import importlib.util
spec = importlib.util.spec_from_file_location('img_gen', '/tmp/image-generate.py')
# 不执行脚本全部，只提取 load_env 并验证
import ast, os
with open('/tmp/image-generate.py') as f:
    tree = ast.parse(f.read())
# 找到 load_env 调用并手动执行
exec(open('/tmp/image-generate.py').read().split('load_env()')[0] + '\nload_env()\n')
assert os.environ.get('MY_CUSTOM_VAR') == 'hello-world', f'MY_CUSTOM_VAR expected hello-world, got {os.environ.get(\"MY_CUSTOM_VAR\")}'
assert os.environ.get('ANOTHER_VAR') == '42', f'ANOTHER_VAR expected 42, got {os.environ.get(\"ANOTHER_VAR\")}'
print('✅ 场景 11 通过：非 ARK_API_KEY 变量也被正确加载')
"
```

- [ ] **Step 13: 恢复用户的 .env**

```bash
cd "$(git rev-parse --show-toplevel)"
if [ -f .env.bak.testing ]; then
    mv .env.bak.testing .env
    echo "✅ 已恢复 .env"
else
    rm -f .env
    echo "ℹ️ 无备份，已清理测试 .env"
fi
rm -f /tmp/image-generate.py
echo "✅ 临时文件已清理"
```

---

### Task 5: 最终验证

- [ ] **Step 1: 确认 SKILL.md 结构完整无损坏**

```bash
cd "$(git rev-parse --show-toplevel)"
python3 -c "
import re
with open('.opencode/skills/image-generate/SKILL.md') as f:
    content = f.read()

# 1. 确认 heredoc 分隔符未被破坏
assert \"<< 'PYEOF'\" in content, '❌ heredoc 开始分隔符 << \\'PYEOF\\' 丢失'
assert content.count('PYEOF') >= 2, '❌ PYEOF 分隔符数量异常'

# 2. 确认 load_env() 函数存在于 heredoc 内
match = re.search(r\"cat > /tmp/image-generate\.py << 'PYEOF'\n(.+?)\nPYEOF\", content, re.DOTALL)
assert match, '❌ 未找到 heredoc 区域'
code = match.group(1)
assert 'def load_env()' in code, '❌ heredoc 内未找到 load_env() 函数'
assert 'load_env()' in code.split('def load_env()')[1] or 'load_env()' in code, '❌ load_env() 调用未找到'

# 3. 验证 Python 语法
compile(code, '<skills>', 'exec')
print('✅ Python 语法检查通过')

# 4. 确认 load_env() 调用在 API key 检查之前
param_pos = code.find('# === 参数解析 ===')
keycheck_pos = code.find('os.environ.get(\"ARK_API_KEY\")')
loadenv_call_pos = code.rfind('load_env()')
# 参数解析应该在 load_env 之前 ? 不，设计中 load_env 在参数解析之后、key 检查之前
assert loadenv_call_pos > param_pos, '❌ load_env() 应在参数解析之后'
assert loadenv_call_pos < keycheck_pos, '❌ load_env() 调用应在 API Key 检查之前'
print('✅ 调用顺序正确')

# 5. 确认前置依赖说明已更新
assert '.env' in content[:200], '❌ 前置依赖中未提及 .env 自动加载'
assert '自动加载' in content[:200] or '写入项目根目录的 .env' in content[:200], '❌ 前置依赖说明未更新'
print('✅ 前置依赖说明已更新')

# 6. 确认错误处理表已更新
error_table_section = content[content.find('错误场景'):]
assert '.env' in error_table_section, '❌ 错误处理表中未包含 .env 相关条目'
print('✅ 错误处理表已更新')

print('\\n🎉 所有验证通过！')
"
```

- [ ] **Step 2: 确认 .env 不会被提交**

```bash
cd "$(git rev-parse --show-toplevel)"
git check-ignore .env >/dev/null 2>&1 && echo "✅ .env 已被 gitignore" || echo "⚠️ .env 未被 gitignore，请检查 .gitignore"
```

- [ ] **Step 3: 确认内容改动边界**

```bash
cd "$(git rev-parse --show-toplevel)"
git diff .opencode/skills/image-generate/SKILL.md
# 确认只改动：
#   1. 「前置依赖」节（约第 21-40 行）
#   2. heredoc 内 Python 脚本（新增 load_env 函数 + 调用）
#   3. 错误处理表（新增 .env 相关行）
# 不应有对 bash 包装器和其他部分的改动
```
