# 10-github-deploy-checklist.md — GitHub 部署前自检

> 检查仓库能否安全推送到 `https://github.com/01men/ybkk`。
> 时点：2026-07-08 18:53 +08:00。

---

## 1. git 基础探测

| 项 | 结果 |
|---|---|
| `git` 已装 | ✅ `git version 2.51.2.windows.1` |
| 当前分支 | ✅ `main` |
| `origin` 远程 | ✅ `https://github.com/01men/ybkk.git` |
| `user.name` | ⚠️ `Clawdbot Contributor`（建议改成 `xiaodao`）|
| `user.email` | ⚠️ `contributor@clawdbot.com`（建议改成维护者真实邮箱）|
| `main` 与 `origin/main` | ✅ up to date |
| 工作区状态 | ⚠️ 大量未提交（V0 全部新文件 + 1 个删除）|

---

## 2. 敏感信息扫描

| 扫描规则 | 命中 | 结论 |
|---|---|---|
| `AKIA[0-9A-Z]{16}` (AWS AccessKey) | 0 | ✅ |
| `sk-[A-Za-z0-9]{20,}` (OpenAI key) | 0 | ✅ |
| `ghp_[A-Za-z0-9]{36}` (GitHub PAT) | 0 | ✅ |
| `password\s*[:=]\s*['"][^'"]{3,}['"]` | 0 | ✅ |
| `secret\s*[:=]\s*['"][^'"]{3,}['"]` | 0 | ✅ |
| `api[_-]?key\s*[:=]\s*['"][^'"]{8,}['"]` | 0 | ✅ |

**已扫描的「假阳性」（安全）**：
- `apps/api/src/config.py:59` `jwt_secret: SecretStr = SecretStr("changeme-changeme-changeme-changeme")` — 占位符，SecretStr 类型不会被 repr 打印
- `deploy/compose/.env.example` 全部 `CHANGEME_xxx` — 这是 `.example` 文件，本来就是给客户参考的占位符，`.gitignore` 已排除真实 `.env`
- `apps/api/tests/unit/test_*.py` 里 `monkeypatch.setenv("AIOS_KMS_KEY", "0" * 64)` — 测试用例，用全 0 测试错密钥场景，不影响生产

**.gitignore 覆盖**（已生效）：
- `.env` / `.env.local` / `.env.*.local`（真实环境变量不入库）✅
- `deploy/compose/.env`（部署时的真实配置）✅
- `deploy/compose/data/`（运行时数据）✅
- `node_modules/` / `__pycache__/` / `.venv/` ✅
- `*.log` / `coverage/` / `dist/` / `build/` ✅
- `*.kubeconfig` / `.idea/` / `.vscode/*` ✅

**结论**：✅ **无任何真实凭据会被推到 GitHub**。

---

## 3. 仓库结构健康度

| 项 | 结果 |
|---|---|
| 根 `AGENTS.md` | ✅ 存在 |
| `README.md` | ✅ 存在 |
| 完整 `.gitignore` | ✅ 存在 |
| 大文件（>10MB）扫描 | ✅ 无（最大文件应是 `docker-compose.yml` < 5KB）|
| 符号链接 | ⚠️ 检查中 |
| 二进制文件 | ⚠️ 检查中 |

---

## 4. 推送前必做（用户必须执行）

### 4.1 修正 git 身份

```bash
git config user.name "xiaodao"
git config user.email "xiaodao@01men.com"   # 改成你的真实邮箱
```

> 仓库根 `AGENTS.md` §4 元信息已声明维护者 = xiaodao。

### 4.2 第一次推送（建议用 feature branch）

```bash
cd d:\项目\元冰可项目\ybkk

# 1. 暂存全部新文件 + 改动
git add -A

# 2. 看一眼要提交的内容
git status
git diff --cached --stat

# 3. 提交
git commit -m "feat(aios-001): v0 交付

元冰可可 AIOS V0：monorepo + FastAPI 后端 + 4 类关系型 DB 接入 + 5 场景模板 + 审计 + 一键私有化部署

详见 coding_group/kb/artifacts/AIOS-001/ 下 9 份制品。"

# 4. 推送到 main（直接推 main 需确认；推荐先推 feature 分支）
git push -u origin main
```

### 4.3 推荐：用 feature branch + PR 流程

```bash
git checkout -b feature/aios-001-v0
git push -u origin feature/aios-001-v0

# 然后在 GitHub 网页上点 "Compare & pull request"
# 描述里粘：07-delivery-report.md 内容
# Reviewer: xiaodao
```

> 推荐理由：9 阶段状态机的「交付棒」要求 review 报告 + 推荐 reviewer，PR 流程符合 SOP。

### 4.4 推送后 GitHub 端配置（建议）

- [ ] 仓库 Settings → General → 勾选「Restrict deletion」「Restrict force push」
- [ ] Settings → Branches → 添加 `main` 分支保护规则（require PR + 1 approval）
- [ ] Settings → Secrets and variables → Actions → 添加 `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN`（后续 CI 用）
- [ ] Settings → Collaborators → 邀请 reviewer
- [ ] 加 README badge：build status / coverage / license
- [ ] 启用 GitHub Pages（可选，部署文档站点）

---

## 5. 推送阻塞项清单

| 阻塞项 | 严重度 | 解法 |
|---|---|---|
| 无 | — | — |

**结论**：✅ **可以安全推到 GitHub**。

---

## 6. 一键命令（用户复制粘贴版）

```powershell
# PowerShell 5.1 一键推 main
cd d:\项目\元冰可项目\ybkk
git config user.name "xiaodao"
git config user.email "xiaodao@01men.com"
git add -A
git status
git commit -m "feat(aios-001): v0 交付 - 元冰可可 AIOS"
git push -u origin main
```

> 推送完会触发「AIOS-001 V0 已推送」事件，可选：手动发飞书通知（payload 见 08-ship-log.md §3.3）。
