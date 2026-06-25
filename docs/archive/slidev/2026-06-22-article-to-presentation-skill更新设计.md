# article-to-presentation Skill更新设计文档

## 概述

更新article-to-presentation skill，添加PPT显示优化经验。

## 需求

1. **添加全屏按钮**：在右上角添加全屏显示按钮
2. **优化内容显示区域**：内容区域完全铺满整个网页空间，无边距无空白
3. **优化图表显示**：图表大小随容器自适应，确保完整显示

## 设计方案

### 1. 更新SKILL.md

在SKILL.md中添加显示优化相关章节：

```markdown
## 显示优化经验

### 全屏按钮

- 位置：右上角
- 样式：半透明橙色背景，悬浮在内容之上
- 实现：Fullscreen API
- 响应式：不同窗口大小下正确显示

### 内容铺满

- 目标：内容区域完全铺满浏览器窗口，无边距无空白
- 实现：修改CSS，使用viewport单位
- 关键CSS：
  ```css
  .reveal .slides {
    padding: 0 !important;
    margin: 0 !important;
    width: 100vw !important;
    height: 100vh !important;
  }
  
  .reveal .slides section {
    padding: 0 !important;
    margin: 0 !important;
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    align-items: center !important;
  }
  ```

### 图表自适应

- 目标：图表自适应容器，确保完整显示
- 实现：为图表添加CSS类
- 图表类型：
  - 柱状图：`.bar-chart`
  - 进度条：`.progress-container`
  - 气泡图：`.bubble-chart`
  - SVG图表：`.iceberg-chart`
```

### 2. 更新technical-details.md

在technical-details.md中添加显示优化技术细节：

```markdown
## 显示优化技术

### 全屏按钮HTML

```html
<button id="fullscreen-btn" style="
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  background: rgba(255, 107, 53, 0.8);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
">全屏</button>
```

### 全屏按钮JavaScript

```javascript
document.getElementById('fullscreen-btn').addEventListener('click', function() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen().catch(err => {
      console.log(`全屏请求失败: ${err.message}`);
    });
  } else {
    document.exitFullscreen();
  }
});
```

### 图表容器CSS

```css
/* 柱状图容器 */
.bar-chart {
  width: 80% !important;
  max-width: 800px !important;
  height: 70vh !important;
  display: flex !important;
  justify-content: center !important;
  align-items: flex-end !important;
  gap: 100px !important;
}

/* 进度条容器 */
.progress-container {
  width: 80% !important;
  max-width: 800px !important;
}

/* 气泡图容器 */
.bubble-chart {
  width: 80% !important;
  max-width: 800px !important;
  height: 60vh !important;
  display: flex !important;
  justify-content: center !important;
  align-items: center !important;
  gap: 80px !important;
}
```

### 响应式样式

```css
/* 全屏按钮响应式 */
@media (max-width: 768px) {
  #fullscreen-btn {
    top: 10px !important;
    right: 10px !important;
    padding: 8px 16px !important;
    font-size: 12px !important;
  }
}

/* 全屏模式下按钮样式 */
:fullscreen #fullscreen-btn {
  background: rgba(255, 107, 53, 0.6) !important;
}

:fullscreen #fullscreen-btn:hover {
  background: rgba(255, 107, 53, 0.9) !important;
}
```
```

### 3. 更新common-pitfalls.md

在common-pitfalls.md中添加显示优化相关陷阱：

```markdown
## 显示优化陷阱

### 1. 内容未铺满

**问题**：内容区域有边距或空白，未完全铺满浏览器窗口

**原因**：`.reveal .slides`和`.reveal .slides section`的padding设置

**解决方案**：
```css
.reveal .slides {
  padding: 0 !important;
  margin: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
}

.reveal .slides section {
  padding: 0 !important;
  margin: 0 !important;
  width: 100% !important;
  height: 100% !important;
}
```

### 2. 图表显示不全

**问题**：图表被截断或未完整显示

**原因**：图表容器使用固定像素尺寸，未自适应容器

**解决方案**：
- 为图表添加CSS类（`.bar-chart`, `.progress-container`, `.bubble-chart`）
- 使用百分比和viewport单位设置尺寸
- 使用flexbox布局确保居中显示

### 3. 全屏按钮不显示

**问题**：全屏按钮未显示或被遮挡

**原因**：z-index设置不当或位置错误

**解决方案**：
- 设置`z-index: 1000`确保在最上层
- 使用`position: fixed`固定位置
- 设置`top: 20px; right: 20px`确保在右上角
```

## 实施步骤

1. 更新SKILL.md，添加显示优化经验章节
2. 更新technical-details.md，添加显示优化技术细节
3. 更新common-pitfalls.md，添加显示优化相关陷阱

## 验证标准

1. ✅ SKILL.md包含显示优化经验
2. ✅ technical-details.md包含显示优化技术细节
3. ✅ common-pitfalls.md包含显示优化相关陷阱
4. ✅ 所有代码示例可直接使用

## 风险评估

- **低风险**：仅更新文档，不影响核心功能
- **兼容性**：所有代码示例已在实际项目中验证
- **回滚方案**：如出现问题，可恢复原始文档