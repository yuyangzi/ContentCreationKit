# video-generate v2 设计文档（渲染落地 + 契约对齐）

**日期**: 2026-09-11
**状态**: 待评审（已过 design-critic 两轮：Q1–Q10 + Q4/Q2/Q8 快速复审修订）
**关联**: `2026-06-16-article-to-video-design.md`、`docs/superpowers/plans/2026-06-16-article-to-video-part2.md`
**范围**: 补齐 Part 2（Remotion 渲染）使 `/video-generate` 真正产出 MP4；schema 升 v2 消除跨生态漂移；修复 Part 1 脚本缺陷；依赖现代化。

---

## 1. 背景与动机

现有 `video-generate` 技能实现了一条"文章 → 视频"管线的前半段：

- ✅ Part 1 已完成：`scenes_schema.py`、`generate_audio.py`、`fetch_assets.py`、`merge_scenes.py` 及 7 个测试套件（约 50 用例）。
- ❌ Part 2 **从未实现**：`remotion/` 下只有 `src/input-props.ts` 一个类型文件，没有 `package.json`、`Root.tsx`、六种场景模板、`render_video.sh`。
- ❌ 命令缺失：`.opencode/commands/` 中没有任何 `to-video*.md`。
- ❌ Stage 1（文章 → `scenes.json`）无 SOP：`2026-06-16-article-to-video-design.md` §8.1 定义的文章→场景映射规则未进入 `SKILL.md`。

结果：管线终点 `scenes_final.json` 无人消费，技能无法产出视频。同时 Part 1 存在若干缺陷：

1. **TTS 时间轴对齐脆弱**：`generate_audio.py::match_scene_timestamps` 用 `len(narration.text)` 字符累加消耗 SRT 条目，标点/空格/英文数字在 Edge-TTS 输出与原文间不一致，误差逐场景漂移。
2. **`--offline` 不彻底**：`fetch_assets.py` 只清了 API key 和 Bing，`search_reference_links`（newspaper3k）仍会联网。
3. **下载无内容校验**：`download_file` 仅判断 >100 字节，Bing 可能返回 HTML/防盗链页被当图片保存。
4. **契约不一致**：`CodeBlockData.language` 在 TS 必填、`schemas.md` 标 optional、`scenes_schema.py` 不校验；`layout`/`animation.type`/`captions.style` 枚举只在 Python 侧，TS 为 `string`。
5. **测试依赖真实网络**：`test_generate_audio.py` 实时调用 Edge-TTS，CI 必 flaky。
6. **依赖陈旧**：`newspaper3k` 自 2020 年停更，依赖 `lxml`/`nltk`，在 Py3.12+ 安装常失败；`edge-tts` 未锁版本却依赖 7.2.8 的 `SubMaker.feed`/`get_srt` API。
7. **schema 校验偏弱**：不校验 id 唯一性、宽高/fps 正数、枚举、类型、JSON 解析错误；`validate_scenes_file` 遇坏 JSON 直接 traceback。

---

## 2. 目标与非目标

### 2.1 目标

1. **跑通端到端**：`/video-generate` 从已定稿文章产出 1920×1080 H.264 MP4。
2. **契约 v2**：以 TS 类型为机读单一事实源，Python / TypeScript / contract 测试经自动漂移守卫同步，消除人肉对齐。
3. **修复 P1**：TTS 对齐、`--offline` 泄漏、下载校验、枚举/类型校验、测试去网络依赖。
4. **现代化依赖**：用 `trafilatura` 替换 `newspaper3k`，锁定 `edge-tts` 版本。
5. **命令化**：新增 `/to-video`（一键）与四个分步命令，把 Stage 1 的映射规则固化为 SOP。

### 2.2 非目标（本轮）

- BGM 内置音乐与旁白 ducking（保留字段与接口，不实现下载/混音）。
- 素材 pHash 感知去重、多维相关性评分（v2 移除 `relevance_score` 字段，仅按分辨率/source 优先级排序）。
- 视频上传平台自动化。
- 实时预览 / 多机位 / 复杂调色。

---

## 3. 核心决策（来自 grill 拷问）

| # | 决策 | 选择 |
|---|------|------|
| D1 | TTS 对齐策略 | **按场景分段合成**，时间戳天然对齐，废弃字符累加 |
| D2 | 渲染范围 | **全 6 模板 + 字幕**，BGM 延后 |
| D3 | Stage 1 落地 | **命令 SOP + schema 校验**（agent 驱动，失败自动修复重试） |
| D4 | 依赖策略 | **现代化**：trafilatura 替换 newspaper3k |
| D5 | 架构总纲 | **契约 v2 一次性对齐**（方案 A） |
| D6 | 音频/字幕模型 | **逐场景音频 + 场景内局部字幕**，取代全局单轨 + 全局对齐 |

---

## 4. 契约 v2

### 4.0 单一事实源与漂移守卫机制

- **机读事实源**：`remotion/src/input-props.ts` 是唯一事实源。枚举与接口必须以可解析形式声明：枚举用 `as const` 数组（`export const SCENE_TYPES = [...] as const`）或字符串字面量联合类型，接口字段带 `?` 标记可选性。
- **人读文档**：`references/schemas.md` 为面向人的说明，**不参与自动断言**（Markdown 表格解析脆弱，不作为契约来源）。
- **漂移守卫（`test_contract_compliance.py` 必须实现）**：测试以正则解析 `input-props.ts`，提取：
  1. **必填字段集合**（接口中非 `?` 字段）→ 断言与 `scenes_schema.py` 暴露的对应 Python 集合（`META_REQUIRED_FIELDS`/`SCENE_REQUIRED_FIELDS`/`NARRATION_REQUIRED_FIELDS`/`AUDIO_REQUIRED_FIELDS`/`CAPTIONS_REQUIRED_FIELDS`）**逐一相等**，并断言参考 `scenes_final.json` 满足全部必填字段、类型正确；
  2. **枚举集合**（`as const` 数组 / 字面量联合）→ 断言与 `scenes_schema.py` 暴露的对应集合（`SCENE_TYPES`、`CAPTION_STYLES`、`ANIMATION_TYPES`、`INFO_CARD_LAYOUTS`、`LANGUAGES`）**逐一相等**。

两个方向都由"集合相等"约束：只改 TS 或只改 Python（无论增删字段、改可选性、改枚举成员）都会使集合不等而失败。该解析机制是 M1 的明确交付物；M1 出口条件"契约测试通过"即验证此机制已生效。

### 4.1 顶层结构

```json
{
  "meta": { ... },
  "scenes": [ ... ],
  "audio": { ... },
  "captions": { ... }
}
```

### 4.2 meta

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `schema_version` | `"2"` | ✅ | 新增；校验器据此拒绝 v1 |
| `language` | `zh \| en \| bilingual` | ✅ | 新增；消费方：`generate_audio.py` 未传 `--voice` 时据此选默认音色（§6.1 映射表） |
| `article_title` | string | ✅ | |
| `article_source` | string | ✅ | 源 markdown 路径 |
| `output` | string | ✅ | 输出 MP4 路径；`render_video.sh` 消费（无其他输出参数时以此为准，§7.3） |
| `width` / `height` | number | ✅ | 正数（1920 / 1080）；宽高是画面比例的唯一权威 |
| `fps` | number | ✅ | 正数（30） |
| `total_duration_frames` | number | ✅ | 由音频阶段回填 |
| `total_duration_seconds` | number | ✅ | 由音频阶段回填（人读取整） |
| `total_duration_ms` | number | ✅ | 由音频阶段回填（权威毫秒） |
| `font_family` | string | ✅ | fallback 链 |
| `color_theme` | object | ✅ | `{primary, accent, text, background}` |

**移除（相对 v1）**：`aspect_ratio`（与 `width`/`height` 冗余，由宽高推导）。

### 4.3 scenes[]

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | string | ✅ | 唯一，如 `"s1"` |
| `type` | enum | ✅ | 6 种场景类型 |
| `duration_frames` | number | ✅ | **v2 由真实音频时长回填**；Stage 1 输入阶段允许占位 `0`（见 §6.3 校验模式） |
| `search_keywords` | `{zh: string[], en: string[]}` | ✅ | 两键均须为字符串数组 |
| `data` | object | ✅ | 类型相关 |
| `animation` | object | ❌ | 见 4.8 |
| `narration` | object | ✅ | 见 4.5 |

### 4.4 data 字段（按场景类型）

| type | 必填 | 可选 |
|---|---|---|
| `title_card` | `title` | `subtitle`, `background` |
| `chapter_title` | `chapter_number`, `title` | `subtitle` |
| `stock_footage` | — | `media[]`, `text_overlays[]` |
| `info_card` | `layout` | `columns[]`, `items[]`, `quote`, `quote_source` |
| `code_block` | `code`, **`language`** | `title` |
| `outro` | `cta_text` | `logo` |

**枚举锁定**：`info_card.data.layout ∈ {bullet_list, quote_box, three_column, split}`。

**素材消费闭环**：仅 `stock_footage` 场景拥有并消费 `data.media[]`。因此 `fetch_assets.py` **只对 `stock_footage` 场景执行搜索与下载**；其余场景**不写入 `media` 键**（渲染模板不读它，避免无消费方字段，见 §6.2）。schema 仅在 `media` 键存在时校验其内容。

**`background` / `logo` 的生产者约定**：`title_card.data.background`、`outro.data.logo` 均为**可选**，且**不由本管线生产**。若 Stage 1 填写，须指向用户手工预置于视频目录的本地文件；若缺省或文件不存在，模板必须降级（渐变色/纯文字）。spec 不为其定义下载来源，也不做存在性校验。

`media[]` 统一 6 字段 schema：

| 字段 | 类型 | 说明 |
|---|---|---|
| `file` | string | **视频目录相对**路径，如 `"assets/s1_00.jpg"`（相对 `content/video/{name}/`） |
| `source` | enum | `pexels \| pixabay \| unsplash \| bing \| trafilatura` |
| `source_url` | string | 原始页 URL，未知为 `""` |
| `type` | `image \| video` | |
| `width` / `height` | number | 未知为 0 |
| `status` | `downloaded \| failed` | |

**不进入渲染契约的调试产物**：`media_manifest[]`（全部候选含失败）仅保留在 `scenes_with_assets.json` 与 `assets/manifest.json`，**不合并进 `scenes_final.json`**。`relevance_score` 本轮移除（无生产者，避免死代码）。

### 4.5 narration（v2 关键变更）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `text` | string | ✅ | 旁白文本 |
| `audio_file` | string | ✅* | **新增**：场景独立音频路径，如 `"audio/s1.mp3"`，**由音频阶段回填** |
| `duration_ms` | number | ✅* | **新增**：真实音频时长（回填） |
| `timestamps` | `{word,start_ms,end_ms}[]` | ✅* | **局部**毫秒（相对场景起点），由音频阶段回填 |

\* 全部为回填字段，Stage 1 产生的 `scenes.json` 中必须缺省。**路径所有权归音频阶段**：`generate_audio.py` 对 `scene.id` 做文件安全清理后生成 `audio/{safe_id}.mp3`，并把实际路径写入 `narration.audio_file`。Stage 1 不写任何音频路径，从根上消除 agent 手写路径与清理规则不一致的风险。

**移除（相对 v1）**：`narration.voice_file`（由 `narration.audio_file` 取代）、`narration.voice_start_ms`、`narration.voice_end_ms`（v1 全局字段，v2 不再有意义）。

### 4.6 audio（顶层）

| 字段 | 类型 | 说明 |
|---|---|---|
| `voice_file` | `string \| null` | **降级为可选导出物**（拼接总轨，供投稿/字幕），非渲染输入；仅 `--export-voice` 时生成 |
| `bgm_file` | `string \| null` | 本轮仅透传 |
| `bgm_volume` | number | 0.0–1.0 |
| `voice_volume` | number | 0.0–1.0 |

### 4.7 captions

| 字段 | 类型 | 说明 |
|---|---|---|
| `enabled` | boolean | |
| `style` | `karaoke \| minimal \| bold` | 枚举锁定 |
| `font_size` | number | 典型 36 |
| `position_y` | number | 典型 920 |
| `active_color` / `inactive_color` | string | |

### 4.8 animation

| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | enum | `ken_burns \| spring \| fade_in \| fade_out \| slide_in \| stagger_reveal \| typewriter \| scale_in` |
| `duration_frames` / `direction` / `stiffness` / `damping` / `mass` / `scale_start` / `scale_end` / `pan_x` / `pan_y` / `stagger_delay_frames` / `chars_per_frame` / `from_scale` | 可选 | 各动画按需 |

---

## 5. 逐场景音频 + 局部字幕（D6 详解）

### 5.1 数据流

```
scenes.json
  │
  ├──► generate_audio.py  ──► audio/s1.mp3, audio/s2.mp3, ... + audio/s1.srt ...
  │                          scenes_complete.json (audio_file/duration_ms/duration_frames/timestamps 回填)
  │                          [--debug] timestamps.json (调试转储，非契约)
  │
  └──► fetch_assets.py    ──► assets/*  + manifest.json(含全部候选)
                             scenes_with_assets.json (仅 stock_footage 的 data.media + 调试 media_manifest)

scenes_complete.json + scenes_with_assets.json
  │
  └──► merge_scenes.py    ──► scenes_final.json  ──► Remotion
```

### 5.2 为什么放弃全局单轨对齐

v1 把全片拼成一条 `voice.mp3`，再用字符数把 SRT 条目摊到各场景。中文标点、空白、英文数字在 Edge-TTS 输出与原文间不完全一致，误差会累积漂移，且 `match_scene_timestamps` 与 `scene_words_map` 存在两套独立累加逻辑。

v2 每个场景独立合成，其 WordBoundary 天然就是**场景局部**时间戳；Remotion 每个场景一个 `<Sequence>`，内嵌该场景音频与局部字幕。收益：

- 删除全部字符累加对齐代码（`match_scene_timestamps`、`scene_words_map`）。
- 画面切换点 = 音频边界 = 字幕边界，三者严格一致。
- `duration_frames` 来自真实音频，不再按字符比例估算。
- 无需 ffmpeg 拼接音频（`voice.mp3` 仅在显式请求时导出）。

### 5.3 duration_frames 计算与失败路径

```
duration_ms_i         = ffprobe(audio_i)（权威）
                        └─ ffprobe 不可用 → SRT 末条 end_ms + TAIL_MS
duration_frames_i     = max(MIN_DURATION_FRAMES,
                            ceil(duration_ms_i / 1000 * fps) + padding_frames)
total_duration_ms     = Σ duration_ms_i            # 音频内容总长（权威，供人读与断言）
total_duration_frames = Σ duration_frames_i         # 时间轴总帧数（Remotion 使用）
timeline_ms           = total_duration_frames * 1000 / fps
total_duration_seconds = round(total_duration_ms / 1000)
```

**硬失败规则**：若某场景 ffprobe 不可用**且** SRT 为空（Edge-TTS 偶发非标准时间戳），**不得**用 0 回填。`generate_audio.py` 必须对该场景报错退出并提示"无法确定音频时长"。这消除了"每场景 1 秒、旁白被截断"的静默错误视频。

**时间轴与音频的关系**：因 `ceil` 与 `MIN_DURATION_FRAMES`，恒有 `timeline_ms ≥ total_duration_ms`（画面不会截断音频）。上界为：

```
0 ≤ timeline_ms − total_duration_ms
  ≤ n * (1000/fps)                                              # 每场景 ceil 最多多 1 帧
  + Σ_i max(0, MIN_DURATION_FRAMES*1000/fps − duration_ms_i)    # 短场景被抬到 30 帧的补偿
  + n * padding_frames * 1000/fps
```

**验收断言**（替代 v1 的 `|timeline_ms − total_duration_ms| ≤ 50ms`；后者对含 `ceil`/`MIN` 的多场景视频在数学上不可满足）：

1. **不截断**：每个场景 `duration_frames_i * 1000/fps ≥ duration_ms_i − 1ms`。
2. **上行受控**：`timeline_ms − total_duration_ms` 落在上式上界内。
3. **渲染一致**：`|ffprobe(final.mp4).duration*1000 − timeline_ms| ≤ 100ms`（编码产物与 spec 时间轴一致）。

`MIN_DURATION_FRAMES = 30`，`TAIL_MS = 200`，`padding_frames` 默认 0。

---

## 6. Python 变更

### 6.1 `generate_audio.py`

- **逐场景合成**：对每个 `scene.narration.text` 独立调用 Edge-TTS，输出 `audio/{safe_id}.mp3`（`safe_id` 由 `scene.id` 文件安全清理得到）。
- **路径回填**：把实际音频路径写入 `narration.audio_file`（路径所有权在音频阶段，见 §4.5）。
- **局部时间戳**：每场景独立 `SubMaker`，产出相对该场景的 `timestamps`。
- **逐段重试**：`RETRY_DELAYS=[5,15,45]`，失败仅重试该场景，不重跑全片。
- **真实时长**：优先 `ffprobe`，不可用则 SRT 兜底；两者皆无则硬失败（§5.3）。
- **回填**：写 `scenes_complete.json`（`narration.audio_file/duration_ms/timestamps` + `duration_frames` + `meta.total_duration_*`）。
- **保留字幕**：每场景导出 `audio/{safe_id}.srt`，供平台投稿（外部消费方）。
- **默认音色**：未传 `--voice` 时按 `meta.language` 选择——`zh` → `zh-CN-XiaoxiaoNeural`、`en` → `en-US-AriaNeural`、`bilingual` → `zh-CN-XiaoxiaoNeural`。
- **可选导出**：`--export-voice` 时拼接各段为 `voice.mp3`（需 ffmpeg），并写顶层 `audio.voice_file`。
- **调试**：`--debug` 时额外写 `timestamps.json`（非契约产物）。
- **新增参数**：`--rate`、`--pitch`、`--volume`（映射 Edge-TTS SSML）。
- 解析器实现需兼容 `edge-tts==7.2.8` 的 `SubMaker.feed`/`get_srt`。

CLI：

```bash
$VENV_PYTHON $SCRIPTS_DIR/generate_audio.py \
  content/video/my-video/scenes.json \
  --outdir content/video/my-video \
  [--voice zh-CN-XiaoxiaoNeural] \
  [--rate +0%] [--pitch +0Hz] [--export-voice] [--debug]
```

### 6.2 `fetch_assets.py`

- **抓取范围**：仅处理 `type == "stock_footage"` 的场景；其余场景**不写入 `media` 键**（消费闭环，见 §4.4）。
- **离线彻底化**：模块级 `OFFLINE` 标志，在 `search_reference_links`、Pexels、Pixabay、Unsplash、Bing 每个入口统一短路；`--offline` 置真。
- **trafilatura 替换 newspaper3k**：用 `trafilatura.extract(url, output_format="json", include_images=True)` 提取正文（`text`）与图片候选（JSON 的 `images` 键）。**必须显式指定 `output_format="json"`**——默认 `txt` 输出会丢弃图片节点导致第一层静默归零。失败跳过并记入 manifest。移除 `newspaper3k` 依赖与 lxml 系统包要求。M1 增加一条 `@pytest.mark.network` 的真实页面图片提取冒烟测试。
- **下载校验**：`download_file` 增加
  - `Content-Type` 前缀校验（`image/` 或 `video/`）；
  - magic bytes 校验（JPEG `FFD8FF`、PNG `89504E47`、GIF、WEBP `RIFF....WEBP`、MP4 `ftyp`）；
  - 体积上限（默认 50 MB）；
  - 超时 + 1 次重试。
- **结果排序**：按 `(分辨率≥1920 优先, source 优先级)` 排序后截断 `max_per_scene`。source 优先级：`trafilatura > pexels/pixabay/unsplash > bing`。
- **跨场景去重**：全局 `seen` 集合，避免同一 URL 被多场景重复下载。
- 扩展名与文件名规范化（剥离 query，真实类型以下载后 magic bytes 为准）。

CLI 保持：`--outdir`（别名 `--assets-dir`）、`--article-source`、`--offline`。

### 6.3 `scenes_schema.py`（v2）

新增校验：

- `meta.schema_version == "2"`（否则报"需迁移到 v2"）。
- `meta.language` 枚举；`width/height/fps` 为正数。
- `scenes[].id` 唯一。
- `search_keywords.zh/en` 均为字符串数组。
- `info_card.data.layout` 枚举；`code_block.data.language` 必填。
- `animation.type` 枚举（若提供 animation）。
- `captions.style` 枚举；`audio.*_volume` ∈ [0,1]。
- 字段类型（非仅键存在）。
- `validate_scenes_file`：捕获 `FileNotFoundError` / `json.JSONDecodeError`，返回友好错误而非 traceback。

**校验模式**：`--stage input|final`（**默认 `input`**，因 Stage 1 自动修复循环是最高频路径；merge/render 流程显式传 `--stage final`）。

- `input`（Stage 1 产物）：允许 `duration_frames == 0`、允许缺省 `narration.audio_file`/`duration_ms`/`timestamps`、允许 `meta.total_duration_*` 为 0。
- `final`（`scenes_final.json`）：上述字段必须已回填且 `duration_frames > 0`。

CLI 增加 `--json` 输出结构化错误列表（供 `/to-video-script` 自动修复循环消费）。

### 6.4 `merge_scenes.py`

适配 v2：

- `meta` / `audio` / `captions` 取自 `scenes_complete.json`。
- `narration` 全字段取自 `scenes_complete.json`（含 `audio_file`/`duration_ms`/局部 `timestamps`）。
- `data.media` 取自 `scenes_with_assets.json`；其余 `data` 字段以 complete 为准、补 wa-only 字段。**不把 `media_manifest` 合并进 final**（调试产物仅留在 with_assets/manifest，见 §4.4）。
- `duration_frames` 取自 complete（真实音频）。
- 保持 count/ID 一致性校验，错误信息描述化。

### 6.5 依赖与配置清理

- `requirements.txt`：新增 `trafilatura`；锁定 `edge-tts==7.2.8`；移除 `newspaper3k`、`Pillow`（4 脚本零 import）。
- `scenes_schema.py` 暴露顶层**枚举集合**（`SCENE_TYPES`/`CAPTION_STYLES`/`ANIMATION_TYPES`/`INFO_CARD_LAYOUTS`/`LANGUAGES`）与**必填字段集合**（`META_REQUIRED_FIELDS`/`SCENE_REQUIRED_FIELDS`/`NARRATION_REQUIRED_FIELDS`/`AUDIO_REQUIRED_FIELDS`/`CAPTIONS_REQUIRED_FIELDS`），供契约测试与 TS 双向比对。
- 更新 `AGENTS.md`：命令数（13 → 18）、核心管线表新增视频分支、`content/video/` 说明。

---

## 7. Remotion 渲染工程（Part 2 落地）

### 7.1 目录结构

```
remotion/
├── package.json          # remotion@^4, @remotion/cli, react, react-dom
├── tsconfig.json
├── remotion.config.ts
├── src/
│   ├── index.ts          # 入口：registerRoot(RemotionRoot)
│   ├── Root.tsx          # <Composition id="MainVideo" calculateMetadata>
│   ├── MainVideo.tsx     # 逐场景 <Sequence>，内嵌音频+模板+字幕
│   ├── input-props.ts    # 契约 v2 类型（机读事实源）
│   ├── theme.ts          # 解析 color_theme / font_family
│   ├── templates/        # TitleCard, ChapterTitle, StockFootageScene,
│   │                     # InfoCardScene, CodeBlockScene, Outro
│   └── components/       # CaptionOverlay, KenBurnsImage, TextCard
└── public/               # 渲染期临时挂载 assets/ + audio/；trap EXIT 清理；.gitignore
```

### 7.2 MainVideo 结构

```tsx
// 逐场景 Sequence：from 为累计时长
<Sequence key={scene.id} from={offset} durationInFrames={scene.duration_frames}>
  <Audio src={staticFile(scene.narration.audio_file)} volume={audio.voice_volume} />
  <SceneRenderer scene={scene} meta={meta} />
  <CaptionOverlay timestamps={scene.narration.timestamps}
                  config={captions} fontFamily={theme.fontFamily} />
</Sequence>
```

- 字幕使用**局部** `start_ms/end_ms`，无需全局时间换算。
- `Root.tsx` 通过 `calculateMetadata` 以 `meta.fps/width/height/total_duration_frames` 设定 Composition。
- 模板实现参照 `plans/2026-06-16-article-to-video-part2.md` Task 6–9 的代码骨架，但 props 类型升级为 v2、字幕改为场景局部。

### 7.3 `render_video.sh`

- 参数：`render_video.sh <video_name> <scenes_final.json>`；输出路径取 `meta.output`，缺省 `<video-dir>/final.mp4`。
- 前置检查：`ffmpeg` / `ffprobe` / `node`（缺则友好报错）。
- 并发锁：`mkdir` 锁（或 `flock`），拒绝并发渲染。
- 依赖自举：`remotion/node_modules` 缺失则 `npm install`。
- 素材挂载：`content/video/{name}/assets` → `remotion/public/assets`，`audio/*` → `remotion/public/audio`。`media.file` 为视频目录相对路径 `assets/...`，故 `staticFile(media.file)` 可解析。**`trap ... EXIT` 同时清理锁与挂载目录**，异常退出也不残留。
- `remotion/public/assets/`、`remotion/public/audio/`、`remotion/public/voice.mp3` 加入 `.gitignore`，避免渲染残留污染 git 状态。
- 渲染命令（Remotion 4 位置参数语法，入口显式指明）：

  ```bash
  npx remotion render src/index.ts MainVideo <output.mp4> \
    --props=<scenes_final.json> --codec=h264 --crf=23 \
    --concurrency=${REMOTION_CONCURRENCY:-4}
  ```

  （实施时先以 `npx remotion render --help` 核对当前版本语法。）
- 收尾：`ffprobe` 校验时长/分辨率并打印体积。

---

## 8. 命令与 SOP

新增 5 个命令文件：

| 命令 | 输入 | 输出 | 实现 |
|---|---|---|---|
| `/to-video` | 已定稿文章 | `final.mp4` | 串联四步（含 merge），自动确认 |
| `/to-video-script` | `content/article/{name}.md` | `scenes.json` | Agent SOP + `scenes_schema.py --stage input` 校验 |
| `/to-video-footage` | `scenes.json` | `assets/` + `manifest.json` + `scenes_with_assets.json`（仅 stock_footage 下载） | `fetch_assets.py` |
| `/to-video-audio` | `scenes.json` | `audio/*.mp3` + `audio/*.srt` + `scenes_complete.json`（`--debug` 额外 `timestamps.json`） | `generate_audio.py` |
| `/to-video-render` | 全部产物 | `final.mp4` | `render_video.sh`（先 merge，`--stage final` 校验） |

**产物消费方**：`scenes_complete.json` → merge；`audio/*.mp3` → Remotion；`audio/*.srt` → 外部投稿字幕；`assets/manifest.json` → 人工排障/替换；`timestamps.json`（`--debug`）与 `scenes_error.json` → **终态诊断产物，供人/agent 复盘**，管线不重读（修复循环消费的是 `scenes_schema.py --json` 的即时 stdout；重跑 `/to-video-script` 时重新读文章，不读 error 文件）。

`/to-video-script` 的 SOP 必须写入 `2026-06-16-article-to-video-design.md` §8.1 的映射规则：

- 表格 → `info_card` + `three_column`
- blockquote → `info_card` + `quote_box`
- fenced code block → `code_block`（必带 `language`）
- 列表 → `info_card` + `bullet_list`
- 标题 → `title_card` / `chapter_title`；结尾 → `outro`；正文段落 → `stock_footage`
- 旁白：书面语转口语，单场景 15–30 秒可读
- 关键词：每场景 3–5 中文 + 3–5 英文
- 校验失败：按 `scenes_schema.py --json --stage input` 错误自动修复，最多重试 3 次；仍失败写 `scenes_error.json`（终态诊断）并中止

`SKILL.md` 更新：管线图（逐场景音频）、命令表、v2 字段、测试数、常见坑（trafilatura `output_format`、`--offline`、ffmpeg/Node 前置、`--stage` 默认）。

---

## 9. 测试与验证

### 9.1 套件升级（v2）

| 套件 | 变更 |
|---|---|
| `test_scenes_schema.py` | 增加 v2 字段、枚举、类型、唯一 id、坏 JSON、`--stage` 两模式用例 |
| `test_generate_audio.py` | 移除真实网络调用，mock Edge-TTS；保留 1 条 `@pytest.mark.network` 手动用例；验证逐场景产物 + 局部时间戳 + ffprobe 时长回填 + SRT/ffprobe 双缺失硬失败 |
| `test_fetch_assets.py` | 增加 `--offline` 彻底断网、magic bytes/content-type 校验、排序、跨场景去重、仅 stock_footage 抓取用例 |
| `test_merge_scenes.py` | 适配 v2 narration 字段；断言 final 不含 `media_manifest` |
| `test_contract_compliance.py` | **解析 `input-props.ts`**（必填字段 + `as const` 枚举），断言字段/枚举集合与 Python 双向相等，且参考 JSON 满足必填/类型（§4.0 漂移守卫） |
| `test_docs_cli_alignment.py` | 覆盖 5 个命令与新增 CLI 参数 |
| `test_e2e_pipeline.py` | offline fetch → 合成 complete(v2) → merge → `--stage final` validate |

网络类冒烟（`@pytest.mark.network`）：trafilatura 真实页面图片提取（§6.2）。

### 9.2 新增

- **TypeScript 类型检查**：`cd remotion && npx tsc --noEmit`。Node/依赖是渲染硬前置，M2 出口**必须真实执行**；仅 `node_modules` 确实缺失时 pytest 显式 skip 并在输出中列出，不计为通过。
- **渲染冒烟**：`@pytest.mark.manual` 的真实渲染，`ffprobe` 校验 `final.mp4` 存在、分辨率 1920×1080，并通过 §5.3 的三项时间轴断言。
- **中文字幕抽帧**（手动）：`ffmpeg -ss` 抽帧肉眼确认中文字形非 `□`。

### 9.3 验收标准

1. 一条真实文章经 `/to-video` 产出可播放 MP4；分辨率 1920×1080；通过 §5.3 的三项时间轴断言（不截断音频、上行受控、编码与 `timeline_ms` 偏差 ≤100ms）。
2. 所有非 `manual`/`network` 测试在无网络、无 API key 环境下通过。
3. `tsc --noEmit` 通过。
4. `scenes_schema.py` 对 v2 合法样例（`--stage input` 与 `--stage final`）零错误，对每类违规精确报字段。
5. 契约测试能通过解析 `input-props.ts` 检出人为注入的字段/枚举漂移（负向验证）。

---

## 10. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 契约升 v2 不兼容旧 `scenes.json` | 旧产物无法渲染 | README/SKILL 标注；校验器对 v1 明确报"需迁移" |
| 分段 TTS 触发 Edge-TTS 限流 | 合成中断 | 逐段退避重试；失败仅重跑该段 |
| ffprobe 与 SRT 同时不可用 | 时长错误 | §5.3 硬失败规则，禁止 0 回填 |
| trafilatura 默认输出丢弃图片 | 第一层静默归零 | 显式 `output_format="json"` + `@pytest.mark.network` 冒烟 |
| 渲染残留污染 git | 工作区脏 | `trap EXIT` 清理挂载 + `.gitignore` |
| ffmpeg/Node 未安装 | 无法渲染/回填时长 | 前置检查，友好报错 |
| 逐场景音频增加文件数量 | 目录变乱 | 统一 `audio/` 子目录，文件名 = safe scene id |
| Remotion 版本 API 漂移 | 渲染失败 | 锁定 `remotion@^4.0.0`；实施时核对 CLI 语法；`tsc` 兜底 |
| 字幕字体缺失 | 中文显示 `□` | fallback 链 + 抽帧手动校验 + SKILL 提示安装字体 |

---

## 11. 里程碑（单 Spec，分节实施）

| 里程碑 | 内容 | 出口条件 |
|---|---|---|
| **M1 契约 v2 + Python** | schema v2、`input-props.ts` v2（可解析枚举+必填字段集合）、漂移守卫测试、`generate_audio.py` 分段、`fetch_assets.py` 硬化、`merge_scenes.py` 适配、依赖清理 | 全部非网络测试通过；`scenes_final.json` 通过 `--stage final` 校验；契约守卫负向验证生效 |
| **M2 Remotion 工程** | 工程脚手架（含 `src/index.ts`）、6 模板、3 组件、`Root`/`MainVideo`、`render_video.sh`、`.gitignore` | `tsc --noEmit` 真实执行通过；手动冒烟产出一条 MP4，通过 §5.3 三项时间轴断言 |
| **M3 命令 + 端到端** | 5 个命令、`/to-video-script` SOP、`SKILL.md` 与 `AGENTS.md` 更新 | `/to-video` 一条文章全自动出片；验收标准全绿 |

每个里程碑各自生成实施计划（`/esdp` 执行）。

---

## 12. 自审查清单

- [x] 无 TBD / TODO 占位符
- [x] 契约 v2 字段、枚举、必填项定义完整
- [x] 单一事实源含**可执行**漂移守卫机制：枚举与必填字段**双向**比对（解析 TS，非人肉同步）
- [x] narration 字段移除清单完整、回填字段所有权明确（音频阶段生成并回填路径）
- [x] 素材消费闭环限定 `stock_footage`；`background`/`logo` 明确为不由管线生产的可选字段；无消费者字段（`relevance_score`）与产物（`media_manifest` 入 final）已清理
- [x] 时长定义自洽：`total_duration_ms`/`total_duration_frames`/`timeline_ms` 关系与三项验收断言明确，废弃不可满足的 ±50ms
- [x] `scenes_error.json` / `timestamps.json` 定性为终态诊断，无循环消费方
- [x] 渲染命令语法/入口文件/挂载路径/异常清理/`.gitignore` 明确
- [x] `meta` 无消费者字段已清理或赋予消费方（`output`→render；`language`→TTS 音色；移除 `aspect_ratio`）
- [x] Python / TypeScript / 测试三方变更均有对应章节
- [x] 5 个命令、Stage 1 SOP、AGENTS.md 更新明确
- [x] 测试策略覆盖单元 / 契约 / 类型 / 端到端 / 手动
- [x] 风险与缓解、验收标准、里程碑清晰
- [x] 非目标明确，防止范围蔓延
