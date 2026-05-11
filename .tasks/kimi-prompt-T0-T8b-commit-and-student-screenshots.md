# Kimi 派单 · T0 + T8b · UI commit + 学生端 audit 截图

> 2026-05-11 23:25 导演产出（Cascade）
> Kimi 直接读本文件按步骤跑即可。完成后回报 commit hash + 截图目录路径。

---

## 项目上下文（一句话）

医小管演示视频项目 Phase 1 启动。UI polish 改动还在工作区未 commit，需要先 commit；同时学生端的 audit 截图脚本还没写（教师端的 `teacher-audit-capture.mjs` 已成熟可参考）。

## 工作目录

```
F:\Documents\code\yixiaoguan-v2
```

> ⚠️ 不要在 worktree 里搞 git。所有命令带 `git -C F:\Documents\code\yixiaoguan-v2 ...` 或者在该目录直接跑。

## 现状

- 当前分支：`fix/realtime-user-channel-push`（HEAD `b38a78e`）
- 工作区改动（来自上个对话的 UI polish 工作）：
  - `apps/student-app/`：`index.html` 大改 +54, `chat/index.vue` 微调 +4, `vite.config.ts` 临时改 10
  - `apps/teacher-app/`：8 个 pages.vue + TopAppBar + tokens.scss + index.html，合计 +755 行
- 教师端 audit 截图已就绪：`.tasks/teacher-ui-audit-2026-05-11/after-avatar/` 11 张 PNG 完整（无需重做）
- 学生端 audit 截图：**还没写脚本，本任务负责**

## 测试账号 / 端点（165 dev backend）

- API base: `http://192.168.100.165:8100`
- 学生端 dev：`http://localhost:3001`
- 学生：`4125150011` / `4125150011`
- 教师：`anjing` / `Anjing@yxg2026`

## 任务 1：T0 commit UI polish（先做，5 分钟）

### 步骤

```powershell
# 1. 验证工作区状态（应该看到 apps/ 下 15 个文件改动）
git -C F:\Documents\code\yixiaoguan-v2 status -s -- apps/

# 2. 只 add apps/ 目录（不要 add 其他 .tasks/ .playwright-cli/ 等垃圾）
git -C F:\Documents\code\yixiaoguan-v2 add apps/

# 3. 确认 staged 改动只在 apps/ 下
git -C F:\Documents\code\yixiaoguan-v2 diff --cached --stat

# 4. commit（message 不含 # 字符以避免 PowerShell 截断）
git -C F:\Documents\code\yixiaoguan-v2 commit -m "feat(ui): teacher-app polish + student-app chat bottom-spacer"

# 5. 显示新 commit
git -C F:\Documents\code\yixiaoguan-v2 log --oneline -3
```

### 不要做的事

- ❌ 不要 push（导演会在后面统一 push）
- ❌ 不要 add `.tasks/` / `.playwright-cli/` / `.tmp/` 这些工作区残留
- ❌ 不要切分支，就在 `fix/realtime-user-channel-push` 上 commit

### 验收

- 新 commit 改动 15 个文件，全部在 `apps/` 下
- 工作区 `apps/` 下应该 clean（`git status -s -- apps/` 无输出）

---

## 任务 2：T8b 学生端 audit 截图（30-60 分钟）

### 目标

抄一份 `.tmp/demo-video/teacher-audit-capture.mjs` → 改造为 `.tmp/demo-video/student-audit-capture.mjs`，针对学生端跑全页截图。

### 抄改要点

**学生端 vs 教师端差异**：

| 字段 | 教师端 | 学生端 |
|---|---|---|
| dev base | `TEA_BASE = "http://localhost:5301"` | `STU_BASE = "http://localhost:3001"` |
| API base | `API_DIRECT = "http://192.168.100.165:8100"` | 一样 |
| token key (localStorage) | `teacher-token` | `v2-token` |
| user-info key | `teacher-user-info` | `v2-user-info` |
| 登录账号 | `anjing` / `Anjing@yxg2026` | `4125150011` / `4125150011` |
| viewport | `393×852` + iPhone UA + DPR 2 | **一样**（学生端也是 mobile） |
| 输出目录 | `.tasks/teacher-ui-audit-2026-05-11/<phase>/` | `.tasks/student-ui-audit-2026-05-11/<phase>/` |
| phase 参数 | `before/after/after-seed/after-avatar` | 一样（这次只跑 `after-avatar`） |

### 学生端路由清单（pages.json 已确认）

```js
const routes = [
  { name: "01-login", path: "/#/pages/login/index", noAuth: true, wait: 1500 },
  { name: "02-home", path: "/#/pages/home/index", wait: 2500 },
  { name: "03-chat-empty", path: "/#/pages/chat/index", wait: 2500 },
  { name: "04-chat-with-conv", path: `/#/pages/chat/index?convId=${demoConvId}`, wait: 3500 },
  { name: "05-history", path: "/#/pages/chat/history", wait: 2500 },
  { name: "06-services", path: "/#/pages/services/index", wait: 2500 },
  { name: "07-profile", path: "/#/pages/profile/index", wait: 2000 },
];
```

> 关于 `demoConvId`：用 demo seed 数据中的任一已 `teacher_serving` 或 `resolved` 状态的 conv。可以用学生 4125150011 自己的 conv（教师端有 30+ 条 [demo] 标记的，里面应该有 4125150011 提的）。

> 兜底：如果学生 4125150011 没有自己的 conv，先用 API 让他创建一条 + 发消息 + escalate（参考 teacher 版本的 demo conv 准备逻辑），拿到 convId 用于 `04-chat-with-conv`。

### 关键代码骨架（直接抄）

```js
import { chromium } from "playwright";
import { mkdirSync, writeFileSync } from "node:fs";
import { join, resolve } from "node:path";

const phase = (process.argv[2] || "after-avatar").toLowerCase();
const STU_BASE = "http://localhost:3001";
const API_DIRECT = "http://192.168.100.165:8100";
const REPO_ROOT = resolve(import.meta.dirname, "..", "..");
const OUT = resolve(REPO_ROOT, ".tasks", "student-ui-audit-2026-05-11", phase);
mkdirSync(OUT, { recursive: true });

const log = (k, msg) => process.stdout.write(`[${new Date().toISOString().slice(11, 23)}] [${k}] ${msg}\n`);

async function api(method, path, token, body) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(API_DIRECT + path, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch {}
  return { status: res.status, data };
}

// 1. 学生登录
log("phase", "1. 学生 API 登录");
const stuLogin = await api("POST", "/api/auth/login", null, {
  staff_id: "4125150011",
  password: "4125150011",
});
if (stuLogin.status !== 200) {
  log("fatal", `学生登录失败: ${stuLogin.status}`);
  process.exit(1);
}
const stuToken = stuLogin.data.access_token;
const stuMe = await api("GET", "/api/auth/me", stuToken);
const stuUserInfo = JSON.stringify(stuMe.data);
log("api", `学生 user_id=${stuMe.data.id}`);

// 2. 准备一条 demo conv 用于 04-chat-with-conv
let demoConvId = 0;
try {
  // 先尝试拿学生自己最近的 conv
  const list = await api("GET", "/api/conversations?page=1&size=10", stuToken);
  if (list.status === 200 && list.data?.items?.length) {
    // 优先挑 teacher_serving / resolved 的
    const preferred = list.data.items.find(c =>
      ["teacher_serving", "resolved"].includes(c.status)
    );
    demoConvId = (preferred || list.data.items[0]).id;
    log("api", `复用已有 conv id=${demoConvId} status=${(preferred || list.data.items[0]).status}`);
  } else {
    // 兜底：临时造一条
    const conv = await api("POST", "/api/conversations", stuToken, {
      title: "[ui-audit] 学生端 UI 截图示例",
    });
    if ([200, 201].includes(conv.status)) {
      demoConvId = conv.data.id;
      await api("POST", `/api/conversations/${demoConvId}/messages`, stuToken, {
        content: "老师好，我想咨询一下选课系统什么时候开放。",
      });
      log("api", `临时创建 conv id=${demoConvId}`);
    }
  }
} catch (e) {
  log("warn", `准备 demo conv 失败: ${e?.message || e}`);
}
if (!demoConvId) demoConvId = 1;

// 3. 启动浏览器，注入学生 token
log("phase", "2. 启动 Chromium 注入学生 token");
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({
  viewport: { width: 393, height: 852 },
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
  deviceScaleFactor: 2,
});
await ctx.addInitScript(({ tk, ui }) => {
  localStorage.setItem("v2-token", tk);
  localStorage.setItem("v2-user-info", ui);
}, { tk: stuToken, ui: stuUserInfo });

const page = await ctx.newPage();

const routes = [
  { name: "01-login", path: "/#/pages/login/index", noAuth: true, wait: 1500 },
  { name: "02-home", path: "/#/pages/home/index", wait: 2500 },
  { name: "03-chat-empty", path: "/#/pages/chat/index", wait: 2500 },
  { name: "04-chat-with-conv", path: `/#/pages/chat/index?convId=${demoConvId}`, wait: 3500 },
  { name: "05-history", path: "/#/pages/chat/history", wait: 2500 },
  { name: "06-services", path: "/#/pages/services/index", wait: 2500 },
  { name: "07-profile", path: "/#/pages/profile/index", wait: 2000 },
];

// 登录页用独立 context（不注入 token，避免被自动跳转）
const noAuthCtx = await browser.newContext({
  viewport: { width: 393, height: 852 },
  userAgent: "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X)",
  deviceScaleFactor: 2,
});
const noAuthPage = await noAuthCtx.newPage();

const results = [];

for (const r of routes) {
  try {
    const usePage = r.noAuth ? noAuthPage : page;
    log("nav", `→ ${r.name} (${r.path})`);
    await usePage.goto("about:blank");
    await usePage.goto(STU_BASE + r.path, { waitUntil: "load", timeout: 20000 });
    await usePage.waitForLoadState("networkidle", { timeout: 8000 }).catch(() => {});
    await usePage.waitForTimeout(r.wait);
    const file = join(OUT, `${r.name}.png`);
    await usePage.screenshot({ path: file, fullPage: true });
    log("snap", `✓ ${file}`);
    results.push({ name: r.name, path: r.path, ok: true });
  } catch (e) {
    log("err", `✗ ${r.name}: ${e?.message || e}`);
    results.push({ name: r.name, path: r.path, ok: false, error: String(e?.message || e) });
  }
}

writeFileSync(join(OUT, "_index.json"), JSON.stringify({
  phase,
  captured_at: new Date().toISOString(),
  demo_conv_id: demoConvId,
  student_user_id: stuMe.data.id,
  routes: results,
}, null, 2));

await browser.close();
log("done", `截图完成 → ${OUT}`);
```

### 执行

```powershell
cd F:\Documents\code\yixiaoguan-v2
node .tmp/demo-video/student-audit-capture.mjs after-avatar
```

### 验收

- `.tasks/student-ui-audit-2026-05-11/after-avatar/` 下有 7 张 PNG（每张 > 50 KB）
- `_index.json` 中 7 个 routes 全部 `ok: true`
- 视觉抽查：
  - `02-home.png` 应能看到首页问候 + 16 个事务格子（或快捷入口）
  - `04-chat-with-conv.png` 应能看到学生 + 老师/AI 的消息气泡
  - `07-profile.png` 应能看到学生姓名 / 班级 / 头像（如已 polish）

---

## 完成后回报

在主对话报告：

1. T0 commit hash（新生成的）
2. T8b 截图目录的 `_index.json` 路径
3. 7 张 PNG 的 `ls` 输出 + 每张大小

导演会立刻进 **T10 AE 重渲**（用真截图替换 4 个 SCENE 占位）。

## 不要做的事

- ❌ 不要 push 任何 commit
- ❌ 不要 merge 到 master
- ❌ 不要改 `services/gateway/` 后端代码
- ❌ 不要动 `vite.config.ts` 临时改的 165 proxy（演示完才能 revert）
- ❌ 不要关闭 SSH tunnel `localhost:18000`（Centrifugo proxy 用着）
