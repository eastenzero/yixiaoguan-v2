# 内测 BI 面板 — Evidence.dev 方案设计

> 制定时间: 2026-05-09 16:30 UTC+8
> 状态: 方案已敲定，待 TX 拍板视觉细节后进入实施
> 上游废止: `.tasks/bi-tier1-design-20260508.md`（手搓 ECharts 方案，已废弃）
> 实现目录: `services/bi-evidence/`（新增）+ TX-New 上的 nginx + cron

---

## 0. 决策清单

| 决策项 | 选定 |
|--------|------|
| **目标** | 给项目领导 / 老师**展示用**的精致演示页（不是教师自助分析工具）|
| **BI 工具** | **Evidence.dev**（markdown + sql，输出杂志/咨询报告级静态站）|
| **后端策略** | **零 endpoint**，仅写 7 个 SQL VIEW（语义层）+ 1 个只读账号 |
| **数据时效** | cron 每 5/10 分钟 build 一次，访问时是静态文件（领导看的是"截至 X 分钟前"，反而更稳）|
| **部署位置** | TX-New（82.156.129.75），与 gateway 共用 nginx |
| **访问形态** | 公开 URL，无登录、无 BI 工具感（看起来就是一份"内测白皮书"页面）|
| **视觉基调** | 杂志感 / 中性偏严肃 / 思源宋体或 Inter 主字体（待 TX 拍板）|
| **二次美化** | 完整 CSS 注入 + 自定义 Svelte 组件（动画/特效）开放 |
| **真实数据 vs 内测数据** | 顶部 toggle，但默认呈现"内测+真实合并"——领导只关心总量趋势 |

---

## 1. 现状对账（以代码 + TX-New 实测为准）

### 1.1 数据底座（已就位，零改动）

| 表 | 关键列 | 备注 |
|----|------|------|
| `events` | `id / user_id / event_name / props JSONB / client_ts / created_at` | 12 个 event_name 已上线，pilot 上线后已产生 130+ 条 |
| `chat_analytics` | `is_answered / rag_score / kb_doc_matched / total_tokens / total_price / latency / user_college_id / user_class_id` | RAG 分 + 成本完整 |
| `feedbacks` | `user_id / device_id / content / contact / source / created_at` | 通用反馈表单 |
| `unanswered_user_feedback` | `user_provided_college_id / user_provided_grade / user_provided_category / user_provided_note` | 学生主动提交的"盲区反馈" |
| `unanswered_questions` | `question_text / question_hash / hit_count / college_id / is_resolved` | 服务端聚类（非用户填）|
| `users` | `staff_id / name / role / college_id / class_id` | `staff_id LIKE 'pilot:%'` = 内测匿名用户 |
| `colleges` | `name / campus` | **bonus**: campus 可做校区维度 |
| `classes` | `name / college_id / grade_year` | **bonus**: grade_year 可做真实年级（不依赖 uuf 自填）|

### 1.2 前端埋点清单（截至 2026-05-09，`@apps/student-app/src/utils/track.ts:76`）

```text
event_name              主要 props                            使用页/组件
─────────────────────────────────────────────────────────────────────────
app_start               role / is_pilot                       App.vue 启动钩
page_view               path                                  4 个页面 onShow
service_card_click      card / source(home|services)          home + services 页
quick_question_click    label                                 home 页快捷问
chat_send               conv_id / content_length              chat 页发送
chat_response_ok        conv_id / message_id / content_length chat 页 SSE done
chat_response_error     conv_id / error_msg                   chat 页 SSE error
unanswered_card_shown   conv_id / message_id                  chat 页判定盲区
unanswered_card_submitted conv_id / has_college / has_grade / has_category / has_note  UnansweredInviteCard
unanswered_card_dismissed conv_id / message_id                UnansweredInviteCard
kb_doc_clicked          conv_id / source_title                chat 页源文档展开
feedback_form_open      —                                     FeedbackDrawer 打开
feedback_form_submit    has_contact                           FeedbackDrawer 提交
```

埋点完整、含义明确，**本期不需要新增埋点**。

### 1.3 TX-New 部署现状

```text
TX-New (82.156.129.75, Ubuntu 24.04)
├─ yixiaoguan-gateway.service     active, uvicorn :8100, user=easten
├─ docker
│  ├─ yx_postgres   postgres:16-alpine,  yixiaoguan_v2 db (owner=yxg)
│  ├─ yx_redis      redis:7-alpine
│  ├─ yxg-centrifugo centrifugo:v6
│  └─ docker-*      Dify 全家桶（独立 stack）
└─ nginx :80        反代到 gateway / dify / centrifugo
```

---

## 2. 后端语义层（7 个 VIEW + 1 个只读账号）

### 2.1 落地位置

新建 `services/gateway/sql/bi_views.sql`（**不走 alembic**，因 VIEW 是 BI 专用、可独立 drop/recreate，alembic 历史记录会变累赘）。

部署方式：
```bash
ssh tx-new
docker exec -i yx_postgres psql -U yx_admin -d yixiaoguan_v2 \
  < /home/easten/dev/yixiaoguan-v2/services/gateway/sql/bi_views.sql
```

### 2.2 完整 SQL 草稿（200 行，已对照真实列名校对）

```sql
-- ════════════════════════════════════════════════════════════════
--  yixiaoguan-v2  BI 语义层 VIEW
--  目的：把业务表打平成 BI 工具友好形态，pilot/real 标签 + 维度 join
--  使用方：Evidence.dev（也兼容 Metabase / Rill / Superset）
-- ════════════════════════════════════════════════════════════════

-- ─── 1. 用户维度 ───
CREATE OR REPLACE VIEW v_users_dim AS
SELECT
  u.id, u.staff_id, u.name, u.role::text,
  u.college_id, c.name AS college_name, c.campus,
  u.class_id,   cls.name AS class_name, cls.grade_year,
  (u.staff_id LIKE 'pilot:%')                                       AS is_pilot,
  CASE WHEN u.staff_id LIKE 'pilot:%' THEN 'pilot' ELSE 'real' END  AS user_type,
  u.created_at AS joined_at
FROM users u
LEFT JOIN colleges c   ON c.id   = u.college_id
LEFT JOIN classes  cls ON cls.id = u.class_id;

-- ─── 2. events 一站式视图 ───
CREATE OR REPLACE VIEW v_events_enriched AS
SELECT
  e.id, e.event_name, e.props, e.client_ts, e.created_at,
  e.user_id, d.staff_id, d.is_pilot, d.user_type,
  d.college_id, d.college_name, d.campus,
  d.class_id, d.class_name, d.grade_year,
  date_trunc('day',  e.created_at)::date  AS day_ts,
  date_trunc('hour', e.created_at)        AS hour_ts,
  EXTRACT(dow  FROM e.created_at)::int    AS dow,
  EXTRACT(hour FROM e.created_at)::int    AS hod
FROM events e
LEFT JOIN v_users_dim d ON d.id = e.user_id;

-- ─── 3. chat_analytics 一站式视图 ───
CREATE OR REPLACE VIEW v_chat_enriched AS
SELECT
  ca.id, ca.conversation_id, ca.user_id, ca.user_query, ca.query_norm,
  ca.rag_score, ca.kb_doc_matched, ca.is_answered,
  ca.prompt_tokens, ca.completion_tokens, ca.total_tokens,
  ca.prompt_price,  ca.completion_price,  ca.total_price, ca.currency,
  ca.latency, ca.created_at,
  d.staff_id, d.is_pilot, d.user_type,
  d.college_name, d.class_name, d.grade_year, d.campus,
  date_trunc('day', ca.created_at)::date AS day_ts,
  CASE
    WHEN ca.rag_score IS NULL    THEN 'unknown'
    WHEN ca.rag_score < 0.3      THEN 'low'
    WHEN ca.rag_score < 0.6      THEN 'mid'
    ELSE 'high'
  END AS rag_bucket
FROM chat_analytics ca
LEFT JOIN v_users_dim d ON d.id = ca.user_id;

-- ─── 4. 日级 KPI rollup ───
CREATE OR REPLACE VIEW v_kpi_daily AS
SELECT
  date_trunc('day', e.created_at)::date AS day,
  COALESCE(d.user_type, 'unknown')      AS user_type,
  COUNT(DISTINCT e.user_id) FILTER (WHERE e.event_name='app_start')                AS dau,
  COUNT(DISTINCT e.user_id)                                                        AS active_users,
  COUNT(*) FILTER (WHERE e.event_name='page_view')                                 AS pv,
  COUNT(*) FILTER (WHERE e.event_name='chat_send')                                 AS chat_sends,
  COUNT(*) FILTER (WHERE e.event_name='chat_response_ok')                          AS chat_ok,
  COUNT(*) FILTER (WHERE e.event_name='chat_response_error')                       AS chat_err,
  COUNT(*) FILTER (WHERE e.event_name='unanswered_card_shown')                     AS card_shown,
  COUNT(*) FILTER (WHERE e.event_name='unanswered_card_submitted')                 AS card_submitted,
  COUNT(*) FILTER (WHERE e.event_name='feedback_form_submit')                      AS feedback_submitted,
  COUNT(*) FILTER (WHERE e.event_name='kb_doc_clicked')                            AS kb_clicks,
  COUNT(*) FILTER (WHERE e.event_name='service_card_click')                        AS service_clicks,
  COUNT(*) FILTER (WHERE e.event_name='quick_question_click')                      AS quick_clicks
FROM events e
LEFT JOIN v_users_dim d ON d.id = e.user_id
GROUP BY 1, 2;

-- ─── 5. 用户级漏斗（每用户最远到达的步骤） ───
CREATE OR REPLACE VIEW v_funnel_user AS
WITH per_user AS (
  SELECT
    e.user_id,
    bool_or(e.event_name='app_start')                                              AS s1_started,
    bool_or(e.event_name='page_view')                                              AS s2_browsed,
    bool_or(e.event_name='chat_send')                                              AS s3_asked,
    bool_or(e.event_name='chat_response_ok')                                       AS s4_got_answer,
    bool_or(e.event_name='unanswered_card_shown')                                  AS s5_card_shown,
    bool_or(e.event_name IN ('unanswered_card_submitted','feedback_form_submit')) AS s6_gave_feedback
  FROM events e
  GROUP BY 1
)
SELECT pu.*, d.user_type, d.college_name, d.campus
FROM per_user pu
LEFT JOIN v_users_dim d ON d.id = pu.user_id;

-- ─── 6. 服务热度（service_card_click + quick_question_click） ───
CREATE OR REPLACE VIEW v_service_heat AS
SELECT
  e.event_name,
  COALESCE(e.props->>'card', e.props->>'label') AS item,
  e.props->>'source'                            AS source,
  d.user_type,
  COUNT(*)                                      AS clicks,
  COUNT(DISTINCT e.user_id)                     AS users,
  date_trunc('day', e.created_at)::date         AS day
FROM events e
LEFT JOIN v_users_dim d ON d.id = e.user_id
WHERE e.event_name IN ('service_card_click', 'quick_question_click')
GROUP BY 1, 2, 3, 4, 7;

-- ─── 7. 未答反馈交叉 ───
CREATE OR REPLACE VIEW v_unanswered_cross AS
SELECT
  uuf.id, uuf.user_id, d.user_type,
  uuf.user_provided_college_id AS college_id, c.name AS college_name,
  uuf.user_provided_grade      AS grade,
  uuf.user_provided_category   AS category,
  uuf.user_provided_note,
  (uuf.user_provided_note IS NOT NULL AND length(trim(uuf.user_provided_note)) > 0) AS has_note,
  uuf.created_at,
  date_trunc('day', uuf.created_at)::date AS day
FROM unanswered_user_feedback uuf
LEFT JOIN v_users_dim d ON d.id = uuf.user_id
LEFT JOIN colleges    c ON c.id = uuf.user_provided_college_id;
```

### 2.3 BI 只读账号

```sql
-- 在 yx_admin 身份下执行
CREATE ROLE ro_bi LOGIN PASSWORD '<32-char random>';   -- 生成: openssl rand -hex 16
GRANT CONNECT ON DATABASE yixiaoguan_v2 TO ro_bi;
GRANT USAGE   ON SCHEMA public TO ro_bi;
GRANT SELECT  ON ALL TABLES    IN SCHEMA public TO ro_bi;
GRANT SELECT  ON ALL SEQUENCES IN SCHEMA public TO ro_bi;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ro_bi;
-- 兜底
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM ro_bi;
```

凭据写到 `services/bi-evidence/.env`（gitignore），不进 git。

---

## 3. Evidence.dev 项目结构

### 3.1 目录布局

```text
services/bi-evidence/
├── package.json              evidence + 必要 deps
├── evidence.plugins.yaml     注册 PG 数据源 + Tailwind
├── .env                      PG 连接（gitignore）
├── .env.schema               .env 模板（进 git）
├── sources/
│   └── yxg/
│       ├── connection.yaml   指向 ro_bi @ yx_postgres
│       └── _meta.json        evidence 自动生成
├── pages/
│   ├── index.md              首页 / hero 区 / 三大数字
│   ├── overview.md           概览：UV / 漏斗 / 时间趋势
│   ├── content.md            内容：服务热度 / 快捷问 / KB 命中
│   ├── voice.md              声音：未答反馈 / 通用反馈 / 学院分布
│   └── cost.md               成本：tokens / price / 模型效率
├── components/
│   ├── HeroNumber.svelte     大数字 hero 组件（自定义动画）
│   ├── JournalCard.svelte    杂志风卡片（含 small caps 标题）
│   └── SectionDivider.svelte 章节分隔（古典中线）
├── static/
│   ├── fonts/                自托管字体（思源宋体 + Inter Variable）
│   └── favicon.svg
└── tailwind.config.js        全局 token（颜色、字体、间距）
```

### 3.2 单页示例（pages/overview.md）

````md
---
title: 概览 · 内测看板
sidebar_position: 2
---

```sql kpi
select
  sum(chat_sends)         as total_questions,
  sum(chat_ok)            as answered,
  sum(active_users)       as au,
  round(100.0 * sum(chat_ok) / nullif(sum(chat_sends), 0), 1) as ai_rate
from yxg.v_kpi_daily
```

<div class="grid grid-cols-4 gap-6">
  <HeroNumber title="累计提问" value={kpi[0].total_questions} />
  <HeroNumber title="AI 解答率" value={kpi[0].ai_rate} suffix="%" />
  <HeroNumber title="活跃用户" value={kpi[0].au} />
  <HeroNumber title="累计答出" value={kpi[0].answered} />
</div>

## 漏斗

```sql funnel
select
  sum(s1_started::int)     as 启动,
  sum(s2_browsed::int)     as 浏览,
  sum(s3_asked::int)       as 提问,
  sum(s4_got_answer::int)  as 收到回复,
  sum(s5_card_shown::int)  as 触达盲区,
  sum(s6_gave_feedback::int) as 留下反馈
from yxg.v_funnel_user
```

<FunnelChart data={funnel} />

## 提问趋势

```sql daily
select day, sum(chat_sends) as 提问, sum(chat_ok) as 答出
from yxg.v_kpi_daily
group by 1 order by 1
```

<LineChart data={daily} x=day y={['提问', '答出']} />
````

### 3.3 视觉策略（待 TX 拍板细节）

| 元素 | 候选 | 待拍板 |
|---|---|---|
| 主字体 | A) 思源宋体 + Inter（杂志/学术风）<br>B) Noto Serif SC + Roboto（克制现代）<br>C) Inter + IBM Plex Sans（科技克制） | TX 选 |
| 配色 | A) 米白 + 深棕 + 朱红强调（中文老书风）<br>B) 深蓝学术 + 金色强调（哈佛/MIT 系）<br>C) 暗黑模式 + 青色（cyberpunk-lite） | TX 选 |
| Hero 区 | 大字号"医小管 · 内测数据" + 副标"Pilot Program · 起始日期 / 第 N 天" + 三个核心数字 | 默认 |
| 章节分隔 | 古典中线（细金线 + 罗马数字 §）or 现代色块 | TX 选 |
| 动画 | 数字 count-up / 页面 fade-in / 图表 stagger | 默认开 |

---

## 4. TX-New 部署形态

### 4.1 拓扑

```text
TX-New
├─ /home/easten/dev/yixiaoguan-v2/services/bi-evidence/
│   ├─ pages/...md
│   ├─ build/                          ← npm run build 产出
│   └─ node_modules/
├─ /etc/cron.d/yxg-bi-build            ← */5 * * * * 触发 build
├─ /var/log/yxg-bi-build.log
└─ nginx
   └─ location /bi/ {
        alias /home/easten/dev/yixiaoguan-v2/services/bi-evidence/build/;
        try_files $uri $uri/ /index.html;
        # 公开访问，无 basic auth
        # （如需要简单门槛，加 auth_basic + .htpasswd）
      }
```

### 4.2 Build 流程

```bash
# 首次
cd /home/easten/dev/yixiaoguan-v2/services/bi-evidence
npm install
cp .env.schema .env  # 填入 ro_bi 密码
npm run sources      # 拉数据快照到 .evidence/template/
npm run build        # 生成 build/

# 后续 cron（每 5 分钟）
*/5 * * * * cd /home/easten/dev/yixiaoguan-v2/services/bi-evidence \
  && npm run sources \
  && npm run build \
  >> /var/log/yxg-bi-build.log 2>&1
```

### 4.3 访问 URL

| 形态 | URL | 用途 |
|---|---|---|
| 内网测试 | `http://82.156.129.75/bi/` | 开发期 |
| 后续公网 | `https://<域名>/bi/` | 给领导/老师分享 |
| **不做** | 登录页 / token gate | 公开无门槛——方便分享 |

**风险提示**：默认无登录 → 数据本身脱敏（已无身份证号 / 银行卡 / 手机号），但聊天 query 文本可能含敏感内容。**首期面板不展示原始 query 文本，只展示聚合数字 + 已被 unanswered_questions 服务端聚类过的脱敏文本**。

---

## 5. 工时拆分

| 阶段 | 子任务 | 工时 | 依赖 |
|---|---|---|---|
| **B1** | 写 `services/gateway/sql/bi_views.sql`（7 个 VIEW） | 0.5h | — |
| **B2** | TX 上跑 SQL，verify VIEW 各跑一遍 | 0.3h | B1 |
| **B3** | 创建 `ro_bi` 账号 + 权限 + 凭据存 .env | 0.3h | B1 |
| **F1** | TX 上装 Node 20 + 拉 evidence 项目骨架 | 0.5h | — |
| **F2** | 配 PG 数据源 + sources YAML + 首次 sync 验证 | 0.5h | B3, F1 |
| **F3** | 写 `pages/index.md`（hero + 三大数字 + 起始日） | 1.5h | F2 |
| **F4** | 写 `pages/overview.md`（漏斗 + KPI + 趋势） | 2h | F2 |
| **F5** | 写 `pages/content.md`（服务热度 + 快捷问） | 1.5h | F2 |
| **F6** | 写 `pages/voice.md`（未答反馈交叉 + 学院分布） | 2h | F2 |
| **F7** | 写 `pages/cost.md`（tokens / price / 效率） | 1h | F2 |
| **V1** | 自定义字体 + 全局 Tailwind token + 配色 | 2h | F3-F7 |
| **V2** | 3 个自定义 Svelte 组件（HeroNumber / JournalCard / SectionDivider） | 2h | V1 |
| **V3** | 视觉精修第二轮（hero 动画、章节过渡、移动端） | 2-3h | V1, V2 |
| **D1** | nginx 反代 + cron build + 日志 | 0.5h | F2 |
| **D2** | 公网域名 / SSL（如要） | TBD | D1 |
| **总计** | | **~17h** | |

并行 1 人 2 天，或我和 TX 配合 1 天。

---

## 6. 风险与缓解

| 风险 | 严重 | 缓解 |
|---|---|---|
| Evidence build 时 PG 查询慢 | 🟢 低 | VIEW 已聚合，单次 build < 5s；events 表加 `idx_events_name_day`（已有）|
| 内测数据量小，图表"空" | 🟡 中 | 在 hero 区写"内测第 N 天 · N 名学生"上下文；漏斗用百分比替代绝对数字 |
| 公开 URL 暴露聚合数字 | 🟢 低 | 不展示原始 query / 用户名 / 学号；学院粒度已是脱敏汇总 |
| cron build 失败无感知 | 🟡 中 | build 脚本失败时保留上次 build 产物（不会显示空白）；写一个企业微信/Bot 告警（可选）|
| 视觉迭代回合多 | 🟡 中 | TX 先在选项中拍板字体/配色基调，再逐章节交付；每页独立 PR 互不干扰 |
| 字体 CDN 在国内慢 | 🟡 中 | 字体自托管在 `static/fonts/`，nginx serve；首屏 critical font 用 `<link rel=preload>` |

---

## 7. 后续可加（不在本期范围）

- **企业微信定时推日报截图**：cron 用 puppeteer 截 `/bi/` 首页 → 推 webhook
- **PDF 导出**：Evidence 内置支持，加一个"导出当前页"按钮即可
- **更多页面**：周报 / 月报 / 启动会专用大屏页（Hero 区独立设计）
- **如需教师自助探索**：再加 Metabase（共用同一份 VIEW，零迁移成本）

---

## 8. 待 TX 拍板（开干前）

1. **字体 + 配色基调**（参考 §3.3 三组候选）
2. **Hero 区起始日期文案**（"内测第 N 天 / 起始 2026-05-08 / 1 个班 X 名学生" 等）
3. **公开 URL 形态**：直接用 IP `http://82.156.129.75/bi/` 给老师测试，还是先申请 / 复用域名？
4. **是否要 build 失败告警**（企业微信/Bot 推送）

---

## 变更日志

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-05-09 16:30 | 首版，Evidence.dev 主选 + 7 VIEW 语义层 + TX-New 部署形态 | Cascade |
