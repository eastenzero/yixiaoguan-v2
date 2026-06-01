# BI Tier-1 横版面板 — 模块设计 + 后端聚合 SQL 草稿

> 制定时间: 2026-05-08 19:50 UTC+8
> 状态: 待 TX 拍板后进入实现
> 上游: `.tasks/master-plan-pilot-mode-20260508.md` §D-P2-1, `.tasks/bi-dashboard-handoff.md`
> 实现入口: `services/gateway/app/routers/analytics.py` + `apps/teacher-app/src/pages/analytics/index.vue`

---

## 0. 决策清单（执行者必读）

| 决策项 | 选定 |
|--------|------|
| 部署形态 | **PC 响应式 + 现页扩展**（teacher-app analytics 页加 `@media (min-width: 1024px)` 横版 grid，移动端保持现有竖版） |
| 图表库 | **ECharts 5.x**（npm `echarts`，按需 import）— 仅在 PC 宽度启用，H5 手机回退到 SCSS 实现 |
| 端点策略 | 5 个 block 扩展现有 fat `/api/analytics`；M4（未答交叉）和 M6 drill 新增独立子端点 |
| pilot vs 真用户 | **所有指标默认双轨展示**（顶部 toggle: 全部 / pilot / real），按 `users.staff_id LIKE 'pilot:%'` 区分 |
| 去重维度 | 因 `events` 表**无 `device_id` 列**（仅 `user_id`），统一用 `user_id` 做 unique；pilot 用户的 `user_id` 与 device 一一映射，等价 |
| 时间粒度 | period chip 维持 7d / 30d / all；by_day 序列长度 = period 天数 |
| 隐私 | feedback content / uuf note 在 PC 面板默认脱敏（手机号 / 学号 mask），admin 可点开看全文 |

---

## 1. 现状校对（以代码为准）

| 表 | 实际字段（关键列） | 备注 |
|----|------|------|
| `events` | `id / user_id / event_name / props JSONB / client_ts / created_at` | **无 device_id**；handoff doc 写错 |
| `chat_analytics` | `is_answered / rag_score / query_norm / kb_doc_matched / prompt_tokens / completion_tokens / total_tokens / prompt_price / completion_price / total_price / currency / latency / user_college_id / user_class_id` | **无 is_sufficient_query / score 字段**（用 `rag_score`） |
| `feedbacks` | `id / user_id / device_id / content / contact / source / created_at` | source 默认 `'general'` |
| `unanswered_user_feedback` | `id / conversation_id / message_id / user_id / user_provided_college_id / user_provided_grade / user_provided_category / user_provided_note / unanswered_question_id / created_at` | 字段名带 `user_provided_` 前缀 |
| `unanswered_questions` | `id / question_text / question_hash / hit_count / sample_conv_ids / college_id / is_resolved` | 服务端聚合（非用户填写） |

**已实现 `/api/analytics` block**（`@/Users/Administrator/Documents/code/yixiaoguan-v2/services/gateway/app/routers/analytics.py:43-261`）：
- `metrics`: `total_questions / ai_rate / avg_response_min / pending_count` + `_prev`
- `trends`: `dates[] / total[] / ai_answered[]`
- `cost_summary`: `total_tokens / total_price / avg_latency_seconds / by_day[]`
- `ai_quality`: `hit_rate / score_low / score_mid / score_high`
- `hot_unanswered`: top 5 `{ id, text, count }`
- `college_distribution`: top 8 `{ name, count }`
- `heatmap`: `7×24` 二维数组

**未实现**：funnel / service_heat / unanswered_cross / 质量延迟 p50/p95 / 成本明细 drill —— 这是本次的全部范围。

---

## 2. 端点契约

### 2.1 扩展现有 fat endpoint

`GET /api/analytics?period=7d|30d|all&user_type=all|pilot|real`

新增 query param `user_type`（默认 `all`，影响所有 block 的 WHERE 条件）。

返回新增 4 个 block：

```json
{
  "metrics": {
    "...": "...",
    "uv": 0,
    "uv_prev": 0,
    "feedback_count": 0,
    "unanswered_feedback_count": 0,
    "ai_no_answer_count": 0,
    "ai_no_answer_rate": 0.0,
    "pilot_user_count": 0,
    "real_user_count": 0
  },
  "funnel": {
    "steps": [
      { "name": "page_view_home", "hits": 0, "users": 0 },
      { "name": "chat_send", "hits": 0, "users": 0 },
      { "name": "chat_response_ok", "hits": 0, "users": 0 },
      { "name": "unanswered_card_shown", "hits": 0, "users": 0 },
      { "name": "feedback_or_unanswered_submit", "hits": 0, "users": 0 }
    ]
  },
  "service_heat": {
    "service_clicks": [{ "card": "校园网", "source": "home", "count": 234 }],
    "quick_question_clicks": [{ "label": "宿舍调换", "count": 89 }]
  },
  "ai_quality": {
    "...": "...",
    "latency_p50": 0.0,
    "latency_p95": 0.0,
    "rag_score_avg": 0.0,
    "feedback_after_no_answer_rate": 0.0
  },
  "cost_summary": {
    "...": "...",
    "cost_per_resolved": 0.0,
    "cost_per_question": 0.0
  }
}
```

### 2.2 新独立端点

#### `GET /api/analytics/unanswered-cross?by={college|grade|category|college_x_category}&period=7d&user_type=all`

```json
{
  "by": "college",
  "rows": [
    {
      "key": 1,
      "label": "临床与基础医学院",
      "total": 47,
      "with_note": 12,
      "top_categories": [{ "category": "scholarship", "count": 18 }]
    }
  ],
  "unfilled": { "no_college": 23, "no_grade": 14, "no_category": 19 },
  "total": 120
}
```

`by=college_x_category` 返回二维：
```json
{ "by": "college_x_category", "matrix": [{ "college_id": 1, "category": "scholarship", "count": 18 }] }
```

#### `GET /api/analytics/cost-detail?by={conv|user|model}&period=7d&limit=10&user_type=all`

```json
{
  "by": "conv",
  "rows": [
    { "conversation_id": 123, "user_id": 45, "is_pilot": true, "tokens": 8204, "price": 0.0123, "calls": 7 }
  ]
}
```

---

## 3. 模块详细契约

### M1. 核心 KPI（横版 6 卡）

| 卡片 | 字段 | 说明 |
|------|------|------|
| 总提问 | `metrics.total_questions` (+ prev) | 沿用 |
| AI 解答率 | `metrics.ai_rate` (+ prev) | 沿用 |
| 平均响应 | `metrics.avg_response_min` (+ prev) | 沿用 |
| 待处理 | `metrics.pending_count` | 沿用 |
| 活跃 UV | `metrics.uv` (+ prev) | 新增；`COUNT(DISTINCT events.user_id)` |
| 反馈/盲区 | `metrics.feedback_count + unanswered_feedback_count` | 新增；两类反馈合并展示，副标记区分 |

PC 横版：6 卡 1 行（每卡 ~16% 宽）；H5：保持 4 卡 2×2，UV / 反馈 卡折叠到详情区。

### M2. 漏斗 funnel（ECharts funnel）

5 步漏斗，PC 端使用 ECharts `funnel` 图：

```
page_view_home
  ↓
chat_send
  ↓
chat_response_ok
  ↓
unanswered_card_shown        # 仅当 chat_response_ok 后判定为未答
  ↓
feedback_or_unanswered_submit  # 卡片提交 OR 通用反馈表单提交
```

每步双指标 `hits / users`，前端切换 segmented control。漏斗右侧附"步间转化率"小表。

### M3. 服务热度（ECharts horizontal bar × 2）

PC 端横版左右 2 栏：
- **服务卡片 Top 10**：`event_name='service_card_click'` 按 `props->>'card'` 聚合，副标签显示 `props->>'source'`(home / services)
- **快捷问 Top 10**：`event_name='quick_question_click'` 按 `props->>'label'` 聚合

H5 端：竖排单列。

### M4. 未答交叉（ECharts heatmap + sankey 备选）

PC 端：4 个 tab 切换 `by` 维度
- 学院（≤21 行 × 1 列）→ 横向 ranked bar
- 年级（6 行）→ ranked bar
- 8 类别（8 行）→ ranked bar
- **学院 × 类别**（21×8 cell）→ ECharts heatmap（重头戏）

每个 row 附右侧"备注样本"（最近 3 条 `user_provided_note` 摘要 + 跳转完整列表入口）。

H5 端：仅展示前 3 个简单维度的 ranked bar，二维 heatmap 用文字摘要替代。

### M5. 质量分布（ECharts gauge + 三档条 + line chart）

PC 横版 3 列布局：
- **命中率 gauge**（沿用 ring 样式，但 ECharts gauge 渲染）
- **rag_score 三档分布**（沿用现有 fill bar）
- **延迟 p50/p95 折线**（新增；按日 line chart）

底部一行小卡：`feedback_after_no_answer_rate`（盲区→反馈转化率），用百分比 + 上下箭头标注趋势。

### M6. 成本明细

PC 横版：上下两块
- **概要卡 4 数字**：`total_tokens / total_price / cost_per_resolved / cost_per_question`
- **明细 drill**：tab 切换 by_day | by_conv | by_user，line/horizontal bar 展示
  - by_day：line chart（沿用现有 `cost_summary.by_day`）
  - by_conv：表格 Top 10，每行 `conv_id | user(pilot/real 标识) | tokens | price | calls`
  - by_user：表格 Top 10，按 user_id 聚合

异常标红规则：单 user 当日 price > 1 元 → 红色 chip + "可能滥用"提示。

---

## 4. SQL 草稿（精校 column 名 + pilot 过滤）

### 全局 helper

```sql
-- pilot/real 过滤子句（参数化）
-- user_type='all'  : 无 WHERE
-- user_type='pilot': u.staff_id LIKE 'pilot:%'
-- user_type='real' : u.staff_id NOT LIKE 'pilot:%'
```

### M1 核心 KPI 新增字段

```sql
-- uv（周期内有埋点的活跃用户）
SELECT COUNT(DISTINCT e.user_id)
FROM events e JOIN users u ON u.id = e.user_id
WHERE e.created_at >= :start
  AND (:user_type = 'all'
       OR (:user_type = 'pilot' AND u.staff_id LIKE 'pilot:%')
       OR (:user_type = 'real'  AND u.staff_id NOT LIKE 'pilot:%'));

-- feedback_count
SELECT COUNT(*) FROM feedbacks f
JOIN users u ON u.id = f.user_id
WHERE f.created_at >= :start
  AND (:user_type = 'all' OR ...);

-- unanswered_feedback_count
SELECT COUNT(*) FROM unanswered_user_feedback uuf
JOIN users u ON u.id = uuf.user_id
WHERE uuf.created_at >= :start
  AND (:user_type = 'all' OR ...);

-- ai_no_answer_count + total（一次扫表）
SELECT
  COUNT(*) FILTER (WHERE ca.is_answered = false) AS no_ans,
  COUNT(*)                                       AS total
FROM chat_analytics ca
JOIN users u ON u.id = ca.user_id
WHERE ca.created_at >= :start
  AND (:user_type = 'all' OR ...);

-- pilot_user_count / real_user_count（始终返回，与 user_type 过滤无关）
SELECT
  COUNT(DISTINCT u.id) FILTER (WHERE u.staff_id LIKE 'pilot:%')     AS pilot_users,
  COUNT(DISTINCT u.id) FILTER (WHERE u.staff_id NOT LIKE 'pilot:%') AS real_users
FROM users u
JOIN events e ON e.user_id = u.id
WHERE e.created_at >= :start;
```

### M2 漏斗

```sql
-- 5 步聚合（一次扫表）
SELECT
  e.event_name,
  COUNT(*)                AS hits,
  COUNT(DISTINCT e.user_id) AS users
FROM events e
JOIN users u ON u.id = e.user_id
WHERE e.created_at >= :start
  AND e.event_name IN (
    'page_view',
    'chat_send', 'chat_response_ok',
    'unanswered_card_shown', 'unanswered_card_submitted',
    'feedback_form_submit'
  )
  AND (:user_type = 'all' OR ...)
GROUP BY e.event_name;

-- page_view 需要进一步过滤为 page='home'，在 Python 端 reduce：
-- WHERE event_name='page_view' AND props->>'page' IN ('home', '/pages/home/index')
-- 提交合并：last_step.hits = unanswered_card_submitted.hits + feedback_form_submit.hits
```

### M3 服务热度

```sql
-- service_card_click Top 10
SELECT
  e.props->>'card'   AS card,
  e.props->>'source' AS source,
  COUNT(*)           AS count
FROM events e
JOIN users u ON u.id = e.user_id
WHERE e.event_name = 'service_card_click'
  AND e.created_at >= :start
  AND (:user_type = 'all' OR ...)
GROUP BY e.props->>'card', e.props->>'source'
ORDER BY count DESC
LIMIT 10;

-- quick_question_click Top 10
SELECT
  e.props->>'label' AS label,
  COUNT(*)          AS count
FROM events e
JOIN users u ON u.id = e.user_id
WHERE e.event_name = 'quick_question_click'
  AND e.created_at >= :start
  AND (:user_type = 'all' OR ...)
GROUP BY e.props->>'label'
ORDER BY count DESC
LIMIT 10;
```

### M4 未答交叉

```sql
-- by=college
SELECT
  uuf.user_provided_college_id            AS key,
  c.name                                  AS label,
  COUNT(*)                                AS total,
  COUNT(*) FILTER (
    WHERE uuf.user_provided_note IS NOT NULL
      AND length(trim(uuf.user_provided_note)) > 0
  )                                       AS with_note
FROM unanswered_user_feedback uuf
LEFT JOIN colleges c  ON c.id = uuf.user_provided_college_id
JOIN users    u  ON u.id = uuf.user_id
WHERE uuf.created_at >= :start
  AND (:user_type = 'all' OR ...)
GROUP BY uuf.user_provided_college_id, c.name
ORDER BY total DESC;

-- 每行 top_categories（与上一查询同组 GROUP BY 维度，Python 端拼到 row）
SELECT
  uuf.user_provided_college_id AS key,
  uuf.user_provided_category   AS category,
  COUNT(*)                     AS count
FROM unanswered_user_feedback uuf
JOIN users u ON u.id = uuf.user_id
WHERE uuf.created_at >= :start
  AND uuf.user_provided_category IS NOT NULL
  AND (:user_type = 'all' OR ...)
GROUP BY uuf.user_provided_college_id, uuf.user_provided_category;

-- by=grade（key=user_provided_grade，label=enum 中文映射在前端做）
-- by=category（key=user_provided_category）

-- by=college_x_category 二维 cell
SELECT
  uuf.user_provided_college_id AS college_id,
  uuf.user_provided_category   AS category,
  COUNT(*)                     AS count
FROM unanswered_user_feedback uuf
JOIN users u ON u.id = uuf.user_id
WHERE uuf.created_at >= :start
  AND uuf.user_provided_college_id IS NOT NULL
  AND uuf.user_provided_category   IS NOT NULL
  AND (:user_type = 'all' OR ...)
GROUP BY uuf.user_provided_college_id, uuf.user_provided_category;

-- unfilled 统计
SELECT
  COUNT(*) FILTER (WHERE uuf.user_provided_college_id IS NULL) AS no_college,
  COUNT(*) FILTER (WHERE uuf.user_provided_grade IS NULL)      AS no_grade,
  COUNT(*) FILTER (WHERE uuf.user_provided_category IS NULL)   AS no_category,
  COUNT(*)                                                     AS total
FROM unanswered_user_feedback uuf
JOIN users u ON u.id = uuf.user_id
WHERE uuf.created_at >= :start
  AND (:user_type = 'all' OR ...);
```

### M5 质量分布扩展

```sql
-- 延迟 p50/p95 + rag 平均
SELECT
  percentile_cont(0.5) WITHIN GROUP (ORDER BY ca.latency)  AS p50,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY ca.latency) AS p95,
  AVG(ca.rag_score)                                        AS rag_avg
FROM chat_analytics ca
JOIN users u ON u.id = ca.user_id
WHERE ca.created_at >= :start
  AND ca.latency IS NOT NULL
  AND (:user_type = 'all' OR ...);

-- feedback_after_no_answer_rate（Python 端做除法）
-- 分母 = M1 ai_no_answer_count
-- 分子 = M1 unanswered_feedback_count
```

### M6 成本概要扩展 + drill

```sql
-- cost_per_resolved / cost_per_question
SELECT
  SUM(ca.total_price)                       AS total_price,
  COUNT(*) FILTER (WHERE ca.is_answered)    AS answered,
  COUNT(*)                                  AS total
FROM chat_analytics ca
JOIN users u ON u.id = ca.user_id
WHERE ca.created_at >= :start
  AND ca.total_price IS NOT NULL
  AND (:user_type = 'all' OR ...);

-- by=conv Top N
SELECT
  ca.conversation_id,
  MIN(ca.user_id)                                       AS user_id,
  bool_or(u.staff_id LIKE 'pilot:%')                    AS is_pilot,
  SUM(ca.total_tokens)                                  AS tokens,
  SUM(ca.total_price)                                   AS price,
  COUNT(*)                                              AS calls
FROM chat_analytics ca
JOIN users u ON u.id = ca.user_id
WHERE ca.created_at >= :start
  AND ca.total_price IS NOT NULL
  AND (:user_type = 'all' OR ...)
GROUP BY ca.conversation_id
ORDER BY price DESC NULLS LAST
LIMIT :limit;

-- by=user Top N
SELECT
  ca.user_id,
  (u.staff_id LIKE 'pilot:%')         AS is_pilot,
  COALESCE(u.name, u.staff_id)        AS display_name,
  SUM(ca.total_tokens)                AS tokens,
  SUM(ca.total_price)                 AS price,
  COUNT(*)                            AS calls
FROM chat_analytics ca
JOIN users u ON u.id = ca.user_id
WHERE ca.created_at >= :start
  AND ca.total_price IS NOT NULL
  AND (:user_type = 'all' OR ...)
GROUP BY ca.user_id, u.staff_id, u.name
ORDER BY price DESC NULLS LAST
LIMIT :limit;
```

---

## 5. ECharts 集成方案

### 5.1 安装

```bash
cd apps/teacher-app
npm install echarts@^5.5.0
```

包体（按需 import 后 gzip）：
- core + Bar + Line + Funnel + Heatmap + Gauge + Pie ≈ 100KB
- 加 GridComponent + Tooltip + Legend + VisualMap + DataZoom ≈ +30KB
- **总计 ~130KB gzip**，在 PC 网络下可接受

### 5.2 统一入口

新建 `apps/teacher-app/src/utils/echarts.ts`：

```ts
import * as echarts from 'echarts/core'
import {
  BarChart, LineChart, FunnelChart, HeatmapChart, GaugeChart, PieChart,
} from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  VisualMapComponent, DataZoomComponent, MarkLineComponent,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'

echarts.use([
  BarChart, LineChart, FunnelChart, HeatmapChart, GaugeChart, PieChart,
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  VisualMapComponent, DataZoomComponent, MarkLineComponent,
  CanvasRenderer,
])

export default echarts
```

### 5.3 Vue3 组件封装（薄封装）

新建 `apps/teacher-app/src/components/EChart.vue`：传入 `option` + 容器尺寸，内部 `init / setOption / dispose / resize`。

### 5.4 PC vs 移动端的图表回退策略

```vue
<template>
  <view v-if="isPC" class="chart-pc">
    <EChart :option="funnelOption" />
  </view>
  <view v-else class="chart-mobile">
    <!-- 现有 SCSS bar 实现作为 fallback -->
  </view>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
const isPC = ref(false)
const updateBP = () => { isPC.value = window.innerWidth >= 1024 }
onMounted(() => { updateBP(); window.addEventListener('resize', updateBP) })
onBeforeUnmount(() => window.removeEventListener('resize', updateBP))
</script>
```

uni-app 编译到小程序时 `window` 不存在 → `import.meta.env.MODE` + `#ifdef H5` 条件编译保护；本面板**仅在 H5 端用**。

---

## 6. 横版布局规格（PC ≥1024px）

CSS Grid 12 列：

```scss
@media (min-width: 1024px) {
  .analytics-page {
    max-width: 1440px;
    margin: 0 auto;
    padding: 24px 32px;
  }

  .metrics-grid          { grid-template-columns: repeat(6, 1fr); }
  .row-funnel-services   { display: grid; grid-template-columns: 6fr 6fr; gap: 24px; }
  .row-cross-quality     { display: grid; grid-template-columns: 7fr 5fr; gap: 24px; }
  .row-cost              { grid-template-columns: 1fr; }

  .section-card { min-height: 360px; padding: 24px; }
}
```

H5 端（< 1024px）：grid 全部塌成单列，沿用现有 `@/Users/Administrator/Documents/code/yixiaoguan-v2/apps/teacher-app/src/pages/analytics/index.vue:505-1144` SCSS。

顶栏新增：
- `user_type` segmented control（全部 / 内测 / 真实）
- 右上角"上次更新 18:12 ⟲"刷新按钮
- 当前 period chip 沿用

---

## 7. 实施任务拆分

| Sub-task | 入口文件 | 工时 | 依赖 |
|----------|---------|------|------|
| **B1** 后端 fat endpoint 加 4 block + `user_type` 参数 | `services/gateway/app/routers/analytics.py` | 3h | 无 |
| **B2** 新端点 `/api/analytics/unanswered-cross` | 同上（拆 sub-router 或同文件） | 2h | 无 |
| **B3** 新端点 `/api/analytics/cost-detail` | 同上 | 1.5h | 无 |
| **B4** 单元测试（fixture + 各 block 断言） | `services/gateway/tests/test_analytics_bi.py` | 2h | B1-B3 |
| **F1** `npm install echarts` + 统一入口 + EChart 组件 | `apps/teacher-app/src/utils/echarts.ts` + `components/EChart.vue` | 1.5h | 无 |
| **F2** PC 响应式 grid 布局重构 | `apps/teacher-app/src/pages/analytics/index.vue` | 3h | F1 |
| **F3** M1+M2+M3 三模块前端 | 同上 + `api/analytics.ts` 类型扩展 | 4h | B1, F1, F2 |
| **F4** M4 未答交叉（含 4 tab 切换） | 同上 | 3h | B2, F1, F2 |
| **F5** M5 质量分布扩展 + M6 成本明细扩展 | 同上 | 3h | B1, B3, F1, F2 |
| **F6** mock fixture（无数据时 fallback） | 同上 | 1h | F3-F5 |
| **F7** PC 横版视觉打磨（间距/配色/动画） | 同上 SCSS 段 | 2h | F3-F5 |

**总工时**: ~26h（后端 ~8.5h + 前端 ~17.5h），单人 3-4 天，并行 2 人 1.5-2 天。

---

## 8. 验收（L0-L3）

| 层级 | 标准 |
|------|------|
| L0 | 文件 / 端点 / 字段全部存在 |
| L1 | ruff + mypy + alembic 语法过；现有 `/api/analytics` 不回归 |
| L2 | pytest 新增单测全过；远端 curl 各端点返回结构正确；ECharts 渲染无 console error |
| L3 | PC 浏览器（1920×1080 / 1366×768）+ H5 手机（375×667）双端打开均正确显示；user_type toggle 切换数据正确变化；6 模块均能在内测真实数据上呈现非零值 |

---

## 9. 风险 & 缓解

| 风险 | 严重度 | 缓解 |
|------|------|------|
| ECharts 在 uni-app H5 SSR / hydration 报错 | 🟡 中 | 用 `defineAsyncComponent` + `if (process.client)` 守护；fallback 到 SCSS |
| `events` 表数据量大 SQL 慢 | 🟡 中 | `idx_events_name_day`(已有) 覆盖大部分查询；M2 漏斗用 `event_name IN (...)` 走 index |
| pilot vs real 切换时数据剧烈波动迷惑用户 | 🟢 低 | 顶栏 toggle 加一行小字"内测数据仅供调试，正式版前清理" |
| 包体超 150KB gzip | 🟢 低 | 已按需 import；如超出可拆 PC 路由级 lazy load |
| 横版断点 1024px 在 iPad 横屏触发但缺 hover | 🟢 低 | 关键交互不依赖 hover（tooltip 同时支持 click） |

---

## 10. 后续可选 Tier 2 / Tier 3（不在本轮范围）

- **Tier 2**: 165 上 `docker run metabase/metabase` + 只读 Postgres 账号，给 TX 做自由 SQL 分析（不开发）
- **Tier 3**: 企业微信机器人定时推日报 / 周报（cron + webhook）

---

## 变更日志

| 日期 | 变更 | 作者 |
|------|------|------|
| 2026-05-08 19:50 | 首版（基于 master-plan §D-P2-1 + handoff doc，校正字段名） | Cascade |
