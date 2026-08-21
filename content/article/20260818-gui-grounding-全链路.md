# GUI Grounding 全链路：模型怎么把"点这个按钮"翻译成屏幕坐标

> **导读**：Anthropic 把 Computer Use 开放出来快两年了，OSWorld 上各路模型的分数从 12% 一路卷到 90%。但 OSWorld 2.0（那个真正模拟长时办公任务的基准）上，frontier 模型仍然在 20% 附近徘徊。同一个时间点，两个数字相差四倍。这篇文章想回答一个比"哪个模型更强"更基础的问题：**模型到底是怎么把"点那个按钮"这句话，翻译成屏幕上 (x, y) 这两个数字的？** 我们沿着 See-Think-Act 的工作链路一路看下来，从坐标生成、路线对比、评测真相一直讲到决策框架和 harness。

---

## 一件让模型尴尬的小事

试着让一个大模型直接输出一对坐标。

```Python
# 看起来天经地义的 prompt
prompt = "点击右上角的关闭按钮，输出坐标"
# 我们期待的输出
# x = 1820.537, y = 28.913
```

GPT-4o 或者 Claude 不会这么干。它们会输出类似 `click(1820, 29)` 这样的整数对，坐标圆整到当前网格粒度。这不是模型偷懒，而是 **目前主流 LLM 无法可靠地回归连续小数**。

背后的原因很简单：当前主流 LLM 是文本生成模型，输出的是 token 序列。它能做的是把一个浮点数切碎成几十上百个 token 然后挨个生成——但每多生成一个 token，误差就多一点。一对坐标要两位小数精度，意味着每个坐标至少要预测 6-8 个 token；在 1920×1080 的屏幕上，6 个 token 的误差足以让点击落在目标旁边几十像素的位置。

> **这意味着 GUI grounding 的本质不是"模型会不会看图"，而是"模型怎么把像素坐标塞进离散 token 的世界"。**

---

## 一、See-Think-Act：一个不直接摸鼠标的 Agent

主流 Computer Use Agent 不管叫什么名字——Claude Computer Use、OpenAI CUA、UI-TARS、AutoGLM，跑的大多是同一个循环。这套循环叫 **See-Think-Act**（感知—思考—行动）。

伪代码长这样（基于 Anthropic computer-use 工具文档与 OpenAI computer tool 文档综合）：

```Python
# 简化版 GUI Agent 主循环
instruction = "把 price 列从 A 拖到 B 列"
state = capture_screenshot()              # See：拿到当前屏幕像素

while not finished:
    thought, action = model(              # Think：模型根据截图和历史做决策
        instruction,
        history,
        screenshot=state
    )
    # CUA 这类模型会先吐一段 chain-of-thought，
    # 再决定动作，比如 {"type": "left_click", "x": 450, "y": 320}
    
    if action.type == "screenshot":
        continue                          # 模型主动要求"再看一眼"
    
    execute(action)                       # Act：由 harness 执行真正的鼠标键盘
    state = capture_screenshot()          # 执行后必须回传新截图
    
    # 模型用前后两张截图的差异判断动作是否生效
    # CUA 对登录、CAPTCHA 这类敏感动作会请求人工确认
```

有三件事值得一开始就说清楚，否则后面所有机制都会读歪。

**第一**，模型不直接操作屏幕。它只输出结构化的动作请求——一个 JSON，描述"我想在哪儿做什么"。真正按下鼠标、敲下键盘的是你自己写的 harness（agent 的"手"）。OpenAI 官方文档原话是这么说的："In practice, your harness acts as the hands on the keyboard and mouse, while the model uses screenshots to understand the current state of the interface and plan the next step."。所以 Computer Use 不是"AI 直接控制电脑"，而是"AI 给出一份带坐标的操作建议，由 harness 落实"。

**第二**，截图是默认的感知通道。模型本身不读 DOM、不读 accessibility tree（部分实现可以显式叠加这些数据），回答"模型怎么知道那是关闭按钮"这类问题，答案主要得在像素里找。

**第三**，循环的终止靠"模型主动说做完了"或"步数上限被撞"。Anthropic 靠模型返回无动作或 `end_turn`，OpenAI CUA 靠模型输出最终文本回答。这两种都意味着：写 harness 的时候必须自带 MAX_STEPS 保险丝，否则模型陷入死循环就真烧钱了。

所谓的"GUI Agent"，本质就是一段**视觉编码 + 坐标回归 + 状态循环**的代码，剩下的工程都是把它包得能落地。

---

## 二、坐标怎么"出"——四种输出范式

LLM 既然不能直接吐浮点坐标，业界的解法是把坐标**离散化**。下面四种范式你大概率会撞到其中一种。

### 2.1 范式 A：归一化整数坐标（OpenAI 风格）

OpenAI 的 CUA 输出相对屏幕的归一化整数坐标，社区实测范围是 0–1000（[官方文档](https://developers.openai.com/api/docs/guides/tools-computer-use) 对坐标范围未做硬性定义，只要求 harness 把模型生成的坐标从降采样坐标系映射回实际屏幕），落点执行时由 harness 换算回 1920×1080 的实际像素。把"整数网格"写进官方文档的是 Google：Gemini Computer Use 把屏幕切成 1000×1000 的网格，模型只输出 0–999 的整数。

这种范式的优点是模型侧极其简单（整数 token 的预测稳定性远高于浮点数）。缺点是精度有上限：1920×1080 的屏幕，每格约 1.9 像素，对小按钮来说偏一两格就点空了。

### 2.2 范式 B：声明的像素空间（Anthropic 风格）

Anthropic 的 computer tool 要求调用方传 `display_width_px` 和 `display_height_px` 两个参数，模型在声明的像素空间里吐坐标 ([Claude Platform Docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool))。但 Anthropic 同时限制了输入截图的尺寸——长边不超过 1568 像素、总像素不超过 1,150,000。**截图先降采样，模型按声明尺寸算坐标，再由 harness 映射回原始屏幕**。

这意味着如果你不显式做坐标映射，每一次点击都会按错误的尺度落点。Anthropic 官方文档里"点击整体向一个方向偏移"这条 troubleshooting 提示，说的就是这种情形。

### 2.3 范式 C：归一化相对坐标（UI-TARS 风格）

字节的 UI-TARS 把坐标直接归一化到 [0, 1] 区间，比如 `click (0.49, 0.40)` 直接当文本吐出来 ([UI-TARS 论文](https://arxiv.org/abs/2501.12326))。SeeClick 也走类似路线，把坐标当成纯文本 token。这种范式对分辨率天然不敏感（同一份输出在任何屏幕上都能用），代价是模型要把小数精度也压进文本生成里。

### 2.4 范式 D：SoM 标记引用（解析器风格）

微软的 [Set-of-Mark (SoM) prompting](https://arxiv.org/abs/2310.11441) 走的是另一条路：先用分割模型（SEEM/SAM）把截图切成区域，给每个区域叠上字母数字标记；模型不直接出坐标，而是说"我想点标记 7"。harness 再把标记 7 解析回真实坐标。这种范式把"定位"问题变成"选择题"，模型只需要从 30 个标记里选一个，精度压力小很多。

### 2.5 坐标为何总偏：绝大多数坑的同一个根

把上面四种范式放一起，你会发现 GUI Agent 踩的绝大多数坑都源自一件事——**"模型看到的图"和"鼠标落点的屏幕"不是同一套坐标系**。

具体来说有三种"不一致"：

第一，**截图分辨率不一致**。你的真实屏幕可能是 4K，API 限制了 1568 像素，必须先降采样。模型按降采样后的图算坐标，harness 必须再映射回去。忘了一步，点击就稳定偏移。

第二，**系统 DPI 缩放**。Windows 200% 缩放下，Chrome DevTools Protocol 上报的 `devicePixelRatio` 经常错报为 1（应为 2），截图内容只占屏幕一角，所有点击错位 ([browser-use Issue #4571](https://github.com/browser-use/browser-use/issues/4571))。修复方法是强制 `--force-device-scale-factor=1` 或调用 `SetProcessDpiAwareness(2)`。

第三，**多显示器 / 虚拟屏**。Linux 无头环境用 Xvfb 起虚拟屏，参数没设对时屏只有 1×1 像素，截图全黑。Anthropic 官方参考容器里的物料清单（Xvfb + Mutter + Tint2 + xdotool + scrot）就是为了把这件事做对 ([infragap 分析](https://infragap.com/computer-use-agents))。

> **这一类问题的修法高度同构：保证 `display_width_px/height_px` 与发送截图的实际像素严格一致，缩放后做坐标映射，DPI 强制 1x。** 三个动作里漏一个，点击就会"稳定地错在一个地方"。

---

## 三、两条路线：让模型自己学 vs 给模型外挂"眼睛"

模型吐坐标的**能力**来自两条路线。

### 3.1 端到端原生 Agent：让模型把 grounding 长在身上

代表工作包括 UI-TARS（[2501.12326](https://arxiv.org/abs/2501.12326)）、Aguvis（[2412.04454](https://arxiv.org/abs/2412.04454)）、CogAgent（[2312.08914](https://arxiv.org/abs/2312.08914)）、SeeClick（[2401.10935](https://arxiv.org/abs/2401.10935)）。这一派的核心做法是把"看截图 + 定位 + 动作决策"塞进同一个视觉语言模型里，用海量"截图 + 元素描述 + 坐标对"做监督微调。

UI-TARS 是这条路线的标本。它在 Qwen2-VL 7B/72B 上持续训练约 50B tokens，其中包含 Web 端 14.8M 元素、桌面端 1.1M 元素、移动端 2.5M 元素。在 OSWorld 上 UI-TARS-72B 拿到 24.6%（50 步），首次超过 Claude Computer Use 的 22.0%（[OpenAI 引用](https://openai.com/index/computer-using-agent/)）。这条路线后来又演化出 UI-TARS-2（多轮 RL），OSWorld 推到 47.5%（[2509.02544](https://arxiv.org/abs/2509.02544)）。

训练方法上，这一派普遍是 **SFT + RL 的组合**：先用人类演示行为克隆（OpenAI CUA 的 System Card 里就是这么做的），再用 RL 教推理和适应意外（[OpenAI Operator System Card](https://openai.com/index/operator-system-card/)）。UI-TARS 还引入了 DPO（直接偏好优化），用错误纠正对和事后反思对来学"哪里点错了"。

### 3.2 外部解析器：让一个"看图专家"先把元素列出来

代表工作是 OmniParser（[2408.00203](https://arxiv.org/abs/2408.00203)）和 SoM prompting（[2310.11441](https://arxiv.org/abs/2310.11441)）。这一派把 grounding 拆成两步：先用专用模型把截图"解析"成结构化元素列表，再让通用 LLM 从列表里选。OmniParser V2 的"解析"配置是 YOLOv8 检测可交互区域、Florence-2 给图标写语义描述。

这种打法的关键数据来自 ScreenSpot-Pro 评测（[2504.07981](https://arxiv.org/abs/2504.07981)）：裸 GPT-4o 在这个面向高分辨率专业软件的 grounding 基准上只有 **0.8%**——不是 8%，是 0.8%。配上 OmniParser V2 之后跳到 39.6% ([微软博客](https://www.microsoft.com/en-us/research/articles/omniparser-v2-turning-any-llm-into-a-computer-use-agent))。换句话说，**grounding 能力远比"模型会不会看图"更稀缺**。

这个 0.8% 的数字值得多看一眼。它意味着在 Adobe、GIMP、AutoCAD 那种专业软件界面上，模型连"哪个元素是按钮"都识别不出来。

### 3.3 混合路线：当前工程主流

两端各有问题：端到端模型泛化强但 grounding 弱，解析器精度高但跨平台不一致。工程界目前的共识是 **混合**——能拿到 HTML/DOM/accessibility tree 的就走结构化，桌面/遗留软件才回退到视觉。

一个反直觉的负面结果：[SeeAct 论文](https://arxiv.org/abs/2401.01614) 在 Mind2Web 上做了系统对比，结论是**纯 SoM 标记对 web agent 没帮助**：SeeAct 最佳 grounding 方法（Choice，HTML 结构 + 视觉双通道）在线成功率 37.8%；人工标注的 oracle grounding 才能到 51.1%。

> **当前的工程现实**：端到端模型（UI-TARS、CUA）和解析器+LLM（OmniParser + GPT-4V）都在被广泛使用，混合方案是大多数产品线的实际选择——浏览器内有 DOM 走 DOM，没 DOM 才回退到截图。

---

## 四、评测的两个数字，藏着 GUI Agent 的全部真相

### 4.1 一条漂亮的上升曲线

OSWorld 是 Computer Use Agent 的核心基准（[2404.07972](https://arxiv.org/abs/2404.07972)），在真实 Ubuntu 虚拟机里跑 369 个真实办公任务。把 2024 年到现在各家厂商的官方成绩按时间排：

| 时间 | 系统 | OSWorld 成功率 |
|---|---|---|
| 2024.04 | GPT-4/GPT-4o（基线） | ~12% |
| 2024.10 | Claude 3.5 Sonnet Computer Use | 22.0% |
| 2025.01 | OpenAI CUA | 38.1% |
| 2025.09 | Claude Sonnet 4.5 | 61.4% |
| 2025.12 | Simular Agent S3 | 72.6%（首超人类 72.36%） |
| 2026.07 | 实在 Agent | 90.2% |

数据来源：[Anthropic 博客](https://www.anthropic.com/news/claude-sonnet-4-5)、[Simular 文章](https://www.simular.ai/articles/simulars-computer-use-agent-outperforms-humans)、[新华网/财联社报道](https://www.xinhuanet.com/government/20260805/60bc929f7f0d4722b6ad4f4f22d90fcb/c.html)。

两年时间从 12% 卷到 90%。

### 4.2 一条崩塌的曲线

但 OSWorld 还有一个变体：**OSWorld 2.0**（[2606.29537](https://arxiv.org/html/2606.29537v1)），2026 年 6 月发布，把任务改成长时工作流——中位耗时 1.6 小时、平均 318 次工具调用（Claude Opus 4.7 配置下的数字）。在这个基准上，frontier 模型的最佳成绩是 **20% 左右**。同一时间点，OSWorld-Verified 上已经到 85%（Claude Fable 5，2026.06）。

**这两个数字之差是 GUI Agent 领域当前最值得注意的事实之一**。Adnan Masood 在 Medium 上的分析文章把 85% vs 20.6% 写进了副标题：[The Hardest Easy Problem in AI: The State of Computer Use Agents](https://medium.com/@adnanmasood/the-hardest-easy-problem-in-ai-the-state-of-computer-use-agents-a7e3aea7fa3a)（付费墙，仅摘要可见）。

### 4.3 为什么单步 99% 也撑不住长任务

数学上很简单：单步准确率 99%，100 步后理论成功率 0.99¹⁰⁰ ≈ 36.6%。50 步后也只有 60.5%。这条规律叫 **累积误差**（error accumulation），是任何串行决策系统都逃不开的约束。

OSWorld 2.0 论文里的实证更具体：任务时长与成功率严格负相关——任务 <45 分钟时 20-24%，137-163 分钟 <10%，超过 163 分钟所有模型都趋近 0%。这印证了一个直觉：**GUI Agent 现在能干的还是短任务，长任务根本接不住**。

> **一个有用的问题：当你看到厂商报 "OSWorld 90%" 时，先问一句——是 OSWorld 1.0 标准版（15-50 步的短任务）还是 OSWorld 2.0（小时级的长任务）？两个基准差异大到可以决定一个产品能不能落地。**

### 4.4 grounding 比规划更底层

OSWorld 论文自己点出了主要失败原因：**GUI grounding 与操作知识**。换句话说，模型还没到"不会规划"那一步，它在"找不到正确的按钮"那一步就已经失败了。ScreenSpot-Pro 上 GPT-4o 仅 0.8% 的数据，和 OmniParser 把这个数字抬到 39.6%，都在重复同一件事——**grounding 是比规划更底层的瓶颈**。

这就解释了为什么这两年大家拼命卷的不是更大的模型，而是合成 grounding 数据（[UGround](https://arxiv.org/abs/2410.05243) 训了 10M 元素）、专门做 grounding 的小模型（[Phi-Ground](https://arxiv.org/abs/2507.23779) 4B 在 ScreenSpot-Pro 上 55.0%，agent 设置下），以及把坐标当成离散分类问题来训练（[Watch and Learn](https://arxiv.org/abs/2510.04673) 的 IDM 离散化 0-999 整数）。

---

## 五、决策框架：什么时候该用 Computer Use

看清 GUI Agent 的能力边界后，工程师真正要决定的，是**什么时候该用它，什么时候不该**。

### 5.1 优先用结构化 API / MCP 的场景

Reflex.dev 做了一份实测（[2026-04 博客](https://reflex.dev/blog/computer-use-is-45x-more-expensive-than-structured-apis)），同一任务用 Computer Use 和结构化 API 各跑一遍：

| 指标 | Vision Agent（Claude Sonnet） | 结构化 API（Claude Sonnet） |
|---|---|---|
| 步数 | 53 ± 13 | 8 ± 0 |
| 墙钟时间 | 1003 秒（~17 分钟） | 19.7 秒 |
| Input tokens | 550,976 ± 178,849 | 12,151 ± 27 |

结论很硬：**Computer Use 比结构化 API 贵约 45 倍**，且方差极大。

> **所以决策的第一原则是：有 API 就别走像素，有 MCP server 就别走 GUI。**

具体场景包括：

1. 浏览器内操作（Playwright MCP 用 accessibility snapshot，token 开销远小于截图）
2. 有标准 API 的 SaaS
3. 需要确定性和可重复性的批处理
4. 涉及数据转换的工作流

### 5.2 必须走 Computer Use 的场景

但有些场景没有第二条路：[tianpan.co 这篇中文文章](https://tianpan.co/zh/blog/2026-04-10-computer-use-agents-when-pixels-replace-apis) 总结了四类：

1. **目标应用没有 API 也没有 accessibility tree**——遗留 ERP、内部管理面板、专有桌面应用
2. **UI 频繁变化**——硬编码的选择器每周都失效，视觉理解能适应
3. **任务本质是视觉的**——比较布局、读图表、验证渲染输出
4. **要验证"人类实际看到的内容"**——UI 测试自动化

OpenAI 官方文档里那句原话更直接："**Keep a human in the loop. Treat that as a security boundary, not a convenience feature.**" 翻译过来就是：Computer Use 的能力等于"用户能做的事"，这是安全边界，不是便利功能。

### 5.3 Hybrid 范式：当前的主流

端到端路线也在往前推：AutoGLM-OS-9B 以端到端在线 RL 把开源模型在 OSWorld 推到 48.9%（[2508.14040](https://arxiv.org/abs/2508.14040)，ComputerRL）。混合路线的代表是 Qwen-UI-Agent（阿里，[2607.28227](https://arxiv.org/abs/2607.28227)），把 GUI 与 CLI 交错执行，OSWorld-Verified 79.5%；EE-MCP（[2604.09815](https://arxiv.org/abs/2604.09815)，UCL、华为诺亚方舟实验室、北大等团队）量化了混合的收益：MCP 主导任务蒸馏带来 +17.8pp，GUI 密集任务经验库带来 +10.0pp。

综合下来，用 Computer Use 的判定标准是：**"API/MCP 走不通，且任务短于 50 步、长任务必须有状态管理"**。如果你的场景同时满足"有 API"和"对成本敏感"，哪怕 Computer Use 现在能跑通也不该上。

---

## 六、Harness：模型之外那个被忽略的胜负手

harness 就是模型以外那一整套工程——截图怎么采、动作怎么执行、上下文怎么管理、循环怎么防护、错误怎么恢复。模型只是其中一部分。

实在 Agent 90.2% 登顶 OSWorld 这件事，新华网那篇报道里有一段引述——"行业给这种工程能力起了一个名字：Harness，它决定了 AI 能不能把'想做的事'真正'做成'"（[新华网](https://www.xinhuanet.com/government/20260805/60bc929f7f0d4722b6ad4f4f22d90fcb/c.html)）。

回到前面的工程细节：

- DPI 强制 1x 是 harness
- MAX_STEPS 保险丝是 harness
- 动作-效果验证（[VeriGUI](https://arxiv.org/abs/2604.05477) 那类动作前后截图对比）是 harness

每一个细节都在拼"单步 99%"和"100 步 36%"之间那段距离。

> **如果说模型决定了 Agent 能走多远，harness 决定了它能不能走到。**

GUI Grounding 本身的技术演进还在继续——RL 训练（UI-TARS-2 多轮 RL、[GUI-R1](https://arxiv.org/abs/2504.10458) 仅 3K 数据超越 13M 数据基线）、长任务规划（OSWorld 2.0 的下一个主战场）这些方向都在向前推。但对当前要落地的工程师来说，先把 harness 做对，比追新模型更划算。

---

## 参考来源

* Anthropic Computer Use 官方文档：https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool
* Anthropic Computer & Browser Use Best Practices：https://claude.com/blog/best-practices-for-computer-and-browser-use-with-claude
* OpenAI Computer Use API 指南：https://developers.openai.com/api/docs/guides/tools-computer-use
* OpenAI Computer-Using Agent (CUA) 介绍：https://openai.com/index/computer-using-agent/
* OpenAI Operator System Card：https://openai.com/index/operator-system-card/
* UI-TARS（字节）：https://arxiv.org/abs/2501.12326
* UI-TARS-2：https://arxiv.org/abs/2509.02544
* Aguvis（Salesforce）：https://arxiv.org/abs/2412.04454
* CogAgent（THUDM）：https://arxiv.org/abs/2312.08914
* SeeClick + ScreenSpot：https://arxiv.org/abs/2401.10935
* Set-of-Mark (SoM)：https://arxiv.org/abs/2310.11441
* OmniParser：https://arxiv.org/abs/2408.00203
* UGround 数据集：https://arxiv.org/abs/2410.05243
* Phi-Ground（微软）：https://arxiv.org/abs/2507.23779
* Watch and Learn（IDM 离散化）：https://arxiv.org/abs/2510.04673
* GUI-R1：https://arxiv.org/abs/2504.10458
* OSWorld：https://arxiv.org/abs/2404.07972
* ScreenSpot-Pro：https://arxiv.org/abs/2504.07981
* SeeAct：https://arxiv.org/abs/2401.01614
* ComputerRL / AutoGLM-OS-9B：https://arxiv.org/abs/2508.14040
* EE-MCP（UCL、华为诺亚方舟实验室、北大等）：https://arxiv.org/abs/2604.09815
* VeriGUI（动作-效果验证）：https://arxiv.org/abs/2604.05477
* Qwen-UI-Agent：https://arxiv.org/abs/2607.28227
* OSWorld 2.0：https://arxiv.org/html/2606.29537v1
* Reflex.dev 成本对比：https://reflex.dev/blog/computer-use-is-45x-more-expensive-than-structured-apis
* Anthropic Quickstarts computer-use-best-practices：https://github.com/anthropics/claude-quickstarts
* microsoft/playwright-mcp：https://github.com/microsoft/playwright-mcp
* browser-use：https://github.com/browser-use/browser-use
* 新华网/财联社《中国智能体登顶OSWorld，90.2%成功率反超海外巨头》：https://www.xinhuanet.com/government/20260805/60bc929f7f0d4722b6ad4f4f22d90fcb/c.html
* Simular Agent S3 超人类基线：https://www.simular.ai/articles/simulars-computer-use-agent-outperforms-humans
* Tian Pan《生产环境中的 Computer Use 代理》：https://tianpan.co/zh/blog/2026-04-10-computer-use-agents-when-pixels-replace-apis
