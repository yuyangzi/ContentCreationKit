# wechat-format Skill 代码审查与优化设计

**日期**: 2026-06-16
**范围**: `.opencode/skills/wechat-format/`
**类型**: 代码审查 → 修复计划
**审查**: Metis (Plan Consultant) + Momus (Plan Critic) 双审查通过

---

## 概述

对 `wechat-format` skill 进行全面代码审查，核心文件 `scripts/format.py`（1763 行）是单文件 Python 脚本，负责 Markdown → 微信兼容 HTML 的排版转换。

> **审查反馈已整合**: 本文档已根据 Metis 和 Momus 的双审查意见修订。关键修正包括：P0-2 方案 A 增加样式注入分离约束、P2-5 升级至 P1、新增 QA 验收标准与提交策略。

---

## 一、P0 级别问题（必须立即修复）

### P0-1: 微信主流程缺少 CJK 间距修复和加粗标点修复

**位置**: `scripts/format.py:1671-1681` vs `:1566-1568`

**问题描述**:

`format_for_output()` 函数在预处理阶段正确调用了 `fix_cjk_spacing()` 和 `fix_cjk_bold_punctuation()`，但该函数仅用于 `--format html` 和 `--format plain` 路径。主要的微信输出路径（`--gallery` 和单主题模式）在 `main()` 函数中自行实现了预处理流程，**遗漏了这两个关键修复**。

```python
# format_for_output() — 正确的预处理（第1566-1568行）
content = fix_cjk_spacing(content)
content = fix_cjk_bold_punctuation(content)

# main() — 遗漏的预处理（第1671-1681行）
content = strip_frontmatter(content)
content = process_callouts(content)
# ❌ 缺少 fix_cjk_spacing(content)
# ❌ 缺少 fix_cjk_bold_punctuation(content)
content = process_manual_footnotes(content)
```

**影响**:
- SKILL.md 第184-185行宣称的 "CJK 间距修复" 和 "加粗标点修复" 在微信输出中**完全失效**
- Gallery 模式和单主题模式均受影响

**修复方案**:

**方案 A（推荐）**: `main()` 统一调用 `format_for_output()`，并将 `format_for_output()` 重构为**仅预处理**（不注入样式），样式注入由 `main()` 统一处理。

**方案 B**: 在 `main()` 的手动预处理流程中补上缺少的两个调用。

**推荐方案 A**: 消除代码重复，单一数据流。详见 P0-2。

**验收标准**:

```bash
# 创建测试文章
cat > /tmp/cjk-test.md << 'EOF'
# 测试
这是一篇测试文章，包含English和中文混排。
**加粗文字，** 后面是标点。
EOF

# 运行微信排版
python3 scripts/format.py --input /tmp/cjk-test.md -o /tmp/cjk-test-out

# 验证 CJK 间距：应包含 "和" 与 "English" 之间的空格
grep -q '包含 English' /tmp/cjk-test-out/*/article.html && echo "CJK OK"

# 验证加粗标点修复：应输出 "**加粗文字**，" 而非 "**加粗文字，**"
grep -q '<strong[^>]*>加粗文字</strong>，' /tmp/cjk-test-out/*/article.html && echo "Bold OK"
```

---

### P0-2: 消除 `main()` 与 `format_for_output()` 的代码重复

**位置**: `scripts/format.py:1549-1614` 与 `:1670-1706`

**问题描述**:

两个函数各自实现了 ~90% 相同的 Markdown 预处理流程，维护两套逻辑直接导致 P0-1 中的遗漏。

**⚠️ 关键约束（审查发现）**: 

当前 `format_for_output(output_format="wechat")` 在预处理后还会调用 `inject_inline_styles()` 和 `convert_image_captions()`。如果 `main()` 直接使用其返回值，后续的样式注入代码（第1735-1741行 `inject_inline_styles`）会造成**双重注入**——`<pre>` 代码块会被嵌套包裹两次，Gallery 的 `_render_single_theme()` 也会重复注入。这是**所有修复方案的根本前置约束**。

**修复方案（修订版）**:

将 `format_for_output()` 重构为**仅负责预处理**（分离样式注入职责），`main()` 统一调用后再自行处理样式注入：

```python
# format_for_output() 改为仅预处理 + Markdown→HTML 转换
# 移除内部的 inject_inline_styles() 和 convert_image_captions() 调用
# 返回未样式化的 html, footnote_html
```

```python
# main() 重构后 — 所有格式统一入口
result = format_for_output(content, input_path, theme, output_dir, vault_root, args.format)
html = result["html"]
footnote_html = result["footnote_html"]

# 非微信格式：直接写入
if args.format != "wechat":
    out_path = output_dir / f"article.{args.format}.html"
    out_html = html + ("\n" + footnote_html if footnote_html else "")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(out_html, encoding="utf-8")
    print(f"\n输出: {out_path}")
    return

# 微信格式：main() 统一处理样式注入（仅一次）
if args.gallery:
    # gallery: _render_single_theme 内部调用 inject_inline_styles（仅一次）
    ...
else:
    # 单主题: 仅一次注入
    html = inject_inline_styles(html, theme)
    if footnote_html:
        footnote_html = inject_inline_styles(footnote_html, theme, skip_wrapper=True)
    html = convert_image_captions(html)
    if footnote_html:
        footnote_html = convert_image_captions(footnote_html)
```

**注意**: `~~删除线~~` 处理已在 `format_for_output()` 第1572行中存在，无需额外补回。

**验收标准**:

```bash
# 验证 wechat/html/plain 三种格式均正常输出
python3 scripts/format.py --input content/article/sample.md --format wechat
python3 scripts/format.py --input content/article/sample.md --format html
python3 scripts/format.py --input content/article/sample.md --format plain

# 验证代码块未被双重包裹（不应出现嵌套的 code_block section）
grep -c 'data-darkmode-bgcolor' content/wechat/*/article.html
# 同一代码块只应出现一套 darkmode 属性，不应重复
```

---

## 二、P1 级别问题（应尽快修复）

### P1-1: `convert_wikilinks` 文件句柄泄漏

**位置**: `scripts/format.py:293`

```python
_cfg = _json.load(open(config_path, encoding="utf-8"))
```

**修复**:

```python
with open(config_path, encoding="utf-8") as f:
    _cfg = _json.load(f)
```

**验收**: 代码审查确认 `with` 语句存在。

---

### P1-2: `convert_wikilinks` 使用 `os.walk(followlinks=True)` 有无限循环风险

**位置**: `scripts/format.py:308`

**修复**: 构建文件名→路径索引（惰性，首次使用时构建），使用 `pathlib.rglob()` 替代 `os.walk`，跳过符号链接：

```python
_image_index: dict[str, Path] = {}
def _build_image_index(search_roots: list[Path]) -> None:
    for root in search_roots:
        if root.exists():
            for p in root.rglob("*"):
                if p.is_file() and not p.is_symlink():
                    _image_index[p.name] = p
```

**验收**: 
```bash
# 验证图片索引正常工作（不触发 walk 循环）
python3 -c "
from pathlib import Path
from scripts.format import convert_wikilinks
# 函数签名检查通过即可
print('OK')
"
```

---

### P1-3: `convert_wikilinks` 中不必要的重新导入

**位置**: `scripts/format.py:291` — 删除 `import json as _json`，使用顶部已导入的 `json`。

---

### P1-4: `_basic_syntax_highlight` 正则高亮器产生实际 bug（审查升级）

**位置**: `scripts/format.py:795-872`

**原优先级**: P2 → **审查升级至 P1**

**理由**: 手写正则高亮器无法处理字符串内转义（`"hello \"world\""` 截断）、在注释中匹配关键字、多行字符串——这些在输出的代码块中产生**可见的语法高亮错误**，对排版工具的公信力造成直接损害。

**修复方案**: 

方案 A: 替换为 Pygments（可选依赖，有 fallback）
方案 B: 改进正则以处理字符串内转义和注释区域——至少修复最明显的错误

**验收**:
```bash
# 含转义的代码块应正确高亮
cat > /tmp/highlight-test.md << 'EOF'
```python
x = "hello \"world\""
# this is a comment with class def return
print(x)
```
EOF
python3 scripts/format.py --input /tmp/highlight-test.md -o /tmp/highlight-out
# 验证：字符串内转义的引号不应截断高亮
```

---

## 三、P2 级别问题（代码质量改进）

### P2-1: `generate_gallery` 中 `selected-theme.txt` 使用全局而非 per-article 路径

**位置**: `scripts/format.py:1541`

```python
(OUTPUT_DIR / "selected-theme.txt").write_text(...)
```

**修复**: 改为 `(output_dir / "selected-theme.txt")`。

**同时修复**: 第1730行的用户提示消息也打印了错误路径，需同步修正。

**验收**:
```bash
# 验证 selected-theme.txt 写入 per-article 目录
ls content/wechat/{文章名}/selected-theme.txt
```

---

### P2-2: Gallery GROUPS 硬编码与 GALLERY_THEMES 不同步

**位置**: `scripts/format.py:1491-1497` 与 `:46-57`

**修复方案**: 在主题 JSON 中添加 `category` 字段，画廊自动按分类分组。30 个主题均需添加（建议脚本批量处理）。

**验收**: 
```bash
# 所有20个画廊主题均有 category 字段
python3 -c "
import json
from pathlib import Path
themes = Path('.opencode/skills/wechat-format/themes')
missing = [t for t in themes.glob('*.json') if 'category' not in json.load(open(t))]
print(f'Missing category: {len(missing)}')
assert len(missing) == 0
"
```

---

### P2-3: `convert_image_captions` 图说匹配局限性

**位置**: `scripts/format.py:1440-1450`

**问题**: 仅匹配 `<p><em>xxx</em></p>` 格式；建议方案中的 `(.{1,80})` 对长图说不友好。

**修复方案**: 放宽限制至 `.{1,200}`，并额外匹配图片元素（`<img` 或 `<section data-role="img-wrapper"`）后的短 `<p>` 段落。

**验收**: 含 CDN 外链图片 + 纯文本图说的测试文章正常渲染。

---

### P2-4: `convert_wikilinks` 缺少文件类型验证（审查新增）

**位置**: `scripts/format.py:299-316`

**问题**: 无条件将 wikilink 文件复制为图片，即使是非图片文件（`.pdf`、`.docx`、`.txt`）也会被包裹在 `<img>` 标签中。

**修复**: 添加扩展名白名单 `['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']`。

**验收**:
```bash
# 非图片 wikilink 不应生成 <img> 
echo '![[sample.pdf]]' > /tmp/wikilink-test.md
python3 scripts/format.py --input /tmp/wikilink-test.md -o /tmp/wikilink-out
grep -c '<img' /tmp/wikilink-out/*/article.html  # 应为 0
```

---

## 四、P3 级别问题（低优先级 / 长期）

### P3-1: `_build_dialogue_html` 多说话人左右分配（原 P2-3，审查降级）

3个以上说话人是边缘场景。当前 `speakers_seen.index()` 会导致第3人与第1人同侧。修复使用 dict 缓存确保每个说话人侧边一致。此修复不对现有行为产生破坏。

### P3-2: `_inject_container_styles` 容器样式硬编码（原 P2-6，审查降级）

容器样式支持主题覆盖是长期目标，当前收益/成本比低。建议先抽取默认样式到独立的 `default_container_styles.json`，后续逐步让主题选择性覆盖。

---

## 五、架构优化建议

| 建议 | 描述 | 工作量 |
|------|------|--------|
| 拆分 format.py | 6 模块：`parser.py` / `styles.py` / `containers.py` / `templates.py` / `highlight.py` / `format.py`(入口) | 大 |
| 类型注解 | 为关键函数添加类型提示 | 中 |
| Jinja2 模板 | 替代 `{{}}`+`.replace()` 方案，提升条件渲染能力 | 中 |
| 单元测试 | `fix_cjk_spacing`、`fix_cjk_bold_punctuation`、`process_fenced_containers`、`inject_inline_styles` 等核心函数 | 大 |
| Pygments 高亮 | 替代手写正则高亮器（如 P1-4 未采用） | 中 |

---

## 六、修复执行计划

### 依赖关系图

```
Wave 1 (P0)
T1 ──────→ T2 ──────→ T3
(format_for_output 重构)

Wave 2 (P1) — 可与 Wave 1 并行
T4 ──┐
T5 ──┤  (wikilinks 修复，独立于 Wave 1)
T6 ──┘

Wave 2.5 (升级的 P1)
T7 ───   (语法高亮，独立)

Wave 3 (P2) — 所有任务彼此独立，可完全并行
T8 ──┐
T9 ──┤
T10─┐┤
T11─┘┘

Wave 4 (P3 / 长期)
T12 ───→ T13 ───→ T14 ───→ T15 ───→ T16
(模块拆分依赖 T1 完成)
```

### Wave 1 — P0 修复（阻塞，不可并行）

| 任务 | 描述 | 文件 | 预估 |
|------|------|------|------|
| T1 | 重构 `format_for_output()` 分离预处理与样式注入 | `format.py` | 中 |
| T2 | `main()` 统一调用 `format_for_output()`，移除重复代码 | `format.py` | 中 |
| T3 | 全格式回归验证（wechat/html/plain + gallery + 单主题） | `format.py` | 小 |

### Wave 2 — P1 修复（可与 Wave 1 并行）

| 任务 | 描述 | 文件 | 预估 |
|------|------|------|------|
| T4 | 修复文件句柄泄漏 (P1-1) | `format.py` | 小 |
| T5 | 移除重复 import (P1-3) | `format.py` | 小 |
| T6 | 构建图片索引替代 os.walk (P1-2) | `format.py` | 中 |
| T7 | 改进语法高亮器 (P1-4，审查升级) | `format.py` | 中 |

### Wave 3 — P2 改进（完全并行）

| 任务 | 描述 | 文件 | 预估 |
|------|------|------|------|
| T8 | 修复 `selected-theme.txt` 路径 + 用户提示 (P2-1) | `format.py` | 小 |
| T9 | 主题 JSON 添加 `category` 字段，自动分组 (P2-2) | `format.py` + 30主题 | 中 |
| T10 | 改进图说识别正则 + 放宽长度限制 (P2-3) | `format.py` | 小 |
| T11 | wikilinks 添加文件类型验证 (P2-4，审查新增) | `format.py` | 小 |

### Wave 4 — 长期架构优化

| 任务 | 描述 | 预估 |
|------|------|------|
| T12 | 拆分 format.py 为模块 | 大 |
| T13 | 添加类型注解 | 中 |
| T14 | 模板引擎改用 Jinja2 | 中 |
| T15 | 添加单元测试 | 大 |
| T16 | 语法高亮改用 Pygments (如 P1-4 未采用) | 中 |

---

## 七、提交策略

建议原子化提交，每次提交对应一个独立修复：

```
提交 1: fix: 重构 format_for_output 分离预处理与样式注入 (P0-2)
提交 2: fix: main() 统一调用 format_for_output 消除代码重复 (P0-1)
提交 3: fix: 修复 convert_wikilinks 文件句柄泄漏 + 重复 import (P1-1, P1-3)
提交 4: fix: 构建图片索引替代 os.walk(followlinks=True) (P1-2)
提交 5: fix: 改进语法高亮器处理字符串转义 (P1-4)
提交 6: fix: 修复 selected-theme.txt per-article 路径 (P2-1)
提交 7: feat: 主题 JSON 添加 category 字段实现自动分组 (P2-2)
提交 8: fix: 改进图说识别正则 + 放宽长度限制 (P2-3)
提交 9: fix: wikilinks 添加图片扩展名白名单 (P2-4)
```

---

## 八、风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 重构 `main()` 引入新 bug（**包括双重样式注入**） | **高** | `format_for_output()` 分离样式注入职责；代码块双重包裹检测；逐格式回归验证 |
| T6 图片索引构建影响启动性能 | 低 | 惰性构建，首次使用时才建立索引 |
| P2-2 批量为 30 个主题添加 `category` 引入人为错误 | 低 | 提供批量迁移脚本，自动分类 |
| P1-4 Pygments 依赖增加安装复杂度 | 低 | 作为可选依赖，检测导入失败时 fallback 到手写高亮 |
| 主题 JSON 格式变更影响现有主题 | 低 | `category` 为可选字段，有默认 fallback 值 |

---

## 九、审查记录

| 审查者 | 日期 | 主要发现 | 整合状态 |
|--------|------|----------|----------|
| Sisyphus (自审) | 2026-06-16 | 无占位符、无矛盾、无歧义 | ✅ 通过 |
| Metis (Plan Consultant) | 2026-06-16 | P0-2 双重注入风险、P2-5→P1、P2-3/P2-6→P3、wikilinks 文件类型验证缺失、P2-3 80字符限制 | ✅ 已整合 |
| Momus (Plan Critic) | 2026-06-16 | 所有引用验证准确、P0-2 样式注入分离约束、缺少 QA 验收标准、缺少提交策略 | ✅ 已整合 |

---

## 附录: 文件清单

```
.opencode/skills/wechat-format/
├── SKILL.md                 # 使用文档
├── config.json              # 配置文件
├── scripts/
│   └── format.py            # 主排版引擎（1763行）
├── templates/
│   ├── preview.html         # 手机预览模板（269行）
│   └── gallery.html         # 主题画廊模板（434行）
└── themes/                  # 30个主题 JSON 文件
    ├── terracotta.json
    ├── bytedance.json
    ├── ...
    └── wechat-native.json
```