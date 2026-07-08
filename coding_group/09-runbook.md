# 故障预案：跑挂了怎么办

> 这套方案跑久了必然撞墙。这一章按「跑挂了怎么办」组织，按问题类型排好。

---

## §1 Agent 完全不响应

### 现象
- 输入完一句话，主控 Agent 没反应
- 日志显示 Agent 仍在跑，但已经 30 分钟没动
- 反复发消息也不接

### 排查
```bash
# 1. 看 .orchestrator-state.json 当前状态
cat .orchestrator-state.json

# 2. 看最近一次门禁跑的时间
cat .gates-state.json | jq .updated_at

# 3. 看是不是有阻塞项堆积
ls -la kb/artifacts/<req-id>/blockers/

# 4. 看 IDE / CLI 是不是卡在 spawn 子 Agent
ps aux | grep -i "claude\|cursor" | head
```

### 修复

1. **如果是 spawn 卡住**：关掉 IDE 重启——参照文章里 Team Mode 撞墙的故事
2. **如果是阻塞项堆积**：人工读阻塞项，自己决策要不要打回哪一棒
3. **如果是 grep / find 没结果**：说明制品没落盘，强制 orchestrator 重新跑这一棒

---

## §2 门禁挂了

### 子类 A：覆盖率（软门禁）

| 现象 | 优先排查 |
|---|---|
| core < 80% | 是不是新加的功能没写单测？回 developer Agent 补 |
| 整体 < 60% | 是改了 utils / lib？补 |
| 突然掉了几个百分点 | 上 git log 看改了什么，加单测 |

### 子类 B：lint 硬门禁

| 失败类型 | 修法 |
|---|---|
| `lint:eslint-failed` | 让 developer 修；不允许"我故意关掉这条规则" |
| `lint:secret-in-code` | **立即**回滚 commit、改 .env 注入、commit amend |
| `lint:sql-injection-risk` | 用 ORM 或参数化查询重写那一行 |

### 子类 C：deploy-test 硬门禁

| 现象 | 排查 |
|---|---|
| 部署超时 | 看部署平台 dashboard；可能是 quota / cold start |
| 健康检查失败 | curl 主页看返回的是什么 |
| 200 但页面空白 | 看部署日志 + 浏览器 dev tools console |

### 子类 D：E2E 硬门禁

| 现象 | 排查 |
|---|---|
| 大面积失败 | staging 部署挂了；回头看 deploy-test |
| 一两个失败 | 看 .gate-output/playwright/ 里的 trace 和截图 |
| 偶发 | 加 retry + 锁环境变量（time / random seed） |

### 子类 E：基线对比 delta

```
"新失败: src/foo.ts: 0.45 < 0.6"
```

意味着**基线里这条失败**还没记录。两种选择：
1. **接受为已知缺陷** → 把这条加进 `kb/known-issues.md` + 更新基线（人工）
2. **修** → 打回 developer

> 基线更新**必须人工**，不能 AI 决定。

---

## §3 制品缺失 / 乱套

### 子类 A：04-code-changes.md 没写

```
某次开发棒跑完，但 kb/artifacts/<req-id>/04-code-changes.md 不存在
```

这是 developer Agent **严重违规**——必打回：补写 04-code-changes.md + 重跑门禁。

### 子类 B：制品目录堆了一堆没 req-id 的文件

这是 orchestrator 没初始化好就跑棒了。修复：

```bash
# 把散落制品归档到临时的 req-id 下
REQ_ID="REQ-XXX-recovery"
mkdir -p kb/artifacts/$REQ_ID
mv <散落文件> kb/artifacts/$REQ_ID/
# 然后写一份恢复说明
cat > kb/artifacts/$REQ_ID/recovery.md <<'EOF'
## 制品散落恢复记录
- 时间: YYYY-MM-DD
- 触发: 散落文件 X、Y、Z 被归档
- 原因: orchestrator 未初始化就走棒
- 处置: 视为初始化中，从当前阶段继续
EOF
```

### 子类 C：阻塞项文档不规范

如果阻塞项没按 `feedback-loop-rules/SKILL.md` §6 写（位置 + 现状 + 期望 + 复核都缺）→ 打回 reviewer 重写。

---

## §4 PR / 部署卡住

### 子类 A：PR 创建失败

- 鉴权失败 → 检查 `GITHUB_TOKEN` 是否还有效、scope 是否够
- 分支冲突 → developer 拉最新 main 重做
- Reviewer 没推荐上 → 检查 CODEOWNERS

### 子类 B：staging 部署健康检查失败

按 §2 C 处理

### 子类 C：生产部署触发后失败

**回滚 SOP**：

```bash
./scripts/gates/gate-deploy-test.sh --capture  # 拿当前 staging 状态
# 触发回滚
gh workflow run rollback.yml --input env=production --input to_version=vX.Y.Z
# 验证
curl -sf https://your-product.com/health
# 发通知
notify_feishu <webhook> "🚨 生产事故回滚：vX.Y.Z → vX.Y.Z-1"
# 写事故复盘
mkdir -p kb/incidents
$EDITOR kb/incidents/$(date +%Y%m%d)-xxx.md
```

---

## §5 Skill 没被加载 / 加载错了

### 现象

- Agent 产出的 PRD 没有 5 维评分
- 审查时不提范围溢出
- 设计文档漏字段

### 排查

| 层级 | 检查 |
|---|---|
| 文件位置 | `kb/skills/<name>/SKILL.md` 路径正确吗？ |
| YAML frontmatter | 有 `name` + `description` 吗？ |
| Agent prompt | `<仓库根>/AGENTS.md` 和 master prompt 第 0 节里**显式提到**要加载这个 Skill 吗？ |
| Skill 本身 | 试过在新会话只加载这一个 Skill？看会不会用 |

### 修复

在 Agent prompt 里显式「加载 Skill X」写明，**不要写「按需要加载」**——AI 不知道什么时候是"需要"。

---

## §6 4 个 Agent 互相干扰

### 现象

- Developer 偷偷改设计文档
- Reviewer 偷偷改代码
- 需求 Agent 写技术方案

### 几乎唯一原因

> **下游 Agent 直接修改了上游产物**

### 修复

1. 看 `kb/artifacts/<req-id>/` 哪些文件被改了（git log）
2. 把这些偏离写进 `blockers/` 由 orchestrator 处理
3. 把 prompt 强化：「不允许改上游产物。改 = 写阻塞项。」

---

## §7 "AI 觉得做完了"但脚本说没过

### 现象

- AI 汇报「开发完成」
- 但 5 道门禁有挂
- 制品里也写了"完成"

### 修复

```
门禁通过 = 完成
门禁挂 = 未完成，不存在中间态
```

在 prompt 里强化：「你写的所有"完成"声明，以最近一份 .gates-state.json 为准。如果有任一硬门禁 FAIL，你没完成。」

---

## §8 飞书 / 部署 webhook 失败

### 排查

```bash
curl -X POST <webhook_url> -d '{"msg_type":"text","content":{"text":"测试"}}'
```

### 修复

- webhook URL 失效（不常见，但有）→ 去群里更新机器人
- 网络问题 → 加 retry、软降级（不阻断交付）

---

## §9 体系长大了，新需求跑不出「完成」

> 3 个月后你发现:新需求几乎每一棒都被打回，5 道门禁又过不去

### 这种情况下要先诊断是「三类问题」中的哪一类

| 问题 | 表现 | 修法 |
|---|---|---|
| **Skill 缺失** | Agent 不知道怎么做 → 反复试错 | 写新 Skill / 改老 Skill |
| **门禁过严** | 看起来挂但其实是「非红线」 | 改硬 → 软 / 调阈值 |
| **流程不准** | 制品齐了但审不过 | 调整 SOP / 加人工关卡 |

不能**只看症状修症状**。先看「4 块拼图缺哪块」（[01-overview](01-overview.md)）：

```
缺约束与流程 → 加 Skill
缺反馈 → 加强门禁
缺知识库 → 补 kb/
缺进化 → 写 changelog
```

---

## §10 找不到原因的时候

> 这是程序员最常见的"我也不知道为什么"的兜底 SOP。

1. 写一份「最小复现」：把流程简化到「一句需求 + 一个空仓库」，看最小集能不能跑通
2. 如果最小集跑通 → 是当前仓库的状态出了问题，对比 working commit
3. 如果最小集也跑不通 → 升级向 Mavis 报告（路径 A 用我）

---

## 经验沉淀（每解决一个事故就写一条）

每个事故 → 一份 `kb/incidents/YYYY-MM-DD-<short-title>.md`：

```markdown
# YYYY-MM-DD <一句话>

## 现象
- ...

## 触发原因
- ...

## 影响面
- ...

## 修复
- ...

## 治本（怎么避免再发生）
- （改哪个 Skill、哪个门禁、哪个 prompt）
- （commit: fix(<scope>): <desc>）
```

写完同步到 `kb/changelog.md` 一行。
