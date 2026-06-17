import json
import os
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