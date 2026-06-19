"""End-to-end test: fetch_assets.py (mocked) -> synthetic complete -> merge -> validate."""
import json
import os
import subprocess
import sys

import pytest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
FETCH = os.path.join(SCRIPTS_DIR, "fetch_assets.py")
MERGE = os.path.join(SCRIPTS_DIR, "merge_scenes.py")


def _build_input_scenes(article_source=""):
    return {
        "meta": {
            "article_title": "E2E Test", "article_source": article_source,
            "output": "out.mp4", "aspect_ratio": "16:9",
            "width": 1920, "height": 1080, "fps": 30,
            "total_duration_frames": 150, "total_duration_seconds": 5,
            "font_family": "sans-serif",
            "color_theme": {"primary": "#000", "accent": "#f00",
                           "text": "#fff", "background": "#000"},
        },
        "scenes": [
            {
                "id": "s1", "type": "title_card", "duration_frames": 90,
                "search_keywords": {"zh": [], "en": []},
                "data": {"title": "Hello"},
                "narration": {"text": "Hi", "voice_file": "v.mp3",
                             "voice_start_ms": 0, "voice_end_ms": 0,
                             "timestamps": []},
            },
            {
                "id": "s2", "type": "stock_footage", "duration_frames": 90,
                "search_keywords": {"zh": ["x"], "en": ["x"]},
                "data": {},
                "narration": {"text": "World", "voice_file": "v.mp3",
                             "voice_start_ms": 0, "voice_end_ms": 0,
                             "timestamps": []},
            },
        ],
        "audio": {"voice_file": "v.mp3", "bgm_file": None,
                 "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {"enabled": True, "style": "karaoke", "font_size": 36,
                    "position_y": 920, "active_color": "#fff",
                    "inactive_color": "#888"},
    }


def test_e2e_pipeline_fetch_then_merge(tmp_path):
    """Run fetch_assets (no API keys -> empty media), synthesize scenes_complete,
    run merge_scenes, validate final output."""
    scenes_path = tmp_path / "scenes.json"
    scenes_path.write_text(json.dumps(_build_input_scenes()),
                          encoding="utf-8")

    # Step 1: fetch_assets.py with --offline -> deterministic empty media arrays
    # (--offline blocks all network IO incl. Bing scraping)
    env = {**os.environ, "PEXELS_API_KEY": "", "PIXABAY_API_KEY": "",
           "UNSPLASH_ACCESS_KEY": ""}
    result = subprocess.run(
        [sys.executable, FETCH, str(scenes_path),
         "--outdir", str(tmp_path / "assets"), "--offline"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert result.returncode == 0, f"fetch failed: {result.stderr[:500]}"
    wa_path = tmp_path / "scenes_with_assets.json"
    assert wa_path.exists()

    # Each scene must have data.media and data.media_manifest (may be empty)
    wa = json.loads(wa_path.read_text(encoding="utf-8"))
    for scene in wa["scenes"]:
        assert "media" in scene["data"]
        assert "media_manifest" in scene["data"]

    # Step 2: synthesize scenes_complete.json (skip generate_audio.py for E2E)
    co = json.loads(scenes_path.read_text(encoding="utf-8"))
    co["meta"]["total_duration_ms"] = 5000
    for s in co["scenes"]:
        s["narration"]["voice_start_ms"] = 0
        s["narration"]["voice_end_ms"] = 1000
        s["narration"]["timestamps"] = [
            {"word": s["narration"]["text"], "start_ms": 0, "end_ms": 1000}
        ]
    co_path = tmp_path / "scenes_complete.json"
    co_path.write_text(json.dumps(co), encoding="utf-8")

    # Step 3: merge_scenes.py
    final_path = tmp_path / "scenes_final.json"
    result = subprocess.run(
        [sys.executable, MERGE, str(wa_path), str(co_path),
         "--output", str(final_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"merge failed: {result.stderr[:500]}"

    # Step 4: validate
    sys.path.insert(0, SCRIPTS_DIR)
    from scenes_schema import validate_scenes
    final = json.loads(final_path.read_text(encoding="utf-8"))
    errs = validate_scenes(final)
    assert errs == [], f"validate_scenes failed: {errs}"

    # Asserts both scene types backfilled, media defaulted to empty
    title_scene = next(s for s in final["scenes"] if s["type"] == "title_card")
    stock_scene = next(s for s in final["scenes"] if s["type"] == "stock_footage")
    assert title_scene["data"]["title"] == "Hello"  # preserved
    assert title_scene["data"].get("media", []) == []
    assert stock_scene["data"].get("media", []) == []
    assert "media_manifest" in stock_scene["data"]
    # Narration timestamps merged from complete
    assert title_scene["narration"]["voice_end_ms"] == 1000
