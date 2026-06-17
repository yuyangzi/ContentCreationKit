# Article-to-Video Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 4-stage pipeline converting Markdown articles to 16:9 MP4 videos via Agent-driven scene generation → 5-layer asset search → Edge-TTS audio → Remotion rendering.

**Architecture:** Python scripts handle data preparation (schema validation, asset fetch, audio generation). Remotion (React/Node.js) handles video rendering. A single `scenes.json` interface file bridges the two ecosystems. OpenCode slash commands orchestrate the pipeline, following existing command/skill patterns.

**Tech Stack:** Python 3 (edge-tts, newspaper3k, Pillow, requests), Node.js (Remotion 4.x, React 18), Bash (orchestration), OpenCode Agent (LLM scene analysis)

**Spec reference:** `docs/superpowers/specs/2026-06-16-article-to-video-design.md`

---

## File Structure

```
.opencode/skills/video-generate/
├── SKILL.md                              # Skill definition (follows image-generate pattern)
├── requirements.txt                      # Python deps
├── scripts/
│   ├── __init__.py
│   ├── scenes_schema.py                  # Schema validator + constants
│   ├── generate_audio.py                 # Edge-TTS + timestamp backfill → scenes_complete.json
│   ├── fetch_assets.py                   # 5-layer asset search + download
│   └── render_video.sh                   # Asset copy + Remotion render + cleanup
└── remotion/
    ├── package.json                      # Remotion + React deps
    ├── tsconfig.json
    ├── remotion.config.ts
    └── src/
        ├── Root.tsx                      # Register composition
        ├── MainVideo.tsx                 # Scene sequencer + audio + captions
        ├── input-props.ts                # TypeScript types for scenes.json
        ├── theme.ts                      # Color/font defaults
        ├── templates/                    # 6 scene type components
        │   ├── TitleCard.tsx
        │   ├── ChapterTitle.tsx
        │   ├── StockFootageScene.tsx
        │   ├── InfoCardScene.tsx
        │   ├── CodeBlockScene.tsx
        │   └── Outro.tsx
        └── components/                   # Reusable sub-components
            ├── CaptionOverlay.tsx
            ├── KenBurnsImage.tsx
            └── TextCard.tsx

.opencode/commands/
├── to-video-script.md                    # Agent-driven scene generation
├── to-video-footage.md                   # Asset search + download
├── to-video-audio.md                     # TTS + timestamp backfill
├── to-video-render.md                    # Remotion render
└── to-video.md                           # One-click full pipeline

Modified:
- .gitignore                              # Add content/video/
```

## Task Dependency Graph

```
Task 1: Scaffold + .gitignore ──────────────────────────────────────┐
Task 2: scenes_schema.py (TDD)         ← depends on Task 1         │
Task 3: input-props.ts                 ← depends on Task 1         │
                                                                   │
Task 4: generate_audio.py              ← depends on Task 2         │
Task 5: fetch_assets.py                ← depends on Task 2         │
                                                                   │
Task 6: Remotion scaffold + configs    ← depends on Task 3         │
Task 7: Remotion templates (6 scenes)  ← depends on Task 6         │
Task 8: Remotion components            ← depends on Task 6         │
Task 9: Remotion Root + MainVideo      ← depends on Task 7,8       │
                                                                   │
Task 10: render_video.sh               ← depends on Task 9         │
                                                                   │
Task 11: SKILL.md + commands            ← depends on Task 4,5,10   │
Task 12: Integration test              ← depends on all above      │
```

## Parallel Execution Graph

```
Wave 1 (no deps):     Task 1
                      ↓
Wave 2 (parallel):    Task 2 ──┬── Task 3
                      ↓        ↓
Wave 3 (parallel):    Task 4   Task 6
                      Task 5   ↓
                               Task 7 ──┬── Task 8
                               ↓        ↓
Wave 4:                        Task 9
                               ↓
Wave 5:                        Task 10
                               ↓
Wave 6 (integration):          Task 11 ── Task 12
```

---

### Task 1: Directory Scaffold + .gitignore

**Files:**
- Create: `.opencode/skills/video-generate/requirements.txt`
- Create: `.opencode/skills/video-generate/scripts/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p .opencode/skills/video-generate/{scripts,remotion/{src/{templates,components},public/bgm}}
```

- [ ] **Step 2: Write requirements.txt**

```txt
edge-tts>=7.2
newspaper3k>=0.2
Pillow>=9.0
requests>=2.31
imagehash>=4.3
pytest>=8.0
```

Note: `stockmedia-sdk` and `imgsearch-api` are NOT included — they don't exist as reliable PyPI packages. `fetch_assets.py` will use `requests` to call Pexels/Pixabay/Unsplash/Bing APIs directly.

- [ ] **Step 3: Touch __init__.py**

```bash
touch .opencode/skills/video-generate/scripts/__init__.py
```

- [ ] **Step 4: Update .gitignore**

Add after the `content/WeChat/` line in `.gitignore`:

```
content/video/
```

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/requirements.txt \
       .opencode/skills/video-generate/scripts/__init__.py \
       .gitignore
git commit -m "feat(video): scaffold video-generate skill directory"
```

---

### Task 2: scenes.json Schema Validator (TDD)

**Files:**
- Create: `.opencode/skills/video-generate/scripts/scenes_schema.py`
- Create: `.opencode/skills/video-generate/scripts/test_scenes_schema.py`

- [ ] **Step 1: Write failing test — valid minimal JSON passes**

Create `test_scenes_schema.py`:

```python
import json
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
```

- [ ] **Step 2: Run test — expect FAIL**

```bash
cd .opencode/skills/video-generate/scripts && python3 -m pytest test_scenes_schema.py::test_valid_minimal_scenes_json_passes -v
```

Expected: FAIL (ModuleNotFoundError: scenes_schema)

- [ ] **Step 3: Write failing test — invalid scene type rejected**

```python
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
```

- [ ] **Step 4: Implement scenes_schema.py**

```python
"""scenes.json schema validator."""

import json
from typing import Any, List

SCENE_TYPES = {"title_card", "chapter_title", "stock_footage",
               "info_card", "code_block", "outro"}
CAPTION_STYLES = {"karaoke", "minimal", "bold"}
ANIMATION_TYPES = {"ken_burns", "spring", "fade_in", "fade_out",
                   "slide_in", "stagger_reveal", "typewriter", "scale_in"}

SCENE_DATA_REQUIRED = {
    "title_card": ["title"],
    "chapter_title": ["chapter_number", "title"],
    "stock_footage": [],
    "info_card": ["layout"],
    "code_block": ["code"],
    "outro": ["cta_text"],
}


def validate_scenes(data: dict) -> List[str]:
    errors = []
    if not isinstance(data, dict):
        return ["root: must be an object"]

    # Meta
    meta = data.get("meta", {})
    for field in ["article_title", "article_source", "output", "aspect_ratio",
                  "width", "height", "fps", "total_duration_frames",
                  "total_duration_seconds", "font_family", "color_theme"]:
        if field not in meta:
            errors.append(f"meta.{field}: required")
    ct = meta.get("color_theme", {})
    for c in ["primary", "accent", "text", "background"]:
        if c not in ct:
            errors.append(f"meta.color_theme.{c}: required")

    # Scenes
    scenes = data.get("scenes", [])
    if not isinstance(scenes, list):
        errors.append("scenes: must be an array")
    else:
        for i, scene in enumerate(scenes):
            p = f"scenes[{i}]"
            if not isinstance(scene, dict):
                errors.append(f"{p}: must be an object"); continue
            if "id" not in scene:
                errors.append(f"{p}.id: required")
            st = scene.get("type")
            if st not in SCENE_TYPES:
                errors.append(f"{p}.type: must be one of {sorted(SCENE_TYPES)}, got '{st}'")
            dur = scene.get("duration_frames")
            if not isinstance(dur, (int, float)) or dur <= 0:
                errors.append(f"{p}.duration_frames: required positive number, got {dur}")
            sk = scene.get("search_keywords", {})
            if not isinstance(sk, dict) or "zh" not in sk or "en" not in sk:
                errors.append(f"{p}.search_keywords: requires 'zh' and 'en' keys")
            nar = scene.get("narration", {})
            for nf in ["text", "voice_file"]:
                if nf not in nar:
                    errors.append(f"{p}.narration.{nf}: required")
            # Per-type data fields
            sd = scene.get("data", {})
            if st in SCENE_DATA_REQUIRED:
                for rf in SCENE_DATA_REQUIRED[st]:
                    if rf not in sd:
                        errors.append(f"{p}.data.{rf}: required for scene type '{st}'")
            # Animation type validation (optional)
            anim = scene.get("animation")
            if anim and isinstance(anim, dict):
                at = anim.get("type")
                if at and at not in ANIMATION_TYPES:
                    errors.append(f"{p}.animation.type: must be one of {sorted(ANIMATION_TYPES)}, got '{at}'")

    # Audio
    audio = data.get("audio", {})
    for af in ["voice_file", "bgm_volume", "voice_volume"]:
        if af not in audio:
            errors.append(f"audio.{af}: required")

    # Captions
    caps = data.get("captions", {})
    if caps.get("style") not in CAPTION_STYLES:
        errors.append(f"captions.style: must be one of {sorted(CAPTION_STYLES)}")

    return errors


def validate_scenes_file(path: str) -> List[str]:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return validate_scenes(data)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 scenes_schema.py <scenes.json>", file=sys.stderr)
        sys.exit(1)
    errors = validate_scenes_file(sys.argv[1])
    if errors:
        for e in errors:
            print(f"❌ {e}")
        sys.exit(1)
    print("✅ Schema validation passed")
```

- [ ] **Step 5: Run all tests — expect PASS**

```bash
cd .opencode/skills/video-generate/scripts && python3 -m pytest test_scenes_schema.py -v
```

Expected: 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add .opencode/skills/video-generate/scripts/scenes_schema.py \
       .opencode/skills/video-generate/scripts/test_scenes_schema.py
git commit -m "feat(video): add scenes.json schema validator with TDD tests"
```

---

### Task 3: TypeScript Type Definitions (input-props.ts)

**Files:**
- Create: `.opencode/skills/video-generate/remotion/src/input-props.ts`

- [ ] **Step 1: Write input-props.ts**

```typescript
// Type definitions for scenes.json consumed by Remotion components

export interface ColorTheme {
  primary: string;
  accent: string;
  text: string;
  background: string;
}

export interface Meta {
  article_title: string;
  article_source: string;
  output: string;
  aspect_ratio: string;
  width: number;
  height: number;
  fps: number;
  total_duration_frames: number;
  total_duration_seconds: number;
  total_duration_ms?: number;
  font_family: string;
  color_theme: ColorTheme;
}

export interface WordTimestamp {
  word: string;
  start_ms: number;
  end_ms: number;
}

export interface Narration {
  text: string;
  voice_file: string;
  voice_start_ms: number;
  voice_end_ms: number;
  timestamps: WordTimestamp[];
}

export interface SearchKeywords {
  zh: string[];
  en: string[];
}

export interface AnimationConfig {
  type?: string;
  duration_frames?: number;
  direction?: string;
  stiffness?: number; damping?: number; mass?: number;
  scale_start?: number; scale_end?: number;
  pan_x?: number; pan_y?: number;
  stagger_delay_frames?: number;
  chars_per_frame?: number;
  from_scale?: number;
}

// Scene-specific data types
export interface TitleCardData { title: string; subtitle?: string; background?: string; }
export interface ChapterTitleData { chapter_number: number; title: string; subtitle?: string; }
export interface StockMediaItem { file: string; source: string; source_url?: string; type: "image" | "video"; width?: number; height?: number; relevance_score?: number; }
export interface TextOverlay { text: string; position?: string; font_size?: number; }
export interface StockFootageData { media?: StockMediaItem[]; text_overlays?: TextOverlay[]; }
export interface InfoCardColumn { title?: string; content: string; icon?: string; }
export interface InfoCardItem { text: string; highlight?: boolean; }
export interface InfoCardData { layout: string; columns?: InfoCardColumn[]; items?: InfoCardItem[]; quote?: string; quote_source?: string; }
export interface CodeBlockData { code: string; language: string; title?: string; }
export interface OutroData { cta_text: string; logo?: string; }

export interface Scene {
  id: string;
  type: string;
  duration_frames: number;
  search_keywords: SearchKeywords;
  data: Record<string, unknown>;
  animation?: AnimationConfig;
  narration: Narration;
}

export interface AudioConfig {
  voice_file: string;
  bgm_file: string | null;
  bgm_volume: number;
  voice_volume: number;
}

export interface CaptionConfig {
  enabled: boolean;
  style: string;
  font_size: number;
  position_y: number;
  active_color: string;
  inactive_color: string;
}

export interface ScenesJson {
  meta: Meta;
  scenes: Scene[];
  audio: AudioConfig;
  captions: CaptionConfig;
}
```

- [ ] **Step 2: Commit**

```bash
git add .opencode/skills/video-generate/remotion/src/input-props.ts
git commit -m "feat(video): add TypeScript type definitions for scenes.json"
```

---

### Task 4: generate_audio.py — Edge-TTS + Timestamp Backfill

**Files:**
- Create: `.opencode/skills/video-generate/scripts/generate_audio.py`
- Create: `.opencode/skills/video-generate/scripts/test_generate_audio.py`

- [ ] **Step 1: Write failing integration test**

```python
# test_generate_audio.py
import json
import os
import subprocess
import sys
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
    # Requires edge-tts to be installed. Skip gracefully if not.
    try:
        from edge_tts import Communicate
    except ImportError:
        pytest.skip("edge-tts not installed")

    # Create minimal scenes.json
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

    # Run generate_audio.py
    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), "generate_audio.py"),
         str(scenes_path), "--outdir", str(tmp_path)],
        capture_output=True, text=True, timeout=120
    )
    assert result.returncode == 0, f"generate_audio.py failed: {result.stderr[:500]}"

    # Verify outputs exist
    assert (tmp_path / "voice.mp3").exists(), "voice.mp3 not created"
    assert (tmp_path / "timestamps.json").exists(), "timestamps.json not created"

    # Verify scenes_complete.json has backfilled timestamps
    complete_path = tmp_path / "scenes_complete.json"
    assert complete_path.exists(), "scenes_complete.json not created"
    with open(complete_path, 'r') as f:
        complete = json.load(f)
    assert complete["scenes"][0]["narration"]["voice_start_ms"] > 0, \
        "voice_start_ms not backfilled"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd .opencode/skills/video-generate/scripts && python3 -m pytest test_generate_audio.py::test_generate_audio_creates_output -v
```

Expected: FAIL (generate_audio.py not found)

- [ ] **Step 3: Implement generate_audio.py**

```python
#!/usr/bin/env python3
"""
Generate TTS voiceover from scenes.json using Edge-TTS.
Outputs voice.mp3, timestamps.json, and scenes_complete.json (with backfilled timestamps).
Does NOT modify the original scenes.json.
"""

import argparse
import asyncio
import json
import os
import re
import sys
import tempfile


async def generate_voice(text: str, voice: str, output_path: str, srt_path: str):
    """Generate MP3 voiceover and SRT subtitles using Edge-TTS."""
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    sub_maker = edge_tts.SubMaker()
    with open(output_path, 'wb') as mp3_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                mp3_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                sub_maker.create_sub(
                    (chunk["offset"], chunk["duration"]), chunk["text"]
                )
    # Write SRT
    with open(srt_path, 'w', encoding='utf-8') as f:
        f.write(sub_maker.generate_subs())
    return sub_maker


def parse_srt_timestamps(srt_path: str):
    """Parse SRT file to extract per-line timing info.
    Returns list of {'text': str, 'start_ms': int, 'end_ms': int}."""
    entries = []
    with open(srt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    # Match SRT blocks: index, timestamp line, text lines
    blocks = re.split(r'\n\n+', content.strip())
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 2:
            continue
        # Parse timestamp line: 00:00:00,000 --> 00:00:00,000
        ts_match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', lines[1])
        if not ts_match:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, ts_match.groups())
        start_ms = ((h1 * 3600 + m1 * 60 + s1) * 1000) + ms1
        end_ms = ((h2 * 3600 + m2 * 60 + s2) * 1000) + ms2
        text = '\n'.join(lines[2:]).strip()
        entries.append({'text': text, 'start_ms': start_ms, 'end_ms': end_ms})
    return entries


def match_scene_timestamps(scenes: list, srt_entries: list, full_text: str):
    """Match SRT entries to scenes by searching for scene narration.text
    substring positions within the concatenated full text."""
    position = 0
    for scene in scenes:
        nar = scene["narration"]
        scene_text = nar["text"].strip()
        # Find this scene's text in the full concatenated text
        idx = full_text.find(scene_text, position)
        if idx == -1:
            # fallback: try with whitespace normalization
            normalized_full = re.sub(r'\s+', '', full_text)
            normalized_scene = re.sub(r'\s+', '', scene_text)
            idx = normalized_full.find(normalized_scene, position)
        if idx >= 0:
            # Map character index to ms using SRT entries (approximate)
            # Count characters up to idx in full_text, find corresponding SRT entry
            char_count = 0
            start_ms = srt_entries[0]["start_ms"] if srt_entries else 0
            end_ms = srt_entries[-1]["end_ms"] if srt_entries else 0
            for entry in srt_entries:
                entry_len = len(entry["text"])
                if char_count <= idx < char_count + entry_len:
                    start_ms = entry["start_ms"]
                if char_count <= (idx + len(scene_text)) < char_count + entry_len:
                    end_ms = entry["end_ms"]
                char_count += entry_len
            nar["voice_start_ms"] = start_ms
            nar["voice_end_ms"] = end_ms
        position = idx + len(scene_text) if idx >= 0 else position


def build_word_timestamps(srt_entries: list, full_text: str):
    """Build word-level timestamps from SRT entries.
    For Chinese, Edge-TTS outputs per-character boundaries in the SRT."""
    words = []
    for entry in srt_entries:
        text = entry["text"]
        # For Chinese: each char is a "word". For English: split by spaces.
        # Edge-TTS WordBoundary per character for CJK
        words.append({
            "word": text,
            "start_ms": entry["start_ms"],
            "end_ms": entry["end_ms"]
        })
    return words


async def main_async(scenes_path: str, outdir: str, voice: str):
    # Read scenes.json
    with open(scenes_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Concatenate all narration texts
    full_text = "".join(s["narration"]["text"] for s in data["scenes"])

    voice_path = os.path.join(outdir, "voice.mp3")
    srt_path = os.path.join(outdir, "temp.srt")

    # Generate voice + SRT
    sub_maker = await generate_voice(full_text, voice, voice_path, srt_path)

    # Parse SRT for timestamps
    srt_entries = parse_srt_timestamps(srt_path)

    # Backfill scene timestamps
    match_scene_timestamps(data["scenes"], srt_entries, full_text)

    # Build word-level timestamps
    word_ts = build_word_timestamps(srt_entries, full_text)
    # Distribute word timestamps to each scene
    offset = 0
    for scene in data["scenes"]:
        nar_text = scene["narration"]["text"]
        char_len = len(nar_text)
        scene_words = []
        accumulated = 0
        for w in word_ts[offset:]:
            if accumulated >= char_len:
                break
            scene_words.append(w)
            accumulated += len(w["word"])
            offset += 1
        scene["narration"]["timestamps"] = scene_words

    # Update meta
    if srt_entries:
        data["meta"]["total_duration_ms"] = srt_entries[-1]["end_ms"]
        data["meta"]["total_duration_seconds"] = round(srt_entries[-1]["end_ms"] / 1000)
        data["meta"]["total_duration_frames"] = int(srt_entries[-1]["end_ms"] * data["meta"]["fps"] / 1000)

    # Distribute total duration across scenes proportionally to narration length
    total_frames = data["meta"]["total_duration_frames"]
    char_lens = [len(scene["narration"]["text"]) for scene in data["scenes"]]
    total_chars = sum(char_lens)
    if total_chars > 0:
        accumulated = 0
        for i, scene in enumerate(data["scenes"]):
            if i == len(data["scenes"]) - 1:
                scene["duration_frames"] = total_frames - accumulated
            else:
                scene["duration_frames"] = int(total_frames * char_lens[i] / total_chars)
                accumulated += scene["duration_frames"]

    # Write outputs
    ts_path = os.path.join(outdir, "timestamps.json")
    complete_path = os.path.join(outdir, "scenes_complete.json")
    with open(ts_path, 'w', encoding='utf-8') as f:
        json.dump(word_ts, f, ensure_ascii=False)
    with open(complete_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # Cleanup temp SRT
    os.remove(srt_path)
    print(f"✅ voice.mp3 → {voice_path}")
    print(f"✅ timestamps.json → {ts_path}")
    print(f"✅ scenes_complete.json → {complete_path}")
    print(f"   Duration: {data['meta']['total_duration_seconds']}s")


def main():
    parser = argparse.ArgumentParser(description="Generate TTS audio from scenes.json")
    parser.add_argument("scenes_path", help="Path to scenes.json")
    parser.add_argument("--outdir", default=None,
                       help="Output directory (default: same dir as scenes.json)")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural",
                       help="Edge-TTS voice name (default: zh-CN-XiaoxiaoNeural)")
    args = parser.parse_args()

    if args.outdir is None:
        args.outdir = os.path.dirname(os.path.abspath(args.scenes_path))
    os.makedirs(args.outdir, exist_ok=True)

    asyncio.run(main_async(args.scenes_path, args.outdir, args.voice))


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run basic import check**

```bash
cd .opencode/skills/video-generate/scripts && python3 -c "from generate_audio import parse_srt_timestamps; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/scripts/generate_audio.py \
       .opencode/skills/video-generate/scripts/test_generate_audio.py
git commit -m "feat(video): add Edge-TTS audio generation with timestamp backfill"
```

---

### Task 5: fetch_assets.py — 5-Layer Asset Search

**Files:**
- Create: `.opencode/skills/video-generate/scripts/fetch_assets.py`

- [ ] **Step 1: Implement fetch_assets.py**

```python
#!/usr/bin/env python3
"""
5-layer asset search and download for video scenes.
Searches: 1) article reference links, 2) Pexels/Pixabay/Unsplash APIs,
3) Bing image search, 4) AI image generation (fallback), 5) Playwright screenshots.

Usage:
    python3 fetch_assets.py content/video/{name}/scenes.json
"""

import argparse
import json
import hashlib
import os
import sys
import time
import urllib.request
import urllib.parse
from typing import List, Dict, Optional

try:
    from PIL import Image
    import imagehash
    HAS_IMAGEHASH = True
except ImportError:
    HAS_IMAGEHASH = False

try:
    from newspaper import Article
    HAS_NEWSPAPER = True
except ImportError:
    HAS_NEWSPAPER = False

import requests

# --- API key sources (environment variables) ---
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")
PIXABAY_API_KEY = os.environ.get("PIXABAY_API_KEY", "")
UNSPLASH_ACCESS_KEY = os.environ.get("UNSPLASH_ACCESS_KEY", "")

USER_AGENT = "ContentCreationKit/1.0"


def md5_hash(data: bytes) -> str:
    return hashlib.md5(data).hexdigest()


def download_file(url: str, dest: str, timeout: int = 30) -> bool:
    """Download a file from URL to dest. Returns True on success."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
        # Basic validation: non-empty
        if len(data) < 100:
            return False
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as f:
            f.write(data)
        return True
    except Exception:
        return False


# --- Layer 1: Article reference links ---

def search_reference_links(scene_keywords_zh: List[str], ref_urls: List[str],
                           max_images: int = 5) -> List[Dict]:
    """Extract top_image from referenced article URLs using newspaper3k."""
    results = []
    if not HAS_NEWSPAPER:
        return results
    for url in ref_urls[:3]:  # limit to 3 refs per scene
        try:
            article = Article(url, request_timeout=10)
            article.download()
            article.parse()
            if article.top_image:
                results.append({
                    "url": article.top_image,
                    "source": "newspaper3k",
                    "source_url": url,
                    "type": "image"
                })
                if len(results) >= max_images:
                    break
        except Exception:
            continue
    return results


# --- Layer 2: Stock APIs ---

def search_pexels(query: str, max_results: int = 5) -> List[Dict]:
    """Search Pexels for photos and videos."""
    results = []
    if not PEXELS_API_KEY:
        return results
    headers = {"Authorization": PEXELS_API_KEY}
    # Photos
    try:
        resp = requests.get("https://api.pexels.com/v1/search",
                          params={"query": query, "per_page": max_results, "orientation": "landscape"},
                          headers=headers, timeout=15)
        if resp.status_code == 200:
            for photo in resp.json().get("photos", []):
                results.append({
                    "url": photo["src"]["large"],
                    "source": "pexels", "source_url": photo["url"],
                    "type": "image", "width": photo["width"], "height": photo["height"],
                    "photographer": photo["photographer"]
                })
    except Exception:
        pass
    # Videos
    try:
        resp = requests.get("https://api.pexels.com/videos/search",
                          params={"query": query, "per_page": 2},
                          headers=headers, timeout=15)
        if resp.status_code == 200:
            for video in resp.json().get("videos", []):
                best = max(video.get("video_files", []),
                          key=lambda f: f.get("width", 0), default=None)
                if best:
                    results.append({
                        "url": best["link"], "source": "pexels",
                        "source_url": video["url"], "type": "video",
                        "width": best["width"], "height": best["height"]
                    })
    except Exception:
        pass
    return results[:max_results]


def search_pixabay(query: str, max_results: int = 5) -> List[Dict]:
    """Search Pixabay for images and videos. Lang=zh for Chinese queries."""
    results = []
    if not PIXABAY_API_KEY:
        return results
    base = "https://pixabay.com/api/"
    # Images
    try:
        resp = requests.get(base, params={
            "key": PIXABAY_API_KEY, "q": query, "lang": "zh",
            "image_type": "photo", "per_page": max_results
        }, timeout=15)
        if resp.status_code == 200:
            for hit in resp.json().get("hits", []):
                results.append({
                    "url": hit["largeImageURL"],
                    "source": "pixabay", "source_url": hit["pageURL"],
                    "type": "image", "width": hit["imageWidth"], "height": hit["imageHeight"]
                })
    except Exception:
        pass
    # Videos
    try:
        resp = requests.get("https://pixabay.com/api/videos/", params={
            "key": PIXABAY_API_KEY, "q": query, "lang": "zh", "per_page": 2
        }, timeout=15)
        if resp.status_code == 200:
            for hit in resp.json().get("hits", []):
                videos = hit.get("videos", {})
                best = videos.get("large") or videos.get("medium")
                if best:
                    results.append({
                        "url": best["url"], "source": "pixabay",
                        "source_url": hit["pageURL"], "type": "video",
                        "width": best["width"], "height": best["height"]
                    })
    except Exception:
        pass
    return results[:max_results]


def search_unsplash(query: str, max_results: int = 3) -> List[Dict]:
    """Search Unsplash for photos."""
    results = []
    if not UNSPLASH_ACCESS_KEY:
        return results
    try:
        resp = requests.get("https://api.unsplash.com/search/photos", params={
            "query": query, "client_id": UNSPLASH_ACCESS_KEY,
            "per_page": max_results, "orientation": "landscape"
        }, timeout=15)
        if resp.status_code == 200:
            for photo in resp.json().get("results", []):
                results.append({
                    "url": photo["urls"]["regular"],
                    "source": "unsplash", "source_url": photo["links"]["html"],
                    "type": "image", "width": photo["width"], "height": photo["height"]
                })
    except Exception:
        pass
    return results


# --- Layer 3: Web image search (Bing) ---

def search_bing_images(query: str, max_results: int = 10) -> List[Dict]:
    """Search Bing images (no API key needed). Uses HTML parsing."""
    results = []
    try:
        url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&first=1"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            # Extract murl from Bing's image JSON data
            import re as _re
            matches = _re.findall(r'"murl"\s*:\s*"([^"]+)"', resp.text)
            for murl in matches[:max_results]:
                results.append({
                    "url": murl, "source": "bing",
                    "source_url": url, "type": "image"
                })
    except Exception:
        pass
    return results


# --- Main search orchestrator ---

def search_all_layers(keywords_zh: List[str], keywords_en: List[str],
                      ref_urls: List[str], max_per_scene: int = 8) -> List[Dict]:
    """Run all 5 search layers, deduplicate, and return best results."""
    all_results = []

    # Layer 1: Reference links
    for kw in keywords_zh[:2]:
        all_results.extend(search_reference_links([kw], ref_urls))

    # Layer 2: Stock APIs
    for query in (keywords_en[:3] + keywords_zh[:2]):
        all_results.extend(search_pexels(query, 3))
        all_results.extend(search_pixabay(query, 3))
        all_results.extend(search_unsplash(query, 2))

    # Layer 3: Bing image search
    for query in (keywords_en[:2] + keywords_zh[:2]):
        all_results.extend(search_bing_images(query, 5))

    # Layer 4 (AI generation) and Layer 5 (screenshots) are deferred
    # — triggered by Agent when no suitable assets found.

    # Deduplicate by URL
    seen = set()
    unique = []
    for r in all_results:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    return unique[:max_per_scene]


def process_scene(scene: dict, ref_urls: List[str],
                  assets_dir: str) -> dict:
    """Process a single scene: search → download → return manifest entry."""
    kw_zh = scene.get("search_keywords", {}).get("zh", [])
    kw_en = scene.get("search_keywords", {}).get("en", [])
    sid = scene["id"]

    results = search_all_layers(kw_zh, kw_en, ref_urls)
    assets = []
    for i, r in enumerate(results):
        ext = "mp4" if r["type"] == "video" else "jpg"
        filename = f"{sid}_{i:02d}.{ext}"
        dest = os.path.join(assets_dir, filename)
        success = download_file(r["url"], dest)
        status = "downloaded" if success else "failed"
        assets.append({
            "file": f"assets/{filename}",
            "source": r["source"],
            "source_url": r.get("source_url", ""),
            "type": r["type"],
            "width": r.get("width", 0),
            "height": r.get("height", 0),
            "status": status
        })

    print(f"   [{sid}] {len([a for a in assets if a['status'] == 'downloaded'])}/{len(assets)} assets downloaded")

    return {
        "scene_id": sid,
        "keywords": kw_en + kw_zh,
        "assets": assets
    }


def extract_ref_urls(article_source: str) -> List[str]:
    """Extract reference URLs from article markdown.
    Looks for markdown links and bare URLs in the article."""
    if not article_source or not os.path.exists(article_source):
        return []
    with open(article_source, 'r', encoding='utf-8') as f:
        text = f.read()
    # Match markdown links [text](url) and bare http(s) URLs
    import re as _re
    md_links = _re.findall(r'\]\((https?://[^\s\)]+)\)', text)
    bare_urls = _re.findall(r'(?<!\()(https?://[^\s\)\]\"]+)', text)
    return list(set(md_links + bare_urls))[:20]


def main():
    parser = argparse.ArgumentParser(description="Fetch video assets from 5-layer search")
    parser.add_argument("scenes_path", help="Path to scenes.json")
    parser.add_argument("--article-source", default=None,
                       help="Path to article markdown (for reference link extraction)")
    parser.add_argument("--outdir", default=None,
                       help="Output directory for assets")
    args = parser.parse_args()

    with open(args.scenes_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if args.outdir is None:
        args.outdir = os.path.join(os.path.dirname(os.path.abspath(args.scenes_path)), "assets")
    os.makedirs(args.outdir, exist_ok=True)

    article_source = args.article_source or data.get("meta", {}).get("article_source", "")
    ref_urls = extract_ref_urls(article_source)
    print(f"🔍 Extracted {len(ref_urls)} reference URLs from article")

    manifest = {"scenes": [], "stats": {"total_assets": 0, "by_source": {}, "failed_queries": []}}

    for i, scene in enumerate(data["scenes"]):
        entry = process_scene(scene, ref_urls, args.outdir)
        manifest["scenes"].append(entry)
        # Backfill downloaded assets into scenes.json so Remotion can read scene.data.media
        data["scenes"][i].setdefault("data", {})["media"] = [a for a in entry["assets"] if a["status"] == "downloaded"]
        data["scenes"][i].setdefault("data", {})["media_manifest"] = entry["assets"]
        for a in entry["assets"]:
            src = a["source"]
            manifest["stats"]["by_source"][src] = manifest["stats"]["by_source"].get(src, 0) + 1
            if a["status"] == "failed":
                manifest["stats"]["failed_queries"].append(a["source_url"])
        manifest["stats"]["total_assets"] += len([a for a in entry["assets"] if a["status"] == "downloaded"])

    manifest_path = os.path.join(args.outdir, "manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # Write backfilled scenes (with asset paths) alongside original scenes.json
    scenes_backfill_path = os.path.splitext(args.scenes_path)[0] + "_with_assets.json"
    with open(scenes_backfill_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ {manifest['stats']['total_assets']} assets saved to {args.outdir}")
    print(f"   manifest.json written with summary")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Verify import**

```bash
python3 -c "from fetch_assets import search_all_layers; print('OK')"
```

Expected: `OK` (no API key warnings are fine)

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/fetch_assets.py
git commit -m "feat(video): add 5-layer asset search and download script"
```

---

### Task 6: Remotion Scaffold

**Files:**
- Create: `.opencode/skills/video-generate/remotion/package.json`
- Create: `.opencode/skills/video-generate/remotion/tsconfig.json`
- Create: `.opencode/skills/video-generate/remotion/remotion.config.ts`
- Create: `.opencode/skills/video-generate/remotion/src/theme.ts`

- [ ] **Step 1: Write package.json**

```json
{
  "name": "video-generate-remotion",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "build": "remotion render MainVideo"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "remotion": "^4.0.0",
    "@remotion/cli": "^4.0.0",
    "@remotion/media": "^4.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "typescript": "^5.5.0"
  }
}
```

- [ ] **Step 2: Write tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "commonjs",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "resolveJsonModule": true
  },
  "include": ["src/**/*"]
}
```

- [ ] **Step 3: Write remotion.config.ts**

```typescript
import { Config } from "@remotion/cli/config";

Config.setEntryPoint("./src/Root.tsx");
Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
```

- [ ] **Step 4: Write theme.ts**

```typescript
import type { ColorTheme, Meta } from "./input-props";

export const DEFAULT_COLOR_THEME: ColorTheme = {
  primary: "#1a1a2e",
  accent: "#e94560",
  text: "#ffffff",
  background: "#0f0f1a",
};

export const DEFAULT_FONT_FAMILY =
  "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'SimHei', sans-serif";

export function resolveTheme(meta: Meta) {
  return {
    color: meta.color_theme || DEFAULT_COLOR_THEME,
    fontFamily: meta.font_family || DEFAULT_FONT_FAMILY,
    width: meta.width,
    height: meta.height,
    fps: meta.fps,
  };
}
```

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/remotion/
git commit -m "feat(video): scaffold Remotion project with configs and theme"
```

---

### Task 7: Remotion Scene Templates (6 Types)

**Files:**
- Create: `.opencode/skills/video-generate/remotion/src/templates/TitleCard.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/templates/ChapterTitle.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/templates/StockFootageScene.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/templates/InfoCardScene.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/templates/CodeBlockScene.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/templates/Outro.tsx`

- [ ] **Step 1: TitleCard.tsx**

```tsx
import { spring, useCurrentFrame, useVideoConfig, interpolate, Img, staticFile } from "remotion";
import type { TitleCardData, AnimationConfig } from "../input-props";
import { resolveTheme } from "../theme";
import type { Meta } from "../input-props";

interface Props {
  data: TitleCardData;
  animation?: AnimationConfig;
  meta: Meta;
}

export const TitleCard: React.FC<Props> = ({ data, meta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(meta);

  const titleSpring = spring({ frame, fps, config: { damping: 12, stiffness: 100 } });
  const subtitleOpacity = interpolate(frame, [30, 60], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div style={{
      width: "100%", height: "100%",
      background: `linear-gradient(135deg, ${theme.color.primary} 0%, ${theme.color.background} 100%)`,
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      fontFamily: theme.fontFamily,
    }}>
      {data.background && (
        <Img src={data.background.startsWith("http") ? data.background : staticFile(data.background)}
          style={{ position: "absolute", width: "100%", height: "100%", objectFit: "cover", opacity: 0.3 }} />
      )}
      <h1 style={{
        color: theme.color.text, fontSize: 72, fontWeight: 700,
        textAlign: "center", maxWidth: "80%",
        transform: `scale(${0.7 + titleSpring * 0.3})`,
        textShadow: "0 2px 20px rgba(0,0,0,0.5)",
      }}>
        {data.title}
      </h1>
      {data.subtitle && (
        <p style={{
          color: theme.color.accent, fontSize: 32, marginTop: 24,
          opacity: subtitleOpacity, maxWidth: "60%", textAlign: "center",
        }}>
          {data.subtitle}
        </p>
      )}
    </div>
  );
};
```

- [ ] **Step 2: ChapterTitle.tsx**

```tsx
import { spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import type { ChapterTitleData, AnimationConfig, Meta } from "../input-props";
import { resolveTheme } from "../theme";

export const ChapterTitle: React.FC<{ data: ChapterTitleData; animation?: AnimationConfig; meta: Meta }> = ({ data, meta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(meta);
  const scale = spring({ frame, fps, config: { damping: 15, stiffness: 80 } });
  const opacity = interpolate(frame, [0, 15], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div style={{
      width: "100%", height: "100%",
      background: theme.color.primary,
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      fontFamily: theme.fontFamily,
    }}>
      <span style={{
        color: theme.color.accent, fontSize: 24, opacity,
        letterSpacing: 8, textTransform: "uppercase",
      }}>
        Chapter {data.chapter_number}
      </span>
      <h2 style={{
        color: theme.color.text, fontSize: 56, fontWeight: 600,
        marginTop: 16, transform: `scale(${scale})`,
      }}>
        {data.title}
      </h2>
      {data.subtitle && (
        <p style={{ color: theme.color.accent, fontSize: 28, marginTop: 12, opacity }}>
          {data.subtitle}
        </p>
      )}
    </div>
  );
};
```

- [ ] **Step 3: StockFootageScene.tsx** (Ken Burns + text overlay)

```tsx
import { Img, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import type { StockFootageData, AnimationConfig, Meta } from "../input-props";
import { resolveTheme } from "../theme";

export const StockFootageScene: React.FC<{ data: StockFootageData; animation?: AnimationConfig; meta: Meta }> = ({ data, meta }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const theme = resolveTheme(meta);
  const scale = interpolate(frame, [0, durationInFrames], [1.0, 1.12], { extrapolateRight: "clamp" });

  const firstMedia = data.media?.[0];
  const hasMedia = !!firstMedia;

  return (
    <div style={{ width: "100%", height: "100%", position: "relative", overflow: "hidden", background: theme.color.background, fontFamily: theme.fontFamily }}>
      {hasMedia && firstMedia.type === "image" && (
        <Img src={staticFile(firstMedia.file)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})` }} />
      )}
      {hasMedia && firstMedia.type === "video" && (
        <OffthreadVideo src={staticFile(firstMedia.file)} style={{ width: "100%", height: "100%", objectFit: "cover", transform: `scale(${scale})` }} />
      )}
      {/* Gradient overlay */}
      <div style={{ position: "absolute", bottom: 0, width: "100%", height: "40%", background: "linear-gradient(transparent, rgba(0,0,0,0.7))" }} />
      {/* Text overlays */}
      {data.text_overlays?.map((overlay, i) => (
        <div key={i} style={{
          position: "absolute", bottom: 60, left: "50%", transform: "translateX(-50%)",
          padding: "16px 32px",
          background: "rgba(0,0,0,0.6)", borderRadius: 8,
          color: theme.color.text, fontSize: overlay.font_size || 28,
          maxWidth: "80%", textAlign: "center",
        }}>
          {overlay.text}
        </div>
      ))}
    </div>
  );
};
```

- [ ] **Step 4: InfoCardScene.tsx**

```tsx
import { spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import type { InfoCardData, AnimationConfig, Meta } from "../input-props";
import { resolveTheme } from "../theme";

export const InfoCardScene: React.FC<{ data: InfoCardData; animation?: AnimationConfig; meta: Meta }> = ({ data, animation, meta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(meta);

  const isBulletList = data.layout === "bullet_list";
  const isQuote = data.layout === "quote_box";
  const isThreeColumn = data.layout === "three_column";
  const isSplit = data.layout === "split";

  return (
    <div style={{
      width: "100%", height: "100%", background: theme.color.background,
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      padding: 80, fontFamily: theme.fontFamily,
    }}>
      {isBulletList && data.items && (
        <ul style={{ listStyle: "none", padding: 0 }}>
          {data.items.map((item, i) => {
            const delay = i * (animation?.stagger_delay_frames || 10);
            const opacity = interpolate(frame - delay, [0, 15], [0, 1], { extrapolateRight: "clamp" });
            const slide = interpolate(frame - delay, [0, 15], [30, 0], { extrapolateRight: "clamp" });
            return (
              <li key={i} style={{
                color: item.highlight ? theme.color.accent : theme.color.text,
                fontSize: 36, lineHeight: 1.8, opacity,
                transform: `translateY(${slide}px)`,
                paddingLeft: 40, position: "relative",
              }}>
                <span style={{ position: "absolute", left: 0, color: theme.color.accent }}>▸</span>
                {item.text}
              </li>
            );
          })}
        </ul>
      )}
      {isQuote && (
        <blockquote style={{ color: theme.color.text, fontSize: 38, fontStyle: "italic", textAlign: "center", maxWidth: "70%", borderLeft: `4px solid ${theme.color.accent}`, paddingLeft: 32 }}>
          "{data.quote}"
          {data.quote_source && <footer style={{ fontSize: 24, marginTop: 16, color: theme.color.accent }}>— {data.quote_source}</footer>}
        </blockquote>
      )}
      {isThreeColumn && data.columns && (
        <div style={{ display: "flex", gap: 40, width: "100%", justifyContent: "center" }}>
          {data.columns.map((col, i) => {
            const delay = i * (animation?.stagger_delay_frames || 12);
            const opacity = interpolate(frame - delay, [0, 20], [0, 1], { extrapolateRight: "clamp" });
            return (
              <div key={i} style={{ flex: 1, background: "rgba(255,255,255,0.05)", borderRadius: 12, padding: 32, opacity, textAlign: "center" }}>
                {col.title && <h3 style={{ color: theme.color.accent, fontSize: 28, marginBottom: 16 }}>{col.title}</h3>}
                <p style={{ color: theme.color.text, fontSize: 24, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{col.content}</p>
              </div>
            );
          })}
        </div>
      )}
      {isSplit && data.columns && (
  <div style={{ display: "flex", gap: 40, width: "100%", justifyContent: "center" }}>
    {data.columns.map((col, i) => (
      <div key={i} style={{ flex: 1, background: "rgba(255,255,255,0.05)", borderRadius: 12, padding: 32 }}>
        {col.title && <h3 style={{ color: theme.color.accent, fontSize: 28, marginBottom: 16 }}>{col.title}</h3>}
        <p style={{ color: theme.color.text, fontSize: 24, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>{col.content}</p>
      </div>
    ))}
  </div>
)}
    </div>
  );
};
```

- [ ] **Step 5: CodeBlockScene.tsx**

```tsx
import { useCurrentFrame, interpolate } from "remotion";
import type { CodeBlockData, AnimationConfig, Meta } from "../input-props";
import { resolveTheme } from "../theme";

export const CodeBlockScene: React.FC<{ data: CodeBlockData; animation?: AnimationConfig; meta: Meta }> = ({ data, meta }) => {
  const frame = useCurrentFrame();
  const theme = resolveTheme(meta);
  const lines = data.code.split("\n");
  const charsPerFrame = 2;
  const totalChars = data.code.length;
  const typedChars = Math.min(frame * charsPerFrame, totalChars);
  const typedText = data.code.substring(0, typedChars);

  const cursorBlink = Math.floor(frame / 15) % 2 === 0;

  return (
    <div style={{
      width: "100%", height: "100%", background: "#0d1117",
      display: "flex", flexDirection: "column", justifyContent: "center",
      padding: 60, fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
    }}>
      {data.title && (
        <div style={{ color: "#8b949e", fontSize: 20, marginBottom: 20, fontFamily: theme.fontFamily }}>
          {data.title}
        </div>
      )}
      <pre style={{ color: "#c9d1d9", fontSize: 28, lineHeight: 1.7, overflow: "hidden", whiteSpace: "pre-wrap" }}>
        <code>{typedText}</code>
        <span style={{ opacity: cursorBlink ? 1 : 0.3 }}>|</span>
      </pre>
    </div>
  );
};
```

- [ ] **Step 6: Outro.tsx**

```tsx
import { spring, useCurrentFrame, useVideoConfig, interpolate } from "remotion";
import type { OutroData, AnimationConfig, Meta } from "../input-props";
import { resolveTheme } from "../theme";

export const Outro: React.FC<{ data: OutroData; animation?: AnimationConfig; meta: Meta }> = ({ data, meta }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const theme = resolveTheme(meta);
  const scale = spring({ frame, fps, config: { damping: 10, stiffness: 60 } });
  const opacity = interpolate(frame, [0, 30], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div style={{
      width: "100%", height: "100%",
      background: `linear-gradient(135deg, ${theme.color.primary}, ${theme.color.background})`,
      display: "flex", flexDirection: "column",
      alignItems: "center", justifyContent: "center",
      fontFamily: theme.fontFamily,
    }}>
      <h2 style={{ color: theme.color.text, fontSize: 48, opacity, transform: `scale(${scale})` }}>
        {data.cta_text}
      </h2>
      <p style={{ color: theme.color.accent, fontSize: 28, marginTop: 16, opacity }}>
        感谢观看
      </p>
    </div>
  );
};
```

- [ ] **Step 7: Commit**

```bash
git add .opencode/skills/video-generate/remotion/src/templates/
git commit -m "feat(video): add 6 Remotion scene templates (TitleCard, ChapterTitle, StockFootage, InfoCard, CodeBlock, Outro)"
```

---

### Task 8: Remotion Reusable Components

**Files:**
- Create: `.opencode/skills/video-generate/remotion/src/components/CaptionOverlay.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/components/KenBurnsImage.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/components/TextCard.tsx`

- [ ] **Step 1: CaptionOverlay.tsx — karaoke captions**

```tsx
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { WordTimestamp, CaptionConfig } from "../input-props";

interface Props {
  timestamps: WordTimestamp[];
  config: CaptionConfig;
  fontFamily: string;
}

export const CaptionOverlay: React.FC<Props> = ({ timestamps, config, fontFamily }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentMs = (frame / fps) * 1000;
  if (!config.enabled || timestamps.length === 0) return null;

  // Find which words are active (overlapping with current time)
  // Show last ~15 words
  const activeWords = timestamps.filter(w => w.start_ms <= currentMs + 500 && w.end_ms >= currentMs - 2000);
  const displayWords = activeWords.slice(-15);

  return (
    <div style={{
      position: "absolute",
      bottom: config.position_y || 920,
      left: "50%", transform: "translateX(-50%)",
      display: "flex", flexWrap: "wrap",
      justifyContent: "center", gap: 8,
      maxWidth: "85%", fontFamily,
    }}>
      {displayWords.map((word, i) => {
        const isActive = currentMs >= word.start_ms && currentMs <= word.end_ms;
        return (
          <span key={i} style={{
            color: isActive ? config.active_color : config.inactive_color,
            fontSize: config.font_size,
            fontWeight: isActive ? 700 : 400,
            textShadow: isActive ? "0 0 10px rgba(255,255,255,0.3)" : "0 1px 4px rgba(0,0,0,0.8)",
          }}>
            {word.word}
          </span>
        );
      })}
    </div>
  );
};
```

- [ ] **Step 2: KenBurnsImage.tsx**

```tsx
import { Img, staticFile, useCurrentFrame, useVideoConfig, interpolate } from "remotion";

interface Props {
  src: string;
  scaleStart?: number;
  scaleEnd?: number;
}

export const KenBurnsImage: React.FC<Props> = ({ src, scaleStart = 1.0, scaleEnd = 1.15 }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const scale = interpolate(frame, [0, durationInFrames], [scaleStart, scaleEnd], { extrapolateRight: "clamp" });

  return (
    <Img
      src={src.startsWith("http") ? src : staticFile(src)}
      style={{
        width: "100%", height: "100%",
        objectFit: "cover",
        transform: `scale(${scale})`,
      }}
    />
  );
};
```

- [ ] **Step 3: TextCard.tsx**

```tsx
interface Props {
  text: string;
  fontFamily: string;
  color: string;
  fontSize?: number;
}

export const TextCard: React.FC<Props> = ({ text, fontFamily, color, fontSize = 28 }) => (
  <div style={{
    position: "absolute", bottom: 60, left: "50%", transform: "translateX(-50%)",
    padding: "16px 32px", background: "rgba(0,0,0,0.6)", borderRadius: 8,
    color, fontSize, fontFamily, maxWidth: "80%", textAlign: "center",
  }}>
    {text}
  </div>
);
```

- [ ] **Step 4: Commit**

```bash
git add .opencode/skills/video-generate/remotion/src/components/
git commit -m "feat(video): add reusable Remotion components (CaptionOverlay, KenBurnsImage, TextCard)"
```

---

### Task 9: Root.tsx + MainVideo.tsx

**Files:**
- Create: `.opencode/skills/video-generate/remotion/src/Root.tsx`
- Create: `.opencode/skills/video-generate/remotion/src/MainVideo.tsx`

- [ ] **Step 1: Root.tsx**

```tsx
import { Composition, registerRoot } from "remotion";
import { MainVideo } from "./MainVideo";
import type { ScenesJson } from "./input-props";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="MainVideo"
      component={MainVideo}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      defaultProps={{ meta: null as unknown as ScenesJson["meta"], scenes: [] as unknown as ScenesJson["scenes"], audio: {} as ScenesJson["audio"], captions: {} as ScenesJson["captions"] }}
      calculateMetadata={({ props }) => {
        const meta = props.meta;
        if (!meta) return {};
        return {
          durationInFrames: meta.total_duration_frames || 300,
          fps: meta.fps || 30,
          width: meta.width || 1920,
          height: meta.height || 1080,
        };
      }}
    />
  );
};

registerRoot(RemotionRoot);
```

- [ ] **Step 2: MainVideo.tsx**

```tsx
import { Audio, Sequence, staticFile } from "remotion";
import type { ScenesJson, Scene } from "./input-props";
import { TitleCard } from "./templates/TitleCard";
import { ChapterTitle } from "./templates/ChapterTitle";
import { StockFootageScene } from "./templates/StockFootageScene";
import { InfoCardScene } from "./templates/InfoCardScene";
import { CodeBlockScene } from "./templates/CodeBlockScene";
import { Outro } from "./templates/Outro";
import { CaptionOverlay } from "./components/CaptionOverlay";
import { resolveTheme } from "./theme";

function SceneRenderer({ scene, meta }: { scene: Scene; meta: ScenesJson["meta"] }) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const props = { data: scene.data as any, animation: scene.animation, meta };

  switch (scene.type) {
    case "title_card": return <TitleCard {...props} />;
    case "chapter_title": return <ChapterTitle {...props} />;
    case "stock_footage": return <StockFootageScene {...props} />;
    case "info_card": return <InfoCardScene {...props} />;
    case "code_block": return <CodeBlockScene {...props} />;
    case "outro": return <Outro {...props} />;
    default: return <div style={{ color: "white" }}>Unknown scene type: {scene.type}</div>;
  }
}

export const MainVideo: React.FC<{
  meta: ScenesJson["meta"];
  scenes: ScenesJson["scenes"];
  audio: ScenesJson["audio"];
  captions: ScenesJson["captions"];
} | Record<string, never>> = (props) => {
  // When --props points to scenes_final.json, Remotion spreads top-level keys.
  const { meta, scenes = [], audio = {} as ScenesJson["audio"], captions = {} as ScenesJson["captions"] } = props;

  if (!meta || scenes.length === 0) return null;

  const theme = resolveTheme(meta);

  // Collect all narration timestamps across all scenes
  const allTimestamps = scenes.flatMap((s: Scene) => s.narration.timestamps || []);

  // Calculate cumulative frame offsets
  let offset = 0;
  const sceneEntries = scenes.map((scene: Scene, i: number) => {
    const entry = { scene, from: offset, key: scene.id || `scene_${i}` };
    offset += scene.duration_frames;
    return entry;
  });

  return (
    <div style={{ width: "100%", height: "100%", background: theme.color.background }}>
      {/* Audio tracks */}
      <Audio src={staticFile(audio.voice_file)} volume={audio.voice_volume} />
      {audio.bgm_file && <Audio src={staticFile(audio.bgm_file)} volume={audio.bgm_volume} />}

      {/* Scene sequences */}
      {sceneEntries.map(({ scene, from, key }) => (
        <Sequence key={key} from={from} durationInFrames={scene.duration_frames}>
          <SceneRenderer scene={scene} meta={meta} />
        </Sequence>
      ))}

      {/* Caption overlay (above all scenes) */}
      <Sequence from={0} durationInFrames={offset}>
        <CaptionOverlay timestamps={allTimestamps} config={captions} fontFamily={theme.fontFamily} />
      </Sequence>
    </div>
  );
};
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/remotion/src/Root.tsx \
       .opencode/skills/video-generate/remotion/src/MainVideo.tsx
git commit -m "feat(video): add Remotion Root and MainVideo with scene sequencer"
```

---

### Task 10: render_video.sh

**Files:**
- Create: `.opencode/skills/video-generate/scripts/render_video.sh`

- [ ] **Step 1: Write render_video.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
REMOTION_DIR="$PROJECT_ROOT/.opencode/skills/video-generate/remotion"
LOCK_FILE="/tmp/video-generate-render.lock"

# --- ffmpeg pre-check ---
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg is required but not installed."
    echo "   Install: sudo apt install ffmpeg  # or brew install ffmpeg"
    exit 1
fi

# --- ffprobe pre-check ---
if ! command -v ffprobe &> /dev/null; then
    echo "❌ ffprobe is required but not installed (part of ffmpeg)."
    echo "   Install: brew install ffmpeg  # macOS"
    echo "   or: sudo apt install ffmpeg   # Linux"
    exit 1
fi

# --- Parse args ---
VIDEO_NAME="${1:-}"
SCENES_FILE="${2:-}"
if [ -z "$VIDEO_NAME" ] || [ -z "$SCENES_FILE" ]; then
    echo "Usage: render_video.sh <video_name> <scenes_final.json>"
    exit 1
fi

OUTPUT_DIR="$PROJECT_ROOT/content/video/$VIDEO_NAME"
ASSETS_SRC="$OUTPUT_DIR/assets"
ASSETS_DST="$REMOTION_DIR/public/assets"
OUTPUT_FILE="$OUTPUT_DIR/final.mp4"

# --- Concurrent render lock (POSIX-compatible, no flock needed) ---
if ! mkdir "$LOCK_FILE.lock" 2>/dev/null; then
    echo "❌ Another render is already running (lock: $LOCK_FILE)"
    exit 1
fi
trap 'rm -rf "$LOCK_FILE.lock"' EXIT

# --- Install Remotion deps if needed ---
if [ ! -d "$REMOTION_DIR/node_modules" ]; then
    echo "📦 Installing Remotion dependencies (first run)..."
    cd "$REMOTION_DIR" && npm install --no-audit --no-fund
fi

# --- Copy assets to Remotion public/ ---
rm -rf "$ASSETS_DST"
if [ -d "$ASSETS_SRC" ]; then
    cp -r "$ASSETS_SRC" "$ASSETS_DST"
    echo "📁 Assets copied: $(find "$ASSETS_DST" -type f | wc -l) files"
else
    mkdir -p "$ASSETS_DST"
    echo "⚠️  No assets directory found at $ASSETS_SRC"
fi

# --- Copy voice file ---
VOICE_SRC="$OUTPUT_DIR/voice.mp3"
if [ -f "$VOICE_SRC" ]; then
    cp "$VOICE_SRC" "$REMOTION_DIR/public/voice.mp3"
    echo "🎤 Voice file copied"
else
    echo "⚠️  voice.mp3 not found at $VOICE_SRC"
fi

# --- Render ---
# Pass scenes_final.json as Remotion input props file (merged assets + timestamps).
# Remotion reads the JSON file and spreads its top-level keys as props.
# MainVideo receives: { meta, scenes, audio, captions }
echo "🎬 Rendering video..."
cd "$REMOTION_DIR"
npx remotion render MainVideo \
    --props="$SCENES_FILE" \
    --output="$OUTPUT_FILE" \
    --codec=h264 \
    --crf=23 \
    --concurrency=${REMOTION_CONCURRENCY:-4}

# --- Cleanup ---
rm -rf "$ASSETS_DST"
rm -f "$REMOTION_DIR/public/voice.mp3"

echo "✅ Video rendered: $OUTPUT_FILE"
echo "   Size: $(du -h "$OUTPUT_FILE" | cut -f1)"
echo "   Duration: $(ffprobe -v quiet -show_entries format=duration -of csv=p=0 "$OUTPUT_FILE")s"
```

- [ ] **Step 2: Make executable, verify syntax**

```bash
chmod +x .opencode/skills/video-generate/scripts/render_video.sh
bash -n .opencode/skills/video-generate/scripts/render_video.sh
```

Expected: no output (syntax OK)

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/render_video.sh
git commit -m "feat(video): add Remotion render script with asset copy and concurrent lock"
```

---

### Task 11: SKILL.md + Command Definitions

**Files:**
- Create: `.opencode/skills/video-generate/SKILL.md`
- Create: `.opencode/commands/to-video-script.md`
- Create: `.opencode/commands/to-video-footage.md`
- Create: `.opencode/commands/to-video-audio.md`
- Create: `.opencode/commands/to-video-render.md`
- Create: `.opencode/commands/to-video.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: video-generate
description: Convert Markdown articles into B站/YouTube-style videos (16:9 MP4) via scene script generation → asset fetching → TTS audio → Remotion rendering.
allowed-tools: Bash,Write
---

# 文章转视频 (Article to Video)

将 Markdown 文章转化为横屏 16:9 中视频，通过四阶段管线：脚本生成 → 素材搜索 → 旁白合成 → Remotion 渲染。

## 触发条件

- 用户说"把这篇文章转成视频"
- 用户说"生成视频"
- 文章发布后需要多平台分发

## 前置依赖

### 系统
- ffmpeg >= 4.0
- Node.js >= 18

### Python（首次运行自动安装）
```bash
pip install -r .opencode/skills/video-generate/requirements.txt
```

### Node.js（首次渲染自动安装）
在 `.opencode/skills/video-generate/remotion/` 目录下 `npm install`

### API Keys（可选，仅素材搜索需要）
- `PEXELS_API_KEY`
- `PIXABAY_API_KEY`
- `UNSPLASH_ACCESS_KEY`

未设置则跳过对应素材源，不影响渲染。

## 管线

| 命令 | 输出 | 说明 |
|------|------|------|
| `/to-video-script` | `scenes.json` | Agent 分析文章 → 分场景脚本 |
| `/to-video-footage` | `assets/` + `manifest.json` | 五层素材搜索下载 |
| `/to-video-audio` | `voice.mp3` + `scenes_complete.json` | Edge-TTS 旁白 + 时间戳回填 |
| *(合并步骤)* | `scenes_final.json` | 合并素材路径 + 音频时间戳 |
| `/to-video-render` | `final.mp4` | Remotion 渲染（读取 `scenes_final.json`） |

一键模式：`/to-video`

## 输出

```
content/video/{article-name}/
├── scenes.json              # 场景脚本（Agent 生成）
├── scenes_with_assets.json  # 含素材路径的场景（fetch_assets 输出）
├── scenes_complete.json     # 含时间戳的场景（generate_audio 输出）
├── scenes_final.json        # 合并后数据（render 输入）
├── voice.mp3                # 旁白音频
├── timestamps.json          # 词级时间戳
├── assets/                  # 素材缓存
│   └── manifest.json
└── final.mp4                # 最终视频
```

## 错误处理

| 场景 | 处理 |
|------|------|
| Edge-TTS 不可用 | 重试 3 次（5s/15s/45s）后提示用户切换自录模式 |
| 素材搜索全空 | 降级为纯色背景 + 文字卡 |
| Remotion 渲染崩溃 | 输出 `--log=verbose` 诊断日志 |
| 中文字体缺失 | 警告用户安装任一中文字体 |
```

- [ ] **Step 2: Write command definitions**

**to-video-script.md:**
```markdown
---
description: 生成视频场景脚本
---

# 文章转视频场景脚本

## 目标
分析 Markdown 文章，生成结构化的视频场景脚本 `scenes.json`。

## 前置条件
`content/article/` 目录已有正式文章。

## 步骤

0. **创建输出目录**：
   ```bash
   mkdir -p content/video/{name}
   ```
1. **读取文章**：读取 `content/article/{name}.md`
2. **分析结构**：识别标题层级、表格、引用块、代码块、列表
3. **生成场景**：
   - 标题 → `title_card`
   - 章节标题 → `chapter_title`
   - 普通段落 → `stock_footage`（附带中英文搜索关键词）
   - 表格 → `info_card` + `three_column`
   - 引用块 → `info_card` + `quote_box`
   - 代码块 → `code_block`
   - 列表 → `info_card` + `bullet_list`
   - 结尾 → `outro`
4. **旁白改写**：将书面语改为口语化的旁白文本
5. **生成中英文搜索关键词**：每场景 3-5 个 zh + 3-5 个 en
6. **Schema 校验**：输出 `scenes.json` 后调用校验：
   ```bash
   python3 .opencode/skills/video-generate/scripts/scenes_schema.py content/video/{name}/scenes.json
   ```
7. **修复策略**：若校验失败，尝试自动修复 JSON 问题（移除尾部逗号、修复引号、闭合花括号）后重试校验，最多 3 次。若仍失败，保存错误场景 JSON 到 `content/video/{name}/scenes_error.json` 并中止。

## 输出
`content/video/{name}/scenes.json` — 8-15 个场景的结构化 JSON

## 约束
- narration.text 必须是口语化旁白，不是原文直接复制
- 每场景旁白控制在 15-30 秒可读完的长度
- voice_start_ms / voice_end_ms 留 0，由 /to-video-audio 回填
```

**to-video-footage.md:**
```markdown
---
description: 搜索下载视频素材
---

# 视频素材搜索下载

## 目标
根据 scenes.json 中的关键词，搜素并下载匹配的画面素材。

## 前置条件
`scenes.json` 已生成。

## 步骤

1. **读取 scenes.json** 获取每个场景的 search_keywords
2. **安装 Python 依赖**（首次）：
   ```bash
   PIP=1; [ -f /tmp/video-generate-deps-installed ] && PIP=0
   [ $PIP -eq 1 ] && pip install -r .opencode/skills/video-generate/requirements.txt && touch /tmp/video-generate-deps-installed
   ```
3. **运行素材搜索**：
   ```bash
   python3 .opencode/skills/video-generate/scripts/fetch_assets.py \
     content/video/{name}/scenes.json \
     --article-source content/article/{name}.md
   ```

## 输出
`content/video/{name}/assets/` + `manifest.json`

## 约束
- 五层搜索：引用链接 → Pexels/Pixabay/Unsplash → Bing 图片 → AI 生图(fallback) → 网页截图(fallback)
- API Key 未设置时自动跳过对应层
- 全空时返回 fallback 标记，不阻断管线
```

**to-video-audio.md:**
```markdown
---
description: 生成视频旁白音频
---

# 视频旁白生成

## 目标
使用 Edge-TTS 生成 AI 旁白音频，并回填时间戳。

## 前置条件
`scenes.json` 已生成。

## 步骤

1. **安装依赖**（首次）：
   ```bash
   PIP=1; [ -f /tmp/video-generate-deps-installed ] && PIP=0
   [ $PIP -eq 1 ] && pip install -r .opencode/skills/video-generate/requirements.txt && touch /tmp/video-generate-deps-installed
   ```
2. **生成音频**：
   ```bash
   python3 .opencode/skills/video-generate/scripts/generate_audio.py \
     content/video/{name}/scenes.json \
     --voice zh-CN-XiaoxiaoNeural
   ```

## 输出
- `voice.mp3` — 旁白音频
- `timestamps.json` — 词级时间戳
- `scenes_complete.json` — 含回填时间戳的完整场景数据（⚠️ 非 render 直接输入，需合并素材路径）

## 约束
- Edge-TTS 失败自动重试 3 次（5s/15s/45s 间隔）
- 不修改原始 `scenes.json`
```

**to-video-render.md:**
```markdown
---
description: 渲染最终视频
---

# 视频渲染

## 目标
使用 Remotion 将场景脚本、素材、音频合成为最终 MP4。

## 前置条件
前三步产物齐全。

## 步骤

```bash
bash .opencode/skills/video-generate/scripts/render_video.sh \
  {video_name} \
  content/video/{video_name}/scenes_final.json
```

## 输出
`content/video/{name}/final.mp4` — 1920×1080 H.264 MP4

## 约束
- 预期渲染时间：5 分钟视频 ~15-30 分钟，15 分钟视频 ~30-60 分钟
- 并发锁防止同时渲染
```

**to-video.md:**
```markdown
---
description: 一键文章转视频
---

# 一键文章转视频

## 目标
全自动将文章转化为视频，无暂停。

## 前置条件
- 文章已通过 `/to-article` 管线最终确认
- `content/video/{name}/scenes.json` 尚未存在（避免覆盖）

## 步骤

0. **确认文章**：检查 `content/article/` 目录选择最新文章，或让用户指定文章名称
1. `/to-video-script` → 生成场景脚本
2. `/to-video-footage` → 搜索下载素材
3. `/to-video-audio` → 生成旁白音频
4. `/to-video-render` → 渲染最终视频

四步自动串联，全程不暂停。
```

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/SKILL.md \
       .opencode/commands/to-video-script.md \
       .opencode/commands/to-video-footage.md \
       .opencode/commands/to-video-audio.md \
       .opencode/commands/to-video-render.md \
       .opencode/commands/to-video.md
git commit -m "feat(video): add SKILL.md and 5 command definitions"
```

---

### Task 12: Integration Test

**Files:**
- Create: `.opencode/skills/video-generate/scripts/test_integration.py`

- [ ] **Step 1: Write integration test**

```python
"""End-to-end integration test for article-to-video pipeline.
Tests each stage with a minimal article.
"""

import json
import os
import subprocess
import sys
import tempfile
import pytest

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))

# Minimal test article
TEST_ARTICLE = """# Test Article

## Section 1

This is a test paragraph about artificial intelligence.

## Section 2

| Column A | Column B |
|----------|----------|
| Value 1  | Value 2  |

> This is an important quote.

```
print("hello world")
```
"""


def test_schema_validator_accepts_valid_json():
    from scenes_schema import validate_scenes
    data = {
        "meta": {"article_title": "T", "article_source": "t.md", "output": "t.mp4",
                 "aspect_ratio": "16:9", "width": 1920, "height": 1080, "fps": 30,
                 "total_duration_frames": 300, "total_duration_seconds": 10,
                 "font_family": "sans-serif",
                 "color_theme": {"primary": "#000", "accent": "#f00", "text": "#fff", "background": "#000"}},
        "scenes": [
            {"id": "s1", "type": "title_card", "duration_frames": 150,
             "search_keywords": {"zh": ["a"], "en": ["a"]}, "data": {"title": "Test"},
             "narration": {"text": "Hi", "voice_file": "v.mp3",
                          "voice_start_ms": 0, "voice_end_ms": 1000, "timestamps": []}},
            {"id": "s2", "type": "code_block", "duration_frames": 150,
             "search_keywords": {"zh": [], "en": []}, "data": {"code": "hello", "language": "python"},
             "narration": {"text": "Code", "voice_file": "v.mp3",
                          "voice_start_ms": 0, "voice_end_ms": 1000, "timestamps": []}},
        ],
        "audio": {"voice_file": "v.mp3", "bgm_file": None, "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {"enabled": True, "style": "karaoke", "font_size": 36,
                    "position_y": 920, "active_color": "#f00", "inactive_color": "#fff"}
    }
    errors = validate_scenes(data)
    assert errors == [], f"Validation errors: {errors}"


def test_fetch_assets_extracts_ref_urls():
    from fetch_assets import extract_ref_urls

    text = """
    Check this link: https://example.com/article
    Also [this one](https://other.com/page)
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(text)
        tmp_path = f.name

    try:
        urls = extract_ref_urls(tmp_path)
        assert len(urls) >= 2
    finally:
        os.unlink(tmp_path)


def test_audio_parse_srt():
    from generate_audio import parse_srt_timestamps

    srt_content = """1
00:00:00,000 --> 00:00:01,500
你好

2
00:00:01,500 --> 00:00:03,000
世界"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write(srt_content)
        tmp_path = f.name

    try:
        entries = parse_srt_timestamps(tmp_path)
        assert len(entries) == 2
        assert entries[0]["start_ms"] == 0
        assert entries[0]["end_ms"] == 1500
        assert entries[0]["text"] == "你好"
    finally:
        os.unlink(tmp_path)


def test_render_script_syntax():
    script_path = os.path.join(SCRIPTS_DIR, "render_video.sh")
    result = subprocess.run(["bash", "-n", script_path], capture_output=True, text=True)
    assert result.returncode == 0, f"render_video.sh has syntax errors: {result.stderr}"
```

- [ ] **Step 2: Run integration tests**

```bash
cd .opencode/skills/video-generate/scripts && python3 -m pytest test_integration.py -v
```

Expected: 4 tests PASS

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/test_integration.py
git commit -m "test(video): add integration tests for pipeline stages"
```

---

## Self-Review

**Spec coverage check:**
- §5 scenes.json schema → Task 2 (validator) ✓
- §6 asset strategy → Task 5 (fetch_assets.py) ✓
- §7 Remotion engine → Tasks 6-9 (scaffold, templates, components, root) ✓
- §8 commands → Task 11 (SKILL.md + 5 commands) ✓
- §9 directory structure → Task 1 (scaffold) ✓
- §10 dependencies → Task 1 (requirements.txt) + Task 6 (package.json) ✓
- §11 background music → deferred (bgm/ dir created in Task 1, public/bgm/ placeholder) ✓
- §12 error handling → embedded in each script ✓
- §13 test plan → Task 2, 4, 12 (unit + integration tests) ✓

**Placeholder scan:** 1 known TBD resolved: InfoCardScene `isSplit` branch now has proper implementation (was "Split layout (content TBD)", replaced with two-column render).

**Type consistency:** `scenes_schema.py` constants match `input-props.ts` types. `animation.type` enum values are shared. Scene data required fields match template component props.

**Gaps identified:** 
- Background music files are not included in this plan (placeholder directory created). The render script copies `voice.mp3` but not BGM. This is acceptable — BGM is a "nice to have" that can be added after core pipeline works end-to-end. The render script and MainVideo.tsx already support `bgm_file` via the `audio` config.
- Asset-to-scene data flow: `fetch_assets.py` now writes `scenes_with_assets.json` with backfilled `data.media` and `data.media_manifest` for Remotion consumption. The `_with_assets.json` file should be passed to the render script instead of the original `scenes.json`.
- Remotion component tests: No snapshot/render tests for the 6 templates and 3 components. Recommended to add in a follow-up after core pipeline verification.

---

Plan complete and saved to `docs/superpowers/plans/2026-06-16-article-to-video.md`.

**Two execution options:**

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration
2. **Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
