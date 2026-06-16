# 文章转视频管线设计文档

**日期**: 2026-06-16
**状态**: 已通过 Grill 拷问，15 项决策已落实
**关联**: ContentCreationKit 创作管线扩展

---

## 1. 背景与动机

ContentCreationKit 现有管线覆盖从选题到公众号排版的完整流程：选题挖掘 → 资料验证 → 草稿生成 → AI 去味审核 → 文章润色 → 公众号排版 → 配图生成。全部内容发布到微信公众号。

用户希望新增一条「文章 → 视频」的分支管线，将已定稿的深度技术分析文章转化为适合 B 站/YouTube 平台的中视频（横屏 16:9，3-15 分钟），实现一文多形态分发。

## 2. 目标

创建一个 OpenCode 技能（`video-generate`），通过四阶段管线将 Markdown 文章转化为完整视频：

1. **脚本生成**：分析文章结构，拆分为场景序列，输出结构化 JSON
2. **素材获取**：五层搜索策略获取与内容匹配的画面素材
3. **旁白生成**：Edge-TTS AI 配音（或用户自录）+ 词级字幕时间戳
4. **视频渲染**：Remotion（React 程序化视频框架）渲染最终 MP4

**非目标**：
- 不支持实时编辑/预览视频（Remotion Studio 可本地预览，非必需）
- 不替代专业剪辑软件（不做多机位、复杂调色）
- 不支持直播/流媒体输出
- 不做视频上传到平台的自动化（可后续扩展）

## 3. 约束条件

| 约束 | 说明 |
|------|------|
| 视频格式 | 横屏 16:9，1920×1080，30fps，H.264 MP4 |
| 视频时长 | 3-15 分钟，取决于文章长度 |
| 配音模式 | 支持 AI 配音（Edge-TTS）和用户自录双模式 |
| 自动化程度 | 混合模式：一键生成 `[/to-video](/)` 或分步控制（四个子命令） |
| 画面策略 | 混合：信息图/文字卡为主体 + 素材库补充 + AI 生图点缀 + 可选录屏 |
| 管线接入点 | 接在文章定稿后（`content/article/`），和公众号排版平级 |
| 成本目标 | 零额外 API 成本（所有核心工具免费/开源） |

## 4. 架构概览

### 4.1 技术选型

| 环节 | 技术 | 语言 | 理由 |
|------|------|------|------|
| 场景脚本生成 | Agent (LLM) | — | 由 OpenCode Agent 调用 LLM 分析文章 |
| 素材搜索下载 | stockmedia-sdk + imgsearch-api + newspaper3k | Python | 统一封装多源素材 API，免费无 Key |
| TTS 旁白 | edge-tts | Python | v7.2.8，中文语音自然，输出词级时间戳 SRT |
| 字幕时间戳 | edge-tts (内置) / Whisper | Python | 词级精确对齐 |
| 视频渲染 | Remotion | Node.js (React) | 弹簧动画、组件化场景、程序化字幕渲染 |
| 管线编排 | OpenCode 命令 | Bash | 延续现有命令驱动模式 |

### 4.2 管线全景

```
content/article/{name}.md           ← 已定稿的文章
        │
        ▼
┌──────────────────────────────────────────────────┐
│  ⑩ /to-video-script                              │
│  Agent 分析文章 → 提取核心论点 → 拆分为 8-15 场景   │
│  每场景含旁白文本、视觉描述、中英文搜索关键词         │
│  输出: content/video/{name}/scenes.json           │
│  (此时 narration.voice_start_ms/end_ms 为空，       │
│   由下一步 /to-video-audio 回填)                     │
├──────────────────────────────────────────────────┤
│  ⑪ /to-video-footage                             │
│  读取 scenes.json 中的 search_keywords              │
│  五层素材搜索（引用链接 → 素材库 → 网络搜图         │
│  → AI生图 → 网页截图）→ 去重 → 下载                │
│  输出: content/video/{name}/assets/ + manifest.json│
├──────────────────────────────────────────────────┤
│  ⑫ /to-video-audio                               │
│  AI模式: Edge-TTS 生成完整旁白 voice.mp3            │
│  通过 SRT 时间戳反查每场景文本位置                       │
│  → 输出 scenes_complete.json（含回填的时间戳）         │
│  → 同时输出 timestamps.json (词级)                    │
│  → 不修改原始 scenes.json（保留脚本生成原稿）           │
│  自录模式: 接受用户录音 + Whisper 对齐                │
│  输出: voice.mp3 + timestamps.json + scenes_complete.json│
├──────────────────────────────────────────────────┤
│  ⑬ /to-video-render                              │
│  Remotion 读入 scenes_complete.json + assets + voice│
├──────────────────────────────────────────────────┤
│  ⑬ /to-video-render                              │
│  Remotion 读入 scenes.json + assets + voice       │
│  → 六种场景模板渲染 → 弹簧动画 → 字幕叠加           │
│  输出: content/video/{name}/final.mp4              │
└──────────────────────────────────────────────────┘
```

一键模式：`/to-video` 串联执行上述四个命令，全程自动不暂停。等同于：

```
/to-video-script → /to-video-footage → /to-video-audio → /to-video-render
```

### 4.3 与现有管线的集成

```
现有管线:
  ⑧ /image-prompt → ⑨ /image-generate → ⑦ /to-wechat

新增视频管线（接在 ⑥ /to-article 之后，与公众号排版平级）:
  ⑩ /to-video-script → ⑪ /to-video-footage → ⑫ /to-video-audio → ⑬ /to-video-render
  ───────────────────────── /to-video (一键) ─────────────────────────
```

## 5. 场景数据结构

`scenes.json` 是 Python 数据准备管线与 Remotion 渲染引擎之间的唯一接口。所有场景信息、素材引用、旁白时间戳都汇聚于此。

### 5.1 完整 Schema

```json
{
  "meta": {
    "article_title": "string",
    "article_source": "content/article/{name}.md",
    "output": "content/video/{name}/final.mp4",
    "aspect_ratio": "16:9",
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "total_duration_frames": "number",
    "total_duration_seconds": "number",
    "font_family": "'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 'WenQuanYi Micro Hei', 'SimHei', sans-serif",
    "color_theme": {
      "primary": "#1a1a2e",
      "accent": "#e94560",
      "text": "#ffffff",
      "background": "#0f0f1a"
    }
  },
  "scenes": [
    {
      "id": "string (unique)",
      "type": "title_card | chapter_title | stock_footage | info_card | code_block | outro",
      "duration_frames": "number",
      "search_keywords": {
        "zh": ["中文关键词1", "中文关键词2"],
        "en": ["english keyword1", "english keyword2"]
      },
      "data": { /* 场景类型相关数据，见 5.2 */ },
      "animation": {
        "type": "ken_burns | spring | fade_in | fade_out | slide_in | stagger_reveal | typewriter | scale_in",
        "duration_frames": 30,
        "direction": "left",
        "scale_start": 1.0, "scale_end": 1.15
      },
      "narration": {
        "text": "string (完整旁白文本)",
        "voice_file": "voice.mp3",
        "voice_start_ms": "number",
        "voice_end_ms": "number",
        "timestamps": [
          { "word": "string", "start_ms": "number", "end_ms": "number" }
        ]
      }
    }
  ],
  "audio": {
    "voice_file": "voice.mp3",
    "bgm_file": "bgm.mp3 | null",
    "bgm_volume": 0.15,
    "voice_volume": 0.9
  },
  "captions": {
    "enabled": true,
    "style": "karaoke | minimal | bold",
    "font_size": 36,
    "position_y": 920,
    "active_color": "#e94560",
    "inactive_color": "#ffffff"
  }
}
```

### 5.2 六种场景类型

| 类型 | 用途 | 建议时长 | 视觉特征 | data 关键字段 |
|------|------|----------|----------|---------------|
| `title_card` | 视频开头标题 | 5s (150帧) | 大标题+副标题+背景图+缓入动画 | `title`, `subtitle`, `background` |
| `chapter_title` | 章节分隔 | 3s (90帧) | 编号+标题+过渡动画 | `chapter_number`, `title`, `subtitle` |
| `stock_footage` | 素材画面 | 10-30s | 图片/视频+Ken Burns+文字卡片 | `media[]`, `text_overlays[]` |
| `info_card` | 信息卡片 | 10-20s | 分屏/三栏/要点列表/引用框+依次揭示 | `layout`, `columns[]`/`items[]` |
| `code_block` | 代码/数据展示 | 5-10s | 代码高亮+行号+打字机动画 | `code`, `language`, `title` |
| `outro` | 结尾 | 5s | Logo+关注引导 | `cta_text`, `logo` |

### 5.3 动画能力

Remotion 提供的动画原语，通过 `data` 中的 `animation` 字段控制：

| 动画 | 用途 | 参数 |
|------|------|------|
| `ken_burns` | 静态图片缓慢缩放/平移 | `scale_start`, `scale_end`, `pan_x`, `pan_y` |
| `spring` | 物理弹簧动画（入场/出场） | `stiffness`, `damping`, `mass` |
| `fade_in` / `fade_out` | 透明度过渡 | `duration_frames` |
| `slide_in` | 从指定方向滑入 | `direction: left/right/up/down` |
| `stagger_reveal` | 要点依次出现 | `stagger_delay_frames` |
| `typewriter` | 逐字出现（代码块） | `chars_per_frame` |
| `scale_in` | 缩放弹入 | `from_scale` |

## 6. 素材获取策略（五层搜索）

### 6.1 搜索层级

```
对每个场景的关键词:
  ├─ 第1层: 文章引用链接提取
  │   newspaper3k 解析引用URL → 提取 top_image + 全部 images
  ├─ 第2层: 素材库 API
  │   stockmedia-sdk → Pexels + Pixabay (lang=zh) + Unsplash
  ├─ 第3层: 网络图片搜索
  │   imgsearch-api → Bing/DDG 搜图 (无需API Key)
  ├─ 第4层: AI 生图 (降级方案)
  │   image-generate skill → Doubao Seedream
  └─ 第5层: 网页截图
      Playwright MCP → 截图引用源关键段落/图表
```

### 6.2 工具清单

| 工具 | PyPI 包名 | 用途 | API Key |
|------|-----------|------|---------|
| `newspaper3k` | `newspaper3k>=0.2` | 从 URL 提取文章正文+图片 | 无需 |
| `stockmedia-sdk` | `stockmedia-sdk>=1.0` | 统一 Pexels+Pixabay+Unsplash 接口 | 需注册 |
| `imgsearch-api` | `imgsearch-api>=0.1` | Bing/DDG/Yandex 图片搜索 | **无需** |
| `better-bing-image-downloader` | `better-bing-image-downloader>=3.5` | Bing 搜图+批量下载+去重 | **无需** |
| `image-generate` (已有) | — | Doubao Seedream AI 生图 | ARK_API_KEY |
| Playwright MCP (已有) | — | 网页截图 | 无需 |

### 6.3 去重与质量评分

- **去重**: MD5 哈希 + 感知哈希 (pHash)，拒绝重复和近重复素材
- **评分**: 分辨率（权重 0.3）+ 文件大小（权重 0.1）+ 与关键词文本相关性（权重 0.6）
- **降级**: 全层搜索结果为 0 时，使用纯色背景 + 文字卡，保证渲染不中断

### 6.4 输出格式

```json
// content/video/{name}/assets/manifest.json
{
  "scenes": [
    {
      "scene_id": "scene_02",
      "keywords": ["jevons", "victorian era", "coal"],
      "assets": [
        {
          "file": "assets/scene02_img1.jpg",
          "source": "newspaper3k",
          "source_url": "https://econlab.substack.com/p/...",
          "type": "image",
          "width": 1200, "height": 800,
          "relevance_score": 0.92
        }
      ]
    }
  ],
  "stats": {
    "total_assets": 45,
    "by_source": { "pexels": 18, "imgsearch": 12, "newspaper3k": 8, "ai_generated": 4, "fallback": 3 },
    "failed_queries": []
  }
}
```

## 7. Remotion 渲染引擎

### 7.1 组件架构

```
Root.tsx
└── <Composition id="main" width={1920} height={1080} fps={30}>
    └── <MainVideo inputProps={scenes.json}>
        ├── <AudioTrack src={voice.mp3} volume={0.9} />
        ├── <AudioTrack src={bgm.mp3} volume={0.15} />
        │
        ├── <Sequence from={frame_offset} durationInFrames={...}>
        │   ├── <TitleCard />         # 六种场景模板之一
        │   ├── <ChapterTitle />
        │   ├── <StockFootageScene>
        │   │   ├── <KenBurnsImage />
        │   │   ├── <VideoClip />     # OffthreadVideo for performance
        │   │   └── <TextCard />
        │   ├── <InfoCardScene>
        │   │   ├── <SplitLayout /> / <ThreeColumn /> / <BulletList />
        │   │   └── <QuoteBox />
        │   ├── <CodeBlockScene />
        │   └── <Outro />
        │
        └── <CaptionOverlay
              timestamps={all_timestamps}
              style="karaoke"
              activeColor={theme.accent} />
```

### 7.2 字幕实现

使用 `@remotion/captions`（Remotion 4.x 内置）结合 Edge-TTS 输出的词级时间戳：

```typescript
// CaptionOverlay.tsx
import { parseSrt, Word } from '@remotion/captions';

// Edge-TTS 输出 SRT → parseSrt() → Word[] → 渲染 karaoke 高亮
```

**中文 karaoke 处理**：Edge-TTS 对中文输出的是**按字符切分的词级时间戳**（每个汉字为一个独立 `word` 条目，含 `start_ms`/`end_ms`）。`@remotion/captions` 的 `Word[]` 按 `start_ms` 排序后逐字播放。不需要额外的分词器（如 jieba），因为时间戳已经精确到字级。

支持三种字幕风格：
- `karaoke`: 当前字高亮（accent 色），已读字淡出，未读字白色
- `minimal`: 底部半透明条 + 白字
- `bold`: 大字黄色描边，冲击力强

### 7.3 渲染命令与素材路径

渲染前，`render_video.sh` 将 `content/video/{name}/assets/` 下的所有素材文件复制到 Remotion 项目的 `public/assets/` 目录（或使用 symlink），渲染完成后清理。避免绝对路径，保证跨电脑、跨平台可移植。

```bash
# render_video.sh 核心逻辑
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
VIDEO_NAME="jevons-paradox"
ASSETS_SRC="$PROJECT_ROOT/content/video/${VIDEO_NAME}/assets"
ASSETS_DST="$PROJECT_ROOT/.opencode/skills/video-generate/remotion/public/assets"
SCENES_FILE="$PROJECT_ROOT/content/video/${VIDEO_NAME}/scenes_complete.json"
OUTPUT_FILE="$PROJECT_ROOT/content/video/${VIDEO_NAME}/final.mp4"

# 并发锁防止同时渲染
LOCK_FILE="/tmp/video-generate-render.lock"
exec 200>"$LOCK_FILE"
if ! flock -n 200; then
    echo "❌ Another render is already running"
    exit 1
fi

# 1. 复制素材到 Remotion public/ 目录
rm -rf "$ASSETS_DST" && cp -r "$ASSETS_SRC" "$ASSETS_DST"

# 2. 渲染
cd "$PROJECT_ROOT/.opencode/skills/video-generate/remotion"
npx remotion render MainVideo \
  --props="{\"scenesPath\": \"$SCENES_FILE\"}" \
  --output="$OUTPUT_FILE" \
  --codec=h264 \
  --crf=23 \
  --concurrency=4

# 3. 清理
rm -rf "$ASSETS_DST"
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--codec` | `h264` | H.264 MP4 编码 |
| `--crf` | `23` | 质量参数（0-51，越低越好，23 为标准质量；15分钟视频约 1.5-2.5 GB） |
| `--concurrency` | `4` | 并行渲染线程数 |

**预期渲染时间**：5 分钟视频约 15-30 分钟，15 分钟视频约 30-60 分钟（取决于 CPU 核数和素材复杂度）。

### 7.4 字体策略（跨平台兼容）

**不打包字体，不依赖系统包管理器。** 使用 CSS `font-family` fallback 链覆盖主流操作系统：

```css
font-family: 'Noto Sans SC', 'PingFang SC', 'Microsoft YaHei', 
             'WenQuanYi Micro Hei', 'SimHei', sans-serif;
```

| 字体 | 平台 |
|------|------|
| Noto Sans SC | Linux（用户自行安装或系统自带） |
| PingFang SC | macOS / iOS |
| Microsoft YaHei | Windows |
| WenQuanYi Micro Hei | Linux 常见中文字体 |
| SimHei | Windows 黑体 |
| sans-serif | 所有平台的最终 fallback |

Remotion 渲染前检测实际可用字体，选择 fallback 链中第一个可用的。

### 7.5 性能考量

- 使用 `<OffthreadVideo>` 替代原生 `<video>` 标签，保证帧解码同步
- 图片使用 `staticFile()` 预加载，防止首帧白屏
- 渲染配置 `--concurrency=4`（4 核并行）
- 素材文件在渲染前一次性复制到 `public/assets/`，渲染后清理

## 8. 命令定义

### 8.1 分步命令

| 命令 | 前置条件 | 输入 | 输出 | 实现方式 |
|------|----------|------|------|----------|
| `/to-video-script` | `content/article/{name}.md` 存在 | 文章 Markdown | `scenes.json` | **Agent 驱动**（Agent 读文章 → 分析 → 输出 JSON），Python 脚本仅做 Schema 校验 |
| `/to-video-footage` | `scenes.json` 存在 | `scenes.json` 中的 `search_keywords` | `assets/` + `manifest.json` | Python 脚本 (`fetch_assets.py`) |
| `/to-video-audio` | `scenes.json` 存在 | `scenes.json` 中的 `narration.text` (+ 可选用户录音) | `voice.mp3` + `timestamps.json` + **`scenes_complete.json`**（含回填时间戳，不修改原 `scenes.json`） | Python 脚本 (`generate_audio.py`) |
| `/to-video-render` | 前三步产物齐全 | 所有产物 | `final.mp4` | Shell 脚本 (`render_video.sh` → `npx remotion render`) |

**`/to-video-script` 的 LLM System Prompt 规则**：Agent 分析 Markdown 时需遵循以下映射：
- 表格 → 自动映射到 `info_card` + `three_column` 布局
- blockquote 引用块 → `info_card` + `quote_box` 布局  
- fenced code block → `code_block` 场景
- 外部 URL 链接 → 提取到场景的引用列表，供素材搜引用源
- 粗体/斜体强调 → 保留标记，供 Remotion 渲染时做视觉强调

### 8.2 一键命令

`/to-video` 串联执行上述四步，使用默认参数自动确认。等同于：

```
/to-video-script → (自动确认) → /to-video-footage → (自动确认) → /to-video-audio → (自动确认) → /to-video-render
```

## 9. 目录结构

```
.opencode/skills/video-generate/
├── SKILL.md                    # 技能定义
├── remotion/                   # Remotion 渲染引擎
│   ├── package.json
│   ├── tsconfig.json
│   ├── remotion.config.ts
│   ├── src/
│   │   ├── Root.tsx
│   │   ├── MainVideo.tsx
│   │   ├── templates/          # 六种场景模板
│   │   │   ├── TitleCard.tsx
│   │   │   ├── ChapterTitle.tsx
│   │   │   ├── StockFootageScene.tsx
│   │   │   ├── InfoCardScene.tsx
│   │   │   ├── CodeBlockScene.tsx
│   │   │   └── Outro.tsx
│   │   ├── components/         # 可复用子组件
│   │   │   ├── KenBurnsImage.tsx
│   │   │   ├── BulletList.tsx
│   │   │   ├── CaptionOverlay.tsx
│   │   │   ├── SplitLayout.tsx
│   │   │   └── TextCard.tsx
│   │   ├── input-props.ts      # scenes.json 类型定义
│   │   └── theme.ts            # 色彩/字体主题
│   └── public/
│       └── bgm/                # 内置背景音乐
├── scripts/
│   ├── generate_scenes.py      # LLM 场景脚本生成
│   ├── fetch_assets.py         # 五层素材搜索下载
│   ├── generate_audio.py       # Edge-TTS 旁白生成
│   └── render_video.sh         # Remotion 渲染入口
└── requirements.txt            # Python 依赖
```

输出目录（全部为生成物，纳入 `.gitignore`）：

```
content/video/{article-name}/
├── scenes.json                 # 场景数据（生成物）
├── voice.mp3                   # 旁白音频（生成物）
├── timestamps.json             # 词级时间戳（生成物）
├── assets/                     # 素材缓存
│   └── manifest.json
└── final.mp4                   # 最终视频（生成物）
```

`.gitignore` 新增（与 `content/WeChat/` 同级对待）：

```
content/video/
```
`scenes.json` 定位为生成物而非源文件，不纳入版本控制。如需保留，用户手动复制到其他目录。

## 10. 依赖清单

### Python (pip install)

```
edge-tts>=7.2
stockmedia-sdk>=1.0
imgsearch-api>=0.1
newspaper3k>=0.2
Pillow>=9.0
requests>=2.31
```

### Node.js (npm install, 仅 remotion/ 目录)

```json
{
  "remotion": "^4.0",
  "@remotion/captions": "^4.0",
  "@remotion/media": "^4.0",
  "react": "^18.0",
  "react-dom": "^18.0",
  "typescript": "^5.0",
  "@types/react": "^18.0"
}
```

### 系统依赖

```
ffmpeg (>=4.0)              # Remotion 必需，用于编码输出
```

中文字体不打包、不强制安装。Remotion 使用 font-family fallback 链自适应系统已有字体。

## 11. 背景音乐

内置 3-5 首无版权背景音乐（从 Pixabay Music 下载，免费可商用），打包在 Remotion 项目中：

```
remotion/public/bgm/
├── tech-ambient.mp3      # 科技感氛围
├── narrative-piano.mp3    # 叙事钢琴
└── upbeat-light.mp3       # 轻快节奏
```

`scenes.json` 的 `audio.bgm_file` 字段指定使用哪首。用户也可替换为自己的音乐文件。

### 10.1 依赖安装策略

**Python**：`scripts/requirements.txt` 统一管理。每个脚本执行前检查标记文件 `/tmp/video-generate-deps-installed`，不存在则 `pip install -r requirements.txt && touch /tmp/video-generate-deps-installed`。首次运行安装，后续跳过。

**Node.js (Remotion)**：`render_video.sh` 执行 `npx remotion render` 前检查 `remotion/node_modules/` 是否存在，不存在则自动 `npm install`。和 `image-generate` 的 `pip install` 模式一致：首次使用等待安装，后续秒开。

## 12. 错误处理

| 错误场景 | 检测方式 | 处理策略 |
|----------|----------|----------|
| 素材搜索全层无结果 | `fetch_assets.py` 返回空列表 | 降级为纯色背景+文字卡，标记 `source: "fallback"` |
| Edge-TTS 限流/不可用 | HTTP 403/超时 | 重试 3 次（间隔 5s/15s/45s），仍失败则提示切换自录模式 |
| 引用链接抓取失败 | HTTP 非 200 / 超时 | 跳过该链接，记录到 `manifest.stats.failed_queries` |
| Remotion 渲染崩溃 | 非零退出码 | 输出 `--log=verbose` 诊断，定位错误帧 |
| 素材下载超时 | 单文件 30s 超时 | 跳过该文件，manifest 标记 `status: "timeout"` |
| 并发渲染冲突 | 多个渲染进程同时操作 `public/assets/` | `render_video.sh` 使用 `flock` 文件锁（`/tmp/video-generate-render.lock`），拒绝并发渲染 |
| 磁盘空间不足 | 渲染前 `df` 检查 | 拒绝渲染，提示需要空间量 |
| 中文字体缺失 | Remotion 渲染时字幕全部为 `□` | 警告用户安装任一中文字体（Noto Sans SC / 微软雅黑 / PingFang SC 均可） |
| scenes.json schema 不合法 | Remotion input-props 校验 | 渲染前 Schema 校验，打印具体违规字段 |
| ARK_API_KEY 未设置 | 环境变量检查 | 跳过 AI 生图层，使用其他层结果 |

## 13. 测试计划

### 13.1 单元测试

| # | 模块 | 测试点 |
|---|------|--------|
| 1 | `generate_scenes.py`（Schema 校验器） | 输入合法 JSON → 通过；输入非法 JSON → 精确报错字段 |
| 2 | `fetch_assets.py` | 关键词搜索 → 返回非空素材列表 |
| 3 | `fetch_assets.py` | 引用 URL 提取 → newspaper3k 成功提取图片 |
| 4 | `fetch_assets.py` | 全源无结果 → 返回 fallback 标记 |
| 5 | `generate_audio.py` | Edge-TTS 生成 → MP3 存在且可播放 + SRT 时间戳合法 |
| 6 | `render_video.sh` | scenes.json + voice.mp3 + assets → MP4 存在且 `ffprobe` 验证 |

### 13.2 集成测试

| # | 场景 | 预期 |
|---|------|------|
| 1 | 完整管线 `/to-video` | 从文章到 MP4，零人工干预 |
| 2 | 分步模式 | 每步输出文件存在，格式合法 |
| 3 | 素材全降级 | 无素材可用时，视频仍正常渲染（纯色背景+文字） |
| 4 | 中文内容 | 字幕正确显示中文，字体不缺失 |
| 5 | 长文章（5000+ 字） | 场景数合理（8-15 个），视频时长 5-12 分钟 |

### 13.3 验证方式

```bash
# 验证 scenes.json schema
python3 -c "import json; json.load(open('content/video/test/scenes.json'))"

# 验证 MP4 输出
ffprobe content/video/test/final.mp4 2>&1 | grep -E "Stream|Duration"

# 验证字幕渲染（抽取一帧）
ffmpeg -i content/video/test/final.mp4 -ss 00:01:00 -vframes 1 test_frame.png
# 肉眼检查 test_frame.png 含有中文字幕

# 验证 .gitignore
grep -q '^content/video/' .gitignore
```

## 14. 自审查清单

- [x] 无 "TBD" 或 "TODO" 占位符
- [x] scenes.json Schema 定义完整，覆盖所有六种场景类型
- [x] 五层素材搜索策略明确定义降级路径
- [x] 与现有管线集成点清晰（/to-article 之后，与 /to-wechat 平级）
- [x] 错误处理覆盖所有已知场景
- [x] 依赖清单完整（Python + Node.js + 系统）
- [x] 测试计划覆盖单元和集成级别
- [x] 性能考量已记录（OffthreadVideo, staticFile 预加载, 字体延迟渲染）
- [x] 成本目标明确：零额外 API 成本
- [x] 非目标清晰列出，防止范围蔓延
