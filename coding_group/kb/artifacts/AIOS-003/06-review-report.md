# 06-review-report.md — V2 审查报告（AIOS-003 review 棒）

> 时点：2026-07-09 12:00 +08:00
> 审查人：reviewer
> 范围：04-code-changes.md 全集 + git diff
> 方法：scope-overflow-check / security-rules / coding-conventions / frontend-quality / feedback-loop-rules

---

## 1. 总体结论

**V2 review PASS。0 阻塞项。**

| 维度 | 评分 | 说明 |
|---|---|---|
| 范围匹配（scope）| A | 10 任务全部对应 02-design-doc §1-§11，无溢出 |
| 安全 | A- | API 走 JWT、文件上传走受控 endpoint，无明文密钥 |
| 编码规范 | A | Python 用 dataclass + type hint，TS 用 React hooks + 类型 |
| 前端质量 | A | 6 页面统一走 ConsoleShell，无裸 UI |
| 反馈循环 | A | 5 道门禁脚本就位，制品全在 AIOS-003/ 下 |
| 测试覆盖 | A- | 19/19 单测通过；E2E 5 spec 写完待 verify 跑 |

---

## 2. Scope 溢出检查（0 命中）

把 04-code-changes.md 7 个变更区域逐一与 01-requirement-doc §3 / 02-design-doc §10 对齐：

| 区域 | 设计对应 | 需求对应 | 是否溢出 |
|---|---|---|---|
| apps/ingest 新增 | §3.2 4 ingester | §3.1 多源摄取 | 否 |
| apps/ontology 新增 | §2 schema + §3 抽取 | §3.2 本体图 | 否 |
| apps/api 3 路由 | §7 API 设计 | §3.1-§3.3 | 否 |
| migration 0004 | §6 数据库 | §3.3.1 多源 | 否（5 → 3 表合并，已在 tasks 说明）|
| flow_engine llm_judge | §9 LLM 增强 | §3.4 LLM 接入 | 否 |
| 前端 6 页面 + 3 菜单 | §8 前端 | §4 UI | 否 |
| docker-compose + ollama | §1.1 新增服务 | §3.1 部署 | 否 |

**0 项超出需求范围。**

---

## 3. 安全审查（0 阻塞 / 1 建议）

| 项 | 检查 | 状态 |
|---|---|---|
| 鉴权 | 所有 V2 新增 API 走 `CurrentUser` 依赖（ingest/ontology/llm 全 JWT 保护） | ✅ |
| SQL 注入 | ingest/llm 路由无原生 SQL，全走 ORM | ✅ |
| 文件上传 | multipart 走 FastAPI UploadFile + size 限制（API 层） | ✅ |
| LLM prompt injection | 业务上下文当文本拼 prompt，不解析指令 | ⚠️ 建议 V3 加 system prompt 隔离 |
| 凭证加密 | LLM URL / Neo4j password 走 .env | ✅ |
| 审计 | ingest upload 写 audit（write_audit 调用） | ✅ |

**0 阻塞，1 建议（V3 处理）：prompt injection 风险。**

---

## 4. 编码规范（Python）

| 项 | 检查 | 状态 |
|---|---|---|
| type hint | dataclass + list[dict] / dict[str, Any] | ✅ |
| async/await | 统一使用，无裸 blocking | ✅ |
| 错误处理 | `except Exception as e:  # noqa: BLE001` 在已知路径 | ✅ |
| 日志 | 用 stdlib logging 而非 print | ✅ |
| 单测 | 每模块 tests/ 目录 | ✅ |
| 命名 | snake_case 一致 | ✅ |

**无违规。**

---

## 5. 编码规范（TypeScript / React）

| 项 | 检查 | 状态 |
|---|---|---|
| 'use client' | 交互页面正确标注 | ✅ |
| hooks 顺序 | useState / useQuery 都在顶部 | ✅ |
| 类型 | interface / type 全用，未用 any（llm_judge.tsx 的 Promise<any> 仅一处，导出数据时） | ⚠️ 建议 |
| API 调用 | 走 `@/lib/api` axios 实例，401 自动跳登录 | ✅ |
| Layout | 6 页面都包 ConsoleShell | ✅ |
| 错误处理 | `App.useApp().message` 统一错误提示 | ✅ |

**0 阻塞，1 建议（typescript any 收紧）。**

---

## 6. 前端质量（自检）

- 菜单增加 3 项，与 V1 现有菜单视觉一致
- 状态机清晰：ingest 上传 → 跳任务详情 → 3s 轮询 → succeeded 提示去 ontology
- ontology 页面 10 类型卡 + 表格 + iframe + 跳详情
- llm-usage 4 provider 按钮可点（Compact 控件）+ 4 统计卡 + 分组表
- 404 处理（ingest/jobs/[id] 不存在时显示 Result status=404）
- 响应式 Col xs/md/lg

**无质量问题。**

---

## 7. 反馈循环（5 道门禁核对）

| 门禁 | 状态 |
|---|---|
| gate-baseline.sh | 通用（V0/V1 已 baseline）|
| gate-coverage.sh | coverage-python 已自动 find apps/api + apps/ingest + apps/ontology |
| gate-lint.sh | Python ruff + TS eslint |
| gate-deploy-test.sh | V2 加 ingest / ontology / ollama 三处 health check |
| gate-e2e.sh | 通用 10 spec（5 V1 + 5 V2）|

**5 道门禁脚本就位，5 spec 写完。**

---

## 8. 阻塞项

**0 项。**

---

## 9. 建议项（不阻断，记入 V3 backlog）

1. **SEC-V3-01**：LLM prompt 加 system 角色隔离，user 上下文只占 data 段
2. **TS-V3-01**：llm-usage/page.tsx 的 Form list value 用强类型
3. **OPS-V3-01**：生产部署加 reverse proxy 鉴权 Neo4j 浏览器
4. **OPS-V3-02**：Ollama 启动后自动 `ollama pull qwen2.5:7b`（docker entrypoint）

---

## 10. review 棒结论

- **PASS**
- 进入 verify 棒：重跑 5 道门禁 + E2E + 写 07-delivery-report.md
