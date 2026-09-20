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
        if key == "hr":
            # hr 无文字承载，渐变允许保留（官方 §4.1.3）
            continue
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
