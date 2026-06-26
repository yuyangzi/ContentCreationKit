---
name: wechat-format
description: Markdown → 微信兼容 HTML 排版引擎。当用户需要将文章排版为微信公众号格式、预览主题、复制到微信后台时使用。支持 30 套精美主题、画廊预览、AI 内容结构增强、深色模式、代码高亮、多类型排版容器。
---

## When to Use

- 用户需要将 Markdown 文章排版为微信公众号格式
- `/to-wechat` 命令调用本 skill 执行排版
- 需要预览多种主题风格并选择最佳方案

## 脚本目录

`{baseDir}` = 本 SKILL.md 所在目录。

| 脚本 | 用途 |
|------|------|
| `scripts/format.py` | 排版引擎：Markdown → 微信兼容 HTML |

## 配置

配置文件：`{baseDir}/config.json`

## 排版容器语法

支持以下容器语法，根据内容类型自动推荐套用：

```markdown
:::dialogue[采访实录]
Alice: 你好
Bob: 你好，很高兴认识你
:::

:::gallery[产品截图]
![](img1.jpg)
![](img2.jpg)
:::

:::timeline[发展历程]
2020: 项目启动
2022: 用户破百万
:::

:::steps[操作步骤]
打开设置页面
点击高级选项
:::

:::compare[方案 A vs 方案 B]
速度快 | 稳定性高
:::

:::quote[乔布斯]
Stay hungry, stay foolish.
:::

```

## 排版工作流

### 第 1 步：确认文章

1. 从 `content/article/` 读取指定文章 Markdown 文件
2. 确认标题和字数

### 第 2 步：结构化预处理

检测 Markdown 结构完整度。缺少 `##` 标题或格式标记较少时执行：

1. 识别逻辑段落插入 `##` 标题
2. 确保段落之间有空行分隔
3. 识别并列内容加列表标记
4. 识别关键词加 `**加粗**`
5. 清理格式（多余空行、缩进、标点）
6. **不改措辞**：不调语序、不增删内容

### 第 3 步：AI 内容分析 + 自动套格式

根据内容类型自动应用排版容器：

| 内容类型 | 容器语法 |
|---------|---------|
| 对话/访谈 | `:::dialogue[标题]` |
| 连续多图（3+） | `:::gallery[标题]` |
| 注意事项 | `> [!warning] 标题` |
| 分隔符 | 章节转换处用 `---` |
| 图说 | 图片后斜体 `*图片说明*` |

### 第 4 步：推荐主题

| 内容类型 | 推荐主题 |
|----------|----------|
| 深度长文/分析 | newspaper, magazine, ink |
| 科技/AI | bytedance, github, sspai |
| 访谈/对话体 | terracotta, coffee-house, mint-fresh |
| 教程/操作指南 | github, sspai, bytedance |
| 文艺/观点 | terracotta, sunset-amber, lavender-dream |

### 第 5 步：打开主题画廊

```bash
python3 {baseDir}/scripts/format.py \
  --input "文章路径.md" \
  --gallery \
  --recommend newspaper magazine ink
```

浏览器中切换主题预览，选择最佳方案(优化使用Edge/Chrome浏览器)。

### 第 6 步（备选）：直接指定主题

```bash
python3 {baseDir}/scripts/format.py \
  --input "文章路径.md" \
  --theme terracotta
```

### 第 7 步：确认并复制

- Gallery 模式：选中主题后点「确认」按钮，记下主题名
- 直接模式：浏览器预览确认后点「复制到微信」
- 将排版好的 HTML 粘贴到公众号后台

### 输出说明

排版输出目录（`--output` 参数）：`content/wechat/{文章名}/`，包含：
- `article.html`：纯微信兼容 HTML（内联样式，可直接复制）
- `preview.html`：手机预览页面（含复制按钮）

同时将原始 Markdown 复制一份到 `content/wechat/{时间戳}-{主题名}.md`。

### 参数说明

**format.py**：
- `--input` / `-i`：Markdown 文件路径（必须）
- `--gallery`：打开主题画廊（推荐）
- `--theme` / `-t`：直接指定主题名
- `--output` / `-o`：输出目录（默认 `content/wechat`）
- `--recommend`：推荐主题 ID 列表
- `--no-open`：不自动打开浏览器
- `--format`：输出格式 wechat/html/plain

## 可用主题（30 个）

### 独立风格（9 个）

| 主题 | ID | 风格 |
|------|-----|------|
| 赤陶 | `terracotta` | 暖橙色，满底圆角标题 |
| 字节蓝 | `bytedance` | 蓝青渐变，科技现代 |
| 中国风 | `chinese` | 朱砂红，古典雅致 |
| 报纸 | `newspaper` | 纽约时报风，严肃深度 |
| GitHub | `github` | 开发者风，浅色代码块 |
| 少数派 | `sspai` | 中文科技媒体红 |
| 包豪斯 | `bauhaus` | 红蓝黄三原色，先锋几何 |
| 墨韵 | `ink` | 纯黑水墨，极简留白 |
| 暗夜 | `midnight` | 深色底+霓虹色 |

### 精选风格（7 个）

| 主题 | ID | 风格 |
|------|-----|------|
| 运动 | `sports` | 渐变色带，活力动感 |
| 薄荷 | `mint-fresh` | 薄荷绿，清爽 |
| 日落 | `sunset-amber` | 琥珀暖调 |
| 薰衣草 | `lavender-dream` | 紫色梦幻 |
| 咖啡 | `coffee-house` | 棕色暖调 |
| 微信原生 | `wechat-native` | 微信绿 |
| 杂志 | `magazine` | 超大留白，品质长文 |

### 模板系列（14 个）

4 种布局（Minimal / Focus / Elegant / Bold）× 多色配色（Gold / Blue / Red / Green / Navy / Gray）

## 内置排版增强

- **CJK 间距修复**：中英文/数字之间自动加空格
- **加粗标点修复**：`**文字，**` → `**文字**，`
- **纯内联样式**：所有 CSS 写在 `style="..."` 上
- **列表模拟**：`<ul>/<ol>` → `<section>` + flexbox
- **外链转脚注**：正文标注 + 文末脚注
- **语法高亮**：代码块着色 + Mac 风格工具栏
- **深色模式**：自动生成 data-darkmode-* 属性
- **多类型 callout**：tip/note/important/warning/caution
- **图说识别**：图片后斜体变居中灰色图说
- **对话气泡**：`:::dialogue` 左右交替聊天气泡
- **图片画廊**：`:::gallery` 横向滚动多图容器
- **时间线**：`:::timeline` 时间线展示
- **步骤流程**：`:::steps` 编号步骤
- **对比卡片**：`:::compare[A vs B]` 两列对比
- **人物引言**：`:::quote[人名]` 引言卡片
- **表格斑马纹**：自动奇偶行背景色
