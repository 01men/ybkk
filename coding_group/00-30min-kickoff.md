# 30 分钟启动清单

> 不看任何理论，先把最小可用状态跑起来。读完这份，按 7 步走，30 分钟内你应该能第一次体验"说一句话 → 团队跑完"的闭环。

---

## 第 1 步：确认你有什么（第 5 分钟）

下面账号 / 订阅 / 工具，**至少需要前三项**才能继续；后三项推荐但不是硬卡点。

| 必须 | 你需要 |
|---|---|
| ✅ Claude / OpenAI / 国产大模型 的任意一个高级订阅 | 你的 AI 跑团队的算力来源。Claude Pro / Max 或者 GPT Plus / Team 都可以 |
| ✅ 一个空 GitHub 仓库（私有的也行） | 代码和制品的"家"。不懂创建就在 GitHub 右上角点 `+` → `New repository` |
| ✅ 一个终端（Mac 的 Terminal / Windows 的 PowerShell） | 跑门禁脚本用 |
| 🟡 一个部署平台账号（Vercel / Cloudflare Pages / 阿里云 / 腾讯云任一） | 第 9 阶段自动部署用。Vercel 最省事 |
| 🟡 一个对象存储 / 数据库账号（按业务可选） | 比如腾讯云 COS、阿里云 OSS、Supabase、Neon |
| 🟡 一个通知通道（飞书 / 企微 / Slack / 邮件） | 交付收尾时提醒你 |

如果你想用 Mavis（就是我）直接帮你跑全套，把第 3 步那个**目标**发给我就行——**我手下的 Agent 团队包含在跟你的对话里**，你连第 2-6 步都不用做。🟢 这一步是路径 A。

---

## 第 2 步：建一个空仓库（第 5 分钟）

打开 GitHub（或者你已经在用的 Gitee），新建一个仓库：
- 名字：`your-product`（你自己起）
- 是否私有：**强烈建议选 Private**
- 是否加 README：**不要勾**（我们后面有一套自己的模板）

然后在本地找一个舒服的目录，把仓库 clone 下来：

```bash
git clone https://github.com/<your-name>/<your-product>.git
cd <your-product>
```

---

## 第 3 步：放进脚手架（第 10 分钟）

把本方案 `output/` 目录下的所有文件原样复制到你的仓库根目录：

```bash
# 在你的仓库根目录执行（路径替换成实际位置）
cp -r /path/to/this/output/* .
```

> 这一步完成之后，你应该能在仓库根目录看到 `README.md`、`01-overview.md`、一个 `assets/` 目录。

打开仓库根的 `AGENTS.md`（自动生成在第 3.5 步），**把所有 `<...>` 占位符替换成你的真实信息**：

- `<YOUR_NAME>` → 你的名字
- `<PRODUCT_NAME>` → 产品名
- `<STACK>` → 技术栈（Vercel + Next.js / Cloudflare + Hono / 阿里云 + Python Flask 都行）
- `<REPO_URL>` → 仓库 URL
- `<DEPLOY_HOOK>` → 部署平台的 webhook URL（在 Vercel 的 Settings → Git → Deploy Hook 找）

---

## 第 3.5 步：生成 AGENTS.md

如果 `output/` 里有 `AGENTS.md` 直接复制就好；如果没有，按 `03-repository-bootstrap.md` 里的模板生成。

这一步是给整个 Agent 团队的"家法"——所有 AI 进入这个仓库，第一件事就是读它。

---

## 第 4 步：注册 5 个 Agent（第 5 分钟）

如果你用 Claude Code，进入 `Settings → Custom Agents`，新建以下 4 个 sub-agent（每个复制 `assets/prompts/` 下对应的 prompt 全文）：

1. `orchestrator`（总控） — 用 `assets/prompts/orchestrator.md`
2. `requirements-analyst`（需求分析）— 用 `assets/prompts/agent-requirements.md`
3. `solution-architect`（方案设计）— 用 `assets/prompts/agent-design.md`
4. `developer`（开发）— 用 `assets/prompts/agent-develop.md`
5. `reviewer`（审查）— 用 `assets/prompts/agent-reviewer.md`

名字必须一字不差，因为流程里靠名字唤起。

---

## 第 5 步：塞进 11 个 Skill（第 3 分钟）

把 `assets/skills/` 下 11 个 `SKILL.md` 文件原样放进你的仓库：

```
<your-product>/
└── kb/
    └── skills/
        ├── prd-quality-check/SKILL.md
        ├── impact-radius-analysis/SKILL.md
        ├── design-doc-template/SKILL.md
        ├── coding-conventions/SKILL.md
        ├── testing-specs/SKILL.md
        ├── deployment-checklist/SKILL.md
        ├── scope-overflow-check/SKILL.md
        ├── security-rules/SKILL.md
        ├── frontend-quality/SKILL.md
        ├── prd-template/SKILL.md
        └── feedback-loop-rules/SKILL.md
```

> 注意：Claude Code 的 Skill 是按 `kb/skills/<skill-name>/SKILL.md` 这种目录结构加载的，**目录名就是 Skill 名**。

---

## 第 6 步：跑门禁脚本（第 2 分钟）

把 `assets/scripts/` 下的 5 个脚本放进仓库的 `scripts/gates/` 目录：

```bash
mkdir -p scripts/gates
cp assets/scripts/* scripts/gates/
chmod +x scripts/gates/*.sh
```

第一次跑一次基线快照（让开发 Agent 知道"改之前的世界长这样"）：

```bash
./scripts/gates/gate-baseline.sh --snapshot
```

这会生成一份 `kb/gates/baseline.json`，里面是当前所有门禁的状态。后面每次跑门禁会用它做对比。

---

## 第 7 步：说你的第一个目标（第 0 分钟）

回到你的 AI 客户端（或者跟我对话），说一句尽量清楚的话，**用下面这个模板**：

```
我要做一个 <什么产品>，核心场景是 <谁在什么情况下做什么>。
本期先做 <具体要落到的最小功能>。
成功标准是 <可观察、可验证的事，比如「能在 / 页面输入网址看到截图」>。
技术栈：<Next.js 15 + Tailwind + Supabase + Vercel> 或其他你听过的都行。
参考产品：<想抄功能的网站 / App 名字>。
```

按下回车。orchestrator 会按 `06-workflow.md` 的 9 阶段**接力跑**：
- 你大概会被问 2~3 次"确认继续 / 改这里"；
- 中间一些技术决策会推给你看；
- 跑完会给你一个可访问的 URL + git commit + 制品清单。

如果中途卡住（很久没反应 / 一再问你 / 一直打回同一段），看 `09-runbook.md`。

---

## 跑完之后

- 让脚本里的 5 道门禁**每次自动跑**。在仓库根目录 `.git/hooks/pre-commit` 里挂一下门禁脚本，开发 Agent 提交前会自动过。
- 升级到路径 B：等你跑通 3~5 个真实需求，**把流程总结发给我**，我帮你把这套独立化到你的 Claude Code 里。

---

## 你现在卡哪了？

> 概率最高的 3 个卡点：
>
> 1. **5 步里不知道注册 sub-agent 的具体位置** → 打开 `04-agents.md`，里面有截图级说明。
> 2. **第 3 步说半天 AI 还是没搞清楚你想要啥** → 打开 `assets/skills/prd-quality-check/SKILL.md`，把那个 5 维评分表自己先填一遍，再发给 AI。
> 3. **门禁跑挂了** → 90% 是覆盖率和 E2E 没达到，开 `09-runbook.md` 的「门禁挂了怎么办」。
