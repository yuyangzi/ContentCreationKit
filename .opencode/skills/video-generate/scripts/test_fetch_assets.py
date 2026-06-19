import json
import os
import subprocess
import sys
import pytest
from unittest.mock import patch, MagicMock

from fetch_assets import (
    search_pexels, search_pixabay, search_unsplash,
    search_bing_images, search_all_layers, extract_ref_urls,
)


class MockResp:
    def __init__(self, status, payload):
        self.status_code = status
        self._payload = payload
    def json(self):
        return self._payload


def test_keyword_search_returns_results(monkeypatch):
    """search_pexels returns images when API key set and mock returns 200."""
    monkeypatch.setenv("PEXELS_API_KEY", "test-key")
    fake = MockResp(200, {"photos": [
        {"id": 1, "src": {"large": "https://x/y.jpg"},
         "url": "https://pexels.com/photo/1", "width": 1920, "height": 1080,
         "photographer": "Test"}
    ]})
    with patch("fetch_assets.requests.get", return_value=fake):
        results = search_pexels("machine learning", 3)
    assert len(results) == 1
    assert results[0]["source"] == "pexels"
    assert results[0]["type"] == "image"


def test_extract_ref_urls_from_markdown(tmp_path):
    """extract_ref_urls parses markdown links and bare URLs from article file."""
    md = tmp_path / "article.md"
    md.write_text(
        "See [guide](https://example.com/article-1) for details.\n"
        "Also: https://other.com/page-2 and https://other.com/page-3"
    )
    urls = extract_ref_urls(str(md))
    assert "https://example.com/article-1" in urls
    assert "https://other.com/page-2" in urls
    assert "https://other.com/page-3" in urls


def test_search_all_layers_returns_empty_without_keys(monkeypatch):
    """When all API keys are unset and Bing scraping blocked, returns empty list.

    NOTE: Patches module-level constants directly (monkeypatch.delenv on os.environ
    would be too late — module-level `PEXELS_API_KEY = os.environ.get(...)` was
    already evaluated at import time).
    """
    import fetch_assets as fa
    monkeypatch.setattr(fa, "PEXELS_API_KEY", "")
    monkeypatch.setattr(fa, "PIXABAY_API_KEY", "")
    monkeypatch.setattr(fa, "UNSPLASH_ACCESS_KEY", "")
    monkeypatch.setattr(fa, "HAS_NEWSPAPER", False)
    with patch("fetch_assets.requests.get", side_effect=Exception("network blocked")):
        results = search_all_layers(["测试"], ["test"], [])
    assert isinstance(results, list)
    assert len(results) == 0


def test_search_pixabay_returns_results(monkeypatch):
    """search_pixabay returns images when API key set and mock returns 200."""
    import fetch_assets as fa
    monkeypatch.setattr(fa, "PIXABAY_API_KEY", "test-key")
    fake = MockResp(200, {"hits": [
        {"largeImageURL": "https://x/y.jpg", "pageURL": "https://pixabay.com/photo/1",
         "imageWidth": 1920, "imageHeight": 1080}
    ]})
    with patch("fetch_assets.requests.get", return_value=fake):
        results = search_pixabay("machine learning", 3)
    assert len(results) == 1
    assert results[0]["source"] == "pixabay"
    assert results[0]["type"] == "image"


def test_search_bing_images_returns_results(monkeypatch):
    """search_bing_images parses murl from Bing HTML when mock returns 200."""
    fake = MockResp(200, {})  # .json() not called; .text is used
    fake.text = '<html>"murl":"https://example.com/img1.jpg"</html>'
    with patch("fetch_assets.requests.get", return_value=fake):
        results = search_bing_images("test query", 5)
    assert len(results) == 1
    assert results[0]["url"] == "https://example.com/img1.jpg"
    assert results[0]["source"] == "bing"


def test_download_file_returns_true_on_success(tmp_path):
    """download_file writes content to dest and returns True on valid file."""
    from fetch_assets import download_file
    dest = tmp_path / "test.jpg"
    import urllib.request
    from unittest.mock import Mock
    fake_response = Mock()
    fake_response.read.return_value = b"x" * 200
    with patch("urllib.request.urlopen", return_value=fake_response):
        result = download_file("https://example.com/img.jpg", str(dest))
    assert result is True
    assert dest.exists()
    assert dest.stat().st_size == 200


def test_download_file_returns_false_on_empty(tmp_path):
    """download_file returns False when response is under 100 bytes."""
    from fetch_assets import download_file
    dest = tmp_path / "empty.jpg"
    import urllib.request
    from unittest.mock import Mock
    fake_response = Mock()
    fake_response.read.return_value = b"x" * 50
    with patch("urllib.request.urlopen", return_value=fake_response):
        result = download_file("https://example.com/empty.jpg", str(dest))
    assert result is False
    assert not dest.exists()


def _make_minimal_scenes_json(tmp_path, article_path=""):
    """Minimal valid scenes.json for CLI invocation."""
    return {
        "meta": {
            "article_title": "T", "article_source": article_path,
            "output": "out.mp4", "aspect_ratio": "16:9",
            "width": 1920, "height": 1080, "fps": 30,
            "total_duration_frames": 150, "total_duration_seconds": 5,
            "font_family": "sans-serif",
            "color_theme": {"primary": "#000", "accent": "#f00",
                           "text": "#fff", "background": "#000"},
        },
        "scenes": [{
            "id": "s1", "type": "stock_footage", "duration_frames": 150,
            "search_keywords": {"zh": ["test"], "en": ["test"]},
            "data": {},
            "narration": {"text": "Hi", "voice_file": "v.mp3",
                         "voice_start_ms": 0, "voice_end_ms": 0,
                         "timestamps": []},
        }],
        "audio": {"voice_file": "v.mp3", "bgm_file": None,
                 "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {"enabled": True, "style": "karaoke", "font_size": 36,
                    "position_y": 920, "active_color": "#fff",
                    "inactive_color": "#888"},
    }


def test_cli_accepts_outdir_flag(tmp_path, monkeypatch):
    """fetch_assets.py CLI must accept --outdir as canonical name."""
    import subprocess, sys, os
    SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "fetch_assets.py")
    scenes_path = tmp_path / "scenes.json"
    scenes_path.write_text(json.dumps(_make_minimal_scenes_json(tmp_path)),
                          encoding="utf-8")
    outdir = tmp_path / "myassets"
    env = {**os.environ, "PEXELS_API_KEY": "", "PIXABAY_API_KEY": "",
           "UNSPLASH_ACCESS_KEY": ""}
    result = subprocess.run(
        [sys.executable, SCRIPT, str(scenes_path),
         "--outdir", str(outdir), "--offline"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert result.returncode == 0, f"stderr: {result.stderr[:500]}"
    assert outdir.exists()
    assert (outdir / "manifest.json").exists()
    assert (tmp_path / "scenes_with_assets.json").exists()


def test_cli_accepts_article_source_flag(tmp_path, monkeypatch):
    """fetch_assets.py CLI must accept --article-source overriding meta."""
    import subprocess, sys, os
    SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "fetch_assets.py")
    article = tmp_path / "myarticle.md"
    article.write_text("# Article\nSee https://example.com/page\n",
                      encoding="utf-8")
    scenes_path = tmp_path / "scenes.json"
    scenes_path.write_text(json.dumps(_make_minimal_scenes_json(tmp_path)),
                          encoding="utf-8")
    env = {**os.environ, "PEXELS_API_KEY": "", "PIXABAY_API_KEY": "",
           "UNSPLASH_ACCESS_KEY": ""}
    result = subprocess.run(
        [sys.executable, SCRIPT, str(scenes_path),
         "--article-source", str(article),
         "--outdir", str(tmp_path / "assets"), "--offline"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert result.returncode == 0, f"stderr: {result.stderr[:500]}"


def test_cli_accepts_assets_dir_alias(tmp_path):
    """fetch_assets.py CLI must keep --assets-dir as deprecated alias."""
    import subprocess, sys, os
    SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "fetch_assets.py")
    scenes_path = tmp_path / "scenes.json"
    scenes_path.write_text(json.dumps(_make_minimal_scenes_json(tmp_path)),
                          encoding="utf-8")
    env = {**os.environ, "PEXELS_API_KEY": "", "PIXABAY_API_KEY": "",
           "UNSPLASH_ACCESS_KEY": ""}
    result = subprocess.run(
        [sys.executable, SCRIPT, str(scenes_path),
         "--assets-dir", str(tmp_path / "assets"), "--offline"],
        capture_output=True, text=True, timeout=60, env=env,
    )
    assert result.returncode == 0, f"stderr: {result.stderr[:500]}"


def test_process_scene_backfills_media_and_manifest(monkeypatch, tmp_path):
    """process_scene() must populate data.media (downloaded) and
    data.media_manifest (all candidates), preserving existing data fields."""
    import fetch_assets as fa
    monkeypatch.setattr(fa, "PEXELS_API_KEY", "fake")
    monkeypatch.setattr(fa, "PIXABAY_API_KEY", "")
    monkeypatch.setattr(fa, "UNSPLASH_ACCESS_KEY", "")
    monkeypatch.setattr(fa, "HAS_NEWSPAPER", False)

    fake_results = [
        {"url": "https://x/ok.jpg", "source": "pexels",
         "source_url": "https://pexels.com/p/1", "type": "image",
         "width": 1920, "height": 1080},
        {"url": "https://x/bad.jpg", "source": "pexels",
         "source_url": "https://pexels.com/p/2", "type": "image",
         "width": 1280, "height": 720},
    ]
    monkeypatch.setattr(fa, "search_all_layers",
                        lambda zh, en, refs: fake_results)

    def fake_download(url, dest, timeout=30):
        if "ok" in url:
            os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
            with open(dest, "wb") as f:
                f.write(b"x" * 200)
            return True
        return False
    monkeypatch.setattr(fa, "download_file", fake_download)

    scene = {
        "id": "s1", "type": "stock_footage",
        "search_keywords": {"zh": ["x"], "en": ["x"]},
        "data": {"text_overlays": [{"text": "preserved"}]},
    }
    fa.process_scene(scene, [], str(tmp_path))

    # data.media: downloaded only
    assert "media" in scene["data"]
    assert len(scene["data"]["media"]) == 1
    assert scene["data"]["media"][0]["status"] == "downloaded"
    assert scene["data"]["media"][0]["file"].endswith("s1_00.jpg")

    # data.media_manifest: all candidates
    assert "media_manifest" in scene["data"]
    assert len(scene["data"]["media_manifest"]) == 2
    statuses = [m["status"] for m in scene["data"]["media_manifest"]]
    assert "downloaded" in statuses and "failed" in statuses

    # Existing data field preserved
    assert scene["data"]["text_overlays"] == [{"text": "preserved"}]


def test_process_scene_preserves_title_card_data(monkeypatch, tmp_path):
    """For non-stock scenes (e.g. title_card), process_scene must not
    overwrite existing data.title; media/media_manifest may be empty arrays."""
    import fetch_assets as fa
    monkeypatch.setattr(fa, "search_all_layers", lambda zh, en, refs: [])

    scene = {
        "id": "s_title", "type": "title_card",
        "search_keywords": {"zh": [], "en": []},
        "data": {"title": "My Video", "subtitle": "An intro"},
    }
    fa.process_scene(scene, [], str(tmp_path))

    assert scene["data"]["title"] == "My Video"
    assert scene["data"]["subtitle"] == "An intro"
    assert scene["data"].get("media", []) == []
    assert scene["data"].get("media_manifest", []) == []


def test_process_scene_no_data_key_initializes_it(monkeypatch, tmp_path):
    """If scene lacks a 'data' key, process_scene must create it without crash."""
    import fetch_assets as fa
    monkeypatch.setattr(fa, "search_all_layers", lambda zh, en, refs: [])

    scene = {
        "id": "s2", "type": "stock_footage",
        "search_keywords": {"zh": [], "en": []},
        # no 'data' key at all
    }
    fa.process_scene(scene, [], str(tmp_path))
    assert "data" in scene
    assert scene["data"]["media"] == []
    assert scene["data"]["media_manifest"] == []
