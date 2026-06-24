# ContentCreationKit — AGENTS.md

内容创作工作流，运行在 OpenCode 之上。专注 AI/科技深度内容，最终发布至微信公众号「玉鸯」。

## 核心管线（按序执行，不可跳过）

```
/find-popular-topics → /review-topics → /review-reference → /create-draft
  → /review-draft → /to-article → /review-article → /to-wechat → /image-prompt
```

| 命令 | 前置条件 | 输出 |
|------|----------|------|
| `/find-popular-topics` | 无 | `content/topics/{ts}-{topic}.md` |
| `/review-topics` | 已完成 `/find-popular-topics` 或已有确认主题 | `content/reference/{ts}-{topic}.md` |
| `/review-reference` | 已完成 `/review-topics` | 修正意见（对话中），确认后改文件 |
| `/create-draft` | 已完成 `/review-reference` | `content/draft/{ts}-{topic}.md` |
| `/review-draft` | 已完成 `/create-draft` | 审核意见（对话中），逐条检查 StyleRule |
| `/to-article` | 已完成 `/review-draft` | `content/article/{ts}-{topic}.md` + 3 候选标题 |
| `/review-article` | 已完成 `/to-article` | 审查意见（对话中） |
| `/to-wechat` | 已完成 `/to-article` | `content/WeChat/{ts}-{topic}/article.html` |
| `/image-prompt` | 已完成 `/to-article` | 2–3 组 prompt（对话中），图存 `content/images/` |

**约束**：一次只讨论一个主题。review 命令只输出意见清单，用户确认后才改文件。

## 内容目录：哪些在 git 中

```
content/article/  ✅ 提交到 main
content/topics/   ✅ 提交到 main
content/draft/    ❌ gitignore — 本地生成
content/reference/ ❌ gitignore
content/WeChat/   ❌ gitignore
content/images/   ❌ gitignore
content/video/    ❌ gitignore
content/ppt/      ❌ gitignore — Slidev 生成输出
```

`content/topics/old/` — 已归档过期主题，不参与 `/find-popular-topics` 的饱和检查。

## 数据验证规则（从踩坑中总结）

**每个数据点都必须核实。不信任模型训练数据。**
- 优先一手来源：官方博客、论文、定价页
- 价格比值自己算，不直觉估算
- 股价/市值查金融数据源（区分"官方"和"外部估算"并标注）
- 论文数据读全文，不看二手中文报道
- 交叉验证中英文源
- 同一篇文章前后一致 — 别在 A 处说用 X 模型、B 处说"都是旧模型"

## Git 规范

- **分支**：内容文件（article/topics）直接提交到 `main`；功能开发在 `feat/*`
- **提交信息**：中文 + semantic prefix（`feat:`/`fix:`/`chore:`/`docs:`）
- **粒度**：按逻辑单元拆分，每提交 ≤ 3 个文件
- **工作流**：`status → 规划 → 逐组 stage → commit → 验证`
- **不自动 push，不自动 commit**

## StyleRule（review-draft 时逐条检查）

在 `StyleRule.md` 中有完整版。审核草稿时逐条对照：

1. **砍元叙述** — 不展示作者"组织内容"的过程
2. **弱化绝对断言** — "全都"→"大多数"
3. **砍冗余说明** — 论据点到为止
4. **砍过细例子** — 留一个够用
5. **列表化** — 3+ 并列要点用列表
6. **第一人称不出头** — "我"是底色不是焦点
7. **数据不堆砌** — 完成逻辑支撑就收
8. **标题去术语化** — 不用"赋能/范式/闭环"
9. **删设问修辞** — 不替读者提问
10. **反戏剧化过渡** — 过渡句只做方向转折
11. **叙事纪律** — 论点纯净 > 信息全面（段级决策，非段内优化）

## Python 环境

两个 Python venv，脚本必须从对应 venv 执行：

```bash
# 根目录（通用脚本）
.venv/bin/python

# video-generate 技能
.opencode/skills/video-generate/.venv/bin/python
```

## 可用的 npm 命令

`package.json` 中唯一定义的脚本：

```bash
npm run slidev:build   # Slidev 演示文稿构建（neocarbon 主题）
```

依赖在根 `node_modules/`，`.opencode/` 下也有独立 `package.json`（仅 `@opencode-ai/plugin`）。

## 视频管线（`feat/video-scaffold` 分支）

严格 TDD — 先 fail 再实现。管线阶段：

```
scenes.json → scenes_with_assets.json → scenes_complete.json → scenes_final.json → output.mp4
```

- 5 阶段：LLM Scene Analysis → Schema Validation → TTS Audio (3a) + Asset Search (3b, 并行) → Merge → Render (Remotion)
- `test_docs_cli_alignment.py` 自动验证 SKILL.md 命令与 argparse 一致

## 命令与技能

- **命令定义**：`.opencode/commands/` — 10 个 `.md` 文件
- **自定义技能**：`.opencode/skills/` — 14 个技能目录（写作、排版、研究、视频等）
- `/create-draft` 必须加载 `humanizer` + `writer-style` + `content-research-writer` 组合
- `/to-wechat` 使用 `wechat-format` skill 的 `scripts/format.py`，默认 `newspaper` 主题
- `article-to-presentation` 技能使用 Slidev + neocarbon 主题，输出到 `content/ppt/`
- `oh-my-openagent.json` 定义 agent 模型映射（visual-engineering 用 MiniMax-M3，ultrabrain/deep 用 DeepSeek-V4-Pro 等）

## Agent 配置要点

- `opencode.jsonc.backup` 包含完整 MCP 配置（Tavily、BraveSearch、BingSearch、Jina、ExaSearch、TrendsHub、Playwright）——但备份文件可能过期，以运行时的实际配置为准
- `.omo/run-continuation/` 存储会话 continuation JSON，由系统自动管理
- `.worktrees/` 在 `.gitignore` 中（git worktree 支持）
