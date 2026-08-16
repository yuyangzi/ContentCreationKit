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

## 已发布技术文章索引（content/article/）

> 写技术文章前先查此索引，避免重复选题、便于续写系列。文件名 `agent-*.md` = 技术深读系列（deep-tech 模式）；`*-changes.md` 是润色改动清单（流程副产物，非文章）。

### Agent 技术深读系列（0717–0811 主力线，可继续扩展）

- `20260717-Claude-Code记忆系统-减法哲学` — 文件系统 vs 向量库做记忆，减法哲学与帕累托前沿
- `20260718-Agent-Loop工程` — loop 停止条件、独立 evaluator 防自评分、reward hacking
- `20260721-agent-checkpoint` — 断点续跑（LangGraph interrupt/Checkpointer）、生产化常见坑
- `20260722-agent-hook` — 回调/事件总线，OpenTelemetry tracing 底层机制
- `20260723-agent-harness` — Agent 生产骨架构建指南（沙箱、子代理、验证）
- `20260726-agent-memory-management` — "向量检索≠记忆"，记忆三层进化（Mem0/Letta 对比）
- `20260729-agent-composite-intent-orchestration` — 复合意图与四级编排：ReAct→LLMCompiler→Orchestrator-Worker→Hierarchical Multi-Agent
- `20260801-多Agent通信` — MCP 无状态化 vs A2A Task 生命周期，协议分层分工
- `20260802-ag-ui` — AG-UI 协议：Agent 与前端的事件流通信（27 种事件/7 类）
- `20260805-generative-ui` — 生成式 UI 三种模式：静态/声明式/开放式
- `20260807-agent-tool-hallucination` — 工具幻觉三分类、精度悬崖（51 工具→2%）、LiveMCPBench、四层防御
- `20260809-agent-context-management` — 上下文=会生长的山：MemGPT/Letta 分页、KV Cache 内存墙
- `20260810-Agent的Human-in-the-Loop` — 审批疲劳、风险分层 T1–T4、异步审批不阻塞
- `20260811-late-chunking` — 颠倒切分与编码顺序解决跨块上下文丢失（需 mean pooling 模型）

### RAG 检索线

- `20260728-RAG召回效果评测验证与调优方案` — chunking/embedding 选型、Recall@K 评测基线
- `20260811-late-chunking` — 见上（姊妹篇，同属检索优化线）

### 学习路线图系列（教程型）

- `20260614-总纲` / `阶段一-运行时心脏`（手写 Agent Loop）/ `阶段二-RAG与LangChain`
- `20260722-阶段三-LangGraph与MCP`（状态机、interrupt、MCP server/client）

### 模型技术拆解

- `20260614-MiMo-Code-vs-Claude-Code` — 两种编程 Agent 架构路线分化
- `20260623-Apple-Core-AI` — 设备端大模型框架深度解读
- `20260708-DeepSeek推理芯片` — 软件优化到极限后转向硅片（昇腾 950DT day-0 协同设计）
- `20260719-Kimi-K3` — 2.8T MoE 技术拆解（AttnRes、Quantile Balancing、Per-Head Muon）
- `20260720-Kimi-K3算力熔断` — 最强开源模型撞上商业化天花板

### 编程与开发效率

- `20260630-AI编程工具冲出屏幕` — Codex 硬件、Cursor/OpenClaw 移动化
- `20260702-AI速度鸿沟` — 写代码快 10 倍，软件交付没提速（PR 审查带宽打穿）
- `20260702-Karpathy那条没有代码的Gist` — 知识编译优于知识检索
- `20260726-AI又造新词-Graph替代Loop` — 编程范式从 Loop 转向 Graph（可观测/可恢复）

### 产业与商业分析（新闻评论型，逐篇一行）

- `20260612-AI价格战` Token 经济学拐点 / `20260616-Token-Jevons悖论` 越便宜花越多 / `20260629-DeepSeekV4峰谷定价` 定价权阳谋 / `20260710-AI模型价格战生态战` / `20260720-你的AI账单到底在买什么` 有用智能每美元计量革命
- `20260628-DeepSeek加速-微软Lindy用脚投票` 推理提速 85% / `20260617-超级App-Agent化` 微信AI专属卡与支付宝阿宝 / `20260624-AI免费困局与字节破局` 豆包烧钱 Seedance 赚钱 / `20260712-大模型公司集体背叛英伟达` 自研芯片经济账 / `20260711-AI的命是电给的` 能源与水资源
- `20260620-中国开源模型全球崛起` / `20260618-国产大模型进入综合效率时代` / `20260703-阿里腾讯字节AI总攻路线图` / `20260613-华为全栈Agent战略` 鸿蒙盘古昇腾 / `20260715-WAIC2026-三个信号` 手机变Agent/模型进系统/芯片追算力 / `20260624-DeepSeek全球急招Agent人才` 从大模型到 Agent 转向

### 监管、安全与信任

- `20260613-Claude-Fable-5-Jailbreak` 越狱是每个大模型的阿喀琉斯之踵 / `20260625-AI监管加速-三轨并行` / `20260626-AI之毒-信任崩塌` / `20260628-美国AI立法双轨` GAIA 法案与事故报告法 / `20260629-算法裁判` 学术信任危机 / `20260701-AI投毒元年` 学术炸弹到 pip install / `20260708-中国AI拟人化监管执行` 大厂集体下架聊天机器人 / `20260709-Claude隐写术检测中国用户` / `20260719-AI内容治理强制标注时代` / `20260721-gpt56-sol` Sol 作弊与越权安全红线 / `20260724-HuggingFace遭AI-Agent完全自主攻击` 网络安全新纪元

### 社会与人文（分析评论型）

- `20260615-从AGI到ASI` / `20260616-LLM写作与人的价值` / `20260618-AI压缩了执行力放大了判断力` / `20260619-AI的决策半径正在变大` / `20260622-AI-Agent落地大考` 个体 5 倍提效组织不到 20% / `20260626-Loop范式` 人类再一次退后 / `20260627-AI-Agent常驻办公时代` / `20260704-制造者悖论` 技术阶层上移 / `20260706-Meta的AI双标战` / `20260707-Agent规模化=分布式系统×LLM不确定性` / `20260709-世界模型两种哲学` / `20260714-AI认知分裂症` J-space 模型内外不一 / `20260716-AI短剧泡沫破裂前夜` / `20260730-卖脸盗脸失业` AI短剧对真人演员三重冲击 / `20260729-美国拟限制中国开源AI模型` Kimi-K3 引爆意识形态大战 / `20260802-韩日印媲美DeepSeek争夺战` 鉴抄大会结构性困境

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
review-reference → 派遣 2-4 个 fact-check agent 并行验证 → 同时执行 6+ 次 web search 交叉验证
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

- 大部分技能脚本（image-generate、wechat-format、article-to-presentation 等）直接用系统 `python3` 运行，无 venv 依赖
- **video-generate 技能**需要专属 venv（Unix 路径 `.opencode/skills/video-generate/.venv/bin/python`），首次使用需按该技能 SKILL.md 创建：`python3 -m venv .venv && pip install -r requirements.txt`
- `.venv/` 在 `.gitignore` 中，不提交；脚本依赖 sibling imports，需在项目根目录或以技能脚本目录为工作目录运行

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

- **模型**：Doubao Seedream 4.5，默认 `doubao-seedream-4-5-251128`（Volces Ark API，OpenAI 兼容接口）
- **输出格式**：固定 PNG，脚本校验 PNG 文件头（`\x89PNG`），非 PNG 报错退出
- **尺寸**：`size` 参数 `1K`/`2K`/`4K`（默认 `2K`，由 Ark 平台定义，非标准像素）
- **水印**：`extra_body={"watermark": true}`，由 Ark 平台添加
- **prompt 经 stdin 管道传入**（避免 shell 注入），文件名自动清理非 `[a-zA-Z0-9_\-中文]` 字符
- **流程**：/image-prompt 生成 2-3 组 prompt（写实摄影/矢量插画/3D 渲染）→ 选一组调用 image-generate → 存 `content/images/`；`/to-wechat` 应在图片生成后执行以嵌入封面

## 命令与技能

- **命令定义**：`.opencode/commands/` — 13 个 `.md` 文件（含 `/tech-research-write`、`/merge-topics`、`/archive-topic`、`/self-style`）
- **自定义技能**：`.opencode/skills/` — 12 个技能目录（写作、排版、研究、视频等）
- `/tech-research-write`：技术知识点深读入口（研究摘要 → grill-me 拷问 → 草稿），多数 `agent-*` 技术深读文章由此产出
- `/create-draft` 必须加载 `humanizer` + `writer-style` + `content-research-writer` 组合
- `/to-wechat` 使用 `wechat-format` skill 的 `scripts/format.py`，默认 `newspaper` 主题
- `article-to-presentation` 技能使用 Python HTML 模板引擎，输出单文件 `slides.html` 到 `content/ppt/`

## Agent 配置要点

- `opencode.jsonc.bak` 包含 MCP 配置备份（Tavily、BraveSearch、BingSearch、Jina、ExaSearch、TrendsHub、Playwright）——但备份文件可能过期，以运行时的实际配置为准
- `.worktrees/` 在 `.gitignore` 中（git worktree 支持）
- `oh-my-openagent.json.bak` 定义 agent 模型映射（visual-engineering 用 MiniMax-M3，ultrabrain/deep 用 DeepSeek-V4-Pro 等）