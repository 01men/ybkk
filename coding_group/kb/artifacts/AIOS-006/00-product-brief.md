# 00-product-brief.md — V5 mac 实跑门禁（AIOS-006）

> 时点：2026-07-09 15:00 ~ 15:25 +08:00
> 状态：**已取消**

---

## 目标

用户要求在 mac 主机 `ssh xiaodaoqin@mdzx.fun`（密码 201314）实跑 5 道门禁。

## 探活结果

| 步骤 | 结果 |
|---|---|
| SSH 连接 | ✅ plink + ed25519 fingerprint 验证通过 |
| mac OS | 15.7.1 ARM64 (Darwin 24.6.0) |
| python3 | ✅ `/usr/bin/python3` |
| git | ✅ `/usr/bin/git` |
| uv | ✅ 现装 0.11.28 (curl 安装到 `~/.local/bin/uv`) |
| node | ✅ 现装 v20.19.0 (curl 二进制分发到 `~/.local/share/node/`) |
| pnpm | ✅ 现装 9.15.9 (npm i -g) |
| docker | ⚠️ Docker Desktop.app 装着，但 daemon socket 未建立；非交互 SSH 无法完成 GUI 授权 |

## 阻塞点

Docker Desktop for Mac 第一次启动需要用户在 GUI 上同意服务条款 / 输入系统密码授权 — SSH 非交互做不到。

## 结论

5 道门禁中的 **baseline / coverage / lint** 在 mac 上可跑（用 uv + pytest + ruff），但 **deploy-test + e2e** 必须 docker，所以全套门禁在该 mac 上无法完整通过。

用户主动取消：「算了，不在这台mac部署了」。

## 后续路径（未推进）

- (A) Linux 8C16G 客户机器实跑全套门禁
- (B) mac 上手动 GUI 启 Docker Desktop 后再跑（需要用户本机操作）
- (C) 直接跳过 mac 验证，留交付文档让客户跑
- (D) 其他路径

## 元冰可可 AIOS 仓库状态

- V0~V4 五棒已 ship，全部 commit push main 成功
- 5 道门禁在沙箱环境受限部分跑过（AST/YAML/JSON），客户实跑路径仍 OPEN