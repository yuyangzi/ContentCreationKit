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
content/ppt/      ❌ gitignore — HTML 演示文稿输出
```

`content/topics/archive/` — 已归档过期主题，不参与 `/find-popular-topics` 的饱和检查。

## 数据验证规则（从踩坑中总结）

**每个数据点都必须核实。不信任模型训练数据。**
- 优先一手来源：官方博客、论文、定价页
- 价格比值自己算，不直觉估算
- 股价/市值查金融数据源（区分"官方"和"外部估算"并标注）
- 论文数据读全文，不看二手中文报道
- 交叉验证中英文源
- 同一篇文章前后一致 — 别在 A 处说用 X 模型、B 处说"都是旧模型"

### 常见数据错误类型（2026年7月踩坑高频项）

数据审核时重点排查以下 6 类错误（按出现频率排序）：

1. **日期错误** — 公告日期、发布日期、事件日期经常差 1-3 天。核实方法：直接找原始公告原文，不要信二手中文报道的日期
2. **数字错误** — 用户数、下载量、点赞数、参数量等数字经常被误报。核实方法：去原文/产品页/arXiv 确认实际数字
3. **来源归属错误** — 数据用了错误的来源（如A公司的数据被归到B公司）。核实方法：交叉验证中英文源
4. **产品名错误** — 某公司产品的正式名称被误写（如 MetaCode 被写成 Code Llama）。核实方法：查官方发布稿
5. **定价错误** — 产品定价档位、金额容易出错（如 $19.99/月 实际是 $250/月 Ultra 档）。核实方法：查定价页
6. **不可验证数据** — 来自付费墙、内部研报、无法溯源的数据。处理原则：**无法独立验证的数据一律删除，不保留"待验证"标记**

### 数据验证工作流

```
review-reference → 派遣 2-4 个 librarian agent 并行验证 → 同时执行 6+ 次 web search 交叉验证
  → 综合输出修正意见清单 → 用户确认 → 执行修改
```

- 每个数据点至少需要 2 个独立来源交叉验证
- 券商研报数据（如国联民生证券的豆包日成本估算）标注"全成本估算"以避免口径歧义
- 付费墙内容标注"（付费墙，仅摘要可见）"
- 第三方引述标注"（第三方引述）"
- **无法独立验证 → 删除，不留"待验证"标记**

## Git 规范

- **分支**：内容文件（article/topics）直接提交到 `main`；功能开发在 `feat/*`
- **提交信息**：中文 + semantic prefix（`feat:`/`fix:`/`chore:`/`docs:`）
- **粒度**：按逻辑单元拆分，每提交 ≤ 3 个文件
- **工作流**：`status → 规划 → 逐组 stage → commit → 验证`
- **不自动 push，不自动 commit**
- **同步规范**：push 前先 `git fetch` 检查远端是否有新提交。若有，先检查路径冲突，再 `git pull --rebase` 保持线性历史，最后 push。**归档操作（移入 archive/）可能由远程触发，rebasing 前务必检查路径重叠**

## StyleRule（review-draft 时逐条检查）

在 `StyleRule.md` 中有完整版。审核草稿时逐条对照：

1. **作者隐身** — 不展示写作过程、不替读者提问、不预告剧情、"我"是底色不是焦点
2. **弱化绝对** — "全都"→"大多数"，不把话说死
3. **论据收敛** — 论据够就收、例子懂了就停、数据到位就止
4. **叙事纯净** — 段不跑题、段间不岔路、过渡不吓人
5. **列表化** — 3+ 并列要点用列表
6. **破折号约束** — 一段最多一处破折号打断，超过即"破折号过载"，改用括号或重新断句

## Python 环境

两个 Python venv，脚本必须从对应 venv 执行：

```bash
# 根目录（通用脚本）
.venv/bin/python

# video-generate 技能
.opencode/skills/video-generate/.venv/bin/python
```

## 主题合并模式（review-topics 阶段高频操作）

当两个或更多 topic 文件高度重叠时，合并为一个文件后再进入管线。操作模式：

1. **grill-me 确认**：使用 grill-me 技能对主题做深度拷问，确认合并方向
2. **用户确认**：展示合并方案（标题、结构、删减内容），用户确认后执行
3. **合并操作**：
   - 以其中一个文件为底稿，吸收其他文件的关键数据作为背景
   - 用 `git rm` 删除旧文件
   - 新建合并后的 topic 文件，时间戳用当前日期
   - 同步更新 reference 文件
4. **典型合并案例**：
   - 两个 AI Labs 芯片自研 topic → 合并为 DeepSeek 推理芯片主线
   - 豆包下架/千问下架/大厂集体砍掉 AI 聊天机器人 → 合并为 AI 拟人化监管执行
   - 世界模型/数字孪生/物理AI + 蚂蚁灵波开源 → 合并为"世界模型两种哲学"

## 审核草稿时 StyleRule 检查重点（按出现频率排序）

2026年7月审核经验，草稿中最常见的 StyleRule 违规（以下按出现频率排序，"破折号过载"已升级为 StyleRule §6 主体规则）：

1. **元叙述**（最频繁）— "写到这里我想到"、"坦白讲"、"讲到这里就绕不开一个问题" → 直接陈述
2. **情绪标签** — "讽刺的是"、"有意思的是"、"尴尬的是" → 直接陈述事实
3. **绝对断言** — "一切"、"完全不是"、"不会" → 弱化为"大多数"、"不是"、"很难保证"
4. **破折号过载** — 一段出现多个破折号打断句子 → 改用括号或重新断句（见 StyleRule §6）
5. **数据堆砌** — 多个论据证明同一个点 → 留一个最有力的
6. **设问修辞** — "为什么要从 XX 说起？" → 直接说 XX

## 主题文件命名与归档

- **时间戳更新**：当 topic 文件被追加更新时，文件名时间戳同步更新为当前日期（`git mv` 重命名）
- **归档机制**：过期 topic 移到 `content/topics/archive/`，不参与 `/find-popular-topics` 的饱和检查
- **归档操作**：由远程或本地执行，注意与远程同步时的路径冲突

## 视频管线（`feat/video-scaffold` 分支）

严格 TDD — 先 fail 再实现。管线阶段：

```
scenes.json → scenes_with_assets.json → scenes_complete.json → scenes_final.json → output.mp4
```

- 5 阶段：LLM Scene Analysis → Schema Validation → TTS Audio (3a) + Asset Search (3b, 并行) → Merge → Render (Remotion)
- `test_docs_cli_alignment.py` 自动验证 SKILL.md 命令与 argparse 一致

## 配图生成经验（image-generate 技能）

- **模型**：Doubao Seedream 4.5（Volces Ark API，OpenAI 兼容接口）
- **输出格式**：API 返回 JPEG，早期脚本校验仅接受 PNG 已修复
- **尺寸**：2048×2048 方形图，prompt 中的"16:9 宽幅"无法通过 API 尺寸参数控制
- **水印**：右下角自动添加平台"AI生成"水印
- **流程**：/image-prompt 生成 2-3 组 prompt（写实摄影/矢量插画/3D 渲染三种风格）→ 选一组调用 image-generate 生成 → 存 `content/images/`

## 命令与技能

- **命令定义**：`.opencode/commands/` — 10 个 `.md` 文件
- **自定义技能**：`.opencode/skills/` — 14 个技能目录（写作、排版、研究、视频等）
- `/create-draft` 必须加载 `humanizer` + `writer-style` + `content-research-writer` 组合
- `/to-wechat` 使用 `wechat-format` skill 的 `scripts/format.py`，默认 `newspaper` 主题
- `article-to-presentation` 技能使用 Python HTML 模板引擎，输出单文件 `slides.html` 到 `content/ppt/`
- `oh-my-openagent.json` 定义 agent 模型映射（visual-engineering 用 MiniMax-M3，ultrabrain/deep 用 DeepSeek-V4-Pro 等）

## Agent 配置要点

- `opencode.jsonc.backup` 包含完整 MCP 配置（Tavily、BraveSearch、BingSearch、Jina、ExaSearch、TrendsHub、Playwright）——但备份文件可能过期，以运行时的实际配置为准
- `.omo/run-continuation/` 存储会话 continuation JSON，由系统自动管理
- `.worktrees/` 在 `.gitignore` 中（git worktree 支持）
- `oh-my-openagent.json` 定义 agent 模型映射（visual-engineering 用 MiniMax-M3，ultrabrain/deep 用 DeepSeek-V4-Pro 等）