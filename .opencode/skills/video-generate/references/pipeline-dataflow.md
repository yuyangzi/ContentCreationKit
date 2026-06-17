# Pipeline Data Flow

Four JSON artifacts, each produced by a distinct stage. Naming is deliberately distinct to prevent confusion.

```
scenes.json                  ← LLM / Agent generates (input)
  │
  ├──► scenes_complete.json  ← generate_audio.py  (timestamps added, duration computed)
  │
  ├──► scenes_with_assets.json ← fetch_assets.py  (media paths + manifest added)
  │
  └──► scenes_final.json     ← merge_scenes.py   (combines both — feed to Remotion)
```

## Stage 1: scenes.json (Input)

**Producer**: LLM Agent (from spec `docs/superpowers/specs/2026-06-16-article-to-video-design.md`)
**Consumer**: `generate_audio.py`, `fetch_assets.py` (both read independently)
**Validation**: `scripts/scenes_schema.py`

Contains scene structure, narration text (no timestamps yet), and metadata. `narration.voice_start_ms` / `voice_end_ms` / `timestamps` are placeholder zeros.

## Stage 2a: scenes_complete.json (Audio)

**Producer**: `generate_audio.py`
**Consumer**: `merge_scenes.py`

Deltas vs input `scenes.json`:
- `scenes[].narration.voice_start_ms` — from SRT parsing
- `scenes[].narration.voice_end_ms` — from SRT parsing
- `scenes[].narration.timestamps[]` — word-level timestamps
- `scenes[].duration_frames` — redistributed proportionally by narration char length, floored at 30 frames
- `meta.total_duration_ms` — from last SRT entry
- `meta.total_duration_seconds` — rounded
- `meta.total_duration_frames` — derived from ms + fps

Side outputs: `voice.mp3` (concatenated audio), `timestamps.json` (word-level), temp SRT (deleted).

## Stage 2b: scenes_with_assets.json (Assets)

**Producer**: `fetch_assets.py`
**Consumer**: `merge_scenes.py`

Deltas vs input `scenes.json`:
- `scenes[].data.media[]` — list of `{file, source, source_url, type, width, height, status}` (only `status == "downloaded"` entries)
- `scenes[].data.media_manifest[]` — full list including failed downloads

Side outputs: `assets/` directory (downloaded files), `manifest.json` (per-scene summary + stats).

## Stage 3: scenes_final.json (Merged)

**Producer**: `merge_scenes.py`
**Consumer**: Remotion renderer (Part 2)

Merge rules per scene:
| Field | Source |
|---|---|
| `meta`, `audio`, `captions` | `scenes_complete.json` (audio is source of truth for duration) |
| `narration.*` (text, voice_file, timestamps, voice_start/end_ms) | `scenes_complete.json` |
| `data.media`, `data.media_manifest` | `scenes_with_assets.json` |
| `id`, `type`, `duration_frames`, `search_keywords`, `animation`, other `data` fields | `scenes_complete.json` |

Validation: scene counts must match; scene IDs must match in order. Exit 1 with descriptive stderr on mismatch.

## Why merge is mandatory

`generate_audio.py` reads `scenes.json` (no assets). `fetch_assets.py` reads `scenes.json` (no timestamps). Neither sees the other's output. Without merge, the renderer gets timestamps but no media paths → `stock_footage` scenes render as empty gradients.
