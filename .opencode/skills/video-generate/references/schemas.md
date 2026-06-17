# scenes.json Schema Reference

Python validator: `scripts/scenes_schema.py`
TypeScript types: `remotion/src/input-props.ts`
Contract test: `scripts/test_contract_compliance.py` (21 assertions bridging both ecosystems)

## Top-level structure

```json
{
  "meta": { ... },
  "scenes": [ ... ],
  "audio": { ... },
  "captions": { ... }
}
```

## meta

| Field | Type | Required | Notes |
|---|---|---|---|
| `article_title` | string | ✅ | Source article title |
| `article_source` | string | ✅ | Source markdown path |
| `output` | string | ✅ | Output MP4 path |
| `aspect_ratio` | string | ✅ | `"16:9"` |
| `width` | number | ✅ | `1920` |
| `height` | number | ✅ | `1080` |
| `fps` | number | ✅ | `30` |
| `total_duration_frames` | number | ✅ | Backfilled by audio stage |
| `total_duration_seconds` | number | ✅ | Backfilled by audio stage |
| `total_duration_ms` | number | ❌ | Backfilled (audio precision) |
| `font_family` | string | ✅ | e.g. `"sans-serif"` |
| `color_theme` | object | ✅ | `{primary, accent, text, background}` |

## scenes[] (each element)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | ✅ | Unique, e.g. `"s1"`, `"s2"` |
| `type` | enum | ✅ | One of: `title_card`, `chapter_title`, `stock_footage`, `info_card`, `code_block`, `outro` |
| `duration_frames` | number | ✅ | Positive; floored at 30 frames |
| `search_keywords` | object | ✅ | `{zh: string[], en: string[]}` — both keys required |
| `data` | object | ✅ | Type-specific (table below) |
| `animation` | object | ❌ | See animation types below |
| `narration` | object | ✅ | See narration below |

### data fields by scene type

| type | Required `data` fields | Optional |
|---|---|---|
| `title_card` | `title` | `subtitle`, `background` |
| `chapter_title` | `chapter_number`, `title` | `subtitle` |
| `stock_footage` | — | `media[]`, `media_manifest[]`, `text_overlays[]` |
| `info_card` | `layout` | `columns[]`, `items[]`, `quote`, `quote_source` |
| `code_block` | `code` | `language`, `title` |
| `outro` | `cta_text` | `logo` |

### narration

| Field | Type | Required | Backfilled |
|---|---|---|---|
| `text` | string | ✅ | — |
| `voice_file` | string | ✅ | — |
| `voice_start_ms` | number | ✅* | ✅ by audio stage |
| `voice_end_ms` | number | ✅* | ✅ by audio stage |
| `timestamps` | array | ✅* | ✅ by audio stage |

\* Required in TypeScript type as optional (pre-backfill JSON is valid).

### timestamps[] (word-level)

| Field | Type |
|---|---|
| `word` | string |
| `start_ms` | number |
| `end_ms` | number |

## audio

| Field | Type | Notes |
|---|---|---|
| `voice_file` | string | e.g. `"voice.mp3"` |
| `bgm_file` | string \| null | Background music path, or `null` |
| `bgm_volume` | number | 0.0–1.0, typical `0.15` |
| `voice_volume` | number | 0.0–1.0, typical `0.9` |

## captions

| Field | Type | Notes |
|---|---|---|
| `enabled` | boolean | |
| `style` | enum | `karaoke`, `minimal`, `bold` |
| `font_size` | number | typical `36` |
| `position_y` | number | vertical offset, typical `920` |
| `active_color` | string | color code |
| `inactive_color` | string | color code |

## Animation types

Optional per scene. If present, `type` is required inside the animation object.

| type | Visual |
|---|---|
| `ken_burns` | Slow zoom + pan (documentary style) |
| `spring` | Physics-based spring motion |
| `fade_in` | Opacity 0 → 1 |
| `fade_out` | Opacity 1 → 0 |
| `slide_in` | Horizontal/vertical slide |
| `stagger_reveal` | Items appear sequentially |
| `typewriter` | Characters appear one by one |
| `scale_in` | Zoom from small to full size |

## Minimal valid example

```json
{
  "meta": {
    "article_title": "Example", "article_source": "ex.md",
    "output": "ex.mp4", "aspect_ratio": "16:9",
    "width": 1920, "height": 1080, "fps": 30,
    "total_duration_frames": 150, "total_duration_seconds": 5,
    "font_family": "sans-serif",
    "color_theme": {"primary": "#1a1a2e", "accent": "#e94560", "text": "#fff", "background": "#000"}
  },
  "scenes": [{
    "id": "s1", "type": "title_card", "duration_frames": 150,
    "search_keywords": {"zh": ["标题"], "en": ["title"]},
    "data": {"title": "My Video"},
    "narration": {"text": "Welcome", "voice_file": "voice.mp3",
                  "voice_start_ms": 0, "voice_end_ms": 0, "timestamps": []}
  }],
  "audio": {"voice_file": "voice.mp3", "bgm_file": null, "bgm_volume": 0.15, "voice_volume": 0.9},
  "captions": {"enabled": true, "style": "karaoke", "font_size": 36,
               "position_y": 920, "active_color": "#fff", "inactive_color": "#888"}
}
```

See `test_contract_compliance.py::build_reference_scenes_json()` for a full 6-scene reference covering every type.
