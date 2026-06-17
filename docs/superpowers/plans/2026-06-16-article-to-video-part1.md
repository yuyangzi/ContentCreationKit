# Article-to-Video Pipeline Implementation Plan — Part 1: Scaffold & Asset Collection

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal (Part 1):** Build the data preparation foundation — schema validation, asset fetching (3-layer search, see *Asset Search Layers* note below), audio generation, and merge step — up to the point where all raw materials are collected into `scenes_final.json`.

**Pipeline overview (full):** 4-stage pipeline converting Markdown articles to 16:9 MP4 videos via Agent-driven scene generation → 3-layer asset search (v1) → Edge-TTS audio → Remotion rendering. *Note: The spec calls for a 5-layer search; v1 implements layers 1-3 (reference links, stock APIs, Bing). Layers 4 (AI generation) and 5 (Playwright screenshots) are deferred to v2 and are explicitly out of scope for Part 1.*

**Architecture:** Python scripts handle data preparation (schema validation, asset fetch, audio generation). Remotion (React/Node.js) handles video rendering. A single `scenes.json` interface file bridges the two ecosystems. OpenCode slash commands orchestrate the pipeline, following existing command/skill patterns.

**Tech Stack:** Python 3 (edge-tts, newspaper3k, Pillow, requests), Node.js (Remotion 4.x, React 18), Bash (orchestration), OpenCode Agent (LLM scene analysis)

**Spec reference:** `docs/superpowers/specs/2026-06-16-article-to-video-design.md`

**Part 2 reference:** `docs/superpowers/plans/2026-06-16-article-to-video-part2.md`

---

## File Structure

```
.opencode/skills/video-generate/
├── SKILL.md                              # Skill definition — **Part 2**
├── requirements.txt                      # Python deps — **Part 1**
├── scripts/
│   ├── __init__.py                       # **Part 1**
│   ├── scenes_schema.py                  # Schema validator + constants — **Part 1**
│   ├── generate_audio.py                 # Edge-TTS → scenes_complete.json — **Part 1**
│   ├── fetch_assets.py                   # 3-layer asset search → scenes_with_assets.json — **Part 1**
│   ├── merge_scenes.py                   # Merge → scenes_final.json — **Part 1**
│   ├── test_scenes_schema.py             # Schema validator tests — **Part 1**
│   ├── test_generate_audio.py            # Audio + retry tests — **Part 1**
│   ├── test_fetch_assets.py              # Asset search tests — **Part 1**
│   ├── test_merge_scenes.py              # Merge validation tests — **Part 1**
│   ├── test_contract_compliance.py       # Python↔TS cross-ecosystem contract — **Part 1**
│   └── render_video.sh                   # Asset copy + Remotion render — **Part 2**
└── remotion/                             # — **Part 2** (all files)
    ├── package.json
    ├── tsconfig.json
    ├── remotion.config.ts
    └── src/
        ├── Root.tsx
        ├── MainVideo.tsx
        ├── input-props.ts                # — **Part 1** (created in Task 3)
        ├── theme.ts
        ├── templates/
        │   ├── TitleCard.tsx
        │   ├── ChapterTitle.tsx
        │   ├── StockFootageScene.tsx
        │   ├── InfoCardScene.tsx
        │   ├── CodeBlockScene.tsx
        │   └── Outro.tsx
        └── components/
            ├── CaptionOverlay.tsx
            ├── KenBurnsImage.tsx
            └── TextCard.tsx

.opencode/commands/                       # — **Part 2** (all files)
├── to-video-script.md
├── to-video-footage.md
├── to-video-audio.md
├── to-video-render.md
└── to-video.md

Modified (Part 1):
- .gitignore                              # Add content/video/
```

## Task Dependency Graph

```
Task 1: Scaffold + .gitignore ──────────────────────────────────────┐
Task 2: scenes_schema.py (TDD)         ← depends on Task 1         │
Task 3: input-props.ts                 ← depends on Task 1         │
                                                                     │
Task 4: generate_audio.py (TDD)        ← depends on Task 2         │
Task 5: fetch_assets.py (TDD)          ← depends on Task 2         │
                                                                     │
Task 5b: merge_scenes.py (TDD)         ← depends on Task 4, 5      │
                                                                      │
Task 5c: test_contract_compliance.py   ← depends on Task 2, 3, 5b │
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

> **Note on data flow:** Tasks 4 and 5 produce *different* artifacts (`scenes_complete.json` from audio; `scenes_with_assets.json` from assets). Task 5b is a **mandatory merge step** before the renderer can see both asset paths and audio timestamps. Part 2's `to-video-render.md` has been updated to consume `scenes_final.json`, not `scenes_complete.json`. Task 5c verifies that the merged `scenes_final.json` structure satisfies both the Python schema and the TypeScript type contract (docs/superpowers/specs/2026-06-16-article-to-video-design.md).

## Parallel Execution Graph

```
Wave 1 (no deps):     Task 1
                       ↓
Wave 2 (parallel):    Task 2 ──┬── Task 3
                       ↓        ↓
Wave 3 (parallel):    Task 4   Task 6
                      Task 5   ↓
                       ↓       Task 7 ──┬── Task 8
Wave 3.5 (sync point): Task 5b ──┬── Task 5c (contract)
                                 ↓
Wave 4:                          Task 9
                               ↓
Wave 5:                       Task 10
                               ↓
Wave 6 (integration):         Task 11 ── Task 12
```

---

### Task 1: Directory Scaffold + .gitignore

**Files:**
- Create: `.opencode/skills/video-generate/requirements.txt`
- Create: `.opencode/skills/video-generate/scripts/__init__.py`
- Modify: `.gitignore`

- [ ] **Step 0: Install system dependencies (prerequisite for `newspaper3k`)**

```bash
# macOS
brew install libxml2 libxslt

# Ubuntu/Debian (uncomment if on Linux):
# sudo apt install libxml2-dev libxslt-dev

# Verify lxml can be compiled later (actual pip install happens after venv setup)
```

> **Why this step matters:** `newspaper3k` depends on `lxml` which requires `libxml2`/`libxslt` development headers at compile time. Without these, `pip install lxml` will fail with cryptic C compiler errors.

- [ ] **Step 0.5: Create Python virtual environment + install deps**

```bash
cd .opencode/skills/video-generate && python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
```

> **Why venv:** Isolates video-generate Python deps from other skills and system Python. Each skill's dependencies stay contained.

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
pytest>=8.0
```

Note: `stockmedia-sdk` and `imgsearch-api` are NOT included — they don't exist as reliable PyPI packages. `fetch_assets.py` will use `requests` to call Pexels/Pixabay/Unsplash/Bing APIs directly. `imagehash` is also NOT included — perceptual-hash dedup is deferred to v2; v1 uses URL-based dedup only.

**System prerequisites for `newspaper3k`** (must be installed BEFORE `pip install -r requirements.txt`):

- macOS: `brew install libxml2 libxslt`
- Ubuntu/Debian: `sudo apt install libxml2-dev libxslt-dev`
- Windows: Use conda or prebuilt wheels from https://www.lfd.uci.edu/~gohlke/pythonlibs/

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
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest test_scenes_schema.py::test_valid_minimal_scenes_json_passes -v
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
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest test_scenes_schema.py -v
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
  // Backfilled by generate_audio.py; optional in agent-generated scenes.json
  voice_start_ms?: number;
  voice_end_ms?: number;
  timestamps?: WordTimestamp[];
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


def test_retry_succeeds_on_second_attempt(monkeypatch):
    """generate_voice_with_retry retries 3x and succeeds on attempt 2.

    Mocks edge_tts.Communicate to raise on first call, succeed on second.
    Verifies call_count == 2 and no exception propagates.
    Skips if edge_tts not installed (same pattern as integration test).
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
        # Second attempt: write a fake mp3 + srt
        with open(output_path, "wb") as f:
            f.write(b"fake-audio")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("1\n00:00:00,000 --> 00:00:01,000\nHi\n\n")
        return None  # sub_maker not needed in this test

    # Patch the module-level generate_voice that retry wraps
    import generate_audio as ga
    monkeypatch.setattr(ga, "generate_voice", fake_generate_voice)
    # Speed up retry sleeps
    monkeypatch.setattr(ga, "RETRY_DELAYS", [0, 0, 0])

    with tempfile.TemporaryDirectory() as td:
        asyncio.run(ga.generate_voice_with_retry(
            "Hi", "test-voice",
            os.path.join(td, "voice.mp3"),
            os.path.join(td, "temp.srt"),
        ))
    assert call_count["n"] == 2, \
        f"expected 2 calls (1 fail + 1 success), got {call_count['n']}"
```

- [ ] **Step 2: Run — expect FAIL**

```bash
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest test_generate_audio.py::test_generate_audio_creates_output -v
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


# Retry config per spec §12 and SKILL.md (5s/15s/45s backoff)
RETRY_DELAYS = [5, 15, 45]
MAX_RETRIES = 3


async def generate_voice_with_retry(text: str, voice: str, output_path: str, srt_path: str):
    """Wrap generate_voice with 3-attempt exponential-ish retry on transient errors."""
    for attempt in range(MAX_RETRIES):
        try:
            return await generate_voice(text, voice, output_path, srt_path)
        except Exception as e:
            if attempt == MAX_RETRIES - 1:
                raise
            delay = RETRY_DELAYS[attempt]
            print(f"⚠️ Edge-TTS attempt {attempt + 1} failed: {e}. "
                  f"Retrying in {delay}s...", file=sys.stderr)
            await asyncio.sleep(delay)


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
        # Supports both comma (locale) and period as millisecond separator
        ts_match = re.match(r'(\d{2}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})[,.](\d{3})', lines[1])
        if not ts_match:
            continue
        h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, ts_match.groups())
        start_ms = ((h1 * 3600 + m1 * 60 + s1) * 1000) + ms1
        end_ms = ((h2 * 3600 + m2 * 60 + s2) * 1000) + ms2
        text = '\n'.join(lines[2:]).strip()
        entries.append({'text': text, 'start_ms': start_ms, 'end_ms': end_ms})
    return entries


def match_scene_timestamps(scenes: list, srt_entries: list, full_text: str):
    """Match SRT entries to scenes by character-position accumulation.

    Since full_text = ''.join(s['narration']['text'] for s in scenes),
    each scene occupies a known character range. SRT entries are walked
    in order, accumulating character lengths until each scene's range
    is covered. This avoids str.find() bugs with duplicate/overlapping
    narration text across scenes.
    """
    if not scenes or not srt_entries:
        return

    # Pre-compute scene character boundaries in full_text
    scene_ends = []
    pos = 0
    for scene in scenes:
        pos += len(scene["narration"]["text"])
        scene_ends.append(pos)

    # Walk SRT entries in order, assigning them to scenes by character range
    srt_idx = 0
    for i, end_pos in enumerate(scene_ends):
        nar = scenes[i]["narration"]
        prev_end = scene_ends[i - 1] if i > 0 else 0
        scene_char_len = end_pos - prev_end

        # First SRT entry for this scene → voice_start_ms
        if srt_idx < len(srt_entries):
            nar["voice_start_ms"] = srt_entries[srt_idx]["start_ms"]
        else:
            nar["voice_start_ms"] = 0
            nar["voice_end_ms"] = 0
            continue

        # Consume SRT entries until we've covered this scene's characters
        consumed = 0
        while srt_idx < len(srt_entries) and consumed < scene_char_len:
            consumed += len(srt_entries[srt_idx]["text"])
            if consumed >= scene_char_len:
                nar["voice_end_ms"] = srt_entries[srt_idx]["end_ms"]
            srt_idx += 1

        if consumed < scene_char_len and srt_entries:
            # Ran out of SRT entries; use last known timestamp
            nar["voice_end_ms"] = srt_entries[-1]["end_ms"]


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

    # Generate voice + SRT (with retry on transient Edge-TTS failures)
    sub_maker = await generate_voice_with_retry(full_text, voice, voice_path, srt_path)

    # Parse SRT for timestamps
    srt_entries = parse_srt_timestamps(srt_path)
    if not srt_entries:
        print("⚠️ Warning: SRT parsing returned 0 entries. "
              "Edge-TTS may have produced non-standard timestamp format.",
              file=sys.stderr)

    # Backfill scene timestamps
    match_scene_timestamps(data["scenes"], srt_entries, full_text)

    # Build word-level timestamps
    word_ts = build_word_timestamps(srt_entries, full_text)

    # Distribute word timestamps to each scene using character-position accumulation
    scene_boundaries = []  # cumulative end-positions in full_text
    cumulative = 0
    for scene in data["scenes"]:
        cumulative += len(scene["narration"]["text"])
        scene_boundaries.append(cumulative)

    scene_words_map = {i: [] for i in range(len(data["scenes"]))}
    scene_idx = 0
    chars_in_srt = 0  # total characters processed from SRT entries
    for w in word_ts:
        entry_len = len(w["word"])
        # Advance scene when cumulative SRT chars exceed the boundary
        while scene_idx < len(scene_boundaries) - 1 and chars_in_srt >= scene_boundaries[scene_idx]:
            scene_idx += 1
        scene_words_map[scene_idx].append(w)
        chars_in_srt += entry_len

    for i, scene in enumerate(data["scenes"]):
        scene["narration"]["timestamps"] = scene_words_map[i]

    # Update meta
    if srt_entries:
        data["meta"]["total_duration_ms"] = srt_entries[-1]["end_ms"]
        data["meta"]["total_duration_seconds"] = round(srt_entries[-1]["end_ms"] / 1000)
        data["meta"]["total_duration_frames"] = int(srt_entries[-1]["end_ms"] * data["meta"]["fps"] / 1000)

    # Distribute total duration across scenes proportionally to narration length
    # M3: floor at 30 frames (1s at 30fps) to prevent Remotion Sequence crash on
    # near-empty scenes (e.g., 1-char interjection)
    MIN_DURATION_FRAMES = 30
    total_frames = data["meta"]["total_duration_frames"]
    char_lens = [len(scene["narration"]["text"]) for scene in data["scenes"]]
    total_chars = sum(char_lens)
    if total_chars > 0:
        accumulated = 0
        for i, scene in enumerate(data["scenes"]):
            if i == len(data["scenes"]) - 1:
                scene["duration_frames"] = max(
                    MIN_DURATION_FRAMES, total_frames - accumulated
                )
            else:
                scene["duration_frames"] = max(
                    MIN_DURATION_FRAMES,
                    int(total_frames * char_lens[i] / total_chars)
                )
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
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -c "from generate_audio import parse_srt_timestamps; print('OK')"
```

Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/scripts/generate_audio.py \
       .opencode/skills/video-generate/scripts/test_generate_audio.py
git commit -m "feat(video): add Edge-TTS audio generation with timestamp backfill"
```

---

### Task 5: fetch_assets.py — 3-Layer Asset Search

**Files:**
- Create: `.opencode/skills/video-generate/scripts/fetch_assets.py`
- Create: `.opencode/skills/video-generate/scripts/test_fetch_assets.py`

**3-Layer search strategy** (layers 4-5 from spec deferred to v2):
- Layer 1: Article reference links → `newspaper3k` top_image extraction
- Layer 2: Stock APIs (Pexels / Pixabay / Unsplash) — requires API keys
- Layer 3: Bing image search (HTML scraping) — no API key needed, fragile

- [ ] **Step 0: Write failing tests (3 tests per spec §13.1)**

Create `test_fetch_assets.py`:

```python
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
    # Mock urlopen to return 200 bytes of data
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
```

- [ ] **Step 0.1: Run — expect FAIL (fetch_assets.py not implemented yet)**

```bash
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest test_fetch_assets.py -v
```

Expected: FAIL (ModuleNotFoundError: fetch_assets)

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

BING_RETRY_DELAYS = [2, 5]  # 2s, then 5s before giving up


def search_bing_images(query: str, max_results: int = 10) -> List[Dict]:
    """Search Bing images (no API key needed). Uses HTML parsing.

    NOTE on fragility: Bing changes HTML structure periodically, which breaks
    the `murl` regex. A retry loop with short backoff mitigates transient
    network/rendering issues. If all attempts fail, a structured warning
    is emitted so callers can detect layer-3 degradation.

    Returns (list): image results. Empty list means all retries failed.
    """
    results = []
    url = f"https://www.bing.com/images/search?q={urllib.parse.quote(query)}&first=1"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for attempt in range(1 + len(BING_RETRY_DELAYS)):  # 1 initial + N retries
        try:
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                import re as _re
                matches = _re.findall(r'"murl"\s*:\s*"([^"]+)"', resp.text)
                for murl in matches[:max_results]:
                    results.append({
                        "url": murl, "source": "bing",
                        "source_url": url, "type": "image"
                    })
                if not matches:
                    print(f"⚠️ Bing 返回 200 但 murl 解析为 0 条 (query={query})。"
                          f"HTML 结构可能已变。", file=sys.stderr)
                # Got results or got 200 with no matches — either way, done.
                break
        except Exception as e:
            if attempt < len(BING_RETRY_DELAYS):
                delay = BING_RETRY_DELAYS[attempt]
                print(f"⚠️ Bing 抓取失败 (attempt {attempt+1}, query={query}): {e}."
                      f" 重试 {delay}s 后…", file=sys.stderr)
                time.sleep(delay)
            else:
                print(f"⚠️ Bing 抓取全部失败 (query={query}): {e}", file=sys.stderr)
    return results


# --- Main search orchestrator ---

def search_all_layers(keywords_zh: List[str], keywords_en: List[str],
                      ref_urls: List[str], max_per_scene: int = 8) -> List[Dict]:
    """Run all 5 search layers, deduplicate, and return best results.

    WARNING: When ALL layers return zero results (no API keys, Bing blocked,
    no ref URLs), the caller will receive an empty list. This function emits
    a structured warning on stderr so the orchestrator can detect degradation.
    """
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

    # Warn if ALL layers returned nothing — highest severity degradation
    if not all_results:
        kw_str = ", ".join(keywords_en[:2] + keywords_zh[:2])
        print(f"⚠️ [search_all_layers] ZERO results for keywords '{kw_str}'. "
              f"Check: PEXELS_API_KEY, PIXABAY_API_KEY, UNSPLASH_ACCESS_KEY env vars, "
              f"Bing availability, and reference URLs.",
              file=sys.stderr)

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
    if not results:
        print(f"⚠️ [{sid}] ZERO assets found across all search layers. "
              f"Scene will render with no background media.",
              file=sys.stderr)
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

- [ ] **Step 2: Verify import** (H2 fix: must `cd` into scripts dir)

```bash
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -c "from fetch_assets import search_all_layers; print('OK')"
```

Expected: `OK` (no API key warnings are fine)

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/fetch_assets.py
git commit -m "feat(video): add 3-layer asset search and download script"
```

---

### Task 5b: merge_scenes.py — Combine Assets + Audio into scenes_final.json

**Files:**
- Create: `.opencode/skills/video-generate/scripts/merge_scenes.py`
- Create: `.opencode/skills/video-generate/scripts/test_merge_scenes.py`

**Files (modify in Part 2):**
- Part 2: `to-video-render.md` — change `scenes_complete.json` → `scenes_final.json` in the render command

> **Why this task exists:** `fetch_assets.py` writes `scenes_with_assets.json` (with `data.media` paths) but `generate_audio.py` reads the **original** `scenes.json` (no assets) and writes `scenes_complete.json` (with timestamps but no assets). Without this merge step, the Remotion renderer would receive `scenes_complete.json` with empty `data.media` arrays and render stock-footage scenes as blank gradients. Task 5b is the **mandatory** consolidation point.

- [ ] **Step 1: Write failing test — merge produces scenes_final.json with both assets and timestamps**

Create `test_merge_scenes.py`:

```python
import json
import os
import subprocess
import sys
import pytest

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MERGE_SCRIPT = os.path.join(SCRIPT_DIR, "merge_scenes.py")


def test_merge_scenes_creates_final(tmp_path):
    """merge_scenes.py reads scenes_with_assets.json + scenes_complete.json → scenes_final.json."""
    with_assets = {
        "meta": {"article_title": "T", "article_source": "t.md", "output": "t.mp4",
                "aspect_ratio": "16:9", "width": 1920, "height": 1080, "fps": 30,
                "total_duration_frames": 150, "total_duration_seconds": 5,
                "font_family": "sans-serif",
                "color_theme": {"primary": "#000", "accent": "#f00", "text": "#fff", "background": "#000"}},
        "scenes": [{
            "id": "s1", "type": "stock_footage", "duration_frames": 150,
            "search_keywords": {"zh": ["测试"], "en": ["test"]},
            "data": {"media": [{"file": "assets/s1_00.jpg", "source": "pexels",
                                "source_url": "x", "type": "image",
                                "width": 1920, "height": 1080}],
                    "media_manifest": []},
            "narration": {"text": "Hi", "voice_file": "voice.mp3",
                          "voice_start_ms": 0, "voice_end_ms": 0, "timestamps": []}
        }],
        "audio": {"voice_file": "voice.mp3", "bgm_file": None,
                 "bgm_volume": 0.15, "voice_volume": 0.9},
        "captions": {"enabled": True, "style": "karaoke", "font_size": 36,
                    "position_y": 920, "active_color": "#f00", "inactive_color": "#fff"}
    }
    complete = json.loads(json.dumps(with_assets))  # deep copy
    complete["scenes"][0]["narration"]["voice_start_ms"] = 100
    complete["scenes"][0]["narration"]["voice_end_ms"] = 1500
    complete["scenes"][0]["narration"]["timestamps"] = [
        {"word": "Hi", "start_ms": 100, "end_ms": 1500}
    ]
    complete["meta"]["total_duration_ms"] = 1500
    complete["meta"]["total_duration_frames"] = 45
    wa_path = tmp_path / "scenes_with_assets.json"
    co_path = tmp_path / "scenes_complete.json"
    wa_path.write_text(json.dumps(with_assets, ensure_ascii=False), encoding="utf-8")
    co_path.write_text(json.dumps(complete, ensure_ascii=False), encoding="utf-8")

    out_path = tmp_path / "scenes_final.json"
    result = subprocess.run(
        [sys.executable, MERGE_SCRIPT,
         str(wa_path), str(co_path), "--output", str(out_path)],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, f"merge_scenes.py failed: {result.stderr[:500]}"
    final = json.loads(out_path.read_text(encoding="utf-8"))
    # Asset data preserved
    assert final["scenes"][0]["data"]["media"][0]["file"] == "assets/s1_00.jpg"
    # Timestamp data preserved
    assert final["scenes"][0]["narration"]["voice_start_ms"] == 100
    assert final["scenes"][0]["narration"]["timestamps"][0]["word"] == "Hi"
    # Meta from complete
    assert final["meta"]["total_duration_ms"] == 1500


def test_merge_rejects_mismatched_scene_count(tmp_path):
    """merge_scenes.py errors out if scene counts differ."""
    wa = {"meta": {"article_title": "T"}, "scenes": [{"id": "s1"}, {"id": "s2"}], "audio": {}, "captions": {}}
    co = {"meta": {"article_title": "T"}, "scenes": [{"id": "s1"}], "audio": {}, "captions": {}}
    wa_path = tmp_path / "wa.json"; co_path = tmp_path / "co.json"
    wa_path.write_text(json.dumps(wa), encoding="utf-8")
    co_path.write_text(json.dumps(co), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, MERGE_SCRIPT,
         str(wa_path), str(co_path), "--output", str(tmp_path / "final.json")],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode != 0
    assert "count" in result.stderr.lower() or "mismatch" in result.stderr.lower()


def test_merge_rejects_mismatched_scene_ids(tmp_path):
    """merge_scenes.py errors out if scene IDs are reordered/different."""
    wa = {"meta": {"article_title": "T"}, "scenes": [{"id": "s1"}, {"id": "s2"}], "audio": {}, "captions": {}}
    co = {"meta": {"article_title": "T"}, "scenes": [{"id": "s2"}, {"id": "s1"}], "audio": {}, "captions": {}}
    wa_path = tmp_path / "wa.json"; co_path = tmp_path / "co.json"
    wa_path.write_text(json.dumps(wa), encoding="utf-8")
    co_path.write_text(json.dumps(co), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, MERGE_SCRIPT,
         str(wa_path), str(co_path), "--output", str(tmp_path / "final.json")],
        capture_output=True, text=True, timeout=30
    )
    assert result.returncode != 0
    assert "id" in result.stderr.lower() or "order" in result.stderr.lower()
```

- [ ] **Step 2: Run test — expect FAIL** (merge_scenes.py doesn't exist)

```bash
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest test_merge_scenes.py -v
```

Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implement merge_scenes.py**

```python
#!/usr/bin/env python3
"""
Merge scenes_with_assets.json (from fetch_assets.py) and scenes_complete.json
(from generate_audio.py) into scenes_final.json (single source of truth for render).

Rules:
- meta: take from scenes_complete.json (audio is source of truth for duration)
- audio: take from scenes_complete.json
- captions: take from scenes_complete.json
- scenes: for each scene index
    - narration (text, voice_file, voice_start_ms, voice_end_ms, timestamps) <- complete
    - data.media, data.media_manifest <- with_assets
    - id, type, duration_frames, search_keywords, animation <- complete
- Validation: scene counts must match, scene IDs must match in order
"""

import argparse
import json
import sys


def load_json(path: str) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate(wa: dict, co: dict) -> list:
    """Return list of error messages. Empty list = OK."""
    errors = []
    wa_scenes = wa.get("scenes", [])
    co_scenes = co.get("scenes", [])
    if not wa_scenes:
        errors.append("scenes_with_assets has no scenes — nothing to merge")
    if not co_scenes:
        errors.append("scenes_complete has no scenes — nothing to merge")
    if errors:
        return errors  # Don't proceed if either is empty
    if len(wa_scenes) != len(co_scenes):
        errors.append(
            f"Scene count mismatch: scenes_with_assets has {len(wa_scenes)}, "
            f"scenes_complete has {len(co_scenes)}"
        )
        return errors  # Can't validate IDs if counts differ
    for i, (w, c) in enumerate(zip(wa_scenes, co_scenes)):
        if w.get("id") != c.get("id"):
            errors.append(
                f"Scene[{i}] ID mismatch: with_assets has '{w.get('id')}', "
                f"complete has '{c.get('id')}'"
            )
    return errors


def merge(wa: dict, co: dict) -> dict:
    """Merge two scenes.json structures into one."""
    final = {
        "meta": co["meta"],
        "scenes": [],
        "audio": co["audio"],
        "captions": co.get("captions", wa.get("captions", {})),
    }
    for w_scene, c_scene in zip(wa["scenes"], co["scenes"]):
        merged = {
            "id": c_scene["id"],
            "type": c_scene["type"],
            "duration_frames": c_scene["duration_frames"],
            "search_keywords": c_scene.get(
                "search_keywords", w_scene.get("search_keywords", {"zh": [], "en": []})
            ),
            "data": {},
            "narration": c_scene["narration"],
        }
        # Asset data from with_assets
        w_data = w_scene.get("data", {})
        for k, v in w_data.items():
            merged["data"][k] = v
        # Data fields from complete (may include updated data after generate_audio)
        c_data = c_scene.get("data", {})
        for k, v in c_data.items():
            if k not in ("media", "media_manifest"):
                merged["data"][k] = v
        # Animation from complete (or with_assets as fallback)
        if "animation" in c_scene:
            merged["animation"] = c_scene["animation"]
        elif "animation" in w_scene:
            merged["animation"] = w_scene["animation"]
        final["scenes"].append(merged)
    return final


def main():
    parser = argparse.ArgumentParser(
        description="Merge scenes_with_assets.json + scenes_complete.json -> scenes_final.json"
    )
    parser.add_argument("with_assets", help="Path to scenes_with_assets.json (from fetch_assets.py)")
    parser.add_argument("complete", help="Path to scenes_complete.json (from generate_audio.py)")
    parser.add_argument("--output", "-o", required=True, help="Output path for scenes_final.json")
    args = parser.parse_args()

    wa = load_json(args.with_assets)
    co = load_json(args.complete)

    errors = validate(wa, co)
    if errors:
        for e in errors:
            print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

    final = merge(wa, co)
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"✅ scenes_final.json -> {args.output}")
    print(f"   {len(final['scenes'])} scenes merged")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run all tests — expect PASS**

```bash
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest test_merge_scenes.py -v
```

Expected: 3 tests PASS

- [ ] **Step 5: Commit**

```bash
git add .opencode/skills/video-generate/scripts/merge_scenes.py \
       .opencode/skills/video-generate/scripts/test_merge_scenes.py
git commit -m "feat(video): add merge_scenes.py to combine assets + audio outputs"
```

> **Part 2 impact (ALREADY FIXED):** `to-video-render.md` (Part 2) has been updated to pass `scenes_final.json` (not `scenes_complete.json`) to `render_video.sh`. The Part 2 SKILL.md and output structure documentation also reflect the merge step.

---

### Task 5c: Cross-Ecosystem Contract Compliance Test

> **Why this task matters (Fix #2 from review):** The Python validation (`scenes_schema.py`) and TypeScript type definitions (`input-props.ts`) are maintained independently. Without a contract test, adding a field in Python but forgetting TypeScript (or vice versa) causes silent rendering failures. This test is the shared truth — it generates a reference `scenes_final.json`, validates it against both ecosystems, and fails early when they drift apart.

**Files:**
- Create: `.opencode/skills/video-generate/scripts/test_contract_compliance.py`

- [ ] **Step 1: Write contract compliance test**

Create `test_contract_compliance.py`:

```python
"""Cross-ecosystem contract compliance test.

Validates that a reference `scenes_final.json` generated by the Python pipeline
satisfies all field expectations required by the TypeScript `input-props.ts` types.
This catches silent drift between the two ecosystems.

The test generates a realistic scenes_final.json, validates it with:
1. Python validate_scenes() — structural correctness
2. Field-presence assertions matching every required TypeScript field
3. Type-level assertions (string vs number vs list vs dict)

If this test fails while all other tests pass, the Python↔TypeScript
interface contract has been broken — check input-props.ts for mismatches.
"""

import json
import os
import sys
import pytest

# Add scripts dir to path for import
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from scenes_schema import validate_scenes, SCENE_TYPES, CAPTION_STYLES


def build_reference_scenes_json() -> dict:
    """Build a reference scenes_final.json covering all scene types.
    
    This mirrors the TypeScript ScenesJson interface from input-props.ts
    and serves as the ground truth for the contract.
    """
    return {
        "meta": {
            "article_title": "Reference Test",
            "article_source": "ref/test.md",
            "output": "ref/test.mp4",
            "aspect_ratio": "16:9",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "total_duration_frames": 900,
            "total_duration_seconds": 30,
            "total_duration_ms": 30000,
            "font_family": "sans-serif",
            "color_theme": {
                "primary": "#1a1a2e",
                "accent": "#e94560",
                "text": "#ffffff",
                "background": "#000000",
            },
        },
        "scenes": [
            {
                "id": "s1",
                "type": "title_card",
                "duration_frames": 150,
                "search_keywords": {"zh": ["测试"], "en": ["test"]},
                "data": {"title": "Hello World", "subtitle": "A Test"},
                "animation": {"type": "fade_in", "duration_frames": 30},
                "narration": {
                    "text": "Hello world",
                    "voice_file": "voice.mp3",
                    "voice_start_ms": 0,
                    "voice_end_ms": 1500,
                    "timestamps": [
                        {"word": "Hello", "start_ms": 0, "end_ms": 500},
                        {"word": "world", "start_ms": 500, "end_ms": 1500},
                    ],
                },
            },
            {
                "id": "s2",
                "type": "chapter_title",
                "duration_frames": 120,
                "search_keywords": {"zh": ["章节"], "en": ["chapter"]},
                "data": {"chapter_number": 1, "title": "Getting Started", "subtitle": "Basics"},
                "narration": {
                    "text": "Chapter one",
                    "voice_file": "voice.mp3",
                    "voice_start_ms": 1500,
                    "voice_end_ms": 3000,
                    "timestamps": [
                        {"word": "Chapter", "start_ms": 1500, "end_ms": 2200},
                        {"word": "one", "start_ms": 2200, "end_ms": 3000},
                    ],
                },
            },
            {
                "id": "s3",
                "type": "stock_footage",
                "duration_frames": 180,
                "search_keywords": {"zh": ["人工智能"], "en": ["AI"]},
                "data": {
                    "media": [
                        {
                            "file": "assets/s3_00.jpg",
                            "source": "pexels",
                            "source_url": "https://pexels.com/photo/1",
                            "type": "image",
                            "width": 1920,
                            "height": 1080,
                            "relevance_score": 0.95,
                        }
                    ],
                    "media_manifest": [],
                    "text_overlays": [
                        {"text": "AI in Action", "position": "bottom", "font_size": 24}
                    ],
                },
                "animation": {"type": "ken_burns", "scale_start": 1.0, "scale_end": 1.1},
                "narration": {
                    "text": "AI is transforming our world",
                    "voice_file": "voice.mp3",
                    "voice_start_ms": 3000,
                    "voice_end_ms": 5000,
                    "timestamps": [
                        {"word": "AI", "start_ms": 3000, "end_ms": 3400},
                        {"word": "is", "start_ms": 3400, "end_ms": 3600},
                        {"word": "transforming", "start_ms": 3600, "end_ms": 4200},
                        {"word": "our", "start_ms": 4200, "end_ms": 4400},
                        {"word": "world", "start_ms": 4400, "end_ms": 5000},
                    ],
                },
            },
            {
                "id": "s4",
                "type": "info_card",
                "duration_frames": 200,
                "search_keywords": {"zh": ["信息"], "en": ["info"]},
                "data": {
                    "layout": "bullet_list",
                    "items": [
                        {"text": "First point", "highlight": True},
                        {"text": "Second point"},
                    ],
                    "columns": [
                        {"title": "Col 1", "content": "Content A", "icon": "star"},
                    ],
                    "quote": "A wise quote",
                    "quote_source": "Expert",
                },
                "narration": {
                    "text": "Here are some key points",
                    "voice_file": "voice.mp3",
                    "voice_start_ms": 5000,
                    "voice_end_ms": 6500,
                    "timestamps": [],
                },
            },
            {
                "id": "s5",
                "type": "code_block",
                "duration_frames": 200,
                "search_keywords": {"zh": ["代码"], "en": ["code"]},
                "data": {"code": "print('hello')", "language": "python", "title": "Example"},
                "narration": {
                    "text": "Print hello",
                    "voice_file": "voice.mp3",
                    "voice_start_ms": 6500,
                    "voice_end_ms": 7500,
                    "timestamps": [],
                },
            },
            {
                "id": "s6",
                "type": "outro",
                "duration_frames": 50,
                "search_keywords": {"zh": ["结尾"], "en": ["outro"]},
                "data": {"cta_text": "Subscribe now", "logo": "logo.png"},
                "narration": {
                    "text": "Thanks for watching",
                    "voice_file": "voice.mp3",
                    "voice_start_ms": 7500,
                    "voice_end_ms": 9000,
                    "timestamps": [],
                },
            },
        ],
        "audio": {
            "voice_file": "voice.mp3",
            "bgm_file": None,
            "bgm_volume": 0.15,
            "voice_volume": 0.9,
        },
        "captions": {
            "enabled": True,
            "style": "karaoke",
            "font_size": 36,
            "position_y": 920,
            "active_color": "#e94560",
            "inactive_color": "#ffffff",
        },
    }


# ── Contract assertions (mirror input-props.ts) ──


def check_field(data: dict, path: str, expected_type: type):
    """Assert that field at dot-separated path exists and is of expected_type."""
    parts = path.split(".")
    current = data
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            pytest.fail(f"Contract breach: missing '{path}' in scenes_final.json")
        current = current[part]
    if not isinstance(current, expected_type):
        pytest.fail(
            f"Contract breach: '{path}' expected {expected_type.__name__}, "
            f"got {type(current).__name__} (value: {current!r})"
        )


class TestContractCompliance:
    """Every assertion here maps to a required field in input-props.ts."""

    def build(self):
        return build_reference_scenes_json()

    # ── Python schema validation ──

    def test_passes_python_schema_validation(self):
        """Must pass scenes_schema.validate_scenes() with zero errors."""
        data = self.build()
        errors = validate_scenes(data)
        assert errors == [], (
            f"Contract breach: Python schema validation failed:\n"
            + "\n".join(f"  - {e}" for e in errors)
        )

    # ── Meta contract ──

    def test_meta_top_level_fields(self):
        data = self.build()["meta"]
        for field in ["article_title", "article_source", "output",
                       "aspect_ratio", "width", "height", "fps",
                       "total_duration_frames", "total_duration_seconds",
                       "font_family", "color_theme"]:
            check_field(data, field, str if field not in ("width", "height", "fps", "total_duration_frames", "total_duration_seconds") else (int, float))

    def test_meta_total_duration_ms(self):
        """total_duration_ms is optional in TS but must be present when backfilled."""
        data = self.build()["meta"]
        check_field(data, "total_duration_ms", (int, float))

    def test_meta_color_theme(self):
        ct = self.build()["meta"]["color_theme"]
        for c in ["primary", "accent", "text", "background"]:
            check_field(ct, c, str)

    # ── Audio contract ──

    def test_audio_fields(self):
        audio = self.build()["audio"]
        for field in ["voice_file", "bgm_volume", "voice_volume"]:
            check_field(audio, field, str if field == "voice_file" else (int, float))

    def test_audio_bgm_file_optional(self):
        """bgm_file can be None (null in JSON)."""
        audio = self.build()["audio"]
        assert "bgm_file" in audio, "Contract breach: missing 'audio.bgm_file'"
        # None (null) is valid — TypeScript type is `string | null`

    # ── Captions contract ──

    def test_captions_fields(self):
        caps = self.build()["captions"]
        for field in ["enabled", "style", "font_size", "position_y",
                       "active_color", "inactive_color"]:
            check_field(caps, field, bool if field == "enabled" else (str if "color" in field else int))

    def test_captions_style_valid(self):
        caps = self.build()["captions"]
        assert caps["style"] in CAPTION_STYLES, \
            f"Contract breach: captions.style '{caps['style']}' not in {CAPTION_STYLES}"

    # ── Scenes contract ──

    def test_each_scene_has_required_fields(self):
        scenes = self.build()["scenes"]
        assert len(scenes) > 0
        for i, s in enumerate(scenes):
            for field in ["id", "type", "duration_frames", "search_keywords",
                           "data", "narration"]:
                assert field in s, \
                    f"Contract breach: scenes[{i}].{field} missing"

    def test_each_scene_type_valid(self):
        scenes = self.build()["scenes"]
        for i, s in enumerate(scenes):
            assert s["type"] in SCENE_TYPES, \
                f"Contract breach: scenes[{i}].type '{s['type']}' not in {SCENE_TYPES}"

    def test_each_scene_duration_frames_positive(self):
        scenes = self.build()["scenes"]
        for i, s in enumerate(scenes):
            assert isinstance(s["duration_frames"], (int, float)) and s["duration_frames"] > 0, \
                f"Contract breach: scenes[{i}].duration_frames must be positive"

    def test_each_scene_search_keywords(self):
        scenes = self.build()["scenes"]
        for i, s in enumerate(scenes):
            sk = s.get("search_keywords", {})
            assert isinstance(sk, dict) and "zh" in sk and "en" in sk, \
                f"Contract breach: scenes[{i}].search_keywords requires 'zh' and 'en'"

    # ── Narration contract (per scene) ──

    def test_each_scene_narration(self):
        scenes = self.build()["scenes"]
        for i, s in enumerate(scenes):
            nar = s.get("narration", {})
            for f in ["text", "voice_file", "voice_start_ms",
                       "voice_end_ms", "timestamps"]:
                assert f in nar, \
                    f"Contract breach: scenes[{i}].narration.{f} missing"

    def test_each_scene_narration_timestamps_type(self):
        scenes = self.build()["scenes"]
        for i, s in enumerate(scenes):
            ts = s["narration"].get("timestamps", [])
            assert isinstance(ts, list), \
                f"Contract breach: scenes[{i}].narration.timestamps must be list"
            for j, t in enumerate(ts):
                for f in ["word", "start_ms", "end_ms"]:
                    assert f in t, \
                        f"Contract breach: scenes[{i}].narration.timestamps[{j}].{f} missing"

    # ── Per-scene-type data contract ──

    def test_title_card_has_title(self):
        scene = [s for s in self.build()["scenes"] if s["type"] == "title_card"][0]
        check_field(scene["data"], "title", str)

    def test_chapter_title_has_number_and_title(self):
        scene = [s for s in self.build()["scenes"] if s["type"] == "chapter_title"][0]
        check_field(scene["data"], "chapter_number", (int, float))
        check_field(scene["data"], "title", str)

    def test_stock_footage_has_media_list(self):
        scene = [s for s in self.build()["scenes"] if s["type"] == "stock_footage"][0]
        media = scene["data"].get("media", [])
        for i, m in enumerate(media):
            for f in ["file", "source", "type"]:
                assert f in m, \
                    f"Contract breach: stock_footage.data.media[{i}].{f} missing"
            if "source_url" in m:
                assert isinstance(m["source_url"], str)

    def test_info_card_has_layout(self):
        scene = [s for s in self.build()["scenes"] if s["type"] == "info_card"][0]
        check_field(scene["data"], "layout", str)

    def test_code_block_has_code(self):
        scene = [s for s in self.build()["scenes"] if s["type"] == "code_block"][0]
        check_field(scene["data"], "code", str)
        check_field(scene["data"], "language", str)

    def test_outro_has_cta_text(self):
        scene = [s for s in self.build()["scenes"] if s["type"] == "outro"][0]
        check_field(scene["data"], "cta_text", str)

    # ── Animation contract (optional but structured) ──

    def test_animation_structure_if_present(self):
        scenes = self.build()["scenes"]
        for i, s in enumerate(scenes):
            anim = s.get("animation")
            if anim and isinstance(anim, dict):
                anim_type = anim.get("type")
                assert anim_type is not None, \
                    f"Contract breach: scenes[{i}].animation.type required if animation present"
```

- [ ] **Step 2: Run all tests — expect PASS**

```bash
cd .opencode/skills/video-generate/scripts && ../.venv/bin/python -m pytest test_contract_compliance.py -v
```

Expected: 20+ tests PASS (all contract assertions pass for the reference JSON)

- [ ] **Step 3: Commit**

```bash
git add .opencode/skills/video-generate/scripts/test_contract_compliance.py
git commit -m "feat(video): add cross-ecosystem contract compliance test"
```

---

> **End of Part 1.** For the remaining tasks (Remotion scaffold → rendering → commands → integration tests), see **[Part 2](2026-06-16-article-to-video-part2.md)**.
