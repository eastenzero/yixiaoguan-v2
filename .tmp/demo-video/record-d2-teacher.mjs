/**
 * record-d2-teacher.mjs · T12 教师端 demo 录制
 *
 * 剧本: video/04-script-plan.md §2.4
 * 目标: 70s 教师端能力演示，含 events.json
 *
 * ⚠️ 注意：04 文档说"1920×1080 desktop"，但教师端 H5 是 mobile-first。
 *    实际录制按 393×852 mobile viewport（与学生端一致），Remotion 后期放在
 *    1920×1080 横屏舞台中央，左右留 757px 字效空间。
 *
 * 镜头序列（约 70s）:
 *   0-10s   : 教师登录 → 工作台 hero + 4 数据卡 + 紫粉问候
 *   10-30s  : 数据看板（4 卡 + 趋势 + 学院分布 + 时段热力 + AI 成本）— 慢推 + 滚动
 *   30-50s  : 知识库 → 高频待补卡 → 点"去补充" → 详情
 *   50-70s  : profile 紫粉 hero + 过渡到 D3
 *
 * 输出:
 *   out/d2/teacher.webm
 *   out/d2/events.json
 */
import { chromium, devices } from "playwright";
import { mkdirSync, writeFileSync, renameSync, readdirSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";

// ─── 配置 ─────────────────────────────────────────────────────────
const TEA_BASE = "http://localhost:5301";
const API_DIRECT = "http://192.168.100.165:8100";
const VIEWPORT = { width: 393, height: 852 };
const FPS = 30;
const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const OUT_DIR = resolve(REPO_ROOT, ".tmp/demo-video/out/d2");

mkdirSync(OUT_DIR, { recursive: true });
mkdirSync(join(OUT_DIR, "frames"), { recursive: true });

// ─── helpers ──────────────────────────────────────────────────────
const events = [];
let t0 = 0;
const now = () => Date.now() - t0;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (k, m) => process.stdout.write(`[${String(now()).padStart(6, " ")}ms] [${k}] ${m}\n`);

async function api(method, path, token, body) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(API_DIRECT + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch { }
  return { status: res.status, data };
}

async function logClick(page, selector, label, opts = {}) {
  try {
    const handle = page.locator(selector).first();
    const box = await handle.boundingBox({ timeout: 3000 });
    if (!box) {
      log("warn", `click "${label}" invisible (selector: ${selector})`);
      return;
    }
    const x = Math.round(box.x + box.width / 2);
    const y = Math.round(box.y + box.height / 2);
    events.push({ time_ms: now(), type: "click", x, y, label, selector });
    log("click", `${label} @ (${x},${y})`);
    await handle.click(opts);
  } catch (e) {
    log("err", `click "${label}" failed: ${e?.message || e}`);
  }
}

// ─── evaluate-based click/tap — uni-app H5 Web Component 必需 ───────────────
async function tapElement(page, result, label) {
  try {
    await page.touchscreen.tap(result.x, result.y);
    events.push({ time_ms: now(), type: "tap", label, selector: result.sel, x: Math.round(result.x), y: Math.round(result.y) });
    log("tap", `${label} @ ${result.tag}.${result.classes} (${Math.round(result.x)},${Math.round(result.y)})`);
    return true;
  } catch (e) {
    log("warn", `tap failed for "${label}": ${e?.message || e}, fallback to el.click()`);
    await page.evaluate(({ sel }) => {
      const el = document.querySelector(sel);
      if (el) el.click();
    }, { sel: result.sel });
    events.push({ time_ms: now(), type: "click", label, selector: result.sel, x: Math.round(result.x), y: Math.round(result.y), fallback: "el.click" });
    return true;
  }
}

async function clickJS(page, selectors, label, opts = {}) {
  const list = Array.isArray(selectors) ? selectors : [selectors];
  const result = await page.evaluate(({ list, requireVisible }) => {
    for (const sel of list) {
      const nodes = document.querySelectorAll(sel);
      for (const el of nodes) {
        const r = el.getBoundingClientRect();
        if (requireVisible && (r.width === 0 || r.height === 0)) continue;
        try { el.scrollIntoView({ block: 'center', inline: 'center' }); } catch { }
        const r2 = el.getBoundingClientRect();
        return { ok: true, sel, tag: el.tagName, classes: String(el.className || '').slice(0, 60), x: r2.x + r2.width / 2, y: r2.y + r2.height / 2 };
      }
    }
    return { ok: false, reason: 'not_found', tried: list };
  }, { list, requireVisible: opts.requireVisible !== false });
  if (!result.ok) {
    log("warn", `clickJS "${label}" failed: ${result.reason} tried=${JSON.stringify(result.tried || [list]).slice(0, 120)}`);
    return false;
  }
  return tapElement(page, result, label);
}

async function clickByText(page, text, baseSelector, label) {
  const result = await page.evaluate(({ text, sel }) => {
    const nodes = document.querySelectorAll(sel);
    for (const el of nodes) {
      const tc = el.textContent || "";
      if (!tc.includes(text)) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      try { el.scrollIntoView({ block: 'center', inline: 'center' }); } catch { }
      const r2 = el.getBoundingClientRect();
      return { ok: true, sel, tag: el.tagName, classes: String(el.className || '').slice(0, 60), x: r2.x + r2.width / 2, y: r2.y + r2.height / 2 };
    }
    return { ok: false, reason: 'no_text_match' };
  }, { text, sel: baseSelector });
  if (!result.ok) {
    log("warn", `clickByText "${label}" "${text}" in ${baseSelector} failed: ${result.reason}`);
    return false;
  }
  return tapElement(page, result, `${label} "${text}"`);
}

// scroll 封装：uni-app scroll-view 是 Web Component，使用 window.scrollBy + scroll-view.scrollBy
async function logScroll(page, deltaY, label) {
  events.push({ time_ms: now(), type: "scroll", deltaY, label });
  log("scroll", `${deltaY}px · ${label}`);
  await page.evaluate((dy) => {
    // 先试页面滚动
    window.scrollBy({ top: dy, behavior: 'smooth' });
    // 同时给任意 scroll-view 也动一下
    document.querySelectorAll('uni-scroll-view, .scroll-view').forEach(sv => {
      try { sv.scrollBy?.({ top: dy, behavior: 'smooth' }); } catch { }
    });
  }, deltaY);
}

async function pause(ms, label) {
  if (label) {
    events.push({ time_ms: now(), type: "pause", duration_ms: ms, label });
    log("pause", `${ms}ms · ${label}`);
  }
  await sleep(ms);
}

async function snap(page, name) {
  const path = join(OUT_DIR, "frames", `${String(now()).padStart(6, "0")}-${name}.png`);
  try { await page.screenshot({ path }); } catch { }
}

// ─── 教师登录 ─────────────────────────────────────────────────────
log("api", "教师登录 anjing …");
const teaLogin = await api("POST", "/api/auth/login", null, {
  staff_id: "anjing",
  password: "Anjing@yxg2026",
});
if (teaLogin.status !== 200) {
  console.error("✗ 教师登录失败", teaLogin);
  process.exit(1);
}
const teaToken = teaLogin.data.access_token;
const teaMe = await api("GET", "/api/auth/me", teaToken);
const teaUserInfo = JSON.stringify(teaMe.data);
log("api", `教师 user_id=${teaMe.data.id} name=${teaMe.data.name || "?"}`);

// ─── 准备一个 demo entry id 用于 knowledge detail ──────────────────
let demoEntryId = 1;
try {
  const list = await api("GET", "/api/v1/knowledge/entries?pageNum=1&pageSize=5", teaToken);
  if (list.status === 200 && list.data?.items?.length) {
    demoEntryId = list.data.items[0].id;
  }
} catch { }
log("api", `demo knowledge entry id=${demoEntryId}`);

// ─── 启动浏览器（录制） ───────────────────────────────────────────
log("phase", "启动 Chromium 录制");
const browser = await chromium.launch({ headless: false });
const context = await browser.newContext({
  ...devices["iPhone 14 Pro"],
  viewport: VIEWPORT,
  deviceScaleFactor: 3,
  recordVideo: { dir: OUT_DIR, size: VIEWPORT },
});

await context.addInitScript(({ tk, ui }) => {
  localStorage.setItem("teacher-token", tk);
  localStorage.setItem("teacher-user-info", ui);
}, { tk: teaToken, ui: teaUserInfo });

const page = await context.newPage();

// ============================================================
// === 录制开始 ===
// ============================================================

// 先去 login 页（不显示，立刻跳）
await page.goto(`${TEA_BASE}/#/pages/login/index`, { waitUntil: "load" });
await page.waitForTimeout(800);

t0 = Date.now();
log("phase", "=== recording start ===");

// ─── 0-10s: 工作台 ────────────────────────────────────────────────
await page.goto(`${TEA_BASE}/#/pages/dashboard/index`, { waitUntil: "load" });
await pause(4000, "工作台 hero + 4 数据卡");
await snap(page, "dashboard");

// 滚动看待处理提问列表
await logScroll(page, 300, "看待处理列表");
await pause(3000, "待处理提问");
await snap(page, "dashboard-scrolled");

await logScroll(page, 250, "继续下滚看提问");
await pause(2000, "看近期提问");

// 滚回顶
await logScroll(page, -550, "回顶部");
await pause(2000, "回到 hero");

// ─── 10-30s: 数据看板 ────────────────────────────────────────────
// dashboard.vue 的快捷操作 "数据报告" 走 navigateTo /pages/analytics/index
const entered = await clickByText(page, '数据报告', '.quick-action-btn', "进入数据看板");
if (!entered) {
  log("warn", "\u6570\u636e\u62a5\u544a chip \u70b9\u4e0d\u52a8\uff0cgoto fallback");
  await page.goto(`${TEA_BASE}/#/pages/analytics/index`, { waitUntil: "load" });
}
await pause(3000, "看板首屏 4 大数据卡");
await snap(page, "analytics-top");

// 滚动到中段（趋势图 + AI 质量分析）
await logScroll(page, 500, "看趋势图 + AI 质量");
await pause(3500, "趋势 + 圆环");
await snap(page, "analytics-mid");

// 滚动到学院分布
await logScroll(page, 500, "看学院分布");
await pause(3000, "学院分布 ring");

// 继续滚动到底部（时段热力 + 成本）
await logScroll(page, 600, "看时段热力 + AI 成本");
await pause(3500, "24×7 热力 + AI 质量序列");
await snap(page, "analytics-bottom");

// 滚回顶部
await logScroll(page, -1200, "看板回顶部");
await pause(1500);

// ─── 30-50s: 知识库 ──────────────────────────────────────────────
// analytics 页面没有 BottomNavBar，先 goBack 回 dashboard
await page.goBack().catch(() => { });
events.push({ time_ms: now(), type: "nav_back", label: "返回 dashboard" });
await pause(2000, "返回工作台（重新看 BottomNavBar）");
await snap(page, "back-to-dashboard");

// 底部自定义 tab "知识库"，包成 .tab-item > tab-label uni-text
const kbOk = await clickByText(page, '知识库', '.tab-item', "底部 Tab: 知识库");
if (!kbOk) {
  log("warn", "tab 知识库 点不动，goto fallback");
  await page.goto(`${TEA_BASE}/#/pages/knowledge/index`, { waitUntil: "load" });
}
await pause(4000, "高频待补卡片列表");
await snap(page, "knowledge-list");

// 点击第一张"高频待补"卡片的"去补充"按钮 — 切换 inline composer
await clickByText(page, '去补充', '.mini-action-btn', "点击 去补充");
await pause(4000, "打开 inline composer (textarea + scope)");
await snap(page, "knowledge-composer");

// 模拟教师在 textarea 里输入答复
// uni-app <textarea> 渲染成 <uni-textarea class="answer-input"> 外包 + <textarea class="uni-textarea-textarea"> 内层
// 操作内层 + 派发 input 事件
const taFilled = await page.evaluate((val) => {
  // 内层 textarea — 任何 .composer-panel 下的 textarea，或全局先匹配 uni-textarea inner
  let ta = document.querySelector('.composer-panel uni-textarea textarea');
  if (!ta) ta = document.querySelector('.composer-panel textarea');
  if (!ta) ta = document.querySelector('textarea.uni-textarea-textarea');
  if (!ta) return { ok: false, reason: 'not_found' };
  ta.removeAttribute('disabled');
  ta.disabled = false;
  const desc = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value');
  if (desc && desc.set) desc.set.call(ta, val);
  else ta.value = val;
  ta.dispatchEvent(new Event('input', { bubbles: true }));
  ta.dispatchEvent(new Event('change', { bubbles: true }));
  return { ok: true, classes: ta.className };
}, '宿舍电费可以通过完美校园 App 充值，也可以前往一楼宿管处缴费。每月 15 日前充值有 9 折优惠。');
events.push({ time_ms: now(), type: "type_textarea", label: "教师答复输入", ok: taFilled.ok, classes: taFilled.classes });
log("type", `textarea fill: ${JSON.stringify(taFilled)}`);
await pause(3000, "教师答复内容");
await snap(page, "knowledge-composer-filled");

// 选个 scope。实际可用 scope: 班级发布 / 学院发布 / 提交审核
await clickByText(page, '班级发布', '.scope-pill', "选择 scope: 班级发布").catch(() => { });
await pause(2000, "展示 scope 选中状态");

// 收起 composer—再滚动看更多卡片
await clickByText(page, '收起', '.mini-action-btn', "收起 composer").catch(() => { });
await pause(1500, "收起 composer");

await logScroll(page, 400, "向下看更多 KB 卡片");
await pause(3000, "看更多卡片");

// ─── 50-70s: profile 收尾 ─────────────────────────────────────────
const profOk = await clickByText(page, '我的', '.tab-item', "底部 Tab: 我的");
if (!profOk) {
  log("warn", "tab 我的 点不动，goto fallback");
  await page.goto(`${TEA_BASE}/#/pages/profile/index`, { waitUntil: "load" });
}
await pause(3500, "profile 紫粉 hero");
await snap(page, "profile");

// 滚一下看完整 profile（系统设置 toggle 等）
await logScroll(page, 400, "看系统设置");
await pause(3500, "系统设置区");
await snap(page, "profile-scrolled");

await logScroll(page, 300, "继续下滚看更多设置");
await pause(3000, "更多设置项");

await pause(2500, "收尾过渡 D3");

// ============================================================
// === 录制结束 ===
// ============================================================
const duration_ms = now();
log("phase", `=== recording end (${duration_ms}ms) ===`);

await page.close();
await context.close();

const videoFiles = readdirSync(OUT_DIR).filter((f) => f.endsWith(".webm"));
if (videoFiles.length > 0) {
  const src = join(OUT_DIR, videoFiles[0]);
  const dst = join(OUT_DIR, "teacher.webm");
  if (existsSync(dst)) {
    renameSync(dst, dst.replace(".webm", `.bak-${Date.now()}.webm`));
  }
  renameSync(src, dst);
  log("done", `video → ${dst}`);
}

const timeline = {
  task: "T12-D2-teacher",
  url: TEA_BASE,
  viewport: VIEWPORT,
  fps: FPS,
  duration_ms,
  teacher_user_id: teaMe.data.id,
  demo_entry_id: demoEntryId,
  events,
};
writeFileSync(join(OUT_DIR, "events.json"), JSON.stringify(timeline, null, 2));
log("done", `events.json (${events.length} events) → ${join(OUT_DIR, "events.json")}`);

await browser.close();
