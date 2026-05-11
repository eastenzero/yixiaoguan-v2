/**
 * record-d3-dual.mjs · T13 D3 双端实时分屏录制（高潮 50s）
 *
 * 剧本: video/04-script-plan.md §2.5
 * 目标: 双 page 并行录制 + t0 同步锚点 + 双向 events.json
 *
 * 这是全片最炫的 50 秒。Playwright 双 context 并行录制：
 *   - 左屏: 学生端 393×852（一直在"等待老师"状态）
 *   - 右屏: 教师端 393×852（工作台 → detail → 输入 → 发送）
 *
 * 同步锚点：
 *   t0 = Date.now()  录制开始
 *   学生 events / 教师 events 都基于 t0 的相对时间，Remotion 可以精确对齐
 *
 * 镜头序列（50s）:
 *   0-10s   : 学生『等待中』动画 ＋ 教师工作台 → 收红点
 *   10-22s  : 教师点 detail，看到学生消息 ＋ 学生屏静默
 *   22-37s  : 教师打字 + 3 次连发 ＋ 学生屏实时跳消息
 *   37-50s  : 学生回复『谢谢老师』＋ 教师标『已解决』
 *
 * 输出:
 *   out/d3/student/<auto>.webm     学生 page 录制
 *   out/d3/teacher/<auto>.webm     教师 page 录制
 *   out/d3/student/events.json     学生 events
 *   out/d3/teacher/events.json     教师 events
 *   out/d3/sync.json               t0 锚点 + 启动元信息
 *
 * 用法:
 *   node .tmp/demo-video/record-d3-dual.mjs
 *
 * ⚠️ 前置准备:
 *   1. 学生 4125150011 + 教师 anjing 都能登录 165 dev backend
 *   2. 通过 API 提前造一条 pending_teacher 状态的 conv（学生已 escalate，老师未 accept）
 *   3. SSH tunnel localhost:18000 → 165:8000 Centrifugo 必须 ON（实时推送通道）
 */
import { chromium, devices } from "playwright";
import { mkdirSync, writeFileSync, renameSync, readdirSync } from "node:fs";
import { join, resolve } from "node:path";

// ─── 配置 ─────────────────────────────────────────────────────────
const STU_BASE = "http://localhost:3001";
const TEA_BASE = "http://localhost:5301";
const API_DIRECT = "http://192.168.100.165:8100";
const VIEWPORT = { width: 393, height: 852 };
const FPS = 30;
const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const OUT_DIR = resolve(REPO_ROOT, ".tmp/demo-video/out/d3");

mkdirSync(OUT_DIR, { recursive: true });
mkdirSync(join(OUT_DIR, "student"), { recursive: true });
mkdirSync(join(OUT_DIR, "teacher"), { recursive: true });

// ─── 时间锚点 ─────────────────────────────────────────────────────
let t0 = 0;
const now = () => Date.now() - t0;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const log = (k, m) => process.stdout.write(`[${String(now()).padStart(6, " ")}ms] [${k}] ${m}\n`);

// 双方 events，最终合并为 sync.json + 各自 events.json
const studentEvents = [];
const teacherEvents = [];

function pushEvent(side, type, extra = {}) {
  const e = { time_ms: now(), type, side, ...extra };
  if (side === "student") studentEvents.push(e);
  else teacherEvents.push(e);
  return e;
}

// ─── API helper ───────────────────────────────────────────────────
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

// ─── 1. 登录拿 token ──────────────────────────────────────────────
log("api", "学生 + 教师登录");
const [stuLogin, teaLogin] = await Promise.all([
  api("POST", "/api/auth/login", null, { staff_id: "4125150011", password: "4125150011" }),
  api("POST", "/api/auth/login", null, { staff_id: "anjing", password: "Anjing@yxg2026" }),
]);
if (stuLogin.status !== 200 || teaLogin.status !== 200) {
  console.error("✗ 登录失败", { stuLogin, teaLogin });
  process.exit(1);
}
const stuToken = stuLogin.data.access_token;
const teaToken = teaLogin.data.access_token;
const [stuMe, teaMe] = await Promise.all([
  api("GET", "/api/auth/me", stuToken),
  api("GET", "/api/auth/me", teaToken),
]);
const stuUserInfo = JSON.stringify(stuMe.data);
const teaUserInfo = JSON.stringify(teaMe.data);
log("api", `学生 id=${stuMe.data.id} · 教师 id=${teaMe.data.id}`);

// ─── 2. 准备一条 pending_teacher conv ──────────────────────────────
log("phase", "造 pending_teacher 状态 conv（学生已 escalate，老师未 accept）");
const conv = await api("POST", "/api/conversations", stuToken, {
  title: "[d3-demo] 宿舍电费 + 复杂申请",
});
if (![200, 201].includes(conv.status)) {
  console.error("✗ 创建 conv 失败", conv);
  process.exit(1);
}
const convId = conv.data.id;
await api("POST", `/api/conversations/${convId}/messages`, stuToken, {
  content: "老师，我家庭情况比较特殊，奖学金加分政策具体怎么核实？AI 答不上来。",
});
await api("POST", `/api/conversations/${convId}/escalate`, stuToken);
log("api", `conv id=${convId} pending_teacher`);

// ─── 3. 启动双 browser context（带 recordVideo） ──────────────────
log("phase", "启动双 page 录制");
const browser = await chromium.launch({ headless: false });

const stuCtx = await browser.newContext({
  ...devices["iPhone 14 Pro"],
  viewport: VIEWPORT,
  deviceScaleFactor: 3,
  recordVideo: { dir: join(OUT_DIR, "student"), size: VIEWPORT },
});
await stuCtx.addInitScript(({ tk, ui }) => {
  localStorage.setItem("v2-token", tk);
  localStorage.setItem("v2-user-info", ui);
}, { tk: stuToken, ui: stuUserInfo });

const teaCtx = await browser.newContext({
  ...devices["iPhone 14 Pro"],
  viewport: VIEWPORT,
  deviceScaleFactor: 3,
  recordVideo: { dir: join(OUT_DIR, "teacher"), size: VIEWPORT },
});
await teaCtx.addInitScript(({ tk, ui }) => {
  localStorage.setItem("teacher-token", tk);
  localStorage.setItem("teacher-user-info", ui);
}, { tk: teaToken, ui: teaUserInfo });

const stuPage = await stuCtx.newPage();
const teaPage = await teaCtx.newPage();

// ─── 4. setup：双方就位（这段会被录进视频开头，后期可剪掉） ────────
const setupStart = Date.now();
log("phase", "setup: 学生 → chat-with-conv 等待页 + 教师 → 工作台");
await Promise.all([
  stuPage.goto(`${STU_BASE}/#/pages/chat/index?convId=${convId}`, { waitUntil: "load" }),
  teaPage.goto(`${TEA_BASE}/#/pages/dashboard/index`, { waitUntil: "load" }),
]);
await sleep(3000); // 等 Centrifugo 连接 + UI settle

// ============================================================
// === 录制开始 (t0 = now) ===
// ============================================================
t0 = Date.now();
pushEvent("student", "stream_start", { url: stuPage.url() });
pushEvent("teacher", "stream_start", { url: teaPage.url() });
log("phase", "=== dual recording start ===");

const setupDurationMs = t0 - setupStart;

// ─── 0-10s: 学生『等待中』 + 教师收红点 ─────────────────────────
await sleep(2000);
pushEvent("student", "waiting_display", { label: "学生屏显示『等待老师』" });
pushEvent("teacher", "dashboard_red_dot", { label: "工作台右上红点出现" });

await sleep(3000);
pushEvent("teacher", "view_pending_card", { label: "教师看到待处理卡片" });

await sleep(3000);

// ─── 10-22s: 教师点 detail ──────────────────────────────────────
// TODO selector: 待处理 conv 卡片
try {
  const card = teaPage.locator(`[data-conv-id="${convId}"], .conv-card`).first();
  const box = await card.boundingBox({ timeout: 3000 });
  if (box) {
    pushEvent("teacher", "click_detail_card", { x: Math.round(box.x + box.width / 2), y: Math.round(box.y + box.height / 2), label: "点开 detail" });
    await card.click();
  } else {
    // 兜底直接 goto
    pushEvent("teacher", "goto_detail", { label: "fallback: goto detail URL" });
    await teaPage.goto(`${TEA_BASE}/#/pages/questions/detail?id=${convId}`);
  }
} catch {
  pushEvent("teacher", "goto_detail_fallback", { label: "fallback after error" });
  await teaPage.goto(`${TEA_BASE}/#/pages/questions/detail?id=${convId}`);
}

await sleep(2500);
pushEvent("teacher", "detail_loaded", { label: "看到学生消息" });

// 老师"接单"操作（如果有 accept 按钮）
// TODO selector: accept 按钮
try {
  await teaPage.locator('button:has-text("接单"), button:has-text("接受")').first().click({ timeout: 2000 });
  pushEvent("teacher", "click_accept", { label: "点击接单" });
} catch { /* 可能自动 accept */ }

await sleep(2000);

// ─── 22-37s: 教师打字 + 3 次连发 ────────────────────────────────
const messages = [
  "你好，关于奖学金加分政策，我们这边有专门的核实流程。",
  "你需要先在校务系统提交家庭情况说明 + 户籍证明扫描件。",
  "审核周期大概 3 个工作日，结果会通过校园短信通知你。",
];

for (let i = 0; i < messages.length; i++) {
  const msg = messages[i];
  // TODO selector: 教师端输入框
  try {
    await teaPage.locator('textarea, .reply-input textarea').first().fill(msg);
    pushEvent("teacher", "type_msg", { idx: i + 1, content: msg });
    await sleep(800);
    // TODO selector: 发送按钮
    await teaPage.locator('button:has-text("发送"), .send-btn').first().click({ timeout: 2000 });
    const sendTs = now();
    pushEvent("teacher", "send_msg", { idx: i + 1, t_sent: sendTs });

    // 学生端通过 Centrifugo 自动收到 — 这边等 2s 让推送完成 + UI 渲染
    await sleep(1500);
    pushEvent("student", "recv_msg", { idx: i + 1, t_recv: now(), latency_ms: now() - sendTs });

    await sleep(2000); // 给观众反应时间
  } catch (e) {
    log("err", `send msg ${i + 1} failed: ${e?.message || e}`);
    break;
  }
}

// ─── 37-50s: 学生回复 + 教师标已解决 ───────────────────────────
// 学生用 API 发回复（不在 UI 操作，避免学生 page 失焦）
await api("POST", `/api/conversations/${convId}/messages`, stuToken, {
  content: "谢谢老师！我下周就去提交材料。",
});
pushEvent("student", "send_reply", { content: "谢谢老师！我下周就去提交材料。" });
await sleep(2500);
pushEvent("teacher", "recv_student_reply", { label: "教师端收到学生回复" });

// 教师标已解决
// TODO selector: 标记已解决按钮
try {
  await teaPage.locator('button:has-text("已解决"), button:has-text("解决"), button:has-text("结束")').first().click({ timeout: 3000 });
  pushEvent("teacher", "mark_resolved", { label: "标记已解决" });
} catch {
  // 兜底用 API
  await api("POST", `/api/conversations/${convId}/resolve`, teaToken);
  pushEvent("teacher", "mark_resolved_api", { label: "fallback: API resolve" });
}

await sleep(3000);

// ============================================================
// === 录制结束 ===
// ============================================================
const duration_ms = now();
log("phase", `=== dual recording end (${duration_ms}ms) ===`);

pushEvent("student", "stream_end", { duration_ms });
pushEvent("teacher", "stream_end", { duration_ms });

await Promise.all([stuPage.close(), teaPage.close()]);
await Promise.all([stuCtx.close(), teaCtx.close()]);

// rename auto-generated webm 到稳定文件名
const renameLatest = (dir, target) => {
  const files = readdirSync(dir).filter((f) => f.endsWith(".webm") && f !== target);
  if (files.length === 0) return;
  files.sort();
  const src = join(dir, files[files.length - 1]); // 最新的
  const dst = join(dir, target);
  renameSync(src, dst);
};
renameLatest(join(OUT_DIR, "student"), "student.webm");
renameLatest(join(OUT_DIR, "teacher"), "teacher.webm");

// emit events
writeFileSync(join(OUT_DIR, "student", "events.json"), JSON.stringify({
  task: "T13-D3-student",
  url: STU_BASE,
  viewport: VIEWPORT,
  fps: FPS,
  duration_ms,
  events: studentEvents,
}, null, 2));
writeFileSync(join(OUT_DIR, "teacher", "events.json"), JSON.stringify({
  task: "T13-D3-teacher",
  url: TEA_BASE,
  viewport: VIEWPORT,
  fps: FPS,
  duration_ms,
  events: teacherEvents,
}, null, 2));

// emit sync.json (双方对齐元信息)
writeFileSync(join(OUT_DIR, "sync.json"), JSON.stringify({
  task: "T13-D3-dual",
  conv_id: convId,
  student_user_id: stuMe.data.id,
  teacher_user_id: teaMe.data.id,
  t0_epoch_ms: t0,
  setup_duration_ms: setupDurationMs,  // setup 段在 video 开头，Remotion 可剪掉
  total_duration_ms: duration_ms,
  viewport: VIEWPORT,
  fps: FPS,
  notes: [
    "两个 webm 视频从同一 t0 开始（context.newContext 后立刻 setupDurationMs 内）",
    "Remotion 应用 setup_duration_ms 修剪两端开头",
    "对齐方法: video.startFrame = round(setup_duration_ms / 1000 * fps)",
  ],
}, null, 2));
log("done", `outputs in ${OUT_DIR}/`);
log("done", `  student: ${studentEvents.length} events`);
log("done", `  teacher: ${teacherEvents.length} events`);

await browser.close();
