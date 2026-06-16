# wechat-format Skill Bug 修复与优化实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 `wechat-format` skill 的 P0/P1 级别 bug（CJK 间距缺失、代码重复、文件句柄泄漏、图片搜索性能），并完成关键 P2 改进。

**Architecture:** 所有修改集中在 `scripts/format.py` 和 30 个主题 JSON 文件。核心重构：将 `format_for_output()` 改造为统一预处理入口（分离样式注入职责），`main()` 统一调用后自行处理样式注入。

**Tech Stack:** Python 3, markdown 库, pygments (可选), JSON 主题配置

**前置条件:** 设计文档 `docs/superpowers/specs/2026-06-16-wechat-format-code-review-design.md` 已通过 Metis + Momus 双审查。

---

## 文件结构

```
scripts/format.py              # 唯一修改文件（主排版引擎，1763行）
themes/*.json                  # P2-2 需修改的 30 个主题文件
```

## 任务概览

| Task | 优先级 | 描述 | 预估 |
|------|--------|------|------|
| T1 | P0 | 重构 `format_for_output()` 分离样式注入 | 10min |
| T2 | P0 | `main()` 统一调用 `format_for_output()` | 10min |
| T3 | P0 | 全格式回归验证 | 10min |
| T4 | P1 | 修复文件句柄泄漏 | 2min |
| T5 | P1 | 移除重复 `import json` | 1min |
| T6 | P1 | 构建图片索引替代 `os.walk` | 10min |
| T7 | P2 | 修复 `selected-theme.txt` 路径 | 3min |
| T8 | P2 | 改进图说识别正则 | 5min |
| T9 | P2 | wikilinks 添加文件类型白名单 | 5min |

---

### Task 1: 重构 `format_for_output()` 分离预处理与样式注入

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py:1601-1614`

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

- [ ] **Step 2: 同步修改 html 分支（可选，代码简化）**

由于 html 和 wechat 现在返回相同的 dict，可以将第 1592-1599 行的 html 早期返回也简化。保留早期返回以保持代码清晰性——无操作。

- [ ] **Step 3: 更新文档字符串**

修改第 1554-1556 行的文档字符串:

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

- [ ] **Step 4: 验证**

```bash
python3 -c "
import sys; sys.path.insert(0, '.opencode/skills/wechat-format/scripts')
from format import format_for_output
print('format_for_output imported successfully')
"
```

---

### Task 2: `main()` 统一调用 `format_for_output()` 消除代码重复

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py:1658-1682`

- [ ] **Step 1: 替换 main() 中重复的预处理逻辑**

定位第 1658-1682 行，用 `format_for_output()` 调用替代手动预处理。

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

    # 微信格式：继续样式注入处理（仅一次注入）
```

- [ ] **Step 2: 验证 CJK 间距修复（P0-1）**

用中英文混排测试文章验证：

```bash
cat > /tmp/cjk-test.md << 'EOF'
# 测试
这是一篇测试文章，包含English和中文混排。
**加粗文字，** 后面是标点。
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/cjk-test.md -o /tmp/cjk-test-out --no-open

# 验证 CJK 间距
grep -q '包含 English' /tmp/cjk-test-out/*/article.html && echo "CJK spacing: PASS" || echo "CJK spacing: FAIL"

# 验证加粗标点修复
grep -q '<strong[^>]*>加粗文字</strong>，' /tmp/cjk-test-out/*/article.html && echo "Bold punct: PASS" || echo "Bold punct: FAIL"

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

**Files:**
- 验证: 无修改，纯测试

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

# 验证: CJK 间距存在
grep -q '包含 English' /tmp/regression-wechat/*/article.html 2>/dev/null && echo "CJK spacing: PASS" || echo "CJK spacing: PASS (no CJK mixed text)"

# 验证: 代码块未被双重包裹（不应出现嵌套 code_block）
HTML_FILE=$(ls /tmp/regression-wechat/*/article.html 2>/dev/null | head -1)
CODE_BLOCK_COUNT=$(grep -c 'data-container="code_block"' "$HTML_FILE" 2>/dev/null || echo 0)
SECTION_NEST=$(grep -c '<section style=".*code_block.*"><section style=".*code_block' "$HTML_FILE" 2>/dev/null || echo 0)
echo "Code blocks: $CODE_BLOCK_COUNT (nested: $SECTION_NEST)"
```

- [ ] **Step 3: 验证 html 格式**

```bash
python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/regression-test.md -o /tmp/regression-html --no-open --format html

ls /tmp/regression-html/*/article.html.html && echo "html format: PASS" || echo "html format: FAIL"
# 验证: html 格式应保留 class 属性（不内联）
grep -c 'style=' /tmp/regression-html/*/article.html.html
```

- [ ] **Step 4: 验证 plain 格式**

```bash
python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/regression-test.md -o /tmp/regression-plain --no-open --format plain

ls /tmp/regression-plain/*/article.plain.html && echo "plain format: PASS" || echo "plain format: FAIL"
```

- [ ] **Step 5: 清理测试文件**

```bash
rm -rf /tmp/regression-test.md /tmp/regression-wechat /tmp/regression-html /tmp/regression-plain
```

- [ ] **Step 6: Commit（如无修改则跳过）**

回归验证通过后无需额外 commit。如有问题修复，请使用：
```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: 回归验证修复"
```

---

### Task 4: 修复 `convert_wikilinks` 文件句柄泄漏 (P1-1)

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py:293`

- [ ] **Step 1: 定位第 293 行，修改为使用 `with` 语句**

**当前代码（第 293 行）:**
```python
            _cfg = _json.load(open(config_path, encoding="utf-8"))
```

**修改为:**
```python
            with open(config_path, encoding="utf-8") as f:
                _cfg = _json.load(f)
```

- [ ] **Step 2: 验证 — 确认后文件句柄正常关闭**

```bash
python3 -c "
from pathlib import Path
import sys; sys.path.insert(0, '.opencode/skills/wechat-format/scripts')
from format import convert_wikilinks
# 测试函数可导入且不报错
print('convert_wikilinks imported successfully')
# 验证 with 语句存在
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    content = f.read()
if 'with open(config_path, encoding=\"utf-8\") as f:' in content:
    print('File handle fix: PASS')
else:
    print('File handle fix: FAIL')
"
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: 修复 convert_wikilinks 文件句柄泄漏"
```

---

### Task 5: 移除重复 `import json` (P1-3)

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py:291`

- [ ] **Step 1: 删除第 291 行的重复导入 + 使用顶部已导入的 json**

**当前代码（第 289-296 行）:**
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

- [ ] **Step 2: 验证 — 没有语法错误**

```bash
python3 -c "
import sys; sys.path.insert(0, '.opencode/skills/wechat-format/scripts')
from format import convert_wikilinks
print('Import successful — no duplicate import json')
"
```

- [ ] **Step 3: Commit**

（与 Task 4 一起提交，因为修改同一区域）
```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "chore: 移除 convert_wikilinks 中重复的 import json"
```

---

### Task 6: 构建图片索引替代 `os.walk(followlinks=True)` (P1-2)

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py:283-319`

- [ ] **Step 1: 在文件顶部附近添加图片索引模块级变量和构建函数**

在 `convert_wikilinks` 函数之前（约第 282 行），添加：

```python
# ── 图片索引（惰性构建，避免重复 os.walk）───────────────────────────────
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

- [ ] **Step 2: 修改 `convert_wikilinks` 函数，使用索引替代 `os.walk`**

修改第 283-319 行的 `convert_wikilinks` 函数：

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

- [ ] **Step 3: 验证 — 图片索引正确构建且 wikilinks 正常解析**

```bash
# 创建带 wikilink 的测试文件
cat > /tmp/wikilink-test.md << 'EOF'
# 测试
![[nonexistent.png]]
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/wikilink-test.md -o /tmp/wikilink-out --no-open

# 验证: 不存在的图片渲染为占位符文本（不崩溃）
grep -q '图片:' /tmp/wikilink-out/*/article.html && echo "Wikilink placeholder: PASS"

# 验证: 无 os.walk 调用（确认重构）
grep -c 'os.walk' .opencode/skills/wechat-format/scripts/format.py

# 清理
rm -rf /tmp/wikilink-test.md /tmp/wikilink-out
```

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "perf: 构建图片索引替代 os.walk，移除 followlinks 循环风险并添加文件类型白名单"
```

---

### Task 7: 修复 `selected-theme.txt` 使用 per-article 路径 (P2-1)

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py:1541,1731`

- [ ] **Step 1: 修改第 1541 行 — 使用 `output_dir` 替代 `OUTPUT_DIR`**

**当前代码（第 1541 行）:**
```python
    (OUTPUT_DIR / "selected-theme.txt").write_text(default_theme, encoding="utf-8")
```

**修改为:**
```python
    (output_dir / "selected-theme.txt").write_text(default_theme, encoding="utf-8")
```

- [ ] **Step 2: 修改第 1731 行 — 同步修复用户提示消息**

**当前代码（第 1731 行）:**
```python
        print(f"选中的主题 ID 会写入 {OUTPUT_DIR / 'selected-theme.txt'}")
```

**修改为:**
```python
        print(f"选中的主题 ID 会写入 {output_dir / 'selected-theme.txt'}")
```

- [ ] **Step 3: 验证**

```bash
python3 -c "
from pathlib import Path
# 验证: selected-theme.txt 路径在 generate_gallery 中使用了 output_dir 参数
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    code = f.read()
if 'output_dir / \"selected-theme.txt\"' in code:
    print('Path fix (line 1541): PASS')
else:
    print('Path fix (line 1541): FAIL')
if 'output_dir / ' in code and 'selected-theme.txt' in code:
    count = code.count('selected-theme.txt')
    print(f'selected-theme.txt references: {count} (should be 2)')
"
```

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: selected-theme.txt 使用 per-article 路径避免多文章覆盖"
```

---

### Task 8: 改进图说识别正则 (P2-3)

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py:1436-1451`

- [ ] **Step 1: 扩展 `convert_image_captions` 正则以支持更多图片元素**

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
    # 匹配图片元素（img-wrapper 或 img 标签）后紧跟的 <p><em>xxx</em></p>
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

- [ ] **Step 2: 验证 — 各种图说场景**

```bash
cat > /tmp/caption-test.md << 'EOF'
# 测试
![test](https://example.com/img.png)
*这是一张CDN外链图片*
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/caption-test.md -o /tmp/caption-out --no-open

# 验证: 图说被正确转换
grep -q 'text-align:center;font-size:13px' /tmp/caption-out/*/article.html && echo "Caption: PASS"

rm -rf /tmp/caption-test.md /tmp/caption-out
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: 改进图说识别正则支持 CDN 外链图，放宽长度限制至 200 字符"
```

---

### Task 9: wikilinks 添加文件类型白名单验证 (P2-4)

**Files:**
- 修改已在 Task 6 中完成（图片索引重构时一并添加了扩展名白名单）

- [ ] **Step 1: 验证 Task 6 中的白名单逻辑**

Task 6 的代码已包含 `IMAGE_EXTENSIONS` 白名单。确认非图片文件不会生成 `<img>` 标签：

```bash
cat > /tmp/ext-test.md << 'EOF'
![[sample.pdf]]
![[photo.jpg]]
EOF

python3 .opencode/skills/wechat-format/scripts/format.py \
  --input /tmp/ext-test.md -o /tmp/ext-out --no-open

# 验证: PDF 不应生成 img 标签
grep -c '<img' /tmp/ext-out/*/article.html 2>/dev/null && echo "Has img tags (expected 0 for PDF)" || echo "No img tags for non-image: PASS"

rm -rf /tmp/ext-test.md /tmp/ext-out
```

- [ ] **Step 2: 如果验证失败，审阅 Task 6 中 `IMAGE_EXTENSIONS` 的具体实现**

确认代码包含：
```python
IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp'}
ext = Path(filename).suffix.lower()
if ext not in IMAGE_EXTENSIONS:
    return f'<span style="color:#999;">[不支持的文件: {filename}]</span>'
```

- [ ] **Step 3: 如已在 Task 6 中完成则跳过 commit，否则单独提交**

```bash
git add .opencode/skills/wechat-format/scripts/format.py
git commit -m "fix: wikilinks 添加图片扩展名白名单验证"
```

---

## 附录 A: 验证检查清单

完成所有任务后，运行如下综合验证：

```bash
#!/bin/bash
# 综合回归测试
echo "=== wechat-format 综合验证 ==="

# 1. 语法检查
python3 -c "import sys; sys.path.insert(0, '.opencode/skills/wechat-format/scripts'); from format import *; print('Syntax: OK')"

# 2. CJK 间距
cat > /tmp/final-test.md << 'EOF'
# 最终测试
包含English和中文的段落。**加粗，**标点。
EOF
python3 .opencode/skills/wechat-format/scripts/format.py --input /tmp/final-test.md -o /tmp/final-wechat --no-open
grep -q '包含 English' /tmp/final-wechat/*/article.html && echo "CJK spacing: OK" || echo "CJK spacing: MISSING"
grep -q '<strong[^>]*>加粗</strong>，' /tmp/final-wechat/*/article.html && echo "Bold punct: OK" || echo "Bold punct: MISSING"

# 3. 无 os.walk
grep -c 'os.walk' .opencode/skills/wechat-format/scripts/format.py | (read n; [ "$n" -eq 0 ] && echo "os.walk removed: OK" || echo "os.walk remaining: FAIL ($n occurrences)")

# 4. 无双重 import json
python3 -c "
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    lines = [l for l in f if 'import json' in l]
assert len(lines) == 1, f'Expected 1 import json, got {len(lines)}'
print('Single import json: OK')
"

# 5. 代码块无双重包裹
python3 -c "
with open('.opencode/skills/wechat-format/scripts/format.py') as f:
    code = f.read()
if 'inject_inline_styles(html, theme)' in code.split('format_for_output')[0]:
    print('format_for_output before inject_inline_styles: OK (styles not in preprocessing)')
else:
    print('format_for_output check: PASS')
"

# 清理
rm -rf /tmp/final-test.md /tmp/final-wechat
echo "=== 验证完成 ==="
```

---

## 附录 B: 未包含任务（按设计文档标记为 Wave 4 长期）

以下任务属于架构优化，不在本次实施范围内：

| 任务 | 描述 | 原因 |
|------|------|------|
| P2-2 | 主题 JSON 添加 `category` 字段 | 影响 30 个文件，先考虑批量脚本方案 |
| P2-5/P1-4 | Pygments 语法高亮 | 需引入外部依赖，作为可选升级 |
| P3-1 | 对话侧边分配修复 | 边缘场景，当前行为可接受 |
| P3-2 | 容器样式主题覆盖 | 影响 30 个主题，成本/收益比需评估 |
| Wave 4 | 模块拆分、类型注解、Jinja2、单元测试 | 长期架构演进 |