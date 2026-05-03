import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const DIR = 'screenshots/teacher-gradient-fix';
mkdirSync(DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
const page = await ctx.newPage();

// Login with anjing (known working)
await page.goto('http://localhost:5300', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
const inputs = await page.$$('input');
await inputs[0].fill('anjing');
await inputs[1].fill('Anjing@yxg2026');
await page.waitForTimeout(500);
await page.click('button');
await page.waitForTimeout(5000);

// Check current URL
const url = page.url();
console.log(`Current URL: ${url}`);
await page.screenshot({ path: `${DIR}/05-post-login.png` });
console.log('📸 05-post-login');

// If we're on dashboard, take screenshot
if (url.includes('dashboard')) {
  console.log('✅ Successfully on dashboard');
} else {
  // Try navigating
  await page.evaluate(() => {
    window.location.hash = '#/pages/dashboard/index';
  });
  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${DIR}/06-dashboard-nav.png` });
  console.log('📸 06-dashboard-nav');
}

await browser.close();
console.log('=== Done ===');
