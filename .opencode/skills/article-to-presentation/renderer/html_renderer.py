import json
import os
from pathlib import Path
from typing import Any

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
except ImportError:
    raise ImportError("jinja2 is required. Install with: pip install jinja2")


CHART_VISUALS = {
    "bar-chart",
    "line-chart",
    "area-chart",
    "pie-chart",
    "doughnut-chart",
    "radar-chart",
    "mixed-chart",
    "horizontal-bar-chart",
}


def get_template_name(slide: dict) -> str:
    """Map slide type + visual to a Jinja2 template file."""
    type_ = slide.get("type", "section")
    visual = slide.get("visual", "chapter")
    return f"{type_}-{visual}.html"


def render(slides: list[dict], title: str = "Presentation") -> str:
    """Render slides into a single HTML string."""
    base_dir = Path(__file__).resolve().parent.parent
    templates_dir = base_dir / "templates"

    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("base.html")

    for idx, slide in enumerate(slides):
        slide["index"] = idx
        slide["template"] = get_template_name(slide)

    echarts_needed = any(
        slide.get("visual", "") in CHART_VISUALS for slide in slides
    )

    return template.render(
        slides=slides,
        title=title,
        echarts_needed=echarts_needed,
    )


def render_from_json(slides_path: str | Path, output_path: str | Path) -> None:
    """Load slides.json and write slides.html."""
    slides_path = Path(slides_path)
    output_path = Path(output_path)

    with slides_path.open("r", encoding="utf-8") as f:
        payload = json.load(f)

    if isinstance(payload, dict):
        slides = payload.get("slides", [])
        title = payload.get("title", "Presentation")
    else:
        slides = payload
        title = "Presentation"

    html = render(slides, title=title)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(html)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Render Slide DSL JSON to HTML")
    parser.add_argument("--slides", required=True, help="Path to slides.json")
    parser.add_argument("--output", required=True, help="Path to output slides.html")
    parser.add_argument("--title", default="Presentation", help="HTML title")
    args = parser.parse_args()

    render_from_json(args.slides, args.output)
    print(f"Rendered: {args.output}")


if __name__ == "__main__":
    main()
