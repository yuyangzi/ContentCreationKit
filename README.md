# ContentCreationKit

**AI 驱动的内容创作工具包 — 从选题到发布的完整管线**

基于 [OpenCode](https://opencode.ai) 构建，集成搜索、写作、排版 Agent 工作流，专注 AI/科技深度内容，最终发布至微信公众号「玉鸯」。

---

## 概述

ContentCreationKit 是一套运行在 OpenCode 之上的内容创作工作流系统。它将选题挖掘、深度研究、草稿生成、AI 去味审核、文章润色、公众号排版、配图生成等环节组织为一条清晰的创作管线，全部通过命令驱动。

> 简而言之：**聚焦内容本身，流程交给工具链。**

**新会话先读 `AGENTS.md`** — 包含管线顺序、数据验证规则、Git 规范、StyleRule 检查清单等完整的代理工作指南。

---

## 核心管线（按序执行，不可跳过）

```
/find-popular-topics → /review-topics → /review-reference → /create-draft
  → /review-draft → /to-article → /review-article → /to-wechat → /image-prompt
```

| 阶段 | 命令 | 说明 | 输出 |
|------|------|------|------|
| ① 选题 | `/find-popular-topics` | 在知乎、微博、36氪等平台挖掘热门话题 | `content/topics/{ts}-{topic}.md` |
| ② 审核 | `/review-topics` | 深度拷问主题，收集背景资料，支持主题合并 | `content/reference/{ts}-{topic}.md` |
| ③ 验证 | `/review-reference` | 派遣 2-4 个 agent 并行验证每条数据 | 修正意见（对话中），确认后改文件 |
| ④ 草稿 | `/create-draft` | 加载 humanizer + writer-style + content-research-writer 生成草稿 | `content/draft/{ts}-{topic}.md` |
| ⑤ 审稿 | `/review-draft` | 逐条检查 StyleRule（6 条核心规则） | 审核意见（对话中） |
| ⑥ 成文 | `/to-article` | 润色为正式文章，生成 3 个候选标题 | `content/article/{ts}-{topic}.md + 3 候选标题` |
| ⑦ 审查 | `/review-article` | 核实文章内容与数据的准确性和时效性 | 审查意见（对话中） |
| ⑧ 排版 | `/to-wechat` | 公众号排版，使用 wechat-format 引擎 | `content/WeChat/{ts}-{topic}/article.html` |
| ⑨ 配图 | `/image-prompt` | 生成 2-3 组 AI 绘图提示词（写实/插画/3D） | 提示词（对话中），图存 `content/images/` |

**约束**：一次只讨论一个主题。review 命令只输出意见清单，用户确认后才改文件。

---

## 目录结构

```
ContentCreationKit/
├── .env                       # 环境变量（如 ARK_API_KEY）
├── AGENTS.md                  # 代理工作指南（新会话先读此文件）
├── StyleRule.md               # 编辑风格规则（6 条）
├── oh-my-openagent.json       # Agent 模型映射配置
├── opencode.jsonc.bak         # MCP 配置备份
├── yuyang.jpg                 # 公众号二维码
├── .opencode/
│   ├── commands/              # 创作管线命令定义（10 个 .md 文件）
│   └── skills/                # 自定义创作技能（12 个）
│       ├── article-extractor/
│       ├── article-to-presentation/   # HTML 演示文稿
│       ├── content-research-writer/   # 深度研究与写作协作
│       ├── humanizer/                 # AI 文本去味
│       ├── image-generate/            # 封面图生成（Doubao Seedream 4.5）
│       ├── recursive-research/        # 递归式深度研究
│       ├── session-log/               # 会话日志汇总
│       ├── video-downloader/          # 视频下载
│       ├── video-generate/            # 文章转视频管线
│       ├── wechat-format/             # 公众号排版引擎
│       ├── writer-style/              # 思辨分析写作风格
│       └── youtube-transcript/        # YouTube 字幕下载
├── content/
│   ├── topics/                # 选题文件（提交到 main）
│   │   └── archive/           # 已归档过期主题
│   ├── reference/             # 参考资料（gitignore）
│   ├── draft/                 # 草稿文件（gitignore）
│   ├── article/               # 正式文章（提交到 main）
│   ├── WeChat/                # 公众号排版输出（gitignore）
│   ├── images/                # 文章配图 / 封面图（gitignore）
│   ├── video/                 # 视频生成产出（gitignore）
│   └── ppt/                   # HTML 演示文稿输出（gitignore）
├── docs/
│   ├── superpowers/
│   │   ├── specs/             # 设计文档
│   │   └── plans/             # 实施计划
│   └── archive/
│       └── slidev/            # 历史资料
└── .omo/
    └── run-continuation/      # 会话 continuation JSON（系统自动管理）
```

---

## 快速开始

### 前提

- [OpenCode](https://opencode.ai) 已安装
- 必要的 MCP 服务已配置（Tavily、BraveSearch、BingSearch、Jina、ExaSearch、TrendsHub、Playwright、Context7）
- **新会话必须先读 `AGENTS.md`** — 包含管线顺序、数据验证规则、Git 规范、StyleRule 检查清单、主题合并模式等完整代理工作指南

### 使用

在 OpenCode 会话中，按管线顺序执行命令：

```
# 1. 找热门选题
/find-popular-topics

# 2. 审核并深化主题
/review-topics

# 3. 验证参考资料
/review-reference

# 4. 生成草稿
/create-draft

# 5. 审核草稿
/review-draft

# 6. 润色为正式文章
/to-article

# 7. 文章内容审查
/review-article

# 8. 排版到公众号
/to-wechat

# 9. 生成配图提示词
/image-prompt
```

每个命令都有前置条件，不能跳过。管线设计确保每一步的输出质量后才进入下一阶段。

---

## 命令参考

| 命令 | 描述 | 前置条件 | 输出 |
|------|------|----------|------|
| `/find-popular-topics` | 从知乎、微博、36氪等平台挖掘热门话题，自动跳过 `archive/` 中已饱和主题 | 无 | `content/topics/{ts}-{topic}.md` |
| `/review-topics` | 对主题进行深度拷问和背景研究，支持主题合并模式 | 已完成 `/find-popular-topics`，或已有确认主题 | `content/reference/{ts}-{topic}.md` |
| `/review-reference` | 派遣 2-4 个 librarian agent 并行验证每条数据，6+ 次 web search 交叉验证 | 已完成 `/review-topics`，`content/reference/` 有资料 | 修正意见（对话中），确认后改文件 |
| `/create-draft` | 加载 humanizer + writer-style + content-research-writer 生成 AI 去味的中文草稿 | 已完成 `/review-reference`，参考资料已确认 | `content/draft/{ts}-{topic}.md` |
| `/review-draft` | 逐条检查 StyleRule（6 条核心规则）+ 数据核对 + 逻辑审核 | 已完成 `/create-draft`，`content/draft/` 有草稿 | 审核意见（对话中） |
| `/to-article` | 润色草稿为正式文章 + 3 个候选标题 | 已完成 `/review-draft`，草稿已通过审核 | `content/article/{ts}-{topic}.md + 3 候选标题` |
| `/review-article` | 核实文章内容与数据的准确性和时效性 | 已完成 `/to-article`，`content/article/` 有文章 | 审查意见（对话中） |
| `/to-wechat` | 公众号排版，使用 wechat-format 引擎（默认 newspaper 主题） | 已完成 `/to-article`，`content/article/` 有文章 | `content/WeChat/{ts}-{topic}/article.html` |
| `/image-prompt` | 生成 2-3 组封面图 AI 提示词（写实摄影/矢量插画/3D 渲染三种风格） | 已完成 `/to-article`，或已有确认文章 | 2-3 组提示词（对话中） |
| `/self-style` | 从 diff 分析总结个人写作风格偏好 | 有已修改未提交的文章 diff | 风格分析总结（对话中） |

---

## 开发工具

```bash
# Python 环境（脚本从对应 venv 执行）
.venv/bin/python              # 根目录通用脚本
.opencode/skills/video-generate/.venv/bin/python  # 视频管线脚本

# HTML 演示文稿生成（article-to-presentation 技能使用）
python .opencode/skills/article-to-presentation/scripts/generate.py \
  --input content/article/YYYY-MM-DD-<topic>.md \
  --output content/ppt/YYYY-MM-DD-<topic>/slides.html
```

## 数据验证规则

详见 `AGENTS.md`。核心原则：

- **每个数据点都必须核实**，优先一手来源（官方博客、论文、定价页）
- 交叉验证中英文源，同一篇文章前后一致
- 券商研报数据标注"全成本估算"，付费墙内容标注"（付费墙，仅摘要可见）"
- **无法独立验证 → 删除，不留"待验证"标记**

---

## 技能集

ContentCreationKit 集成了以下自定义技能，为创作管线提供能力支撑：

| 技能 | 作用 |
|------|------|
| **article-extractor** | 网页文章内容提取 |
| **article-to-presentation** | 文章转 HTML 演示文稿（B站视频素材 / 知识分享） |
| **content-research-writer** | 深度研究与内容写作协作 |
| **humanizer** | AI 文本去味，消除 AI 腔（基于 Wikipedia Signs of AI Writing） |
| **image-generate** | AI 封面图生成（Doubao Seedream 4.5，Volces Ark API） |
| **recursive-research** | 递归式深度研究（PhD 级别，自动 checkpoint） |
| **session-log** | 会话日志汇总至 weekly agent-log |
| **video-downloader** | 视频下载（mp4/webm/mkv，支持多档画质） |
| **video-generate** | 文章转视频管线（场景分镜 + TTS + Remotion 渲染，TDD 驱动） |
| **wechat-format** | 微信公众号排版引擎（30 套主题，画廊预览） |
| **writer-style** | 思辨分析写作风格（技术深潜 / 深度分析两种模式） |
| **youtube-transcript** | YouTube 字幕下载 |

> 其他辅助技能（brainstorming、grill-me 等）位于用户级 `~/.config/opencode/skills/`，按需加载。

---

## 技术栈

| 组件 | 用途 |
|------|------|
| **OpenCode** | AI 编码代理运行环境 |
| **Tavily MCP** | 综合性网络研究与搜索 |
| **BraveSearch MCP** | 搜索引擎 |
| **BingSearch MCP** | 中文搜索引擎 |
| **Jina MCP** | 网页内容提取 |
| **ExaSearch MCP** | 精准内容搜索与提取 |
| **TrendsHub MCP** | 各平台热点榜单聚合（知乎、微博、36氪、B站等） |
| **Context7 MCP** | 库文档实时查询 |
| **Playwright MCP** | 浏览器自动化 |
| **oh-my-openagent** | Agent 模型配置与管理（visual-engineering → MiniMax-M3，ultrabrain/deep → DeepSeek-V4-Pro） |
| **Volces Ark / Doubao Seedream 4.5** | AI 封面图生图模型（2048×2048，JPEG 输出） |
| **Edge-TTS** | 视频管线中文语音合成 |
| **Remotion** | 文章转视频管线渲染引擎 |
| **Python HTML Template Engine + ECharts** | 演示文稿生成 |
| **Python venv** | 技能脚本运行环境（两个：根目录 + video-generate） |

---

## 创作示例

`content/` 目录下已有的创作案例（共 40+ 篇，持续增长）：

- **AI Agent 学习路线图（四阶段系列）** — 运行时心脏 / RAG / LangGraph & MCP / 实战部署
- **Agent-Loop 深度解析** — AI Agent 运行时循环的架构解构，Karpathy 一句话让全场安静
- **Token-Jevons 悖论** — 越便宜花越多，Token 经济学底层规律（已制作成视频）
- **AI 时代灵魂拷问** — LLM 写作 vs 人的价值（全管线示例，含封面图）
- **华为全栈 Agent 战略** — 鸿蒙 + 盘古 + 昇腾深度分析
- **从 AGI 到 ASI** — 超级智能演进路径
- **DeepSeek 500 亿融资** — 反资本的资本局
- **微信 AI 专属卡 & 支付宝阿宝** — 超级 App Agent 化浪潮
- **国产大模型进入综合效率时代** — 成本战之后的竞争逻辑
- **AI 压缩了执行力，放大了判断力** — 人与 AI 协作的底层变化
- **AI 的决策半径正在变大** — 从辅助到自主的临界点
- **Claude Fable 5 越狱** — AI 大模型的安全阿喀琉斯之踵
- **MiMo Code vs Claude Code** — AI 编程工具架构分化
- **中国开源模型全球崛起** — DeepSeek、Qwen 等的国际影响力
- **AI Agent 落地大考** — 个体 5 倍提效，组织不到 20%
- **Apple Core AI 框架深度解读** — 设备端大模型时代来临
- **AI 投毒元年** — 从学术炸弹到 pip-install 的全面沦陷
- **AI 速度鸿沟** — 写代码快了，交付没提速
- **AI 全栈战争** — 芯片与模型层攻防战
- **美国 AI 立法双轨** — GAIA 法案与事故报告法
- **AI 免费困局与字节破局** — 豆包 68 元替代小团队
- **AI 安全 2026 三层危机** — 从越狱到地缘政治
- **制造者悖论** — AI 替代技术阶层上移
- **Meta 的 AI 双标战** — 硅谷底线在哪里
- **中国 AI 拟人化监管执行** — 大厂集体下架 AI 聊天机器人
- **世界模型两种哲学** — 物理世界模拟 vs 认知推理
- **DeepSeek 推理芯片** — 软硬一体极效
- **Claude 隐写术检测中国用户** — 技术解剖与隐私争议
- **Agent 规模化 = 分布式系统 × LLM 不确定性** — 工程前沿
- **Vibe Coding 昙花一现还是真改变编程范式** — 2026 年中局反思
- **GPT-5.5 暗中降智** — Scaling Law 曝 bug，OpenAI 信任危机
- **AI 砍掉第一批大厂人** — 高薪高绩效为何最先被裁
- **EU AI Act 八月大限** — 全球 AI 监管进入罚款时代
- **硅谷争抢哲学家** — AI 越便宜判断力越稀缺
- **AI 讨好型人格** — 大模型为什么不敢坚持正确答案
- **AI 自繁衍代码** — 英伟达最危险论文
- **400 家报纸起诉 OpenAI 微软** — AI 版权战争终局
- **AI 造谣第一案** — 虚假信息如何做空上市公司
- **Anthropic 切开 Claude 大脑** — 发现 J 空间类意识工作台
- **Linus 再谈 AI** — 大模型能写 Demo 但复杂系统要有敬畏

每篇文章均经过完整管线处理，最终发布到微信公众号。

---

## 关注我的公众号

![玉鸯公众号二维码](yuyang.jpg)

扫码关注「玉鸯」公众号

---

## 更多信息

| 文档 | 内容 |
|------|------|
| **`AGENTS.md`** | 完整管线指南、数据验证规则、Git 规范、StyleRule 检查清单、主题合并模式、配图生成经验、视频管线说明 |
| **`StyleRule.md`** | 编辑风格规则（6 条）：作者隐身、弱化绝对、论据收敛、叙事纯净、列表化、破折号约束 |
| **`.opencode/commands/`** | 10 个管线命令的定义与前置条件 |
| **`.opencode/skills/`** | 12 个自定义技能的 SKILL.md 文档 |

---

## 许可证

MIT
