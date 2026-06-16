# wechat-format Skill 代码审查与优化设计

**日期**: 2026-06-16
**范围**: `.opencode/skills/wechat-format/`
**类型**: 代码审查 → 修复计划

---

## 概述

对 `wechat-format` skill 进行全面代码审查，核心文件 `scripts/format.py`（1763 行）是单文件 Python 脚本，负责 Markdown → 微信兼容 HTML 的排版转换。审查发现以下关键问题需要优先修复。

---

## 一、P0 级别问题（必须立即修复）

### P0-1: 微信主流程缺少 CJK 间距修复和加粗标点修复

**位置**: `scripts/format.py:1671-1681` vs `:1566-1568`

**问题描述**:

`format_for_output()` 函数在预处理阶段正确调用了 `fix_cjk_spacing()` 和 `fix_cjk_bold_punctuation()`，但该函数仅用于 `--format html` 和 `--format plain` 路径。主要的微信输出路径（`--gallery` 和单主题模式）在 `main()` 函数中自行实现了预处理流程，**遗漏了这两个关键修复**。

```python
# format_for_output() — 正确的预处理（第1566-1568行）
content = fix_cjk_spacing(content)
content = fix_cjk_bold_punctuation(content)

# main() — 遗漏的预处理（第1671-1681行）
content = strip_frontmatter(content)
content = process_callouts(content)
# ❌ 缺少 fix_cjk_spacing(content)
# ❌ 缺少 fix_cjk_bold_punctuation(content)
content = process_manual_footnotes(content)
```

**影响**:
- SKILL.md 宣称的 "CJK 间距修复：中英文/数字之间自动加空格" 在实际微信输出中**完全失效**
- SKILL.md 宣称的 "加粗标点修复：`**文字，**` → `**文字**，`" 在实际微信输出中**完全失效**
- 只影响 `--format html` 和 `--format plain`，不影响微信格式

**修复方案**:

**方案 A（推荐）**: `main()` 统一调用 `format_for_output()` 处理所有格式

```python
# 在 main() 中，用 format_for_output() 替代重复的预处理逻辑
result = format_for_output(content, input_path, theme, output_dir, vault_root, "wechat")
html = result["html"]
footnote_html = result["footnote_html"]
```

**方案 B**: 在 `main()` 的手动预处理流程中补上缺少的调用

```python
content = strip_frontmatter(content)
content = fix_cjk_spacing(content)           # ← 补上
content = fix_cjk_bold_punctuation(content)   # ← 补上
content = process_callouts(content)
```

**推荐方案 A**: 统一调用 `format_for_output()` 消除代码重复，单一数据流，未来修改只需改一处。

---

### P0-2: 消除 `main()` 与 `format_for_output()` 的代码重复

**位置**: `scripts/format.py:1549-1614` 与 `:1670-1706`

**问题描述**:

`format_for_output()` 和 `main()` 各自实现了几乎相同的 Markdown 预处理流程（strip_frontmatter、process_callouts、process_manual_footnotes、process_fenced_containers、convert_wikilinks、copy_markdown_images、md_to_html），维护两套逻辑容易产生不一致（如 P0-1）。

**修复方案**:

与 P0-1 合并修复：`main()` 中所有格式分支统一通过 `format_for_output()` 处理。

```python
# main() 重构后
result = format_for_output(content, input_path, theme, output_dir, vault_root, args.format)
html = result["html"]
footnote_html = result["footnote_html"]

if args.gallery:
    # gallery 模式：使用 result 中的 html/footnote 并行渲染
    ...
else:
    # 单主题模式：直接使用 result
    html = inject_inline_styles(html, theme)  # format_for_output 已做
    ...
```

**注意**: 需要验证 `format_for_output()` 中是否包含了 `~~删除线~~` 的处理（`re.sub(r'~~(.+?)~~', r'<del>\1</del>', content)`），目前该处理只在 `main()` 中存在。

---

## 二、P1 级别问题（应尽快修复）

### P1-1: `convert_wikilinks` 文件句柄泄漏

**位置**: `scripts/format.py:293`

```python
_cfg = _json.load(open(config_path, encoding="utf-8"))
```

`open()` 未使用 `with` 上下文管理器，也未显式关闭。

**修复方案**:

```python
with open(config_path, encoding="utf-8") as f:
    _cfg = _json.load(f)
```

---

### P1-2: `convert_wikilinks` 使用 `os.walk(followlinks=True)` 有无限循环风险

**位置**: `scripts/format.py:308`

```python
for root, dirs, files in os.walk(search_root, followlinks=True):
```

如果存在循环符号链接，`followlinks=True` 会导致无限循环。且每次图片搜索都对整个 vault 做全量遍历，O(n×m) 复杂度。

**修复方案**:

1. 构建文件名 → 路径的索引字典（执行一次）
2. 移除 `followlinks=True` 或添加 `os.path.realpath()` 循环检测
3. 使用 `pathlib.rglob()` 替代 `os.walk`

```python
# 一次性构建索引
_image_index: dict[str, Path] = {}
def _build_image_index(search_roots: list[Path]) -> None:
    for root in search_roots:
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file() and not p.is_symlink():
                    _image_index[p.name] = p

def replace_img(match):
    filename = match.group(1).strip().split("|")[0]
    if filename in _image_index:
        img_path = _image_index[filename]
        images_dir.mkdir(parents=True, exist_ok=True)
        dest = images_dir / filename
        if not dest.exists():
            shutil.copy2(img_path, dest)
        return f'<section data-role="img-wrapper"><img src="images/{filename}" alt="{filename}"></section>'
    return f'<span style="color:#999;">[图片: {filename}]</span>'
```

---

### P1-3: `convert_wikilinks` 中不必要的重新导入

**位置**: `scripts/format.py:291`

```python
import json as _json
```

`json` 已在文件顶部（第14行）导入，此处重复导入是无用代码，应删除。

---

## 三、P2 级别问题（代码质量改进）

### P2-1: `generate_gallery` 中 `selected-theme.txt` 使用全局而非 per-article 路径

**位置**: `scripts/format.py:1541`

```python
(OUTPUT_DIR / "selected-theme.txt").write_text(default_theme, encoding="utf-8")
```

使用全局 `OUTPUT_DIR`（`content/wechat/`），而非 per-article 的 `output_dir`（`content/wechat/{文章名}/`），多篇文章同时运行会互相覆盖。

**修复方案**:

```python
(output_dir / "selected-theme.txt").write_text(default_theme, encoding="utf-8")
```

---

### P2-2: Gallery GROUPS 硬编码与 GALLERY_THEMES 不同步

**位置**: `scripts/format.py:1491-1497` 与 `:46-57`

`GROUPS` 在 `generate_gallery()` 中硬编码，与顶层 `GALLERY_THEMES` 独立维护。添加新主题时必须同时更新两个位置。

**修复方案**:

在主题 JSON 中添加 `category` 字段，画廊自动按分类分组：

```json
// themes/terracotta.json
{
  "name": "赤陶",
  "category": "文艺随笔",
  ...
}
```

然后修改 `generate_gallery()` 按 `category` 字段自动分组：

```python
from collections import defaultdict
groups = defaultdict(list)
for tid in theme_ids:
    cat = theme_map[tid].get("category", "其他")
    groups[cat].append(tid)
```

---

### P2-3: `_build_dialogue_html` 多说话人左右分配不合理

**位置**: `scripts/format.py:692`

```python
side = "left" if speakers_seen.index(speaker) % 2 == 0 else "right"
```

3 个以上说话人时，第 3 人 (index=2) 与第 1 人 (index=0) 同侧。

**修复方案**:

保持每个说话人的侧边不变（使用 dict 缓存而非 list.index），或支持在 markdown 中显式指定 `[left]`/`[right]`：

```markdown
:::dialogue[采访实录]
Alice: 你好
Bob: 你好
Alice: 最近怎么样    ← Alice 应始终在同一侧
:::
```

```python
speaker_sides = {}
for line in lines:
    ...
    if speaker not in speaker_sides:
        speaker_sides[speaker] = "left" if len(speaker_sides) % 2 == 0 else "right"
    side = speaker_sides[speaker]
```

---

### P2-4: `convert_image_captions` 只能匹配 `<p><em>` 格式的图说

**位置**: `scripts/format.py:1440-1450`

正则仅匹配 `</section>` 后紧跟的 `<p><em>xxx</em></p>`，但如果图片不是通过 `img_wrapper` 包裹（CDN 外链），或图说使用纯文本 `<p>` 格式，则无法匹配。

**修复方案**:

支持更广泛的后缀匹配（图片元素后的第一个 `<p>` 内容较短的段落）：

```python
# 匹配图片标签后的短段落作为图说
img_pattern = r'(<(?:img|section data-role="img-wrapper")[^>]*>.*?</(?:section)>\s*)<p[^>]*>(.{1,80})</p>'
```

---

### P2-5: `_basic_syntax_highlight` 正则高亮器局限性

**位置**: `scripts/format.py:795-872`

手写正则 + 关键字集合存在以下局限：
- 无法正确处理字符串内转义（`"hello \"world\""`）
- 无法区分注释中的关键字
- 不支持多行字符串
- 不支持模板字符串内的表达式 `${}`

**修复方案**:

替换为 Pygments 库：

```python
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

def _syntax_highlight(code: str, language: str) -> str:
    lexer = get_lexer_by_name(language, stripall=True)
    formatter = HtmlFormatter(style='monokai', noclasses=True)
    return highlight(code, lexer, formatter)
```

**权衡**: 引入 Pygments 依赖会增加安装复杂度。如果不想引入外部依赖，至少改进现有正则以处理字符串内转义。

---

### P2-6: `_inject_container_styles` 容器样式全部硬编码

**位置**: `scripts/format.py:881-1129`

所有容器样式（dialogue, gallery, longimage, stat, timeline, steps, compare, quote）都硬编码在函数中，仅 accent 色从主题读取。

**修复方案**:

在主题 JSON 的 `styles` 中增加容器样式字段（可选，有默认值）：

```json
{
  "styles": {
    "container_dialogue": {
      "margin_top": "20px",
      ...
    }
  }
}
```

修改 `_inject_container_styles()` 先读取主题配置，缺失时使用内置默认值。

---

## 四、架构优化建议

### 建议 1: 拆分 `format.py` 为模块

**现状**: 1763 行单文件。

**建议拆分**:

```
scripts/
├── format.py          # CLI 入口 + 编排 (~100行)
├── parser.py          # Markdown 预处理（CJK、callout、容器、脚注）
├── styles.py          # 主题加载、内联样式注入、深色模式
├── containers.py      # 围栏容器 HTML 构建（dialogue/gallery/timeline等）
├── templates.py       # 预览/画廊 HTML 生成
└── highlight.py       # 语法高亮
```

### 建议 2: 添加类型注解

为关键函数添加类型提示，提高可维护性：

```python
def load_theme(theme_name: str) -> dict[str, Any]: ...
def inject_inline_styles(html: str, theme: dict[str, Any], skip_wrapper: bool = False) -> str: ...
def format_for_output(content: str, input_path: Path, theme: dict, ...) -> dict[str, str]: ...
```

### 建议 3: 模板渲染使用 Jinja2

当前使用 `{{PLACEHOLDER}}` + `.replace()` 渲染 HTML 模板，对于复杂的条件渲染（如 gallery 中的推荐标记、分组标签）不够灵活。改用 Jinja2 可以减少 Python 代码中的 HTML 拼接。

### 建议 4: 添加单元测试

至少为核心函数添加测试覆盖：

| 函数 | 测试要点 |
|------|----------|
| `fix_cjk_spacing()` | 中英文、中数字间距 |
| `fix_cjk_bold_punctuation()` | `**文字，**` → `**文字**，` |
| `process_fenced_containers()` | 各容器类型解析 |
| `extract_links_as_footnotes()` | 外链 → 脚注转换 |
| `inject_inline_styles()` | 样式注入正确性 |
| `convert_lists_to_sections()` | 列表转换 + 嵌套 |
| `convert_image_captions()` | 图说识别 |

---

## 五、修复执行计划

### Wave 1 — P0 修复（必须立即修复）

| 任务 | 描述 | 文件 | 预估工作量 |
|------|------|------|-----------|
| T1 | 统一 `main()` 调用 `format_for_output()`，消除代码重复 | `format.py` | 中 |
| T2 | 补回 `~~删除线~~` 处理到 `format_for_output()` | `format.py` | 小 |
| T3 | 验证 CJK 间距和加粗标点修复在微信输出中生效 | `format.py` | 小 |

### Wave 2 — P1 修复（应尽快修复）

| 任务 | 描述 | 文件 | 预估工作量 |
|------|------|------|-----------|
| T4 | 修复 `convert_wikilinks` 文件句柄泄漏 | `format.py` | 小 |
| T5 | 移除重复 `import json` | `format.py` | 小 |
| T6 | 构建图片索引替代 `os.walk(followlinks=True)` | `format.py` | 中 |

### Wave 3 — P2 改进（代码质量）

| 任务 | 描述 | 文件 | 预估工作量 |
|------|------|------|-----------|
| T7 | 修复 `selected-theme.txt` 路径 | `format.py` | 小 |
| T8 | 主题 JSON 添加 `category` 字段，自动分组 | `format.py` + 30个主题 | 中 |
| T9 | 修复多说话人对话侧边分配逻辑 | `format.py` | 小 |
| T10 | 改进图说识别正则 | `format.py` | 小 |
| T11 | 容器样式支持主题覆盖 | `format.py` + 主题 | 大 |

### Wave 4 — 架构优化（长期）

| 任务 | 描述 | 预估工作量 |
|------|------|-----------|
| T12 | 拆分 format.py 为模块 | 大 |
| T13 | 添加类型注解 | 中 |
| T14 | 模板引擎改用 Jinja2 | 中 |
| T15 | 添加单元测试 | 大 |
| T16 | 语法高亮改用 Pygments | 中 |

---

## 六、风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 重构 `main()` 引入新 bug | 中 | 逐格式验证（wechat/html/plain），保留旧代码作为 reference |
| 图片索引构建影响启动性能 | 低 | 惰性构建，首次使用时才建立索引 |
| Pygments 依赖增加安装复杂度 | 低 | 作为可选依赖，fallback 到手写高亮 |
| 主题 JSON 格式变更影响现有主题 | 低 | `category` 和容器样式字段均为可选，有默认值 |

---

## 附录: 文件清单

```
.opencode/skills/wechat-format/
├── SKILL.md                 # 使用文档
├── config.json              # 配置文件
├── scripts/
│   └── format.py            # 主排版引擎（1763行）
├── templates/
│   ├── preview.html         # 手机预览模板（269行）
│   └── gallery.html         # 主题画廊模板（434行）
└── themes/                  # 30个主题 JSON 文件
    ├── terracotta.json
    ├── bytedance.json
    ├── ...
    └── wechat-native.json
```