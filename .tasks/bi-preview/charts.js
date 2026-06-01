/* eslint-disable */
// Chart instances + interactions for BI preview
(function () {
  const M = window.MOCK;
  if (!window.echarts) {
    document.body.insertAdjacentHTML('afterbegin',
      '<div style="position:fixed;top:0;left:0;right:0;background:#fef3c7;color:#92400e;padding:8px;text-align:center;font-size:12px;z-index:9999">ECharts CDN 加载失败，请检查网络或下载 echarts.min.js 到本地</div>');
    return;
  }

  // ===== Theme palette =====
  // Project violet scale (Tailwind violet, matches student-app theme.scss)
  const PALETTE = {
    p50: '#f5f3ff', p100: '#ede9fe', p200: '#ddd6fe', p300: '#c4b5fd',
    p400: '#a78bfa', p500: '#8b5cf6', p600: '#7c3aed', p700: '#6d28d9',
    p800: '#5b21b6', p900: '#4c1d95',
    // Accents
    sky: '#0ea5e9', skyD: '#0284c7', emerald: '#10b981', emeraldD: '#059669',
    amber: '#f59e0b', amberD: '#d97706', rose: '#f43f5e', roseD: '#e11d48',
    pink: '#ec4899', fuchsia: '#c026d3', fuchsiaD: '#a21caf',
    gold: '#bc9e68', goldD: '#8a6d35',
    // Neutrals
    text: '#27272a', textMuted: '#71717a', textSubtle: '#a1a1aa',
    grid: '#f4f4f5', divider: '#e4e4e7', bg: '#fafafa',
  };

  const fontFamily = "'Inter', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', -apple-system, sans-serif";
  const fontMono = "'JetBrains Mono', 'SF Mono', 'Menlo', 'Consolas', monospace";

  const tooltipBase = {
    backgroundColor: 'rgba(46, 16, 101, .95)',
    borderColor: 'transparent',
    borderWidth: 0,
    padding: 0,
    textStyle: { color: '#fafafa', fontSize: 12, fontFamily },
    extraCssText:
      'box-shadow:0 10px 32px -4px rgba(0,0,0,.18),0 4px 8px -2px rgba(0,0,0,.1);' +
      'border-radius:10px;padding:10px 12px;backdrop-filter:blur(8px);' +
      'border:1px solid rgba(255,255,255,.06);',
  };

  // ===== Sparkline factory =====
  function spark(id, data, color) {
    const el = document.getElementById(id);
    if (!el) return;
    const c = echarts.init(el);
    const opt = {
      grid: { left: 0, right: 0, top: 4, bottom: 0 },
      xAxis: { type: 'category', show: false, data: data.map((_, i) => i) },
      yAxis: { type: 'value', show: false, scale: true },
      tooltip: { ...tooltipBase, formatter: p => `${p[0].value}` },
      series: [{
        type: 'line',
        data,
        smooth: true,
        symbol: 'none',
        lineStyle: { color, width: 1.6 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '55' },
            { offset: 1, color: color + '00' },
          ]),
        },
      }],
    };
    c.setOption(opt);
    return c;
  }

  spark('spark-1', M.sparks.total, PALETTE.p600);
  spark('spark-2', M.sparks.aiRate, PALETTE.skyD);
  spark('spark-3', M.sparks.respMin, PALETTE.emeraldD);
  spark('spark-4', M.sparks.uv, PALETTE.amberD);
  spark('spark-5', M.sparks.feedback, PALETTE.fuchsiaD);
  spark('spark-6', M.sparks.noAns, PALETTE.roseD);

  // ===== M2 Funnel =====
  const funnelEl = document.getElementById('chart-funnel');
  const funnelChart = echarts.init(funnelEl);
  // Brand purple monochrome scale (deep → light) + fuchsia accent for the final step
  const FUNNEL_COLORS = [
    [PALETTE.p700, PALETTE.p600],
    [PALETTE.p600, PALETTE.p500],
    [PALETTE.p500, PALETTE.p400],
    [PALETTE.p400, PALETTE.p300],
    [PALETTE.fuchsiaD, PALETTE.fuchsia],
  ];
  function renderFunnel(mode) {
    const data = M.funnel[mode] || M.funnel.hits;
    const max = Math.max(...data.map(d => d.value));
    funnelChart.setOption({
      tooltip: {
        ...tooltipBase,
        formatter: p => {
          const pct = ((p.value / max) * 100).toFixed(1);
          return `<div style="font-weight:600;margin-bottom:4px">${p.name.split(' ')[0]}</div>` +
            `<div style="font-family:${fontMono};font-size:16px;font-weight:700;color:#fff">` +
            p.value.toLocaleString() + `<span style="color:rgba(255,255,255,.5);font-size:11px;font-weight:500;margin-left:6px">${mode === 'users' ? '人' : '次'} · ${pct}%</span></div>`;
        },
      },
      series: [{
        type: 'funnel',
        left: 8, right: 8, top: 6, bottom: 8,
        minSize: '24%',
        maxSize: '100%',
        sort: 'descending',
        gap: 3,
        funnelAlign: 'center',
        label: {
          show: true,
          position: 'inside',
          formatter: p => `{n|${p.name.split(' ')[0]}}\n{v|${p.value.toLocaleString()}}`,
          rich: {
            n: { color: 'rgba(255,255,255,.85)', fontSize: 11.5, lineHeight: 16, fontWeight: 500, fontFamily },
            v: { color: '#fff', fontSize: 17, lineHeight: 22, fontWeight: 700, fontFamily: fontMono, padding: [2, 0, 0, 0] },
          },
        },
        labelLine: { show: false },
        itemStyle: { borderColor: '#fff', borderWidth: 2, borderRadius: 8 },
        emphasis: { label: { fontSize: 17 }, itemStyle: { shadowBlur: 16, shadowColor: 'rgba(124,58,237,.3)' } },
        data: data.map((d, i) => ({
          name: d.name, value: d.value,
          itemStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: FUNNEL_COLORS[i][0] },
              { offset: 1, color: FUNNEL_COLORS[i][1] },
            ]),
          },
        })),
      }],
    });
  }
  renderFunnel('hits');

  // ===== M3 Service Heat (horizontal bars) =====
  function horizontalBar(id, data, valueKey, labelKey, scheme) {
    const el = document.getElementById(id);
    const c = echarts.init(el);
    const sorted = [...data].sort((a, b) => a[valueKey] - b[valueKey]);
    const max = Math.max(...sorted.map(d => d[valueKey]));
    c.setOption({
      grid: { left: 4, right: 56, top: 4, bottom: 4, containLabel: true },
      xAxis: { type: 'value', show: false, max: max * 1.12 },
      yAxis: {
        type: 'category',
        data: sorted.map(d => d[labelKey]),
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: PALETTE.text, fontSize: 12, fontFamily, fontWeight: 500 },
      },
      tooltip: {
        ...tooltipBase,
        formatter: p => `<div style="font-weight:600;margin-bottom:3px">${p.name}</div>` +
          `<div style="font-family:${fontMono};font-size:14px;font-weight:700">${p.value.toLocaleString()}<span style="font-weight:500;color:rgba(255,255,255,.55);font-size:11px;margin-left:5px">次点击</span></div>`,
      },
      series: [{
        type: 'bar',
        data: sorted.map((d, i) => ({
          value: d[valueKey],
          itemStyle: {
            borderRadius: [0, 4, 4, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: scheme[0] },
              { offset: 1, color: scheme[1] },
            ]),
          },
        })),
        barWidth: 14,
        label: {
          show: true, position: 'right', distance: 6,
          color: PALETTE.text, fontSize: 11.5, fontWeight: 700, fontFamily: fontMono,
          formatter: p => p.value.toLocaleString(),
        },
        emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(124,58,237,.35)' } },
      }],
    });
    return c;
  }
  horizontalBar('chart-services', M.services, 'count', 'card', [PALETTE.p400, PALETTE.p600]);
  horizontalBar('chart-quicks', M.quicks, 'count', 'label', [PALETTE.p200, PALETTE.p500]);

  // ===== M4 Cross =====
  const crossEl = document.getElementById('chart-cross');
  const crossChart = echarts.init(crossEl);
  function renderCross(mode) {
    if (mode === 'college_x_category') {
      crossChart.clear();
      crossChart.setOption({
        tooltip: {
          ...tooltipBase,
          formatter: p => {
            const college = M.colleges[p.data[1]];
            const cat = M.categories[p.data[0]].label;
            return `${college} · ${cat}<br/><span style="font-size:14px;font-weight:700">${p.data[2]}</span> 条未答`;
          },
        },
        grid: { left: 110, right: 30, top: 30, bottom: 24, containLabel: false },
        xAxis: {
          type: 'category',
          data: M.categories.map(c => c.label),
          position: 'top',
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: PALETTE.textMuted, fontSize: 11, fontFamily, interval: 0 },
          splitArea: { show: false },
        },
        yAxis: {
          type: 'category',
          data: M.colleges,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: {
            color: PALETTE.text, fontSize: 11, fontFamily,
            formatter: v => v.length > 8 ? v.slice(0, 7) + '…' : v,
          },
          inverse: true,
        },
        visualMap: {
          min: 0,
          max: Math.max(...M.crossMatrix.map(c => c[2])),
          calculable: false,
          orient: 'horizontal',
          left: 'right', bottom: 'auto', top: 2,
          itemWidth: 8, itemHeight: 90,
          textStyle: { color: PALETTE.textSubtle, fontSize: 9.5, fontFamily, fontWeight: 500 },
          text: ['多', '少'],
          inRange: { color: [PALETTE.p50, PALETTE.p100, PALETTE.p300, PALETTE.p500, PALETTE.p700, PALETTE.p900] },
        },
        series: [{
          type: 'heatmap',
          data: M.crossMatrix,
          label: {
            show: true, color: '#fff', fontSize: 10, fontWeight: 700, fontFamily: fontMono,
            formatter: p => p.data[2] >= 4 ? p.data[2] : '',
          },
          itemStyle: { borderRadius: 4, borderColor: '#fff', borderWidth: 2 },
          emphasis: {
            itemStyle: { shadowBlur: 12, shadowColor: 'rgba(124,58,237,.45)', borderColor: 'rgba(124,58,237,.5)' },
            label: { fontSize: 11 },
          },
        }],
      });
    } else {
      const rows = M.aggBy(mode);
      crossChart.clear();
      crossChart.setOption({
        tooltip: {
          ...tooltipBase,
          formatter: p => `${p.name}<br/><span style="font-size:14px;font-weight:700">${p.value}</span> 条${mode === 'college' && rows[p.dataIndex].top ? '<br/><span style="font-size:11px;color:rgba(255,255,255,.7)">' + rows[p.dataIndex].top + '</span>' : ''}`,
        },
        grid: { left: 8, right: 80, top: 12, bottom: 12, containLabel: true },
        xAxis: {
          type: 'value', show: false,
          max: Math.max(...rows.map(r => r.total)) * 1.15,
        },
        yAxis: {
          type: 'category',
          data: rows.map(r => r.label).reverse(),
          axisLine: { show: false }, axisTick: { show: false },
          axisLabel: { color: PALETTE.text, fontSize: 12, fontFamily },
        },
        series: [{
          type: 'bar',
          data: rows.map(r => r.total).reverse(),
          barWidth: 16,
          itemStyle: {
            borderRadius: [0, 5, 5, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
              { offset: 0, color: PALETTE.p300 },
              { offset: 1, color: PALETTE.p600 },
            ]),
          },
          label: {
            show: true, position: 'right', distance: 6,
            color: PALETTE.text, fontSize: 12, fontWeight: 700, fontFamily: fontMono,
            formatter: p => p.value,
          },
          emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(124,58,237,.35)' } },
        }],
      });
    }
  }
  renderCross('college_x_category');

  // ===== M5 Gauge =====
  const gaugeEl = document.getElementById('chart-gauge');
  const gaugeChart = echarts.init(gaugeEl);
  gaugeChart.setOption({
    series: [{
      type: 'gauge',
      startAngle: 215, endAngle: -35,
      min: 0, max: 100,
      radius: '92%',
      splitNumber: 5,
      axisLine: { lineStyle: { width: 10, color: [[1, PALETTE.p100]] } },
      pointer: { show: false },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      anchor: { show: false },
      progress: {
        show: true, width: 10, roundCap: true,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: PALETTE.p400 },
            { offset: 0.6, color: PALETTE.p600 },
            { offset: 1, color: PALETTE.p700 },
          ]),
          shadowBlur: 8, shadowColor: 'rgba(124,58,237,.25)',
        },
      },
      title: {
        offsetCenter: [0, '38%'],
        color: PALETTE.textMuted, fontSize: 11, fontFamily, fontWeight: 500,
      },
      detail: {
        valueAnimation: true,
        offsetCenter: [0, '-2%'],
        formatter: v => '{v|' + Math.round(v) + '}{u|%}',
        rich: {
          v: { color: PALETTE.p700, fontSize: 32, fontWeight: 700, fontFamily: fontMono, padding: [0, 0, 0, 0] },
          u: { color: PALETTE.textMuted, fontSize: 14, fontWeight: 600, fontFamily: fontMono, padding: [0, 0, 4, 2] },
        },
      },
      data: [{ value: M.quality.hitRate, name: 'RAG 命中率' }],
    }],
  });

  // ===== M5 Latency Line =====
  const latencyEl = document.getElementById('chart-latency');
  const latencyChart = echarts.init(latencyEl);
  latencyChart.setOption({
    grid: { left: 32, right: 16, top: 6, bottom: 22 },
    tooltip: {
      ...tooltipBase, trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: PALETTE.p200, type: 'dashed' } },
      formatter: p => `<div style="font-weight:600;margin-bottom:4px">${p[0].axisValue}</div>` +
        p.map(s => `<div style="display:flex;align-items:center;gap:6px;padding:1px 0"><span style="width:7px;height:7px;border-radius:50%;background:${s.color};display:inline-block"></span><span style="flex:1;color:rgba(255,255,255,.7);font-size:11px">${s.seriesName}</span><strong style="font-family:${fontMono};font-size:13px;color:#fff">${s.value}s</strong></div>`).join(''),
    },
    legend: { show: false },
    xAxis: {
      type: 'category',
      data: M.quality.latencyP50.map(d => d.date),
      boundaryGap: false,
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: PALETTE.textSubtle, fontSize: 10, fontFamily, fontFeatureSettings: 'tnum' },
    },
    yAxis: {
      type: 'value',
      splitLine: { lineStyle: { color: PALETTE.grid, type: 'dashed' } },
      axisLine: { show: false }, axisTick: { show: false },
      axisLabel: { color: PALETTE.textSubtle, fontSize: 10, fontFamily: fontMono, formatter: '{value}s' },
    },
    series: [
      {
        name: 'p95', type: 'line', smooth: true,
        data: M.quality.latencyP50.map(d => +d.p95.toFixed(2)),
        symbol: 'circle', symbolSize: 5, showSymbol: false,
        lineStyle: { color: PALETTE.amber, width: 1.5, type: [3, 3] },
        itemStyle: { color: PALETTE.amber, borderColor: '#fff', borderWidth: 2 },
        emphasis: { showSymbol: true, scale: 1.4 },
      },
      {
        name: 'p50', type: 'line', smooth: true,
        data: M.quality.latencyP50.map(d => +d.p50.toFixed(2)),
        symbol: 'circle', symbolSize: 5, showSymbol: false,
        lineStyle: { color: PALETTE.p600, width: 2 },
        itemStyle: { color: PALETTE.p600, borderColor: '#fff', borderWidth: 2 },
        emphasis: { showSymbol: true, scale: 1.4 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(124,58,237,.16)' },
            { offset: 1, color: 'rgba(124,58,237,0)' },
          ]),
        },
      },
    ],
  });

  // ===== M6 Cost =====
  const costEl = document.getElementById('chart-cost');
  const costChart = echarts.init(costEl);
  function renderCost(mode) {
    if (mode === 'day') {
      costChart.setOption({
        grid: { left: 48, right: 48, top: 32, bottom: 28 },
        tooltip: {
          ...tooltipBase, trigger: 'axis',
          axisPointer: { type: 'shadow', shadowStyle: { color: 'rgba(124,58,237,.06)' } },
          formatter: p => `<div style="font-weight:600;margin-bottom:5px">${p[0].axisValue}</div>` +
            p.map(s => {
              const v = s.seriesName === '价格' ? '¥ ' + s.value.toFixed(3) : s.value.toLocaleString();
              return `<div style="display:flex;align-items:center;gap:6px;padding:1px 0"><span style="width:7px;height:7px;border-radius:2px;background:${s.color};display:inline-block"></span><span style="flex:1;color:rgba(255,255,255,.7);font-size:11px">${s.seriesName}</span><strong style="font-family:${fontMono};font-size:13px;color:#fff">${v}</strong></div>`;
            }).join(''),
        },
        legend: {
          data: [
            { name: 'Tokens', icon: 'roundRect' },
            { name: '价格', icon: 'circle' },
          ],
          top: 2, right: 8,
          textStyle: { color: PALETTE.textMuted, fontSize: 11, fontFamily, fontWeight: 500 },
          itemWidth: 10, itemHeight: 6, itemGap: 14,
        },
        xAxis: {
          type: 'category',
          data: M.costByDay.map(d => d.date),
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { color: PALETTE.textSubtle, fontSize: 10.5, fontFamily, fontFeatureSettings: 'tnum' },
        },
        yAxis: [
          {
            type: 'value', name: 'TOKENS',
            nameTextStyle: { color: PALETTE.textSubtle, fontSize: 9.5, padding: [0, 30, 0, 0], fontWeight: 600, letterSpacing: 0.5 },
            splitLine: { lineStyle: { color: PALETTE.grid, type: 'dashed' } },
            axisLine: { show: false }, axisTick: { show: false },
            axisLabel: { color: PALETTE.textSubtle, fontSize: 10, fontFamily: fontMono, formatter: v => (v / 1000) + 'k' },
          },
          {
            type: 'value', name: '¥',
            nameTextStyle: { color: PALETTE.textSubtle, fontSize: 9.5, padding: [0, 0, 0, 30], fontWeight: 600 },
            splitLine: { show: false }, axisLine: { show: false }, axisTick: { show: false },
            axisLabel: { color: PALETTE.textSubtle, fontSize: 10, fontFamily: fontMono, formatter: '¥{value}' },
          },
        ],
        series: [
          {
            name: 'Tokens', type: 'bar', yAxisIndex: 0,
            data: M.costByDay.map(d => d.tokens),
            barWidth: 24,
            itemStyle: {
              borderRadius: [5, 5, 0, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: PALETTE.p400 },
                { offset: 1, color: PALETTE.p600 },
              ]),
            },
            emphasis: { itemStyle: { shadowBlur: 12, shadowColor: 'rgba(124,58,237,.35)' } },
          },
          {
            name: '价格', type: 'line', yAxisIndex: 1, smooth: true,
            data: M.costByDay.map(d => d.price),
            symbol: 'circle', symbolSize: 7,
            lineStyle: { color: PALETTE.pink, width: 2 },
            itemStyle: { color: PALETTE.pink, borderColor: '#fff', borderWidth: 2 },
            z: 5,
          },
        ],
      });
    } else {
      const data = mode === 'conv' ? M.costByConv : M.costByUser;
      const labelKey = mode === 'conv' ? (d => '#' + d.conv_id) : (d => d.name);
      costChart.setOption({
        grid: { left: 8, right: 64, top: 8, bottom: 8, containLabel: true },
        tooltip: {
          ...tooltipBase,
          formatter: p => {
            const d = data[p.dataIndex];
            return `<div style="font-weight:600;margin-bottom:4px">${p.name}</div>` +
              `<div style="font-family:${fontMono};font-size:14px;font-weight:700;color:#fff">${p.value.toLocaleString()}<span style="color:rgba(255,255,255,.5);font-size:11px;font-weight:500;margin-left:5px">tokens</span></div>` +
              `<div style="margin-top:5px;display:flex;gap:8px;align-items:center;font-size:11px;color:rgba(255,255,255,.65)">` +
              `<span style="color:${d.is_pilot ? PALETTE.amber : PALETTE.emerald}">●</span>${d.is_pilot ? '内测设备' : '真实学生'} · ${d.calls} 次调用` +
              (d.warn ? `<span style="color:${PALETTE.rose};margin-left:4px">⚠ 异常</span>` : '') +
              `</div>`;
          },
        },
        xAxis: { type: 'value', show: false, max: data[0].tokens * 1.12 },
        yAxis: {
          type: 'category', data: data.map(labelKey).reverse(),
          axisLine: { show: false }, axisTick: { show: false },
          axisLabel: { color: PALETTE.text, fontSize: 11.5, fontFamily, fontWeight: 500 },
        },
        series: [{
          type: 'bar', barWidth: 14,
          data: data.map((d, i) => ({
            value: d.tokens,
            itemStyle: {
              borderRadius: [0, 4, 4, 0],
              color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
                { offset: 0, color: d.warn ? '#fda4af' : PALETTE.p300 },
                { offset: 1, color: d.warn ? PALETTE.roseD : PALETTE.p600 },
              ]),
            },
          })).reverse(),
          label: {
            show: true, position: 'right', distance: 6,
            color: PALETTE.text, fontSize: 11, fontWeight: 700, fontFamily: fontMono,
            formatter: p => p.value.toLocaleString(),
          },
          emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(124,58,237,.35)' } },
        }],
      });
    }
    renderCostTable(mode);
  }
  function renderCostTable(mode) {
    const tbody = document.getElementById('cost-tbody');
    let rows;
    if (mode === 'day') {
      rows = M.costByDay.map((d, i) => ({
        rank: i + 1, label: d.date, sub: '日聚合', is_pilot: null,
        tokens: d.tokens, price: d.price, warn: false,
      }));
    } else if (mode === 'conv') {
      rows = M.costByConv.map((d, i) => ({
        rank: i + 1, label: '#' + d.conv_id, sub: d.user, is_pilot: d.is_pilot,
        tokens: d.tokens, price: d.price, warn: d.warn,
      }));
    } else {
      rows = M.costByUser.map((d, i) => ({
        rank: i + 1, label: d.name, sub: d.user_id, is_pilot: d.is_pilot,
        tokens: d.tokens, price: d.price, warn: d.warn,
      }));
    }
    tbody.innerHTML = rows.map(r => `
      <tr>
        <td><span class="tbl-row-rank ${r.rank <= 3 ? 'tbl-row-rank--top' : ''}">${r.rank}</span></td>
        <td>
          <div class="tbl-row-label">${r.label}${r.warn ? '<span class="tag tag-warn">⚠ 异常</span>' : ''}</div>
          <div class="tbl-row-sub">${r.sub}</div>
        </td>
        <td>${r.is_pilot === null ? '<span class="muted" style="font-family:var(--font-mono)">—</span>' : r.is_pilot ? '<span class="tag tag-pilot">内测</span>' : '<span class="tag tag-real">真实</span>'}</td>
        <td>${r.tokens.toLocaleString()}</td>
        <td>¥ ${r.price.toFixed(3)}</td>
      </tr>
    `).join('');
  }
  renderCost('day');

  // ===== Tab interactions =====
  document.querySelectorAll('[data-funnel-mode]').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('[data-funnel-mode]').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      renderFunnel(t.dataset.funnelMode);
    });
  });

  document.querySelectorAll('[data-cross]').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('[data-cross]').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      renderCross(t.dataset.cross);
    });
  });

  document.querySelectorAll('[data-cost]').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('[data-cost]').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
      const mode = t.dataset.cost;
      const tag = document.getElementById('cost-tag');
      tag.textContent = mode === 'day' ? 'BY DAY' : mode === 'conv' ? 'BY CONV' : 'BY USER';
      renderCost(mode);
    });
  });

  // Generic seg toggle (period / user_type) - just visual
  document.querySelectorAll('.seg').forEach(seg => {
    seg.querySelectorAll('.seg-item').forEach(item => {
      item.addEventListener('click', () => {
        seg.querySelectorAll('.seg-item').forEach(x => x.classList.remove('active'));
        item.classList.add('active');
      });
    });
  });

  // Resize handler
  window.addEventListener('resize', () => {
    [funnelChart, crossChart, gaugeChart, latencyChart, costChart].forEach(c => c && c.resize());
    document.querySelectorAll('.kpi-spark').forEach(el => {
      const inst = echarts.getInstanceByDom(el);
      if (inst) inst.resize();
    });
    ['chart-services', 'chart-quicks'].forEach(id => {
      const el = document.getElementById(id);
      const inst = echarts.getInstanceByDom(el);
      if (inst) inst.resize();
    });
  });
})();
