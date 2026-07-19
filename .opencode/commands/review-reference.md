---
description: 审核参考资料
model: Volcengine-Plan/DeepSeek-V4-Flash
---

# 审核参考资料

## 目标

对创作主题相关的参考资料进行准确性、时效性和合法性审查，确保数据可靠。

## 前置条件

已完成 `/review-topics`，`content/reference/` 目录已有参考资料

## 输入

- `content/reference/` 目录下的资料文件

## 步骤

1. 派遣 `librarian` Agent逐条核实参考数据：确认每条数据准确且为最新版本。优先查找官方一手来源进行交叉验证。
2. 派遣 `librarian` Agent追溯所有引用来源：验证不存在内容幻觉或错误引用。
3. 审查内容合法性：剔除所有不良、违规或侵权信息。
4. 如发现问题，给出具体修正意见供我审核，不要直接修改资料文件。

## 输出

- 修正意见清单（在对话中呈现）
- 经用户确认后，**新建** `content/reference/{YYYYMMDD}-{主题名}-v{N+1}.md`（N 为当前版本号），保留旧版本文件不删

## reference 命名空间规范

- `/review-topics` 输出 → `content/reference/{YYYYMMDD}-{主题名}-v1.md`（首次审核问答）
- `/review-reference` 每次确认后 → 在原文件名基础上**新建** `-v{N+1}.md`，**不覆盖**旧版本
- 老文件（如 `-审核记录` 后缀）保留不动，不强制迁移
- 示例演进：`Kimi-K3-v1.md` → `Kimi-K3-v2.md`（首次 review-reference） → `Kimi-K3-v3.md`（再次 review-reference）

## 约束

**必须遵守：**

- 数据核实优先查找官方一手来源
- 关注数据的时效性，标注过期数据及更新时间

**禁止操作：**

- 不要未经确认直接修改资料文件
- 不要仅凭模型训练数据判断真伪，须以搜索查证结果为准
