# UI 美化 + 宣传界面 — handoff prompt

> 给下一轮 AI 的简短上手 prompt。直接 paste 即可。

---

## 任务

医小管 v2（`F:\Documents\code\yixiaoguan-v2`）实时推送已修完。现在需要：

1. **重点：教师端 UI 美化 + 逻辑梳理** — 目前粗糙、配色/间距/字号不统一、状态切换逻辑混乱
2. 学生端再打磨（已对齐 tokens，但还能精进）
3. **加分项：宣传/演示数据 mock 填充** — 让 dashboard / 工单列表 / 知识库看起来饱满，方便对外演示

## 工作区状态

- 当前分支：`fix/realtime-user-channel-push`（实时推送修复，**别合 master、别动后端**）
- 后端跑在 165 dev：`http://192.168.100.165:8100`
- Centrifugo 走 SSH tunnel：`localhost:18000`（已开，别关）

## Dev server（已经跑着）

- 学生端：`http://localhost:3001`
- 教师端：`http://localhost:5301`

如果挂了重启：
```bash
# student
pnpm --dir apps/student-app dev:h5
# teacher
pnpm --dir apps/teacher-app dev:h5
```

## 测试账号（165 dev backend）

- 学生：`4125150011` / `4125150011`（有 college/class，RAG 正常）
- 教师：`anjing` / `Anjing@yxg2026`

## 用 Playwright 看实际效果（不要只看 .vue 源码）

抄 `.tmp/demo-video/test-realtime-v7.mjs` 套路，最简模板：

```js
import { chromium } from "playwright";

// 先 API 拿 token
const r = await fetch("http://192.168.100.165:8100/api/auth/login", {
  method: "POST", headers: {"Content-Type": "application/json"},
  body: JSON.stringify({ staff_id: "anjing", password: "Anjing@yxg2026" })
});
const { access_token } = await r.json();

const browser = await chromium.launch({ headless: false });
const ctx = await browser.newContext({ viewport: { width: 393, height: 852 } });

// 教师端 token key 是 teacher-token；学生端是 v2-token
await ctx.addInitScript(({ tk }) => {
  localStorage.setItem("teacher-token", tk);
}, { tk: access_token });

const page = await ctx.newPage();
await page.goto("http://localhost:5301/#/pages/dashboard/index", { waitUntil: "load" });
await page.waitForTimeout(3000);
await page.screenshot({ path: "out/teacher-dashboard.png", fullPage: true });
```

把 `pages/dashboard/index` 换成各页面 path 全跑一遍，做"现状审计表"再开工。

## 教师端重点文件

```
apps/teacher-app/src/styles/tokens.scss              # design tokens（核对是否对齐学生端）
apps/teacher-app/src/pages/dashboard/index.vue       # 工作台首页（数据卡片粗糙）
apps/teacher-app/src/pages/questions/index.vue       # 工单列表
apps/teacher-app/src/pages/questions/detail.vue      # 工单详情（含回复 textarea）
apps/teacher-app/src/pages/knowledge/*.vue           # 知识入库（数据稀疏）
apps/teacher-app/src/pages/profile/index.vue         # 个人中心
apps/teacher-app/src/pages/login/index.vue           # 登录页
apps/teacher-app/src/components/TopAppBar.vue        # 通用顶栏
```

## 学生端标杆参考（对齐用）

```
apps/student-app/src/styles/tokens.scss              # tokens 体系
apps/student-app/src/pages/chat/index.vue            # AI 聊天页（精致）
apps/student-app/src/pages/services/index.vue        # 事务导办
apps/student-app/src/pages/home/index.vue
```

## 宣传/演示数据填充思路

教师端很多页面没数据时空荡荡。建议做：

- `services/gateway/scripts/seed-demo-data.py`：生成 N 条假 conversation / message / knowledge entry，绑到现有 21 个 college 的 stu1/stu2/...，用 Faker zh_CN
- 仅在 dev/staging 跑（看 `.env` 里的 `app_env`），prod 不动
- 跑完 demo 再 `delete from conversations where id > X` 清理
- 这样 demo 视频里 dashboard 数字、工单列表都很饱满

## 不要破坏

- `services/gateway/` 后端代码（实时推送修复刚搞完）
- `vite.config.ts` 临时 165 proxy + `localhost:18000` rewrite（演示完才能 revert）
- SSH tunnel `ssh -N -L 18000:127.0.0.1:8000 easten@192.168.100.165`
- `.tasks/realtime-fix-postmortem-20260511.md` 这份复盘日志

## 跑完别忘

修完 UI 跑一遍 `node .tmp/demo-video/test-realtime-v7.mjs`，确认实时聊天 T1+T2+T3 还 PASS。
