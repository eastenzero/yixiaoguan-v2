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

async function logScroll(page, deltaY, label) {
  events.push({ time_ms: now(), type: "scroll", deltaY, label });
  log("scroll", `${deltaY}px · ${label}`);
  await page.mouse.wheel(0, deltaY);
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
await pause(3500, "工作台 hero + 4 数据卡");
await snap(page, "dashboard");

// 滚动看待处理提问列表
await logScroll(page, 250, "看待处理列表");
await pause(2500, "待处理提问");
await snap(page, "dashboard-scrolled");

// 滚回顶
await logScroll(page, -250, "回顶部");
await pause(1500);

// ─── 10-30s: 数据看板 ────────────────────────────────────────────
// TODO selector: 进入数据看板的入口（dashboard 上的"数据报告"chip）
await logClick(page, 'text=数据报告, text=数据看板, [data-route="analytics"]', "进入数据看板");
await pause(3000, "看板首屏 4 大数据卡");
await snap(page, "analytics-top");

// 滚动到中段（趋势图 + AI 质量分析）
await logScroll(page, 500, "看趋势图 + AI 质量");
await pause(3000, "趋势 + 圆环");
await snap(page, "analytics-mid");

// 滚动到底部（学院分布 + 时段热力 + 成本）
await logScroll(page, 700, "看学院分布 + 时段热力");
await pause(3500, "学院分布 + 24×7 热力");
await snap(page, "analytics-bottom");

// 滚回顶部准备切页
await logScroll(page, -1200, "看板回顶部");
await pause(1500);

// ─── 30-50s: 知识库 ──────────────────────────────────────────────
// TODO selector: 底部 tab "知识库"
await logClick(page, '.tab-item:has-text("知识库"), [data-tab="knowledge"]', "底部 Tab: 知识库");
await pause(3000, "高频待补 5 张卡片");
await snap(page, "knowledge-list");

// 点击第一张卡片的"去补充"
// TODO selector: 第一个"去补充"按钮
await logClick(page, 'button:has-text("去补充"):first, .kb-card .action-btn:first', "点击去补充");
await pause(3500, "知识详情/编辑页");
await snap(page, "knowledge-detail");

// 返回知识库列表
await page.goBack();
await pause(1500);
await logScroll(page, 300, "向下看更多");
await pause(2000, "看更多待补");

// ─── 50-70s: profile 收尾 ─────────────────────────────────────────
// TODO selector: 底部 tab "我的"
await logClick(page, '.tab-item:has-text("我的"), [data-tab="profile"]', "底部 Tab: 我的");
await pause(3000, "profile 紫粉 hero");
await snap(page, "profile");

// 滚一下看完整 profile（系统设置 toggle 等）
await logScroll(page, 400, "看系统设置");
await pause(3000, "系统设置区");
await snap(page, "profile-scrolled");

await pause(2000, "收尾过渡 D3");

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
