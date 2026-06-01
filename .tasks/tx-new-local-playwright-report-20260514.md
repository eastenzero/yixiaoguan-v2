# tx-new 与本地/165-dev Playwright 验证报告（2026-05-14）

## 1. 验证目标

本次验证目标：

1. 用 Playwright CLI / 现有 Playwright 脚本实际打开页面，不只看代码和 git diff。
2. 对比 `tx-new` 线上环境和本地当前代码 + 165-dev 后端的功能状态。
3. 判断本地已修复的内容是否真实可用，以及哪些仍未部署到 `tx-new`。

## 2. 验证环境

### tx-new 线上

- 学生端：`https://yxg.xiaoguan.site/#/`
- 教师端：`https://teacher.xiaoguan.site/#/`
- 后端：同域 `/api/*`
- 当前服务器仓库：`master @ 6e5f434`
- 当前静态资源：仍是旧 icon。

### 本地前端 + 165-dev 后端

- 学生端本地 H5：`http://localhost:3001/#/`
- 教师端本地 H5：`http://localhost:5301/#/`
- 后端 API：`http://192.168.100.165:8100`
- Centrifugo tunnel：`127.0.0.1:18000 -> 192.168.100.165:8000`
- 本地代码分支：`fix/realtime-user-channel-push @ afd2f83` + 当前工作区未提交修复。

## 3. 复用脚本与命令

### 已复用脚本

- `.tmp/demo-video/test-realtime-v7.mjs`
  - 双端 UI 实时聊天闭环。
  - 教师 UI 发消息 -> 学生 UI 实时出现。
  - 学生 UI 发消息 -> 教师 UI 实时出现。
  - 再来一轮教师 -> 学生，验证持续可用。

- `.tmp/demo-video/verify-ui-bugs.mjs`
  - Material Symbols FOUT/ligature 闪烁采样验证。
  - 双端聊天滚动到底。
  - 新消息动效 class 验证。

- `services/gateway/tests/test_knowledge_entries_list.py`
  - 本地知识条目列表 API 单测。

- `services/gateway/tests/test_notify_conversation_parties.py`
  - 本地实时推送 user/channel 逻辑单测。

### 本次新增临时验证脚本

- `.tmp/verify-tx-local-api.mjs`
  - 对 `tx-new` 和 `165-dev` 做同一组 API 对比。
  - 检查 `analytics`、`conversations`、`knowledge entries` 等修复点。

## 4. tx-new 线上验证结果

### 4.1 学生端免登录

结果：**PASS**。

Playwright CLI 实际打开：

- 初始 URL：`https://yxg.xiaoguan.site/#/`
- 约 3 秒后自动跳转：`https://yxg.xiaoguan.site/#/pages/home/index`
- 页面显示：`下午好，pilot-*`
- `localStorage` 有：
  - `v2-device-id`
  - `v2-token`
  - `v2-user-info`

网络请求：

- `POST /api/auth/pilot-anonymous` -> 200
- `GET /api/auth/me` -> 200
- `GET /api/conversations/unread-summary` -> 200
- `GET /api/conversations?page=1&size=3` -> 200
- `POST /api/track` -> 200

判断：

- 线上学生端免登录是正常工作的。
- 这和服务器 `.env` 里的 `pilot_mode_enabled=true` 一致。

### 4.2 学生端 AI 问答

结果：**PASS**。

Playwright CLI 实际操作：

1. 打开学生端。
2. 点击首页 `立即开启`。
3. 进入 `#/pages/chat/index`。
4. 输入：`校园卡在哪里办理？`
5. 点击发送。

页面结果：

- 用户消息显示成功。
- AI 回复显示成功。
- 回复内容包含：
  - 新生入学报到时统一领取实体校园卡。
  - 补办/虚拟校园卡方式。
  - 参考资料区域。

网络请求：

- `POST /api/conversations` -> 201
- `POST /api/chat/send` -> 200
- `POST /api/track` -> 200

控制台：

- 0 errors
- 0 warnings

判断：

- tx-new 当前学生端核心体验（免登录 + AI 问答）是可用的。

### 4.3 教师端登录与工作台

结果：**页面可用，但存在实时连接报错**。

Playwright CLI 实际操作：

1. 打开 `https://teacher.xiaoguan.site/#/`。
2. 输入账号：`anjing`
3. 输入密码：`Anjing@yxg2026`
4. 点击 `uni-button.login-btn`。
5. 成功进入 `#/pages/dashboard/index`。

页面结果：

- 标题：`工作台`
- 展示：`下午好，安静 👋`
- 工作台、学生提问、知识库、我的 tab 可见。
- 待处理提问列表可加载。

接口结果：

- `POST /api/auth/login` -> 200
- `GET /api/auth/me` -> 200
- `GET /api/conversations?page=1&size=1` -> 200
- `GET /api/conversations?page=1&size=5&status=pending_teacher` -> 200

控制台问题：

- 线上教师端出现旧 WebSocket 报错：
  - `wss://teacher.xiaoguan.site/ws?token=...`
  - handshake failed: `Unexpected response code: 301`

服务器侧探测：

- `https://teacher.xiaoguan.site/ws?token=bad` -> 301
- `https://teacher.xiaoguan.site/ws/?token=bad` -> 404
- `https://teacher.xiaoguan.site/centrifugo/connection/websocket` -> 400（无 WS upgrade 时返回 400 是正常的）

判断：

- 教师端页面和数据接口可用。
- 旧 `/ws` 线上 Nginx 路径有问题，会产生控制台噪音。
- Centrifugo 路径看起来是对的，但 tx-new 当前代码还不是本地实时修复版本。

### 4.4 tx-new API 修复点状态

使用 `.tmp/verify-tx-local-api.mjs` 对比得到：

```text
## tx-new https://teacher.xiaoguan.site
login 200 token=ok
me {"status":200}
analytics_7d {"status":500,"error":"Internal Server Error"}
conversations {"status":200,"total":5,"first":{"id":72,"status":"teacher_serving","student_id":18,"student_name":null,"teacher_name":null}}
knowledge_entries {"status":404,"detail":"Not Found"}
knowledge_pending {"status":404,"detail":"Not Found"}
unanswered_top {"status":200,"items":2}
```

结论：

- `analytics` 时间修复：**tx-new 未部署**，仍 500。
- `knowledge entries` API：**tx-new 未部署**，仍 404。
- `conversations` 学生/教师姓名字段：**tx-new 未部署**，`student_name` / `teacher_name` 为 null。
- `unanswered-top`：线上可用。

### 4.5 tx-new 图标状态

结果：**旧图标仍在线上**。

HTTP 检查：

- `https://yxg.xiaoguan.site/static/favicon.svg` -> 200，长度约 208。
- `https://teacher.xiaoguan.site/static/favicon.svg` -> 200，长度约 208。

本地新图标：

- `apps/student-app/src/static/favicon.svg` -> 长度约 8555。
- `apps/teacher-app/src/static/favicon.svg` -> 长度约 8555。
- `viewBox="520 160 640 640"`
- 不包含原来的背景 rect。

结论：

- 新图标本地已完成，但还没有部署到 tx-new。

## 5. 本地前端 + 165-dev 验证结果

### 5.1 本地学生端

结果：**PASS**。

Playwright CLI 实际打开：

- URL：`http://localhost:3001/#/`
- 自动跳转：`#/pages/home/index`
- 页面显示：`下午好，pilot-*`

网络请求：

- `POST /api/auth/pilot-anonymous` -> 200
- `GET /api/auth/me` -> 200
- `GET /api/conversations/unread-summary` -> 200
- `GET /api/conversations?page=1&size=3` -> 200
- `POST /api/track` -> 200

控制台：

- 0 errors
- 0 warnings

判断：

- 本地学生端免登录、首页、接口代理都可用。
- pilot 用户跳过无意义实时连接后，学生端控制台很干净。

### 5.2 本地教师端

结果：**页面 PASS；需要 tunnel 才能消除 Centrifugo 连接问题**。

Playwright CLI 实际操作：

- 打开 `http://localhost:5301/#/`
- 账号 `anjing` 登录成功。
- 进入 `#/pages/dashboard/index`。
- 工作台数据正常加载。

未启动 tunnel 时：

- `/centrifugo/connection/websocket` 连接失败。

启动 tunnel 后：

- `127.0.0.1:18000 -> 192.168.100.165:8000`
- `GET /api/auth/centrifugo-token` -> 200
- 页面数据接口仍全部正常。
- 仍可看到旧 `/ws` warning，但不影响 Centrifugo 双端实时脚本通过。

判断：

- 教师端基本页面正常。
- 本地 dev 的实时验证依赖 tunnel；脚本前提满足后实时链路通过。

### 5.3 本地新图标

结果：**PASS**。

检查：

- `http://localhost:3001/static/favicon.svg` -> 200，长度约 8555。
- `http://localhost:5301/static/favicon.svg` -> 200，长度约 8555。
- `hasBgRect=false`
- `viewBox="520 160 640 640"`

结论：

- 本地两端都已经使用新透明 SVG。
- 只需 build + 上传静态目录即可让 tx-new 生效。

## 6. 本地/165-dev 后端修复验证

### 6.1 API 对比结果

```text
## 165-dev http://192.168.100.165:8100
login 200 token=ok
me {"status":200}
analytics_7d {"status":200,"keys":["metrics","trends","cost_summary","ai_quality","hot_unanswered","college_distribution"]}
conversations {"status":200,"total":94,"first":{"id":171,"status":"teacher_serving","student_id":18,"student_name":"林小满","teacher_name":"安静"}}
knowledge_entries {"status":200,"total":29,"items":2}
knowledge_pending {"status":404,"detail":"Not Found"}
unanswered_top {"status":200,"items":1}
```

结论：

- `analytics` 修复：**165-dev 已可用**。
- `knowledge entries` API：**165-dev 已可用**。
- `conversations` 学生/教师姓名字段：**165-dev 已可用**。
- `knowledge_pending` 本次使用的路径返回 404，可能是我探测路径不对，不作为本次修复结论。

### 6.2 本地相关单测

命令：

```bash
JWT_SECRET=test-secret-for-local-validation-please-change \
python -m pytest \
  services/gateway/tests/test_knowledge_entries_list.py \
  services/gateway/tests/test_notify_conversation_parties.py -q
```

结果：

```text
11 passed, 3 warnings
```

说明：

- 知识条目列表 API 单测通过。
- 实时推送到会话双方 user/channel 的核心单测通过。

另外尝试一起跑 `test_analytics_capture.py` 时：

- 20/21 通过。
- 1 个失败是测试直接调用 slowapi 装饰的 endpoint，缺少 `Request` 参数。
- 这个失败更像测试调用方式/限流装饰器兼容问题，不是线上 `analytics` 500 的 timezone 修复本身。
- 实际 165-dev API `/api/analytics?period=7d` 已返回 200。

## 7. 本地 Playwright 脚本验证结果

### 7.1 双端实时聊天

脚本：`.tmp/demo-video/test-realtime-v7.mjs`

结果：**PASS**。

关键输出：

```text
T1 (teacher UI 发 -> student UI 实时收): PASS
T2 (student UI 发 -> teacher UI 实时收): PASS
T3 (再一轮 teacher -> student): PASS
student frames=8, teacher frames=3
stu user# hits=2, tea user# hits=0
summary T1=true T2=true T3=true
```

判断：

- 本地前端 + 165-dev 后端的双端 UI 实时聊天闭环可用。
- 教师端 `user#` 自动订阅仍为 0，这与之前记录的 P2 遗留一致；但不影响当前 detail 页内双端实时聊天。

### 7.2 FOUT / 滚动 / 动效

脚本：`.tmp/demo-video/verify-ui-bugs.mjs`

结果：**PASS**。

关键输出：

```text
Bug 1 (字体闪烁): student=PASS teacher=PASS
Bug 2 (滚动 + 动效): scroll=PASS animate=PASS
```

具体结果：

- 学生端 Material Symbols ligature 泄漏：`0/30 samples`
- 教师端 Material Symbols ligature 泄漏：`0/30 samples`
- teacher -> student 连发 5 条：全部 `contains=true inViewport=true hasAnimate=true`
- student -> teacher 连发 5 条：全部 `contains=true inViewport=true hasAnimate=true`

判断：

- 本地 FOUT 防御、聊天自动滚动、消息入场动效都已经修好。

## 8. 本地与 tx-new 当前差异总结

| 功能点 | tx-new 线上 | 本地/165-dev | 结论 |
|---|---|---|---|
| 学生免登录 | PASS | PASS | 线上和本地都正常 |
| 学生 AI 问答 | PASS | 未重复跑 UI，但 API/页面正常 | 线上当前可用 |
| 教师登录/工作台 | PASS，有 `/ws` 301 报错 | PASS，有 tunnel 后实时可用 | 页面可用，实时链路本地更完整 |
| 新项目图标 | 未部署，仍旧图标 | PASS，新透明 SVG | 可优先上传 |
| analytics | 500 | 200 | 本地修复未部署 |
| knowledge entries | 404 | 200 | 本地新增 API 未部署 |
| conversation student_name/teacher_name | null | 有真实姓名 | 本地修复未部署 |
| 双端实时 UI | 未在 tx-new 完整验证；旧 `/ws` 报错 | PASS | 建议部署实时修复后再测 tx-new |
| FOUT 防御 | 未在 tx-new 版本体现完整修复 | PASS | 本地修复有效 |
| 聊天滚动/动效 | 未在 tx-new 版本体现完整修复 | PASS | 本地修复有效 |

## 9. 风险与建议

### 9.1 可以立即做的小部署

建议先部署：**图标小包**。

原因：

- 本地已验证新图标资源正确。
- tx-new 仍是旧图标。
- 只影响静态 H5，不需要重启 gateway。
- 风险最低。

包含：

- 学生端 `src/static/favicon.svg`
- 教师端 `src/static/favicon.svg`
- 学生端登录页 logo 替换
- 教师端登录页 logo 替换

### 9.2 建议下一批部署的后端修复

建议部署：

- `analytics.py` timezone/naive datetime 修复。
- `GET /api/v1/knowledge/entries`。
- `ConversationResponse.student_name / teacher_name`。

原因：

- 这些在 tx-new 明确缺失或报错。
- 165-dev 已实际验证通过。
- 单测覆盖了 knowledge entries 和通知逻辑。

### 9.3 实时推送修复建议单独部署

本地实时脚本已经 PASS，但它牵涉：

- 后端 Centrifugo v6 JSON-RPC。
- 前端 Centrifuge token/connection。
- Nginx `/centrifugo/connection/websocket`。
- 旧 `/ws` 报错噪音。

建议单独部署并做一次 tx-new 双端 Playwright 验证。

### 9.4 tx-new 旧 `/ws` 问题

现状：

- `wss://teacher.xiaoguan.site/ws?token=...` 被 Nginx 301 到 `/ws/?token=...`。
- `/ws/` 返回 404。

建议：

- 如果旧 WebSocket 仍保留，Nginx 需要正确 proxy `/ws` 且避免 slash redirect。
- 如果未来完全依赖 Centrifugo，应考虑前端不再主动连旧 `wsManager`，或降级为非错误日志。
- 当前学生 pilot 用户本地已经跳过实时连接，这是一个正确方向。

## 10. 总体结论

- **tx-new 当前内测主链路可用**：学生免登录、AI 问答、教师登录/工作台都能实际打开并使用。
- **tx-new 仍缺本地若干修复**：analytics 500、knowledge entries 404、姓名字段缺失、新图标未部署、旧 `/ws` 301 报错。
- **本地修复总体质量较好**：新图标、学生/教师本地页面、165-dev analytics、knowledge entries、姓名字段、双端实时、FOUT、滚动/动效均通过实际验证。
- **不建议整仓覆盖 tx-new**：仍应按“图标小包 -> 后端低风险修复 -> 前端体验更新 -> 实时修复”分批上传。
