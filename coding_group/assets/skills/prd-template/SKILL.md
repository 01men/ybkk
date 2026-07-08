---
name: prd-template
description: 需求理解文档的强制模板。需求 Agent 在写 01-requirement-doc.md 时用。触发词：「PRD 模板」「写需求」。
---

# PRD Template

需求 Agent 写 `01-requirement-doc.md` 时强制按这个模板。**漏字段视为文档不完整**。

## 模板

```yaml
# 01-requirement-doc.md — 需求理解文档
req-id: <REQ-XXX，由 orchestrator 分配>
created: YYYY-MM-DD
author: requirements-analyst
version: 1

## 1. 一句话目标
（用一句话描述：谁在什么场景下做什么，得到什么结果）

## 2. 目标用户与场景
- 主要用户: <who>
- 触发场景: <when & where>
- 用户想要的: <核心欲望>

## 3. 用户故事（建议 3~7 条）
- AS <role> I WANT <feature> SO THAT <value>

## 4. 验收标准（**每条都可观察、可验证**）
- [ ] 当 <触发条件>，系统 <可观察行为>
- [ ] ...

## 5. 非目标（明确不做）
- ...
- ...

## 6. 影响半径
（由 impact-radius-analysis Skill 算出，填充进来）

## 7. PRD 完整性自评（5 维 0~100，每维 ≥ 60 总分 ≥ 60 为通过）
- 目标明确性: ?
- 验收可验证性: ?
- 范围清晰性: ?
- 数据/接口契约: ?
- 风险与依赖: ?
- 总分: ?

## 8. 阻塞项（如有）
- [BLOCKER] <描述>

## 9. 与上游/历史的关联（如适用）
- 与历史需求 REQ-XXX 的关系
- 与已有模块 foo 的关系
```

## 字段说明（坑最多的几处）

### 一句话目标
- **错**：「做一个更好的分享按钮」（不 "更好" 在哪？）
- **对**：「用户在文章页点击分享按钮，3s 内弹出含标题/摘要/二维码的分享卡」

### 验收标准
- **错**：「页面要好看」（不可验证）
- **对**：「页面在 1920×1080 桌面分辨率下，不出现横向滚动条」
- 每一条都用 Given/When/Then 或者 if/then 风格写

### 非目标
- 至少 3 条。**不写非目标的 PRD 默认被 review 打回**（文章里的隐含规则：用户不写非目标 = 你不知道下次要不要做这件事）

## 触发条件

需要写需求文档时（由 requirements-analyst Agent 触发），加载本 Skill，按模板生成。
