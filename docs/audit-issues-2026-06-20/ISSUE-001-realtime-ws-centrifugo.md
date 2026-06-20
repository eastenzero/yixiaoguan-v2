# ISSUE-001 实时通信链路不可用

## 现象

学生端和教师端可以通过 HTTP/SSE 完成部分流程，但 H5 浏览器测试中实时消息链路不可用。教师端和学生端之间的实时响应依赖 WebSocket/Centrifugo，当前配置会导致订阅或连接失败。

## 证据

- 浏览器控制台多次出现 `wss://teacher.xiaoguan.site/ws?token=...` 相关错误。
- 线上 Nginx 对 `/ws?token=...` 返回 301，因为配置看起来只匹配 `/ws/`。
- 浏览器 WebSocket 不会像普通 HTTP 请求一样跟随 301。
- Centrifugo subscribe proxy 配置中的 `X-Auth` 仍像占位值，和 gateway 使用的 `centrifugo_proxy_secret` 不匹配。

## 影响

- 教师端可能不能实时收到学生呼叫、状态变化或新消息。
- 学生端在教师接入后可能不能实时看到教师回复。
- 工单处理看起来“能点进去”，但真正内测时会出现延迟、需要刷新、状态不同步。

## 涉及区域

- Nginx 线上配置
- `deploy/nginx-centrifugo.conf`
- `deploy/centrifugo-config.json`
- `services/gateway/app/routers/ws.py`
- `services/gateway/app/services/centrifugo_client.py`
- 学生端/教师端 WebSocket 管理模块

## 建议修复方向

- 统一前端 WebSocket 地址为后端真实匹配路径，避免 `/ws` 和 `/ws/` 分裂。
- 修正 Nginx WebSocket location，确保带 query 的 `/ws?token=...` 不被 301。
- 对齐 Centrifugo proxy secret/header。
- 做双端浏览器回归：学生呼叫、教师接单、教师回复、学生实时收到、状态变更。

