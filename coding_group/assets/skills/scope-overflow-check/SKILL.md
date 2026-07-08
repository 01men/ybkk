---
name: scope-overflow-check
description: 检查「这次改动有没有超出需求范围」。reviewer 在审查时必跑；developer 自己写完代码也跑一次。触发词：「范围溢出」「scope」「有没有越界」。
---

# Scope Overflow Check

## 用途

防御一类**最顽固**的 AI 行为：它写着写着觉得"这里顺手优化一下"、"这里设计得不好我改一下"。从它的角度是"优化"，从工程的角度是**擅自改设计**。

每一项超出需求范围的改动 → Reviewer **直接打回**。

---

## 自查清单（必跑 8 条）

```
1. 必读 01-requirement-doc.md §3「用户故事」：本次改动对应哪几条？
2. 必读 02-design-doc.md §10「范围」：我改了的内容是不是设计里的「包含」？
3. 必读 03-tasks.md：我改的每一行代码是不是在某条任务下？
4. 跑 git diff origin/main，**逐文件**判断：
   - 这个文件在不在设计文档 §2「架构变更」里？
   - 这个文件不在，但代码被动过（哪怕是一行），写 BLOCKER
5. 跑 git diff origin/main，**逐函数 / 逐类**判断：
   - 这个函数 / 类是不是设计文档里就有的？
   - 新增的，写 BLOCKER
6. 跑 git diff origin/main，**逐字段**判断（数据模型）：
   - 新增表 / 字段有没有在设计文档的「数据模型变更」段？
   - 没有，写 BLOCKER
7. 跑 git diff origin/main，**逐接口**判断：
   - 新增 endpoint / 修改现有 endpoint 有没有在「接口契约变更」段？
   - 没有，写 BLOCKER
8. 跑 git diff origin/main，**逐依赖**判断：
   - 新增第三方依赖（package.json / requirements.txt / go.mod）有没有在设计文档 §3「关键技术决策」段？
   - 没有，写 BLOCKER
```

---

## 阻塞项的写法

发现任一溢出 → **不要在对话里说**，按下面格式写到 `kb/artifacts/<req-id>/blockers/`：

```markdown
# [BLOCKER] 范围溢出 — <具体某条>

- 类型: 范围溢出
- 位置: <文件:行 或 模块>
- 现状: <代码在做什么>
- 期望: <应该改回去 / 删除 / 移到单独的需求>
- 复核: <怎么验证已经修好>

例如: 「在 git log 里此文件不应出现本次需求外的 commit」

## 影响半径
- 影响上下游: <是 / 否>
- 是否需要回滚: <是 / 否>
- 回滚方式: git revert <commit> 或 删除对应代码段
```

---

## 反例（绝对不能做的）

- ❌ 觉得"这一行顺手优化了" → 加进自己的 commit → 没写阻塞项
- ❌ 觉得"这设计写得不好，我改了" → 自己改了 → 没写阻塞项
- ❌ 觉得"反正用户会喜欢" → 加了点 PRD 没说的小功能
- ❌ 把"重命名" / "格式调整" 顺手做了而不写明

---

## 例外条款（什么情况下可以"顺手"做）

只有以下两类：

1. **拼写错误 / 明显 typo**：在 commit message 里写明 `chore(<req-id>): fix typo in src/foo.ts`
2. **删掉明显死代码**：dead import / 未使用的变量，必须提交单测通过的 evidence（如 `git blame` 表明超过 30 天未用）

其他的「顺手」 → 不行。

---

## 给 Reviewer 的强化提示

> Reviewer 这一项**从严**。宁可多写阻塞项，不要漏。

开发者会感谢你抓得严——reviewer 不抓，到了生产用户会抓，那代价大一个数量级。
