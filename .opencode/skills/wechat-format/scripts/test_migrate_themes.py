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

    def test_fade_out_uses_first_stop(self):
        # 淡出型渐变（0.94 → 透明）：有意义的颜色在首 stop
        v = ("linear-gradient(90deg, rgba(236,228,255,0.94) 0%, "
             "rgba(236,228,255,0.2) 74%, rgba(236,228,255,0) 100%)")
        self.assertEqual(self.m.solid_from_gradient(v), ("rgba(236,228,255,0.94)", False))

    def test_radial_fade_out_uses_first_stop(self):
        v = ("radial-gradient(80.23% 80.23% at 50% 88.37%, "
             "rgba(174,78,245,0.22) 0%, rgba(174,78,245,0) 100%)")
        self.assertEqual(self.m.solid_from_gradient(v), ("rgba(174,78,245,0.22)", False))

    def test_radial_gradient_supported(self):
        v = "radial-gradient(circle, #ff0 0%, #f00 100%)"
        self.assertEqual(self.m.solid_from_gradient(v), ("#f00", False))

    def test_uniform_gradient_uses_stop_color(self):
        v = "linear-gradient(rgba(75,110,245,0.35), rgba(75,110,245,0.35))"
        self.assertEqual(self.m.solid_from_gradient(v), ("rgba(75,110,245,0.35)", False))

    def test_borders_from_position_top_bottom(self):
        self.assertEqual(
            self.m.borders_from_position("center top, center bottom", "#111"),
            {"border_top": "1px solid #111", "border_bottom": "1px solid #111"},
        )


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

    def test_hr_gradient_preserved(self):
        # hr 无文字承载，渐变应保留（官方 §4.1.3）
        newspaper = json.loads(
            (THEMES_DIR / "newspaper.json").read_text(encoding="utf-8")
        )
        hr_blob = json.dumps(newspaper["styles"]["hr"], ensure_ascii=False)
        self.assertIn("gradient", hr_blob)

    def test_focus_titles_use_borders_not_background_color(self):
        # 装饰细线不得被转成整块底色
        for name in ("focus-blue", "focus-gold", "focus-red"):
            d = json.loads((THEMES_DIR / f"{name}.json").read_text(encoding="utf-8"))
            for key in ("h1", "h2", "h3"):
                props = d["styles"][key]
                self.assertNotIn("background_color", props, f"{name}.{key}")
                self.assertNotIn("background_image", props, f"{name}.{key}")
                self.assertIn("border_top", props, f"{name}.{key}")
                self.assertIn("border_bottom", props, f"{name}.{key}")

    def test_fade_out_gradients_keep_first_stop(self):
        # 淡出型渐变应保留首 stop 实色，而非整段删除
        expectations = {
            ("lavender-dream", "h2"): "rgba(236,228,255,0.94)",
            ("midnight", "h2"): "rgba(174,78,245,0.22)",
            ("midnight", "h3"): "rgba(139,92,246,0.18)",
            ("sunset-amber", "h2"): "rgba(236,191,132,0.24)",
            ("wechat-native", "h2"): "rgba(7,193,96,0.12)",
        }
        for (name, key), expected in expectations.items():
            d = json.loads((THEMES_DIR / f"{name}.json").read_text(encoding="utf-8"))
            self.assertEqual(
                d["styles"][key].get("background_color"), expected, f"{name}.{key}"
            )


if __name__ == "__main__":
    unittest.main()
