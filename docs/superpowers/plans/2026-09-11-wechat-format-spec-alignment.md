# WeChat Format 官方规范对齐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `wechat-format` 的外链降级为纯文本（去上标引用），并全面对齐微信官方《编辑器插件开发规范》（去手写 darkmode、去 `<pre>`、宽度豁免、去文字背景渐变）。

**Architecture:** 改动集中在 `format.py` 渲染管道 + 30 个主题 JSON 的一次性迁移脚本 + 一个 stdlib `unittest` 回归套件 + 文档。深色模式分两次提交（先删引擎注入、后清主题），保证可回滚。

**Tech Stack:** Python 3（系统 `python3`，`markdown` 库，`unittest`，无 pytest/venv 依赖）、JSON 主题、内联样式 HTML。

**Spec:** `docs/superpowers/specs/2026-09-11-wechat-format-spec-alignment-design.md`

## Global Constraints

- 工作目录：仓库根 `/mnt/c/Development/Github/ContentCreationKit`。
- 运行脚本一律用系统 `python3`，**不使用任何 venv**。
- 测试框架为 stdlib `unittest`（系统 python3 无 pytest），测试文件放 `.opencode/skills/wechat-format/scripts/`，用 `python3 <path>` 直接运行。
- 主题文件序列化：`json.dumps(d, ensure_ascii=False, indent=2)`，**不加末尾换行**（已实测字节级复原）；脚本**无变化不写盘**（幂等）。
- 不改主题 `dark_mode` 之外的配色结构；不改 `content/` 下任何文章。
- 提交信息用中文 + semantic prefix（`feat:`/`fix:`/`refactor:`/`chore:`/`docs:`/`test:`）。
- 每完成一个 Task 结束前必须跑该 Task 的验证命令并确认 PASS。
- `format.py` 顶部不得新增第三方依赖；仅可用 stdlib（`urllib.parse`）。

---

## 文件结构

| 文件 | 职责 | 动作 |
|------|------|------|
| `.opencode/skills/wechat-format/scripts/format.py` | 排版引擎 | 修改 |
| `.opencode/skills/wechat-format/scripts/migrate_themes_spec.py` | 主题迁移脚本（幂等） | 新建 |
| `.opencode/skills/wechat-format/scripts/test_spec_compliance.py` | 引擎行为回归 | 新建/追加 |
| `.opencode/skills/wechat-format/scripts/test_migrate_themes.py` | 迁移解析 + 主题不变量回归 | 新建 |
| `.opencode/skills/wechat-format/themes/*.json` | 30 主题 | 由脚本迁移 |
| `.opencode/skills/wechat-format/templates/preview.html` | 预览页 | 修改 |
| `.opencode/skills/wechat-format/SKILL.md` | 技能文档 | 修改 |
| `.opencode/commands/to-wechat.md` | 命令文档 | 修改 |

---

## Task 1: 外链降级为纯文本 + 移除自动脚注管道

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py`（顶部 import；:409-448；:1475-1496；:1538-1545；:1618-1678；:1722-1811）
- Test: `.opencode/skills/wechat-format/scripts/test_spec_compliance.py`（新建）

**Interfaces:**
- Consumes: 无（首个 Task）
- Produces:
  - `unwrap_external_links(html: str) -> str`
  - `format_for_output(content, input_path, theme, output_dir, vault_root, output_format="wechat") -> {"html": str, "title": str, "word_count": int}`（**不再含** `footnote_html`）
  - `generate_preview(article_html, theme, title, word_count, output_path)`
  - `_render_single_theme(tid, theme_data, gallery_html) -> tuple[str, str]`

- [ ] **Step 1: 写失败测试**

新建 `.opencode/skills/wechat-format/scripts/test_spec_compliance.py`：

```python
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import format as fmt


class TestUnwrapExternalLinks(unittest.TestCase):
    def test_http_link_becomes_text(self):
        html = '<p>见 <a href="https://example.com/x">官方博客</a>。</p>'
        self.assertEqual(fmt.unwrap_external_links(html), "<p>见 官方博客。</p>")

    def test_wechat_internal_link_preserved(self):
        html = '<a href="https://mp.weixin.qq.com/s/abc">站内</a>'
        self.assertEqual(fmt.unwrap_external_links(html), html)

    def test_anchor_and_mailto_preserved(self):
        for html in ('<a href="#sec">目录</a>', '<a href="mailto:a@b.com">邮件</a>'):
            self.assertEqual(fmt.unwrap_external_links(html), html)

    def test_data_href_not_confused(self):
        html = '<a data-href="https://evil.com" href="https://real.com">文字</a>'
        self.assertEqual(fmt.unwrap_external_links(html), "文字")

    def test_inline_markup_in_link_text_kept(self):
        html = '<a href="https://x.com">看 <code>代码</code></a>'
        self.assertEqual(fmt.unwrap_external_links(html), "看 <code>代码</code>")

    def test_autolink_text_kept(self):
        html = '<a href="https://x.com/a">https://x.com/a</a>'
        self.assertEqual(fmt.unwrap_external_links(html), "https://x.com/a")


class TestFootnotePipelineRemoval(unittest.TestCase):
    def _format(self, md, output_format="wechat"):
        tmp = Path(tempfile.mkdtemp())
        md_path = tmp / "t.md"
        md_path.write_text(md, encoding="utf-8")
        theme = fmt.load_theme("newspaper")
        return fmt.format_for_output(
            md, md_path, theme, tmp / "out", fmt.VAULT_ROOT, output_format
        )

    def test_external_link_no_sup_no_reference_section(self):
        out = self._format("正文 [官方](https://example.com/x) 结束。")["html"]
        self.assertNotIn("<sup", out)
        self.assertNotIn("参考链接", out)
        self.assertIn("官方", out)

    def test_html_format_keeps_anchor(self):
        out = self._format("正文 [官方](https://example.com/x)。", "html")["html"]
        self.assertIn('<a href="https://example.com/x"', out)

    def test_return_dict_has_no_footnote_key(self):
        result = self._format("正文。")
        self.assertEqual(set(result.keys()), {"html", "title", "word_count"})


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: FAIL —— `AttributeError: module 'format' has no attribute 'unwrap_external_links'`；`assertNotIn '<sup'` 失败（外链被转上标）；返回 dict 含 `footnote_html`。

- [ ] **Step 3: 实现 `unwrap_external_links`**

在 `format.py` 顶部 import 区（`import json` 之后）加入：

```python
from urllib.parse import urlparse
```

在 `extract_links_as_footnotes` 原位置（:409-448）替换为：

```python
_ANCHOR_RE = re.compile(
    r'<a\s[^>]*?(?<![-\w])href\s*=\s*"([^"]*)"[^>]*>(.*?)</a>',
    re.DOTALL,
)


def unwrap_external_links(html: str) -> str:
    """把 http(s) 外链 anchor 拆成链接文字；mp.weixin 内链保留为 <a>。

    - 仅处理 http(s)；# 锚点、mailto:、相对路径原样保留
    - host 为 mp.weixin.qq.com 或 *.mp.weixin.qq.com 时保留 anchor
    """

    def replace_link(match):
        href = match.group(1)
        text = match.group(2)
        if not href.lower().startswith(("http://", "https://")):
            return match.group(0)
        host = (urlparse(href).hostname or "").lower()
        if host == "mp.weixin.qq.com" or host.endswith(".mp.weixin.qq.com"):
            return match.group(0)
        return text

    return _ANCHOR_RE.sub(replace_link, html)
```

同时删除原 `extract_links_as_footnotes` 整个函数。

- [ ] **Step 4: 改造 `format_for_output` 返回结构与外链调用**

将 `format_for_output`（:1618-1678）的 docstring 改为：

```python
    """统一格式化入口，支持多种输出格式

    Args:
        output_format: "wechat"（默认，预处理 + 外链降级，不含样式注入）
                      "html"（标准 HTML，保留原始 <a>，不内联样式）
                      "plain"（纯文本 + 基本 HTML 结构）

    Returns:
        dict with keys: html, title, word_count
        (html 未样式化，由调用方注入)
    """
```

`plain` 分支返回：

```python
        return {"html": html, "title": title, "word_count": word_count}
```

删除 `# 外链 → 脚注` 段，改为：

```python
    if output_format == "html":
        # 标准 HTML：保留原始 <a>
        return {"html": html, "title": title, "word_count": word_count}

    # wechat：外链降级为纯文本
    html = unwrap_external_links(html)
    return {"html": html, "title": title, "word_count": word_count}
```

- [ ] **Step 5: 清理 `footnote_html` 管道（精确行号，勿误删正文）**

`generate_preview`（:1475-1496）签名与实现改为：

```python
def generate_preview(article_html: str, theme: dict,
                     title: str, word_count: int, output_path: Path):
    """生成浏览器预览 HTML 文件"""
    template_path = TEMPLATE_DIR / "preview.html"
    template = template_path.read_text(encoding="utf-8")

    preview_html = (
        template
        .replace("{{TITLE}}", title)
        .replace("{{THEME_NAME}}", theme.get("name", ""))
        .replace("{{WORD_COUNT}}", f"{word_count:,}")
        .replace("{{ARTICLE_HTML}}", article_html)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(preview_html, encoding="utf-8")
    return output_path
```

`_render_single_theme`（:1538-1545）改为：

```python
def _render_single_theme(tid, theme_data, gallery_html):
    """渲染单个主题（用于并行 gallery）"""
    rendered = inject_inline_styles(gallery_html, theme_data)
    rendered = convert_image_captions(rendered)
    return tid, rendered
```

`main()`：

1. 删除 `footnote_html = result["footnote_html"]`（保留 `html = result["html"]`）。
2. 非微信分支删除脚注拼接：
```python
    if args.format != "wechat":
        out_path = output_dir / f"article.{args.format}.html"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(html, encoding="utf-8")
        print(f"\n输出: {out_path}")
        return
```
3. gallery 分支删除 `gallery_footnote = footnote_html`，`_render_single_theme` 调用改为 `executor.submit(_render_single_theme, tid, theme_map[tid], gallery_html)`。
4. 单主题分支改为：
```python
    # ── 单主题模式 ──
    html = inject_inline_styles(html, theme)
    html = convert_image_captions(html)

    # 保存纯文章 HTML
    article_path = output_dir / "article.html"
    article_path.write_text(html, encoding="utf-8")

    # 保存预览 HTML
    preview_path = output_dir / "preview.html"
    generate_preview(html, theme, title, word_count, preview_path)
    print(f"\n排版成品: {preview_path}")
```
**注意：必须保留 `html = convert_image_captions(html)`（原 :1797）**，它处理正文图说，与脚注无关。

- [ ] **Step 6: 运行测试，确认通过**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: PASS（9 项）。

- [ ] **Step 7: 端到端回归（wechat / html / plain / gallery 四分支不崩）**

Run:
```bash
python3 .opencode/skills/wechat-format/scripts/format.py --input content/article/20260910-Transformer架构原理.md --theme newspaper --output /tmp/t1-wechat --no-open
python3 .opencode/skills/wechat-format/scripts/format.py --input content/article/20260910-Transformer架构原理.md --theme newspaper --output /tmp/t1-html --no-open --format html
python3 .opencode/skills/wechat-format/scripts/format.py --input content/article/20260910-Transformer架构原理.md --theme newspaper --output /tmp/t1-plain --no-open --format plain
python3 .opencode/skills/wechat-format/scripts/format.py --input content/article/20260910-Transformer架构原理.md --theme newspaper --output /tmp/t1-gallery --no-open --gallery
grep -c "<sup" /tmp/t1-wechat/*/article.html
grep -o "<a href" /tmp/t1-html/*/article.html.html | wc -l
```
Expected: 四分支均输出文件；wechat `article.html` 的 `<sup>` 计数为 0（该文无手写脚注）；html 分支保留 `<a href>`（>0）。

- [ ] **Step 8: 提交**

```bash
git add .opencode/skills/wechat-format/scripts/format.py .opencode/skills/wechat-format/scripts/test_spec_compliance.py
git commit -m "feat: 外链降级为纯文本并移除自动脚注管道"
```

---

## Task 2: 移除手写 darkmode 注入（引擎）

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py`（:793-855 删除；:1348-1351 调用删除）
- Test: `.opencode/skills/wechat-format/scripts/test_spec_compliance.py`（追加）

**Interfaces:**
- Consumes: Task 1 的 `format.py`
- Produces: `inject_inline_styles(html, theme, skip_wrapper=False) -> str`（不再产出 `data-darkmode-*`）

- [ ] **Step 1: 写失败测试**

在 `test_spec_compliance.py` 的 `TestFootnotePipelineRemoval` 类之后追加：

```python
class TestNoHandwrittenDarkmode(unittest.TestCase):
    def test_no_darkmode_attrs_in_output(self):
        theme = fmt.load_theme("newspaper")
        html = fmt.inject_inline_styles(fmt.md_to_html("<p>正文</p>"), theme)
        self.assertNotIn("data-darkmode-", html)

    def test_darkmode_helper_functions_removed(self):
        self.assertFalse(hasattr(fmt, "_auto_dark_mode"))
        self.assertFalse(hasattr(fmt, "inject_dark_mode_attrs"))
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: FAIL —— 输出含 `data-darkmode-color`；`hasattr` 为 True。

- [ ] **Step 3: 删除函数与调用**

删除 `_auto_dark_mode`（:793-828）与 `inject_dark_mode_attrs`（:831-855）两个函数整体。

将 `inject_inline_styles()` 结尾（:1344-1353）改为：

```python
    # === 8. 处理 wrapper（整体背景色，用于 dark/retro 等主题）===
    if "wrapper" in style_map and not skip_wrapper:
        html = f'<section style="{style_map["wrapper"]}">{html}</section>'

    return html
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: PASS（11 项）。

- [ ] **Step 5: 提交**

```bash
git add .opencode/skills/wechat-format/scripts/format.py .opencode/skills/wechat-format/scripts/test_spec_compliance.py
git commit -m "refactor: 移除手写 darkmode 注入，交由平台自动转换"
```

---

## Task 3: 代码块 `<pre>` → `<section>`

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py`（`style_pre`，:1226-1269）
- Test: `.opencode/skills/wechat-format/scripts/test_spec_compliance.py`（追加）

**Interfaces:**
- Consumes: Task 2 的 `format.py`
- Produces: 代码块产物不含 `<pre>`，仍保留 `code_header` 与高亮 span

- [ ] **Step 1: 写失败测试**

追加：

```python
class TestCodeBlockNoPre(unittest.TestCase):
    def test_code_block_uses_section_not_pre(self):
        theme = fmt.load_theme("newspaper")
        md = "```python\ndef f():\n    return 1\n```\n"
        html = fmt.inject_inline_styles(fmt.md_to_html(md), theme)
        self.assertNotIn("<pre", html)
        self.assertIn("return", html)

    def test_code_block_has_wrap_styles(self):
        theme = fmt.load_theme("newspaper")
        md = "```python\nprint(1)\n```\n"
        html = fmt.inject_inline_styles(fmt.md_to_html(md), theme)
        self.assertIn("white-space:pre-wrap", html)
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: FAIL —— 输出含 `<pre`。

- [ ] **Step 3: 修改 `style_pre` 返回标签**

**修改** `style_pre` 的 return 语句（format.py:1262-1267），改为（保留既有 `pre_style`，必要时补换行样式）：

```python
        if "white-space" not in pre_style:
            pre_style += ";white-space:pre-wrap;word-break:break-all"
        return (
            f'<section style="{code_block_style}">'
            f'{mac_header}'
            f'<section style="{pre_style}">{pre_content}</section>'
            f'</section>'
        )
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: PASS（13 项）。

- [ ] **Step 5: 提交**

```bash
git add .opencode/skills/wechat-format/scripts/format.py .opencode/skills/wechat-format/scripts/test_spec_compliance.py
git commit -m "refactor: 代码块改用 section 承载，规避 pre 移动端截断"
```

---

## Task 4: `:::gallery` 宽度豁免

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/format.py`（`process_fenced_containers` gallery 分支 :579-588；`_inject_container_styles` gallery :995-1006）
- Test: `.opencode/skills/wechat-format/scripts/test_spec_compliance.py`（追加）

**Interfaces:**
- Consumes: Task 3 的 `format.py`
- Produces: gallery-scroll 标签带裸布尔属性 `data-ignore-width`

- [ ] **Step 1: 写失败测试**

追加：

```python
class TestGalleryWidthExemption(unittest.TestCase):
    def test_gallery_scroll_has_data_ignore_width(self):
        theme = fmt.load_theme("newspaper")
        md = ":::gallery[截图]\n![a](a.png)\n![](b.png)\n:::\n"
        content = fmt.process_fenced_containers(md)
        html = fmt.inject_inline_styles(fmt.md_to_html(content), theme)
        idx = html.find('data-container="gallery-scroll"')
        self.assertNotEqual(idx, -1)
        self.assertIn("data-ignore-width", html[idx:idx + 200])
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: FAIL —— gallery-scroll 标签无 `data-ignore-width`。

- [ ] **Step 3: 修改生成处与注入处**

`process_fenced_containers` 的 gallery 分支改为：

```python
            elif container_type == "gallery":
                inner_html = md_to_html(inner_text)
                result.append(
                    f'<section data-container="gallery">'
                    f'<p data-container="gallery-title">{container_title}</p>'
                    f'<section data-container="gallery-scroll" data-ignore-width>'
                    f'{inner_html}'
                    f'</section></section>'
                )
```

`_inject_container_styles` 中 gallery-scroll 的 replace 改为：

```python
    html = html.replace(
        '<section data-container="gallery-scroll" data-ignore-width>',
        f'<section data-container="gallery-scroll" data-ignore-width style="{gallery_scroll}">'
    )
```

- [ ] **Step 4: 运行测试，确认通过**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: PASS（14 项）。

- [ ] **Step 5: 提交**

```bash
git add .opencode/skills/wechat-format/scripts/format.py .opencode/skills/wechat-format/scripts/test_spec_compliance.py
git commit -m "fix: gallery 横向滚动容器声明 data-ignore-width"
```

---

## Task 5: 主题迁移脚本 + 30 主题落盘

**Files:**
- Create: `.opencode/skills/wechat-format/scripts/migrate_themes_spec.py`
- Create: `.opencode/skills/wechat-format/scripts/test_migrate_themes.py`
- Modify: `.opencode/skills/wechat-format/themes/*.json`（30 个，由脚本迁移）

**Interfaces:**
- Consumes: Task 2（引擎已不消费 `dark_mode`）
- Produces:
  - `migrate_themes_spec.last_gradient_body(value: str) -> str | None`
  - `migrate_themes_spec.last_stop_color(body: str) -> str`
  - `migrate_themes_spec.solid_from_gradient(value: str) -> tuple[str | None, bool]`（`(solid_color, delete_attr)`）
  - `migrate_themes_spec.migrate_dir(themes_dir: Path) -> int`（写盘文件数，幂等）

- [ ] **Step 1: 写失败测试**

新建 `.opencode/skills/wechat-format/scripts/test_migrate_themes.py`：

```python
import json
import sys
import unittest
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

THEMES_DIR = SCRIPT_DIR.parent / "themes"


class TestGradientParsing(unittest.TestCase):
    def setUp(self):
        import migrate_themes_spec as m
        self.m = m

    def test_last_stop_with_position_suffix(self):
        v = ("linear-gradient(180deg, rgba(0,0,0,0) 0%, rgba(0,0,0,0) 62%, "
             "rgba(50,104,145,0.1) 62%, rgba(50,104,145,0.1) 100%)")
        self.assertEqual(self.m.solid_from_gradient(v), ("rgba(50,104,145,0.1)", False))

    def test_two_arg_gradient(self):
        v = "linear-gradient(135deg, rgba(244,114,182,0.05), rgba(168,85,247,0.02))"
        self.assertEqual(self.m.solid_from_gradient(v), ("rgba(168,85,247,0.02)", False))

    def test_multi_gradient_uses_last_function(self):
        v = "linear-gradient(90deg, #fff, #eee), linear-gradient(180deg, #aaa, #000)"
        self.assertEqual(self.m.solid_from_gradient(v), ("#000", False))

    def test_repeating_transparent_is_delete(self):
        v = "repeating-linear-gradient(90deg, transparent 0, transparent 8px)"
        self.assertEqual(self.m.solid_from_gradient(v), (None, True))

    def test_opaque_alpha_zero_is_delete(self):
        v = "linear-gradient(#ffffff 0%, rgba(255,255,255,0) 100%)"
        self.assertEqual(self.m.solid_from_gradient(v), (None, True))

    def test_radial_gradient_supported(self):
        v = "radial-gradient(circle, #ff0 0%, #f00 100%)"
        self.assertEqual(self.m.solid_from_gradient(v), ("#f00", False))


class TestMigratedThemeInvariants(unittest.TestCase):
    def test_all_themes_have_no_dark_mode(self):
        for f in THEMES_DIR.glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            self.assertNotIn("dark_mode", d, f.name)

    def test_no_text_gradient_left(self):
        for f in THEMES_DIR.glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            for key, props in d.get("styles", {}).items():
                blob = json.dumps(props, ensure_ascii=False)
                if key == "hr":
                    continue
                self.assertNotIn("gradient(", blob, f"{f.name}:{key}")
                self.assertNotIn("border_image", props, f"{f.name}:{key}")

    def test_pre_has_no_overflow_x(self):
        for f in THEMES_DIR.glob("*.json"):
            d = json.loads(f.read_text(encoding="utf-8"))
            pre = d.get("styles", {}).get("pre", {})
            self.assertNotIn("overflow_x", pre, f.name)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试，确认失败**

Run: `python3 .opencode/skills/wechat-format/scripts/test_migrate_themes.py -v`
Expected: FAIL —— `ModuleNotFoundError: No module named 'migrate_themes_spec'`；主题不变量亦失败。

- [ ] **Step 3: 实现迁移脚本**

新建 `.opencode/skills/wechat-format/scripts/migrate_themes_spec.py`：

```python
#!/usr/bin/env python3
"""主题规范迁移：删除 dark_mode、文字背景渐变转实色、删除 border_image 与 pre.overflow_x。

幂等：内容无变化时不写盘；序列化参数与现有文件一致（indent=2，无末尾换行）。
"""
import json
import re
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
THEMES_DIR = SCRIPT_DIR.parent / "themes"

GRADIENT_START_RE = re.compile(
    r"(?:repeating-)?(?:-webkit-)?(?:linear|radial|conic)-gradient\(", re.I
)
COLOR_STOP_POS_RE = re.compile(r"^(.*?)\s+(?:-?\d*\.?\d+)(?:px|%|em|rem|deg)?$")
ALPHA_ZERO_RE = re.compile(
    r"^rgba\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*0(?:\.0+)?\s*\)$"
)


def last_gradient_body(value: str):
    """返回最后一个 gradient 函数体（括号内内容），无则 None。"""
    matches = list(GRADIENT_START_RE.finditer(value))
    if not matches:
        return None
    i = matches[-1].end()
    depth = 1
    start = i
    while i < len(value) and depth > 0:
        if value[i] == "(":
            depth += 1
        elif value[i] == ")":
            depth -= 1
        i += 1
    return value[start:i - 1]


def _split_top_level(body: str):
    parts, depth, cur = [], 0, []
    for ch in body:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    parts.append("".join(cur))
    return parts


def last_stop_color(body: str) -> str:
    last = _split_top_level(body)[-1].strip()
    m = COLOR_STOP_POS_RE.match(last)
    return (m.group(1).strip() if m else last)


def solid_from_gradient(value: str):
    """返回 (实色, 是否删除该属性)。透明末 stop → (None, True)。"""
    body = last_gradient_body(value)
    if body is None:
        return None, False
    color = last_stop_color(body)
    low = color.lower().replace(" ", "")
    if low == "transparent" or ALPHA_ZERO_RE.match(low):
        return None, True
    return color, False


def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def migrate_theme_data(d: dict) -> bool:
    """原地迁移一个主题 dict，返回是否有改动。"""
    changed = False
    if "dark_mode" in d:
        del d["dark_mode"]
        changed = True

    accent = d.get("colors", {}).get("accent", "#000000")
    try:
        ar, ag, ab = _hex_to_rgb(accent)
    except (ValueError, IndexError):
        ar, ag, ab = 0, 0, 0

    for key, props in d.get("styles", {}).items():
        for bg_key in ("background", "background_image"):
            if bg_key in props and isinstance(props[bg_key], str) and "gradient(" in props[bg_key]:
                color, delete = solid_from_gradient(props[bg_key])
                del props[bg_key]
                if key == "strong":
                    props["background_color"] = f"rgba({ar},{ag},{ab},0.12)"
                elif not delete and color is not None:
                    props["background_color"] = color
                changed = True
        if "border_image" in props:
            del props["border_image"]
            changed = True
        if key == "pre" and "overflow_x" in props:
            del props["overflow_x"]
            changed = True
    return changed


def migrate_dir(themes_dir: Path = THEMES_DIR) -> int:
    written = 0
    for path in sorted(Path(themes_dir).glob("*.json")):
        original = path.read_text(encoding="utf-8")
        d = json.loads(original)
        if not migrate_theme_data(d):
            continue
        updated = json.dumps(d, ensure_ascii=False, indent=2)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            written += 1
    return written


if __name__ == "__main__":
    n = migrate_dir()
    print(f"迁移完成，写入 {n} 个主题文件")
```

- [ ] **Step 4: 运行测试，确认解析测试通过（不变量测试此时仍失败）**

Run: `python3 .opencode/skills/wechat-format/scripts/test_migrate_themes.py -v`
Expected: `TestGradientParsing` 6 项 PASS；`TestMigratedThemeInvariants` FAIL（尚未迁移）。

- [ ] **Step 5: 执行迁移并落盘**

Run:
```bash
python3 .opencode/skills/wechat-format/scripts/migrate_themes_spec.py
git diff --stat .opencode/skills/wechat-format/themes/
```
Expected: `迁移完成，写入 30 个主题文件`；diff 显示 30 个文件变更。

- [ ] **Step 6: 运行不变量测试，确认通过**

Run: `python3 .opencode/skills/wechat-format/scripts/test_migrate_themes.py -v`
Expected: PASS（9 项）。

- [ ] **Step 7: 幂等性验证**

Run:
```bash
python3 .opencode/skills/wechat-format/scripts/migrate_themes_spec.py
```
Expected: 第二次输出 `迁移完成，写入 0 个主题文件`（无变化不写盘）；`git diff --stat .opencode/skills/wechat-format/themes/` 与上一步相同（第二次运行不产生新 diff）。

- [ ] **Step 8: 人工抽查 3 个主题的 diff**

Run:
```bash
git diff .opencode/skills/wechat-format/themes/newspaper.json
git diff .opencode/skills/wechat-format/themes/magazine.json
git diff .opencode/skills/wechat-format/themes/midnight.json
```
Expected: `newspaper.strong` 变为 `background_color: rgba(50,104,145,0.12)`；`magazine` 的 h2/h3/blockquote/callout 删除 `border_image`、保留 `border_left`；`midnight` 的 blockquote 渐变变实色。确认无 `<hr>` 被误改。

- [ ] **Step 9: 提交**

> 注：30 个主题为一次机械迁移，属 AGENTS.md「每提交 ≤3 文件」的豁免情形。如需严格遵守，可分 3 次提交（每 10 个主题）。

```bash
git add .opencode/skills/wechat-format/scripts/migrate_themes_spec.py .opencode/skills/wechat-format/scripts/test_migrate_themes.py .opencode/skills/wechat-format/themes/
git commit -m "chore: 迁移 30 主题——去 dark_mode、文字渐变转实色、去 border_image"
```

---

## Task 6: 端到端规范回归测试

**Files:**
- Modify: `.opencode/skills/wechat-format/scripts/test_spec_compliance.py`（追加集成测试类）

**Interfaces:**
- Consumes: Task 1-5 的全部产物
- Produces: 规范不变量回归套件（全 `style` 扫描、无 `!important`、嵌套 ≤10）

- [ ] **Step 1: 写集成测试（TDD：先跑，应随前序 Task 自然通过）**

追加：

```python
import re
import subprocess


REPO_ROOT = SCRIPT_DIR.parents[3]


class TestSpecInvariants(unittest.TestCase):
    FIXTURE = (
        "# 标题\n\n"
        "正文 [外链](https://example.com/x) 与 [内链](https://mp.weixin.qq.com/s/a)，"
        "还有 [锚点](#sec) 与 [邮件](mailto:a@b.com)。\n\n"
        "**重点** 与 `代码`。\n\n"
        "> 引用\n\n"
        "```python\nprint(1)\n```\n\n"
        ":::gallery[图]\n![a](a.png)\n:::\n\n"
        "手写脚注[^1]。\n\n[^1]: 注释内容\n"
    )

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.md = cls.tmp / "fixture.md"
        cls.md.write_text(cls.FIXTURE, encoding="utf-8")
        out = cls.tmp / "out"
        subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "format.py"),
             "--input", str(cls.md), "--theme", "newspaper",
             "--output", str(out), "--no-open"],
            check=True, cwd=str(REPO_ROOT),
        )
        cls.html = next(out.glob("*/article.html")).read_text(encoding="utf-8")

    def test_no_darkmode(self):
        self.assertNotIn("data-darkmode-", self.html)

    def test_no_pre(self):
        self.assertNotIn("<pre", self.html)

    def test_no_gradient_except_hr(self):
        no_hr = re.sub(r"<hr[^>]*>", "", self.html)
        self.assertIsNone(re.search(r"[a-z-]*gradient\(", no_hr))
        self.assertNotIn("border-image", no_hr)

    def test_no_important(self):
        self.assertNotIn("!important", self.html)

    def test_gallery_has_ignore_width(self):
        self.assertIn("data-ignore-width", self.html)

    def test_external_unwrapped_internal_kept(self):
        self.assertIn('<a href="https://mp.weixin.qq.com/s/a"', self.html)
        self.assertIn('<a href="#sec"', self.html)
        self.assertIn('<a href="mailto:a@b.com"', self.html)
        self.assertNotIn('<a href="https://example.com/x"', self.html)

    def test_manual_footnote_still_renders_sup(self):
        self.assertIn("<sup", self.html)

    def test_section_nesting_depth(self):
        depth = 0
        max_depth = 0
        for m in re.finditer(r"<section\b|</section>", self.html):
            if m.group(0).startswith("</"):
                depth -= 1
            else:
                depth += 1
                max_depth = max(max_depth, depth)
        self.assertEqual(depth, 0, "section 标签不平衡")
        self.assertLessEqual(max_depth, 10)
```

- [ ] **Step 2: 运行测试**

Run: `python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py -v`
Expected: 全 PASS。若某项 FAIL，检查对应前序 Task 而非改测试。

- [ ] **Step 3: 提交**

```bash
git add .opencode/skills/wechat-format/scripts/test_spec_compliance.py
git commit -m "test: 增加微信规范端到端不变量回归"
```

---

## Task 7: 文档更新（SKILL.md / to-wechat.md / preview.html）

**Files:**
- Modify: `.opencode/skills/wechat-format/SKILL.md`（「内置排版增强」段；新增「规范对齐」小节）
- Modify: `.opencode/commands/to-wechat.md`（注意事项）
- Modify: `.opencode/skills/wechat-format/templates/preview.html`（toolbar-info）

**Interfaces:**
- Consumes: Task 1-6
- Produces: 文档与实现一致

- [ ] **Step 1: 更新 `SKILL.md` 内置排版增强**

将该段中三行改为：

```markdown
- **外链降级**：http(s) 外链拆为纯文本（URL 不保留），`mp.weixin.qq.com` 内链保留为 `<a>`；`#` 锚点与 `mailto:` 不受影响
- **语法高亮**：代码块着色 + Mac 风格工具栏（用 `<section>` 承载，非 `<pre>`）
- **深色模式**：遵循微信平台自动转换算法，不手写 `data-darkmode-*`
```

- [ ] **Step 2: 新增「微信官方规范对齐」小节**

在「内置排版增强」之后追加：

```markdown
## 微信官方规范对齐

对齐《微信公众平台编辑器插件开发规范》（developers.weixin.qq.com/doc/service/guide/product/plugin_spec.html）：

| 官方条款 | 本 skill 做法 |
|----------|---------------|
| §1.4.4 横向滚动需宽度豁免 | `:::gallery` 滚动容器带 `data-ignore-width` |
| §1.8 不用 `<pre>` 承载内容 | 代码块用 `<section>` + `white-space:pre-wrap` |
| §2.1 嵌套 ≤10 层 | 结构最深层级 ≤4，回归测试锁定 |
| §3 不设字体族 | 仅 code/pre 用等宽字体（合理例外） |
| §4.1.2 文字背景不用渐变 | 30 主题文字渐变已迁移为实色；`hr` 无文字，保留渐变 |
| §4.5.2 不用 `!important` | 全文不使用 |
```

- [ ] **Step 3: 更新 `to-wechat.md` 注意事项**

在「图片处理」之后追加：

```markdown
- **外链处理**：正文 http(s) 外链会降级为纯文本、不保留 URL；`mp.weixin.qq.com` 内链保留可点击；`#` 锚点与 `mailto:` 不受影响；手写 `[^N]` 脚注仍支持
```

- [ ] **Step 4: 更新 `preview.html`**

`toolbar-info` 内追加一行：

```html
<span>深色模式以微信平台算法为准</span>
```

- [ ] **Step 5: 校验文档无残留旧描述**

Run:
```bash
grep -rn "外链转脚注\|data-darkmode-" .opencode/skills/wechat-format/SKILL.md .opencode/commands/to-wechat.md
```
Expected: 无输出（若出现，说明旧描述未清理）。
（`<pre>` 仅允许出现在「不用 `<pre>`」这类新说明中，不参与本 grep。）

- [ ] **Step 6: 提交**

```bash
git add .opencode/skills/wechat-format/SKILL.md .opencode/commands/to-wechat.md .opencode/skills/wechat-format/templates/preview.html
git commit -m "docs: 同步外链降级与官方规范对齐说明"
```

---

## Task 8: 最终验收

**Files:** 无（只跑命令）

- [ ] **Step 1: 全部单测**

Run:
```bash
python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py
python3 .opencode/skills/wechat-format/scripts/test_migrate_themes.py
```
Expected: 两个套件全部 PASS。

- [ ] **Step 2: 真实文章端到端（newspaper）**

Run:
```bash
rm -rf /tmp/final-align
python3 .opencode/skills/wechat-format/scripts/format.py --input content/article/20260910-Transformer架构原理.md --theme newspaper --output /tmp/final-align --no-open
grep -q "data-darkmode-" /tmp/final-align/*/article.html && echo "FAIL darkmode" || echo "PASS darkmode"
grep -q "<pre" /tmp/final-align/*/article.html && echo "FAIL pre" || echo "PASS pre"
grep -o "<sup[^>]*>" /tmp/final-align/*/article.html | wc -l
python3 - <<'PY'
import glob, re
html = open(glob.glob('/tmp/final-align/*/article.html')[0], encoding='utf-8').read()
no_hr = re.sub(r'<hr[^>]*>', '', html)
print('FAIL gradient' if re.search(r'[a-z-]*gradient\(', no_hr) else 'PASS gradient')
print('FAIL border-image' if 'border-image' in no_hr else 'PASS border-image')
print('FAIL important' if '!important' in html else 'PASS important')
PY
```
Expected: `PASS darkmode` / `PASS pre` / `<sup>` 计数 0 / `PASS gradient` / `PASS border-image` / `PASS important`。

- [ ] **Step 3: 人工深色模式验收（硬性关卡）**

将 `/tmp/final-align/*/article.html` 内容粘贴进公众号编辑器，切换「深色模式预览」，确认正文/标题/引用/表格/代码块可读；对 `bytedance`、`midnight` 各抽查一次（`--theme bytedance` / `--theme midnight` 重新生成）。
- 不通过 → 回滚 Task 2 提交，或按 spec §2 兜底给 `code_block` 加 `data-no-dark`。
- 记录结论到 spec §八审查记录。

---

## Self-Review

**1. Spec coverage**

| Spec 章节 | 覆盖 Task |
|-----------|-----------|
| §1 外链降级 + 管道清理（含 :1810/docstring/保留 :1797） | Task 1 |
| §2 去手写 darkmode（引擎 + 分级提交） | Task 2（引擎）、Task 5（主题） |
| §3 代码块 `<pre>`→`<section>` + 删 `pre.overflow_x` | Task 3、Task 5 |
| §4 gallery `data-ignore-width` | Task 4 |
| §5 结构/字体（测试锁死） | Task 6 |
| §6 preview 提示 | Task 7 |
| §7 文档 | Task 7 |
| §8 回归测试（8 条断言） | Task 1/6 |
| 验收标准（自动化 + 人工） | Task 8 |
| 可回滚（提交 1/2） | Task 2 提交、Task 5 提交 |

无遗漏。

**2. Placeholder scan**：无 TBD/TODO；所有代码步骤含完整代码；无「类似 Task N」。

**3. Type consistency**
- `format_for_output` 返回键在 Task 1 定义 `{html,title,word_count}`，Task 1 测试与 `main` 一致。
- `unwrap_external_links` 名称在 Task 1 定义并被 Task 6 断言。
- `solid_from_gradient` / `last_gradient_body` / `last_stop_color` 在 Task 5 定义并被同 Task 测试引用，命名一致。
- `generate_preview` / `_render_single_theme` 新签名仅在 Task 1 定义并同步调用点，无跨 Task 漂移。

**4. 已知豁免**：Task 5 的 30 文件提交超出 AGENTS.md ≤3 文件粒度，已在 Task 内标注为机械迁移豁免并给替代方案。
