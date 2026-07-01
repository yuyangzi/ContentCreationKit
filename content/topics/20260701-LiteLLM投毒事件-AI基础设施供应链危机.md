# LiteLLM投毒事件：AI基础设施的"软件恐怖袭击"

> 热度：⭐⭐⭐⭐⭐

## 主题背景

2026年3月，月下载量近5亿的知名AI网关工具 LiteLLM 遭遇供应链攻击。攻击者在 v1.82.7 和 v1.82.8 版本中注入恶意代码，导致通过 pip install 安装的用户系统被植入后门，用于窃取API密钥和模型推理数据。

前 OpenAI 研究总监 Andrej Karpathy 公开将其称为 "software terror incident"（软件恐怖事件），引发AI社区对基础设施安全的大规模讨论。

这不是一个 isolated 事件——它反映了一个更深层的问题：当AI应用依赖的底层工具链（Python 包管理器、GitHub 仓库、npm 生态）被攻击时，整个AI产业的安全性建立在沙子之上。

## 类型标签

- 安全事件 / 供应链攻击
- AI基础设施
- 开源治理
- 技术深度

## 创作方向建议

### 角度一：事件还原 + 影响分析
从 LiteLLM 事件本身切入，讲清楚：谁在用这个工具？攻击者做了什么？影响范围多大？Karpathy 为什么用"恐怖事件"这个词？

### 角度二：AI供应链安全全景
以 LiteLLM 为引子，展开讨论整个AI开发栈的供应链攻击面——从 PyPI/npm 包、Docker 镜像、到 Hugging Face 模型仓库，每一层都有被投毒的风险。

### 角度三：信任危机
为什么开源软件的安全问题在AI时代变得更加危险？当我们把API密钥、用户数据、模型推理结果都交给一个 pip install 的包时，传统的开源信任模型还够用吗？

## 与已有内容的差异

「AI之毒-信任崩塌」聚焦数据/知识层面的投毒（训练数据被污染），本文聚焦**AI基础设施供应链**——代码层面的攻击，是2026年全新的攻击范式。两者互补但不重叠。

## 来源

- [LiteLLM poisoning incident - 腾讯朱雀实验室](https://matrix.tencent.com/en/2026/03/31/the-litellm-poisoning-incident-with-480-million-downloads-a-look-at-ai-infrastructure-security-attack-and-defense)
- [Data Poisoning 2026 - Lakera](https://www.lakera.ai/blog/training-data-poisoning)
- Andrej Karpathy 公开评论
