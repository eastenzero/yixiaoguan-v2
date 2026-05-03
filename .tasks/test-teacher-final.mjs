import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const DIR = 'screenshots/teacher-gradient-fix';
mkdirSync(DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
const page = await ctx.newPage();

// Login (same approach as working test-teacher.mjs)
await page.goto('http://localhost:5300', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
const inputs = await page.$$('input');
console.log(`Found ${inputs.length} inputs`);
await inputs[0].click();
await page.keyboard.type('anjing', { delay: 15 });
await inputs[1].click();
await page.keyboard.type('Anjing@yxg2026', { delay: 15 });

// Click submit using the same selector that worked before
const submitBtn = await page.$('button');
if (submitBtn) {
  await submitBtn.click();
  console.log('Clicked button');
} else {
  const allBtns = await page.$$('.login-btn');
  console.log(`Found ${allBtns.length} .login-btn`);
  if (allBtns[0]) await allBtns[0].click();
}
await page.waitForTimeout(5000);
await page.screenshot({ path: `${DIR}/10-dashboard-after-login.png` });
console.log('📸 10-dashboard-after-login');

await browser.close();
console.log('=== Done ===');
