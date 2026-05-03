# MCP ssh-manager 连接问题（待 user 复盘）

## 现象
2026-04-30 cascade session 中，`mcp0_ssh_execute server=hk-et` 多次返回：
```
Failed to connect to hk-et: Failed to connect to ali-et: Connection lost before handshake
```
连续 4-5 次 mcp tool call 全部失败。

## 同时同条件下直接 ssh 仍然能用
`cmd /c "ssh root@64.90.13.65 ..."` 同一时刻全部正常工作（多次成功），命令、网络、凭证都没问题。

## 推测
- MCP `hk-et` 在 ssh-manager config 里被定义为 **走 ProxyJump 经过 `ali-et` (60.205.205.99)**。
- 我直接 ssh 用的是 windows 上 `~/.ssh/config` 配置，里面 hk-et 的连接路径不一样（更可能是直连 64.90.13.65 公网，**不走 ali-et 跳板**）。
- 所以是 **`ali-et` (阿里云中转节点) 跟 ssh-manager mcp server 之间的链路**有抖动 / handshake 失败，跟 64 自身无关。
- 用户切换网络后第二次仍未恢复（user cancel 了 mcp 测试）。

## 影响
- mcp 的 ssh tool 在这个 session 内失效，cascade fall back 到 PowerShell `cmd /c ssh ...` 直连 64。
- 直连 ssh 64 工作正常 ⇒ 任务可继续推进。

## 待复盘问题
1. mcp 的 hk-et 是不是必须走 ali-et 跳板？能否改为直连 `64.90.13.65:22`（用户配的 ~/.ssh 已经能直连）？
2. ali-et 60.205.205.99 是否最近有抖动 / IP 改了 / EasyTier mesh 路径变了？
3. ssh-manager mcp 的「Failed to connect ... Connection lost before handshake」是否有更详细 log（mcp server 那侧）？
4. 是否可以让 mcp 在 jump host 不可达时自动 fall back 直连？

## 建议
- 临时：cascade 在这种情况下回退 `cmd /c ssh root@<host> ...` 直连，不影响进度。
- 长期：在 mcp config 里给 hk-et 定义两个连接 profile（with-jump / direct），自动 fail-over。
