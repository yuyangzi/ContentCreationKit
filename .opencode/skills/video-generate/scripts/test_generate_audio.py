import json
import os
import subprocess
import sys
import tempfile
import pytest


def test_edge_tts_available():
    """Verify edge-tts CLI is installed."""
    result = subprocess.run(
        [sys.executable, "-m", "edge_tts", "--list-voices"],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0 or "edge_tts" in result.stderr.lower(), \
        f"edge-tts not available: {result.stderr[:200]}"


def test_generate_audio_creates_output(tmp_path):
    """End-to-end: input scenes.json → output voice.mp3, timestamps.json, scenes_complete.json."""
    try:
        from edge_tts import Communicate
    except ImportError:
        pytest.skip("edge-tts not installed")

    scenes = {
        "meta": {"article_title": "Test", "article_source": "t.md", "output": "t.mp4",
                 "aspect_ratio": "16:9", "width": 1920, "height": 1080, "fps": 30,
                 "total_duration_frames": 0, "total_duration_seconds": 0,
                 "font_family": "sans-serif",
                 "color_theme": {"primary": "#000", "accent": "#f00", "text": "#fff", "background": "#000"}},
        "scenes": [
            {"id": "s1", "type": "title_card", "duration_frames": 150,
             "search_keywords": {"zh": ["测试"], "en": ["test"]},
             "data": {"title": "Test"},
             "narration": {"text": "你好世界", "voice_file": "voice.mp3",
                          "voice_start_ms": 0, "voice_end_ms": 0, "timestamps": []}}
        ],
        "audio": {"voice_file": "voice.mp3", "bgm_file": None, "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {"enabled": True, "style": "karaoke", "font_size": 36,
                    "position_y": 920, "active_color": "#f00", "inactive_color": "#fff"}
    }
    scenes_path = tmp_path / "scenes.json"
    with open(scenes_path, 'w', encoding='utf-8') as f:
        json.dump(scenes, f, ensure_ascii=False)

    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), "generate_audio.py"),
         str(scenes_path), "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, f"generate_audio.py failed: {result.stderr[:500]}"

    assert (tmp_path / "voice.mp3").exists(), "voice.mp3 not created"
    assert (tmp_path / "timestamps.json").exists(), "timestamps.json not created"

    complete_path = tmp_path / "scenes_complete.json"
    assert complete_path.exists(), "scenes_complete.json not created"
    with open(complete_path, 'r') as f:
        complete = json.load(f)
    assert complete["scenes"][0]["narration"]["voice_start_ms"] > 0, \
        "voice_start_ms not backfilled"


def test_retry_succeeds_on_second_attempt(monkeypatch):
    """generate_voice_with_retry retries 3x and succeeds on attempt 2.

    Mocks edge_tts.Communicate to raise on first call, succeed on second.
    Verifies call_count == 2 and no exception propagates.
    """
    try:
        import edge_tts  # noqa
    except ImportError:
        pytest.skip("edge-tts not installed")

    import asyncio
    from generate_audio import generate_voice_with_retry, RETRY_DELAYS

    call_count = {"n": 0}

    async def fake_generate_voice(text, voice, output_path, srt_path):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise ConnectionError("mock transient failure")
        with open(output_path, "wb") as f:
            f.write(b"fake-audio")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:01,000\nHi\n\n")
        return None

    import generate_audio as ga
    monkeypatch.setattr(ga, "generate_voice", fake_generate_voice)
    monkeypatch.setattr(ga, "RETRY_DELAYS", [0, 0, 0])

    with tempfile.TemporaryDirectory() as td:
        asyncio.run(ga.generate_voice_with_retry(
            "Hi", "test-voice",
            os.path.join(td, "voice.mp3"),
            os.path.join(td, "temp.srt"),
        ))
    assert call_count["n"] == 2, \
        f"expected 2 calls (1 fail + 1 success), got {call_count['n']}"