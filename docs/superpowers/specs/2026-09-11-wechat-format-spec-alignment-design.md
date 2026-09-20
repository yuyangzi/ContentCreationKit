# WeChat Format Skill 官方规范对齐设计

**日期**: 2026-09-11
**范围**: `.opencode/skills/wechat-format/` + `.opencode/commands/to-wechat.md`
**类型**: 渲染行为重构（引擎 + 30 主题 + 模板 + 文档）
**前置设计**:
- `2026-06-16-wechat-format-code-review-design.md`（P0-P2 代码 bug 修复）
- `2026-07-03-wechat-format-command-optimization-design.md`（使用层面优化）

---

## 一、背景与目标

`wechat-format` 是公众号管线 `/to-wechat` 的排版引擎。本次要解决两件事：

1. **去除外链产生的上标引用**：当前 `extract_links_as_footnotes()` 把**所有** `<a href>`（含 `mp.weixin.qq.com` 内链）转成正文 `文字<sup>[N]</sup>` + 文末「参考链接」节，导致正文出现大量上标。
2. **全面对齐官方《微信公众平台编辑器插件开发规范》**：该规范（`plugin_spec`，2026 版，原文见附录 A）对 Dark Mode、`<pre>`、宽度自适应、嵌套层级、字体等提出了明确要求，当前实现对多处不合规。

**用户决策（已确认）**:
- 外链 → 只保留链接文字，**URL 丢弃**；`mp.weixin.qq.com` 内链保留为可点击 `<a>`。
- 深色模式 → **彻底移除**手写 `data-darkmode-*`，完全交给平台自动转换算法。
- 适配范围 → **全面对齐**官方规范。

### 量化事实（均已核实）

| 事实 | 数值 | 方法 |
|------|------|------|
| 文章总数 / http(s) 链接数 | 98 篇 / 954 处 | `ls content/article/*.md`；`grep -roh 'https\?://[^ )]*'` |
| 手写 `[^N]` 脚注文章数 | 1 篇 | `grep -rl '\[\^[0-9]'` |
| 文字背景渐变 style 键 | **97** 处（background 78 + background_image 10 + border_image 9） | 主题 JSON 解析（附录 B） |
| 含 `border_image` 渐变的主题 | 3 个（`magazine` / `midnight` / `sports`，各 3 处） | 同上 |
| `dark_mode` 块 | 30/30 主题 | 同上 |
| 样例文章 `mp.weixin` 内链 / 手写脚注 | 0 / 0 | `content/article/20260910-Transformer架构原理.md` |

### 非目标

- 不给 `<img>` 补 `data-w`（无 PIL，无法可靠获取原图宽）。
- 不做主题数量收敛（30 → 精选，属另一议题）。
- 不移除 code/pre 的等宽 `font-family`（合理例外，见 §5）。
- 不做真实深色模式模拟（平台算法不可复刻）。
- 不破坏文内 `#` 锚点与 `mailto:` 链接（见 §1）。

---

## 二、现状 vs 官方规范

| 官方条款 | 当前实现 | 状态 |
|----------|----------|------|
| §1.8 `pre` 不应承载内容（移动端截断） | 代码块用 `<section><pre>`（format.py:1226-1269） | ✗ 改 |
| §1.4.4 固定宽/横向滚动需 `data-ignore-width` | `:::gallery` 横向滚动无豁免（format.py:989-1047） | ✗ 改 |
| §2.1 同标签同样式单子节点嵌套 ≤ 10 层 | 实际 3-4 层 | ✓ 加测试锁死 |
| §2.2 `span[leaf]` 仅行内元素 | 未使用 `leaf` | ✓ |
| §3 不建议设置任何 `font-family` | 仅 code/pre_code 设等宽 | △ 文档注明例外 |
| §4.1.2 文字背景尽量不用渐变 | 30 主题共 **97** 处（含 border_image 9） | ✗ 改 |
| §4.5.2 不使用 `!important` | 无 | ✓ |
| Dark Mode 自动转换 + `data-no-dark`/`data-ignore-dm` | 手写 `data-darkmode-*`（74 个/篇）+ 30 主题 `dark_mode` 块 | ✗ 改 |

**关键判断**：官方规范已不再描述 `data-darkmode-color/bgcolor`，而是以「平台自动转换算法」为核心。当前实现手写暗色属性属于旧机制，应移除并依赖算法。

**补充事实**：`_auto_dark_mode()` 会为 `p/strong/h3/h4/h5/h6/td/list_item_text/footnote_item/footnote_title/callout_content` 自动补默认暗色，即使主题无 `dark_mode` 块也会触发。因此必须**删除函数本身**，不能只删主题块。

---

## 三、详细设计

### §1 外链：去掉上标引用，降级为纯文本

**删除** `extract_links_as_footnotes()`（format.py:409-448）。

**新增**：
```python
from urllib.parse import urlparse   # 顶部新增 import

def unwrap_external_links(html: str) -> str:
    """把 http(s) 外链 anchor 拆成链接文字；mp.weixin 内链保留为 <a>。"""
```

实现约束：
- 正则 `<a\s[^>]*?(?<![-\w])href\s*=\s*"([^"]*)"[^>]*>(.*?)</a>`（`DOTALL`）。`(?<![-\w])` 边界防止命中 `data-href`；当前 Markdown 输出 href 恒为双引号，单引号不在范围内。
- 仅拆 **http/https**：`href.lower().startswith(("http://", "https://"))`。`#` 锚点、`mailto:`、相对路径**原样返回**，避免破坏文内目录锚点。
- host 判定：
  ```python
  host = (urlparse(href).hostname or "").lower()
  if host == "mp.weixin.qq.com" or host.endswith(".mp.weixin.qq.com"):
      return match.group(0)          # 保留 anchor
  return match.group(2)              # 只留链接文字（含 <code>/<strong> 等内联 HTML）
  ```
  后缀判断天然排除 `mp.weixin.qq.com.evil.com`。
- Markdown autolink（`<https://x>`）链接文字即 URL，拆后保留 URL 文本，符合「只留文字」。

**生效范围**：仅 wechat 输出。`format_for_output()` 中 plain / html 分支在调用前 `return`，`--format html` 保留原始 `<a>`（"标准 HTML"语义）。结构：
```python
html = md_to_html(content)
if output_format == "plain":
    return {...}                 # 不处理链接
if output_format == "html":
    return {...}                 # 保留 <a>
html = unwrap_external_links(html)   # 仅 wechat
return {...}
```

**管道清理**（`footnote_html` 恒为空，整条移除）：
- `format_for_output()` 返回 `{"html", "title", "word_count"}`；删除 :1660 `extract_links_as_footnotes` 调用；删除 :1628-1630 docstring 中 `footnote_html` 声明；plain/html 两分支返回结构同步。
- `main()` **精确删除，勿误伤正文**：
  - 删 :1726 `footnote_html = result["footnote_html"]`（保留 :1725 `html = result["html"]`）
  - 删 :1733-1734 非微信分支脚注拼接（保留 :1730-1732、:1735 写出）
  - 删 :1794-1795 脚注样式注入（**保留 :1797 `html = convert_image_captions(html)`**）
  - 删 :1798-1799 脚注图说
  - 删 :1803-1804 `full_article += "\n" + footnote_html`（保留 :1801-1802、:1805-1806）
  - 改 :1810 `generate_preview(html, theme, title, word_count, preview_path)`（去掉实参）
- Gallery：`_render_single_theme(tid, theme_data, gallery_html)` 去 `gallery_footnote`（:1538-1545）；`main` gallery 分支 :1744-1745、:1768 同步。
- `generate_preview()` 签名改 `(article_html, theme, title, word_count, output_path)`（:1475-1496）；**调用点 :1810 必须同步**。

**保留**：`process_manual_footnotes()`（:483-527）与 `FOOTNOTE_PLACEHOLDERS`、主题 `footnote_sup/section/title/item` 键不变——手写 `[^N]` 脚注仍可用。

**文档**：`SKILL.md` 内置增强中「外链转脚注：正文标注 + 文末脚注」→ 改为「外链降级为纯文本（URL 丢弃，微信内链保留）」。

---

### §2 深色模式：彻底移除手写 darkmode

**引擎删除**：
- `_auto_dark_mode(theme)`（format.py:793-828）
- `inject_dark_mode_attrs(...)`（format.py:831-855）
- `inject_inline_styles()` 中的调用（format.py:1348-1351）

**主题清理**（30 个 `themes/*.json`）：删除顶层 `"dark_mode": {...}` 块。

**渐变清理规则**（官方 §4.1.2）：

| 键 | 处理 |
|----|------|
| `strong` | `background_color = rgba(accent_rgb, 0.12)`，删 `background` / `background_image` |
| `h1/h2/h3/h4`、`th`、`blockquote`、`code_header`、`callout`、`code`、`ol_item_bullet` 的 `background` / `background_image` | 转实色 `background_color` = 解析出的实色；**但末 stop alpha=0 时回退首 stop**（淡出型渐变），全部透明才删除 |
| 装饰型背景（伴随 `background_size`/`background_position`/`background_repeat`，如 `focus-*` 的上下 1px 细线） | 删除 `background_image` 及装饰属性，用实色 `border_top`/`border_bottom`（1px solid）还原；**绝不**铺 `background_color`（否则细线变整块底色） |
| `h2/h3/blockquote/callout` 的 `border_image` | **直接删除** `border_image`，保留既有 `border_left` 实色（实测 9 处均已有 `border_left`；`sports` 的 `border_left` 无显式色 → 继承 `currentColor`，可接受）。**不得**把渐变转成 `background_color`（否则竖边框变整块底色） |
| `hr` | 保留渐变（无文字承载，§4.1.3 允许） |

**实色解析算法**（`migrate_themes_spec.py` 必须实现，覆盖真实数据）：
1. 取属性值中**最后一个** `(linear|radial|conic)-gradient(...)` 函数（含 `repeating-` 与 `-webkit-` 前缀）：用括号配对定位，**不能按逗号 split**（`focus-*` 的 `background_image` 是双逗号分隔渐变）。`radial-gradient` 真实存在于 `midnight.h2/h3`、部分 `th`，必须一并覆盖。
2. 在该函数体内按**顶层逗号**切分 token，只保留颜色 stop（忽略 `180deg`/`to bottom`/`circle` 等方向 token）。
3. 剥离位置后缀（如 ` 100%`、` 0`、` 8px`），仅留颜色 token。
4. 颜色/alpha 归一：
   - 取**末个彩色 stop**；末 stop 透明（alpha=0）时**回退到首 stop**（淡出型渐变的有意义颜色在首端，如 `lavender-dream.h2` 的 `0.94→0`）；首末均透明才**删除整个属性**（如 `chinese.h1` 的 repeating 透明条纹）。
   - 其余保留原 alpha（如 `rgba(50,104,145,0.1)` 保持 0.1）。
5. 装饰型背景判定：属性含 `background_size`/`background_position`/`background_repeat` 时视为装饰线，走表格第 2 行规则（边框还原），不进 `background_color` 分支。

**实施分级（可回滚）**：
- **提交 1**：删引擎注入函数 + 调用（format.py）。此步后产物不再带 `data-darkmode-*`，但主题仍保留 `dark_mode`（无消费方，无副作用）。
- **提交 2**：主题迁移脚本 + 30 主题落盘。
- 真机验收不通过 → 回滚提交 1 即恢复手写暗色。

**兜底（条件动作，非默认）**：若真机发现代码块/图片在暗色下表现差，按官方 §4.5.1 对 `code_block` 容器加 `data-no-dark`（仅该节点）。

**验收关卡（人工）**：对 `newspaper` 主题产出的 `article.html`，在公众号编辑器「深色模式预览」与真机深色模式下确认：正文、标题、引用块、表格、代码块均可读；再抽查 `bytedance`、`midnight` 各一次。

---

### §3 代码块：`<pre>` → `<section>`

**修改** `style_pre()`（format.py:1226-1269）：
- 现状：`<section code_block><section code_header>…dots…</section><pre pre>…</pre></section>`。
- 改为：`<section code_block><section code_header>…dots…</section><section pre>…</section></section>`。
- 内联样式须含 `white-space:pre-wrap;word-break:break-all`（主题 `pre` 键已含，如 newspaper.json:144-157）。
- 换行仍由已实现的 `&nbsp;` + `<br>` 保障，与 `<pre>` 语义无关。
- `code` 内联标签样式（`pre_code`）保留。
- **同步删除主题 `pre` 键的 `overflow_x`**（如 newspaper.json:149）或给代码块 `<section>` 加 `data-ignore-width`。因已 `pre-wrap + break-all` 双向换行，无需滚动 → **删除 `overflow_x`**（§4 论据闭合）。

**说明**：官方 §1.8 针对用 `<pre>` 包裹普通段落；代码块属半例外，但本项目已手工处理空格与换行，改用 `<section>` 无功能损失且彻底规避移动端截断。

---

### §4 宽度豁免

**修改** `process_fenced_containers()` 与 `_inject_container_styles()`：
- `gallery-scroll` 标记增加**裸布尔**属性 `data-ignore-width`（与官方 §1.4.4 示例一致）：
  - 生成处：`<section data-container="gallery-scroll" data-ignore-width>`
  - 注入处：`html.replace('<section data-container="gallery-scroll" data-ignore-width>', '<section data-container="gallery-scroll" data-ignore-width style="{gallery_scroll}">')`
- `:::longimage` 为纵向滚动（`max-height + overflow-y`），无横向溢出，不加豁免。
- 图片维持 `width:100%` 响应式。

---

### §5 结构 / 字体

- `!important`、`text-align:start/end`、`span leaf`：现状已合规，§8 测试锁死。
- 嵌套 ≤10：当前最大约 3-4 层，不引入运行时 dedupe；§8 测试断言。
- `font-family`：仅 code/pre_code 保留等宽字体，作为官方 §3 的合理例外，在 `SKILL.md`「规范对齐」小节注明。

---

### §6 预览页

- `templates/preview.html` 顶部信息区加一行提示：「深色模式以微信平台算法为准」。
- 不实现假深色切换（平台算法不可复刻，避免误导）。

---

### §7 文档

**`SKILL.md`**：
- 「内置排版增强」重写：
  - 删除「外链转脚注」条目，替换为「外链降级纯文本（http(s) 外链拆为文字，微信内链保留）」。
  - 「深色模式：自动生成 data-darkmode-* 属性」→「深色模式：遵循平台自动转换算法，不做手写暗色覆盖」。
  - 代码块条目注明使用 `<section>` 而非 `<pre>`。
- 新增「微信官方规范对齐」小节，逐条列出 §1.4.4/1.8/2.1/3/4.1.2/4.5.2 的合规方式与本 skill 实现位置。

**`to-wechat.md`**：
- 注意事项补充：「正文 http(s) 外链会降级为纯文本、URL 不保留；`mp.weixin.qq.com` 内链保留可点击；`#` 锚点与 `mailto:` 不受影响；手写 `[^N]` 脚注仍支持」。

---

### §8 回归测试

新增 `scripts/test_spec_compliance.py`（**stdlib `unittest`**，因系统 `python3` 无 pytest）。

**测试方式**：
- `unwrap_external_links` / `style_pre` 等纯函数：`sys.path.insert(0, SCRIPT_DIR)` 后 import 直测（快、可断言返回值）。
- `main` 全链路：`subprocess` 跑一次，读产物 `article.html`。
- 注意：`format.py` import 期读取 `SKILL_DIR/config.json`（format.py:103）；测试以仓库内已存在的 config 为准。

Fixture 覆盖：http 外链、`mp.weixin` 内链、`#` 锚点链接、`mailto:`、手写 `[^1]` 脚注、fenced code、`:::gallery`、`blockquote`、`**strong**`、`:::timeline/steps/compare/quote`。

断言（全部基于产物 `article.html`）：
1. 外链处无 `<sup>`；`mp.weixin` 内链保留 `<a`；`#` 锚点与 `mailto:` 原样保留；手写脚注仍产生 `<sup>`。
2. 全文不含 `data-darkmode-`。
3. 全文不含 `<pre`。
4. 对全文**所有** `style="..."` 属性统一扫描：除 `hr` 外不含任何 `*-gradient(`（linear/radial/conic/repeating）；且全文不含渐变 `border-image`（兼容官方「样式逻辑键 ≠ 标签名」，不按标签名硬编码）。
5. `data-container="gallery-scroll"` 所在标签含 `data-ignore-width`。
6. 全文不含 `!important`。
7. 同一标签同样式单子节点连续嵌套 ≤10 层。
8. `--format html` 产物仍含 `<a href`（验证 unwrap 不作用于 html 分支）。

---

## 四、文件清单

| 文件 | 改动 |
|------|------|
| `.opencode/skills/wechat-format/scripts/format.py` | 删 `extract_links_as_footnotes`、`_auto_dark_mode`、`inject_dark_mode_attrs`；新增 `unwrap_external_links` + `urllib.parse` import；清 `footnote_html` 管道（含 :1810 与 docstring）；`style_pre` 标签替换；gallery 加豁免 |
| `.opencode/skills/wechat-format/scripts/migrate_themes_spec.py` | 新增：批量删 `dark_mode` + 文字渐变转实色 + 删 `border_image`（幂等） |
| `.opencode/skills/wechat-format/scripts/test_spec_compliance.py` | 新增：规范回归测试 |
| `.opencode/skills/wechat-format/themes/*.json` | 30 个：删 `dark_mode` + 渐变转实色 + 删 `pre.overflow_x` |
| `.opencode/skills/wechat-format/templates/preview.html` | 新增深色模式提示行 |
| `.opencode/skills/wechat-format/SKILL.md` | 内置增强重写 + 新增规范对齐小节 |
| `.opencode/commands/to-wechat.md` | 注意事项补充外链行为 |

---

## 五、验收标准

### 自动化

```bash
# 1. 规范回归测试
python3 .opencode/skills/wechat-format/scripts/test_spec_compliance.py

# 2. 迁移脚本幂等性：约定脚本无变化不写盘，且固定序列化
#    json.dumps(d, ensure_ascii=False, indent=2)，不加末尾换行（实测字节级复原）
python3 .opencode/skills/wechat-format/scripts/migrate_themes_spec.py
git diff --stat .opencode/skills/wechat-format/themes/   # 第二次应为空

# 3. 真实文章端到端
python3 .opencode/skills/wechat-format/scripts/format.py \
  --input content/article/20260910-Transformer架构原理.md \
  --theme newspaper --output /tmp/spec-align --no-open

grep -q 'data-darkmode-' /tmp/spec-align/*/article.html && echo 'FAIL darkmode' || echo 'PASS darkmode'
grep -q '<pre' /tmp/spec-align/*/article.html && echo 'FAIL pre' || echo 'PASS pre'
python3 - <<'PY'
import glob, re
html = open(glob.glob('/tmp/spec-align/*/article.html')[0], encoding='utf-8').read()
no_hr = re.sub(r'<hr[^>]*>', '', html)   # hr 无文字承载，允许渐变
print('FAIL gradient' if re.search(r'[a-z-]*gradient\(', no_hr) else 'PASS gradient')
print('FAIL border-image' if 'border-image' in no_hr else 'PASS border-image')
PY
grep -o '<sup[^>]*>' /tmp/spec-align/*/article.html | head   # 本文章 0 手写脚注 → 应为空
```

### 人工

- 将 `article.html` 粘贴进公众号编辑器，切换「深色模式预览」：正文/标题/引用/表格/代码块可读。
- 真机深色模式复核一次。
- 浅色模式下 `newspaper` 观感与改造前基本一致（渐变→实色的偏差可接受）。
- 重点复核 `strong` 高亮：原为「下半段荧光笔」渐变，改为 `rgba(accent,0.12)` 整块底色后几何变化最明显；若观感不可接受，退化为 `border-bottom: 2px solid rgba(accent,0.35)` 方案（newspaper 等 8 个主题）。

---

## 六、风险

| 风险 | 级别 | 缓解 |
|------|------|------|
| 移除 `data-darkmode-*` 后暗色观感变化 | 中 | 分两次提交（引擎先、主题后），回滚提交 1 即恢复；编辑器暗色预览 + 真机为硬性验收关卡 |
| 渐变→实色使主题观感微变 | 中 | `migrate_themes_spec.py` 幂等可复现；逐主题 `git diff`，先抽查 newspaper/bytedance/midnight |
| 删除 `footnote_html` 管道是非局部改动 | 低 | 精确行号（保留 :1797 正文图说）；§8 覆盖 wechat/plain/html/gallery 分支 |
| 平台暗色算法真实行为与规范文档有偏差 | 中 | 真机验证为硬性关卡；不通过则回滚提交 1，或对敏感节点加 `data-no-dark` |
| `unwrap` 误伤 `#` 锚点 / `mailto:` | 低 | 限制仅 http(s) 外链；§8 断言覆盖锚点与 mailto |
| 官方规范原文不可审计 | 低 | 附录 A 附链接与抓取日期；可选把快照存入 `docs/` |

---

## 七、实施波次（供 writing-plans 展开）

```
Wave 1 — 引擎行为
  T1 §1 外链降级（删函数 + 新增 unwrap + 清管道，含 :1810 与 docstring）
  T2 §2 删 darkmode 注入函数与调用（提交 1，可回滚）
  T3 §3 代码块 section 化 + §4 gallery 豁免

Wave 2 — 主题迁移（依赖 T2）
  T4a migrate_themes_spec.py（含 border_image / 多渐变 / repeating 规则）
  T4b 30 主题落盘 + 删 pre.overflow_x + 人工抽查（提交 2）

Wave 3 — 文档与测试
  T5 测试脚本
  T6 SKILL.md / to-wechat.md / preview.html
```

Wave 1 内 T1-T3 相互独立；T4 依赖 T2；T5/T6 依赖 Wave 1+2。

---

## 八、审查记录

| 审查者 | 日期 | 主要发现 | 整合状态 |
|--------|------|----------|----------|
| Sisyphus（自审） | 2026-09-11 | 坏验收管道 | ✅ 已修 |
| design-critic 兜底（general） | 2026-09-11 | B1-B4 阻断；H1-H5 高优先；Y1-Y6 建议 | ✅ 全部整合进本版 |
| design-critic 兜底（general）·复核 | 2026-09-11 | B1-B4/H2-H5/Y1-Y6 全部落地；新发现 radial/conic 未覆盖 + alpha=0 分级衔接 + strong 几何变化 | ✅ 已补（算法扩为 `*-gradient`、表格衔接第4步、§5 加 strong 复核项与退路） |
| plan-reviewer | 2026-09-11 | 无阻断；H1 border_image 规则与 spec 不一致（实为 spec 被回退）、Y1 换行注不一致（同上）；plan 侧死代码/断言窗口/定位描述 | ✅ spec 回改 border_image=直接删除、末尾不换行；plan 删 `BACKGROUND_KEYS`、窗口 120→200、定位改 :1262-1267 |
| 实施（executing-plans） | 2026-09-11 | 发现既有 bug：`fix_cjk_spacing` 多链接同行占位符残留 | ✅ 已修（保护顺序改为 代码→图片→链接→裸URL），加回归测试 |
| 实施验收（自动化） | 2026-09-11 | 34 项单测 PASS；newspaper/bytedance/midnight 三主题产物：无 data-darkmode-、无 `<pre>`、无 gradient(、无 border-image、无 !important；真实文章外链 0 残留、0 占位符 | ✅ 自动化通过 |
| 实施验收（人工深色模式） | 2026-09-11 | 待用户在公众号编辑器「深色模式预览」+ 真机确认 | ⏳ 待办 |
| code-review（general，b85c156..fe50c02） | 2026-09-11 | C1 focus-* 标题装饰细线被误转为整块底色；I1 淡出型渐变被整段删除（应取首 stop）；I3 测试盲区（无 hr fixture、无 focus 断言） | ✅ 已修：算法加首-stop 回退 + 装饰线转边框；补 focus/lavender/hr 断言；spec §2 算法同步 |

---

## 附录 A：官方规范出处

- 《微信公众平台编辑器插件开发规范》：`https://developers.weixin.qq.com/doc/service/guide/product/plugin_spec.html`（抓取日期 2026-09-11）
- 官方校验实现：`https://github.com/wechatjs/verify-article-structure-spec`

## 附录 B：数据核验方法

```bash
# 外链总数
grep -roh 'https\?://[^ )]*' content/article/*.md | wc -l
# 渐变 style 键统计
python3 - <<'PY'
import json, glob
bg = bi = bd = 0
for f in glob.glob('.opencode/skills/wechat-format/themes/*.json'):
    d = json.load(open(f, encoding='utf-8'))
    for tag, p in d.get('styles', {}).items():
        s = json.dumps(p, ensure_ascii=False)
        if 'linear-gradient' in s:
            if 'background_image' in p: bi += 1
            elif 'border_image' in p: bd += 1
            elif 'background' in p: bg += 1
print('background:', bg, 'background_image:', bi, 'border_image:', bd, 'total:', bg + bi + bd)
PY
```
