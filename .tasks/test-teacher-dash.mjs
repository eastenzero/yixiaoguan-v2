import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const DIR = 'screenshots/teacher-gradient-fix';
mkdirSync(DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
const page = await ctx.newPage();

// Login
await page.goto('http://localhost:5300', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
const inputs = await page.$$('input');
await inputs[0].click();
await page.keyboard.type('admin', { delay: 15 });
await inputs[1].click();
await page.keyboard.type('Admin@yxg2026', { delay: 15 });
const btn = await page.$('button');
if (btn) await btn.click();
await page.waitForTimeout(4000);
await page.screenshot({ path: `${DIR}/03-after-login.png` });
console.log('📸 03-after-login');

// Navigate to dashboard explicitly
await page.goto('http://localhost:5300/#/pages/dashboard/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await page.screenshot({ path: `${DIR}/04-dashboard-final.png` });
console.log('📸 04-dashboard-final');

await browser.close();
console.log('=== Done ===');
