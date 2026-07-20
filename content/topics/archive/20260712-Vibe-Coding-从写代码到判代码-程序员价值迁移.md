# Vibe Coding 之后：当 AI 写代码，程序员判代码

## 热度背景

2026 年 7 月，三件事在中文技术社区形成了共振：

**第一件**：知乎"你觉得 Vibe Coding 是昙花一现还是真的在改变编程这件事？"话题获得 113 万热度。讨论已从"这是什么"进化到"什么时候用、什么时候不用"——但连这个词的发明者 Karpathy 本人都已在 2026 年 2 月弃用它，改称 "agentic engineering"。

**第二件**：2026 年 3 月被 OpenAI 以九位数美元收购的 Python 包管理工具 uv 的创始人 Charlie Marsh，在 6 月的播客中坦言：用 GPT-5 写了一个内部工具后"一行代码都没读就发布了"。但比这句话更有冲击力的是他的另一句坦白——"团队现在不信任我的 PR 了。以前他们觉得不需要仔细审查我的代码，现在我用 Claude Code 提交的 PR 里确实有我手写时不会出现的错误。"

**第三件**：Linux 和 Git 之父 Linus Torvalds 在 2026 年 6 月孟买的开源峰会上，系统性地谈了他对 AI 编程的最新看法。他说 LLM 是"创可贴式补丁"——修复了眼前问题，同类 bug 还在走廊里等着从另一个地方跳出来打你。他 5 月在明尼阿波利斯还说过一句更狠的话："看到有人说 99% 的代码是 AI 写的，我就来气——我保证他们 100% 的代码是编译器生成的，但他们从不这么说。"

**三件事指向同一个问题**：当 AI 能写出 90% 的代码时，剩下 10% 的判断力、架构品味、工程直觉，才真正定义了程序员的价值。我们正在经历的不只是工具升级，而是**程序员核心技能从"写代码"到"判代码"的迁移**。

## 类型标签

- AI 编程
- 开发者生态
- 软件工程
- 编程范式

## 创作方向

### 叙事线：三层递进

1. **现象层 — Vibe Coding 没死，它进化了**
   - 从 Karpathy 弃用"vibe coding"切入——这个词死了，但现象在加速
   - 数据面：92% 采用率 vs 33% 信任度、1.7x 缺陷率、45% AI 代码含漏洞
   - 核心张力：用得越多，信得越少

2. **冲击层 — 最懂 AI 编程的人也在挣扎**
   - Charlie Marsh 自白：团队不信任他用 AI 写的 PR
   - "提交成本为零，审核成本不变"——开源社区正在被 AI PR 淹没（cURL 漏洞悬赏关停、Linus 安全列表失控）
   - 矛盾在于：连创造工具的人都无法完全信任工具产出

3. **定调层 — Linus 的冷静剂**
   - 编译器类比：编译器生成 100% 机器码，没人说软件是"编译器写的"。AI 占据的是同样的位置
   - "创可贴补丁"比喻：AI 擅长修复症状，不理解病因
   - 但 Linus 也说：净产出已经开始为正——"希望它创造的生产力已经超过它消耗的"

### 核心论断

**程序员的价值正在从"写代码"迁移到"判代码"。**

当 AI 接管了语法细节、样板代码、常规逻辑，程序员的核心竞争力变成了：判断 AI 的代码对不对、好不好、适不适合这个系统。这不是降级——写代码从来不是程序员最有价值的技能，判断力才是。

### 关键数据锚点

| 维度 | 数据 | 来源 |
|------|------|------|
| 采用 vs 信任 | 84% 使用，仅 33% 信任 | Stack Overflow 2025 |
| 缺陷密度 | AI 代码 1.7x 人类 | CodeRabbit |
| 安全漏洞 | 45% 含 OWASP Top 10 | Veracode |
| 生产力悖论 | 资深者复杂任务慢 19%，自认为快 20% | METR 2025 |
| 重构萎缩 | 从 25% → 不足 10% | GitClear |
| 代码流失 | AI 代码 12-18%，人类 5.7% | Larridin |

## 来源链接

### Vibe Coding
- 知乎话题：https://www.zhihu.com/question/2056791474608366568
- Karpathy 原推：https://x.com/karpathy/status/1886192184808149383
- Wikipedia：https://en.wikipedia.org/wiki/Vibe_coding
- GitClear：https://www.gitclear.com/the_ai_code_quality_maintainability_gap
- CodeRabbit：https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report
- METR：https://metr.org/blog/2026-02-24-uplift-update/

### uv 创始人
- InfoQ：https://www.infoq.cn/article/katE2jJKMX7FaGskhvRL
- The Peterman Pod（原播客）：https://youtu.be/Iw65FD4MGgs
- 文字稿：https://www.developing.dev/p/openai-eng-and-dev-tools-founder
- OpenAI 收购公告：https://openai.com/index/openai-to-acquire-astral/

### Linus Torvalds
- InfoQ 全文编译：https://www.infoq.cn/article/11fNtPYf59T76fyQkiPa
- 36氪：https://www.36kr.com/p/3885475579211783
- LWN：https://lwn.net/Articles/1073761/
- The New Stack：https://thenewstack.io/torvalds-ai-programming-productivity/
- OSS India 2026 视频：https://www.youtube.com/watch?v=YKkEe-PxW10
