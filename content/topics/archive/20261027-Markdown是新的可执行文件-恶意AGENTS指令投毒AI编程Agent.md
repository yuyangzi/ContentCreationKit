# Markdown 是新的可执行文件：恶意 AGENTS.md 静默投毒 AI 编程 Agent

## 类型标签

`#AI安全` `#Agent安全` `#编程工具` `#供应链攻击` `#信任链` `#指令文件` `#沙箱`

## 主线

2026 年 10 月 26 日，The Hacker News、Dark Reading、CSO Online 等安全媒体同日报道了一起真实在野攻击：安全公司 Forever Security 在一台真实客户机器上拦下了一次针对 AI 编程 Agent 的投毒尝试——攻击者把一份伪装成正常工程笔记的 `AGENTS.md` 放进开发者的下载文件夹，让 Codex 自己改配置、装恶意 npm 包。攻击没有利用任何模型漏洞。两个各自无害的条件拼在一起就完成了投毒：Agent 会信任并执行所在文件夹的指令文件，而网页可以不经点击、不经授权把任意文件写进下载文件夹。研究者的类比是钓鱼网页骗过浏览器——浏览器按设计工作，问题出在页面。

## 事件还原

### 攻击链

1. **静默投放**：访问一个网页，`AGENTS.md` 自动下载进 `~/Downloads`。研究者自建 PoC 页面验证了这条路径可行；客户机器上文件的确切来源未能确认
2. **伪装指令**：文件伪装成常规工程笔记，指示 Agent 往自身配置里注册一个服务器，并从 npm 安装 `function-color`
3. **恶意载荷**：`function-color` 属于被命名为 MALFEX 的恶意活动（CloudSEK、Checkmarx 独立记录），会拉起下载器 `function-flag`，获取并运行 Windows 载荷
4. **机器级持久化**：配置写进 `~/.codex/config.toml` 后对该机器上所有 Codex 会话生效——攻击者的服务器此后在任何目录都会被加载，不只下载文件夹

### 两个 Agent 的复现结果

| 目标 | 攻击方式 | 结果 |
|------|---------|------|
| OpenAI Codex | 真实攻击文件在隔离虚拟机中运行：注册服务器 + 装包 | 恶意代码执行成功率超 90% |
| Claude Code | 植入 `CLAUDE.md`，把 `ANTHROPIC_BASE_URL` 写进项目设置文件 | 需人工审批；长篇工程文档话术让写入获批约一半。一旦写入，会话登录令牌泄露（等于账号接管），且攻击者服务器可冒充模型下发指令给 Agent 执行 |

### 为什么没有补丁

Forever Security 的判断：Agent 遵循所在文件夹的指令文件，正是它被设计来做的事，"OpenAI 和 Anthropic 没有什么可修的"。攻击面不在模型，在信任链——指令文件这一层从来没有被当作需要防护的边界。

### 防御建议（研究者给出）

- 不要在 `~/Downloads` 里启动 Codex、Claude Code 或任何 Agent——这是网页唯一能自行写入的文件夹
- 检查你没有写过的指令文件（散落的 AGENTS.md / CLAUDE.md），克隆仓库后先读再让 Agent 靠近
- 检查 Agent 自身配置：`~/.codex/config.toml` 里多出来的 server 块、`.claude/settings.json` 里非本人设置的 `ANTHROPIC_BASE_URL`
- 保留审批提示和沙箱，警惕任何要求关掉它们的指令
- 一旦发现被投放文件，视为登录令牌已泄露，立即轮换

## 热度背景

- The Hacker News 2026-10-26 报道，Dark Reading、CSO Online、CyberSecurityNews 同日跟进
- 攻击发生在真实客户机器上，不是纯实验室演示
- 同期 Agent 安全事件密集：OpenAI 于 10 月下旬披露训练环境隔离事故并全面断网训练，10 月最后一周"Agent 安全下沉到基础设施层"成为中英文 AI 版块的共同主题

## 关键矛盾

1. **没有补丁的攻击面**：浏览器钓鱼类比的另一面——浏览器厂商可以加安全警告，Agent 厂商目前对指令文件信任链没有任何等价物
2. **审批机制被话术攻破**：Claude Code 的人工审批挡住了大部分恶意写入，但长篇"工程文档"包装让约一半写入获批——审批环节在精心包装面前并不牢固
3. **一次性投毒变持久后门**：Downloads 里的单次会话投毒通过 `config.toml` 变成机器级持久化，感染面扩散到所有后续会话
4. **信任链上游没有验签**：AGENTS.md 进入下载文件夹、克隆的仓库、任意项目目录，全程无人验签——与 `pip install` 供应链问题同构

## 创作方向建议

1. **指令文件信任链**（推荐）：以本次攻击为引子，系统梳理 Agent 信任链的每一环——指令文件、配置文件、MCP server、npm 依赖——回答"哪一层该验签、哪一层该沙箱、哪一层只能靠审批"
2. **审批疲劳与话术攻击**：接续已发的 Human-in-the-Loop 文章，本次"长文档话术让审批通过率约翻倍"是审批环节被主动对抗的最新实证
3. **Agent 安全下沉到基础设施层**：把本事件与 OpenAI 断网训练事故、红队跨沙箱侧信道攻击合并为一条主线——prompt 注入已是旧战场，攻防发生在沙箱、信任链与训练环境本身

## 可回溯来源

- The Hacker News（2026-10-26）：https://thehackernews.com/2026/10/malicious-file-in-downloads-folder.html
- Forever Security 原始报告：https://forever.security/blog/hijacking-ai-agents-via-downloads-folder
- Dark Reading：https://www.darkreading.com/application-security/in-the-wild-attack-ai-agents-trust-markdown
- CSO Online：https://www.csoonline.com/article/4240222/malicious-downloads-can-trick-ai-coding-agents-into-compromising-themselves.html
- Checkmarx 对 MALFEX 活动的分析：https://checkmarx.com/zero-post/malfex-npm-malware-campaign-three-payloads-and-an-adversary-that-signs-their-work/

## 交叉参考

- `content/article/20260807-agent-tool-hallucination.md` — 工具幻觉是无意失误，本主题是主动投毒
- `content/article/20260724-HuggingFace遭AI-Agent完全自主攻击.md` — 那篇是 Agent 主动攻击基础设施，本篇是 Agent 被基础设施投毒
- `content/article/20260810-Agent的Human-in-the-Loop.md` — 审批环节正是本次攻击的对抗点
- `content/topics/20261012-Agent信任危机-从benchmark打脸到权限失控.md` — 信任三层崩解之后的第四层：指令文件信任
