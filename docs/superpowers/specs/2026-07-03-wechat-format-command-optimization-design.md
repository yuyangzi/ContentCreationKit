# WeChat Format Command & Skill 使用层面优化设计

**日期**: 2026-07-03
**范围**: `.opencode/commands/to-wechat.md` + `.opencode/skills/wechat-format/`
**类型**: 使用层面优化（非代码 bug 修复）
**前置设计**: `2026-06-16-wechat-format-code-review-design.md`（已修复 P0-P2 代码 bug，本设计关注**使用层面**的问题）

---

## 一、背景

2026-06-16 已对 `wechat-format` skill 完成一轮代码审查，修复了 P0-P2 级别的代码 bug（CJK 间距缺失、代码重复、文件句柄泄漏、os.walk 循环风险等）。当前 `format.py`（1790 行）代码质量已基本过关。

但通过分析 **4 次 `/to-wechat` 实际使用 session 日志**（06-30 至 07-03），发现一批**使用层面**的问题未得到关注：

| 数据点 | 值 |
|--------|-----|
| 分析 session 数 | 4 次历史 `/to-wechat` 调用 |
| 最终使用主题 | 100% newspaper |
| 使用画廊模式 | 1/4（25%），最终仍回归 newspaper |
| 执行段落拆分 | 1/4（25%） |
| 使用容器语法 | 0/4（0%） |
| 主题选择被用户纠正 | 1 次（bytedance → newspaper） |
| 实际启用主题（30 个中） | 2 个（newspaper, bytedance） |

核心矛盾：SKILL.md 描述了一套**完整工作流**（结构化预处理 → AI 分析 → 画廊选主题 → 容器套用），但 command 和实际使用走的是一条**快速通道**（→ 直接 newspaper 输出 → 完成）。

---

## 二、当前状态

### 2.1 已完成的代码修复（06-16 设计已落地）

| 项 | 状态 | 文件位置 |
|----|------|----------|
| P0-1 CJK 间距 + 加粗标点 | ✅ 统一到 `format_for_output()` | `format.py:1607-1608` |
| P0-2 消除预处理代码重复 | ✅ main() 统一调用 | `format.py:1590-1647` |
| P1-1 wikilinks 文件句柄泄漏 | ✅ `with` 语句 | `format.py:313-321` |
| P1-2 os.walk 循环风险 → 惰性索引 | ✅ rglob + is_symlink 过滤 | `format.py:286-304` |
| P1-3 重复 import json | ✅ 已合并 | 顶部单 `import json` |
| P2-1 selected-theme.txt per-article 路径 | ✅ `output_dir / selected-theme.txt` | `format.py:1579` |
| P2-3 图说识别正则 | ✅ 200 字符 + CDN 支持 | `format.py:1468-1489` |
| P2-4 wikilinks 文件类型白名单 | ✅ 扩展名过滤 | `format.py:327-338` |

### 2.2 未实施的遗留代码项

| 项 | 优先级 | 原因 |
|----|--------|------|
| P1-4 手写语法高亮器改进 | P1（原） | 需引入 Pygments 可选依赖，归入后续 |
| P2-2 主题 JSON 添加 `category` 字段 | P2 | 影响 30 个文件，需批量迁移脚本 |
| P3-1 多说话人对话侧边分配 | P3 | 边缘场景 |
| P3-2 容器样式支持主题覆盖 | P3 | 成本/收益比低 |
| Wave 4 模块拆分（format.py → 6 模块） | 长期 | 架构演进 |

### 2.3 核心文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `.opencode/commands/to-wechat.md` | 46 行 | 命令定义（本设计主要修改目标之一） |
| `.opencode/skills/wechat-format/SKILL.md` | 192 行 | 技能文档（本设计主要修改目标之一） |
| `.opencode/skills/wechat-format/config.json` | 11 行 | 配置（本设计需修改） |
| `.opencode/skills/wechat-format/scripts/format.py` | 1790 行 | 排版引擎（本设计仅轻量修改） |
| `.opencode/skills/wechat-format/themes/*.json` | 30 个 | 主题（本设计不改） |
| `.opencode/skills/wechat-format/templates/preview.html` | 269 行 | 预览模板（本设计不改） |

---

## 三、问题与优化方案

### 🔴 P0：配置不统一（必须修）

#### P0-1: `default_theme` 三方值冲突

**现象**：
- `config.json` 写 `"default_theme": "terracotta"`
- `to-wechat.md` 写"默认使用 `newspaper` 主题"
- 实际使用 4/4 最终都用 `newspaper`

**影响**：如果 agent 直接调 `format.py --input article.md` 不带 `--theme`，输出 terracotta 而不是实际约定的 newspaper。

**方案**：将 `config.json` 的 `default_theme` 改为 `newspaper`，与 command 约定一致。

**涉及文件**: `config.json`（1 行修改）

#### P0-2: 目录大小写不统一（跨平台隐患）

**现象**：

| 文件 | 写法 |
|------|------|
| `AGENTS.md` | `content/WeChat/`（大写 W、C） |
| `README.md` | `content/WeChat/` |
| `to-wechat.md` | `content/wechat/`（全小写） |
| `config.json` | `content/wechat/` |
| `SKILL.md` | `content/wechat/` |

**影响**：macOS 大小写不敏感不报错，但 Linux/Docker/CI 环境会找不到路径或创建重复目录。实际 session 输出也混用了两种写法。

**方案**：全局统一为 `content/WeChat/`（与 AGENTS.md + README.md 一致）。涉及 3 个文件：
- `config.json` 的 `"output_dir"`
- `SKILL.md` 中所有路径引用
- `to-wechat.md` 中所有路径引用

**涉及文件**: `config.json` + `SKILL.md` + `to-wechat.md`（总计约 6 处修改）

#### P0-3: "HTML 已复制到剪贴板" 承诺不实

**现象**：`to-wechat.md` 第 28-29 行写"告知用户排版完成，HTML 已复制到剪贴板，可粘贴到公众号后台发布"。实际上 `format.py` 只是生成 `preview.html`+`article.html`，让用户自己在浏览器中点"复制到微信"按钮。

**影响**：用户期望被误导，以为 HTML 已自动就绪。

**方案**：修改 `to-wechat.md` 第 28-29 行描述为准确表述，例如"告知用户排版完成，打开 `preview.html` 点击『复制到微信』按钮，即可粘贴到公众号后台发布"。

### 🟡 P1：实际使用模式对齐

#### P1-1: 结构化预处理执行不落地

**现象**：
- `to-wechat.md` 第 3 步要求"段落不宜过长，每段控制在手机屏幕 3-5 行；适当增加小标题分割长内容"
- `SKILL.md` 第 2 步要求识别逻辑段落、加 `##` 标题、加列表标记
- 实际 4/4 session 中仅 1 次执行了段落拆分（agent 自主行为）
- 剩余 3 次直接调用 format.py，跳过了整个预处理

**根因**：command 和 SKILL.md 只在"步骤描述"中提出了预处理要求，但没有任何**硬性 check 机制**。agent 没有"在调用 format.py 之前必须先做段落拆分"的明确约束。

**方案 A（推荐）**：在 `to-wechat.md` 的步骤 2 和步骤 3 之间加入**条件判定节点**：

```
2. 运行前预处理判定：
   - 读取文章全文，检查段落长度
   - 如果存在任何段落 > 200 字（约手机 6+ 行），则：
     a. 将长段落拆分为 3-5 行/段的短段落
     b. 在内容转折处添加 `---` 分隔线或 `##` 小标题
   - 注意：不改措辞，只改段落边界
3. 调用 format.py 排版...
```

**方案 B**：在 `format.py` 中加入自动长段落拆分功能（`auto_split_long_paragraphs()`），AI 分析段落语义断点，无需人工步骤。

**选择**：方案 A（零代码改动，仅改文档），方案 B 作为未来增强。

#### P1-2: 容器语法（dialogue/gallery/timeline/steps/compare/quote）实际使用率为 0

**现象**：
- `SKILL.md` 大幅宣传 6 种容器语法
- 4 次 session 中零使用
- command 使用 `deepseek-v4-flash-free` 模型，能力不足以主动识别内容类型并套用容器

**方案 A（推荐）**：在 `SKILL.md` 顶部显式标注这些容器语法为**手动标记功能**，而非自动处理。增加说明："以上语法需要在 Markdown 源文件中手动编写，排版引擎会自动渲染。写作阶段即可使用。"

**方案 B**：升级 command 到更强的模型（如 `deep` 类别），由模型判断文章内容中是否有对话/时间线等结构并自动套用容器。

**选择**：方案 A（诚实标注），方案 B 留作未来 option。

**涉及文件**: `SKILL.md`（容器语法区加标注）

#### P1-3: 画廊模式实际使用率低（1/4）

**现象**：
- `SKILL.md` 大力推荐 gallery 流程（步骤 5）
- 实际仅 1/4 session 使用，最终仍回归 newspaper
- 30 个主题中实际启用 2 个

**方案**：明确 gallery 为可选流程，非默认。在 `to-wechat.md` 步骤中调整顺序：

```
步骤（默认快速模式）：
1. 确认文章
2. 结构化预处理（段落拆分 + 加小标题）
3. 直接使用 newspaper 主题运行 format.py
4. 输出文章 HTML + 预览
5. 告知用户完成

可选步骤（当用户明确要求换主题时）：
- 使用 --gallery 参数打开画廊预览
- 按内容类型参考主题推荐表
```

**涉及文件**: `to-wechat.md`（步骤重构）、`SKILL.md`（流程描述对齐）

#### P1-4: 主题推荐表对实际选型帮助有限

**现象**：`SKILL.md` 有一张主题推荐表（深度长文→newspaper/magazine/ink 等），但 07-03 session 中 agent 按推荐表选了 bytedance（科技/AI 类），被用户纠正为 newspaper。

**根因**：推荐表过于笼统，而作者的公众号实际有稳定的视觉风格偏好（ne wspaper 风格是最优解）。推荐表给出的多选反而造成错误决策。

**方案**：在 `to-wechat.md` 中明确："本公众号深度分析类文章统一使用 `newspaper` 主题。" 主题推荐表保留在 `SKILL.md` 中供其他用户参考，但在 command 层面不做多选推荐。

**涉及文件**: `to-wechat.md`（加入主题选择偏好说明）

### 🟢 P2：文档与命名一致性

#### P2-1: "主题名" vs "文章名" 用词不一致

**现象**：
- `SKILL.md` 第 130 行：`content/wechat/{时间戳}-{主题名}.md` 中的 "主题名"
- 实际输出：`content/wechat/{时间戳}-{文章名}/` 目录
- 实际值：`20260703-阿里腾讯字节AI总攻路线图`——显然是文章名，不是主题名

**方案**：统一改为"文章名"。

**涉及文件**: `SKILL.md`（1 处）、`to-wechat.md`（输出描述 2 处）

#### P2-2: frontmatter 处理未文档化

**现象**：`format.py` 的 `format_for_output()` 内部调用 `strip_frontmatter()`，文章头部的 YAML frontmatter 会被自动剥离。但 `SKILL.md` 和 `to-wechat.md` 均未提及此事。

**方案**：在 `to-wechat.md` 输出描述中补充一行："注意：文章的 YAML frontmatter（title/date 等元数据）在排版时会被自动剥离，不会出现在最终 HTML 中。"

#### P2-3: 图片处理说明缺失

**现象**：
- `format.py` 支持 wikilinks `![[image.jpg]]` 和标准 Markdown `![alt](path)` 图片
- `config.json` 配置了 `image_search_paths: ["content/article/images"]`
- `to-wechat.md` 无任何关于图片处理的描述
- 4 篇已排版的文章均为纯文字深度分析，未触发图片流程

**方案**：在 `to-wechat.md` 中补充图片处理说明：
- 文章中的本地图片会自动复制到输出目录的 `images/` 子目录
- 支持标准 Markdown 图片语法和 Obsidian wikilink 语法
- 推荐将图片放在 `content/article/images/` 目录下

### 🔵 P3：架构遗留项（标记，不在此次实施）

| 项 | 说明 | 受影响的文件 |
|----|------|-------------|
| P1-4 语法高亮改进 | 手写正则高亮 -> Pygments 可选依赖 | `format.py:868-904` |
| P2-2 主题 JSON category | 30 个主题单文件添加 `category` 字段 | 30 × `themes/*.json` + `format.py` |
| Wave 4 模块拆分 | 单文件 1790 行 → 6 模块 | `format.py` → 多个模块 |

---

## 四、实施计划

### 依赖关系

```
Wave 1 (P0, 独立)
T1 ── config.json default_theme 修改
T2 ── 全局目录大小写统一 (config.json + SKILL.md + to-wechat.md)
T3 ── "复制到剪贴板" 描述修正 (to-wechat.md)

Wave 2 (P1, 独立)
T4 ── 结构化预处理条件判定节点 (to-wechat.md)
T5 ── 容器语法重新标注 (SKILL.md)
T6 ── 流程重构 + 主题选择说明 (to-wechat.md + SKILL.md)

Wave 3 (P2, 独立)
T7 ── 用词一致性修正 (SKILL.md + to-wechat.md)
T8 ── frontmatter 处理说明 + 图片处理说明 (to-wechat.md)
```

所有 Wave 内的任务彼此独立，可并行。Wave 间无依赖。

### 任务分解

#### Wave 1 — P0 配置统一（3 个独立任务）

| 编号 | 描述 | 文件 | 预期工作量 |
|------|------|------|-----------|
| T1 | config.json: `default_theme` → `"newspaper"` | `config.json` | 1 行 |
| T2 | 全局统一 `content/WeChat/` 大写形式 | `config.json` + `SKILL.md` + `to-wechat.md` | ~6 处替换 |
| T3 | 修正"HTML 已复制到剪贴板"描述 | `to-wechat.md:28-29` | 1 处替换 |

**T1 操作细节**:
```
# config.json
"default_theme": "newspaper"
```

**T2 操作细节**:
```
config.json:
  "output_dir": "content/WeChat"

SKILL.md:
  第 130 行: content/WeChat/{时间戳}-{文章名}.md
  第 127 行: content/WeChat/{文章名}/

to-wechat.md:
  第 33-35 行: 所有 content/wechat/ → content/WeChat/
```

**T3 操作细节**:
```
# to-wechat.md 第 5 步
当前: "告知用户排版完成，HTML 已复制到剪贴板，可粘贴到公众号后台发布。"
修改: "告知用户排版完成，打开预览页面（preview.html）点击「复制到微信」按钮，即可粘贴到公众号后台发布。"
```

#### Wave 2 — P1 使用模式对齐（3 个独立任务）

| 编号 | 描述 | 文件 | 预期工作量 |
|------|------|------|-----------|
| T4 | 在步骤 2-3 间插入预处理条件判定节点 | `to-wechat.md` | 新增 ~8 行 |
| T5 | 容器语法重新标注为手动功能 | `SKILL.md` | 1 处标注说明 |
| T6 | 重构 quick 流程 vs gallery 可选流程 | `to-wechat.md` + `SKILL.md` | 重写步骤和流程描述 |

**T4 操作细节**（插入到 `to-wechat.md` 步骤 2 之后）:

```markdown
3. 预处理判定（重要）：读取文章全文，检查段落长度。
   - 如果存在任何段落 > 200 字，则做以下预处理：
     a. 将长段落拆分为手机 3-5 行的短段落
     b. 在内容转折处添加 `---` 分隔线或 `##` 小标题
   - 不改措辞，只改段落边界和段落结构
```

后续步骤号顺延。

**T5 操作细节**: 在 `SKILL.md` "排版容器语法"章节顶部加标注：

```markdown
> ⚠️ **注意**：这些容器语法需要在 Markdown 源文件中手动编写（写作阶段即可使用），
> 排版引擎会自动识别并渲染为对应的微信兼容 HTML。当前不会自动判断内容类型来套用。
```

**T6 操作细节**:
- `to-wechat.md` 步骤重构为"快速模式"（默认）+ "可选模式"（换主题时）
- `SKILL.md` 流程表格中提到 gallery 前面加 "（可选）"

#### Wave 3 — P2 文档完善（2 个独立任务）

| 编号 | 描述 | 文件 | 预期工作量 |
|------|------|------|-----------|
| T7 | "主题名" → "文章名" 统一 | `SKILL.md` + `to-wechat.md` | 3 处替换 |
| T8 | 补充 frontmatter + 图片处理说明 | `to-wechat.md` | 新增 2 条说明 |

---

## 五、验收标准

### Wave 1 验收

```bash
# T1: default_theme 检查
python3 -c "
import json
cfg = json.load(open('.opencode/skills/wechat-format/config.json'))
assert cfg['settings']['default_theme'] == 'newspaper', f'Expected newspaper, got {cfg[\"settings\"][\"default_theme\"]}'
print('T1 default_theme: PASS')
"

# T2: 目录大小写统一
python3 -c "
import os
files = ['.opencode/skills/wechat-format/config.json',
         '.opencode/skills/wechat-format/SKILL.md',
         '.opencode/commands/to-wechat.md']
for f in files:
    content = open(f).read()
    # 不应出现小写 content/wechat/（在 Markdown 路径/配置键中）
    # 允许注释或说明中出现
    lines = [l for l in content.split('\n') if 'content/wechat/' in l.lower()]
    issues = [l for l in lines if 'content/wechat/' in l]
    if issues:
        print(f'  Issues in {f}: {len(issues)} lines with lowercase')
        for l in issues:
            print(f'    - {l.strip()[:80]}')
    else:
        print(f'T2 {f}: PASS')
"

# T3: to-wechat.md 不出现"已复制到剪贴板"
python3 -c "
content = open('.opencode/commands/to-wechat.md').read()
assert '已复制到剪贴板' not in content, 'T3 FAIL: found outdated copy description'
print('T3 copy description: PASS')
"
```

### Wave 2 验收

```markdown
# 人工审查：
# T4: to-wechat.md 步骤 2 后是否有预处理判定节点
# T5: SKILL.md 容器语法区是否有"手动编写"标注
# T6: to-wechat.md 和 SKILL.md 流程描述是否对齐为"快速模式优先"
```

### Wave 3 验收

```bash
# T7: "主题名" 不应在输出路径描述中出现
python3 -c "
import os
files = ['.opencode/skills/wechat-format/SKILL.md',
         '.opencode/commands/to-wechat.md']
for f in files:
    content = open(f).read()
    # 只在路径上下文中检查，非示例代码
    issues = []
    lines = content.split('\n')
    for i, l in enumerate(lines):
        if 'content/' in l and '主题名' in l:
            issues.append((i+1, l.strip()))
    if issues:
        for ln, l in issues:
            print(f'  {f}:{ln} - {l}')
    else:
        print(f'T7 {f}: PASS')
"

# T8: frontmatter + 图片说明存在
python3 -c "
content = open('.opencode/commands/to-wechat.md').read()
checks = ['frontmatter', 'YAML', '图片']
missing = [c for c in checks if c not in content]
if missing:
    print(f'T8: Missing references: {missing}')
else:
    print('T8: PASS')
"
```

---

## 六、提交策略

```
提交 1: fix: config.json default_theme 统一为 newspaper (P0-1)
        修改 config.json 1 行

提交 2: fix: 全局统一目录大小写为 content/WeChat/ (P0-2)
        修改 config.json + SKILL.md + to-wechat.md

提交 3: docs: 修正"HTML 已复制到剪贴板"不实描述 (P0-3)
        修改 to-wechat.md 1 处

提交 4: docs: 增加结构化预处理条件判定节点 (P1-1)
        修改 to-wechat.md 步骤 2-3 间插入

提交 5: docs: 容器语法重新标注为手动编写功能 (P1-2)
        修改 SKILL.md 容器语法区

提交 6: docs: 重构快速模式 vs gallery 可选流程 (P1-3 + P1-4)
        修改 to-wechat.md + SKILL.md 流程描述

提交 7: docs: 统一"主题名"→"文章名" + 补充 frontmatter/图片说明 (P2)
        修改 SKILL.md + to-wechat.md
```

实际可合并为较少的提交（如 P0 的 3 个任务合并为一个提交）。

---

## 七、风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 目录大小写改动后，macOS 上测试不充分，Linux 上才暴露 | 中 | 可以在 CI 或 Docker 中验证 create/write 行为 |
| 结构化预处理条件判定节点增加 agent 决策负担 | 低 | 条件非常明确（>200 字），agent 容易判断 |
| 快速模式优先导致 gallery 和容器被完全遗忘 | 低 | 这是**尊重实际使用模式**，不是功能删除 |
| 已有输出目录 `content/wechat/` 与 `content/WeChat/` 共存 | 低 | macOS 大小写不敏感，git 重命名后自动统一 |

---

## 八、审查记录

| 审查者 | 日期 | 主要发现 | 整合状态 |
|--------|------|----------|----------|
| Sisyphus (自审) | 2026-07-03 | — | ✅ 待审查 |

---

## 附录: 修改文件清单

```
.opencode/
├── commands/
│   └── to-wechat.md              # 修改: 步骤重构 + 路径修正 + 描述修正
└── skills/
    └── wechat-format/
        ├── SKILL.md               # 修改: 路径修正 + 流程描述对齐 + 容器标注
        ├── config.json            # 修改: default_theme + output_dir
        └── scripts/
            └── format.py          # ❌ 不改（仅文档优化）
```
