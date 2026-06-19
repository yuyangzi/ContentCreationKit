---
name: video-generate
description: Convert Markdown articles into 16:9 MP4 videos via scene generation, 3-layer asset search, Edge-TTS audio, and Remotion rendering. Use when user wants to create a video from an article, turn written content into video, generate a video narration, or run the article-to-video pipeline. Triggers on phrases like "生成视频", "转成视频", "create video from article", "article to video", "视频化这篇文章", "把文章做成视频".
---

# Video Generate

Article → 16:9 MP4 video pipeline via Agent-driven scene scripting → 3-layer asset search → Edge-TTS audio → Remotion rendering. Python prepares data; Remotion renders.

## Pipeline Overview

5 sequential stages (stages 3a/3b run in parallel):

```
1. LLM Scene Analysis  → scenes.json
2. Schema Validation   → (validate, fail-fast)
3a. TTS Audio          → voice.mp3 + timestamps → scenes_complete.json
3b. Asset Search       → downloaded media      → scenes_with_assets.json
4. Merge               → scenes_final.json (combines audio + assets)
5. Render              → output.mp4 (Remotion, Part 2)
```

For JSON structure at each stage, see [references/pipeline-dataflow.md](references/pipeline-dataflow.md).

## Prerequisites

### Python venv (required)

```bash
cd .opencode/skills/video-generate
python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

### System packages (for newspaper3k / lxml)

- Ubuntu/Debian: `sudo apt install libxml2-dev libxslt1-dev`
- macOS: `brew install libxml2 libxslt`

### API keys (optional, for stock asset search)

See [references/api-config.md](references/api-config.md) for full list and where to get each key. No API keys needed for Edge-TTS audio.

## Running Scripts

All scripts live in `.opencode/skills/video-generate/scripts/`. Invoke from the skill's venv:

```bash
VENV_PYTHON=.opencode/skills/video-generate/.venv/bin/python
SCRIPTS_DIR=.opencode/skills/video-generate/scripts
```

### Validate a scenes.json

```bash
$VENV_PYTHON $SCRIPTS_DIR/scenes_schema.py content/video/my-video/scenes.json
```

### Generate TTS audio (Stage 3a)

```bash
$VENV_PYTHON $SCRIPTS_DIR/generate_audio.py \
  content/video/my-video/scenes.json \
  --outdir content/video/my-video \
  --voice zh-CN-XiaoxiaoNeural
```

Output: `voice.mp3`, `timestamps.json`, `scenes_complete.json`

### Fetch assets (Stage 3b)

```bash
$VENV_PYTHON $SCRIPTS_DIR/fetch_assets.py \
  content/video/my-video/scenes.json \
  --article-source content/article/my-article.md \
  --outdir content/video/my-video/assets
```

Output: `assets/` directory, `manifest.json`, `scenes_with_assets.json`

### Merge audio + assets (Stage 4)

```bash
$VENV_PYTHON $SCRIPTS_DIR/merge_scenes.py \
  content/video/my-video/scenes_with_assets.json \
  content/video/my-video/scenes_complete.json \
  --output content/video/my-video/scenes_final.json
```

### Run all tests

```bash
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest -v
```

## Scene Types

6 types, each with specific `data` field requirements:

| Type | Required `data` fields | Typical use |
|------|----------------------|-------------|
| `title_card` | `title` | Opening title |
| `chapter_title` | `chapter_number`, `title` | Chapter dividers |
| `stock_footage` | — | B-roll + overlays |
| `info_card` | `layout` | Bullet lists, tables, quotes |
| `code_block` | `code` | Code demonstrations |
| `outro` | `cta_text` | Closing call-to-action |

For full field spec, animation types, caption styles: [references/schemas.md](references/schemas.md).

## Tests

50 tests across 7 suites (all pass in CI):

| Suite | Tests | Coverage |
|---|---|---|
| `test_scenes_schema.py` | 4 | JSON schema validation |
| `test_generate_audio.py` | 3 | Edge-TTS + timestamp backfill + retry |
| `test_fetch_assets.py` | 13 | 3-layer search + download + CLI + data backfill |
| `test_merge_scenes.py` | 4 | Merge logic + count/ID mismatch + wa-only field preservation |
| `test_contract_compliance.py` | 23 | Python↔TypeScript cross-ecosystem contract |
| `test_docs_cli_alignment.py` | 2 | SKILL.md command examples ↔ argparse parity |
| `test_e2e_pipeline.py` | 1 | Fetch → merge → validate end-to-end |

## Common Pitfalls

- **Edge-TTS v7.2.8 API**: Uses `SubMaker.feed(chunk)` + `get_srt()` (not `create_sub`/`generate_subs`). `Communicate(..., boundary="WordBoundary")` is required.
- **Python path**: Scripts rely on sibling imports (`from scenes_schema import ...`). Always invoke via venv from project root, or `cd scripts/` before running pytest.
- **Merge is mandatory**: `generate_audio.py` and `fetch_assets.py` independently read the original `scenes.json`. Skipping merge → `scenes_complete.json` has empty `data.media` arrays.

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ModuleNotFoundError: lxml` | Missing system libxml2 headers | Install system packages above |
| `edge-tts not available` | venv not activated or pip install incomplete | Re-run `pip install -r requirements.txt` in `.venv` |
| `search_all_layers` warns ZERO results | No API keys set + Bing blocked | Set env keys from [references/api-config.md](references/api-config.md) |
| SRT parsing returns 0 entries | Edge-TTS non-standard timestamp format | Check stderr warning; audio still valid |
