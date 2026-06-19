# 图片生成技能 — 自动加载 .env 环境变量

**日期**: 2026-06-18  
**状态**: 已审查，待实施  
**审查人**: Metis (Plan Consultant)  
**关联**: `.opencode/skills/image-generate/SKILL.md`  

---

## 1. 背景

项目根目录已存在 `.env` 文件，包含 `ARK_API_KEY`。但当前 `image-generate` 技能不会自动加载它——如果 `ARK_API_KEY` 未通过其他方式（如 bash export）设置，脚本会直接报错退出。

需要让技能在运行时自动检测并加载项目根目录的 `.env` 文件，减少手动配置步骤。

## 2. 设计决策

| 决策 | 选择 | 原因 |
|------|------|------|
| 加载方式 | **Python 内嵌解析** | 零额外依赖，与现有 `allowed-tools: Bash` 兼容 |
| 路径检测 | **git 项目根目录** | 与现有 `cd "$(git rev-parse --show-toplevel)"` 一致 |
| .env 不存在 | **静默跳过** | 兼容无 .env 的环境（如 CI/CD 通过 export 设置） |
| 变量优先级 | **环境变量 > .env** | `os.environ` 中已存在的值不会被 .env 覆盖 |

## 3. 实现方案

### 3.1 Python 函数

在 `/tmp/image-generate.py` 中添加 `load_env()` 函数：

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

### 3.2 调用时机

在 `main` 逻辑的最前面调用 `load_env()`，早于 `os.environ.get("ARK_API_KEY")` 检查。

### 3.3 注意事项

1. **Python 中 git 检测是冗余但防御性的**：bash 包装器已 `cd` 到 git 根目录，Python 再次检测是作为后备（当 bash 的 git 检测失败时）。不要"清理"掉。
2. **`load_env()` 加载 *.env* 中所有变量**，不限于 `ARK_API_KEY`。这是有意为之，方便未来扩展。
3. **重复 key 采用"先出现者获胜"**（因 `key not in os.environ` 检查）。注意这不是常见的"后出现者获胜"行为。

### 3.4 SKILL.md 中的改动位置

| 位置 | 改动 |
|------|------|
| 前置条件说明 | 更新「前置依赖」节，说明支持从 `.env` 自动加载 |
| Python 脚本 heredoc | 新增 `load_env()` 函数 + 调用 |
| 错误处理表 | 新增 `.env` 相关错误行（见第 6 节） |

## 4. 不变的部分

- bash 包装脚本的步骤不受影响
- 参数传递方式（stdin + argv）不变
- 错误处理策略不变（仅新增 .env 自动加载）
- 安全措施不变（.env 中的值仅在 Python 进程内生效）

## 5. 风险与缓解

| 风险 | 缓解 |
|------|------|
| `.env` 中有 shell 敏感字符 | 在 Python 中解析，不经过 shell，无注入风险 |
| 其他 skill 也需加载 `.env` | 此为独立修改，不影响其他 skill |
| `.env` 路径无法通过 git 检测 | 回退到 `os.getcwd()`，与 bash 中逻辑一致 |
| `.env` 权限不足 / 编码异常 | `open()` 外部包裹 `try/except`，任何 I/O 错误静默跳过 |
| heredoc 语法错误 | 修改后人工验证 Python 语法（`python3 -c "compile(...)"`）|

## 6. 更新后的错误处理表

在现有错误处理表中增加以下行：

| 错误场景 | 检测方式 | 处理方式 |
|----------|----------|----------|
| `.env` 不存在 | `os.path.isfile()` 返回 False | 静默跳过，依赖已有环境变量 |
| `.env` 权限不足 | `open()` 抛出 `PermissionError` | 被 `load_env()` 的 try/except 捕获，静默跳过 |
| `.env` 编码异常 | `open()` 抛出 `UnicodeError` | 被 `load_env()` 的 try/except 捕获，静默跳过 |
| `.env` 格式错误 | 行内无 `=` | 跳过该行，继续解析下一行 |
| 行内注释 | 检测值中的 ` #` | 截断 ` #` 之后的内容 |

## 7. 验证方案（10 个场景）

| # | 场景 | 步骤 | 预期 |
|---|------|------|------|
| 1 | 成功路径 | 创建 `.env` 含 `ARK_API_KEY=test-key-123`，取消设置环境变量后运行脚本 | 通过 key 检查，到达 API 调用（预期报 API 错误，非"未设置"） |
| 2 | .env 缺失 | 移除/重命名 `.env`，取消设置 `ARK_API_KEY` | 报"未设置 ARK_API_KEY" |
| 3 | 环境变量优先 | `export ARK_API_KEY=prefer-me` + .env 含不同值 | 使用 `prefer-me` |
| 4 | 引号处理 | .env 含 `ARK_API_KEY="quoted-key"` | 提取 `quoted-key` |
| 5 | 注释+空行 | .env 含 `# 注释行` 和空行 | 跳过，正常解析有效行 |
| 6 | export 前缀 | .env 含 `export ARK_API_KEY=exported-key` | 提取 `exported-key` |
| 7 | 行内注释 | .env 含 `ARK_API_KEY=val # comment` | 值为 `val`（不含 ` # comment`） |
| 8 | 权限错误 | `chmod 000 .env` | 不崩溃，回退到"未设置" |
| 9 | BOM 编码 | 以 UTF-8 BOM 保存 .env | 正确解析 |
| 10 | 非 git 目录 | 在 git 树外运行 | 回退到 `os.getcwd()` |

## 8. 自审查

- [x] 无 "TBD" 或 "TODO" 占位符
- [x] 与现有 Python 脚本风格一致
- [x] 错误处理覆盖所有预期场景（文件不存在、解析异常）
- [x] 非目标明确：不改动 bash 包装、不改动其他 skill
- [x] 变量优先级行为明确：环境变量 > .env
