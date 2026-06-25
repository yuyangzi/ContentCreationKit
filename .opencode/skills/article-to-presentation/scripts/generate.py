import argparse
import json
import os
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR))

from parser.markdown_parser import parse_file, format_ppt_copy
from renderer.html_renderer import render_from_json


def generate_basic_slides(parsed: dict, source: str = "") -> dict:
    slides = []

    slides.append({
        "type": "cover",
        "visual": "hero-center",
        "title": parsed.get("title", "Untitled"),
        "subtitle": parsed.get("subtitle", ""),
        "source": source,
        "data": {},
    })

    for idx, section in enumerate(parsed.get("sections", [])):
        if idx == 0:
            slides.append({
                "type": "section",
                "visual": "chapter",
                "title": section["title"],
                "badge": idx + 1,
                "source": source,
                "data": {},
            })
        slides.append({
            "type": "layout",
            "visual": "simple-text",
            "title": section["title"],
            "source": source,
            "data": {"content": section.get("content", "")},
        })

    if parsed.get("quotes"):
        slides.append({
            "type": "quote",
            "visual": "quote-center",
            "title": "",
            "source": source,
            "data": {"quote": parsed["quotes"][0], "source": source},
        })

    if parsed.get("metrics"):
        slides.append({
            "type": "data",
            "visual": "metric-cards",
            "title": "关键数据",
            "source": source,
            "data": {
                "cards": [
                    {"badge": str(i + 1), "color": "blue", "title": m["label"], "description": str(m["value"])}
                    for i, m in enumerate(parsed["metrics"][:4])
                ]
            },
        })

    slides.append({
        "type": "summary",
        "visual": "summary-list",
        "title": "总结",
        "source": source,
        "data": {"items": [s["title"] for s in parsed.get("sections", [])][:5]},
    })

    return {"title": parsed.get("title", "Untitled"), "source": source, "slides": slides}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate HTML presentation from markdown article")
    parser.add_argument("--input", required=True, help="Path to markdown article")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--source", default="", help="Source citation")
    parser.add_argument("--skip-copy", action="store_true", help="Skip regenerating PPT文案.md")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    copy_path = output_dir / "PPT文案.md"
    slides_path = output_dir / "slides.json"
    html_path = output_dir / "slides.html"

    parsed = parse_file(input_path)

    if not args.skip_copy or not copy_path.exists():
        copy_text = format_ppt_copy(parsed)
        with copy_path.open("w", encoding="utf-8") as f:
            f.write(copy_text)
        print(f"Written: {copy_path}")

    if not slides_path.exists():
        basic = generate_basic_slides(parsed, source=args.source)
        with slides_path.open("w", encoding="utf-8") as f:
            json.dump(basic, f, ensure_ascii=False, indent=2)
        print(f"Written (basic): {slides_path}")
        print("Tip: refine slides.json with LLM before rendering.")

    render_from_json(slides_path, html_path)
    print(f"Rendered: {html_path}")


if __name__ == "__main__":
    main()
