"""3-layer asset search and download for video scene generation."""
import argparse
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

import requests

PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

try:
    from newspaper import Article
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False
    Article = None

USER_AGENT = "ContentCreationKit/1.0"


def download_file(url, dest, timeout=30):
    try:
        os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        resp = urllib.request.urlopen(req, timeout=timeout)
        try:
            data = resp.read()
        finally:
            resp.close()
        if len(data) <= 100:
            return False
        with open(dest, "wb") as f:
            f.write(data)
        return True
    except Exception:
        return False


def extract_ref_urls(article_source):
    with open(article_source, "r", encoding="utf-8") as f:
        content = f.read()
    md_links = re.findall(r"\]\((https?://[^\s\)]+)\)", content)
    bare_urls = re.findall(r"(?<!\()(https?://[^\s\)\]\"]+)", content)
    all_urls = list(dict.fromkeys(md_links + bare_urls))
    return all_urls[:20]


def search_reference_links(ref_urls, keyword):
    results = []
    for url in ref_urls[:3]:
        try:
            article = Article(url)
            article.download()
            article.parse()
            if article.top_image:
                results.append({
                    "url": article.top_image,
                    "source": "newspaper3k",
                    "source_url": url,
                    "type": "image",
                })
        except Exception:
            pass
    return results


def search_pexels(query, max_results=5):
    api_key = os.environ.get("PEXELS_API_KEY", PEXELS_API_KEY)
    if not api_key:
        return []
    results = []
    try:
        resp = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": max_results, "orientation": "landscape"},
        )
        if resp.status_code == 200:
            data = resp.json()
            for photo in data.get("photos", []):
                results.append({
                    "url": photo["src"]["large"],
                    "source": "pexels",
                    "source_url": photo["url"],
                    "type": "image",
                    "width": photo["width"],
                    "height": photo["height"],
                })
    except Exception:
        pass
    try:
        resp_v = requests.get(
            "https://api.pexels.com/videos/search",
            headers={"Authorization": api_key},
            params={"query": query, "per_page": 2},
        )
        if resp_v.status_code == 200:
            data_v = resp_v.json()
            for video in data_v.get("videos", []):
                video_files = video.get("video_files", [])
                best = None
                for vf in video_files:
                    if vf.get("width", 0) >= 1920:
                        best = vf
                        break
                if not best and video_files:
                    best = max(video_files, key=lambda v: v.get("width", 0))
                if best:
                    results.append({
                        "url": best["link"],
                        "source": "pexels",
                        "source_url": video["url"],
                        "type": "video",
                        "width": best.get("width", 0),
                        "height": best.get("height", 0),
                    })
    except Exception:
        pass
    return results


def search_pixabay(query, max_results=5):
    api_key = os.environ.get("PIXABAY_API_KEY", PIXABAY_API_KEY)
    if not api_key:
        return []
    results = []
    try:
        resp = requests.get(
            "https://pixabay.com/api/",
            params={
                "key": api_key, "q": query, "lang": "zh",
                "image_type": "photo", "per_page": max_results,
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            for hit in data.get("hits", []):
                results.append({
                    "url": hit["largeImageURL"],
                    "source": "pixabay",
                    "source_url": hit["pageURL"],
                    "type": "image",
                    "width": hit["imageWidth"],
                    "height": hit["imageHeight"],
                })
    except Exception:
        pass
    try:
        resp_v = requests.get(
            "https://pixabay.com/api/videos/",
            params={"key": api_key, "q": query, "per_page": 2},
        )
        if resp_v.status_code == 200:
            data_v = resp_v.json()
            for video in data_v.get("hits", []):
                videos = video.get("videos", {})
                vid_url = videos.get("large") or videos.get("medium")
                if vid_url:
                    results.append({
                        "url": vid_url.get("url", ""),
                        "source": "pixabay",
                        "source_url": video.get("pageURL", ""),
                        "type": "video",
                        "width": vid_url.get("width", 0),
                        "height": vid_url.get("height", 0),
                    })
    except Exception:
        pass
    return results


def search_unsplash(query, max_results=3):
    api_key = os.environ.get("UNSPLASH_ACCESS_KEY", UNSPLASH_ACCESS_KEY)
    if not api_key:
        return []
    results = []
    try:
        resp = requests.get(
            "https://api.unsplash.com/search/photos",
            params={
                "client_id": api_key, "query": query,
                "per_page": max_results, "orientation": "landscape",
            },
        )
        if resp.status_code == 200:
            data = resp.json()
            for result in data.get("results", []):
                results.append({
                    "url": result["urls"]["regular"],
                    "source": "unsplash",
                    "source_url": result["links"]["html"],
                    "type": "image",
                    "width": result["width"],
                    "height": result["height"],
                })
    except Exception:
        pass
    return results


def search_bing_images(query, max_results=10):
    quoted = urllib.parse.quote(query)
    url = f"https://www.bing.com/images/search?q={quoted}&first=1"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }
    delays = [2, 5]
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                murls = re.findall(r'"murl"\s*:\s*"([^"]+)"', resp.text)
                if not murls:
                    print(
                        "Warning: Bing returned 200 but 0 murl matches found",
                        file=sys.stderr,
                    )
                    return []
                results = []
                for murl in murls[:max_results]:
                    results.append({"url": murl, "source": "bing"})
                return results
            return []
        except Exception:
            if attempt < 2:
                time.sleep(delays[attempt])
    return []


def search_all_layers(keywords_zh, keywords_en, ref_urls, max_per_scene=8):
    seen = set()
    results = []
    any_found = False

    # Layer 1: reference links
    if HAS_NEWSPAPER and ref_urls:
        for kw in keywords_zh[:2]:
            try:
                for r in search_reference_links(ref_urls, kw):
                    if r["url"] not in seen:
                        seen.add(r["url"])
                        results.append(r)
                        any_found = True
            except Exception:
                pass

    # Layer 2: Pexels, Pixabay, Unsplash
    if PEXELS_API_KEY or PIXABAY_API_KEY or UNSPLASH_ACCESS_KEY:
        for kw in keywords_en[:3] + keywords_zh[:2]:
            if PEXELS_API_KEY:
                try:
                    for r in search_pexels(kw, 3):
                        if r["url"] not in seen:
                            seen.add(r["url"])
                            results.append(r)
                            any_found = True
                except Exception:
                    pass
            if PIXABAY_API_KEY:
                try:
                    for r in search_pixabay(kw, 3):
                        if r["url"] not in seen:
                            seen.add(r["url"])
                            results.append(r)
                            any_found = True
                except Exception:
                    pass
            if UNSPLASH_ACCESS_KEY:
                try:
                    for r in search_unsplash(kw, 2):
                        if r["url"] not in seen:
                            seen.add(r["url"])
                            results.append(r)
                            any_found = True
                except Exception:
                    pass

    # Layer 3: Bing
    for kw in keywords_en[:2] + keywords_zh[:2]:
        try:
            for r in search_bing_images(kw, 5):
                if r["url"] not in seen:
                    seen.add(r["url"])
                    results.append(r)
                    any_found = True
        except Exception:
            pass

    if not any_found:
        print(
            "Warning: All asset search layers returned zero results",
            file=sys.stderr,
        )

    return results[:max_per_scene]


def process_scene(scene, ref_urls, assets_dir):
    sid = scene["id"]
    keywords_zh = scene.get("search_keywords", {}).get("zh", [])
    keywords_en = scene.get("search_keywords", {}).get("en", [])

    results = search_all_layers(keywords_zh, keywords_en, ref_urls)

    assets = []
    downloaded = 0
    failed = 0
    for i, r in enumerate(results):
        raw_ext = r["url"].rsplit(".", 1)[-1] if "." in r["url"] else "jpg"
        ext = raw_ext.split("?")[0]
        if len(ext) > 5 or not ext:
            ext = "jpg"
        filename = f"{sid}_{i:02d}.{ext}"
        dest = os.path.join(assets_dir, filename)
        if download_file(r["url"], dest):
            r["file"] = f"assets/{filename}"
            r["status"] = "downloaded"
            downloaded += 1
        else:
            r["file"] = f"assets/{filename}"
            r["status"] = "failed"
            failed += 1
        assets.append(r)

    print(f"Scene {sid}: {downloaded} downloaded, {failed} failed")
    scene["_assets"] = assets
    return scene


def main():
    parser = argparse.ArgumentParser(
        description="3-layer asset search and download for video scenes"
    )
    parser.add_argument("scenes_path", help="Path to scenes.json")
    parser.add_argument(
        "--assets-dir", default=None, help="Assets output directory"
    )
    args = parser.parse_args()

    with open(args.scenes_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    base = os.path.splitext(args.scenes_path)[0]
    outdir = args.assets_dir or os.path.join(
        os.path.dirname(os.path.abspath(args.scenes_path)), "assets"
    )
    os.makedirs(outdir, exist_ok=True)

    article_source = data.get("meta", {}).get("article_source", "")
    ref_urls = []
    if article_source and os.path.exists(article_source):
        ref_urls = extract_ref_urls(article_source)

    manifest = {"scenes": {}}
    for scene in data["scenes"]:
        process_scene(scene, ref_urls, outdir)
        sid = scene["id"]
        manifest["scenes"][sid] = scene.get("_assets", [])

    manifest_path = os.path.join(outdir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    with_assets_path = f"{base}_with_assets.json"
    for scene in data["scenes"]:
        scene.pop("_assets", None)
    with open(with_assets_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"manifest.json -> {manifest_path}")
    print(f"{os.path.basename(base)}_with_assets.json -> {with_assets_path}")


if __name__ == "__main__":
    main()