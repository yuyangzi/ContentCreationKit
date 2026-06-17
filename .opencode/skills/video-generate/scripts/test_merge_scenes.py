import json
import os
import subprocess
import sys
import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MERGE_SCRIPT = os.path.join(SCRIPT_DIR, "merge_scenes.py")


def test_merge_scenes_creates_final(tmp_path):
    """merge_scenes.py reads scenes_with_assets.json + scenes_complete.json → scenes_final.json."""
    with_assets = {
        "meta": {"article_title": "T", "article_source": "t.md", "output": "t.mp4",
                "aspect_ratio": "16:9", "width": 1920, "height": 1080, "fps": 30,
                "total_duration_frames": 150, "total_duration_seconds": 5,
                "font_family": "sans-serif",
                "color_theme": {"primary": "#000", "accent": "#f00", "text": "#fff", "background": "#000"}},
        "scenes": [{
            "id": "s1", "type": "stock_footage", "duration_frames": 150,
            "search_keywords": {"zh": ["测试"], "en": ["test"]},
            "data": {"media": [{"file": "assets/s1_00.jpg", "source": "pexels",
                                "source_url": "x", "type": "image",
                                "width": 1920, "height": 1080}],
                    "media_manifest": []},
            "narration": {"text": "Hi", "voice_file": "voice.mp3",
                          "voice_start_ms": 0, "voice_end_ms": 0, "timestamps": []}
        }],
        "audio": {"voice_file": "voice.mp3", "bgm_file": None,
                 "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {"enabled": True, "style": "karaoke", "font_size": 36,
                    "position_y": 920, "active_color": "#f00", "inactive_color": "#fff"}
    }
    complete = json.loads(json.dumps(with_assets))
    complete["scenes"][0]["narration"]["voice_start_ms"] = 100
    complete["scenes"][0]["narration"]["voice_end_ms"] = 1500
    complete["scenes"][0]["narration"]["timestamps"] = [
        {"word": "Hi", "start_ms": 100, "end_ms": 1500}
    ]
    complete["meta"]["total_duration_ms"] = 1500
    complete["meta"]["total_duration_frames"] = 45
    wa_path = tmp_path / "scenes_with_assets.json"
    co_path = tmp_path / "scenes_complete.json"
    wa_path.write_text(json.dumps(with_assets, ensure_ascii=False), encoding="utf-8")
    co_path.write_text(json.dumps(complete, ensure_ascii=False), encoding="utf-8")

    out_path = tmp_path / "scenes_final.json"
    result = subprocess.run(
        [sys.executable, MERGE_SCRIPT,
         str(wa_path), str(co_path), "--output", str(out_path)],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"merge_scenes.py failed: {result.stderr[:500]}"
    final = json.loads(out_path.read_text(encoding="utf-8"))
    # Asset data preserved
    assert final["scenes"][0]["data"]["media"][0]["file"] == "assets/s1_00.jpg"
    # Timestamp data preserved
    assert final["scenes"][0]["narration"]["voice_start_ms"] == 100
    assert final["scenes"][0]["narration"]["timestamps"][0]["word"] == "Hi"
    # Meta from complete
    assert final["meta"]["total_duration_ms"] == 1500


def test_merge_rejects_mismatched_scene_count(tmp_path):
    """merge_scenes.py errors out if scene counts differ."""
    wa = {"meta": {"article_title": "T"}, "scenes": [{"id": "s1"}, {"id": "s2"}], "audio": {}, "captions": {}}
    co = {"meta": {"article_title": "T"}, "scenes": [{"id": "s1"}], "audio": {}, "captions": {}}
    wa_path = tmp_path / "wa.json"; co_path = tmp_path / "co.json"
    wa_path.write_text(json.dumps(wa), encoding="utf-8")
    co_path.write_text(json.dumps(co), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, MERGE_SCRIPT,
         str(wa_path), str(co_path), "--output", str(tmp_path / "final.json")],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode != 0
    assert "count" in result.stderr.lower() or "mismatch" in result.stderr.lower()


def test_merge_rejects_mismatched_scene_ids(tmp_path):
    """merge_scenes.py errors out if scene IDs are reordered/different."""
    wa = {"meta": {"article_title": "T"}, "scenes": [{"id": "s1"}, {"id": "s2"}], "audio": {}, "captions": {}}
    co = {"meta": {"article_title": "T"}, "scenes": [{"id": "s2"}, {"id": "s1"}], "audio": {}, "captions": {}}
    wa_path = tmp_path / "wa.json"; co_path = tmp_path / "co.json"
    wa_path.write_text(json.dumps(wa), encoding="utf-8")
    co_path.write_text(json.dumps(co), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, MERGE_SCRIPT,
         str(wa_path), str(co_path), "--output", str(tmp_path / "final.json")],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode != 0
    assert "id" in result.stderr.lower() or "order" in result.stderr.lower()
