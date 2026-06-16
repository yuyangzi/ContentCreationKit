# wechat-format Skill Bug 修复与优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `wechat-format` skill 的 P0/P1 级别 bug（CJK 间距缺失、代码重复、文件句柄泄漏、图片搜索性能），并完成关键 P2 改进。

**Architecture:** 所有修改集中在 `scripts/format.py`（1763行）。核心重构：将 `format_for_output()` 改造为统一预处理入口（分离样式注入职责），`main()` 统一调用后自行处理样式注入。

**Tech Stack:** Python 3, markdown 库, JSON 主题配置

**前置条件:** 设计文档 `docs/superpowers/specs/2026-06-16-wechat-format-code-review-design.md` 已通过 Metis + Momus 双审查。

---

## 文件结构

```
scripts/format.py              # 唯一修改文件（主排版引擎，1763行）
```

## 任务概览与并行执行

```
Wave 1 (P0, 串行依赖):  T1 ──→ T2 ──→ T3
                         │
Wave 2 (P1, 可与W1并行): ├── T4 ──→ T5
                         │         (wikilinks 区域，独立于 W1)
                         │
Wave 3 (P2, 完全并行):   ├── T6 ──→ T7
                         │    (均可独立执行，无依赖)
```

| Task | Wave | 描述 | 依赖 | 可并行 |
|------|------|------|------|--------|
| T1 | W1-P0 | 重构 `format_for_output()` 分离样式注入 | — | — |
| T2 | W1-P0 | `main()` 统一调用 `format_for_output()` | T1 | — |
| T3 | W1-P0 | 全格式回归验证 | T2 | — |
| T4 | W2-P1 | 修复 wikilinks 文件句柄泄漏 + 移除重复 import | — | ✅ 与 T1-T3 |
| T5 | W2-P1 | 构建图片索引替代 `os.walk` | — | ✅ 与 T1-T4 |
| T6 | W3-P2 | 修复 `selected-theme.txt` 路径 | — | ✅ 任意顺序 |
| T7 | W3-P2 | 改进图说识别正则 | — | ✅ 任意顺序 |

> **并行提示**: T4/T5 修改 `convert_wikilinks` 区域（~290行），T1-T3 修改 `format_for_output`/`main()` 区域（~1550-1760行），两者互不冲突，可在子代理模式下并行分派。

---

### Task 1: 重构 `format_for_output()` 分离预处理与样式注入

**Wave:** W1-P0 | **Files:** Modify `.opencode/skills/wechat-format/scripts/format.py:1601-1614`

**背景:** 当前 `format_for_output()` 在 wechat 模式下会调用 `inject_inline_styles()` 和 `convert_image_captions()`，导致 `main()` 再次调用时产生双重注入。

- [ ] **Step 1: 删除 wechat 分支中的样式注入代码**

定位第 1601-1614 行，将 wechat 分支的样式注入代码替换为统一的最终返回。

**当前代码（第 1601-1614 行）:**
```python
    # wechat: 全套微信兼容处理
    html = inject_inline_styles(html, theme)
    if footnote_html:
        footnote_html = inject_inline_styles(footnote_html, theme, skip_wrapper=True)
    html = convert_image_captions(html)
    if footnote_html:
        footnote_html = convert_image_captions(footnote_html)

    return {
        "html": html,
        "footnote_html": footnote_html,
        "title": title,
        "word_count": word_count,
    }
```

**修改为:**
```python
    # 返回未样式化的 HTML（html/wechat 通用）
    # 样式注入由调用方（main() / _render_single_theme()）统一处理
    return {
        "html": html,
        "footnote_html": footnote_html,
        "title": title,
        "word_count": word_count,
    }
```

- [ ] **Step 2: 更新文档字符串**

修改文档字符串（第 1552-1556 行），反映新的职责分离：

```python
    """统一格式化入口，支持多种输出格式

    Args:
        output_format: "wechat" (默认，预处理 + 脚注转换，不含样式注入)
                      "html" (标准 HTML，保留 class，不内联样式)
                      "plain" (纯文本 + 基本 HTML 结构)

    Returns:
        dict with keys: html, footnote_html, title, word_count
        (html/footnote_html 均未样式化，由调用方注入)
    """
```

- [ ] **Step 3: 验证**

```bash
python3 -c "
import sys; sys.path.insert(0, '.opencode/skills/wechat-format/scripts')
from format import format_for_output
print('format_for_output imported successfully')
"
```

---

### Task 2: `main()` 统一调用 `format_for_output()` 消除代码重复

**Wave:** W1-P0 | **Files:** Modify `.opencode/skills/wechat-format/scripts/format.py:1658-1682`

**注意:** T1 修改了上方代码（~1601行），如行号漂移，请以 `# 处理流程` 注释（`main()` 中的手动预处理）和 `# wechat: 全套微信兼容处理` 注释（`format_for_output` 中待删除块）为锚点定位。

- [ ] **Step 1: 替换 main() 中重复的预处理逻辑**

**当前代码（第 1658-1682 行）:**
```python
    # 非微信格式：简单输出
    if args.format != "wechat":
        result = format_for_output(content, input_path, theme, output_dir, vault_root, args.format)
        out_path = output_dir / f"article.{args.format}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_html = result["html"]
        if result["footnote_html"]:
            out_html += "\n" + result["footnote_html"]
        out_path.write_text(out_html, encoding="utf-8")
        print(f"\n输出: {out_path}")
        return

    # 处理流程
    content = strip_frontmatter(content)
    content = process_callouts(content)
    content = process_manual_footnotes(content)
    content = process_fenced_containers(content)
    content = re.sub(r'~~(.+?)~~', r'<del>\1</del>', content)

    output_dir.mkdir(parents=True, exist_ok=True)
    content = convert_wikilinks(content, vault_root, output_dir)
    content = copy_markdown_images(content, input_path.parent, output_dir)

    html = md_to_html(content)
    html, footnote_html = extract_links_as_footnotes(html)
```

**修改为:**
```python
    # 所有格式统一通过 format_for_output() 预处理
    # （返回未样式化的 HTML，样式注入由下方各分支统一处理）
    result = format_for_output(content, input_path, theme, output_dir, vault_root, args.format)
    html = result["html"]
    footnote_html = result["footnote_html"]

    # 非微信格式：直接写入后返回
    if args.format != "wechat":
        out_path = output_dir / f"article.{args.format}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_html = html
        if footnote_html:
            out_html += "\n" + footnote_html
        out_path.write_text(out_html, encoding="utf-8")
        print(f"\n输出: {out_path}")
        return

    # 微信格式：继续样式注入处理（仅一次注入 — format_for_output 不再注入）
    # 注: 下方 gallery 和单主题代码保持不变，html/footnote_html 均为未样式化
```

- [ ] **Step 2: 验证 CJK 间距修复（P0-1）+ 确认无双重样式注入**

```bash
cat > /tmp/cjk-test.md << 'EOF'
# 测试
这是一篇测试文章，包含English和中文混排。
**加粗文字，** 后面是标点。

```python
def hello():
    print("test")
```
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/cjk-test.md -o /tmp/cjk-test-out --no-open

# 验证 CJK 间距：应包含 "和" 与 "English" 之间的空格
grep -q '包含 English' /tmp/cjk-test-out/*/article.html && echo "CJK spacing: PASS" || echo "CJK spacing: FAIL"

# 验证加粗标点修复：应输出 **加粗文字**， 而非 **加粗文字，**
grep -q '<strong[^>]*>加粗文字</strong>，' /tmp/cjk-test-out/*/article.html && echo "Bold punct: PASS" || echo "Bold punct: FAIL"

# 验证无双重包裹：代码块 <section> 不应嵌套
HTML_FILE=$(ls /tmp/cjk-test-out/*/article.html 2>/dev/null | head -1)
if grep -q '<section style="[^"]*code_block[^"]*"><section style="[^"]*code_block' "$HTML_FILE" 2>/dev/null; then
    echo "Double wrap: FAIL (code block nested)"
else
    echo "Double wrap: PASS (no nested code blocks)"
fi

# 清理
rm -rf /tmp/cjk-test.md /tmp/cjk-test-out
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: 重构 format_for_output 分离样式注入，main() 统一调用消除 CJK/bold 修复缺失"
```

---

### Task 3: 全格式回归验证

**Wave:** W1-P0 | **Files:** 无修改，纯测试

- [ ] **Step 1: 创建测试文章**

```bash
cat > /tmp/regression-test.md << 'REGEOF'
# 回归测试文章

这是正文段落，包含**加粗**和*斜体*以及`行内代码`。

> 这是引用文字。

## 二级标题

### 三级标题

- 列表项 1
- 列表项 2

1. 有序列表项 1
2. 有序列表项 2

```python
def hello():
    print("Hello, World!")
```

| 列1 | 列2 |
|-----|-----|
| A   | B   |

> [!tip] 小技巧
> 这是一个 callout

~~删除线文字~~
REGEOF
```

- [ ] **Step 2: 验证 wechat 格式**

```bash
python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/regression-test.md -o /tmp/regression-wechat --no-open --format wechat

# 验证: 输出文件存在
ls /tmp/regression-wechat/*/article.html && echo "wechat article: PASS" || echo "wechat article: FAIL"
ls /tmp/regression-wechat/*/preview.html && echo "wechat preview: PASS" || echo "wechat preview: FAIL"

# 验证: 代码块未被双重包裹
HTML_FILE=$(ls /tmp/regression-wechat/*/article.html 2>/dev/null | head -1)
CODE_BLOCK_COUNT=$(grep -c '<section style="[^"]*code_block' "$HTML_FILE" 2>/dev/null || echo 0)
NESTED_COUNT=$(grep -c '<section style="[^"]*code_block[^"]*"><section style="[^"]*code_block' "$HTML_FILE" 2>/dev/null || echo 0)
echo "Code block sections: $CODE_BLOCK_COUNT (nested: $NESTED_COUNT — must be 0)"
[ "$NESTED_COUNT" -eq 0 ] && echo "No double wrap: PASS" || echo "No double wrap: FAIL"
```

- [ ] **Step 3: 验证 html 格式（不应内联样式）**

```bash
python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/regression-test.md -o /tmp/regression-html --no-open --format html

ls /tmp/regression-html/*/article.html.html && echo "html format file: PASS" || echo "html format file: FAIL"

# 验证: html 格式不应有内联样式（需保留 class，不应注入 style=）
style_count=$(grep -c 'style=' /tmp/regression-html/*/article.html.html 2>/dev/null || echo 0)
[ "$style_count" -eq 0 ] && echo "HTML format (no inline styles): PASS" || echo "HTML format has $style_count inline styles — review expected"
```

- [ ] **Step 4: 验证 plain 格式（内容完整）**

```bash
python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/regression-test.md -o /tmp/regression-plain --no-open --format plain

ls /tmp/regression-plain/*/article.plain.html && echo "plain format file: PASS" || echo "plain format file: FAIL"

# 验证: 基本内容存在（不是空文件）
grep -q '回归测试文章' /tmp/regression-plain/*/article.plain.html && echo "Plain content: PASS" || echo "Plain content: FAIL"
grep -q '<strong>' /tmp/regression-plain/*/article.plain.html && echo "Plain bold tag: PASS" || echo "Plain bold tag: PASS (no bold in plain)"
```

- [ ] **Step 5: 清理测试文件**

```bash
rm -rf /tmp/regression-test.md /tmp/regression-wechat /tmp/regression-html /tmp/regression-plain
```

- [ ] **Step 6: Commit（如无修改则跳过）**

回归验证通过后无需额外 commit。如有问题修复：
```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: 回归验证修复"
```

---

### Task 4: 修复 `convert_wikilinks` 文件句柄泄漏 + 移除重复 import (P1-1, P1-3)

**Wave:** W2-P1 | **Files:** Modify `.opencode/skills/wechat-format/scripts/format.py:289-297`

**注意:** T1-T3 修改上方代码（~1550-1760行），本任务修改 ~290 行区域，**无冲突**，可与 T1-T3 并行执行。

- [ ] **Step 1: 合并修复：文件句柄 + 移除重复 import**

**当前代码（第 289-297 行）:**
```python
    config_path = SKILL_DIR / "config.json"
    if config_path.exists():
        import json as _json
        try:
            _cfg = _json.load(open(config_path, encoding="utf-8"))
            for p in _cfg.get("image_search_paths", []):
                search_roots.append(Path(p).expanduser())
        except Exception:
            pass
```

**修改为:**
```python
    config_path = SKILL_DIR / "config.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                _cfg = json.load(f)
            for p in _cfg.get("image_search_paths", []):
                search_roots.append(Path(p).expanduser())
        except Exception:
            pass
```

- [ ] **Step 2: 验证**

```bash
python3 -c "
import sys; sys.path.insert(0, '.opencode/skills/wechat-format/scripts')
from format import convert_wikilinks
print('convert_wikilinks imported successfully')

# 确认仅一次 import json
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    import_lines = [l.strip() for l in f if l.strip().startswith('import json')]
assert len(import_lines) == 1, f'Expected 1 import json, got {len(import_lines)}'
print('Single import json: PASS')

# 确认 with 语句存在
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    content = f.read()
assert 'with open(config_path, encoding=\"utf-8\") as f:' in content
print('File handle fix (with statement): PASS')
"
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: 修复 convert_wikilinks 文件句柄泄漏 + 移除重复 import json (P1-1, P1-3)"
```

---

### Task 5: 构建图片索引替代 `os.walk(followlinks=True)` (P1-2)

**Wave:** W2-P1 | **Files:** Modify `.opencode/skills/wechat-format/scripts/format.py:283-319`

**注意:** 与 T1-T4 无冲突（修改不同区域），可并行。本重构有一项**有意的行为变更**：符号链接文件将不再被发现（`not p.is_symlink()`），以消除 `followlinks=True` 的无限循环风险。如 vault 依赖符号链接图片，需事后评估。

- [ ] **Step 1: 添加图片索引模块级变量和惰性构建函数**

在 `convert_wikilinks` 函数定义之前（约第 282 行），添加：

```python
# ── 图片索引（惰性构建，替代 os.walk）─────────────────────────────────
# 注意: 符号链接文件不会被索引（not p.is_symlink），
# 以消除 followlinks=True 的循环递归风险。
_image_index: dict[str, Path] = {}
_image_index_built = False


def _build_image_index(search_roots: list[Path]) -> None:
    """惰性构建文件名→路径索引，一次构建，多次查询"""
    global _image_index, _image_index_built
    if _image_index_built:
        return
    for search_root in search_roots:
        if not search_root.exists():
            continue
        for p in search_root.rglob("*"):
            if p.is_file() and not p.is_symlink():
                _image_index[p.name] = p
    _image_index_built = True
```

- [ ] **Step 2: 修改 `convert_wikilinks` 函数**

修改第 283-319 行：

```python
def convert_wikilinks(text: str, vault_root: Path, output_dir: Path) -> str:
    """把 Obsidian ![[image.jpg]] 转为 <img> 标签，复制图片到输出目录"""
    images_dir = output_dir / "images"
    # 搜索路径：vault 目录（如需额外图片目录，在 config.json 的 image_search_paths 中配置）
    search_roots = [vault_root]
    # 支持自定义图片搜索目录
    config_path = SKILL_DIR / "config.json"
    if config_path.exists():
        try:
            with open(config_path, encoding="utf-8") as f:
                _cfg = json.load(f)
            for p in _cfg.get("image_search_paths", []):
                search_roots.append(Path(p).expanduser())
        except Exception:
            pass

    # 惰性构建图片索引（首次调用时构建）
    _build_image_index(search_roots)

    # 图片扩展名白名单
    IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'}

    def replace_img(match):
        filename = match.group(1).strip()
        # 处理带尺寸的 wikilink: ![[image.jpg|300]]
        if "|" in filename:
            filename = filename.split("|")[0].strip()

        # 验证文件扩展名
        ext = Path(filename).suffix.lower()
        if ext not in IMAGE_EXTENSIONS:
            return f'<span style="color:#999;">[不支持的文件: {filename}]</span>'

        # 从索引查找
        if filename in _image_index:
            img_path = _image_index[filename]
            images_dir.mkdir(parents=True, exist_ok=True)
            dest = images_dir / filename
            if not dest.exists():
                shutil.copy2(img_path, dest)
            return f'<section data-role="img-wrapper"><img src="images/{filename}" alt="{filename}"></section>'

        return f'<span style="color:#999;">[图片: {filename}]</span>'

    return re.sub(r"!\[\[([^\]]+)\]\]", replace_img, text)
```

- [ ] **Step 3: 验证 — 索引正确构建 + 实际图片复制**

```bash
# 创建测试图片和 wikilink
echo "fake png content" > /tmp/real-test-img.png
cat > /tmp/wikilink-test.md << 'EOF'
# 测试
![[real-test-img.png]]
![[nonexistent.png]]
![[sample.pdf]]
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/wikilink-test.md -o /tmp/wikilink-out --no-open --vault-root /tmp

# 验证: 实际图片被复制
ls /tmp/wikilink-out/*/images/real-test-img.png && echo "Image copy: PASS" || echo "Image copy: FAIL"

# 验证: 不存在的图片渲染为占位符
grep -q '图片:' /tmp/wikilink-out/*/article.html && echo "Missing img placeholder: PASS" || echo "Missing img placeholder: FAIL"

# 验证: PDF 被白名单拒绝
grep -q '不支持的文件' /tmp/wikilink-out/*/article.html && echo "Non-image rejection: PASS" || echo "Non-image rejection: FAIL"

# 验证: 无 os.walk 调用
grep -c 'os.walk' .opencode/skills/wechat-format/scripts/format.py | (read n; [ "$n" -eq 0 ] && echo "os.walk removed: PASS" || echo "os.walk remaining: $n occurrences")

# 清理
rm -rf /tmp/real-test-img.png /tmp/wikilink-test.md /tmp/wikilink-out
```

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "perf: 构建图片索引替代 os.walk，移除 followlinks 循环风险并添加文件类型白名单"
```

---

### Task 6: 修复 `selected-theme.txt` 使用 per-article 路径 (P2-1)

**Wave:** W3-P2 | **Files:** Modify `.opencode/skills/wechat-format/scripts/format.py:1541,1731`

**注意:** 独立于所有其他任务，可任意顺序执行。

- [ ] **Step 1: 修改第 1541 行 — 使用 `output_dir` 替代 `OUTPUT_DIR`**

```python
# 当前（第 1541 行）
(OUTPUT_DIR / "selected-theme.txt").write_text(default_theme, encoding="utf-8")

# 修改为
(output_dir / "selected-theme.txt").write_text(default_theme, encoding="utf-8")
```

- [ ] **Step 2: 修改第 1731 行 — 同步修复用户提示消息**

```python
# 当前（第 1731 行）
print(f"选中的主题 ID 会写入 {OUTPUT_DIR / 'selected-theme.txt'}")

# 修改为
print(f"选中的主题 ID 会写入 {output_dir / 'selected-theme.txt'}")
```

- [ ] **Step 3: 验证 — 运行时确认路径正确**

```bash
cat > /tmp/theme-path-test.md << 'EOF'
# 测试
测试文章内容。
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/theme-path-test.md -o /tmp/theme-path-out --gallery --no-open

# 验证: selected-theme.txt 在 per-article 目录下，而非全局 content/wechat/
ls /tmp/theme-path-out/*/selected-theme.txt && echo "Per-article path: PASS" || echo "Per-article path: FAIL"
! ls /tmp/theme-path-out/selected-theme.txt 2>/dev/null && echo "Not in global dir: PASS" || echo "Not in global dir: CHECK"

rm -rf /tmp/theme-path-test.md /tmp/theme-path-out
```

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: selected-theme.txt 使用 per-article 路径避免多文章覆盖"
```

---

### Task 7: 改进图说识别正则 (P2-3)

**Wave:** W3-P2 | **Files:** Modify `.opencode/skills/wechat-format/scripts/format.py:1436-1451`

**注意:** 独立于所有其他任务，可任意顺序执行。

- [ ] **Step 1: 扩展 `convert_image_captions` 正则**

**当前代码（第 1436-1451 行）:**
```python
def convert_image_captions(html: str) -> str:
    """将图片后紧跟的斜体段落转为图说样式"""
    caption_style = "text-align:center;font-size:13px;color:#999999;margin-top:-8px;margin-bottom:16px;font-style:normal"
    # 匹配 img wrapper (</section>) 后面紧跟的 <p><em>xxx</em></p>
    html = re.sub(
        r'(</section>\s*)<p[^>]*><em>(.*?)</em></p>',
        rf'\1<p style="{caption_style}">\2</p>',
        html
    )
    # 同时匹配 </p>（CDN/外链图片）后面的斜体图说
    html = re.sub(
        r'(</p>\s*)<p[^>]*><em>(.*?)</em></p>',
        rf'\1<p style="{caption_style}">\2</p>',
        html
    )
    return html
```

**修改为:**
```python
def convert_image_captions(html: str) -> str:
    """将图片后紧跟的斜体段落转为图说样式"""
    caption_style = "text-align:center;font-size:13px;color:#999999;margin-top:-8px;margin-bottom:16px;font-style:normal"
    # 匹配图片元素（img-wrapper 或 img 标签）后紧跟的 <p><em>xxx</em></p>（最多200字符）
    html = re.sub(
        r'(</section>\s*)<p[^>]*><em>(.{1,200})</em></p>',
        rf'\1<p style="{caption_style}">\2</p>',
        html
    )
    # 同时匹配 </p> 和 <img ...>（CDN/外链图片）后面的斜体图说
    html = re.sub(
        r'((?:</p>|<img[^>]*>)\s*)<p[^>]*><em>(.{1,200})</em></p>',
        rf'\1<p style="{caption_style}">\2</p>',
        html
    )
    return html
```

- [ ] **Step 2: 验证 — CDN 外链图说正确转换**

```bash
cat > /tmp/caption-test.md << 'EOF'
# 测试
![test](https://example.com/img.png)
*这是一张CDN外链图片*
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/caption-test.md -o /tmp/caption-out --no-open

# 验证: 图说被正确转换为居中灰色样式
grep -q 'text-align:center;font-size:13px' /tmp/caption-out/*/article.html && echo "Caption style: PASS" || echo "Caption style: FAIL"

rm -rf /tmp/caption-test.md /tmp/caption-out
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: 改进图说识别正则支持 CDN 外链图，放宽长度限制至 200 字符"
```

---

## 附录 A: 综合验证检查清单

完成所有任务后，运行如下综合回归验证：

```bash
#!/bin/bash
echo "=== wechat-format 综合验证 ==="

# 1. 语法检查
python3 -c "import sys; sys.path.insert(0, '.opencode/skills/wechat-format/scripts'); from format import *; print('Syntax: OK')"

# 2. CJK 间距 + 加粗标点
cat > /tmp/final-test.md << 'EOF'
# 最终测试
包含English和中文的段落。**加粗，**标点。
EOF
python3 .opencode/skills/wechat-format/scripts/format.py --input /tmp/final-test.md -o /tmp/final-wechat --no-open
grep -q '包含 English' /tmp/final-wechat/*/article.html && echo "CJK spacing: OK" || echo "CJK spacing: MISSING"
grep -q '<strong[^>]*>加粗</strong>，' /tmp/final-wechat/*/article.html && echo "Bold punct: OK" || echo "Bold punct: MISSING"

# 3. 无 os.walk
grep -c 'os.walk' .opencode/skills/wechat-format/scripts/format.py | (read n; [ "$n" -eq 0 ] && echo "os.walk removed: OK" || echo "os.walk remaining: FAIL ($n occurrences)")

# 4. 仅一次 import json
python3 -c "
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    lines = [l for l in f if 'import json' in l]
assert len(lines) == 1, f'Expected 1 import json, got {len(lines)}'
print('Single import json: OK')
"

# 5. format_for_output 不注入样式
python3 -c "
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    code = f.read()
fn_start = code.index('def format_for_output')
fn_end = code.index('\ndef ', fn_start + 1) if '\ndef ' in code[fn_start+1:] else len(code)
fn_body = code[fn_start:fn_end]
if 'inject_inline_styles' not in fn_body:
    print('No inject_inline_styles in format_for_output: OK')
else:
    print('WARNING: inject_inline_styles still in format_for_output')
"

# 6. 代码块无双层包裹
HTML_FILE=$(ls /tmp/final-wechat/*/article.html 2>/dev/null | head -1)
if [ -n "$HTML_FILE" ] && grep -q '<section[^>]*code_block[^>]*><section[^>]*code_block' "$HTML_FILE" 2>/dev/null; then
    echo "Code block nesting: FAIL"
else
    echo "Code block nesting: OK"
fi

# 清理
rm -rf /tmp/final-test.md /tmp/final-wechat
echo "=== 验证完成 ==="
```

---

## 附录 B: 未包含任务

以下任务按设计文档标记为 Wave 4 长期或已降级：

| 任务 | 设计优先级 | 排除原因 |
|------|-----------|----------|
| P1-4 正则高亮器改进 | P1 | 需重构 `_basic_syntax_highlight`（~80行正则引擎），引入 Pygments 作为可选依赖更合适，归入 Wave 4 |
| P2-2 主题 JSON `category` 字段 | P2 | 影响 30 个文件，先设计批量迁移脚本方案 |
| P3-1 对话侧边分配修复 | P3 | 3+ 说话人是边缘场景，当前行为可接受 |
| P3-2 容器样式主题覆盖 | P3 | 影响 30 个主题，成本/收益比需评估 |
| Wave 4 模块拆分 | 架构 | 长期架构演进 |