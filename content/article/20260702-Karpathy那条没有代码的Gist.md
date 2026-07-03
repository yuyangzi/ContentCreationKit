# Karpathy那条没有代码的Gist，凭什么火遍全网

> **导读**：2026年4月，Karpathy在GitHub上发布了一份Gist，标题叫"LLM Wiki"——没有代码，没有产品，只是一份markdown格式的idea file，描述了一种用LLM编译和维护个人知识库的方法。

---

"Karpathy又封神，掀翻RAG。"

7月1日，36氪和新智元用这个标题把一份三个月前的GitHub Gist重新推到中文读者视野里。点进去之前，你大概率以为Karpathy又发布了一个新产品或者开源了一个框架。点进去之后你会发现——什么都没有。没有GitHub仓库，没有pip install，没有可运行的demo。

只有一份markdown文件。

这份Gist创建于2026年4月4日，标题是"llm-wiki.md"。Karpathy在文件开头写得很清楚："This is an idea file, it is designed to be copy pasted to your own LLM Agent."翻译过来：这不是产品，你拿去看，看完贴给你的AI Agent用。

但它确实产生了一些东西。逾万star，数千fork，以及一个正在形成中的——没有代码的——生态。

---

## 把知识当源代码，让LLM当编译器

Karpathy提出的方案，核心思路一句话就能说清楚：**把知识当源代码，让LLM当编译器。**

传统的RAG是这样工作的：你把文档切成小块，存成向量，每次用户提问时从向量库里搜出相关片段，塞进prompt让LLM回答。每一次查询，本质上都是一次"从零重建知识"的过程——检索、拼接、理解、回答，然后扔掉，下次再来一遍。

Karpathy觉得这条路在个人知识管理场景里走歪了。他的原话是"rediscovering knowledge from scratch on every question"——每次提问都在重新发现知识。替代方案：不要每次都检索，提前编译好。

具体怎么做？三层架构：

1. **Raw（原始素材层）**——收集的文章、论文、笔记原文，只读不写，来源可追溯
2. **Wiki（知识层）**——由LLM全权维护的markdown文件，结构化，交叉链接，随时更新
3. **Schema（约定层）**——类似CLAUDE.md或AGENTS.md的指令文件，告诉LLM怎么组织、维护、遵循什么规范

三种操作：

- **Ingest（摄入编译）**——新素材喂给LLM，LLM阅读、提取、结构化，更新Wiki
- **Query（查询存档）**——直接查已编译的Wiki，不需要重新检索原始素材
- **Lint（健康检查）**——定期检查Wiki质量：有没有过时内容、矛盾表述、死链接

Karpathy自己用这套方法维护着一个约100篇文章、40万词规模的知识库，全部由LLM编写和维护。他在Gist里说："You never (or rarely) write the wiki yourself — the LLM writes and maintains all of it."

Gist原文里有一句最能概括这套方案哲学的话："**Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase.**"Obsidian是IDE，LLM是程序员，Wiki是代码库。人类的工作从"写笔记"变成了"curate sources, direct the analysis, ask good questions, and think about what it all means"——筛选素材、引导分析、提出好问题、思考这些意味着什么。

---

## "编译一次，多次使用"

RAG和LLM Wiki之间最根本的区别，不在于技术路线，而在于对"知识"的理解。

RAG把知识当成一个需要被"查找"的东西。你问一个问题，系统去翻书，找到相关段落，拼给你。这个过程无状态——上一次查询和下一次之间没有任何积累。你问了十次同一个问题，它翻了十次书。

Karpathy的方案把知识当成一个需要被"维护"的东西。素材来了，编译进Wiki。之后每次查询都直接使用已编译的知识，不需要从原始素材重新搜。知识会累积——你今天读了一篇论文，Wiki更新了；下周再问相关问题，Wiki里已经有结构化过的内容。

"编译"这个隐喻很精准。编译一次成本高，之后每次使用都便宜。增量编译——新素材只触发受影响页面的更新。可审计性也不同。RAG的向量嵌入是个黑箱——你不知道为什么搜出这段而不是那段，也不知道遗漏了什么。LLM Wiki的输出是纯markdown，你可以逐行检查LLM写了什么、改了什么、为什么这么组织。

---

## 个人端的范式在变，企业端的问题没解决

不过这套方案有一个Karpathy自己也不讳言的局限：规模。他在Gist里明确写了这是在"moderate scale (~100 sources, ~hundreds of pages)"场景下的方案。当文档量级达到企业级——数万份合同、几十万封邮件、跨部门异构数据——向量检索加语义匹配仍然是更务实的选择。MindStudio和Towards AI的多篇分析也指向同一个结论：LLM Wiki在个人和小团队场景下优于RAG，但大规模文档检索，RAG的问题虽多，至少它跑得起来。

所以准确地说，目前来看正在发生的是：**个人端的知识管理逻辑正在从"搜索式"向"记忆式"迁移，而企业端的RAG问题依然没有解决。**

这里并不是在讨论"RAG和LLM Wiki哪个更好"，而是"你的知识是什么类型的"。如果是需要反复查阅、持续维护、不断深化的私人知识——读过的论文、研究过的课题、长期跟踪的领域——编译一次反复使用确实比每次都从零检索更合理。如果是偶尔需要查一次的海量文档——公司档案、客户邮件、合规文件——RAG的按需检索是正确的选择。

我甚至不觉得企业端的问题短期内能被LLM Wiki这种方案解决。企业知识管理的复杂度不完全在技术——权限体系、合规要求、版本管理、跨部门语义对齐——这些维度RAG已经吃力了，编译式架构只会更难。但个人端的变化是真实的，而且正在加速。

---

## 当AI开始"记得你知道什么"

RAG模式下，AI每次对话都是从零开始的——它不知道你昨天问过什么、上周读过什么、上个月研究过什么。

LLM Wiki改变了这件事。Wiki是你的外部记忆，LLM维护着这份记忆。当你问"上次我们讨论过的那篇论文里的实验方法"，它不需要重新检索——Wiki里已经有结构化的记录，LLM知道你在说什么。

这不只是一个技术改进。它改变的是人与AI的关系。

从"你问它答的工具"变成"它记得你知道什么的协作者"。

这件事如果做得好，对个人知识管理的影响可能超出目前的想象。我们读过的很多东西，最终并没有变成能用得上的知识。不是因为我们不认真，而是因为人类的工作记忆和长期记忆之间的转化过程本来就有大量损耗。读十篇论文，三个月后能清晰回忆的可能只有两篇的核心观点。

LLM Wiki提供了一种可能性：你不是把笔记"存起来"，而是让AI帮你"消化并结构化"，然后成为你可以随时调用的外部认知。不是第二大脑的存储功能，是第二大脑的回忆功能。

但这里有一个很现实的危险：LLM编译的知识如果出现错误，问题会非常隐蔽。若在更新Wiki时误解了某篇论文的结论，基于此生成的交叉链接和推论都会偏移，而错误传播隐身在结构化内容中，难以被察觉。Karpathy的方案里，Lint操作的设计初衷就是应对这个问题——但Lint本身也是LLM在执行，它能不能识别自己的错误，这件事并没有得到验证。

这是整个方案目前最薄弱的环节。编译式知识管理要真正可信，需要解决的问题不在"能不能编译"，而在"编译错了怎么办"。

---

我不觉得Karpathy在一个Gist里写的东西是什么"技术突破"。三层架构、三种操作、编译式隐喻——这些都不新鲜。新鲜的是他把它写出来了。

个人知识管理这件事，RAG跑了好几年，体验始终差点意思。现在多了一条路。

*参考来源：*
- Andrej Karpathy, "llm-wiki.md" (GitHub Gist, 2026-04-04): [https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f)
- Karpathy X推文 "LLM Knowledge Bases" (2026-04-03)
- 新智元/36氪, "Karpathy又封神，掀翻RAG" (2026-07-01): [https://www.36kr.com/p/3876746138415108](https://www.36kr.com/p/3876746138415108)
- MindStudio, "Where RAG Breaks Down: The Karpathy LLM Wiki Alternative"
- HTX Insights, "Karpathy's Genius Strikes Again" (2026-07-01)
- Analytics Drift, "Karpathy's LLM Knowledge Base Workflow Explained" (2026-04-05)
- Techstrong.ai, "Karpathy's Instructions for Building an AI-Driven Second Brain" (2026-04-07)
- Towards AI, "Your Second Brain Doesn't Need RAG. It Needs a Map"
- LabGrimoire, "Knowledge Compilation Over Knowledge Retrieval" (2026-05-09)
- Vannevar Bush, "As We May Think" (The Atlantic, 1945)
- LLM Wiki Newsroom (GitHub: alfadur7/llm-wiki-newsroom)
- trip2g MCP Server
- Equational Applications expo-llm-wiki (GitHub: equationalapplications/expo-llm-wiki)
- projectbrain.md (GitHub: mindmuxai/brain.md)
