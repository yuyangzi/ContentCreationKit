import re
import subprocess
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


class TestNoHandwrittenDarkmode(unittest.TestCase):
    def test_no_darkmode_attrs_in_output(self):
        theme = fmt.load_theme("newspaper")
        html = fmt.inject_inline_styles(fmt.md_to_html("<p>正文</p>"), theme)
        self.assertNotIn("data-darkmode-", html)

    def test_darkmode_helper_functions_removed(self):
        self.assertFalse(hasattr(fmt, "_auto_dark_mode"))
        self.assertFalse(hasattr(fmt, "inject_dark_mode_attrs"))


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


class TestGalleryWidthExemption(unittest.TestCase):
    def test_gallery_scroll_has_data_ignore_width(self):
        theme = fmt.load_theme("newspaper")
        md = ":::gallery[截图]\n![a](a.png)\n![](b.png)\n:::\n"
        content = fmt.process_fenced_containers(md)
        html = fmt.inject_inline_styles(fmt.md_to_html(content), theme)
        idx = html.find('data-container="gallery-scroll"')
        self.assertNotEqual(idx, -1)
        self.assertIn("data-ignore-width", html[idx:idx + 200])


REPO_ROOT = SCRIPT_DIR.parents[3]


class TestCjkSpacingPreservesLinks(unittest.TestCase):
    def test_multiple_links_on_one_line_intact(self):
        line = ("正文 [外链](https://example.com/x) 与 "
                "[内链](https://mp.weixin.qq.com/s/a)，还有 [锚点](#sec)。")
        out = fmt.fix_cjk_spacing(line)
        self.assertEqual(out, line)
        self.assertNotIn("\x00P", out)

    def test_bare_url_and_image_intact(self):
        line = "裸链接 https://example.com/y 与 ![图](a.png)。"
        self.assertEqual(fmt.fix_cjk_spacing(line), line)


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
        self.assertIn('href="https://mp.weixin.qq.com/s/a"', self.html)
        self.assertIn('href="#sec"', self.html)
        self.assertIn('href="mailto:a@b.com"', self.html)
        self.assertNotIn('href="https://example.com/x"', self.html)

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


if __name__ == "__main__":
    unittest.main()
