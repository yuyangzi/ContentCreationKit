import sys
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR))

from renderer.html_renderer import render


class TemplateRenderingTest(unittest.TestCase):
    def test_render_uses_refined_slide_system_classes(self) -> None:
        html = render(
            [
                {
                    "type": "cover",
                    "visual": "hero-center",
                    "eyebrow": "Agent Workflow",
                    "title": "把文章变成录屏友好的演示文稿",
                    "subtitle": "更稳的中文排版与深色科技风",
                    "data": {"tags": ["B站录屏", "公众号视频"]},
                },
                {
                    "type": "layout",
                    "visual": "simple-text",
                    "eyebrow": "Context",
                    "title": "长文本要稳定",
                    "data": {"content": "第一段观点。\n第二段观点。"},
                },
            ],
            title="Template smoke test",
        )

        self.assertIn("class=\"slide-shell", html)
        self.assertIn("class=\"slide-kicker\"", html)
        self.assertIn("class=\"content-panel", html)
        self.assertIn("overflow-wrap: anywhere", html)
        self.assertIn("text-wrap: balance", html)


if __name__ == "__main__":
    unittest.main()
