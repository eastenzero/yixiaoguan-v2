# 阶段 0 · 腾讯云安全组手工放行(无法脚本化)

## 为什么手工

TX-NEW (`82.156.129.75`) 的安全组由腾讯云控制台管理(`YJ-FIREWALL-INPUT` chain),
系统内 `ufw` / `iptables` **不起决定作用**,必须在云控制台加入站规则。

## 操作步骤

1. 登录 https://console.cloud.tencent.com/
2. 找到轻量应用服务器(或 CVM,按你这台机型) `VM-0-17-ubuntu` / 公网 IP `82.156.129.75`
3. 进入该实例 → **防火墙 / 安全组** 选项卡
4. 添加/确认以下**入站**规则:

| 类型 | 协议 | 端口 | 源 | 说明 |
|------|------|------|----|----|
| 已有 | TCP | 22 | 0.0.0.0/0 | SSH(请改为你的家/办公 IP 段更安全) |
| **新增** | TCP | **80** | 0.0.0.0/0 | nginx HTTP(R11 内测) |
| **新增** | TCP | **81** | 0.0.0.0/0 | nginx HTTP 教师端 |
| 延迟 | TCP | 443 | 0.0.0.0/0 | 等阶段 99 域名切换时再开 |

5. **不要** 放行 5432 / 6379 / 8000 / 8100 — 它们都在 127.0.0.1 内部

## 验证

本地 PowerShell:

```powershell
Test-NetConnection 82.156.129.75 -Port 80
Test-NetConnection 82.156.129.75 -Port 81
```

应该 `TcpTestSucceeded : True`(即使 nginx 还没起,也应该是 "Connection refused" 而不是 "Timed out"——后者说明安全组没放)。

## 完成后

回来跟 Cascade 说"安全组已放 80/81",然后跑阶段 A。
