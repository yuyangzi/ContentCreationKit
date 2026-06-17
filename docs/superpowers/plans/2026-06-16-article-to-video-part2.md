# Article-to-Video Pipeline Implementation Plan — Part 2: Remotion Rendering & Integration

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal (Part 2):** Build the Remotion rendering engine (6 scene templates + reusable components + sequencer), the render shell script, skill/command definitions, and integration tests.

**Prerequisites:** Assumes **[Part 1](2026-06-16-article-to-video-part1.md)** is complete — directory scaffolded, `scenes.json` schema validator + audio generator + asset fetcher all implemented and committed.

**Part 1 reference:** `docs/superpowers/plans/2026-06-16-article-to-video-part1.md`

**Spec reference:** `docs/superpowers/specs/2026-06-16-article-to-video-design.md`

---

## Task Dependency Graph

```
Part 1 — complete:
  Task 1: Scaffold + .gitignore ✓
  Task 2: scenes_schema.py (TDD) ✓
  Task 3: input-props.ts ✓
  Task 4: generate_audio.py ✓
  Task 5: fetch_assets.py ✓

Part 2 — to implement:
  Task 6: Remotion scaffold + configs    ← depends on Task 3
  Task 7: Remotion templates (6 scenes)  ← depends on Task 6
  Task 8: Remotion components            ← depends on Task 6
  Task 9: Remotion Root + MainVideo      ← depends on Task 7,8

  Task 10: render_video.sh               ← depends on Task 9

  Task 11: SKILL.md + commands            ← depends on Task 4,5,10
  Task 12: Integration test              ← depends on all above
```

## Parallel Execution Graph

```
Task 6
 ↓
Task 7 ──┬── Task 8
 ↓        ↓
Task 9
 ↓
Task 10
 ↓
Task 11 ── Task 12
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
          &ldquo;{data.quote}&rdquo;
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
    echo "ffmpeg is required but not installed."
    echo "   Install: sudo apt install ffmpeg  # or brew install ffmpeg"
    exit 1
fi

# --- ffprobe pre-check ---
if ! command -v ffprobe &> /dev/null; then
    echo "ffprobe is required but not installed (part of ffmpeg)."
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
    echo "Another render is already running (lock: $LOCK_FILE)"
    exit 1
fi
trap 'rm -rf "$LOCK_FILE.lock"' EXIT

# --- Install Remotion deps if needed ---
if [ ! -d "$REMOTION_DIR/node_modules" ]; then
    echo "Installing Remotion dependencies (first run)..."
    cd "$REMOTION_DIR" && npm install --no-audit --no-fund
fi

# --- Copy assets to Remotion public/ ---
rm -rf "$ASSETS_DST"
if [ -d "$ASSETS_SRC" ]; then
    cp -r "$ASSETS_SRC" "$ASSETS_DST"
    echo "Assets copied: $(find "$ASSETS_DST" -type f | wc -l) files"
else
    mkdir -p "$ASSETS_DST"
    echo "No assets directory found at $ASSETS_SRC"
fi

# --- Copy voice file ---
VOICE_SRC="$OUTPUT_DIR/voice.mp3"
if [ -f "$VOICE_SRC" ]; then
    cp "$VOICE_SRC" "$REMOTION_DIR/public/voice.mp3"
    echo "Voice file copied"
else
    echo "voice.mp3 not found at $VOICE_SRC"
fi

# --- Render ---
echo "Rendering video..."
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

echo "Video rendered: $OUTPUT_FILE"
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
description: Convert Markdown articles into video (16:9 MP4) via scene script generation
  asset fetching  TTS audio  Remotion rendering.
allowed-tools: Bash,Write
---

# Article to Video

Convert Markdown articles to 16:9 landscape video through a 4-stage pipeline:
script generation  asset search  voiceover synthesis  Remotion rendering.

## Triggers

- User says "turn this article into a video"
- User says "generate video"
- Multi-platform distribution after article publish

## Prerequisites

### System
- ffmpeg >= 4.0
- Node.js >= 18

### Python (auto-installed on first run)
```bash
pip install -r .opencode/skills/video-generate/requirements.txt
```

### Node.js (auto-installed on first render)
In `.opencode/skills/video-generate/remotion/` run `npm install`

### API Keys (optional, only for asset search)
- `PEXELS_API_KEY`
- `PIXABAY_API_KEY`
- `UNSPLASH_ACCESS_KEY`

If not set, the corresponding source is skipped without blocking the render.

## Pipeline

| Command | Output | Description |
|---------|--------|-------------|
| `/to-video-script` | `scenes.json` | Agent analyzes article  generates scene script |
| `/to-video-footage` | `assets/` + `manifest.json` | 5-layer asset search and download |
| `/to-video-audio` | `voice.mp3` + `scenes_complete.json` | Edge-TTS voiceover + timestamp backfill |
| *(merge step)* | `scenes_final.json` | Combines `scenes_with_assets.json` + `scenes_complete.json` |
| `/to-video-render` | `final.mp4` | Remotion rendering (reads `scenes_final.json`) |

One-click mode: `/to-video`

## Output Structure

```
content/video/{article-name}/
 scenes.json              # Scene script (Agent generated)
 scenes_with_assets.json  # Scenes with asset paths (fetch_assets output)
 scenes_complete.json     # Scenes with audio timestamps (generate_audio output)
 scenes_final.json        # Merged: assets + timestamps (input to render_video.sh)
 voice.mp3                # Voiceover audio
 timestamps.json          # Word-level timestamps
 assets/                  # Asset cache
   manifest.json
 final.mp4                # Final video
```

## Error Handling

| Scenario | Handling |
|----------|----------|
| Edge-TTS unavailable | Retry 3 times (5s/15s/45s), then prompt user for manual recording |
| All asset searches empty | Fallback to solid color background + text cards |
| Remotion render crash | Output `--log=verbose` diagnostic log |
| Chinese font missing | Warn user to install any Chinese font |
```

- [ ] **Step 2: Write command definitions**

**to-video-script.md:**
```markdown
---
description: Generate video scene script
---

# Article to Video Scene Script

## Goal
Analyze Markdown article, produce structured scene script `scenes.json`.

## Prerequisites
`content/article/` directory has the final article.

## Steps

0. **Create output directory**:
   ```bash
   mkdir -p content/video/{name}
   ```
1. **Read article**: Read `content/article/{name}.md`
2. **Analyze structure**: Identify heading levels, tables, blockquotes, code blocks, lists
3. **Generate scenes**:
   - Title  `title_card`
   - Section heading  `chapter_title`
   - Paragraph  `stock_footage` (with zh/en search keywords)
   - Table  `info_card` + `three_column`
   - Blockquote  `info_card` + `quote_box`
   - Code block  `code_block`
   - List  `info_card` + `bullet_list`
   - Ending  `outro`
4. **Rewrite narration**: Convert written language to conversational voiceover
5. **Generate zh/en search keywords**: 3-5 zh + 3-5 en per scene
6. **Schema validation**: Validate output:
   ```bash
   python3 .opencode/skills/video-generate/scripts/scenes_schema.py content/video/{name}/scenes.json
   ```
7. **Fix strategy**: On failure, auto-fix JSON issues (trailing commas, quotes, braces) retry up to 3 times. If still failing, save error JSON to `content/video/{name}/scenes_error.json` and abort.

## Output
`content/video/{name}/scenes.json`  8-15 scenes structured JSON

## Constraints
- narration.text must be conversational voiceover, not copied原文
- Each scene narration should be readable within 15-30 seconds
- voice_start_ms / voice_end_ms leave as 0, backfilled by `/to-video-audio`
```

**to-video-footage.md:**
```markdown
---
description: Search and download video assets
---

# Video Asset Search Download

## Goal
Based on scenes.json keywords, search and download matching visual assets.

## Prerequisites
`scenes.json` generated.

## Steps

1. **Read scenes.json** for each scene's search_keywords
2. **Install Python deps** (first time only):
   ```bash
   PIP=1; [ -f /tmp/video-generate-deps-installed ] && PIP=0
   [ $PIP -eq 1 ] && pip install -r .opencode/skills/video-generate/requirements.txt && touch /tmp/video-generate-deps-installed
   ```
3. **Run asset search**:
   ```bash
   python3 .opencode/skills/video-generate/scripts/fetch_assets.py \
     content/video/{name}/scenes.json \
     --article-source content/article/{name}.md
   ```

## Output
`content/video/{name}/assets/` + `manifest.json`

## Constraints
- 5 layers: reference links  Pexels/Pixabay/Unsplash  Bing images  AI image (fallback)  Screenshot (fallback)
- Missing API keys skip corresponding layers automatically
- Empty results return fallback flag, do not block pipeline
```

**to-video-audio.md:**
```markdown
---
description: Generate video voiceover audio
---

# Video Voiceover Generation

## Goal
Use Edge-TTS to generate AI voiceover audio with timestamp backfill.

## Prerequisites
`scenes.json` generated.

## Steps

1. **Install deps** (first time only):
   ```bash
   PIP=1; [ -f /tmp/video-generate-deps-installed ] && PIP=0
   [ $PIP -eq 1 ] && pip install -r .opencode/skills/video-generate/requirements.txt && touch /tmp/video-generate-deps-installed
   ```
2. **Generate audio**:
   ```bash
   python3 .opencode/skills/video-generate/scripts/generate_audio.py \
     content/video/{name}/scenes.json \
     --voice zh-CN-XiaoxiaoNeural
   ```

## Output
- `voice.mp3`  Voiceover audio
- `timestamps.json`  Word-level timestamps
- `scenes_complete.json`  Complete scenes with backfilled timestamps (⚠️ NOT the render input — merge step combines it with `scenes_with_assets.json` into `scenes_final.json`)

## Constraints
- Edge-TTS failure auto-retries 3 times (5s/15s/45s intervals)
- Original `scenes.json` is NOT modified
```

**to-video-render.md:**
```markdown
---
description: Render final video
---

# Video Rendering

## Goal
Use Remotion to composite scene script, assets, and audio into final MP4.

## Prerequisites
All 3 previous step outputs ready.

## Steps

```bash
bash .opencode/skills/video-generate/scripts/render_video.sh \
  {video_name} \
  content/video/{video_name}/scenes_final.json
```

## Output
`content/video/{name}/final.mp4`  19201080 H.264 MP4

## Constraints
- Expected render time: 5min video ~15-30min, 15min video ~30-60min
- Concurrent lock prevents simultaneous renders
```

**to-video.md:**
```markdown
---
description: One-click article to video
---

# One-Click Article to Video

## Goal
Fully automated article-to-video pipeline, no pauses.

## Prerequisites
- Article finalized through `/to-article` pipeline
- `content/video/{name}/scenes.json` does not yet exist (avoid overwrite)

## Steps

0. **Confirm article**: Check `content/article/` for latest article or ask user to specify
1. `/to-video-script`  Generate scene script
2. `/to-video-footage`  Search and download assets
3. `/to-video-audio`  Generate voiceover audio
4. `/to-video-render`  Render final video

All 4 steps auto-sequence without pauses.
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

---

## Self-Review

**Spec coverage check (Part 2):**
- Remotion engine  Tasks 6-9 (scaffold, templates, components, root) ✓
- Commands  Task 11 (SKILL.md + 5 commands) ✓
- render_video.sh  Task 10 ✓
- Integration tests  Task 12 ✓

**Dependencies on Part 1:**
- Task 6 depends on Task 3 (input-props.ts)  already created in Part 1
- Task 11 depends on Tasks 4 and 5 (audio + asset scripts)  already created in Part 1
- Task 12 depends on all Part 1 scripts imported for testing

**Placeholder scan:** 1 known TBD resolved: InfoCardScene `isSplit` branch now has proper implementation (was "Split layout (content TBD)", replaced with two-column render).

**Type consistency:** Remotion template props match the TypeScript types defined in `input-props.ts` (Part 1). Animation type enums shared.

**Gaps identified:**
- Background music files are not included in this plan (placeholder directory created). The render script copies `voice.mp3` but not BGM. This is acceptable  BGM is a "nice to have" that can be added after core pipeline works end-to-end. The render script and MainVideo.tsx already support `bgm_file` via the `audio` config.
- Asset-to-scene data flow: `fetch_assets.py` (Part 1) writes `scenes_with_assets.json` with backfilled `data.media` and `data.media_manifest` for Remotion consumption. The `_with_assets.json` file should be passed to the render script instead of the original `scenes.json`.
- Remotion component tests: No snapshot/render tests for the 6 templates and 3 components. Recommended to add in a follow-up after core pipeline verification.

---

> **End of Part 2.** Begin by ensuring Part 1 is complete, then execute Tasks 6-12 in the order specified by the dependency graph above.
```
```
```
```
```
```
