/**
 * record-d1-student.mjs · T11 学生端 demo 录制
 *
 * 剧本: video/04-script-plan.md §2.3
 * 目标: 70s 学生端核心闭环，含 events.json 供 Remotion zoom/pulse 编排
 *
 * 镜头序列（约 70s）:
 *   38-46  (8s)  : 登录页 → 输入学号 → 进入 home
 *   46-54  (8s)  : home 快速浏览（问候/快捷/服务卡）
 *   54-1:10 (16s): 点 AI 问答 → 提问『宿舍电费怎么交』→ AI 流答（高度采样镜头跟随）
 *   1:10-1:20 (10s): 打开来源弹层 → 翻历史
 *   1:20-1:32 (12s): 提复杂问题 → 触发『转人工』
 *   1:32-1:48 (16s): buffer + 收尾过渡到 D2
 *
 * 输出:
 *   out/d1/student.webm    (Playwright 原始录制)
 *   out/d1/events.json     (timeline)
 *
 * 用法:
 *   node .tmp/demo-video/record-d1-student.mjs
 *
 * ⚠️ TODO selector：本脚本中标 `// TODO selector` 处需要根据 polished UI 的实际 DOM 微调
 *    建议先用 headless: false 跑一次盲测，把失败的 selector 抄到 DevTools 重定位。
 */
import { chromium, devices } from "playwright";
import { mkdirSync, writeFileSync, renameSync, readdirSync, existsSync } from "node:fs";
import { join, resolve } from "node:path";

// ─── 配置 ─────────────────────────────────────────────────────────
const STU_BASE = "http://localhost:3001";
const API_DIRECT = "http://192.168.100.165:8100";
const VIEWPORT = { width: 393, height: 852 };
const FPS = 30;
const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const OUT_DIR = resolve(REPO_ROOT, ".tmp/demo-video/out/d1");

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
      log("warn", `click "${label}" — element invisible (selector: ${selector})`);
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

async function logFill(page, selector, value, label) {
  try {
    const handle = page.locator(selector).first();
    const box = await handle.boundingBox({ timeout: 3000 });
    if (!box) return log("warn", `fill "${label}" — element invisible`);
    const x = Math.round(box.x + box.width / 2);
    const y = Math.round(box.y + box.height / 2);
    events.push({ time_ms: now(), type: "fill", x, y, label, selector, value });
    log("fill", `${label} = "${value}"`);
    await handle.fill(value);
  } catch (e) {
    log("err", `fill "${label}" failed: ${e?.message || e}`);
  }
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

// ─── AI 流答镜头跟随：MutationObserver 采样答案高度 ──────────────────
async function streamingSample(page, selector, maxMs = 25000, settleMs = 2000) {
  const start = now();
  events.push({ time_ms: start, type: "ai_streaming_start", selector });
  const heights = [];
  let lastChange = Date.now();
  while (Date.now() - lastChange < settleMs) {
    if (Date.now() - start > maxMs) break;
    try {
      const h = await page.locator(selector).first().evaluate((el) => el.scrollHeight);
      const last = heights[heights.length - 1]?.height ?? 0;
      heights.push({ t: now(), height: h });
      if (h > last) lastChange = Date.now();
    } catch { break; }
    await sleep(150);
  }
  events.push({ time_ms: now(), type: "ai_streaming_end", samples: heights.length, final_height: heights[heights.length - 1]?.height });
  log("ai", `streaming done · ${heights.length} samples · final=${heights[heights.length - 1]?.height}px`);
  return heights;
}

// ─── 学生登录拿 token ─────────────────────────────────────────────
log("api", "学生登录 4125150011 …");
const stuLogin = await api("POST", "/api/auth/login", null, {
  staff_id: "4125150011",
  password: "4125150011",
});
if (stuLogin.status !== 200) {
  console.error("✗ 学生登录失败", stuLogin);
  process.exit(1);
}
const stuToken = stuLogin.data.access_token;
const stuMe = await api("GET", "/api/auth/me", stuToken);
const stuUserInfo = JSON.stringify(stuMe.data);
log("api", `学生 user_id=${stuMe.data.id} name=${stuMe.data.name || "?"}`);

// ─── 启动浏览器（录制） ───────────────────────────────────────────
log("phase", "启动 Chromium 录制 (recordVideo)");
const browser = await chromium.launch({ headless: false });
const context = await browser.newContext({
  ...devices["iPhone 14 Pro"],
  viewport: VIEWPORT,
  deviceScaleFactor: 3,
  recordVideo: { dir: OUT_DIR, size: VIEWPORT },
});

// 注入 token 让 home 直接进
await context.addInitScript(({ tk, ui }) => {
  localStorage.setItem("v2-token", tk);
  localStorage.setItem("v2-user-info", ui);
}, { tk: stuToken, ui: stuUserInfo });

const page = await context.newPage();

// 先去 login（不带 token）展示登录页 → 再 reload 带 token 进 home
const noAuthCtx = await browser.newContext({
  ...devices["iPhone 14 Pro"],
  viewport: VIEWPORT,
  deviceScaleFactor: 3,
});
const loginPage = await noAuthCtx.newPage();

// ============================================================
// === 录制开始 ===
// ============================================================
t0 = Date.now();
log("phase", "=== recording start ===");

// ─── 0-8s: 登录页 ─────────────────────────────────────────────────
await loginPage.goto(`${STU_BASE}/#/pages/login/index`, { waitUntil: "load" });
await pause(2000, "登录页首屏");
await snap(loginPage, "login-empty");

// TODO selector: 学号输入框（用 placeholder 兜底）
await logFill(loginPage, 'input[placeholder*="学号"], input[type="text"]', "4125150011", "输入学号");
await pause(500);
await logFill(loginPage, 'input[type="password"]', "4125150011", "输入密码");
await pause(800);
// TODO selector: 登录按钮
await logClick(loginPage, 'button:has-text("登录"), button.login-btn', "点击登录按钮");
await pause(2500, "登录跳转中");

// ─── 8-16s: home 首页 ────────────────────────────────────────────
await page.goto(`${STU_BASE}/#/pages/home/index`, { waitUntil: "load" });
await pause(2500, "首页 hero + 快捷区");
await snap(page, "home");

// 横向滑动快捷入口 (TODO: 真实 selector)
// await page.locator(".chip-scroll").first().evaluate((el) => el.scrollBy({ left: 200, behavior: "smooth" }));
// events.push({ time_ms: now(), type: "scroll-h", deltaX: 200, label: "快捷入口滑动" });
await pause(2000, "服务卡区");

// ─── 16-32s: AI 问答 + 流式回答 ──────────────────────────────────
// TODO selector: 底部 tab "智能问答"
await logClick(page, '.tab-item:has-text("智能问答"), [data-tab="chat"]', "底部 Tab: 智能问答");
await pause(2000, "进入 AI 对话页");
await snap(page, "chat-empty");

// 提一个真实问题
// TODO selector: 输入框
await logFill(page, 'textarea, .chat-input textarea, input[placeholder*="提问"]', "宿舍电费怎么交", "提问");
await pause(500);
// TODO selector: 发送按钮
await logClick(page, 'button:has-text("发送"), .send-btn', "发送提问");
await pause(800, "等首字符");

// 镜头跟随：采样答案高度
await streamingSample(page, '.ai-answer, .message-ai .content', 20000, 1500);
await snap(page, "after-stream");

// ─── 32-42s: 来源弹层 + 翻历史 ───────────────────────────────────
// TODO selector: 来源按钮（点开来源弹层）
await logClick(page, 'text=查看来源, [data-action="source"]', "点开来源弹层");
await pause(2500, "查看来源详情");
await snap(page, "source-modal");

// 关闭弹层
await logClick(page, '.modal-close, button:has-text("关闭")', "关闭弹层");
await pause(1000);

// 切到历史
// TODO selector: 历史 tab 或入口
await logClick(page, 'text=历史, [data-tab="history"]', "进入历史");
await pause(2500, "历史列表");
await snap(page, "history");

// ─── 42-54s: 转人工 ──────────────────────────────────────────────
// 回 chat 提一个复杂问题触发转人工
await logClick(page, '.tab-item:has-text("智能问答"), [data-tab="chat"]', "回 chat");
await pause(1500);
await logFill(page, 'textarea, .chat-input textarea', "我家庭情况比较特殊，奖学金加分政策具体怎么核实？", "提复杂问题");
await pause(500);
await logClick(page, 'button:has-text("发送"), .send-btn', "发送复杂问题");
await pause(2000, "等 AI 答复");

// TODO selector: 转人工按钮
await logClick(page, 'text=转人工, button:has-text("人工"), [data-action="escalate"]', "点击转人工");
await pause(2500, "转人工触发");
await snap(page, "escalated");

// ─── 54-70s: 等待 + buffer ────────────────────────────────────────
await pause(3000, "等待老师接单（学生屏幕显示『等待中』）");
await snap(page, "waiting");
await pause(2000, "buffer 收尾过渡 D2");

// ============================================================
// === 录制结束 ===
// ============================================================
const duration_ms = now();
log("phase", `=== recording end (${duration_ms}ms) ===`);

await loginPage.close();
await noAuthCtx.close();
await page.close();
await context.close();

// rename auto-generated video
const videoFiles = readdirSync(OUT_DIR).filter((f) => f.endsWith(".webm"));
if (videoFiles.length > 0) {
  const src = join(OUT_DIR, videoFiles[0]);
  const dst = join(OUT_DIR, "student.webm");
  if (existsSync(dst)) {
    // 备份旧版
    renameSync(dst, dst.replace(".webm", `.bak-${Date.now()}.webm`));
  }
  renameSync(src, dst);
  log("done", `video → ${dst}`);
}

// emit timeline
const timeline = {
  task: "T11-D1-student",
  url: STU_BASE,
  viewport: VIEWPORT,
  fps: FPS,
  duration_ms,
  student_user_id: stuMe.data.id,
  events,
};
writeFileSync(join(OUT_DIR, "events.json"), JSON.stringify(timeline, null, 2));
log("done", `events.json (${events.length} events) → ${join(OUT_DIR, "events.json")}`);

await browser.close();
