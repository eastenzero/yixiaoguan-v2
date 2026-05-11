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

// ─── evaluate-based click — 绕过 Playwright actionability 检查 ────────────────
// uni-app H5 把 <view>/<button>/<text> 包成 Web Component。双重保险：
//   1. 先 page.evaluate 找元素 + scrollIntoView + 拿 bbox
//   2. page.touchscreen.tap(x, y) 发送真正的触控事件（uni-app mobile 都走 @tap，el.click() 踩不动）
//   3. 插上一个同步 el.click() fallback作为残下保险
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

// uni-app @longpress 需要真正的 touchstart 保持 350ms+ 后不动 → touchend。
// Playwright 的 mouse.down/up 在手机仿真下不会转成 touch 事件，走 CDP 直发。
async function longpressJS(page, selectors, label, holdMs = 900) {
  const list = Array.isArray(selectors) ? selectors : [selectors];
  const result = await page.evaluate(({ list }) => {
    for (const sel of list) {
      const el = document.querySelector(sel);
      if (!el) continue;
      const r = el.getBoundingClientRect();
      if (r.width === 0 || r.height === 0) continue;
      return { ok: true, sel, x: r.x + r.width / 2, y: r.y + r.height / 2 };
    }
    return { ok: false };
  }, { list });
  if (!result.ok) {
    log("warn", `longpressJS "${label}" element not found`);
    return false;
  }
  try {
    const cdp = await page.context().newCDPSession(page);
    await cdp.send('Input.dispatchTouchEvent', {
      type: 'touchStart',
      touchPoints: [{ x: result.x, y: result.y, id: 0 }],
    });
    await sleep(holdMs);
    await cdp.send('Input.dispatchTouchEvent', {
      type: 'touchEnd',
      touchPoints: [],
    });
    events.push({ time_ms: now(), type: "longpress", x: Math.round(result.x), y: Math.round(result.y), label, holdMs, selector: result.sel });
    log("longpress", `${label} @ (${Math.round(result.x)},${Math.round(result.y)}) hold=${holdMs}ms`);
    return true;
  } catch (e) {
    log("err", `longpressJS "${label}" failed: ${e?.message || e}`);
    return false;
  }
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

// uni-app H5 <input> 渲染成 <input class="uni-input-input">，初始状态会带 disabled
// 属性导致 playwright.fill() 永远 timeout。通过 evaluate 直接操作 native value setter
// + 派发 input 事件让 Vue v-model 拿到值。这是经过验证的 uni-app fill 解法。
// opts.index 指定在多匹配下拿第几个（默认 0）——uni-app password input 可能不是 type=password
async function fillUni(page, selector, value, label, opts = {}) {
  const { index = 0 } = opts;
  try {
    await page.locator(selector).nth(index).waitFor({ timeout: 5000 });
    const ok = await page.evaluate(({ sel, i, val }) => {
      const els = Array.from(document.querySelectorAll(sel));
      const el = els[i];
      if (!el) return false;
      el.removeAttribute('disabled');
      el.disabled = false;
      const desc = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value');
      if (desc && desc.set) desc.set.call(el, val);
      else el.value = val;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }, { sel: selector, i: index, val: value });
    if (!ok) throw new Error("element not found");
    const box = await page.locator(selector).nth(index).boundingBox({ timeout: 1500 }).catch(() => null);
    const ev = { time_ms: now(), type: "fill", label, selector, index, value };
    if (box) { ev.x = Math.round(box.x + box.width / 2); ev.y = Math.round(box.y + box.height / 2); }
    events.push(ev);
    log("fill", `${label}[${index}] = "${value}"`);
  } catch (e) {
    log("err", `fillUni "${label}" failed: ${e?.message || e}`);
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

// ─── AI 流答镜头跟随：直接 page.evaluate 采样 scrollHeight ──────────────────
// 跟 clickJS 一样，绕过 Playwright locator（uni-app Web Component 不友好）
// 注意：内部用 Date.now() 比较 wallclock，不混 now() 相对时间（原版有此 bug）
async function streamingSample(page, selector, maxMs = 25000, settleMs = 2000) {
  const startWall = Date.now();
  events.push({ time_ms: now(), type: "ai_streaming_start", selector });
  const heights = [];
  let lastChange = Date.now();
  let sawElement = false;
  while (Date.now() - lastChange < settleMs) {
    if (Date.now() - startWall > maxMs) break;
    const h = await page.evaluate((sel) => {
      const els = document.querySelectorAll(sel);
      if (!els.length) return 0;
      // 取最后一个 ai-bubble（最新的 AI 答案）
      const el = els[els.length - 1];
      return el.scrollHeight || 0;
    }, selector).catch(() => 0);
    if (h > 0) {
      sawElement = true;
      const last = heights[heights.length - 1]?.height ?? 0;
      heights.push({ t: now(), height: h });
      if (h > last) lastChange = Date.now();
    } else if (!sawElement) {
      // 还没出现 AI bubble，重置 lastChange 让循环继续等
      lastChange = Date.now();
    }
    await sleep(150);
  }
  events.push({ time_ms: now(), type: "ai_streaming_end", samples: heights.length, final_height: heights[heights.length - 1]?.height });
  log("ai", `streaming done · ${heights.length} samples · final=${heights[heights.length - 1]?.height}px · elapsed=${Date.now() - startWall}ms`);
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
// 单 context 录制：page 走完 login → home → chat 全程，全部入 webm。
// 不预注入 token —— 让 page 真实展示空登录页，然后 fill + click 登录，触发后端 /api/auth/login
// 回填 token → app.vue userStore → onShow redirect 到 home，这样录到的就是真实演示。
log("phase", "启动 Chromium 录制 (recordVideo)");
const browser = await chromium.launch({ headless: false });
const context = await browser.newContext({
  ...devices["iPhone 14 Pro"],
  viewport: VIEWPORT,
  deviceScaleFactor: 3,
  recordVideo: { dir: OUT_DIR, size: VIEWPORT },
});

// 预注入 token —— 让 userStore.init() 读取到 token 后走 getMe 路径，不走 pilot。
// 这样 login 页 onShow 调 redirectIfLogged 会看到 isLoggedIn=true → switchTab home，
// 脚本能隔中看到“登录页 闪现 → home”的隐含动画，后续所有 API 都能走通。
await context.addInitScript(({ tk, ui }) => {
  try {
    localStorage.setItem("v2-token", tk);
    localStorage.setItem("v2-user-info", ui);
  } catch { }
}, { tk: stuToken, ui: stuUserInfo });

// 拦住 pilot，避免网络错误时动不动走匿名路径覆盖我们的 token
await context.route("**/api/auth/pilot-anonymous", (route) => route.fulfill({ status: 403, contentType: "application/json", body: JSON.stringify({ detail: "demo blocks pilot" }) }));

const page = await context.newPage();

// ============================================================
// === 录制开始 ===
// ============================================================
t0 = Date.now();
log("phase", "=== recording start ===");

// ─── 0-8s: 登录页 → onShow redirect → home ───────────────────────────
// Token 已通过 addInitScript 预注入。goto login 后：
//   App.vue onLaunch → userStore.init() → 读取 v2-token → getMe → isLoggedIn=true
//   → login 页 onShow → redirectIfLogged → switchTab home
// 所以会闪现登录页 ♇1s，然后自动跳到 home。这是原本剧本接受的“自动重定向”路径。
await page.goto(`${STU_BASE}/#/pages/login/index`, { waitUntil: "load" });
await pause(1500, "登录页首屏 (token 已预注入，即将 redirect)");
await snap(page, "login-empty");

// 等 redirect。如果 4s 后还不在 home，手动 goto。
for (let i = 0; i < 8; i++) {
  if (page.url().includes("/home/index")) break;
  await sleep(500);
}
if (!page.url().includes("/home/index")) {
  log("warn", `redirect 超时，URL=${page.url()}，手动 goto home`);
  await page.goto(`${STU_BASE}/#/pages/home/index`, { waitUntil: "load" });
}
await pause(800, "home 着陆");

// ─── 8-16s: home 首页 ────────────────────────────────────────────
// 若已在 home（真实登录路径），page 已经渲染好；否则上面 fallback 已 goto。
await pause(2500, "首页 hero + 快捷区");
await snap(page, "home");

// 横滑 chip 区让镜头有点动感
await page.evaluate(() => {
  const sv = document.querySelector('.tag-scroll');
  if (sv) sv.scrollBy({ left: 120, behavior: 'smooth' });
}).catch(() => { });
events.push({ time_ms: now(), type: "scroll", direction: "h", delta: 120, label: "chip 横滑" });
await pause(1500, "chip 横滑");

// 滚回顶（chip 区回正）
await page.evaluate(() => {
  const sv = document.querySelector('.tag-scroll');
  if (sv) sv.scrollTo({ left: 0, behavior: 'smooth' });
}).catch(() => { });
await pause(1500, "chip 横滑回正");
await pause(1500, "服务卡区");

// ─── 16-32s: AI 问答 + 流式回答 ──────────────────────────────────
// 自然演示路径：home 上点击 chip『宿舍电费怎么交？』
//   → home/index.vue onTagClick 写 localStorage.chat_init_query + switchTab
//   → chat/index.vue onMounted 消费 chat_init_query → sendMessage()
// chip 被包成 .tag-chip > uni-text，Playwright text= 进不去可视化 shadow，用 clickByText 走 evaluate
await clickByText(page, '宿舍电费', '.tag-chip', "快捷 chip: 宿舍电费怎么交？");
await pause(4000, "等 chat 页 mount + onMounted 消费 chat_init_query + AI 流式开始");
await snap(page, "chat-streaming-start");

// 镜头跟随：流答 22s 内采样 .msg-bubble.ai-bubble 高度（让 Remotion 后期做平滑滚动跟随）
await streamingSample(page, '.msg-bubble.ai-bubble', 22000, 2500);
await snap(page, "after-stream");
await pause(2500, "浏览 AI 完整答案 + 参考资料");

// ─── 32-42s: 来源弹层 + 翻历史 ───────────────────────────────────
// 学生端来源是内联 .cit-item（参考资料），点开后浮起 .source-overlay
const sourceOpened = await clickJS(page, ['.cit-item'], "点开来源（第一条 citation）");
if (sourceOpened) {
  await pause(3500, "查看来源详情（包含文档详情阅读镜头）");
  await snap(page, "source-modal");
  await clickJS(page, ['.source-close', '.source-overlay'], "关闭来源弹层");
  await pause(1200);
} else {
  log("warn", ".cit-item 不存在（AI 答案可能无引用），跳过来源镜头");
  await pause(3500);
}

// 切到历史：chat 页右上角 .nav-history-icon → navigateTo /pages/chat/history
await clickJS(page, ['.nav-right', '.nav-history-icon'], "进入历史");
await pause(3500, "历史列表（浏览以往 conv）");
await snap(page, "history");

// ─── 42-54s: 提复杂问题 → 转人工 ──────────────────────────────────
// 从历史返回 chat（点 nav-back-icon 或 history 列表第一项再返回）
const backed = await clickJS(page, ['.nav-back-icon', '.nav-left'], "返回 chat");
if (backed) {
  await pause(2200, "回到 chat");
} else {
  log("warn", "navBack 失败，goto chat");
  await page.goto(`${STU_BASE}/#/pages/chat/index`, { waitUntil: "load" });
  await pause(1800);
}

// 兜底：可能落在 home（switchTab 行为差异），强制 goto chat
if (!page.url().includes("/chat/index")) {
  await page.goto(`${STU_BASE}/#/pages/chat/index`, { waitUntil: "load" });
  await pause(800);
}

await fillUni(page, '.bottom-area input.uni-input-input, .welcome-input-area input.uni-input-input', "我家庭情况比较特殊，奖学金加分政策具体怎么核实？", "提复杂问题");
await pause(800);
await clickJS(page, ['.bottom-area .send-btn', '.welcome-input-area .send-btn', '.send-btn'], "发送复杂问题");
await pause(6500, "等 AI 答复（refusal 或正常）");

// 触发转人工：尝试 1) inline .inline-call-teacher → 2) longpress send → 3) API fallback
let escalated = false;
// 1) inline 转人工服务。AI 未拒答时不出现该按钮。
escalated = await clickJS(page, ['.inline-call-teacher'], "点击 inline 转人工服务");
if (!escalated) {
  log("warn", ".inline-call-teacher 没出现（AI 未拒答），尝试 CDP longpress send-btn");
  // 2) longpress send-btn → showCallMenu → 点呼叫老师菜单
  const longpressed = await longpressJS(page, ['.bottom-area .send-btn', '.send-btn'], "长按发送按钮", 900);
  if (longpressed) {
    await pause(800, "等 call-menu 弹起");
    escalated = await clickJS(page, ['.call-menu-item'], "点击 呼叫老师 菜单");
  }
  if (!escalated) {
    log("warn", "longpress / call-menu 不行，用 API fallback");
    try {
      const convList = await api("GET", "/api/conversations?page=1&size=1", stuToken);
      const cid = convList.data?.items?.[0]?.id;
      if (cid) {
        await api("POST", `/api/conversations/${cid}/escalate`, stuToken);
        events.push({ time_ms: now(), type: "api_escalate", conv_id: cid });
        log("api", `API escalate conv=${cid}`);
        escalated = true;
      }
    } catch (e3) {
      log("err", `API escalate 失败: ${e3?.message || e3}`);
    }
  }
}
events.push({ time_ms: now(), type: "escalate_done", success: escalated });

await pause(2500, "转人工 UI settle");
await snap(page, "escalated");

// ─── 54-70s: 等待 + buffer ────────────────────────────────────────
await pause(5500, "等待老师接单（学生屏幕显示『等待中』）");
await snap(page, "waiting");
await pause(3000, "buffer 收尾过渡 D2");

// ============================================================
// === 录制结束 ===
// ============================================================
const duration_ms = now();
log("phase", `=== recording end (${duration_ms}ms) ===`);

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
