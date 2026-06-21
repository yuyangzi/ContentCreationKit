# ContentCreationKit — Agents.md

内容创作工作流系统，运行在 OpenCode 之上。专注 AI/科技深度内容，最终发布至微信公众号「玉鸯」。

## 核心管线（命令按序执行）

```
find-popular-topics → review-topics → review-reference → create-draft
  → review-draft → to-article → review-article → to-wechat → image-prompt
```

| 阶段 | 命令 | 输出 |
|------|------|------|
| 选题 | `/find-popular-topics` | `content/topics/{ts}-{topic}.md` |
| 审核主题 | `/review-topics` | `content/reference/{ts}-{topic}.md` |
| 验证资料 | `/review-reference` | 修正意见（对话中） |
| 草稿 | `/create-draft` | `content/draft/{ts}-{topic}.md` |
| 审稿 | `/review-draft` | 审核意见（对话中） |
| 成文 | `/to-article` | `content/article/{ts}-{topic}.md` + 3 标题 |
| 审查 | `/review-article` | 审查意见（对话中） |
| 排版 | `/to-wechat` | `content/WeChat/{ts}-{topic}/article.html` |
| 配图 | `/image-prompt` | 2-3 组 prompt（对话中），图存 `content/images/` |

## .gitignore — 这些目录不在 git 中

`content/draft/`, `content/reference/`, `content/WeChat/`, `content/images/`, `content/video/` — 本地生成，不提交。git 里只有 `content/article/` 和 `content/topics/` 的内容文件是可见的。

## 管线约束

- **按序执行**：每个命令有前置条件，不能跳过。
- **讨论时一次只讨论一个主题**，不能一次性抛多个。
- **数据必须核实**：优先一手来源（官方博客、论文、定价页），交叉验证中英文源。仅凭模型训练数据判断真伪 → 不允许。
- **核实后才改文件**：review 命令只输出意见清单（对话中），用户确认后才修改。
- **草稿使用 `humanizer`+`writer-style`+`content-research-writer`** 技能组合。

## StyleRule（10 条，review-draft 时逐条检查）

1. 砍元叙述 — 不展示作者"组织内容"的过程
2. 弱化绝对断言 — "全都"→"大多数"
3. 砍冗余说明 — 论据点到为止
4. 砍过细例子 — 留一个够用
5. 列表化 — 3+ 并列要点用列表
6. 第一人称不出头 — "我"是底色不是焦点
7. 数据不堆砌 — 完成逻辑支撑就收
8. 标题去术语化 — 不用"赋能/范式/闭环"
9. 删设问修辞 — 不替读者提问
10. 反戏剧化过渡 — 过渡句只做方向转折

详见 `StyleRule.md`。

## 数据准确性（已踩过的坑）

**每个数据点都要核实。区别太大，列出典型错误供警觉：**

- GLM-5.2 价格：中文报道说 ~1/70 of Fable 5 → 实际 ~1/7-1/10，差了 ~7 倍
- DeepSeek 识图：报道说 800×800 图片 → 实际 80×80，分辨率差 100 倍
- Moonshot 融资：~$39 亿 → 实际 $20 亿
- 智谱市值 ~$560 亿 → 实际 528 亿港元（~$67.7 亿），高估 ~8 倍
- 智谱股价 YTD "600%+" → 实际约 +1,700%

**教训**：
- 价格比值自己算一遍，不直觉估算
- 论文数据读全文，不看二手中文报道
- 股价/市值查金融数据源
- 区分"官方来源"和"外部估算"并标注
- 同一篇文章前后一致 — 别在 A 处说用 X 模型、B 处说"都是旧模型"

## Git 规范

- 内容文件（article/topics）直接提交到 main
- 功能开发在 `feat/*` 分支
- 提交风格：中文 + SEMANTIC (`feat:`/`fix:`/`chore:`/`docs:`)
- 按逻辑单元拆分，每提交 ≤ 3 个文件
- 工作流：`status → 规划 → 逐组 stage → commit → 验证`
- 提交后验证 `git log --oneline -5`
- 不自动 push，不自动 commit

## 命令与技能

- **命令定义**：`.opencode/commands/` — 10 个 `.md` 文件
- **自定义技能**：`.opencode/skills/` — 13 个（参见 `skill` tool 列表）
- **Agent 模型配置**：`oh-my-openagent.json`
- **MCP 配置**：Tavily, BraveSearch, BingSearch, TrendsHub, Playwright — 参见 `opencode.jsonc.backup`

## 视频管线（`feat/video-scaffold` 分支）

- 管线：`scenes.json → scenes_with_assets.json → scenes_complete.json → scenes_final.json`
- 严格 TDD，先 FAIL 测试再实现
- `test_docs_cli_alignment.py` 自动验证 SKILL.md 命令与 argparse 一致