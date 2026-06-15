# 从零搭 RAG 到用 LangChain 重构——阶段二：给 Agent 装上知识手脚

阶段一收尾的时候我说过一句话：你已经理解了 Agent 怎么思考，接下来让它知道更多。

"知道更多"这件事，初看很简单——给 LLM 接个搜索引擎不就行了？但真动手的时候你会发现，RAG 不是接个 API 就完事。文档怎么切、切多细、用什么模型把文字变成向量、向量搜出来的东西怎么保证和用户的问题有关——每一步都有坑。而且这些坑不是 LangChain 藏起来的，是 RAG 本身的结构性问题。

LangChain 的问题刚好反过来。它的坑是自己挖的——API 变得比天气还快，你三个月前照着官方 tutorial 写的代码，今天跑起来满屏 deprecation warning。但面试还在考它，社区大量教程还在用它，你不学不行。

这篇要做的事：先用最裸的方式搭一个 RAG 系统——ChromaDB 直接 API，sentence-transformers 直接调——理解每一环在干什么。然后用 LangChain 把同样的东西用几行代码重写一遍，感受一下"原来你帮我干了这些"的透明感。最后把 RAG 塞进你在阶段一写的 Agent Loop 里，再加两个工具——一个查数据库，一个存文件——做出一个真正能用的文档问答 Agent。

和阶段一一样，所有代码都能跑。不是 Jupyter Notebook 片段，是完整的 Python 脚本。

---

## 你的 Agent 为什么需要 RAG

先用一个例子说清楚问题。

你随便找个模型，问它"上周 GitHub trending 第一是什么项目"。它会编一个答案——看起来很像真的，有项目名，有描述，甚至可能给你一个假的 star 数。这不是幻觉，是它真的不知道。LLM 的知识停在训练截止日期，训练完之后世界发生了什么，它一概不知。

但你不希望 Agent 也这样。你希望它接到一个问题之后，能自己去查、去搜、去读它没见过的东西。这就是 RAG（检索增强生成）——在 LLM 生成回答之前，先检索相关文档，把检索结果塞进上下文窗口，让 LLM 基于这些刚查到的资料来回答，而不是从训练数据的记忆里瞎编。

### 一个最小 RAG 管道长什么样

```
[离线]  文档 → Chunking → Embedding → 存入向量数据库
                                           ↓
[在线]  用户提问 → Embedding → 向量检索 → 取回 Chunk → 拼进 Prompt → LLM 回答
```

每一步都有决策点。Chunk 切多大？用什么 Embedding 模型？向量检索和关键词检索要不要混用？检索回来的东西怎么保证和问题有关？下面挨个拆开。不跳步骤——你会在每一环亲手写代码。

---

## 模块一：从零搭一个 RAG（先裸写，再 LangChain 重构）

### Chunking：你切的不是文档，是上下文

RAG 的第一步是把文档切成小块（chunk）。为什么切？两个原因。一是 Embedding 模型有输入长度限制——你不能把一本 500 页的书整个塞进去。二是检索精度——chunk 太大，包含的噪音太多，LLM 容易被无关信息带偏；chunk 太小，丢失上下文，LLM 看不懂这段在说什么。

三种主流策略：

**固定长度切分**。每 N 个字符切一刀。最简单，也最粗糙。一句话可能被拦腰切断，前半句在 chunk A，后半句在 chunk B。召回的时候要么两个都召回（浪费 token），要么只召回一个（丢失语义）。

**语义切分**。用分隔符（句号、换行、段落）找自然断点。比固定长度好，但对代码、表格、日志这种不以自然语言为边界的文档效果很差。

**递归切分**。先按段落切，太长了按句子切，还太长按字符切。这是 LangChain 的 `RecursiveCharacterTextSplitter` 的默认策略，也是大多数场景下的最佳起点——但它不是什么魔法，你用 Python 原生也能写。

```Python
# 裸写：递归切分，500 字一块，重叠 50 字
def recursive_split(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks

with open("data/knowledge_base.txt", "r", encoding="utf-8") as f:
    raw_text = f.read()

chunks = recursive_split(raw_text)
print(f"切成了 {len(chunks)} 个 chunk")
```

chunk 之间的 overlap（重叠）是一个容易被跳过的细节。假设你按 500 字分块，每块之间重叠 50 字——这 50 字是上下文锚点，保证切在边界上的信息不会被割裂。overlap 太小，语义断裂；overlap 太大，冗余信息吃掉 token 预算。500/50 是一个合理的起点，但实际值取决于你的文档结构——教程类文档段落短，overlap 可以小一些；论文类文档论证链长，overlap 可能需要更大。

一个重要的简化：这篇用 txt 文本文件做数据源，不是 PDF。PDF 解析——版面检测、表格提取、OCR——本身就是一个复杂话题，会分散你对 RAG 核心概念的注意力。用 `open()` 直接读，零解析复杂度。真实场景中你只需要替换文件读取那一行，chunking 和后续流程完全不变。

### Embedding：文字怎么变成数字

切完文档之后，你需要把每个 chunk 变成一个向量（一组数字）。这个过程叫 Embedding。这个向量的核心属性是：语义相近的文字，向量也相近。

"北京是中国的首都"和"中国的首都在北京"两个 chunk，它们在向量空间里的距离很近——因为它们说的是一件事，尽管措辞不同。反过来，"北京是中国的首都"和"今天天气不错"距离很远——尽管它们都是中文短句。

Embedding 模型的选择直接影响检索质量。几个关键考量：

**领域对齐**。通用 Embedding 模型（如 OpenAI 的 `text-embedding-3-small`）在通用文本上表现不错，但在医疗、法律、金融等垂直领域需要对应领域微调的专用模型——通用模型在这些场景的召回率掉得很厉害。

**中文场景**。如果你的文档是中文，BGE 系列（`bge-large-zh-v1.5`）是社区验证过的首选。它不针对某个垂直领域，但在通用中文场景下的语义理解比多语言模型有明显优势。

**维度**。向量维度越高，表达能力越强，但存储和检索越慢。OpenAI 的 `text-embedding-3-small` 是 1536 维，`text-embedding-3-large` 可以调到 3072 维。但你不一定需要大模型——取决于你的文档有多复杂。

**多语言**。纯中文文档用中文 Embedding 模型（`bge-large-zh-v1.5` 等），中英混合文档用多语言模型（`paraphrase-multilingual`）。用错模型的结果不是你想象中的"差一点点"——用多语言模型查纯中文文档，检索精度可能直接腰斩（我踩过这个坑，查了一下午才发现 Embedding 模型选错了）。

```Python
# 裸写：用 sentence-transformers 直接做 embedding
from sentence_transformers import SentenceTransformer

embedder = SentenceTransformer("BAAI/bge-small-zh-v1.5")  # 中文轻量，512 维
chunk_vectors = embedder.encode(chunks)  # 每个 chunk 变成一个 512 维向量
print(f"第一个 chunk 的向量形状：{chunk_vectors[0].shape}")
```

### 向量数据库与检索：存进去，搜出来

有了向量，你需要一个地方存它们——向量数据库。它本质上是一个支持"找最相似的 N 个向量"的高效索引。ChromaDB 是学习阶段的最佳选择：`pip install` 就能用，零配置，API 直觉。生产环境你会换 Milvus 或 Pinecone，但现在没必要——先理解检索是怎么发生的。

```Python
# 裸写：ChromaDB 直接 API
import chromadb

client = chromadb.Client()
collection = client.create_collection("knowledge_base")

# 存入：每个 chunk 配一个 id 和它的向量
for i, (chunk, vector) in enumerate(zip(chunks, chunk_vectors)):
    collection.add(
        ids=[f"chunk_{i}"],
        documents=[chunk],
        embeddings=[vector.tolist()]
    )

# 检索：用户提问 → embedding → 找最相似的 3 个 chunk
query = "Agent 的 finish_reason 是什么意思"
query_vector = embedder.encode([query])[0].tolist()
results = collection.query(query_embeddings=[query_vector], n_results=3)

for doc in results["documents"][0]:
    print(doc[:200], "...")
```

到这里，你已经搭好了一个最小可行的 RAG 系统。不算 chunking，整个流程 20 行 Python。它能跑，能搜，能把相关文档片段捞出来。

但它还不够好。

### 为什么纯向量检索不够

向量检索擅长"语义相近"——"finish_reason 是什么"能匹配到"LLM 停止生成的原因"这类文字。但它不擅长"精确匹配"——用户问"commit abc123 是谁写的"，向量检索可能给你一堆关于 git commit 的文档，但就是找不到那个具体的 hash。

这就是关键词检索不可替代的地方。关键词检索（BM25）不讲语义，只讲词频——一个词在文档中出现越多次、在全集中出现越少，这个词对这篇文档就越"关键"。它对精确匹配（ID、错误码、日期、专有名词）的召回率远高于向量检索。

这两种检索是互补关系，不是替代关系。向量检索管"意思相近"，BM25 管"字面匹配"。所以生产级的 RAG 几乎都做混合检索（Hybrid Search）——两路并行，然后把结果融合。融合策略里最常用的是 RRF（Reciprocal Rank Fusion）：

```
score(doc) = Σ 1/(k + rank_i(doc))
```

k 是一个常数（通常取 60），`rank_i(doc)` 是文档在第 i 路检索中的排名。这个公式的直觉很简单：两路都排在前面的文档得高分；只有一路排在前面另一路排很后面，得分会大打折扣。

LangChain 里有现成的封装，但你现在已经知道它下面在算什么了。

### Rerank：粗排之后还要精排

即使加了混合检索，你取回的 top_k 个 chunk 也只是"粗排"结果——它们是相对于查询向量的最近邻，但这不意味着它们和用户的问题真的有因果关系。

Rerank 模型做的事：把 {查询，每个候选 chunk} 组成的 pair 喂给一个专门训练来做"这个 chunk 能不能回答这个查询"的模型，重新打分。Rerank 比 Embedding 慢（因为它要对每个 pair 做交叉编码，而不是单独编码），但精度显著更高——在 MTEB 等标准 benchmark 上，Rerank 后的 top-3 召回率通常能提升 20%-50%，具体取决于你的文档领域和 Embedding 模型选型。

一个实用的策略：粗排取 top-20 → Rerank 精排取 top-3 → 塞进 Prompt → LLM 回答。粗排保证召回率（不错过可能的答案），精排保证精度（LLM 只看到最相关的上下文）。

```Python
# Rerank：对粗排结果重新打分
from FlagEmbedding import FlagReranker

reranker = FlagReranker("BAAI/bge-reranker-v2-m3")
candidates = collection.query(query_embeddings=[query_vector], n_results=20)

# 每个候选 chunk 和查询组成 pair，重新计算相关性分数
pairs = [(query, doc) for doc in candidates["documents"][0]]
scores = reranker.compute_score(pairs)

# 取 top-3
top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
for idx in top_indices:
    print(f"Score: {scores[idx]:.4f} | {candidates['documents'][0][idx][:100]}...")
```

### 用 LangChain 重构：同样的流程，十分之一的代码

还记得阶段一的模式吗——先用原生代码理解每一行，再用框架重写，"原来你帮我干了这些"。RAG 也一样。

这是你刚才用了三十行代码搭出来的 RAG 流程，LangChain 版（注意：以下 import 适用于 langchain>=1.3，旧版本需要从不同的子包导入）：

```Python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_chroma import Chroma

loader = TextLoader("data/knowledge_base.txt")
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
embedder = HuggingFaceEmbeddings(model_name="BAAI/bge-small-zh-v1.5")

# 加载 → 切块 → Embedding → 存入向量数据库，一条链
docs = loader.load()
chunks = splitter.split_documents(docs)
db = Chroma.from_documents(chunks, embedder)

# 检索
results = db.similarity_search("Agent 的 finish_reason 是什么意思", k=3)
```

你是不是觉得少了点什么？少了你手写的那些 for 循环、id 管理、向量转 list、手动调用 `collection.add` 和 `collection.query`。LangChain 把这些全打包在了 `TextLoader`、`RecursiveCharacterTextSplitter`、`HuggingFaceEmbeddings`、`Chroma.from_documents` 四个类里——封装了三十行，同时暴露了你可以替换的每一个环节。换数据源？换一个 Loader。换切分策略？换一个 Splitter。换 Embedding 模型？第二个参数换掉。

省了代码，但你知道每一行下面在发生什么。这就是"原理先行"的兑现。

> **RAG 的坑地图。** Chunk 切太细 → 丢失上下文，LLM 看不懂片段在说什么。Embedding 模型和文档领域不匹配 → 再好的检索策略也救不回来。只做了向量检索没做 BM25 → 精确查询（ID、错误码）的召回率接近零。Rerank 没加 → 粗排结果里混进了大量"看起来相关"但不是真答案的文档。这些问题不是 bug，是 RAG 管道每个环节都对的、但组合起来仍可能失败的 design failure。

---

好，现在我们终于可以回到 Agent 本身了。RAG 管线搭好了，但它还只是"一段能检索的代码"，不是 Agent。让这段代码成为 Agent 的一部分，是你接下来要做的事。

---

## 模块二：从 Mini Loop 到 LangChain Agent

### 你的 Agent Loop 和 LangChain 的 Agent 本质上是同一段代码

阶段一里你写了一个 Mini Agent Loop——一个 while 循环，每轮问 LLM"你要说话还是调工具"，如果调工具就执行然后把结果塞回 messages，如果说话就返回。核心代码四十行。

LangChain 的 `create_agent` 做的事一模一样。

```Python
# 阶段一原生 Agent Loop（简化）
def run_agent(user_message):
    messages = [system_prompt, user_message]
    for _ in range(max_turns):
        response = client.chat.completions.create(
            model="deepseek-v4-flash", messages=messages, tools=tools, tool_choice="auto"
        )
        msg = response.choices[0].message
        if msg.tool_calls:
            messages.append(msg)
            for tc in msg.tool_calls:
                result = tool_map[tc.function.name](**json.loads(tc.function.arguments))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": str(result)})
        else:
            return msg.content
```

```Python
# LangChain 版
from langchain.agents import create_agent

agent = create_agent(model=llm, tools=tools, system_prompt="你是一个助手")
result = agent.invoke({"messages": [{"role": "user", "content": "帮我查一下"}]})
```

那个 while 循环、`finish_reason` 检查、`tool_calls` 解析、工具结果回传——全被 `create_agent` 一行封装了。你花两天写的 100 行代码，LangChain 用一行解决。但你知道里面在干什么——你不会被黑盒吓到，因为你在阶段一亲手写过那个循环，你知道 `messages.append(msg)` 不能省是因为 LLM 下一轮需要知道自己上轮调了什么工具，你知道 `tool_call_id` 必须精确匹配否则 LLM 会忽略返回值。

读到这你可能会想：那 LangChain 到底给我省了什么？不只是代码行数。它帮你处理了你很难处理的东西——`parallel_tool_calls` 的并发执行、`tool_choice` 和 `finish_reason` 的边界情况、流式输出中 tool_call 的分块聚合。这些你用原生代码也能写，但要写对需要踩很多坑。

### API 变更：为什么你搜到的教程大概率是错的

2026 年 6 月，LangChain 已经进化到 1.x 了。你在网上搜到的教程——特别是 2024 年的——十个有八个用的还是旧 API。

| 旧 API（已废弃） | 当前 API（langchain==1.3.9） |
|---|---|
| `create_react_agent`（langgraph.prebuilt） | `create_agent`（langchain.agents） |
| `RunnableWithMessageHistory` | `checkpointer=InMemorySaver()` 直接传参 |
| `ConversationBufferMemory` | 不再需要单独 memory 层，checkpointer 统一管理 |
| `LLMChain` | LCEL：`prompt \| model \| StrOutputParser()` |

如果你照着 2024 年的教程写 `AgentExecutor` 或 `RunnableWithMessageHistory`，pytest 会直接炸（别问我怎么知道的）。当前版本 `langchain==1.3.9`、`langgraph==1.2.5`（验证于 2026-06-14）。

这道坎你必须过。不是因为 LangChain 值得你花时间学 API 变更——而是因为面试还在考它，社区还在用它。你至少要能分辨旧代码和新代码。

### Memory：多轮对话不需要重新发明轮子

你的原生 Agent Loop 有一个明显的问题：每次调用 `run_agent()` 都是全新的对话。LLM 看不到上一轮你问过什么、它回答过什么。用户说"再帮我查一次那个地方"，Agent 会傻眼——"那个地方"是哪儿？

阶段一里没讲 Memory，因为当时的目标是理解 Agent Loop 的决策机制。现在该加了。Memory 的本质是一件事：在 Agent 的多轮调用之间，持久化 messages 数组。不是什么神秘的"记忆模块"——就是一个能存能取的聊天记录。

LangChain 的做法：

```Python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

agent = create_agent(
    model=llm,
    tools=tools,
    checkpointer=InMemorySaver()  # 教程用；生产环境换 PostgresSaver
)

config = {"configurable": {"thread_id": "user-123"}}

agent.invoke({"messages": [{"role": "user", "content": "我叫张三"}]}, config)
agent.invoke({"messages": [{"role": "user", "content": "我叫什么名字？"}]}, config)
# Agent 回答"张三"——checkpointer 记住了上一轮的 messages
```

同一个 `thread_id` 的所有调用共享上下文。`InMemorySaver` 存在内存里——进程重启就没了，所以只适合开发。生产环境换 `PostgresSaver`。

### Chains 和 LCEL：管道的乐高感

除了 Agent 和 Memory，LangChain 还有一个你用原生代码不太好表达的概念——链（Chains）。

回头看你的 Agent Loop。它是一个硬编码的、不可拆分的 while 循环——LLM 调用、工具执行、结果回传，全写死在同一个函数里。但有时候你不想这么重。你只是想"把用户问题翻译成英文 → 调 LLM → 解析输出为 JSON"——这不需要工具调用，不需要 while 循环，只需要一个管道。

这就是 LCEL（LangChain Expression Language）的价值：

```Python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个翻译助手，把用户输入翻译成英文。"),
    ("user", "{input}")
])

chain = prompt | model | StrOutputParser()
result = chain.invoke({"input": "今天天气真好"})
# "The weather is really nice today."
```

`|` 操作符让管道读起来像数据流动的方向：输入经过 prompt 模板，进入 model，最后被 parser 解析出来。每个环节是一个 `Runnable` 对象，支持 `.invoke()`、`.stream()`、`.batch()` 统一接口。说实话，大多数人日常用 LangChain 最频繁的不是 `create_agent`，就是 `|`。

---

到这里，你有了三样东西：一个能检索文档的 RAG 管线，一个能用工具的多轮对话 Agent，还有一个管道思维（LCEL）。接下来把它们揉成一个整体。

---

## 模块三：多工具集成——一个 Agent，三个数据层

### 统一项目：文档问答 Agent 从头长到尾

这个系列不搞"每章一个新 demo"——阶段一一个项目打通了 Agent Loop，阶段二也只有一个项目。它从模块一的 RAG 管线开始，模块二加了 Memory 和 Agent 壳，模块三再加两种"手"：查数据库（结构化数据）和存文件（持久化输出）。

三种能力对应三种数据层。Agent 在面对一个问题时，需要自主判断"这个问题该查文档、查数据库、还是直接存文件"——不是三个独立的功能演示，是一个 Agent 同时拥有三种工具。

### 工具一：文档检索

直接把模块一的 RAG 管线包装成一个 Tool：

```Python
from langchain_core.tools import tool

@tool
def search_docs(query: str) -> str:
    """在知识库中搜索相关文档。当用户询问技术概念、定义、原理时使用此工具。"""
    results = db.similarity_search(query, k=3)  # db 是模块一的 Chroma 实例
    return "\n\n".join([doc.page_content for doc in results])
```

一行 `db.similarity_search` 触发整个 RAG 管线：查询向量化 → 向量检索 → 返回最相关的 chunk。你可以在内部加 Hybrid Search 和 Rerank，但对外面 Agent 来说，它只看到一个"输入查询，返回文档"的黑盒工具。Tool 的 `description` 告诉 LLM 什么时候该用它——不是你手动 if-else，是 LLM 自己判断。

### 工具二：数据库查询

文档检索管非结构化数据。但真实场景里，很多数据是结构化的——员工表、订单记录、日志。Agent 需要能查数据库。

```Python
@tool
def query_database(sql: str) -> str:
    """在 SQLite 数据库中执行 SQL 查询。当用户要求查找、统计、筛选数据时使用此工具。
    数据库包含 'employees' 表，字段：id, name, department, salary。"""
    conn = sqlite3.connect("data/company.db")
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
        return str(cursor.fetchall())
    except Exception as e:
        return f"SQL 错误：{e}"
    finally:
        conn.close()
```

这里的关键是 description。你告诉 LLM 这个数据库有什么表、什么字段，它就能把自然语言问题翻译成 SQL——"技术部工资最高的三个人是谁"变成 `SELECT name, salary FROM employees WHERE department='技术部' ORDER BY salary DESC LIMIT 3`。LLM 的 SQL 生成能力在简单查询上已经很可靠。安全方面注意一条：这是本地 SQLite，不要让它连生产数据库。

### 工具三：文件保存

直接复用阶段一的 `write_file`，加 Harness 权限控制：

```Python
import os

ALLOWED_DIRS = ["./output", "./data"]

@tool
def save_to_file(filename: str, content: str) -> str:
    """将内容保存到本地文件。当用户要求保存、导出、记录信息时使用此工具。"""
    if not any(os.path.abspath(filename).startswith(os.path.abspath(d)) for d in ALLOWED_DIRS):
        return f"错误：无权写入 {filename}。允许的目录：{ALLOWED_DIRS}"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    return f"成功写入 {filename}"
```

`ALLOWED_DIRS` 是阶段一 Harness Engineering 的产物——Agent 能做的事，是你明确允许它做的事。约束放在工具函数里，不是放在 System Prompt 里——因为 LLM 不会主动帮你在调用前检查权限。

### 完整组装

三种工具，一个 Agent，一条命令：

```Python
from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="deepseek-v4-flash",
    api_key="your-key",
    base_url="https://api.deepseek.com"
)

agent = create_agent(
    model=llm,
    tools=[search_docs, query_database, save_to_file],
    system_prompt="""你是一个文档问答助手，可以搜索知识库、查询数据库、保存文件到本地。""",
    checkpointer=InMemorySaver()
)

config = {"configurable": {"thread_id": "user-123"}}
result = agent.invoke(
    {"messages": [{"role": "user", "content": "技术部有多少人？把结果存到 output/tech_count.txt"}]},
    config
)
```

这条消息会触发一个多步决策链：LLM 先判断"技术部有多少人"需要调 `query_database`，拿到结果后判断"把结果存到 output/tech_count.txt"需要调 `save_to_file`，两个工具先后执行，最终回复用户。不是两个独立调用——是 Agent 在一个决策序列中连续推理。

**三种工具之间的层次关系**：

```
Agent 面对用户问题
    ├── "XX 是什么原理？" → search_docs（查文档）
    ├── "技术部多少人？" → query_database（查数据库）
    ├── "把结果存起来"   → save_to_file（存文件）
    └── "技术部工资最高的人是谁？把结果存到 output/top_salary.txt"
        → query_database → 拿到结果 → save_to_file → 回复用户
```

最后一个路径最有意思。Agent 需要连续调用两个不同的工具——先查数据库，根据结果判断需要存文件，再调文件保存。这不是"一次调用一个工具"，而是"根据前一个工具的结果，决定下一个工具要不要调、调哪个"——这才是 Agent Loop 的真正价值。

---

## 你现在知道了

这篇走下来，你手上多了一个能查文档、查数据库、存文件的完整 Agent。从搭 RAG 管道到用 LangChain 重构到装上三种工具——这中间的代码你全都写过，每一行都知道在干什么。`create_agent` 底层就是你手写的那个 while 循环，它帮你省了 90% 的代码，但你看穿它了。三种"手"——查文档、查数据库、存文件——分别对应非结构化、结构化、持久化三种数据层。

有几个东西我故意没展开：RAG 的高阶玩法（HyDE、Self-RAG、GraphRAG），LangChain 的其他几个模块（Models、Prompts、Indexes），生产环境的向量数据库选型（Milvus、Pinecone、Weaviate）。这些不是不重要，是不该在这个阶段分散你的注意力。你手上已经有了一个能跑通的完整系统——在这个骨架上再加东西，不会迷路。

阶段一让你理解了 Agent 怎么思考。阶段二让你能给它装上手脚——检索、记忆、多种工具。但你现在的 Agent 是个独行侠。它不能和别人协作，不能把复杂任务拆成几路并行执行，不能在遇到不确定时停下来问人类。

这些是阶段三要做的事。LangGraph 的图结构编排——把链式调用升级成条件路由和状态图。MCP 协议——让外部工具像 USB 一样即插即用（这个被称作 Agent 界的"HTTP"不是我先说的，但确实到位）。CrewAI 多 Agent 协作——几个 Agent 各司其职，互相派活。还有一个你可能没想到的问题：你大概率不需要一个 Agent 团队来查天气。什么时候该上多 Agent，什么时候纯属过度设计，阶段三也会讲。

---

*参考来源：*

- LangChain 官方文档（v1.3 迁移指南）：https://docs.langchain.com/oss/python/migrate/langgraph-v1
- LangChain Forum（流式相关问题讨论）：https://forum.langchain.com/t/2284
- ChromaDB 文档：https://docs.trychroma.com/
- BGE Embedding 模型（BAAI）：https://huggingface.co/BAAI/bge-small-zh-v1.5
- BGE Reranker 模型（BAAI）：https://huggingface.co/BAAI/bge-reranker-v2-m3
- Datawhale Hello-Agents（第 6-8 章）：https://github.com/datawhalechina/hello-agents
- ai-agents-from-zero（第 03-04 节）
- Reciprocal Rank Fusion（RRF）：Cormack et al., SIGIR 2009
- DeepSeek API 文档（Function Calling）：https://platform.deepseek.com/api-docs
