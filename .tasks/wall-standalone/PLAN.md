# 医小管 内测大屏 · 独立页 PLAN

> **目标**：把大屏从 Evidence 框架里抽离出来做成独立产品，
> 路径 `https://yxg.xiaoguan.site/wall/`，全屏占满，
> 米色画报头版风（与 `/bi/` 画报体系共用 token 但自成一脉）。
>
> **设计原则**：
> 1. 与 Evidence 完全解耦，未来 Evidence 升级不破
> 2. 视觉与 BI 画报共用 `yxg-theme.css` 的 token（米色 + 紫绛 + 思源宋体）
> 3. 自适应 1080p / 2K / 4K，部署一次满足三档
> 4. 现阶段 5 分钟 cron 轮询，未来可平滑切到 WebSocket

---

## 决策记录（2026-05-10）

| 决策 | 结论 |
|---|---|
| **URL** | `/wall/`（与 `/bi/` 平起平坐的独立产品） |
| **刷新机制** | 阶段 1 = cron 5 分钟轮询。阶段 2 = WebSocket 实时（**记入 backlog，本期不做**） |
| **目标分辨率** | 一次适配 1080p / 2K / 4K（1920×1080、2560×1440、3840×2160） |
| **栈** | 纯 HTML + CSS + vanilla JS + ECharts（图表） |
| **数据源** | 直连 postgres (127.0.0.1:5432, ro_bi 只读账号)，复用 Evidence 的 7 个 v_* view。独立 `wall_export.py` 脚本生成 JSON 快照, 不走 Evidence DuckDB |
| **token 来源** | 复用 `services/bi-evidence/static/yxg-theme.css` 的米色画报 token（紫绛 / 朱红 / 冷金 / 米色 / 思源宋体）|

---

## 阶段 0 · 准备

- [x] **0.1** 确认数据源：**postgres** (127.0.0.1:5432 / yixiaoguan_v2 / ro_bi 只读 / public schema)，7 个 v_* view。详见下方"数据源 schema"段落
- [x] **0.2** 确认部署环境:tx-new 服务器、nginx、Python 3 已就绪
- [x] **0.3** 用户决策（URL / 刷新机制 / 分辨率 / PLAN 落地）已确定
- [x] **0.4** 本 PLAN 文件落地

### 数据源 schema (0.1 附录)

**连接配置** (从 `services/bi-evidence/sources/yxg/connection.yaml` 读出)：
```yaml
host: 127.0.0.1
port: 5432
database: yixiaoguan_v2
user: ro_bi
password: f0263944224d4b2470a57bb788d87f4a
schema: public
```

**主力 view**：
| view | 列 (简) |
|---|---|
| v_kpi_daily | day, user_type, dau, active_users, pv, chat_sends, chat_ok, chat_err, card_shown, card_submitted, card_dismissed, feedback_opens, feedback_submitted, kb_clicks, service_clicks, quick_clicks |
| v_funnel_user | user_id, s1_started..s6_gave_feedback (bool), user_type, college_name, campus, class_name, grade_year |
| v_events_enriched | id, event_name, props (jsonb), client_ts, user_id, user_type, college_name, campus, day_ts, hour_ts |

**口径约定**：
- `user_type` 目前只有 `'pilot'` 一个值 (内测期)，分 student/teacher 要 join v_users_dim 或读 props.role
- 累计 KPI 以 `sum(...) from v_kpi_daily` (所有历史)，当日指标 `where day = CURRENT_DATE`
- `day_num` = (CURRENT_DATE - DATE '2026-05-08' + 1)
- ticker 默认排除 `page_view` (量大淹没真实行为)

---

## 阶段 1 · 数据层（Python 导出脚本）

### 1.1 `scripts/wall_export.py`

- [x] **1.1.1** 写 Python 脚本 `scripts/wall_export.py`, 连接 **postgres** (ro_bi 只读), 4 个查询全通过, dry-run 22ms
    - `kpis`: active=10 / questions=14 / answered=13 / ai_rate=93 / blind=4 / feedback=0
    - `funnel`: [17, 17, 3, 3, 3, 0] (内测 pilot 19 人)
    - `daily`: 3 行 (2026-05-08~05-10)
    - `ticker`: 20 行 (排除 page_view)
- [x] **1.1.2** 输出格式: `{ generated_at, day_num, kpis, funnel[], daily[], ticker[], elapsed_ms, error }`
- [x] **1.1.3** 输出路径 `/var/www/yixiaoguan/wall/data.json` (原子写: tmpfile → os.replace)
- [x] **1.1.4** 错误处理: connect_timeout=5s / statement_timeout=5s / 单查询失败降级 / 全局失败仍返合法 JSON + error 字段
- 服务器装 `python3-psycopg2` 系统包 (apt) 作为依赖

### 1.2 调度

- [x] **1.2.1** systemd unit + timer 落地: `deploy/systemd/yxg-wall-export.{service,timer}`
  - User=easten, Type=oneshot, TimeoutStartSec=30s
  - Timer: OnBootSec=30s, OnUnitActiveSec=5min, AccuracySec=10s, Persistent=true
- [x] **1.2.2** 服务器安装 + enable + 立即跑一次 (22ms ok)
- [x] **1.2.3** 验证: `systemctl status yxg-wall-export.timer` = active(waiting), 下次触发 11:22:35

### 1.3 验收

- [x] **1.3.1** 手动 dry-run JSON 结构符合预期
- [x] **1.3.2** data.json 生成于 `/var/www/yixiaoguan/wall/`, 644, easten:easten, nginx 可读
- [x] **1.3.3** 11:22:35 timer 触发后 data.json mtime 更新为 11:22 (验证轮询产生新快照)

---

## 阶段 2 · 前端实现

### 2.1 项目结构

本地源码：`f:\Documents\code\yixiaoguan-v2\services\wall-standalone\`

```
wall-standalone/
├── index.html            (报头 + §一 KPI + §二 漏斗+趋势 + §三 ticker + 页脚)
├── assets/
│   ├── wall-tokens.css   (从 yxg-theme.css 抽出的 CSS vars + 1080/2K/4K 尺寸级)
│   ├── wall.css          (大屏专属样式 + 报章骨架 + 隐鼠标)
│   └── wall.js           (fetch + 时钟 + ECharts + count-up + 离线兑底)
└── README.md             (部署说明)
```

> NOTE: ECharts 用 jsdelivr CDN (`echarts@5.5.0`) 未本地化，如后续 CDN 不稳再补 (PLAN 2.6.1 其中一项)

### 2.2 token 抽取

- [x] **2.2.1** `assets/wall-tokens.css`: 从 yxg-theme.css 抽出全部 CSS vars (jiang · huangzi · zhuhong · cooljin · xiangya · yumi · mizhi · mohei · hui · line-gold · serif/sans/mono 字体)
- [x] **2.2.2** 三档断点 vars: 1080p 默认 / 2K (>=2400px) / 4K (>=3600px), 统一 padding·字号·间距·chart-h 全变量控制

### 2.3 HTML 骨架

- [x] **2.3.1** `<head>`: viewport=1920 / link tokens.css + wall.css / favicon=data: / meta refresh 15min 兑底
- [x] **2.3.2** 报头 masthead: PILOT VOL.I + 宋体 900 大字刺名 + 启动天数 + 时钟 + 朱红 LIVE 脱机状态可切 OFFLINE
- [x] **2.3.3** § 一: 6 KPI 数据栏 (data-kpi="active|questions|..." 被js 填)
- [x] **2.3.4** § 二: 漏斗 (#funnelList) + 折线 (#dailyChart, ECharts)
- [x] **2.3.5** § 三: ticker (#tickerTrack)
- [x] **2.3.6** 页脚: 最后更新时间 + 朱红印章小标

### 2.4 CSS 自适应 (通过 wall-tokens.css 的 var() 切换跳档不动结构)

- [x] **2.4.1** 1080p 默认: pad 2.5/1.6rem, kpi 3.4rem, chart 240px
- [x] **2.4.2** 2K ≥2400px: pad 3/2.2rem, kpi 4.4rem, chart 310px
- [x] **2.4.3** 4K ≥3600px: pad 4/3rem, kpi 6rem, chart 420px
- [x] **2.4.4** wall-charts 中区 grid 1fr/1.5fr, KPI 6 列 + 1440 以下降为 3 列 + 900 以下降为 2 列 (不是设计目标但不炸)

### 2.5 JS 行为

- [x] **2.5.1** 时钟 1s setInterval, 独立于数据 fetch
- [x] **2.5.2** 数据: load + 5min setInterval, fetch 带 cache buster `?_=Date.now()` + cache:no-store
- [x] **2.5.3** 渲染: KPI count-up / funnel 条 (max 标化到 100%) / ticker (双份拼接无限滚)
- [x] **2.5.4** ECharts SVG renderer 折线, 调色板 #5B1F5B/#A23130/#A98B4F
- [x] **2.5.5** fetch fail → 顶部红小标 "数据离线" + LIVE 变 OFFLINE
- [x] **2.5.6** count-up ease-out cubic, 800ms

### 2.6 字体本地化

- [x] **2.6.1** 思源宋体 SC 权重 400/500/600/700/900 已从 fonts.font.im 引入 (wall-tokens.css 顶部 @import)
- [x] **2.6.2** Inter weights 200/300/400/500/600/700 已引入 (200 用于 KPI 大数字)
- [ ] **2.6.3** 4K 高 DPI 下思源宋体粗细 (依赖阶段 4 真机验证)
- [ ] **2.6.4** ECharts 本地化 (如后续 CDN 不稳才做。 现用 jsdelivr cdn)

---

## 阶段 3 · 部署

### 3.1 服务器目录

- [x] **3.1.1** `/var/www/yixiaoguan/wall/` 已存在 (阶段 1.2.1 为 timer 用创建)
- [x] **3.1.2** index.html / assets/ 3 个文件上传 · chown www-data
- [x] **3.1.3** chown www-data:www-data (不动 data.json, easten:easten 依然 timer 读写)

### 3.2 nginx

- [x] **3.2.1** 在 `/etc/nginx/sites-enabled/yixiaoguan` 的 yxg.xiaoguan.site server block 中加入 `location /wall/`（插在 /bi/ 之前）
- [x] **3.2.2** `nginx -t` syntax ok + `systemctl reload nginx`
- [x] **3.2.3** `curl https://yxg.xiaoguan.site/wall/` → HTTP 200 6213b text/html

### 3.3 数据导出脚本部署

- [x] **3.3.1** `wall_export.py` 在 `/home/easten/dev/yixiaoguan-v2/scripts/`
- [x] **3.3.2** systemd unit 在 `/etc/systemd/system/yxg-wall-export.{service,timer}`
- [x] **3.3.3** `daemon-reload` + `enable --now`
- [x] **3.3.4** timer active(waiting) + 11:22:35 已运行一次 (mtime 更新验证)

---

## 阶段 4 · 多分辨率验证

- [ ] **4.1** Chrome F12 → device emulation 切到 1920×1080，截图，对照 PLAN 的视觉预期
- [ ] **4.2** 切到 2560×1440，再截图
- [ ] **4.3** 切到 3840×2160，再截图
- [ ] **4.4** 真机：用户在实际办公室显示器上访问 → 反馈
- [ ] **4.5** 微调（如有）：grid 比例 / 字号 / padding

---

## 阶段 5 · 退旧

> 旧的 `/bi/wall/` 路径建议保留 30 天作为对比/回退用，到期后删。

- [ ] **5.1** 在画报 `/bi/` 首页或 sidebar 加链接"→ 内测大屏"指向 `/wall/`
- [ ] **5.2** （30 天后）删 `services/bi-evidence/pages/wall/` 目录
- [ ] **5.3** （30 天后）删 `services/bi-evidence/static/yxg-wall.css`
- [ ] **5.4** （30 天后）`/bi-v1/wall/` 也归档（但 `/bi-v1/` 画报保留作历史）

---

## Backlog（本期不做，记下来）

### 阶段 6 · 实时化（WebSocket 推送）
- [ ] 6.1 网关侧加 WebSocket endpoint `/ws/wall/`
- [ ] 6.2 学生提交事件 → Centrifugo 广播 → 大屏 ticker 实时增加一行（不再 5 分钟刷新）
- [ ] 6.3 KPI 数字也走 WebSocket 增量更新（每个事件后 +1）

### 阶段 7 · 夜间暗色模式
- [ ] 7.1 检测客户端时间 19:00 ~ 07:00 自动切深紫绛底（`#1F0F22` 配学院深紫 #2E1065）
- [ ] 7.2 字体颜色反转（米色字 / 浅金 hairline）
- [ ] 7.3 配独立 wall-night.css

### 阶段 8 · 投屏 / 推送
- [ ] 8.1 OBS / Kiosk 模式优化（隐藏鼠标 + 全屏快捷键 + meta refresh fallback）
- [ ] 8.2 每天 8 点 Headless Chrome 截 1080p 大屏图 → 钉钉机器人推送学院群
- [ ] 8.3 大屏右下角"扫码看全报告"二维码 → 跳到 `/bi/` 画报

### 阶段 9 · 多维切片
- [ ] 9.1 大屏 URL 加学院 query 参数 `/wall/?college=basic`，拉对应学院数据
- [ ] 9.2 报头加切换器（左右箭头切学院）
- [ ] 9.3 各学院首屏副刊（"基础医学院 · 第三天"独立页）

### 阶段 10 · 性能 / 监控
- [ ] 10.1 Sentry / Plausible 加埋点：大屏 hit 量 + 报错
- [ ] 10.2 data.json 大小报警（如 > 1MB 提示扩容）
- [ ] 10.3 自动 fallback：如果 3 次连续 fetch 失败，切到本地缓存 + 离线提示

---

## 风险 & 假设

| 风险 | 缓解 |
|---|---|
| ~~Evidence DuckDB 文件被独占~~ → 已改直连 postgres，非问题 | ro_bi 只读账号 + 快速查询 + 读超时 5s，不影响业务 |
| cron 5 分钟 vs 用户预期"实时" | 顶部时钟实时跳秒、ticker 自动滚动给"动感"；阶段 6 WebSocket 可补 |
| 4K 字体太大失协调 | 严格用 clamp() 而不是 vw，三档手动 tune |
| nginx /wall/ 与 SSL 协调 | 在已有 yxg.xiaoguan.site server block（443 + certbot）内加 location 即可 |
| postgres view 不存在 (首次部署或 view drop) | wall_export.py 错误降级输出 zero-data JSON + error 字段, 前端不白屏 |

---

## 进度看板（汇总）

```
阶段 0 准备           ✅ 4/4
阶段 1 数据层         ✅ 10/10
阶段 2 前端           ✅ 17/19 (2.6.3 4K 验证 + 2.6.4 ECharts 本地化 待验证后决定)
阶段 3 部署           ✅ 9/9
阶段 4 多分辨率验证   ⏸ 0/5
阶段 5 退旧           ⏸ 0/4 (5.2-5.4 推 30 天)
─────────────────────
Backlog (6-10)        📋 已记录, 不计入本期
```

> 完成一项就把 `- [ ]` 改为 `- [x]`，并把对应阶段在"进度看板"里更新分子。

---

**最后修改**：2026-05-10 10:55
**所有者**：易小管编辑部
**对应 IDE todo_list**：见 Cascade 内置任务管理器（与本文件双向同步）
