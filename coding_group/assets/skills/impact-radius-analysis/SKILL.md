---
name: impact-radius-analysis
description: 估算一次需求会动多少模块、多少接口、多少文件、多少风险点。写需求理解后必跑。触发词：「影响半径」「估算」「哪些模块」。
---

# Impact Radius Analysis

## 用途

把模糊的「这个需求有多大」翻译成具体的「要动哪些东西」。给方案设计和总控判断要不要弹「方案确认」关卡。

## 估算维度

| 维度 | 怎么估 |
|---|---|
| **涉及模块** | frontend / backend / database / deploy / configs / tests / docs |
| **新增接口** | 列出 URL + 方法 + 入参出参契约 |
| **修改接口** | 同上（标 modified） |
| **数据模型变更** | 新增 / 修改 / 删除字段 |
| **文件估算** | 粗估会动多少个文件 |
| **风险等级** | low / medium / high |

## 风险等级判定（自动）

```
high    = 涉及：鉴权改造 / 数据迁移 / 多模块协作 / 接口合约破坏
medium  = 涉及：数据库 schema 变化 / 第三方依赖接入 / 性能边界变更
low     = 单模块 + 纯前端 / 纯配置改动
```

## 输出格式（写到需求文档 §6）

```yaml
## 6. 影响半径
involves:
  modules: [frontend, backend]            # 列表
  endpoints_added:
    - method: POST
      path: /api/screenshots
      req: {url: string}
      res: {id: string, url: string}
  endpoints_modified: []
  db_changes:
    - table: screenshots
      change: add column thumbnail_url
  file_estimate: ~12
  risk_level: medium
crosses_module_boundary: true    # 跨模块 → orchestrator 弹方案确认关卡
performance_boundary_change: false
auth_change: false
data_migration: false
```

## 触发特殊流程的判定

| 条件 | 触发 |
|---|---|
| `risk_level == high` | orchestrator **必弹**方案确认关卡 |
| `crosses_module_boundary` | orchestrator **必弹**方案确认关卡 |
| `auth_change` 或 `data_migration` | orchestrator **必弹**方案确认关卡 + 在交付报告标记 `requires_human_eyes: true` |
| 其他 | orchestrator 走默认流程 |

## 反例

- ❌ 只写「涉及后端」不说具体接口
- ❌ 列了一堆接口但不给字段
- ❌ 把"加一个按钮"估成 high 风险
- ❌ 不打 `crosses_module_boundary` 让 orchestrator 漏弹确认关卡
