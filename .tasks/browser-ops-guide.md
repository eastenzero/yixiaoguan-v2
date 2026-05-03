# 浏览器操控指南 (Playwright)

> 供 AI 助手在远端 Windows 机器上使用，用于学生端 UI 审查与自动化测试。

## 环境

- **Node.js**: 已安装
- **Playwright**: 已安装 (npm global + `.tasks/` local)
- **Chromium**: `C:\Users\Administrator\AppData\Local\ms-playwright\chromium-1217`
- **agent-browser**: v0.13.0 已安装但 daemon 在 Windows 上不可用（Unix socket 问题），不使用

## 启动开发服务器

```bash
cd apps/student-app
npm run dev:h5
# 默认 http://localhost:3000 (已从 5174 改为 3000，原端口 EACCES)
```

## Playwright 脚本位置

所有脚本在 `.tasks/` 目录，使用 `.tasks/node_modules/playwright`。

| 脚本 | 用途 |
|------|------|
| `browse.mjs` | 基础巡览：打开登录页 → 截图各页面 |
| `login-v2.mjs` | 完整登录 + 巡览：自动填表 → 登录 → 遍历所有页面并截图 |
| `browser-tool.mjs` | 通用工具脚本（open/login/tour 子命令） |

## 核心用法

### 登录并巡览所有页面

```bash
cd .tasks
node login-v2.mjs
# 截图输出到 .tasks/screenshots/
```

### 自定义脚本模板

```javascript
import { chromium } from 'playwright';
const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
const page = await ctx.newPage();

await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });

// 填写表单（uni-app v-model 需要 keyboard.type 而非 fill）
const inputs = await page.$$('input');
await inputs[0].click();
await page.keyboard.type('4125150012', { delay: 30 });
await inputs[1].click();
await page.keyboard.type('4125150012', { delay: 30 });

// 点击登录
await page.click('.submit-btn');
await page.waitForTimeout(3000);

// 导航到指定页面
await page.goto('http://localhost:3000/#/pages/home/index', { waitUntil: 'networkidle' });

// 截图
await page.screenshot({ path: 'output.png', fullPage: true });
await browser.close();
```

## 注意事项

1. **uni-app 的 v-model**: Playwright 的 `fill()` 不触发 Vue reactivity，必须用 `keyboard.type()` 逐字输入
2. **Hash 路由**: 页面 URL 格式为 `http://localhost:3000/#/pages/xxx/index`
3. **API 代理**: `vite.config.ts` 已将 `/api` 和 `/ws` 代理到 `https://yxg.xiaoguan.site`（外网 HK 服务器）
4. **viewport**: 使用 390×844 模拟 iPhone 14 Pro 尺寸
5. **PowerShell 不支持 `&&`**: 命令链接用 `;` 或分开执行

## 测试账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 学生 | 4125150012 (尾号01~47均可) | 同学号 |
| 教师 | anjing | Anjing@yxg2026 |
| 管理员 | admin | Admin@yxg2026 |

## 截图目录

`.tasks/screenshots/` — 所有自动截图存放于此。
