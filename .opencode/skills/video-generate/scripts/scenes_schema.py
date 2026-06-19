"""scenes.json schema validator."""

import json
from typing import Any, List

SCENE_TYPES = {"title_card", "chapter_title", "stock_footage",
               "info_card", "code_block", "outro"}
CAPTION_STYLES = {"karaoke", "minimal", "bold"}
ANIMATION_TYPES = {"ken_burns", "spring", "fade_in", "fade_out",
                   "slide_in", "stagger_reveal", "typewriter", "scale_in"}

SCENE_DATA_REQUIRED = {
    "title_card": ["title"],
    "chapter_title": ["chapter_number", "title"],
    "stock_footage": [],
    "info_card": ["layout"],
    "code_block": ["code"],
    "outro": ["cta_text"],
}


def validate_scenes(data: dict) -> List[str]:
    errors = []
    if not isinstance(data, dict):
        return ["root: must be an object"]

    # Meta
    meta = data.get("meta", {})
    for field in ["article_title", "article_source", "output", "aspect_ratio",
                  "width", "height", "fps", "total_duration_frames",
                  "total_duration_seconds", "font_family", "color_theme"]:
        if field not in meta:
            errors.append(f"meta.{field}: required")
    ct = meta.get("color_theme", {})
    for c in ["primary", "accent", "text", "background"]:
        if c not in ct:
            errors.append(f"meta.color_theme.{c}: required")

    # Scenes
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append("scenes: must be an array")
    else:
        for i, scene in enumerate(scenes):
            p = f"scenes[{i}]"
            if not isinstance(scene, dict):
                errors.append(f"{p}: must be an object"); continue
            if "id" not in scene:
                errors.append(f"{p}.id: required")
            st = scene.get("type")
            if st not in SCENE_TYPES:
                errors.append(f"{p}.type: must be one of {sorted(SCENE_TYPES)}, got '{st}'")
            dur = scene.get("duration_frames")
            if not isinstance(dur, (int, float)) or dur <= 0:
                errors.append(f"{p}.duration_frames: required positive number, got {dur}")
            sk = scene.get("search_keywords", {})
            if not isinstance(sk, dict) or "zh" not in sk or "en" not in sk:
                errors.append(f"{p}.search_keywords: requires 'zh' and 'en' keys")
            nar = scene.get("narration", {})
            for nf in ["text", "voice_file"]:
                if nf not in nar:
                    errors.append(f"{p}.narration.{nf}: required")
            # Per-type data fields
            sd = scene.get("data", {})
            if st in SCENE_DATA_REQUIRED:
                for rf in SCENE_DATA_REQUIRED[st]:
                    if rf not in sd:
                        errors.append(f"{p}.data.{rf}: required for scene type '{st}'")
            # Animation type validation (optional)
            anim = scene.get("animation")
            if anim and isinstance(anim, dict):
                at = anim.get("type")
                if at and at not in ANIMATION_TYPES:
                    errors.append(f"{p}.animation.type: must be one of {sorted(ANIMATION_TYPES)}, got '{at}'")

    # Audio
    audio = data.get("audio", {})
    for af in ["voice_file", "bgm_volume", "voice_volume"]:
        if af not in audio:
            errors.append(f"audio.{af}: required")

    # Captions
    caps = data.get("captions", {})
    if caps.get("style") not in CAPTION_STYLES:
        errors.append(f"captions.style: must be one of {sorted(CAPTION_STYLES)}")

    return errors


def validate_scenes_file(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return validate_scenes(data)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 scenes_schema.py <scenes.json>", file=sys.stderr)
        sys.exit(1)
    errors = validate_scenes_file(sys.argv[1])
    if errors:
        for e in errors:
            print(f"❌ {e}")
        sys.exit(1)
    print("✅ Schema validation passed")
