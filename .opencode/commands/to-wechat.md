---
description: 文章转公众号排版
---

# 转公众号排版

## 目标

将正式文章排版为微信公众号发布格式，利用 `wechat-format` skill 进行专业排版，适配移动端阅读体验和平台调性。

## 前置条件

已完成 `/to-article`，`content/article/` 目录已有正式文章

## 输入

- `content/article/` 目录下的文章文件（Markdown）

## 步骤

1. 加载 `wechat-format` skill，按其排版工作流对文章进行处理。
2. 使用 `scripts/format.py` 进行排版：没有额外要求，默认使用 github 主题。
3. 对文章进行公众号适配补充：
   - 段落不宜过长，每段控制在手机屏幕 3-5 行
   - 适当增加小标题分割长内容
   - 添加引导关注话术（如文末引导语）
4. 以 `{时间戳}-{主题名}.md` 的文件名保存到 `content/wechat/` 目录。
5. 告知用户排版完成，HTML 已复制到剪贴板，可粘贴到公众号后台发布。

## 输出

- `content/wechat/{时间戳}-{主题名}.md`：公众号排版后的文章文件
- `content/wechat/{时间戳}-{文章名}/article.html`：微信兼容的 HTML 文件（可直接复制到公众号后台）
- `content/wechat/{时间戳}-{文章名}/preview.html`：手机预览页面

## 约束

**必须遵守：**

- 使用 `wechat-format` skill 的 `format.py` 进行核心排版，不手动内联样式
- 排版以手机阅读体验为优先
- 引导关注话术简洁自然

**禁止操作：**

- 不要删减文章核心内容
- 不要使用过于花哨的排版样式
