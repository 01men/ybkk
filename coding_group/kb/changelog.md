# Changelog — 体系演进日志

> 任何对 AGENTS.md / Skill / Scripts / Workflow 的修改都写一行在这里。三个月后你才会感谢这一份。

## 格式

```markdown
## YYYY-MM-DD: <一句话标题>

- 改动: <改了哪个文件 / 哪一段、为什么>
- 触发原因: <那次撞墙 / 那个需求>
- 影响面: <哪些 Skill / 哪些 Agent 受影响>
- 回滚方法: <如果改坏了怎么改回去>
```

---

## 启动记录

- YYYY-MM-DD（今天）：V1 建立。
  - 改动: 初始搭脚手架（AGENTS.md / 11 个 Skill / 5 道门禁脚本 / 5 个 Agent prompt）
  - 触发原因: 从零开始按个人编程 Agent 团队搭建方案落地
  - 影响面: 全部
  - 回滚方法: `git revert` 这次 commit，或在 git 历史里找回上一个稳定版本
