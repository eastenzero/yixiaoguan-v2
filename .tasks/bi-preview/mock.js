/* eslint-disable */
// Mock data fixtures for BI preview
window.MOCK = (function () {
  const dates7d = [];
  const today = new Date('2026-05-08T00:00:00+08:00');
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today.getTime() - i * 86400000);
    dates7d.push(`${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`);
  }

  // ===== Sparklines for KPI =====
  const sparks = {
    total: [98, 112, 105, 134, 121, 158, 119],
    aiRate: [69, 71, 70, 72, 75, 73, 73],
    respMin: [16.2, 14.8, 15.0, 13.4, 12.9, 13.2, 12.4],
    uv: [22, 28, 25, 30, 31, 24, 26],
    feedback: [4, 6, 9, 8, 12, 7, 8],
    noAns: [38, 41, 30, 36, 28, 30, 24],
  };

  // ===== M2 Funnel =====
  const funnel = {
    hits: [
      { name: '首页曝光 page_view', value: 1614 },
      { name: '开始提问 chat_send', value: 847 },
      { name: 'AI 成功响应 chat_response_ok', value: 811 },
      { name: '未答邀请曝光 unanswered_card_shown', value: 217 },
      { name: '提交反馈 feedback / unanswered submit', value: 32 },
    ],
    users: [
      { name: '首页曝光 page_view', value: 186 },
      { name: '开始提问 chat_send', value: 142 },
      { name: 'AI 成功响应 chat_response_ok', value: 138 },
      { name: '未答邀请曝光 unanswered_card_shown', value: 67 },
      { name: '提交反馈 feedback / unanswered submit', value: 28 },
    ],
  };

  // ===== M3 Service Heat =====
  const services = [
    { card: '空教室申请', source: 'home', count: 234 },
    { card: '校园网', source: 'services', count: 198 },
    { card: '网上报修', source: 'services', count: 167 },
    { card: '接诉即办', source: 'services', count: 142 },
    { card: '校医院', source: 'home', count: 121 },
    { card: '预约中心', source: 'services', count: 98 },
    { card: '人脸采集', source: 'services', count: 87 },
    { card: '班车查询', source: 'home', count: 76 },
    { card: '学术讲座', source: 'services', count: 54 },
    { card: '证件照采集', source: 'services', count: 42 },
  ];

  const quicks = [
    { label: '宿舍调换流程', count: 156 },
    { label: '选课系统在哪', count: 134 },
    { label: '学费分期可以吗', count: 121 },
    { label: '补办学生证', count: 98 },
    { label: '论文格式要求', count: 87 },
    { label: '奖学金评定标准', count: 76 },
    { label: '请假怎么办理', count: 65 },
    { label: '体测时间安排', count: 52 },
    { label: '校园卡丢失', count: 41 },
    { label: '图书馆开放', count: 33 },
  ];

  // ===== M4 Unanswered Cross =====
  const colleges = [
    '临床与基础医学院', '第一临床医学院', '第二临床医学院', '公共卫生学院',
    '药学院', '护理学院', '口腔医学院', '中医学院',
    '医学影像学院', '康复医学院', '医学心理学院', '生物医学院',
    '管理学院', '马克思主义学院', '外国语学院', '体育教学部',
    '继续教育学院', '研究生院', '国际教育学院', '医学技术学院',
    '健康管理学院',
  ];
  const categories = [
    { key: 'scholarship', label: '奖助学金' },
    { key: 'course', label: '课程教务' },
    { key: 'registration', label: '学籍手续' },
    { key: 'dorm', label: '宿舍生活' },
    { key: 'medical', label: '医疗保健' },
    { key: 'network', label: '校园网络' },
    { key: 'activity', label: '活动赛事' },
    { key: 'other', label: '其他' },
  ];
  const grades = [
    { key: 'grade_1', label: '大一' },
    { key: 'grade_2', label: '大二' },
    { key: 'grade_3', label: '大三' },
    { key: 'grade_4', label: '大四' },
    { key: 'grad', label: '研究生' },
    { key: 'other', label: '其他' },
  ];

  // 21 college × 8 category 矩阵；总和 ≈ 100~120
  function genMatrix() {
    const m = [];
    let seed = 42;
    const rand = () => {
      seed = (seed * 9301 + 49297) % 233280;
      return seed / 233280;
    };
    for (let i = 0; i < colleges.length; i++) {
      // 不同学院量级有差异：医学相关学院量大
      const base = i < 6 ? 8 : i < 12 ? 4 : 2;
      for (let j = 0; j < categories.length; j++) {
        // 每个学院有 1-2 个"热点类别"
        const hotJ = (i * 3 + 1) % categories.length;
        const hotJ2 = (i * 5 + 4) % categories.length;
        const boost = j === hotJ ? 2.5 : j === hotJ2 ? 1.6 : 1;
        const v = Math.floor(rand() * base * boost);
        if (v > 0) m.push([j, i, v]); // [x=cat, y=college, value]
      }
    }
    return m;
  }
  const crossMatrix = genMatrix();

  function aggBy(axis) {
    if (axis === 'college') {
      const arr = colleges.map((label, i) => {
        const total = crossMatrix.filter(c => c[1] === i).reduce((s, c) => s + c[2], 0);
        const cats = {};
        crossMatrix.filter(c => c[1] === i).forEach(c => {
          cats[categories[c[0]].label] = (cats[categories[c[0]].label] || 0) + c[2];
        });
        const top = Object.entries(cats).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([k, v]) => `${k}${v}`);
        return { label, total, top: top.join(' · ') };
      }).filter(r => r.total > 0);
      return arr.sort((a, b) => b.total - a.total);
    }
    if (axis === 'category') {
      return categories.map(({ label }, j) => ({
        label,
        total: crossMatrix.filter(c => c[0] === j).reduce((s, c) => s + c[2], 0),
      })).sort((a, b) => b.total - a.total);
    }
    if (axis === 'grade') {
      // mock: 按年级分布（与 matrix 无关，独立 mock）
      return [
        { label: '大三', total: 38 },
        { label: '大二', total: 31 },
        { label: '大四', total: 22 },
        { label: '大一', total: 18 },
        { label: '研究生', total: 8 },
        { label: '其他', total: 3 },
      ];
    }
    return [];
  }

  // ===== M5 Quality =====
  const quality = {
    hitRate: 68,
    high: 135,
    mid: 86,
    low: 42,
    ragAvg: 0.58,
    latencyP50: dates7d.map((d, i) => ({ date: d, p50: 0.9 + Math.sin(i) * 0.2 + 0.1, p95: 2.4 + Math.cos(i) * 0.4 + 0.2 })),
    feedbackRate: 14.1,
  };

  // ===== M6 Cost =====
  const costByDay = dates7d.map((d, i) => {
    const tokens = 120000 + Math.floor(Math.sin(i * 1.3) * 30000) + i * 5000;
    return { date: d, tokens, price: +(tokens * 0.0000118).toFixed(4) };
  });

  const costByConv = [
    { conv_id: 8124, user: 'pilot:abc8f29e', is_pilot: true, tokens: 28490, price: 0.336, calls: 14, warn: true },
    { conv_id: 8013, user: '20231024 张同学', is_pilot: false, tokens: 18204, price: 0.215, calls: 9 },
    { conv_id: 7998, user: 'pilot:5b3a7f12', is_pilot: true, tokens: 15832, price: 0.187, calls: 11 },
    { conv_id: 8089, user: '20221107 李同学', is_pilot: false, tokens: 12450, price: 0.147, calls: 7 },
    { conv_id: 8103, user: 'pilot:9e2d4a01', is_pilot: true, tokens: 11280, price: 0.133, calls: 6 },
    { conv_id: 7950, user: '20239043 王同学', is_pilot: false, tokens: 9810, price: 0.116, calls: 5 },
    { conv_id: 8077, user: 'pilot:7c1f8b45', is_pilot: true, tokens: 8932, price: 0.105, calls: 6 },
    { conv_id: 8045, user: '20221220 陈同学', is_pilot: false, tokens: 8104, price: 0.096, calls: 4 },
    { conv_id: 7982, user: 'pilot:3a8e1c67', is_pilot: true, tokens: 7560, price: 0.089, calls: 5 },
    { conv_id: 8118, user: '20231156 刘同学', is_pilot: false, tokens: 6840, price: 0.081, calls: 3 },
  ];

  const costByUser = [
    { user_id: 'pilot:abc8f29e', is_pilot: true, name: '内测设备 #128', tokens: 42810, price: 0.505, calls: 28, warn: true },
    { user_id: '20231024', is_pilot: false, name: '张同学（临床）', tokens: 38240, price: 0.451, calls: 19 },
    { user_id: 'pilot:5b3a7f12', is_pilot: true, name: '内测设备 #45', tokens: 31802, price: 0.375, calls: 24 },
    { user_id: '20221107', is_pilot: false, name: '李同学（药学）', tokens: 28934, price: 0.341, calls: 15 },
    { user_id: 'pilot:9e2d4a01', is_pilot: true, name: '内测设备 #67', tokens: 24190, price: 0.286, calls: 18 },
    { user_id: '20239043', is_pilot: false, name: '王同学（公卫）', tokens: 21580, price: 0.255, calls: 11 },
    { user_id: 'pilot:7c1f8b45', is_pilot: true, name: '内测设备 #92', tokens: 19470, price: 0.230, calls: 14 },
    { user_id: '20221220', is_pilot: false, name: '陈同学（口腔）', tokens: 17812, price: 0.210, calls: 9 },
    { user_id: 'pilot:3a8e1c67', is_pilot: true, name: '内测设备 #103', tokens: 15240, price: 0.180, calls: 10 },
    { user_id: '20231156', is_pilot: false, name: '刘同学（中医）', tokens: 13680, price: 0.162, calls: 7 },
  ];

  return {
    dates7d, sparks, funnel,
    services, quicks,
    colleges, categories, grades, crossMatrix, aggBy,
    quality, costByDay, costByConv, costByUser,
  };
})();
