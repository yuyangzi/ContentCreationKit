---
description: 文章转公众号排版
model: opencode/deepseek-v4-flash-free
---

# 转公众号排版

## 目标

将正式文章排版为微信公众号发布格式，利用 `wechat-format` skill 进行专业排版，适配移动端阅读体验和平台调性。

## 前置条件

已完成 `/to-article`，`content/article/` 目录已有正式文章

## 输入

- `content/article/` 目录下的文章文件（Markdown）

## 步骤

### 默认快速模式

1. 加载 `wechat-format` skill，从 `content/article/` 读取待排版文章。
2. **结构化预处理判定**（重要）：读取文章全文，检查段落长度。
   - 如果存在任何段落 > 200 字（约手机 6+ 行），则做以下预处理：
     a. 将长段落拆分为手机 3-5 行的短段落
     b. 在内容转折处添加 `---` 分隔线或 `##` 小标题
   - 不改措辞，只改段落边界和段落结构
3. 使用 `scripts/format.py` 以 `newspaper` 主题排版。本公众号深度分析类文章统一使用 `newspaper` 主题。
4. 以 `{时间戳}-{主题名}.md` 的文件名保存到 `content/WeChat/` 目录。
5. 告知用户排版完成，打开预览页面（preview.html）点击「复制到微信」按钮，即可粘贴到公众号后台发布。

### 可选模式（当用户明确要求换主题时）

- 使用 `--gallery` 参数打开主题画廊预览，在浏览器中切换主题对比
- 按内容类型参考 `wechat-format` skill 中的主题推荐表
- 选中主题后点「确认」按钮，再按上述步骤 4-5 保存输出

## 输出

- `content/WeChat/{时间戳}-{主题名}.md`：公众号排版后的文章文件
- `content/WeChat/{时间戳}-{文章名}/article.html`：微信兼容的 HTML 文件（可直接复制到公众号后台）
- `content/WeChat/{时间戳}-{文章名}/preview.html`：手机预览页面

## 约束

**必须遵守：**

- 使用 `wechat-format` skill 的 `format.py` 进行核心排版，不手动内联样式
- 排版以手机阅读体验为优先

**禁止操作：**

- 不要删减文章核心内容
- 不要使用过于花哨的排版样式
