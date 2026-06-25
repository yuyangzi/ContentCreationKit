import re
from pathlib import Path
from typing import Any


def parse(markdown: str) -> dict[str, Any]:
    lines = markdown.splitlines()
    result: dict[str, Any] = {
        "title": "",
        "subtitle": "",
        "source": "",
        "sections": [],
        "metrics": [],
        "quotes": [],
        "sources": [],
    }

    current_section: dict[str, Any] | None = None
    current_body: list[str] = []

    for line in lines:
        heading_match = re.match(r"^(#{1,2})\s+(.*)$", line)
        if heading_match:
            level, text = heading_match.groups()
            text = text.strip()
            if level == "#" and not result["title"]:
                result["title"] = text
            elif level == "#":
                _flush_section(current_section, current_body, result)
                current_section = {"title": text, "content": ""}
                current_body = []
            elif level == "##":
                _flush_section(current_section, current_body, result)
                current_section = {"title": text, "content": ""}
                current_body = []
            continue

        quote_match = re.match(r"^>\s+(.*)$", line)
        if quote_match:
            result["quotes"].append(quote_match.group(1).strip())
            continue

        source_match = re.match(r"^[\*\-]\s*来源[:：]?\s*(.+)$", line, re.IGNORECASE)
        if source_match:
            result["sources"].append(source_match.group(1).strip())
            continue

        metric_match = re.match(r".*?(\d+(?:\.\d+)?%?)\s*([\u4e00-\u9fa5a-zA-Z]+).*", line)
        if metric_match and len(metric_match.group(1)) <= 6:
            value, label = metric_match.groups()
            result["metrics"].append({"label": label.strip(), "value": value.strip()})

        if current_section is not None:
            current_body.append(line)

    _flush_section(current_section, current_body, result)

    if not result["subtitle"] and len(result["sections"]) > 0:
        first_content = result["sections"][0].get("content", "")
        sentences = re.split(r"[。！？]", first_content)
        if sentences:
            result["subtitle"] = sentences[0].strip()[:80]

    return result


def _flush_section(
    current_section: dict[str, Any] | None,
    current_body: list[str],
    result: dict[str, Any],
) -> None:
    if current_section is not None:
        content = "\n".join(current_body).strip()
        current_section["content"] = content
        result["sections"].append(current_section)


def parse_file(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return parse(f.read())


def format_ppt_copy(parsed: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {parsed['title']}")
    if parsed.get("subtitle"):
        lines.append(f"\n{parsed['subtitle']}\n")
    lines.append("\n## 核心论点\n")
    if parsed["sections"]:
        lines.append(parsed["sections"][0]["content"][:300])
    lines.append("\n## 关键数据\n")
    for m in parsed["metrics"][:6]:
        lines.append(f"- {m['label']}: {m['value']}")
    lines.append("\n## 故事线\n")
    for s in parsed["sections"]:
        lines.append(f"- {s['title']}")
    lines.append("\n## 金句\n")
    for q in parsed["quotes"][:3]:
        lines.append(f"> {q}")
    lines.append("\n## 数据来源\n")
    for src in parsed["sources"] or ["待补充"]:
        lines.append(f"- {src}")
    return "\n".join(lines)


def main() -> None:
    import argparse, json

    parser = argparse.ArgumentParser(description="Parse markdown article into PPT copy structure")
    parser.add_argument("--input", required=True, help="Path to markdown file")
    parser.add_argument("--output", required=True, help="Path to output PPT文案.md")
    args = parser.parse_args()

    parsed = parse_file(args.input)
    text = format_ppt_copy(parsed)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        f.write(text)
    print(f"Written: {out}")


if __name__ == "__main__":
    main()
