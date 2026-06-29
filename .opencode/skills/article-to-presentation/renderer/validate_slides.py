import json
import sys
from pathlib import Path
from typing import Any

VALID_TYPES = {"cover", "section", "compare", "table", "data", "process", "terminal", "quote", "layout", "summary"}

VISUAL_BY_TYPE: dict[str, set[str]] = {
    "cover": {"hero-split", "hero-center"},
    "section": {"chapter"},
    "compare": {"before-after-metric", "before-after-cards", "three-column-flow"},
    "table": {"comparison-table"},
    "data": {"big-number", "metric-cards", "bar-chart", "line-chart", "area-chart", "pie-chart", "doughnut-chart", "radar-chart", "mixed-chart", "horizontal-bar-chart"},
    "process": {"vertical-steps", "horizontal-steps", "timeline"},
    "terminal": {"code-terminal"},
    "quote": {"quote-center", "quote-with-source"},
    "layout": {"simple-text", "split-text-image", "full-image", "two-column-text"},
    "summary": {"summary-list", "key-takeaways"},
}

REQUIRED_TOP_FIELDS = {"type", "visual", "title"}

COLOR_SEMANTICS = {
    "green": "正面/增长/成功/重构后",
    "red": "负面/下降/重构前/警告",
    "orange": "中性强调/标签/封面",
    "blue": "信息/规则/路径",
    "purple": "概念/Skill/Agent",
    "pink": "安全/个人",
    "cyan": "代码/技术术语",
}

SCHEMA_REQUIREMENTS = {
    ("section", "chapter"): {"keys": {"badge"}, "data_keys": {"color"}},
    ("cover", "hero-split"): {"data_keys": {"before", "after"}},
    ("cover", "hero-center"): {},
    ("compare", "before-after-metric"): {"data_keys": {"before", "after"}},
    ("compare", "before-after-cards"): {"data_keys": {"before", "after"}},
    ("compare", "three-column-flow"): {"data_keys": {"left", "center", "right"}},
    ("table", "comparison-table"): {"data_keys": {"rows"}},
    ("data", "metric-cards"): {"data_keys": {"cards"}},
    ("data", "big-number"): {"data_keys": {"value", "color", "label"}},
    ("data", "bar-chart"): {"data_keys": {"labels", "values", "color"}},
    ("data", "line-chart"): {"data_keys": {"labels", "datasets"}},
    ("data", "area-chart"): {"data_keys": {"labels", "datasets"}},
    ("data", "pie-chart"): {"data_keys": {"series"}},
    ("data", "doughnut-chart"): {"data_keys": {"series"}},
    ("data", "radar-chart"): {"data_keys": {"indicators", "datasets"}},
    ("data", "mixed-chart"): {"data_keys": {"labels", "datasets"}},
    ("data", "horizontal-bar-chart"): {"data_keys": {"labels", "values", "color"}},
    ("process", "vertical-steps"): {"data_keys": {"steps"}},
    ("process", "horizontal-steps"): {"data_keys": {"steps"}},
    ("process", "timeline"): {"data_keys": {"events"}},
    ("terminal", "code-terminal"): {"data_keys": {"lines"}},
    ("quote", "quote-center"): {"data_keys": {"quote"}},
    ("quote", "quote-with-source"): {"data_keys": {"quote"}},
    ("layout", "simple-text"): {"data_keys": {"content"}},
    ("layout", "split-text-image"): {},
    ("layout", "full-image"): {},
    ("layout", "two-column-text"): {"data_keys": {"left", "right"}},
    ("summary", "summary-list"): {"data_keys": {"items"}},
    ("summary", "key-takeaways"): {"data_keys": {"items"}},
}

errors: list[str] = []


def validate(slides_data: dict[str, Any]) -> list[str]:
    errors.clear()
    slides = slides_data.get("slides", [])
    if not isinstance(slides, list):
        errors.append("top-level 'slides' must be a list")
        return errors

    for i, s in enumerate(slides):
        prefix = f"[slide {i}]"
        if not isinstance(s, dict):
            errors.append(f"{prefix} is not a dict")
            continue

        slide_type = s.get("type", "")
        visual = s.get("visual", "")
        data = s.get("data", {})

        for key in REQUIRED_TOP_FIELDS:
            if key not in s:
                errors.append(f"{prefix} missing '{key}'")

        if slide_type not in VALID_TYPES:
            errors.append(f"{prefix} unknown type '{slide_type}'")

        if slide_type in VISUAL_BY_TYPE and visual not in VISUAL_BY_TYPE[slide_type]:
            valid = ", ".join(sorted(VISUAL_BY_TYPE[slide_type]))
            errors.append(f"{prefix} visual '{visual}' not valid for type '{slide_type}'. Valid: {valid}")

        if not isinstance(data, dict):
            errors.append(f"{prefix} 'data' must be a dict, got {type(data).__name__}")
            continue

        key = (slide_type, visual)
        if key in SCHEMA_REQUIREMENTS:
            req = SCHEMA_REQUIREMENTS[key]
            for top_key in req.get("keys", set()):
                if top_key not in s:
                    errors.append(f"{prefix} missing top-level key '{top_key}' (required for {slide_type}/{visual})")
            for data_key in req.get("data_keys", set()):
                if data_key not in data:
                    errors.append(f"{prefix} data missing '{data_key}' (required for {slide_type}/{visual})")

        errors.extend(_validate_colors(prefix, data))

    return errors


def _validate_colors(prefix: str, obj: Any, path: str = "data") -> list[str]:
    errs: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("color", "badge_color") and isinstance(v, str):
                if v not in COLOR_SEMANTICS and not v.startswith("#"):
                    errs.append(f"{prefix} {path}.{k} = '{v}' is not a valid CSS color or semantic color")
            errs.extend(_validate_colors(prefix, v, f"{path}.{k}"))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            errs.extend(_validate_colors(prefix, item, f"{path}[{idx}]"))
    return errs


def validate_file(path: str | Path) -> list[str]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = json.load(f)
    return validate(data)


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: validate_slides.py <slides.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    errs = validate_file(path)
    if errs:
        print(f"Validation failed ({len(errs)} errors):")
        for e in errs:
            print(f"  ✗ {e}")
        sys.exit(1)
    else:
        print("Validation passed ✓")
        sys.exit(0)


if __name__ == "__main__":
    main()
