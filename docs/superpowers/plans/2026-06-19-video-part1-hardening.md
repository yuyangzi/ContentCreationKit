# Video Part 1 Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the article-to-video Part 1 data preparation pipeline (`fetch_assets.py` -> `generate_audio.py` -> `merge_scenes.py`) mergeable, runnable, and verifiable by aligning CLI/docs, backfilling assets into `scene.data.media`, fixing merge field preservation, and locking contracts with tests.

**Architecture:** Three Python scripts produce a chain of JSON artifacts: `scenes.json` -> `scenes_with_assets.json` -> `scenes_complete.json` -> `scenes_final.json`. Each artifact is validated by `scenes_schema.py` and a Python-TypeScript contract test. The hardening fixes (1) §4.3 schema ambiguity by locking unified field set for `media`/`media_manifest`, (2) CLI parameter contract (`--outdir` with `--assets-dir` deprecated alias), (3) merge field-preservation rules, and (4) docs-CLI alignment via automated test.

**Tech Stack:** Python 3 (stdlib + `requests` + optional `newspaper3k`), pytest, argparse, Edge-TTS (downstream), Remotion/TypeScript (downstream consumer of `scenes_final.json`).

**Source spec:** `docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md`

**Revision:** v2 (2026-06-19) — Applied 6 fixes after Metis/Momus review of v1:
1. Task 3: corrected `input-props.ts` line numbers and single-line `oldString` (file is 99 lines, not 489+)
2. Task 5: removed dead if/else branch; introduced `--offline` flag for deterministic test runs
3. Task 11: removed misleading "schema may need updating" fallback (verified `scenes_schema.py` does not validate media item internals)
4. Task 12: rewrote regex to match SKILL.md's `$VENV_PYTHON $SCRIPTS_DIR/xxx.py` form + added sanity test for all 4 scripts
5. Task 14: re-scoped (SKILL.md fetch_assets example was already correct; only test counts need sync)
6. Tasks 4/15/17: added `--offline` to fetch_assets invocations to prevent Bing network leak in tests
7. Tasks 16/17: replaced hard-coded `origin/feat/video-scaffold` with `$BASE` variable resolved at runtime
8. Task 17: replaced fragile `grep` guard with structural diff of `match_scene_timestamps` body

**Review findings addressed (from Metis + Momus):**

- BLOCKER: §4.3 `media`/`media_manifest` schema mismatch with plan code -> Task 2
- BLOCKER: §6 AC2 only mentions stock_footage but §4.3 says all scenes -> Task 13
- IMPORTANT: AC6 docs-match-CLI not auto-verifiable -> Task 12
- IMPORTANT: §4.4 merge rule ambiguity -> Task 9
- IMPORTANT: `process_scene()` data backfill could overwrite existing data -> Task 6
- MEDIUM: `status` field missing in TypeScript `StockMediaItem` -> Task 3
- MEDIUM: SKILL.md test count drift, captions merge rule, article_source path resolution -> Tasks 4, 9, 14

---

## File Structure

### Files to modify

- `.opencode/skills/video-generate/scripts/fetch_assets.py` — CLI args + backfill into `scene.data.media`/`media_manifest`
- `.opencode/skills/video-generate/scripts/merge_scenes.py` — preserve wa-only non-media fields; document captions rule
- `.opencode/skills/video-generate/scripts/test_fetch_assets.py` — add CLI integration + backfill tests
- `.opencode/skills/video-generate/scripts/test_merge_scenes.py` — add wa-only field preservation test
- `.opencode/skills/video-generate/scripts/test_contract_compliance.py` — assert all `StockMediaItem` fields incl. `status`
- `.opencode/skills/video-generate/SKILL.md` — sync CLI commands and test count
- `.opencode/skills/video-generate/references/schemas.md` — precise table schemas
- `.opencode/skills/video-generate/references/pipeline-dataflow.md` — document `data.media` lifecycle
- `.opencode/skills/video-generate/remotion/src/input-props.ts` — add `status?` field to `StockMediaItem`
- `docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md` — fix §4.3 example, §6 AC2, add E2E AC

### Files to create

- `.opencode/skills/video-generate/scripts/test_docs_cli_alignment.py` — verify SKILL.md command examples match argparse
- `.opencode/skills/video-generate/scripts/test_e2e_pipeline.py` — fetch (mocked) -> merge -> validate

### Files NOT to touch (out-of-scope)

- `generate_audio.py` `match_scene_timestamps()` character-position logic (Metis warning: do NOT over-fix)
- Anything under `remotion/src/` other than `input-props.ts` `StockMediaItem`
- Any Part 2 rendering: `Composition.tsx`, `render_video.sh`, MP4 paths, `.opencode/commands/video-*`
- Untracked `content/**` files in the workspace

---

## Task 1: Branch sync and environment

**Files:** None (env only)

- [ ] **Step 1: Verify branch**

Run: `git status && git branch --show-current`
Expected: branch is `feat/video-scaffold`. If not, STOP and ask user.

- [ ] **Step 2: Confirm Part 1 file inventory**

Run: `ls .opencode/skills/video-generate/scripts/`
Expected: contains `fetch_assets.py`, `generate_audio.py`, `merge_scenes.py`, `scenes_schema.py`, and 5 `test_*.py` files.

- [ ] **Step 3: Set up skill-private virtualenv if missing**

Run:

```bash
test -d .opencode/skills/video-generate/.venv && echo "venv exists" || (
  cd .opencode/skills/video-generate &&
  python3 -m venv .venv &&
  .venv/bin/python -m pip install --upgrade pip &&
  .venv/bin/python -m pip install requests pytest newspaper3k lxml_html_clean
)
```

Expected: install completes without errors.

- [ ] **Step 4: Run baseline pytest, record collected count**

Run:

```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest --collect-only -q 2>&1 | tail -5
```

Expected: pytest collects N tests. Record N as `BASELINE_TEST_COUNT` for Task 14 reference.

---

(continued in subsequent edits)

## Task 2: Lock unified media schema in references

**Files:** Modify `.opencode/skills/video-generate/references/schemas.md`

**Background:** Spec §4.3 example JSON shows two different field sets for `media[]` vs `media_manifest[]` (BLOCKER per Momus). The plan code uses a unified schema. This task locks unified schema as single source of truth.

- [ ] **Step 1: Find insertion point**

Run: `grep -n 'stock_footage\|^### narration' .opencode/skills/video-generate/references/schemas.md`
Expected: `stock_footage` row near line 53; `### narration` heading near line 58.

- [ ] **Step 2: Insert schema sub-section before `### narration`**

Use Edit tool. Find this exact text in `references/schemas.md`:

```
### narration
```

Replace with this expanded block (note: `### narration` is preserved at the end):

```
### media[] / media_manifest[] item schema

Both `data.media[]` and `data.media_manifest[]` use the **same item schema**. The two arrays differ only by content:
- `media[]`: only items with `status == "downloaded"` (consumed by Remotion render)
- `media_manifest[]`: all candidates including failed downloads (debug/manual replacement)

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | string | yes | Project-relative path, e.g. `"assets/s1_00.jpg"` |
| `source` | enum | yes | One of: `pexels`, `pixabay`, `unsplash`, `bing`, `newspaper3k` |
| `source_url` | string | yes | Original page URL; `""` if unknown |
| `type` | enum | yes | `image` or `video` |
| `width` | number | yes | Pixels; `0` if unknown |
| `height` | number | yes | Pixels; `0` if unknown |
| `status` | enum | yes | `downloaded` or `failed` |

**Status lifecycle:** Search-layer results carry no status. After `download_file()` runs, each candidate is tagged `downloaded` (HTTP 200, body > 100 bytes) or `failed`. No `pending` state in persisted JSON.

**Empty arrays:** When no candidates found OR all downloads failed, both arrays may be empty (`[]`). Render must degrade gracefully (text-only background).

**TypeScript counterpart:** `StockMediaItem` in `remotion/src/input-props.ts` has `status?: "downloaded" | "failed"` as optional.

### narration
```

- [ ] **Step 3: Verify**

Run: `grep -A 5 'media\[\] / media_manifest\[\] item schema' .opencode/skills/video-generate/references/schemas.md`
Expected: header + table fragment visible.

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/video-generate/references/schemas.md
git commit -m "docs(schemas): lock unified media/media_manifest item schema"
```

---

## Task 3: Add `status?` to TypeScript `StockMediaItem`

**Files:** Modify `.opencode/skills/video-generate/remotion/src/input-props.ts`

**NOTE (verified):** The file is ~99 lines total. `StockMediaItem` is on **line 60** as a **single-line interface** (NOT multi-line). Do not assume multi-line layout.

- [ ] **Step 1: Locate the interface and verify single-line format**

Run:
```bash
grep -n 'interface StockMediaItem' .opencode/skills/video-generate/remotion/src/input-props.ts
sed -n '60p' .opencode/skills/video-generate/remotion/src/input-props.ts
```

Expected line ~60 content (single line):
```typescript
export interface StockMediaItem { file: string; source: string; source_url?: string; type: "image" | "video"; width?: number; height?: number; relevance_score?: number; }
```

If the format differs (e.g. multi-line), copy the exact content shown by `sed` and adjust the Edit tool oldString/newString below to match the actual layout exactly.

- [ ] **Step 2: Add `status?` field (single-line format)**

Use Edit tool with these exact strings:

oldString:
```
relevance_score?: number; }
```

newString:
```
relevance_score?: number; status?: "downloaded" | "failed"; }
```

This is unique on line 60 (the only place `relevance_score?: number; }` appears). The closing `}` here belongs to `StockMediaItem`.

- [ ] **Step 3: Verify**

Run: `grep -n 'status?: "downloaded"' .opencode/skills/video-generate/remotion/src/input-props.ts`
Expected: matches inside `StockMediaItem` definition on line 60.

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/video-generate/remotion/src/input-props.ts
git commit -m "feat(types): add status? field to StockMediaItem"
```

---

## Task 4: Failing tests — `fetch_assets.py` CLI accepts `--outdir` and `--article-source`

**Files:** Modify `.opencode/skills/video-generate/scripts/test_fetch_assets.py`

**Background:** Currently `fetch_assets.py` has only `--assets-dir`. We will add `--outdir` (canonical) and keep `--assets-dir` as deprecated alias. We also add `--article-source` to override `meta.article_source`.

- [ ] **Step 1: Append failing CLI tests**

Use Edit tool. Find the last line of `test_fetch_assets.py` (run `tail -5 .opencode/skills/video-generate/scripts/test_fetch_assets.py` to confirm). Append after the last test:

```python


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
```

- [ ] **Step 2: Run tests to verify they FAIL**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_fetch_assets.py -v -k "cli_accepts" 2>&1 | tail -20
```
Expected: FAIL — `--outdir` and `--article-source` are not yet recognized by argparse.

- [ ] **Step 3: Commit failing tests**

```bash
git add .opencode/skills/video-generate/scripts/test_fetch_assets.py
git commit -m "test(fetch_assets): add failing CLI tests for --outdir, --article-source, --assets-dir alias"
```

---

## Task 5: Implement `--outdir` / `--article-source` / `--assets-dir` alias in `fetch_assets.py`

**Files:** Modify `.opencode/skills/video-generate/scripts/fetch_assets.py`

- [ ] **Step 1: Replace argparse block**

Use Edit tool. Find this exact block in `fetch_assets.py` (currently lines 340-348):

```python
    parser = argparse.ArgumentParser(
        description="3-layer asset search and download for video scenes"
    )
    parser.add_argument("scenes_path", help="Path to scenes.json")
    parser.add_argument(
        "--assets-dir", default=None, help="Assets output directory"
    )
    args = parser.parse_args()
```

Replace with:

```python
    parser = argparse.ArgumentParser(
        description="3-layer asset search and download for video scenes"
    )
    parser.add_argument("scenes_path", help="Path to scenes.json")
    parser.add_argument(
        "--outdir", "--assets-dir", dest="outdir", default=None,
        help="Assets output directory (default: <scenes_dir>/assets)",
    )
    parser.add_argument(
        "--article-source", dest="article_source", default=None,
        help="Path to source article markdown (overrides meta.article_source)",
    )
    parser.add_argument(
        "--offline", dest="offline", action="store_true",
        help="Skip all network search/download (test-only). Produces empty media arrays.",
    )
    args = parser.parse_args()

    # Honor --offline by short-circuiting all search layers.
    if args.offline:
        global PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY
        PEXELS_API_KEY = ""
        PIXABAY_API_KEY = ""
        UNSPLASH_ACCESS_KEY = ""
        # Disable Bing scraping by monkeypatching the function reference here.
        global search_bing_images
        search_bing_images = lambda q, mr=5: []
```

- [ ] **Step 2: Use `args.outdir` and `args.article_source` consistently**

Find this block (lines 350-362):

```python
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
```

Replace with:

```python
    with open(args.scenes_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    scenes_dir = os.path.dirname(os.path.abspath(args.scenes_path))
    outdir = args.outdir or os.path.join(scenes_dir, "assets")
    os.makedirs(outdir, exist_ok=True)

    # Article source: --article-source > meta.article_source > none
    article_source = args.article_source or data.get("meta", {}).get(
        "article_source", ""
    )
    ref_urls = []
    if article_source and os.path.exists(article_source):
        ref_urls = extract_ref_urls(article_source)
    elif article_source:
        print(
            f"Warning: article source not found: {article_source}",
            file=sys.stderr,
        )
```

- [ ] **Step 3: Fix the `scenes_with_assets.json` output path to a fixed location**

Find this block (lines ~373-378 in the current `fetch_assets.py`):

```python
    with_assets_path = f"{base}_with_assets.json"
    for scene in data["scenes"]:
        scene.pop("_assets", None)
    with open(with_assets_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

Replace with:

```python
    # Always write to scenes_with_assets.json in scenes_dir.
    # If input is itself scenes_with_assets.json, this is a no-op overwrite
    # (idempotent re-run). Avoids chained naming like _with_assets_with_assets.
    with_assets_path = os.path.join(scenes_dir, "scenes_with_assets.json")
    for scene in data["scenes"]:
        scene.pop("_assets", None)
    with open(with_assets_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

Also update the print statements at the bottom from `os.path.basename(base)` to a fixed string. Find:

```python
    print(f"manifest.json -> {manifest_path}")
    print(f"{os.path.basename(base)}_with_assets.json -> {with_assets_path}")
```

Replace with:

```python
    print(f"manifest.json -> {manifest_path}")
    print(f"scenes_with_assets.json -> {with_assets_path}")
```

The `base = os.path.splitext(args.scenes_path)[0]` line should also be removed (it's no longer used). If it still exists after the Step 2 edit, find:

```python
    base = os.path.splitext(args.scenes_path)[0]
```

and delete it (replace with empty string).

- [ ] **Step 4: Run CLI tests — should now PASS**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_fetch_assets.py -v -k "cli_accepts" 2>&1 | tail -15
```
Expected: 3 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/scripts/fetch_assets.py
git commit -m "feat(fetch_assets): add --outdir + --article-source CLI args, keep --assets-dir alias"
```

---

## Task 6: Failing tests — `process_scene()` backfills `data.media` and `data.media_manifest` without overwriting existing data

**Files:** Modify `.opencode/skills/video-generate/scripts/test_fetch_assets.py`

**Background:** Currently `process_scene()` writes assets to `scene["_assets"]` (a temp key that gets popped). We need it to write to `scene["data"]["media"]` (downloaded only) and `scene["data"]["media_manifest"]` (all candidates) without overwriting existing fields like `title_card.data.title`.

- [ ] **Step 1: Append failing tests for backfill behavior**

Use Edit tool to append after the CLI tests added in Task 4:

```python


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
```

- [ ] **Step 2: Run tests to verify they FAIL**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_fetch_assets.py -v -k "process_scene" 2>&1 | tail -15
```
Expected: FAIL — `scene["data"]["media"]` not yet populated.

- [ ] **Step 3: Commit failing tests**

```bash
git add .opencode/skills/video-generate/scripts/test_fetch_assets.py
git commit -m "test(fetch_assets): add failing tests for data.media/manifest backfill"
```

---

## Task 7: Implement `process_scene()` data backfill

**Files:** Modify `.opencode/skills/video-generate/scripts/fetch_assets.py`

- [ ] **Step 1: Replace `process_scene()` body**

Use Edit tool. Find this exact block (currently lines 308-337):

```python
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
```

Replace with:

```python
def _normalize_asset(raw, file_path, status):
    """Project a search-layer result into the unified media item schema."""
    return {
        "file": file_path,
        "source": raw.get("source", "unknown"),
        "source_url": raw.get("source_url", ""),
        "type": raw.get("type", "image"),
        "width": raw.get("width", 0),
        "height": raw.get("height", 0),
        "status": status,
    }


def process_scene(scene, ref_urls, assets_dir):
    sid = scene["id"]
    keywords_zh = scene.get("search_keywords", {}).get("zh", [])
    keywords_en = scene.get("search_keywords", {}).get("en", [])

    results = search_all_layers(keywords_zh, keywords_en, ref_urls)

    manifest_items = []
    downloaded = 0
    failed = 0
    for i, r in enumerate(results):
        raw_ext = r["url"].rsplit(".", 1)[-1] if "." in r["url"] else "jpg"
        ext = raw_ext.split("?")[0]
        if len(ext) > 5 or not ext:
            ext = "jpg"
        filename = f"{sid}_{i:02d}.{ext}"
        dest = os.path.join(assets_dir, filename)
        file_rel = f"assets/{filename}"
        if download_file(r["url"], dest):
            manifest_items.append(_normalize_asset(r, file_rel, "downloaded"))
            downloaded += 1
        else:
            manifest_items.append(_normalize_asset(r, file_rel, "failed"))
            failed += 1

    print(f"Scene {sid}: {downloaded} downloaded, {failed} failed")

    # Backfill data.media (downloaded) and data.media_manifest (all),
    # preserving existing data fields like title_card.data.title
    scene.setdefault("data", {})
    scene["data"]["media"] = [
        m for m in manifest_items if m["status"] == "downloaded"
    ]
    scene["data"]["media_manifest"] = manifest_items
    # Keep _assets as a transient mirror for manifest.json output
    scene["_assets"] = manifest_items
    return scene
```

- [ ] **Step 2: Run process_scene tests — should PASS**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_fetch_assets.py -v -k "process_scene" 2>&1 | tail -15
```
Expected: 3 tests PASS.

- [ ] **Step 3: Run full test_fetch_assets.py to ensure no regression**

Run:
```bash
../.venv/bin/python -m pytest test_fetch_assets.py -v 2>&1 | tail -20
```
Expected: all tests PASS (including the original 5 + new 6).

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/video-generate/scripts/fetch_assets.py
git commit -m "feat(fetch_assets): backfill data.media/media_manifest with unified schema"
```

---

## Task 8: Failing test — merge preserves wa-only non-media data fields

**Files:** Modify `.opencode/skills/video-generate/scripts/test_merge_scenes.py`

**Background:** Spec §4.4 says "不得丢失仅存在于 scenes_with_assets.json 的非媒体字段". Current merge code starts from `co_data` and only overwrites `media`/`media_manifest`, so wa-only fields are dropped.

- [ ] **Step 1: Append failing test**

Use Edit tool. Append after the last test in `test_merge_scenes.py`:

```python


def test_merge_preserves_wa_only_non_media_fields(tmp_path):
    """Fields that exist only in scenes_with_assets.json (non-media) must
    survive the merge into scenes_final.json."""
    with_assets = {
        "meta": {"article_title": "T"},
        "audio": {}, "captions": {},
        "scenes": [{
            "id": "s1", "type": "stock_footage",
            "data": {
                "media": [{"file": "a.jpg", "source": "pexels",
                          "source_url": "x", "type": "image",
                          "width": 1, "height": 1, "status": "downloaded"}],
                "media_manifest": [],
                "wa_only_field": "preserve_me",
            },
        }],
    }
    complete = {
        "meta": {"article_title": "T", "total_duration_frames": 100,
                "total_duration_seconds": 3.3},
        "audio": {"voice_file": "v.mp3", "bgm_file": None,
                 "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {},
        "scenes": [{
            "id": "s1", "type": "stock_footage",
            "data": {"co_only_field": "from_complete"},
            "narration": {"text": "Hi", "voice_file": "v.mp3",
                         "voice_start_ms": 0, "voice_end_ms": 100,
                         "timestamps": []},
        }],
    }
    wa_path = tmp_path / "wa.json"
    co_path = tmp_path / "co.json"
    out_path = tmp_path / "final.json"
    wa_path.write_text(json.dumps(with_assets), encoding="utf-8")
    co_path.write_text(json.dumps(complete), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, MERGE_SCRIPT, str(wa_path), str(co_path),
         "--output", str(out_path)],
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, f"stderr: {result.stderr[:500]}"

    final = json.loads(out_path.read_text(encoding="utf-8"))
    data = final["scenes"][0]["data"]
    assert data["co_only_field"] == "from_complete"
    assert data["wa_only_field"] == "preserve_me"
    assert data["media"][0]["file"] == "a.jpg"
```

- [ ] **Step 2: Run test — should FAIL**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_merge_scenes.py -v -k "wa_only" 2>&1 | tail -15
```
Expected: FAIL — `wa_only_field` is missing from merged output.

- [ ] **Step 3: Commit failing test**

```bash
git add .opencode/skills/video-generate/scripts/test_merge_scenes.py
git commit -m "test(merge_scenes): add failing test for wa-only non-media field preservation"
```

---

## Task 9: Implement merge field preservation in `merge_scenes.py`

**Files:** Modify `.opencode/skills/video-generate/scripts/merge_scenes.py`

- [ ] **Step 1: Replace the data-merging block**

Use Edit tool. Find this exact block (lines 64-78):

```python
        # data: media + media_manifest from with_assets; other fields from complete
        wa_data = wa_scene.get("data", {})
        co_data = co_scene.get("data", {})
        merged_data = {}

        # Start with complete's data fields
        merged_data.update(co_data)

        # Overwrite media and media_manifest with with_assets (asset source of truth)
        if "media" in wa_data:
            merged_data["media"] = wa_data["media"]
        if "media_manifest" in wa_data:
            merged_data["media_manifest"] = wa_data["media_manifest"]

        merged_scene["data"] = merged_data
```

Replace with:

```python
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
```

- [ ] **Step 2: Run all merge tests**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_merge_scenes.py -v 2>&1 | tail -15
```
Expected: all 4 tests PASS.

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/merge_scenes.py
git commit -m "fix(merge_scenes): preserve wa-only non-media data fields"
```

---

## Task 10: Update `references/pipeline-dataflow.md` to document new contract

**Files:** Modify `.opencode/skills/video-generate/references/pipeline-dataflow.md`

- [ ] **Step 1: Find merge rule section**

Run: `grep -n "merge\|scenes_final\|media_manifest" .opencode/skills/video-generate/references/pipeline-dataflow.md`
Expected: shows existing references to merge step and scenes_final.json.

- [ ] **Step 2: Add or replace merge rules sub-section**

Use Edit tool. Locate the description of `merge_scenes.py` step (search for "merge_scenes" or "scenes_final.json"). Append (or replace existing rules) with this exact block:

```markdown
### Merge precedence (scenes_final.json)

The merge step combines `scenes_with_assets.json` (asset side) and `scenes_complete.json` (audio side). Per spec §4.4:

| Field | Source |
|---|---|
| `meta` | scenes_complete.json |
| `audio` | scenes_complete.json |
| `captions` | scenes_complete.json (fallback to with_assets if absent) |
| `scenes[i].narration` | scenes_complete.json |
| `scenes[i].data.media` | scenes_with_assets.json |
| `scenes[i].data.media_manifest` | scenes_with_assets.json |
| `scenes[i].data.<other>` | scenes_complete.json wins; wa-only fields are added if not in complete |

`media_manifest` is a Part 1 debug field. Part 2 (Remotion render) consumes `media[]` and may ignore `media_manifest`.
```

- [ ] **Step 3: Verify**

Run: `grep -A 5 "Merge precedence" .opencode/skills/video-generate/references/pipeline-dataflow.md`
Expected: new section present.

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/video-generate/references/pipeline-dataflow.md
git commit -m "docs(pipeline-dataflow): document merge precedence rules"
```

---

## Task 11: Strengthen contract test for full `StockMediaItem` field set

**Files:** Modify `.opencode/skills/video-generate/scripts/test_contract_compliance.py`

**Background:** Current contract test only checks `file`, `source`, `type`. We need it to assert ALL fields in the unified schema (Task 2).

- [ ] **Step 1: Locate the existing media field check**

Run: `grep -n "stock_footage_has_media_list\|StockMediaItem" .opencode/skills/video-generate/scripts/test_contract_compliance.py`
Expected: shows existing test function and any TS interface mentions.

- [ ] **Step 2: Read the test function**

Run: `grep -A 25 "def test_stock_footage_has_media_list" .opencode/skills/video-generate/scripts/test_contract_compliance.py`
Expected: shows current assertions. Note the existing test name and structure.

- [ ] **Step 3: Add a new test for full schema parity**

Use Edit tool. Append at end of file:

```python


def test_media_item_has_all_unified_schema_fields():
    """Every media[] item must carry the full unified schema:
    file, source, source_url, type, width, height, status."""
    from scenes_schema import validate_scenes
    # Build a reference scene with stock footage and a downloaded media item
    scenes = build_reference_scenes_json()  # existing helper
    stock_scene = next(
        (s for s in scenes["scenes"] if s["type"] == "stock_footage"),
        None,
    )
    assert stock_scene is not None, "Reference must have a stock_footage scene"
    # Inject a fully-populated media item
    stock_scene["data"]["media"] = [{
        "file": "assets/test.jpg",
        "source": "pexels",
        "source_url": "https://pexels.com/p/test",
        "type": "image",
        "width": 1920,
        "height": 1080,
        "status": "downloaded",
    }]
    stock_scene["data"]["media_manifest"] = stock_scene["data"]["media"][:]
    # Schema must accept it
    ok, errs = validate_scenes(scenes)
    assert ok, f"validate_scenes failed: {errs}"
    # Field assertion
    item = stock_scene["data"]["media"][0]
    required_fields = {"file", "source", "source_url", "type",
                      "width", "height", "status"}
    assert required_fields.issubset(item.keys()), (
        f"missing fields: {required_fields - set(item.keys())}"
    )
    assert item["status"] in ("downloaded", "failed")


def test_media_manifest_can_contain_failed_items():
    """media_manifest must allow status='failed' items;
    media (downloaded-only) must filter them."""
    from scenes_schema import validate_scenes
    scenes = build_reference_scenes_json()
    stock_scene = next(
        (s for s in scenes["scenes"] if s["type"] == "stock_footage"),
        None,
    )
    stock_scene["data"]["media"] = []  # nothing downloaded
    stock_scene["data"]["media_manifest"] = [{
        "file": "assets/failed.jpg",
        "source": "bing",
        "source_url": "",
        "type": "image",
        "width": 0,
        "height": 0,
        "status": "failed",
    }]
    ok, errs = validate_scenes(scenes)
    assert ok, f"validate_scenes failed: {errs}"
```

- [ ] **Step 4: Run new tests**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_contract_compliance.py -v -k "unified_schema or failed_items" 2>&1 | tail -15
```
Expected: 2 tests PASS.

**NOTE:** `scenes_schema.py`'s `validate_scenes()` does NOT inspect fields inside `media[]` items (verified: `SCENE_DATA_REQUIRED["stock_footage"] = []` and there is no per-media-item validator). So adding `status`, `width`, `height`, `source_url` to media items will NOT trigger schema rejection. If these tests fail, it is a real assertion failure in the test logic — do NOT modify `scenes_schema.py` to "fix" it.

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/scripts/test_contract_compliance.py
git commit -m "test(contract): assert full unified media item schema and failed-status manifest"
```

---

## Task 12: Create `test_docs_cli_alignment.py` to enforce SKILL.md ↔ CLI parity

**Files:** Create `.opencode/skills/video-generate/scripts/test_docs_cli_alignment.py`

**Background:** Spec §6 AC6 ("文档命令与实际 CLI 完全一致") was not auto-verifiable. This new test parses CLI invocations from SKILL.md and validates each flag against argparse.

**NOTE (verified):** Current SKILL.md uses `$VENV_PYTHON $SCRIPTS_DIR/xxx.py` form, NOT `python xxx.py`. The regex below explicitly matches both forms so it works on the existing SKILL.md without forcing a rewrite of every command.

- [ ] **Step 1: Create the test file**

Use Write tool to create `test_docs_cli_alignment.py` with content:

```python
"""Verify CLI command examples in SKILL.md actually match each script's argparse.

Matches both forms used in SKILL.md:
  - $VENV_PYTHON $SCRIPTS_DIR/<name>.py [flags...]
  - python <name>.py [flags...]
  - python scripts/<name>.py [flags...]
"""
import os
import re
import subprocess
import sys
import pytest

SKILL_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Matches:
#   $VENV_PYTHON $SCRIPTS_DIR/foo.py
#   $VENV_PYTHON path/to/foo.py
#   python foo.py
#   python scripts/foo.py
#   python3 foo.py
INVOCATION_RE = re.compile(
    r"(?:\$VENV_PYTHON|python3?)\s+"           # interpreter token
    r"(?:[^\s`]*?/)?"                           # optional path prefix
    r"(\w+\.py)"                                # script name (capture 1)
    r"((?:\s+(?:\\\s*\n\s*)?[^\n`]*)*)",        # everything until end of line/block (capture 2)
    re.MULTILINE,
)


def _extract_python_invocations(md_path):
    """Return a list of (script_name, [flags...]) from SKILL.md."""
    with open(md_path, encoding="utf-8") as f:
        text = f.read()
    invocations = []
    for match in INVOCATION_RE.finditer(text):
        script = match.group(1)
        rest = match.group(2) or ""
        flags = re.findall(r"--[a-zA-Z][a-zA-Z0-9-]*", rest)
        invocations.append((script, flags))
    return invocations


def _get_script_help(script_name):
    """Run script with --help and return stdout+stderr."""
    path = os.path.join(SCRIPTS_DIR, script_name)
    if not os.path.exists(path):
        return ""
    result = subprocess.run(
        [sys.executable, path, "--help"],
        capture_output=True, text=True, timeout=15,
    )
    return result.stdout + result.stderr


def test_skill_md_has_python_invocations():
    """SKILL.md must contain at least one parseable script invocation."""
    invocations = _extract_python_invocations(SKILL_MD)
    assert invocations, (
        "No python invocations parsed from SKILL.md. "
        "Either SKILL.md lacks command examples, or INVOCATION_RE needs an update."
    )
    # Sanity: must mention all four Part 1 scripts at least once
    script_names = {s for s, _ in invocations}
    expected = {"scenes_schema.py", "generate_audio.py",
                "fetch_assets.py", "merge_scenes.py"}
    missing = expected - script_names
    assert not missing, f"SKILL.md missing invocation examples for: {missing}"


def test_skill_md_python_invocations_use_known_flags():
    """Every --flag in a python invocation in SKILL.md must be recognized
    by the corresponding script's argparse."""
    invocations = _extract_python_invocations(SKILL_MD)
    failures = []
    for script, flags in invocations:
        if not flags:
            continue
        help_text = _get_script_help(script)
        if not help_text:
            failures.append(f"{script}: --help failed or script missing")
            continue
        for flag in flags:
            if flag not in help_text:
                failures.append(
                    f"{script}: flag {flag} not in argparse --help"
                )

    assert not failures, "CLI/docs drift:\n" + "\n".join(failures)
```

- [ ] **Step 2: Run the new test**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_docs_cli_alignment.py -v 2>&1 | tail -20
```

Expected outcomes:
- `test_skill_md_has_python_invocations`: PASS (regex finds 4+ invocations across all four scripts)
- `test_skill_md_python_invocations_use_known_flags`: PASS if SKILL.md flags are aligned with argparse. If FAIL, the failure message points to the specific script + flag drift, fixed in Task 14.

Note: `test_skill_md_python_invocations_use_known_flags` may legitimately FAIL at this point if any SKILL.md command uses a flag the script doesn't yet implement. Task 14 ensures alignment.

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/test_docs_cli_alignment.py
git commit -m "test(docs-cli): enforce SKILL.md command examples match argparse"
```

---

## Task 13: Spec amendments — fix BLOCKER ambiguities in design doc

**Files:** Modify `docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md`

**Background:** Address Momus + Metis findings: §4.3 example JSON had two different schemas, §6 AC2 only mentioned stock_footage but §4.3 said "every scene", and AC6/AC7 were not mechanically verifiable.

- [ ] **Step 1: Fix §4.3 example JSON to use unified schema**

Use Edit tool. Find the `media_manifest` example block (around line 97-105):

```json
    "media_manifest": [
      {
        "url": "https://...",
        "file": "assets/s1_00.jpg",
        "source": "pexels",
        "type": "image",
        "status": "downloaded"
      }
    ]
```

Replace with:

```json
    "media_manifest": [
      {
        "file": "assets/s1_00.jpg",
        "source": "pexels",
        "source_url": "https://...",
        "type": "image",
        "width": 1920,
        "height": 1080,
        "status": "downloaded"
      }
    ]
```

(Both arrays now use the same item schema. Authoritative reference: `references/schemas.md` "media[] / media_manifest[] item schema".)

- [ ] **Step 2: Generalize AC2 to all scene types**

Find this acceptance criterion (Section 6, item 2):

```
- `scenes_with_assets.json` 的 stock footage scene 包含 `data.media` 和 `data.media_manifest`。
```

Replace with:

```
- `scenes_with_assets.json` 中**每个 scene** 的 `data` 都包含 `media` 和 `media_manifest` 字段（即使为空数组），与 §4.3 设计一致。Stock footage 类型的 scene 在有可用素材时 `media` 非空。
```

- [ ] **Step 3: Add E2E acceptance criterion (AC8)**

Find Section 6 verification list. Add as new bullet:

```
- 完整管线 `fetch_assets.py` → `generate_audio.py`（mock）→ `merge_scenes.py` 在测试样本上跑通，`scenes_final.json` 通过 `validate_scenes()`（由 `test_e2e_pipeline.py` 验证）。
```

- [ ] **Step 4: Replace AC6 with auto-verifiable form**

Find AC6:

```
- 文档命令与实际 CLI 完全一致。
```

Replace with:

```
- `test_docs_cli_alignment.py` 通过：SKILL.md 中所有 `python ... --flag` 例子都能被对应脚本的 argparse 识别。
```

- [ ] **Step 5: Add MUST-NOT to §3 protecting timestamp logic**

Find Section 3 (非目标). Append as new bullet:

```
- 不修改 `generate_audio.py` 的 `match_scene_timestamps()` 字符位置累加逻辑。该函数对 Edge-TTS 输出与原始文本逐字符对齐有依赖，已知边缘情况（数字念读、标点规范化）由 Part 2 处理。
```

- [ ] **Step 6: Verify spec is internally consistent**

Run:
```bash
grep -n "media_manifest\|stock footage\|every scene\|每个 scene" docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md | head -20
```
Expected: §4.3 example uses unified schema; §6 AC2 says "每个 scene"; AC6 references test_docs_cli_alignment.py.

- [ ] **Step 7: Commit**

```bash
git add docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md
git commit -m "docs(spec): fix §4.3 schema, generalize AC2, replace AC6 with auto-test, add E2E AC8"
```

---

## Task 14: Update `SKILL.md` test count and verify CLI examples

**Files:** Modify `.opencode/skills/video-generate/SKILL.md`

**NOTE (verified):** Current `SKILL.md` (line 72-76) already documents `fetch_assets.py` with `--article-source` and `--outdir` — those examples are ALREADY correct for the new CLI. The main drift is the **test count** advertised on line 112 ("38 tests") and on line 118 ("`test_fetch_assets.py | 7`"), which will change after Tasks 4, 6, 8, 11, 12, 15 add new tests.

- [ ] **Step 1: Confirm fetch_assets example still uses canonical flags**

Run: `grep -n 'fetch_assets\|--outdir\|--article-source\|--assets-dir' .opencode/skills/video-generate/SKILL.md`

Expected: shows `$VENV_PYTHON $SCRIPTS_DIR/fetch_assets.py` with `--article-source` and `--outdir` flags. Should NOT contain `--assets-dir` (deprecated alias is supported in code but not documented).

If `--assets-dir` appears anywhere in SKILL.md, replace those occurrences with `--outdir`.

- [ ] **Step 2: Get current test counts**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest --collect-only -q 2>&1 | tail -5
```
Note total count `T_total`.

Per-file count:
```bash
for f in test_scenes_schema.py test_generate_audio.py test_fetch_assets.py \
         test_merge_scenes.py test_contract_compliance.py \
         test_docs_cli_alignment.py test_e2e_pipeline.py; do
  count=$(../.venv/bin/python -m pytest --collect-only -q "$f" 2>&1 | grep -E "^[0-9]+ tests" | head -1)
  echo "$f: $count"
done
```

Record per-file counts.

- [ ] **Step 3: Update SKILL.md test counts**

Use Edit tool. Find this exact block (around lines 110-121 in current SKILL.md):

```
38 tests across 5 suites (all pass in CI):

| Suite | Tests | Coverage |
|---|---|---|
| `test_scenes_schema.py` | 4 | JSON schema validation |
| `test_generate_audio.py` | 3 | Edge-TTS + timestamp backfill + retry |
| `test_fetch_assets.py` | 7 | 3-layer search + download + URL extraction |
| `test_merge_scenes.py` | 3 | Merge logic + count/ID mismatch errors |
| `test_contract_compliance.py` | 21 | Python↔TypeScript cross-ecosystem contract |
```

Replace with (filling actual numbers from Step 2):

```
<T_total> tests across 7 suites (all pass in CI):

| Suite | Tests | Coverage |
|---|---|---|
| `test_scenes_schema.py` | 4 | JSON schema validation |
| `test_generate_audio.py` | 3 | Edge-TTS + timestamp backfill + retry |
| `test_fetch_assets.py` | <fetch_count> | 3-layer search + download + CLI + data backfill |
| `test_merge_scenes.py` | <merge_count> | Merge logic + count/ID mismatch + wa-only field preservation |
| `test_contract_compliance.py` | <contract_count> | Python↔TypeScript cross-ecosystem contract |
| `test_docs_cli_alignment.py` | 2 | SKILL.md command examples ↔ argparse parity |
| `test_e2e_pipeline.py` | 1 | Fetch → merge → validate end-to-end |
```

Substitute `<T_total>`, `<fetch_count>`, `<merge_count>`, `<contract_count>` with actual values from Step 2.

- [ ] **Step 4: Run docs-CLI alignment test**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_docs_cli_alignment.py -v 2>&1 | tail -10
```
Expected: both tests PASS.

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/SKILL.md
git commit -m "docs(SKILL): sync test count and suite list after hardening"
```

---

## Task 15: Create `test_e2e_pipeline.py` for end-to-end validation

**Files:** Create `.opencode/skills/video-generate/scripts/test_e2e_pipeline.py`

**Background:** Spec AC8 (added in Task 13) requires an E2E test. This wires fetch_assets.py (mocked downloads) → a synthetic scenes_complete.json (skip generate_audio.py since Edge-TTS needs network) → merge_scenes.py → validate_scenes.

- [ ] **Step 1: Create the E2E test file**

Use Write tool to create `test_e2e_pipeline.py`:

```python
"""End-to-end test: fetch_assets.py (mocked) -> synthetic complete -> merge -> validate."""
import json
import os
import subprocess
import sys
from unittest.mock import patch

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
    ok, errs = validate_scenes(final)
    assert ok, f"validate_scenes failed: {errs}"

    # Asserts both scene types backfilled, media defaulted to empty
    title_scene = next(s for s in final["scenes"] if s["type"] == "title_card")
    stock_scene = next(s for s in final["scenes"] if s["type"] == "stock_footage")
    assert title_scene["data"]["title"] == "Hello"  # preserved
    assert title_scene["data"].get("media", []) == []
    assert stock_scene["data"].get("media", []) == []
    assert "media_manifest" in stock_scene["data"]
    # Narration timestamps merged from complete
    assert title_scene["narration"]["voice_end_ms"] == 1000
```

- [ ] **Step 2: Run E2E test**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_e2e_pipeline.py -v 2>&1 | tail -15
```
Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/test_e2e_pipeline.py
git commit -m "test(e2e): add fetch -> merge -> validate end-to-end pipeline test"
```

---

## Task 16: Final whitespace & line-ending cleanup on touched Part 1 files

**Files:** All files touched in Tasks 1-15

**Background:** Spec acceptance criterion: `git diff --check` must not report CRLF or trailing-whitespace problems on Part 1 files.

- [ ] **Step 1: Determine the diff base**

The default base is `origin/feat/video-scaffold`. Verify it exists:

```bash
git fetch origin
git rev-parse --verify origin/feat/video-scaffold 2>&1 | head -1
```

- If output is a SHA (40 hex chars): use `BASE=origin/feat/video-scaffold`.
- If `unknown revision`: fall back to the merge-base of the current branch with the most recent default branch:
  ```bash
  BASE=$(git merge-base HEAD $(git symbolic-ref refs/remotes/origin/HEAD --short 2>/dev/null || echo "main"))
  echo "Using BASE=$BASE"
  ```
  If neither works, set `BASE=$(git rev-parse HEAD~10)` as a last-resort relative reference covering recent commits.

Export `BASE` for the rest of this task.

- [ ] **Step 2: Run `git diff --check` against the chosen base**

Run:
```bash
git diff --check "$BASE"...HEAD -- \
  .opencode/skills/video-generate/ \
  docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md
```

Expected: NO output (clean). If there is output, note each file and line.

- [ ] **Step 3: For any reported file, strip trailing whitespace and fix CRLF**

For each file flagged in Step 2:

```bash
# macOS sed — strip trailing whitespace
sed -i '' -E 's/[[:space:]]+$//' <flagged-file>

# Convert CRLF -> LF if needed
perl -i -pe 's/\r\n/\n/g' <flagged-file>
```

- [ ] **Step 4: Re-run check**

```bash
git diff --check "$BASE"...HEAD -- \
  .opencode/skills/video-generate/ \
  docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md
```
Expected: clean.

- [ ] **Step 5: Commit cleanup if anything changed**

```bash
git status
# if dirty:
git add -u .opencode/skills/video-generate/ docs/superpowers/specs/2026-06-19-video-part1-hardening-design.md
git commit -m "chore: normalize line endings and strip trailing whitespace on Part 1 files"
```

---

## Task 17: Full pytest pass and acceptance verification

**Files:** None (verification only)

- [ ] **Step 1: Run full Part 1 test suite**

Run:
```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest -v 2>&1 | tail -30
```
Expected: ALL tests PASS (baseline + new tests from Tasks 4, 6, 8, 11, 12, 15).

- [ ] **Step 2: Verify all spec acceptance criteria**

Walk through each spec §6 acceptance criterion and confirm:

```bash
# AC1: fetch_assets.py CLI runs (--offline keeps test deterministic and offline)
echo '{"meta":{"article_title":"T","article_source":"","output":"o.mp4","aspect_ratio":"16:9","width":1920,"height":1080,"fps":30,"total_duration_frames":30,"total_duration_seconds":1,"font_family":"s","color_theme":{"primary":"#000","accent":"#f00","text":"#fff","background":"#000"}},"scenes":[],"audio":{"voice_file":"v.mp3","bgm_file":null,"bgm_volume":0.15,"voice_volume":0.9},"captions":{"enabled":false,"style":"minimal","font_size":36,"position_y":920,"active_color":"#fff","inactive_color":"#888"}}' > /tmp/scenes.json
PEXELS_API_KEY="" PIXABAY_API_KEY="" UNSPLASH_ACCESS_KEY="" \
  python .opencode/skills/video-generate/scripts/fetch_assets.py /tmp/scenes.json --outdir /tmp/assets --offline
ls /tmp/assets/manifest.json /tmp/scenes_with_assets.json
# Expected: both files exist
```

```bash
# AC4: pytest pass
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest -v 2>&1 | tail -3
# Expected: all PASS
```

```bash
# AC5: git diff --check clean (use BASE chosen in Task 16 Step 1)
git diff --check "$BASE"...HEAD -- .opencode/skills/video-generate/
# Expected: no output
```

```bash
# AC6: docs-CLI alignment test
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest test_docs_cli_alignment.py -v
# Expected: PASS
```

```bash
# AC8 (newly added): E2E pipeline test
../.venv/bin/python -m pytest test_e2e_pipeline.py -v
# Expected: PASS
```

- [ ] **Step 3: Confirm out-of-scope items NOT touched**

Run:
```bash
git diff --stat "$BASE"...HEAD | grep -E "(Composition|render_video|commands/video)" || echo "OK: no Part 2 files touched"
```
Expected: `OK: no Part 2 files touched`.

```bash
# Verify match_scene_timestamps function body is unchanged.
# Strategy: extract the function body from BASE and HEAD, compare.
git show "$BASE":.opencode/skills/video-generate/scripts/generate_audio.py 2>/dev/null \
  | awk '/^def match_scene_timestamps/,/^def [^m]/' > /tmp/match_base.py
awk '/^def match_scene_timestamps/,/^def [^m]/' \
  .opencode/skills/video-generate/scripts/generate_audio.py > /tmp/match_head.py
if diff -q /tmp/match_base.py /tmp/match_head.py >/dev/null 2>&1; then
  echo "OK: match_scene_timestamps body unchanged"
else
  echo "FAIL: match_scene_timestamps was modified — out of scope per spec §3"
  diff -u /tmp/match_base.py /tmp/match_head.py | head -40
  exit 1
fi
```
Expected: `OK: match_scene_timestamps body unchanged`.

- [ ] **Step 4: Final summary**

Print a one-line completion message and the list of new tests added:

```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest --collect-only -q 2>&1 | tail -3
git log --oneline "$BASE"..HEAD
```

Expected: clean test count, list of all hardening commits visible.

---

## Self-Review

This section was completed by the plan author before delivery.

**1. Spec coverage check:**

| Spec section | Task(s) implementing it |
|---|---|
| §2 goal 1 (CLI runnable) | Tasks 4, 5 |
| §2 goal 2 (asset backfill) | Tasks 6, 7 |
| §2 goal 3 (merge keeps both) | Task 9 + existing test_merge_scenes |
| §2 goal 4 (docs ↔ CLI) | Tasks 12, 14 |
| §2 goal 5 (tests pass) | Task 17 |
| §2 goal 6 (whitespace clean) | Task 16 |
| §3 non-goals (no Part 2) | Task 17 step 3 |
| §4.2 CLI contract | Task 5 |
| §4.3 schema | Tasks 2, 6, 7 (unified schema) |
| §4.4 merge rules | Tasks 9, 10 |
| §4.5 documentation | Tasks 10, 14 |
| §5.1 test list | Tasks 4, 6, 8, 11, 12, 15 |
| §6 acceptance criteria | Task 17 |
| §7 risks | Mitigated in §3 of design (Task 13 amendment) |

**2. Placeholder scan:** No "TBD", "TODO", or "implement later" present. All code blocks contain executable code.

**3. Type consistency:**
- `media[]` item field set: `file`, `source`, `source_url`, `type`, `width`, `height`, `status` — consistent across schemas.md (Task 2), input-props.ts `StockMediaItem` (Task 3), `_normalize_asset()` (Task 7), contract test (Task 11).
- CLI flags: `--outdir` canonical, `--assets-dir` alias, `--article-source` — consistent across argparse (Task 5), tests (Task 4), SKILL.md (Task 14), docs-CLI test (Task 12).
- Merge precedence: complete wins for shared, wa-only non-media added — consistent in code (Task 9), test (Task 8), references (Task 10).

**4. BLOCKER findings from review addressed:**
- BLOCKER 1 (schema mismatch in §4.3) → Task 2 (schemas.md) + Task 13 step 1 (spec amendment)
- BLOCKER 2 (AC2 too narrow) → Task 13 step 2 + Task 15 covers both scene types

**5. Open assumptions explicitly documented:**
- `meta.article_source` is interpreted relative to CWD (project root in normal use). Not enforced by absolute path.
- `download_file()` validity check remains "size > 100 bytes" — not strengthened (out-of-scope; flagged in design risk table).
- Edge-TTS character-position alignment is locked behind §3 non-goal (Task 13 step 5).

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-06-19-video-part1-hardening.md`.**

Two execution options:

**1. Subagent-Driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration. Best for plans with many independent tasks like this one.

**2. Inline Execution** — Execute tasks in this session using `superpowers:executing-plans`, batch execution with checkpoints for review.

Which approach?
