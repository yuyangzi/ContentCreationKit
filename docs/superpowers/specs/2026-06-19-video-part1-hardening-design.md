# Article-to-Video Part 1 完善设计

**日期**: 2026-06-19
**状态**: 待实现
**关联**: `docs/superpowers/plans/2026-06-16-article-to-video-part1.md`

---

## 1. 背景

当前文章转视频功能只要求交付 Part 1：数据准备基础设施。Part 1 的目标不是渲染最终 MP4，而是把 Agent 生成的 `scenes.json` 经过素材搜索、音频生成和合并，产出可供后续渲染阶段消费的 `scenes_final.json`。

现有远端实现已经包含 Part 1 的主要文件：

- `.opencode/skills/video-generate/scripts/scenes_schema.py`
- `.opencode/skills/video-generate/scripts/fetch_assets.py`
- `.opencode/skills/video-generate/scripts/generate_audio.py`
- `.opencode/skills/video-generate/scripts/merge_scenes.py`
- `.opencode/skills/video-generate/scripts/test_*.py`
- `.opencode/skills/video-generate/SKILL.md`
- `.opencode/skills/video-generate/references/*.md`
- `.opencode/skills/video-generate/remotion/src/input-props.ts`

审查中发现 Part 1 仍有几个会阻断合并或真实使用的问题：CLI 文档与脚本参数不一致、素材结果没有回填到 `scene.data.media`、换行/尾随空白质量检查不过、测试环境未验证通过。

## 2. 目标

本次完善只让 Part 1 达到可合并、可运行、可验证的状态：

1. `fetch_assets.py` 能按文档命令运行，并支持 Part 1 需要的输入输出路径。
2. 素材搜索/下载结果必须写回 `scenes_with_assets.json` 的 `scene.data.media` 和 `scene.data.media_manifest`。
3. `merge_scenes.py` 合并后生成的 `scenes_final.json` 同时保留素材字段和音频时间戳字段。
4. `SKILL.md`、`references/*.md` 和 Part 1 plan 中的命令、数据流说明与实际脚本一致。
5. Part 1 测试覆盖关键契约，并能在准备好的 Python 环境中通过。
6. `git diff --check` 不再报告 Part 1 相关文件的 CRLF 或尾随空白问题。

## 3. 非目标

以下内容明确不在本次完善范围内：

- 不实现 Remotion 渲染组件、模板、`render_video.sh` 或最终 MP4 输出。
- 不实现 Part 2 的 OpenCode 命令链。
- 不实现 5 层素材搜索中的 AI 生图和 Playwright 截图；Part 1 仍为 3 层搜索：引用链接、素材 API、Bing 图片。
- 不引入新的素材搜索 SDK；继续使用 `requests`、`newspaper3k` 和标准库。
- 不处理未跟踪的文章、选题或其他内容文件。
- 不重构与 video-generate 无关的技能、命令和内容归档。
- 不修改 `generate_audio.py` 的 `match_scene_timestamps()` 字符位置累加逻辑。该函数对 Edge-TTS 输出与原始文本逐字符对齐有依赖，已知边缘情况（数字念读、标点规范化）由 Part 2 处理。

## 4. 设计方案

### 4.1 分支和文件范围

实现应在 `feat/video-scaffold` 上进行，并先同步到 `origin/feat/video-scaffold` 的 Part 1 文件状态。修改范围限制在：

- `.opencode/skills/video-generate/**`
- `.gitignore`
- `docs/superpowers/plans/2026-06-16-article-to-video-part1.md`
- 本 spec 文件后续必要的小修订

如果工作区存在未跟踪内容文件，保持不触碰。

### 4.2 `fetch_assets.py` CLI 契约

脚本应支持以下调用方式：

```bash
python fetch_assets.py content/video/my-video/scenes.json \
  --article-source content/article/my-article.md \
  --outdir content/video/my-video/assets
```

同时为了兼容已有代码，可保留 `--assets-dir` 作为 `--outdir` 的别名。路径解析规则：

- `scenes_path` 必填。
- `--article-source` 可选；未传时回退到 `meta.article_source`。
- `--outdir`/`--assets-dir` 可选；未传时默认为 `scenes.json` 同目录下的 `assets/`。
- `scenes_with_assets.json` 输出到 `scenes.json` 同目录，命名为 `scenes_with_assets.json`，避免 `scenes_with_assets_with_assets.json` 这类链式命名。
- `manifest.json` 输出到 assets 目录。

### 4.3 素材回填数据结构

`process_scene()` 不应只把素材放到临时 `_assets`。每个 scene 都应在 `data` 中保留以下字段：

```json
{
  "data": {
    "media": [
      {
        "file": "assets/s1_00.jpg",
        "source": "pexels",
        "source_url": "https://...",
        "type": "image",
        "width": 1920,
        "height": 1080,
        "status": "downloaded"
      }
    ],
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
  }
}
```

规则：

- `media` 只包含 `status == "downloaded"` 的可用素材，供后续渲染消费。
- `media_manifest` 包含所有搜索候选及下载状态，供调试和人工替换。
- 原有 scene type 的 `data` 字段必须保留。例如 `title_card.data.title`、`info_card.data.layout` 不能被覆盖。
- 没有搜索结果或全部下载失败时，`media` 为空数组，`media_manifest` 记录失败候选；下游可降级为空背景或文字卡。

### 4.4 合并逻辑契约

`merge_scenes.py` 继续把 `scenes_with_assets.json` 和 `scenes_complete.json` 合并为 `scenes_final.json`。合并规则保持清晰：

- `meta`、`audio`、`narration` 以 `scenes_complete.json` 为准。
- `data.media` 和 `data.media_manifest` 以 `scenes_with_assets.json` 为准。
- 其他 `data` 字段默认以 `scenes_complete.json` 为准，但不得丢失仅存在于 `scenes_with_assets.json` 的非媒体字段。
- scene 数量必须一致。
- scene id 顺序必须一致。
- 合并后的 `scenes_final.json` 必须通过 `validate_scenes()` 和跨生态契约测试。

### 4.5 文档一致性

需要同步更新：

- `.opencode/skills/video-generate/SKILL.md` 中的运行命令。
- `references/pipeline-dataflow.md` 中 `scenes_with_assets.json` 和 `scenes_final.json` 的字段说明。
- `references/schemas.md` 中 `media` / `media_manifest` 的字段说明。
- Part 1 plan 中 Task 5、Task 5b、Task 5c 的验收说明。

文档中不得宣称 Part 2 已完成；可明确说明 render 阶段是后续实现。

## 5. 测试方案

### 5.1 新增或强化的测试

`test_fetch_assets.py` 需要覆盖：

1. CLI 支持 `--article-source` 和 `--outdir`。
2. 成功下载的素材写入 `scene.data.media`。
3. 所有候选写入 `scene.data.media_manifest`。
4. 原有 `data` 字段不会被素材回填覆盖。
5. 没有 API key 且 Bing 被 mock 阻断时，输出合法的空 `media` 数组。

`test_merge_scenes.py` 需要覆盖：

1. 合并结果同时保留 `data.media` 和 `narration.timestamps`。
2. 仅存在于 with-assets 侧的非媒体 `data` 字段不会丢失。
3. scene 数量或 id 顺序不一致时失败。

`test_contract_compliance.py` 需要覆盖：

1. 参考 `scenes_final.json` 通过 Python schema。
2. `media` 与 TypeScript `StockMediaItem` 字段一致。
3. `bgm_file: null` 被视为合法。

### 5.2 验证命令

首选验证命令：

```bash
cd .opencode/skills/video-generate/scripts
../.venv/bin/python -m pytest -v
```

如果 skill 私有 venv 不存在，则创建并安装：

```bash
cd .opencode/skills/video-generate
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd scripts
../.venv/bin/python -m pytest -v
```

质量检查：

```bash
git diff --check main...HEAD
```

如果只验证当前工作区未提交改动：

```bash
git diff --check
```

## 6. 验收标准

满足以下条件才认为 Part 1 完善完成：

- `fetch_assets.py --article-source ... --outdir ...` 可运行，输出 `assets/manifest.json` 和 `scenes_with_assets.json`。
- `scenes_with_assets.json` 中**每个 scene** 的 `data` 都包含 `media` 和 `media_manifest` 字段（即使为空数组），与 §4.3 设计一致。Stock footage 类型的 scene 在有可用素材时 `media` 非空。
- `merge_scenes.py` 能生成同时包含素材和音频时间戳的 `scenes_final.json`。
- 完整管线 `fetch_assets.py` → `generate_audio.py`（mock）→ `merge_scenes.py` 在测试样本上跑通，`scenes_final.json` 通过 `validate_scenes()`（由 `test_e2e_pipeline.py` 验证）。
- Part 1 Python 测试通过。
- `git diff --check` 不报告 Part 1 相关文件问题。
- `test_docs_cli_alignment.py` 通过：SKILL.md 中所有 `python ... --flag` 例子都能被对应脚本的 argparse 识别。
- 代码和文档没有扩大到 Part 2 渲染实现。

## 7. 风险与处理

| 风险 | 影响 | 处理 |
|------|------|------|
| `newspaper3k` / `lxml` 安装失败 | 引用链接层不可用，测试环境搭建受阻 | 引用链接层保持可选；缺依赖时跳过真实 newspaper 调用，单元测试用 mock |
| Edge-TTS 依赖网络 | 真实音频生成测试不稳定 | 单元测试优先 mock 重试和 SRT 解析；真实 E2E 可作为可选手动验证 |
| Bing HTML 结构变化 | 第 3 层搜索返回空 | 脚本应输出 warning，不使 Part 1 整体失败 |
| 工作区有未跟踪内容文件 | 容易误提交无关内容 | 实现和提交时只 stage Part 1 文件 |
| CRLF 规范化涉及大量文件 | diff 噪音大 | 只规范 Part 1 范围内新增/修改文件 |

## 8. 推荐实施顺序

1. 同步 `feat/video-scaffold` 到远端 Part 1 状态。
2. 写失败测试：CLI 参数契约与素材回填。
3. 修 `fetch_assets.py`。
4. 写失败测试：merge 保留素材和额外 data 字段。
5. 修 `merge_scenes.py`。
6. 更新 SKILL 和 references。
7. 规范 Part 1 文件换行和尾随空白。
8. 跑 pytest 与 `git diff --check`。

