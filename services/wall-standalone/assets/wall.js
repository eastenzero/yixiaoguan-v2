/* ════════════════════════════════════════════════════════════════
 * 医小管 · 内测大屏 · 主脚本
 *   1. 时钟实时跳秒 (1s)
 *   2. 数据 fetch /wall/data.json (load + 5min 轮询)
 *   3. KPI count-up + funnel 条 + ECharts 折线 + ticker 滚动
 *   4. 离线兜底: 顶部右上角红色提示, 不白屏
 * ════════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  // ── 配置 ─────────────────────────────────────────────────
  const DATA_URL = 'data.json';                  // 与 index.html 同目录
  const FETCH_INTERVAL = 5 * 60 * 1000;          // 5 分钟
  const COUNT_UP_DUR = 800;                      // KPI 数字滚动时长 ms

  // 紫绛 / 朱红 / 冷金 — 折线配色 (与 BI 画报一致)
  const CHART_COLORS = ['#5B1F5B', '#A23130', '#A98B4F'];

  // ── DOM 缓存 ─────────────────────────────────────────────
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const elDayNum = $('#dayNum');
  const elClockTime = $('#clockTime');
  const elClockDate = $('#clockDate');
  const elLive = $('#liveBadge');
  const elFunnel = $('#funnelList');
  const elTicker = $('#tickerTrack');
  const elUpdated = $('#updatedAt');
  const elFootYear = $('#footYear');
  const elOffline = $('#offlineNote');
  const elDailyChart = $('#dailyChart');

  // ── 工具 ─────────────────────────────────────────────────
  const pad2 = (n) => String(n).padStart(2, '0');

  function formatClock(d) {
    return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`;
  }
  function formatDate(d) {
    const wd = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'][d.getDay()];
    return `${d.getFullYear()}.${pad2(d.getMonth() + 1)}.${pad2(d.getDate())} · ${wd}`;
  }
  function formatUpdated(iso) {
    if (!iso) return '—';
    try {
      const d = new Date(iso);
      return `${pad2(d.getHours())}:${pad2(d.getMinutes())}:${pad2(d.getSeconds())}`;
    } catch (e) {
      return '—';
    }
  }

  // 数字 count-up 动画
  function countUp(el, target, duration) {
    const start = parseInt(el.textContent, 10) || 0;
    if (start === target) return;
    const t0 = performance.now();
    function step(now) {
      const p = Math.min(1, (now - t0) / duration);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - p, 3);
      const cur = Math.round(start + (target - start) * eased);
      el.textContent = cur;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // ── 时钟 (独立, 每秒) ────────────────────────────────────
  function tickClock() {
    const now = new Date();
    elClockTime.textContent = formatClock(now);
    elClockDate.textContent = formatDate(now);
    elFootYear.textContent = now.getFullYear();
  }
  tickClock();
  setInterval(tickClock, 1000);

  // ── ECharts 折线 ─────────────────────────────────────────
  let chart = null;

  function initChart() {
    if (typeof echarts === 'undefined') {
      console.warn('ECharts not loaded');
      return;
    }
    chart = echarts.init(elDailyChart, null, { renderer: 'svg' });
    window.addEventListener('resize', () => chart && chart.resize());
  }

  function renderChart(daily) {
    if (!chart) return;
    const days = (daily || []).map(r => r.day);
    const opt = {
      grid: { left: 40, right: 20, top: 30, bottom: 30, containLabel: true },
      legend: {
        top: 0,
        right: 10,
        textStyle: { color: '#5B1F5B', fontFamily: 'Inter, sans-serif', fontSize: 12 },
        itemGap: 18,
      },
      tooltip: {
        trigger: 'axis',
        confine: true,                       /* 不超出图表容器 */
        backgroundColor: '#FBF8F1',
        borderColor: '#C5A977',
        borderWidth: 1,
        textStyle: { color: '#1F1A24', fontFamily: 'Inter, "Noto Serif SC", sans-serif', fontSize: 12 },
        padding: [6, 10],
      },
      toolbox: { show: false },              /* 显式禁用 (有些浏览器扩展会注入 Save/Download 按钮) */
      xAxis: {
        type: 'category',
        data: days,
        boundaryGap: false,
        axisLine: { lineStyle: { color: '#C5A977' } },
        axisTick: { show: false },
        axisLabel: {
          color: '#6B6470',
          fontFamily: 'Inter, sans-serif',
          fontSize: 11,
        },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: '#D9CDB6', type: 'dashed' } },
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: {
          color: '#9C9099',
          fontFamily: 'Inter, sans-serif',
          fontSize: 11,
        },
      },
      color: CHART_COLORS,
      series: [
        {
          name: '提问',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          data: (daily || []).map(r => r.asked),
          lineStyle: { width: 2.5 },
          itemStyle: { color: CHART_COLORS[0] },
        },
        {
          name: 'AI 已答',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          data: (daily || []).map(r => r.answered),
          lineStyle: { width: 2.5 },
          itemStyle: { color: CHART_COLORS[1] },
        },
        {
          name: '活跃用户',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 7,
          data: (daily || []).map(r => r.active),
          lineStyle: { width: 2.5 },
          itemStyle: { color: CHART_COLORS[2] },
        },
      ],
    };
    chart.setOption(opt, true);
  }

  // ── 渲染 KPI ─────────────────────────────────────────────
  function renderKpis(kpis) {
    if (!kpis) return;
    $$('[data-kpi]').forEach(el => {
      const k = el.getAttribute('data-kpi');
      const v = parseInt(kpis[k], 10) || 0;
      countUp(el, v, COUNT_UP_DUR);
    });
  }

  // ── 渲染漏斗 ─────────────────────────────────────────────
  function renderFunnel(funnel) {
    if (!Array.isArray(funnel) || funnel.length === 0) {
      elFunnel.innerHTML = '<div class="wall-funnel-row"><div class="wall-funnel-step">暂无数据</div><div class="wall-funnel-bar-wrap"></div><div class="wall-funnel-num">—</div></div>';
      return;
    }
    const max = Math.max(1, ...funnel.map(r => r.cnt));
    elFunnel.innerHTML = funnel.map(r => {
      const w = Math.max(2, (r.cnt / max) * 100);
      return `
        <div class="wall-funnel-row">
          <div class="wall-funnel-step">${escapeHtml(r.step)}</div>
          <div class="wall-funnel-bar-wrap"><div class="wall-funnel-bar" style="width:${w.toFixed(1)}%"></div></div>
          <div class="wall-funnel-num">${r.cnt}</div>
        </div>`;
    }).join('');
  }

  // ── 渲染 ticker (双倍数据 + 无限滚动) ────────────────────
  function renderTicker(ticker) {
    if (!Array.isArray(ticker) || ticker.length === 0) {
      elTicker.innerHTML = '<div class="wall-ticker-item"><span class="wall-ticker-detail">暂无事件 · 等待学生提问</span></div>';
      return;
    }
    const items = ticker.map(e => {
      const detail = [
        e.role && e.role !== '—' ? e.role : '',
        e.college,
        e.detail,
      ].filter(Boolean).join(' · ');
      return `
        <div class="wall-ticker-item">
          <span class="wall-ticker-time">${escapeHtml(e.t)}</span>
          <span class="wall-ticker-event">[${escapeHtml(e.evt)}]</span>
          <span class="wall-ticker-detail">${escapeHtml(detail) || '—'}</span>
        </div>`;
    }).join('');
    // 双份 → 拼接无限滚 (CSS animation translateX -50%)
    elTicker.innerHTML = items + items;
  }

  function escapeHtml(s) {
    if (s == null) return '';
    return String(s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  // ── 数据 fetch ───────────────────────────────────────────
  async function loadData(showLoading) {
    try {
      const url = `${DATA_URL}?_=${Date.now()}`;   // bust cache
      const res = await fetch(url, { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const d = await res.json();
      applySnapshot(d);
      setOffline(false);
    } catch (err) {
      console.warn('[wall] fetch failed:', err);
      setOffline(true, String(err));
    }
  }

  function applySnapshot(d) {
    if (!d || typeof d !== 'object') return;

    if (d.day_num) elDayNum.textContent = d.day_num;
    elUpdated.textContent = formatUpdated(d.generated_at);

    renderKpis(d.kpis);
    renderFunnel(d.funnel);
    renderChart(d.daily);
    renderTicker(d.ticker);

    // 后端有 error 字段, 不当离线但提示
    if (d.error) {
      console.warn('[wall] backend reported error:', d.error);
      // 可选: 在 footer 加小标
    }
  }

  function setOffline(off, msg) {
    if (off) {
      elOffline.textContent = `数据离线 · ${msg || '等待重连'}`;
      elOffline.classList.add('show');
      elLive.classList.add('offline');
      elLive.textContent = 'OFFLINE';
    } else {
      elOffline.classList.remove('show');
      elLive.classList.remove('offline');
      elLive.textContent = 'LIVE';
    }
  }

  // ── 鼠标空闲隐藏 (大屏挂着的时候) ────────────────────────
  let idleTimer = null;
  function resetIdle() {
    document.body.classList.remove('idle');
    clearTimeout(idleTimer);
    idleTimer = setTimeout(() => document.body.classList.add('idle'), 5000);
  }
  window.addEventListener('mousemove', resetIdle);
  window.addEventListener('keydown', resetIdle);
  resetIdle();

  // ── 启动 ─────────────────────────────────────────────────
  initChart();
  loadData();
  setInterval(loadData, FETCH_INTERVAL);

  // 调试用
  window.__wall = {
    reload: () => loadData(),
    chart: () => chart,
  };
})();
