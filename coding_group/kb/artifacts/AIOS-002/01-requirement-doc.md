# 01-requirement-doc.md — V1 需求文档（AIOS-002 analyze 棒）

> 评估维度：5 维（用户价值 / 范围清晰 / 可验收 / 与架构契合 / 风险识别）
> 评估人：requirements-analyst
> 时点：2026-07-09 09:42 +08:00

---

## 1. V1 一句话定位

**让客户从「拿到代码」到「端到端跑通一个内置场景」= 一个 PR 周期内完成。**

## 2. 用户故事（V1 新增 / 升级）

### US-V1-1：数据源接入（升级）

**作为** 工厂 IT 管理员
**我想要** 在控制台页面填表 + 选只读账号 + 提交
**以便** 接入 MySQL/PG/SqlServer/Oracle 任一客户 DB，系统自动抽表元数据

**验收**：
- 浏览器打开 `http://<server>:3000/datasources`
- 看到列表页（空）
- 点「新建」→ 弹表单（host/port/user/password/db/read_only_account_ack）
- 提交 → 后台连接 → 抽表 → 列表页多一行 status=CONNECTED
- 失败 → 列表页多一行 status=FAILED + error 字段

### US-V1-2：场景模板加载（升级）

**作为** 业务部门负责人
**我想要** 在控制台看到 5 个内置场景 + 看到每个场景的流模板
**以便** 选择一个挂到数据源上

**验收**：
- 浏览器打开 `http://<server>:3000/scenarios`
- 5 个内置场景卡片（库存预警 / 设备保养 / 质检抽检 / 排产优化 / 来料异常）
- 点卡片 → 看流模板 DAG 图 + 默认标准
- 点「激活」→ 选数据源 → 创建 Flow

### US-V1-3：流程运行（新增）

**作为** 业务部门负责人
**我想要** 看到流程运行实时状态 + 历史
**以便** 知道流程跑没跑、跑成没跑成

**验收**：
- 浏览器打开 `http://<server>:3000/flows`
- 列表显示所有 Flow
- 点 Flow → 看 FlowRun 历史（pending / running / succeeded / failed / cancelled）
- 手动触发按钮（对 schedule 类型场景）

### US-V1-4：审计日志（升级）

**作为** 工厂审计员
**我想要** 在控制台看到所有操作记录 + 不可篡改
**以便** 出合规报告

**验收**：
- 浏览器打开 `http://<server>:3000/audits`
- 列表按时间倒序，显示 actor/action/target/payload/hash_chain
- 链完整性校验按钮（前端调 `verifyChain` 显示「valid」或「broken at N」）

### US-V1-5：登录 / 鉴权（新增）

**作为** 系统
**我需要** 任何人访问控制台必须先登录
**以便** 区分 actor 写审计

**验收**：
- 浏览器打开 `http://<server>:3000` → 跳到 `/login`
- 输 admin / 初始密码 → 进控制台
- JWT 存 httpOnly cookie
- 后续所有 API 走 JWT

## 3. 范围（IN / OUT）

### IN（V1 必须做）

- Next.js 14 App Router 工程启动
- 5 个前端页面：login / datasources / scenarios / flows / audits
- Ant Design Pro 组件库
- apps/flow_engine 服务（FastAPI + Temporal worker）
- 5 个内置场景的 Temporal Workflow 实现
- FlowRun 状态机
- 3 类触发器：manual / schedule / ontology_event
- Playwright E2E：login → 接入数据源 → 激活场景 → 触发 → 看 FlowRun → 看审计
- JWT 鉴权中间件（V1 简化版：单租户 + admin role）
- 5 道门禁在客户机器实跑

### OUT（V1 不做）

- Excel / PDF / 会议 worker（V2）
- 本体推断 / Neo4j（V2）
- 多租户 / RBAC 完整版（V3）
- 监控告警 / Grafana（V3）
- 安装脚本完善 / 离线安装（V3）

## 4. 与架构契合度

| 维度 | 评估 |
|---|---|
| V0 数据层延续 | ✅ 复用 datasources / scenarios / flows / flow_runs / audit_log 表 |
| V0 错误体系 | ✅ 复用 errors.py + 中间件 |
| V0 审计 hash 链 | ✅ 复用 packages/audit |
| V0 LLM 网关 | ✅ 暂不接（场景执行 V1 走同步 + 标准引擎；LLM V2 再接） |
| Temporal 引入 | ⚠️ 新增依赖，docker-compose 加 1 个服务（temporal + 1 worker） |

## 5. 风险识别

| 风险 | 概率 | 影响 | 对策 |
|---|---|---|---|
| Next.js 构建慢（大型前端） | 中 | 中 | 用 App Router + RSC，按需引入 antd pro 组件 |
| Temporal 学习曲线 | 中 | 中 | 抄官方 Python SDK 示例，5 场景走同一个 worker 框架 |
| Playwright E2E 跑挂 | 中 | 高 | 拆成 5 个独立 E2E，CI 可分批跑 |
| 前端调 API 跨域 | 低 | 中 | 同源部署（Next.js SSR + FastAPI 同 domain）|
| 5 道门禁客户机器 GPU 驱动不齐 | 低 | 中 | install.sh 加预检 + 缺包自动装 |

## 6. 5 维自评

| 维度 | 分 | 评语 |
|---|---|---|
| 用户价值 | 90 | 客户拿到产品端到端跑通一个场景 = 「AI 转型」第一脚 |
| 范围清晰 | 88 | 5 个用户故事验收点明确，IN/OUT 划分清 |
| 可验收 | 85 | 5 道门禁 + E2E 可客观判定 |
| 与架构契合 | 92 | 100% 复用 V0 资产，只新增 flow_engine + apps/web |
| 风险识别 | 80 | 5 个风险都给了对策 |
| **平均** | **87** | ≥ 60 阈值 ✅ |

## 7. 门禁

- ✅ PRD 自评 87 分（≥ 60）→ 进入「需求确认」棒
