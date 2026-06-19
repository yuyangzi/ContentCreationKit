#!/usr/bin/env python3
"""Merge scenes_with_assets.json and scenes_complete.json into scenes_final.json."""

import argparse
import json
import sys


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def validate(with_assets: dict, complete: dict) -> None:
    wa_scenes = with_assets.get("scenes", [])
    co_scenes = complete.get("scenes", [])

    if not wa_scenes:
        print("Error: scenes_with_assets has empty scenes array", file=sys.stderr)
        sys.exit(1)
    if not co_scenes:
        print("Error: scenes_complete has empty scenes array", file=sys.stderr)
        sys.exit(1)

    if len(wa_scenes) != len(co_scenes):
        print(
            f"Error: scene count mismatch — with_assets has {len(wa_scenes)}, "
            f"complete has {len(co_scenes)}",
            file=sys.stderr,
        )
        sys.exit(1)

    for i, (wa_s, co_s) in enumerate(zip(wa_scenes, co_scenes)):
        if wa_s["id"] != co_s["id"]:
            print(
                f"Error: scene ID mismatch at index {i} — "
                f"with_assets has '{wa_s['id']}', complete has '{co_s['id']}'",
                file=sys.stderr,
            )
            sys.exit(1)


def merge(with_assets: dict, complete: dict) -> dict:
    merged = {
        "meta": complete["meta"],
        "audio": complete["audio"],
        "captions": complete.get("captions", with_assets.get("captions", {})),
        "scenes": [],
    }

    for wa_scene, co_scene in zip(with_assets["scenes"], complete["scenes"]):
        merged_scene = {}

        # Top-level keys from complete: id, type, duration_frames, search_keywords, animation
        for key in ("id", "type", "duration_frames", "search_keywords", "animation"):
            if key in co_scene:
                merged_scene[key] = co_scene[key]
            elif key in wa_scene:
                merged_scene[key] = wa_scene[key]

        # narration always from complete (audio is source of truth)
        merged_scene["narration"] = co_scene.get("narration", wa_scene.get("narration", {}))

        # data merge rule (per spec §4.4):
        # 1. Start with complete's data (it wins for shared non-media fields)
        # 2. media/media_manifest always come from with_assets
        # 3. Add wa-only non-media fields that complete does not have
        wa_data = wa_scene.get("data", {})
        co_data = co_scene.get("data", {})
        merged_data = {}
        merged_data.update(co_data)

        if "media" in wa_data:
            merged_data["media"] = wa_data["media"]
        if "media_manifest" in wa_data:
            merged_data["media_manifest"] = wa_data["media_manifest"]

        # Preserve wa-only non-media fields
        for key, val in wa_data.items():
            if key in ("media", "media_manifest"):
                continue
            if key not in merged_data:
                merged_data[key] = val

        merged_scene["data"] = merged_data
        merged["scenes"].append(merged_scene)

    return merged


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge scenes_with_assets.json + scenes_complete.json → scenes_final.json"
    )
    parser.add_argument("with_assets", help="Path to scenes_with_assets.json")
    parser.add_argument("complete", help="Path to scenes_complete.json")
    parser.add_argument("--output", required=True, help="Output path for scenes_final.json")
    args = parser.parse_args()

    with_assets = load_json(args.with_assets)
    complete = load_json(args.complete)

    validate(with_assets, complete)

    final = merge(with_assets, complete)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)

    print(f"✅ scenes_final.json → {args.output} ({len(final['scenes'])} scenes)")


if __name__ == "__main__":
    main()
