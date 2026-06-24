# 重构 article-to-presentation：改用配置禁用目录生成

## 需求背景

`article-to-presentation` 技能当前通过全量 CSS selector 强制隐藏所有导航/目录/overview 面板，存在以下问题：

1. **代码重复**：TOC 隐藏 CSS 在 3 个文件重复出现，版本不一致（SKILL.md 和 common-pitfalls.md 缺失 2 个 selector）
2. **CSS 范围过大：不仅隐藏 TOC，错误隐藏了所有导航、侧边栏、overview 面板
3. **导出配置缺失**：frontmatter 模板未添加 `export.withToc: false`，导出 PDF 会自动生成目录页

用户要求：移除通过全量 CSS selector 强制隐藏所有目录相关元素，使用配置移除。

## 设计方案

### 目标
- 通过 Slidev 原生配置 `export.withToc: false` 禁用导出 PDF 时自动生成目录页
- CSS 只隐藏 UI 层面的 TOC 面板，保持 B 站录屏清洁（无目录遮挡）
- 消除代码重复，只在 `technical-details.md` 保留一份权威 CSS 定义

### 变更范围

| 文件 | 变更内容 |
|------|----------|
| `references/technical-details.md | 1. 在 frontmatter 模板添加 `export: withToc: false` <br> 2. 精简「录屏面板隐藏」CSS，只保留 TOC 相关 selector |
| `SKILL.md` | 删除内联 CSS 速查，改为直接引用 technical-details.md |
| `references/common-pitfalls.md | 更新陷阱 #14 的 selector 列表与权威版本一致 |

### CSS 精简对比

**修改前**（22 个 selector，隐藏所有导航面板）：
```css
#slidev-overview,
#slidev-toc,
.slidev-overview,
.slidev-toc,
.slidev-toc-list,
.slidev-sidebar,
.slidev-nav,
.slidev-slide-nav,
.slidev-nav-overlay,
.slidev-navigation,
.slidev-overview-panel,
.slidev-control-layout,
.nav,
.nav-overlay,
.toc,
.toc-overlay,
aside,
nav,
[class*="sidebar"],
[class*="toc"],
[class*="navigation"],
[class*="nav-overlay"],
[id*="slidev-overview"],
[id*="slidev-nav"],
[id*="slidev-toc"] {
  display: none !important;
}
```

**修改后**（只保留 TOC 相关，共 8 个 selector）：
```css
/* Hide only TOC (table of contents) panels for clean Bilibili recording */
#slidev-toc,
.slidev-toc,
.slidev-toc-list,
.toc,
.toc-overlay,
[class*="toc"],
[id*="slidev-toc"] {
  display: none !important;
}
```

### frontmatter 模板更新

**添加：
```yaml
# 禁用导出 PDF/PPTX 时自动生成目录页
export:
  withToc: false
```

## 收益

1. ✅ 导出目录由配置原生禁用，比 CSS 更优雅可靠
2. ✅ 不再错误隐藏导航面板，CSS 职责清晰
3. ✅ 消除代码重复，只维护一份权威定义
4. ✅ 保持 B 站录屏清洁，无 TOC 遮挡内容

## 风险评估

低风险，只修改技能文档模板，不影响已生成的 PPT。新生成的 PPT 会自动应用新配置。
