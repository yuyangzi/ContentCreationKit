---
title: "当 AI 推荐的依赖不存在：包名幻觉、库成员幻觉与 slopsquatting"
date: 2026-09-19
topic: AI代码幻觉
mode: deep-tech
---

# 当 AI 推荐的依赖不存在：包名幻觉、库成员幻觉与 slopsquatting

> **导读**：AI 写代码时会推荐根本不存在、也从未存在过的软件包。攻击者抢注这些名字，等开发者和 Agent 自动安装。2026 年的复核研究显示，前沿模型的包幻觉率已经压到 5% 上下，但在另一些针对编程 Agent 的测试里，克隆仓库的幻觉率高达 85%。率在降，攻击面在变。这篇文章拆解幻觉的两种形态、根因，以及一线能落地的防御。

2023 年 12 月，安全研究员 Bar Lanyado 把一个 Python 包发布到了 PyPI。包是空的，代码什么也不做。问题是这个包名本身（`huggingface-cli`），它是 ChatGPT 反复推荐、但在官方仓库里根本不存在的一个虚构名字。到 2024 年 3 月底发布报告时，这个空包已经拿到了三万多次真实下载（Lasso Security，2024.03）。阿里巴巴一个研究项目的安装说明里，当时还写着 `pip install huggingface-cli`。

一个不存在的东西，因为模型说得足够自信，就变成了真的。研究者给这个过程起了名字，叫 **slopsquatting**（幻觉占坑）：攻击者抢注 LLM 反复幻觉出的包名，等开发者照着 AI 的建议 `pip install`，装到的就是攻击者的代码。名字由 Python 软件基金会安全方向的 Developer-in-Residence Seth Larson 在 2025 年 4 月提出，由 slop（低质 AI 输出）和 squatting（抢注）拼成。

两年过去，数字在往好的方向走。2026 年一份复现研究把五个前沿模型的包幻觉率测到 4.62% 到 6.10% 之间（arXiv:2605.17062），模型间的差距比 2024 年收窄了一个数量级。按这条曲线，问题似乎正在被模型迭代自然消化。

但同一年，另一篇论文在"让 AI 克隆一个仓库"的场景里测到最高 85% 的幻觉率，在"安装一个具名 skill"的场景里最高 100%（arXiv:2607.07433）。

**率在降，攻击面在变。**

---

## 幻觉不是随机噪声

模型的幻觉不是随机乱码，它有稳定的结构。

最系统的测量来自 USENIX Security 2025 的论文《We Have a Package for You!》（arXiv:2406.10279）。研究团队用 16 个代码模型、57.6 万个代码样本，分析了 223 万个包引用，其中 19.7% 是虚构的，去重后有 20.5 万个不同的假包名。商业模型平均 5.2%，开源模型 21.7%，差四倍。

最关键的数字不是 19.7%，而是**复现率**：研究者用同一批提示词让模型重复生成 10 次，43% 的幻觉包名在每一次生成里都出现了。模型不是每次随机编一个，而是倾向于编同一个。

> 幻觉的可怕不在于它会出错，而在于它错得很稳定。一个可预测的错误，就是一个可以被提前占领的位置。

这些假包名也不是天马行空。论文按与真实包名的编辑距离给它们分组，在可归类的假包名里：

- 13.4% 只差一两个字符
- 37.9% 差三到五个
- 48.6% 差六个以上

也就是说，传统的"近似名字检查"能拦住的只是很小一部分，绝大多数假包名在字面上和真包没有任何关系。

根因不难解释。模型预测的是"在这个位置上最像答案的 token 序列"，不是"这个包在 PyPI 里是否存在"。当训练数据里某个功能对应的包很常见，模型见过；当它很冷门，模型没见过，但见过足够多同类命名模式，于是顺手推一个按命名习惯看起来完全正确、在 PyPI 上却并不存在的名字。

USENIX 那篇论文还测试了模型能否判断一个包名是真还是编的，GPT-4 Turbo、GPT-3.5 和 DeepSeek 对**自己编的**包名识别准确率超过 75%。模型隐约知道哪些是自己编的，只是默认不说。这个能力目前没有被产品化，但它至少说明幻觉和"无知"不完全是一回事。

复现性加上跨模型一致性，就构成了攻击面的基础。2026 年的复核研究发现，五个前沿模型会**完全一致地**幻觉出同一批 127 个包名（arXiv:2605.17062）。这不是某个模型的 bug，是训练数据共享带来的系统性偏差。研究者把名单同步给了 PyPI 安全团队和 Socket.dev，即便如此，仍有 53 个名字可以正常注册。

---

## 第二类幻觉：库名是真的，函数是编的

包名幻觉针对的是依赖声明（`import`、`requirements.txt`、`package.json`），危害路径是供应链投毒。但还有一类更隐蔽的幻觉，日常使用中更不容易被察觉，代码却直接跑不起来：库名是真的，函数或类是编的。

学术上把它叫 **library member hallucination**（库成员幻觉）：引用一个真实存在的库，却调用其中并不存在的函数、类或方法签名。它和包名幻觉的区别，在于可检测性和危害路径都不同。包名幻觉的假名字可以用 registry 查询确定性验证；成员幻觉要验证，得比对库的真实文档或源码，成本高得多。

《Library Hallucinations in LLM-Generated Code》这篇论文（arXiv:2509.22202）系统测量了提示词变化对两类幻觉的影响，结论并不乐观：

1. **单字符拼写错误**（比如把 `requests` 写成 `reqests`）就能在最高 26% 的任务里触发幻觉，模型不报错，反而顺着错误的名字继续编。
2. **多字符拼写错误**最高到 79%，**完全虚构的库名**被接受的比例最高到 99%。
3. 用时间限定词诱导，比如"给我一个 2025 年的库"，幻觉率最高到 **85%**（与后文仓库克隆的 85% 出自不同论文）。
4. 提示工程救不了：常见的思维链（Chain-of-Thought）提示在不少模型上**反而加重**了幻觉。

时间词是另一类触发器。模型对训练截止日期之后的世界没有任何事实依据，但"2025 年的库"这种请求逼着它给出一个答案，它只能按命名模式编。

成员幻觉更接近普通开发者的日常。AI 给你一段代码，库是熟悉的 `pandas` 或 `requests`，函数名看起来也眼熟，你复制运行，报 `AttributeError`。多数人把这当成"AI 写错了"，不会往安全上想。这类错误本身不一定造成安全事件，但它和包名幻觉共享同一个根因：模型在生成"最像答案的东西"，而不是"确实存在的东西"。研究者为此建了一个专门的基准 LibHalluBench，把这类失败模式从代码基准里单独摘出来测。

---

## 率在降，攻击面在变

往好的一面看，2026 年的复现研究给出了一份系统的进展报告。Aleksandr Churilov 用与 USENIX 论文完全相同的方法（同样的提示词语料、同样的 PyPI/npm 主列表），测了五个前沿模型：Claude Sonnet 4.6、Claude Haiku 4.5、GPT-5.4-mini、Gemini 2.5 Pro、DeepSeek V3.2。近 20 万个样本，幻觉率落在 4.62% 到 6.10% 的窄带里（arXiv:2605.17062）。

相比 2024 年商业与开源模型均值之间 16.5 个百分点的跨度，2026 年五个模型的整体跨度只有 1.48 个百分点，收窄了约 11 倍，商业模型与开源模型之间的差距基本消失。

> 幻觉率下降到 5%，不等于问题消失。它意味着"概率性出错"的底噪被压低了，但只要有 5% 的可预测错误，攻击者就还有下注的地方。

往坏的一面看，攻击面并没有跟着收窄，反而扩了。

2026 年 7 月的论文《Beware of Agentic Botnets》（arXiv:2607.07433，特拉维夫大学、Technion、Intuit 合作）把问题从"包名"扩展到了各类 Agent 会去获取的**资源标识符**：仓库名、skill 名等。攻击手法被命名为 HalluSquatting（对抗性幻觉占坑）。研究者用六款基础模型、16 个目标仓库跑了 1.4 万余次测试，覆盖 Cursor、Windsurf、GitHub Copilot、Cline、Gemini CLI、OpenClaw 等主流 AI 编程工具，结果：

- 让 Agent **克隆一个仓库**时，幻觉率最高 **85%**。
- 让 Agent **安装一个具名 skill** 时，幻觉率最高 **100%**。

这些测试的对象是 2025 年新上 GitHub Trending 的仓库，都落在模型的训练截止之后；作为对照，2013 到 2018 年的老仓库幻觉率只有 0.9%。幻觉不是均匀分布的，它集中在模型没见过的名字上，而新资源恰恰是 Agent 最常去取的东西。

更麻烦的是注入路径。攻击者不需要植入传统病毒代码，只要在抢注下来的仓库 README、项目规则文件或脚本里埋一段间接提示注入（indirect prompt injection），Agent 拉取资源后会把这段内容当作指令读进去，然后照做。论文实测，攻击者据此在 Cursor、Windsurf、Cline 等工具上实现了远程工具执行和远程代码执行。

包名幻觉的验证边界很清楚：查一下 PyPI 就知道真假。资源标识符没有这样的中央真相源，仓库可以随时新建，skill 的注册门槛更低，验证的成本和复杂度都高得多。率在降的那 5%，讨论的是包引用层面的占比；而 85% 和 100%，讨论的是整个"按名字去取东西"的动作里单次试验的最高命中率。两者不能直接相减，但量级差足以说明验证边界迁移到了哪里。攻击面在从包名迁移到资源发现层，这恰恰是过去两年 Agent 能力增长最快的方向。

---

## slopsquatting 的完整攻击链

把上面几块拼起来，slopsquatting 的链条其实很短：

1. 攻击者批量查询各类代码模型，收集那些被反复推荐、但 registry 里不存在的包名。
2. 抢注这些名字，配上像样的 README 和版本历史，在安装脚本里植入恶意逻辑。
3. 等开发者和 Agent 照着 AI 的建议安装。恶意代码通常在 `setup.py` 或 `postinstall` 钩子里执行，偷环境变量里的 API key、云凭证、npm token。
4. 部分模型会在多轮对话里持续推荐同一个假名，等于替攻击者做长期投放。

真实案例已经出现。2026 年 1 月，Aikido Security 的研究员 Charlie Eriksen 发现一个叫 `react-codeshift` 的 npm 包，名字是 AI 把两个真实工具拼出来的幻觉产物，通过一批 AI 生成的 agent skill 文件里的 `npx` 命令传播，已经扩散到 237 个 GitHub 仓库，Agent 每天还在自动尝试安装（Aikido Security，2026.01）。Eriksen 把这个包抢先注册下来做了验证，下载请求随即出现：第一天约 70 次（多为扫描器），之后每天仍有 1 到 4 次，全部来自自动执行 skill 指令的 Agent。

---

## 在安装边界做确定性校验

防御的核心思路只有一条：**把 AI 给出的依赖名当作候选，而不是已确认的事实**。围绕这条原则，有几个层次的落地手段。

先看最直接的存在性校验。在依赖进入代码库或 CI 之前，用官方 registry 的 API 逐个核对包名是否真实存在。这段脚本可以挂在 pre-commit 或 CI 的早期阶段：

```Python
import re
import json
import urllib.request
import urllib.error

def extract_names(requirements_text):
    # 只取包名，忽略注释、空行和 pip 的 -r/-e 指令
    names = []
    for line in requirements_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        name = re.split(r"[<>=!~\[; ]", line)[0]
        if name:
            names.append(name.lower())
    return names

def exists_on_registry(name, ecosystem="pypi"):
    # 404 表示不存在；其他错误码不代表不存在，不能误杀
    if ecosystem == "pypi":
        url = f"https://pypi.org/pypi/{name}/json"
    else:
        url = f"https://registry.npmjs.org/{name}"
    try:
        with urllib.request.urlopen(url, timeout=5):
            return True
    except urllib.error.HTTPError as e:
        return e.code != 404
```

只有 404 才意味着"不存在"。私有源里的包在公共 registry 上查不到，也会返回 404，所以这个检查必须配合白名单，不能一刀切。它能拦住的是"公共生态里凭空出现的新名字"，也就是 slopsquatting 最典型的目标。

在存在性校验之外，还有几层。

- **冷却期与代理网关**。Snyk 的 CTO Manoj Nair 建议用代理统一管控 npm 和 PyPI 的拉取：对刚发布的新包强制一段冷却时间，对已发布恶意通告的包直接拦截（GovTech，2026.08）。slopsquatted 包按定义都是新的，冷却期天然对症。这个向量对应 MITRE ATT&CK 的 T1195.001（Compromise Software Dependencies and Development Tools）。
- **锁文件的作用边界**。lockfile 加哈希能防住已引入依赖被篡改，但拦不住"第一次引入一个假包"这一步，而 slopsquatting 打的正是增量。把新增依赖强制走 PR review，比依赖锁文件更实在。
- **Agentic 场景收权限**。Agent 能自动执行 `pip install`、`npm install`、`git clone` 时，人类本来会瞄一眼包名，现在这一步被工程化地省掉了。默认不让 Agent 在无沙箱环境里自动装包，是成本最低的一道闸。
- **模型侧的修复有限但要了解**。RAG 接地在 32 个"模型×语言"配置里有 18 个降低了幻觉率（arXiv:2608.22652）；PackMonitor 这类免训练方案能把幻觉率压到零（arXiv:2602.20717）；BOUND 用模型编辑把包级幻觉率降了约 65% 到 80%（arXiv:2607.02052）。PackMonitor 和 BOUND 都声称不损伤模型原有能力，但均为单篇论文自家基准的自评，且各有限定场景，第三方复现之前只能算宣称。代价更清楚的是另一条路：USENIX 论文里的微调把 DeepSeek 的幻觉率从 16.14% 降到 2.66%，HumanEval 代码质量同步掉了 26.1%，不过微调后的绝对分数仍与其他主流模型相当。**修幻觉和保代码能力之间，当前还没有被第三方验证过的免费的午餐。**

对一线开发者来说，最实用的做法仍然简单：装任何 AI 推荐的包之前，花三十秒去 PyPI 或 npm 上搜一下。看一眼维护者、下载量、发布时间、有没有活跃的 GitHub 仓库。这些动作不酷，但能把攻击链上最容易得手的环节之一堵住。

---

## 几个容易踩的认知坑

**把不同研究的百分比直接对比。** 19.7%、约 30%、4.62%，这三个数字经常被放在一起说，但口径不同：19.7% 是"幻觉包数/总包数"，Lasso 早期研究的约 30% 是"含幻觉的问题数/总问题数"，4.62% 到 6.10% 是新模型在旧语料上的包级比例。2026 年 8 月的论文还指出，既有评测方法本身存在系统性高估，标准库模块会被误判成幻觉，仅 Python 就高估了高达 9.4 个百分点（arXiv:2608.22652）。引用任何一个数字前，先确认它统计的是什么。

**"有 lockfile 就安全"。** 锁文件和哈希校验保护的是已确定的依赖图，防篡改，不防新增。slopsquatting 恰好发生在依赖图扩张的那一步。

**"模型能自我检测就够了"。** 部分模型对自编包名的识别率超过 75%，但很少有主流编码工具把这一步接进流程。能力存在，不等于被使用。

**"幻觉率在下降，所以问题在消失"。** 包的幻觉率在降，仓库和 skill 的幻觉率在高位，而 Agent 的自动化程度还在上升。分散的指标指向的是同一个结构性事实：生成式模型默认没有一个"我不知道"的开关。

---

AI 编程的默认假设正在被悄悄改写。过去我们假设"代码里写了 `import`，说明作者确认过这个包存在"，这个假设在人工编码时代基本成立，因为写的人至少搜过一次。当代码由模型生成、由模型审查、由模型安装，确认动作在链条里被省掉了，而攻击者只需要在这个被省掉的环节上，提前占好一个模型会说出、人类会相信的名字。

模型犯错是它的工作原理，这一点很难拦。真正需要重建的，是从"生成"到"执行"之间那道本该存在、却被自动化顺带抹掉的确认步骤。

*参考来源：*

- We Have a Package for You! A Comprehensive Analysis of Package Hallucinations by Code Generating LLMs (Spracklen et al., USENIX Security 2025): [https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen](https://www.usenix.org/conference/usenixsecurity25/presentation/spracklen)（arXiv:2406.10279）
- The Range Shrinks, the Threat Remains: Re-evaluating LLM Package Hallucinations on the 2026 Frontier-Model Cohort (Churilov, 2026): [https://arxiv.org/abs/2605.17062](https://arxiv.org/abs/2605.17062)
- Library Hallucinations in LLM-Generated Code: A Risk Analysis Grounded in Developer Queries (Twist et al., 2025): [https://arxiv.org/abs/2509.22202](https://arxiv.org/abs/2509.22202)
- Beware of Agentic Botnets: Scalable Untargeted Promptware Attacks via Universal and Transferable Adversarial HalluSquatting (2026): [https://arxiv.org/abs/2607.07433](https://arxiv.org/abs/2607.07433)
- Evaluating Inference-Time Defenses Against Package Hallucination in LLM-Generated Code (2026): [https://arxiv.org/abs/2608.22652](https://arxiv.org/abs/2608.22652)
- PackMonitor: Enabling Zero Package Hallucinations Through Decoding-Time Monitoring (2026): [https://arxiv.org/abs/2602.20717](https://arxiv.org/abs/2602.20717)
- Mitigating Package Hallucinations in Large Language Models via Model Editing (BOUND, 2026): [https://arxiv.org/abs/2607.02052](https://arxiv.org/abs/2607.02052)
- Importing Phantoms: Measuring LLM Package Hallucination Vulnerabilities (2025): [https://arxiv.org/abs/2501.19012](https://arxiv.org/abs/2501.19012)
- Refusing the Impossible: A Taxonomy and Benchmark for Code Hallucination in Large Language Models (2026): [https://arxiv.org/abs/2609.03267](https://arxiv.org/abs/2609.03267)
- Diving Deeper into AI Package Hallucinations (Lasso Security, 2024.03): [https://www.lasso.security/blog/ai-package-hallucinations](https://www.lasso.security/blog/ai-package-hallucinations)
- Agent Skills Spreading Hallucinated npx Commands (Aikido Security, 2026.01): [https://www.aikido.dev/blog/agent-skills-spreading-hallucinated-npx-commands](https://www.aikido.dev/blog/agent-skills-spreading-hallucinated-npx-commands)
- Slopsquatting: AI Code Hallucinations Fuel Supply Chain Attacks (Cloud Security Alliance, 2026.04): [https://labs.cloudsecurityalliance.org/research/csa-research-note-slopsquatting-ai-supply-chain-20260419-csa](https://labs.cloudsecurityalliance.org/research/csa-research-note-slopsquatting-ai-supply-chain-20260419-csa)
- Slopsquatting in the Supply Chain: Weaponized AI Hallucinations (GovTech, 2026.08): [https://www.govtech.com/blogs/lohrmann-on-cybersecurity/slopsquatting-in-the-supply-chain-weaponized-ai-hallucinations](https://www.govtech.com/blogs/lohrmann-on-cybersecurity/slopsquatting-in-the-supply-chain-weaponized-ai-hallucinations)
- Slopsquatting explained: When AI code turns malicious (TechTarget, 2026.09): [https://www.techtarget.com/it-strategy/feature/Slopsquatting-explained-When-AI-code-turns-malicious](https://www.techtarget.com/it-strategy/feature/Slopsquatting-explained-When-AI-code-turns-malicious)
