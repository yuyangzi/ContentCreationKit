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

    def test_hr_gradient_preserved(self):
        # hr 无文字承载，渐变应保留（官方 §4.1.3）
        newspaper = json.loads(
            (THEMES_DIR / "newspaper.json").read_text(encoding="utf-8")
        )
        hr_blob = json.dumps(newspaper["styles"]["hr"], ensure_ascii=False)
        self.assertIn("gradient", hr_blob)


if __name__ == "__main__":
    unittest.main()
