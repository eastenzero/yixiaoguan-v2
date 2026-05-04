<template>
  <view class="analytics-page">
    <!-- ── App Bar ── -->
    <view class="custom-app-bar">
      <view class="app-bar-content">
        <view class="app-bar-left" @click="goBack">
          <text class="material-symbols-outlined app-bar-icon">arrow_back</text>
          <text class="app-bar-title">数据看板</text>
        </view>
      </view>
    </view>

    <!-- ── Main Scroll ── -->
    <scroll-view scroll-y class="main-scroll">
      <!-- Period Selector -->
      <view class="period-row">
        <view
          v-for="p in periods"
          :key="p.value"
          class="period-chip"
          :class="{ active: period === p.value }"
          @click="changePeriod(p.value)"
        >
          <text class="period-chip-text">{{ p.label }}</text>
        </view>
      </view>

      <!-- Loading -->
      <view v-if="loading" class="loading-wrap">
        <text class="material-symbols-outlined loading-spin">progress_activity</text>
        <text class="loading-text">正在加载数据…</text>
      </view>

      <template v-if="!loading && data">
        <!-- ── 1. Metric Cards ── -->
        <view class="metrics-grid animate-fade-up">
          <view
            v-for="m in metricCards"
            :key="m.key"
            class="metric-card"
            :class="'metric-card--' + m.color"
          >
            <view class="metric-top">
              <view class="metric-icon-wrap" :class="'icon-bg--' + m.color">
                <text class="material-symbols-outlined metric-icon">{{ m.icon }}</text>
              </view>
              <view v-if="m.change !== null" class="metric-change" :class="m.dir">
                <text class="material-symbols-outlined change-arrow">{{ m.dir === 'up' ? 'trending_up' : 'trending_down' }}</text>
                <text class="change-pct">{{ m.change }}%</text>
              </view>
            </view>
            <text class="metric-value">{{ m.display }}</text>
            <text class="metric-label">{{ m.label }}</text>
          </view>
        </view>

        <!-- ── 2. Trend Chart ── -->
        <view class="section-card animate-fade-up">
          <view class="section-header-row">
            <text class="section-title">提问趋势</text>
            <view class="legend-row">
              <view class="legend-item"><view class="legend-dot dot--total"></view><text class="legend-text">总提问</text></view>
              <view class="legend-item"><view class="legend-dot dot--ai"></view><text class="legend-text">AI 解答</text></view>
            </view>
          </view>
          <view v-if="trendMax === 0" class="empty-chart">
            <text class="empty-chart-text">暂无趋势数据</text>
          </view>
          <scroll-view v-else scroll-x class="trend-scroll" :show-scrollbar="false">
            <view class="trend-chart" :style="{ width: trendChartWidth }">
              <!-- Y gridlines -->
              <view class="y-grid">
                <view v-for="t in yTicks" :key="t" class="y-line" :style="{ bottom: (t / trendMax * 100) + '%' }">
                  <text class="y-label">{{ t }}</text>
                </view>
              </view>
              <!-- Bars -->
              <view class="bar-area">
                <view v-for="(d, i) in trendItems" :key="i" class="bar-group">
                  <view class="bar-stack">
                    <view class="bar bar--ai" :style="{ height: barH(d.ai) }"></view>
                    <view class="bar bar--rest" :style="{ height: barH(d.total - d.ai) }"></view>
                  </view>
                  <text class="bar-date">{{ d.shortDate }}</text>
                </view>
              </view>
            </view>
          </scroll-view>
        </view>

        <!-- ── 3. AI Quality ── -->
        <view class="section-card animate-fade-up">
          <text class="section-title">AI 质量分析</text>
          <view class="ai-quality-row">
            <!-- Ring -->
            <view class="ring-wrap">
              <view class="ring" :style="ringStyle">
                <view class="ring-inner">
                  <text class="ring-value">{{ data.ai_quality.hit_rate }}%</text>
                  <text class="ring-label">命中率</text>
                </view>
              </view>
            </view>
            <!-- Score Distribution -->
            <view class="score-bars">
              <view class="score-row">
                <text class="score-label">优</text>
                <view class="score-track"><view class="score-fill fill--high" :style="{ width: scorePct('high') }"></view></view>
                <text class="score-num">{{ data.ai_quality.score_high }}</text>
              </view>
              <view class="score-row">
                <text class="score-label">中</text>
                <view class="score-track"><view class="score-fill fill--mid" :style="{ width: scorePct('mid') }"></view></view>
                <text class="score-num">{{ data.ai_quality.score_mid }}</text>
              </view>
              <view class="score-row">
                <text class="score-label">低</text>
                <view class="score-track"><view class="score-fill fill--low" :style="{ width: scorePct('low') }"></view></view>
                <text class="score-num">{{ data.ai_quality.score_low }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- ── 4. Hot Unanswered ── -->
        <view class="section-card animate-fade-up">
          <text class="section-title">热门未解答 Top 5</text>
          <view v-if="data.hot_unanswered.length === 0" class="empty-chart">
            <text class="empty-chart-text">暂无未解答问题</text>
          </view>
          <view v-else class="hot-list">
            <view v-for="(q, idx) in data.hot_unanswered" :key="q.id" class="hot-item">
              <view class="hot-rank" :class="'rank--' + (idx + 1)">
                <text class="rank-text">{{ idx + 1 }}</text>
              </view>
              <text class="hot-text">{{ q.text }}</text>
              <view class="hot-count-badge">
                <text class="hot-count">{{ q.count }}次</text>
              </view>
            </view>
          </view>
        </view>

        <!-- ── 5. College Distribution ── -->
        <view class="section-card animate-fade-up">
          <text class="section-title">学院提问分布</text>
          <view v-if="data.college_distribution.length === 0" class="empty-chart">
            <text class="empty-chart-text">暂无学院数据</text>
          </view>
          <view v-else class="college-bars">
            <view v-for="c in data.college_distribution" :key="c.name" class="college-row">
              <text class="college-name">{{ c.name }}</text>
              <view class="college-track">
                <view class="college-fill" :style="{ width: collegePct(c.count) }"></view>
              </view>
              <text class="college-num">{{ c.count }}</text>
            </view>
          </view>
        </view>

        <!-- ── 6. Heatmap ── -->
        <view class="section-card animate-fade-up">
          <text class="section-title">提问时段分布</text>
          <scroll-view scroll-x class="heatmap-scroll" :show-scrollbar="false">
            <view class="heatmap-wrap">
              <!-- Hour labels -->
              <view class="hm-header">
                <view class="hm-day-label"></view>
                <text v-for="h in hourLabels" :key="h" class="hm-hour">{{ h }}</text>
              </view>
              <!-- Rows -->
              <view v-for="(row, d) in heatmapRows" :key="d" class="hm-row">
                <text class="hm-day-label">{{ dayLabels[d] }}</text>
                <view
                  v-for="(val, h) in row"
                  :key="h"
                  class="hm-cell"
                  :style="{ opacity: heatOpacity(val) }"
                ></view>
              </view>
              <!-- Legend -->
              <view class="hm-legend">
                <text class="hm-legend-text">少</text>
                <view class="hm-legend-cell" style="opacity:0.08"></view>
                <view class="hm-legend-cell" style="opacity:0.25"></view>
                <view class="hm-legend-cell" style="opacity:0.50"></view>
                <view class="hm-legend-cell" style="opacity:0.75"></view>
                <view class="hm-legend-cell" style="opacity:1"></view>
                <text class="hm-legend-text">多</text>
              </view>
            </view>
          </scroll-view>
        </view>

        <!-- bottom spacer -->
        <view style="height: 40px"></view>
      </template>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getAnalytics } from '@/api/analytics'
import type { AnalyticsData } from '@/api/analytics'

const period = ref<'7d' | '30d' | 'all'>('7d')
const periods = [
  { value: '7d', label: '近 7 天' },
  { value: '30d', label: '近 30 天' },
  { value: 'all', label: '全部' },
]
const loading = ref(false)
const data = ref<AnalyticsData | null>(null)

const goBack = () => uni.navigateBack()

async function load() {
  loading.value = true
  try {
    data.value = await getAnalytics(period.value)
  } catch (e) {
    console.error('Analytics load error', e)
  } finally {
    loading.value = false
  }
}

function changePeriod(p: string) {
  period.value = p as any
  load()
}

onMounted(load)

// ── 1. Metric cards ──

function pctChange(cur: number, prev: number): { change: string; dir: string } | { change: null } {
  if (!prev) return { change: null }
  const diff = ((cur - prev) / prev) * 100
  return { change: Math.abs(diff).toFixed(1), dir: diff >= 0 ? 'up' : 'down' }
}

const metricCards = computed(() => {
  if (!data.value) return []
  const m = data.value.metrics
  return [
    {
      key: 'total', icon: 'query_stats', label: '总提问', color: 'violet',
      display: m.total_questions, ...pctChange(m.total_questions, m.total_questions_prev),
    },
    {
      key: 'ai', icon: 'smart_toy', label: 'AI 解答率', color: 'blue',
      display: m.ai_rate + '%', ...pctChange(m.ai_rate, m.ai_rate_prev),
    },
    {
      key: 'resp', icon: 'schedule', label: '平均响应', color: 'emerald',
      display: m.avg_response_min > 0 ? m.avg_response_min + ' 分' : '-',
      ...pctChange(m.avg_response_min_prev, m.avg_response_min),  // reversed: lower is better
    },
    {
      key: 'pending', icon: 'pending_actions', label: '待处理', color: 'amber',
      display: m.pending_count, change: null,
    },
  ]
})

// ── 2. Trend ──

const trendItems = computed(() => {
  if (!data.value) return []
  const t = data.value.trends
  return t.dates.map((d, i) => ({
    total: t.total[i],
    ai: t.ai_answered[i],
    shortDate: d.slice(5),   // MM-DD
  }))
})

const trendMax = computed(() => {
  const vals = trendItems.value.map(d => d.total)
  return Math.max(...vals, 1)
})

const yTicks = computed(() => {
  const max = trendMax.value
  if (max <= 5) return [1, 2, 3, 4, 5].filter(v => v <= max)
  const step = Math.ceil(max / 4)
  return [step, step * 2, step * 3, step * 4].filter(v => v <= max * 1.2)
})

const trendChartWidth = computed(() => {
  const count = trendItems.value.length
  return Math.max(count * 44, 300) + 'px'
})

function barH(val: number): string {
  if (!val || trendMax.value === 0) return '0%'
  return (val / trendMax.value * 100) + '%'
}

// ── 3. AI Quality ──

const ringStyle = computed(() => {
  const pct = data.value?.ai_quality.hit_rate ?? 0
  return {
    background: `conic-gradient(#5b21b6 0% ${pct}%, #ede9fe ${pct}% 100%)`,
  }
})

function scorePct(level: 'high' | 'mid' | 'low'): string {
  if (!data.value) return '0%'
  const q = data.value.ai_quality
  const total = q.score_low + q.score_mid + q.score_high
  if (!total) return '0%'
  const map = { high: q.score_high, mid: q.score_mid, low: q.score_low }
  return (map[level] / total * 100) + '%'
}

// ── 5. College ──

const collegeMax = computed(() => {
  if (!data.value) return 1
  return Math.max(...data.value.college_distribution.map(c => c.count), 1)
})

function collegePct(count: number): string {
  return (count / collegeMax.value * 100) + '%'
}

// ── 6. Heatmap ──

const dayLabels = ['日', '一', '二', '三', '四', '五', '六']
const hourLabels = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0'))

const heatmapRows = computed(() => data.value?.heatmap ?? Array.from({ length: 7 }, () => new Array(24).fill(0)))

const heatmapMax = computed(() => {
  let max = 0
  for (const row of heatmapRows.value)
    for (const v of row)
      if (v > max) max = v
  return max || 1
})

function heatOpacity(val: number): number {
  if (!val) return 0.06
  return 0.15 + (val / heatmapMax.value) * 0.85
}
</script>

<style lang="scss">
@import '@/styles/tokens.scss';

.analytics-page {
  min-height: 100vh;
  background: $surface;
  display: flex;
  flex-direction: column;
}

// ── App Bar ──

.custom-app-bar {
  background: $surface;
  padding-top: env(safe-area-inset-top);
  position: sticky;
  top: 0;
  z-index: 100;
}
.app-bar-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px $space-4;
}
.app-bar-left {
  display: flex;
  align-items: center;
  gap: 8px;
}
.app-bar-icon {
  font-size: 22px;
  color: $on-surface;
}
.app-bar-title {
  font-size: 18px;
  font-weight: 700;
  color: $on-surface;
}

// ── Main Scroll ──

.main-scroll {
  flex: 1;
  padding: 0 $space-4;
}

// ── Period Selector ──

.period-row {
  display: flex;
  gap: 8px;
  margin: 12px 0 16px;
}
.period-chip {
  padding: 6px 16px;
  border-radius: 9999px;
  background: $surface-container-low;
  transition: all 0.25s ease;
}
.period-chip.active {
  background: $primary;
  box-shadow: 0 2px 8px rgba(91, 33, 182, 0.25);
}
.period-chip-text {
  font-size: 13px;
  font-weight: 500;
  color: $on-surface-variant;
}
.period-chip.active .period-chip-text {
  color: #fff;
}

// ── Loading ──

.loading-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 0;
  gap: 12px;
}
.loading-spin {
  font-size: 36px;
  color: $primary;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { font-size: 14px; color: $on-surface-variant; }

// ── Animations ──

.animate-fade-up {
  animation: fadeUp 0.45s ease both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(18px); }
  to   { opacity: 1; transform: translateY(0); }
}

// ── Empty chart ──

.empty-chart {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 0;
}
.empty-chart-text {
  font-size: 13px;
  color: $on-surface-variant;
}

// ══════════════════════════════════════
// 1. Metric Cards
// ══════════════════════════════════════

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}
.metric-card {
  background: $surface-container-lowest;
  border-radius: $radius-md;
  padding: 16px;
  box-shadow: $elevation-1;
  display: flex;
  flex-direction: column;
  gap: 4px;
  position: relative;
  overflow: hidden;
}
// subtle gradient accent at top
.metric-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  border-radius: $radius-md $radius-md 0 0;
}
.metric-card--violet::before { background: linear-gradient(90deg, #5b21b6, #8b5cf6); }
.metric-card--blue::before   { background: linear-gradient(90deg, #2563eb, #60a5fa); }
.metric-card--emerald::before{ background: linear-gradient(90deg, #059669, #34d399); }
.metric-card--amber::before  { background: linear-gradient(90deg, #d97706, #fbbf24); }

.metric-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.metric-icon-wrap {
  width: 36px; height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.icon-bg--violet { background: rgba(91, 33, 182, 0.10); }
.icon-bg--blue   { background: rgba(37, 99, 235, 0.10); }
.icon-bg--emerald{ background: rgba(5, 150, 105, 0.10); }
.icon-bg--amber  { background: rgba(217, 119, 6, 0.10); }

.metric-icon {
  font-size: 20px;
}
.metric-card--violet .metric-icon { color: #5b21b6; }
.metric-card--blue   .metric-icon { color: #2563eb; }
.metric-card--emerald .metric-icon { color: #059669; }
.metric-card--amber  .metric-icon { color: #d97706; }

.metric-change {
  display: flex;
  align-items: center;
  gap: 2px;
  padding: 2px 6px;
  border-radius: 6px;
  font-size: 11px;
}
.metric-change.up {
  background: rgba(5, 150, 105, 0.10);
  .change-arrow, .change-pct { color: #059669; }
}
.metric-change.down {
  background: rgba(220, 38, 38, 0.10);
  .change-arrow, .change-pct { color: #dc2626; }
}
.change-arrow { font-size: 14px; }
.change-pct   { font-size: 11px; font-weight: 600; }

.metric-value {
  font-size: 28px;
  font-weight: 800;
  color: $on-surface;
  letter-spacing: -0.5px;
  margin-top: 4px;
}
.metric-label {
  font-size: 12px;
  color: $on-surface-variant;
  font-weight: 500;
}

// ══════════════════════════════════════
// Section Card (shared)
// ══════════════════════════════════════

.section-card {
  background: $surface-container-lowest;
  border-radius: $radius-md;
  padding: 20px 16px;
  box-shadow: $elevation-1;
  margin-bottom: 16px;
}
.section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.section-title {
  font-size: 16px;
  font-weight: 700;
  color: $on-surface;
  margin-bottom: 16px;
}
.section-header-row .section-title {
  margin-bottom: 0;
}

// ══════════════════════════════════════
// 2. Trend Chart
// ══════════════════════════════════════

.legend-row { display: flex; gap: 12px; }
.legend-item { display: flex; align-items: center; gap: 4px; }
.legend-dot {
  width: 8px; height: 8px; border-radius: 2px;
}
.dot--total { background: #5b21b6; }
.dot--ai    { background: #ddd6fe; }
.legend-text { font-size: 11px; color: $on-surface-variant; }

.trend-scroll { margin-top: 4px; }
.trend-chart {
  position: relative;
  height: 180px;
  padding-left: 32px;
}
.y-grid {
  position: absolute;
  left: 0; top: 0; bottom: 24px; right: 0;
}
.y-line {
  position: absolute;
  left: 0; right: 0;
  border-bottom: 1px dashed rgba(91, 33, 182, 0.08);
}
.y-label {
  position: absolute;
  left: 0;
  bottom: 2px;
  font-size: 10px;
  color: $on-surface-variant;
  width: 28px;
  text-align: right;
}

.bar-area {
  position: absolute;
  left: 36px; right: 0; top: 0; bottom: 0;
  display: flex;
  align-items: flex-end;
  gap: 2px;
  padding-bottom: 24px;
}
.bar-group {
  flex: 1;
  min-width: 28px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.bar-stack {
  width: 16px;
  display: flex;
  flex-direction: column-reverse;
  border-radius: 4px 4px 0 0;
  overflow: hidden;
}
.bar {
  width: 100%;
  min-height: 0;
  transition: height 0.5s cubic-bezier(0.22, 1, 0.36, 1);
}
.bar--ai   { background: #5b21b6; }
.bar--rest { background: #ddd6fe; }

.bar-date {
  font-size: 9px;
  color: $on-surface-variant;
  margin-top: 4px;
  white-space: nowrap;
}

// ══════════════════════════════════════
// 3. AI Quality
// ══════════════════════════════════════

.ai-quality-row {
  display: flex;
  align-items: center;
  gap: 20px;
}

.ring-wrap {
  flex-shrink: 0;
}
.ring {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.ring-inner {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: $surface-container-lowest;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.ring-value {
  font-size: 20px;
  font-weight: 800;
  color: #5b21b6;
  line-height: 1;
}
.ring-label {
  font-size: 10px;
  color: $on-surface-variant;
  margin-top: 2px;
}

.score-bars {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.score-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.score-label {
  font-size: 12px;
  font-weight: 600;
  color: $on-surface-variant;
  width: 18px;
  text-align: center;
}
.score-track {
  flex: 1;
  height: 10px;
  background: rgba(91, 33, 182, 0.06);
  border-radius: 5px;
  overflow: hidden;
}
.score-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}
.fill--high { background: linear-gradient(90deg, #5b21b6, #7c3aed); }
.fill--mid  { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
.fill--low  { background: linear-gradient(90deg, #c4b5fd, #ddd6fe); }

.score-num {
  font-size: 12px;
  font-weight: 600;
  color: $on-surface;
  width: 28px;
  text-align: right;
}

// ══════════════════════════════════════
// 4. Hot Unanswered
// ══════════════════════════════════════

.hot-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.hot-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: $surface-container-low;
  border-radius: 12px;
  transition: background 0.2s;
}
.hot-rank {
  width: 24px; height: 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.rank-text {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}
.rank--1 { background: linear-gradient(135deg, #5b21b6, #7c3aed); }
.rank--2 { background: linear-gradient(135deg, #7c3aed, #a78bfa); }
.rank--3 { background: linear-gradient(135deg, #a78bfa, #c4b5fd); }
.rank--4, .rank--5 {
  background: $surface-container;
  .rank-text { color: $on-surface-variant; }
}

.hot-text {
  flex: 1;
  font-size: 13px;
  color: $on-surface;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.hot-count-badge {
  background: rgba(91, 33, 182, 0.08);
  padding: 2px 8px;
  border-radius: 6px;
  flex-shrink: 0;
}
.hot-count {
  font-size: 11px;
  font-weight: 600;
  color: #5b21b6;
}

// ══════════════════════════════════════
// 5. College Distribution
// ══════════════════════════════════════

.college-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.college-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.college-name {
  font-size: 12px;
  color: $on-surface;
  width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: right;
  flex-shrink: 0;
}
.college-track {
  flex: 1;
  height: 12px;
  background: rgba(91, 33, 182, 0.06);
  border-radius: 6px;
  overflow: hidden;
}
.college-fill {
  height: 100%;
  border-radius: 6px;
  background: linear-gradient(90deg, #5b21b6, #a78bfa);
  transition: width 0.6s cubic-bezier(0.22, 1, 0.36, 1);
}
.college-num {
  font-size: 12px;
  font-weight: 600;
  color: $on-surface;
  width: 32px;
  flex-shrink: 0;
}

// ══════════════════════════════════════
// 6. Heatmap
// ══════════════════════════════════════

.heatmap-scroll { margin-top: 4px; }
.heatmap-wrap {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 560px;
}
.hm-header, .hm-row {
  display: flex;
  align-items: center;
  gap: 3px;
}
.hm-day-label {
  width: 20px;
  font-size: 10px;
  color: $on-surface-variant;
  text-align: center;
  flex-shrink: 0;
}
.hm-hour {
  flex: 1;
  min-width: 18px;
  font-size: 9px;
  color: $on-surface-variant;
  text-align: center;
}
.hm-cell {
  flex: 1;
  min-width: 18px;
  height: 18px;
  border-radius: 3px;
  background: #5b21b6;
  transition: opacity 0.3s;
}

.hm-legend {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 4px;
  margin-top: 8px;
  padding-right: 4px;
}
.hm-legend-text {
  font-size: 10px;
  color: $on-surface-variant;
}
.hm-legend-cell {
  width: 14px;
  height: 14px;
  border-radius: 2px;
  background: #5b21b6;
}
</style>
