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
