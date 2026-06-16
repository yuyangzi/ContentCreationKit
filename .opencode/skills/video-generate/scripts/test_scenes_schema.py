"""Tests for scenes_schema validator."""

from scenes_schema import validate_scenes


def create_valid_base():
    return {
        "meta": {
            "article_title": "Test", "article_source": "test.md",
            "output": "test.mp4", "aspect_ratio": "16:9",
            "width": 1920, "height": 1080, "fps": 30,
            "total_duration_frames": 150, "total_duration_seconds": 5,
            "font_family": "sans-serif",
            "color_theme": {"primary": "#000", "accent": "#f00",
                          "text": "#fff", "background": "#000"}
        },
        "scenes": [],
        "audio": {"voice_file": "", "bgm_file": None,
                 "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {"enabled": True, "style": "karaoke",
                    "font_size": 36, "position_y": 920,
                    "active_color": "#fff", "inactive_color": "#000"}
    }


def test_valid_minimal_scenes_json_passes():
    data = create_valid_base()
    data["scenes"] = [{
        "id": "s1", "type": "title_card", "duration_frames": 150,
        "search_keywords": {"zh": ["t"], "en": ["t"]},
        "data": {"title": "Test"},
        "animation": {"type": "fade_in"},
        "narration": {"text": "Hi", "voice_file": "v.mp3",
                     "voice_start_ms": 0, "voice_end_ms": 1000, "timestamps": []}
    }]
    data["meta"]["total_duration_frames"] = 150
    errors = validate_scenes(data)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_invalid_scene_type_rejected():
    data = create_valid_base()
    data["scenes"] = [{
        "id": "s1", "type": "not_a_valid_type", "duration_frames": 30,
        "search_keywords": {"zh": [], "en": []}, "data": {},
        "narration": {"text": "", "voice_file": "",
                     "voice_start_ms": 0, "voice_end_ms": 0, "timestamps": []}
    }]
    errors = validate_scenes(data)
    assert any("not_a_valid_type" in e for e in errors)


def test_title_card_requires_title():
    data = create_valid_base()
    data["scenes"] = [{
        "id": "s1", "type": "title_card", "duration_frames": 150,
        "search_keywords": {"zh": [], "en": []},
        "data": {},  # missing "title"
        "narration": {"text": "", "voice_file": "",
                     "voice_start_ms": 0, "voice_end_ms": 0, "timestamps": []}
    }]
    errors = validate_scenes(data)
    assert any("title" in e.lower() for e in errors)


def test_code_block_requires_code():
    data = create_valid_base()
    data["scenes"] = [{
        "id": "s1", "type": "code_block", "duration_frames": 150,
        "search_keywords": {"zh": [], "en": []},
        "data": {"language": "python"},  # missing "code"
        "narration": {"text": "", "voice_file": "",
                     "voice_start_ms": 0, "voice_end_ms": 0, "timestamps": []}
    }]
    errors = validate_scenes(data)
    assert any("code" in e.lower() for e in errors)
