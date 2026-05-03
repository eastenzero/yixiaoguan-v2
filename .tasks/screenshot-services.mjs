import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
const page = await ctx.newPage();

// Login
await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
const inputs = await page.$$('input');
await inputs[0].click();
await page.keyboard.type('4125150012', { delay: 20 });
await inputs[1].click();
await page.keyboard.type('4125150012', { delay: 20 });
await page.click('.submit-btn');
await page.waitForTimeout(3000);

// Navigate to services
await page.goto('http://localhost:3000/#/pages/services/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);

// Top view
await page.screenshot({ path: 'screenshots/svc-top.png' });
console.log('📸 svc-top');

// Scroll to middle
await page.evaluate(() => {
  const sv = document.querySelector('.main-content');
  if (sv) sv.scrollTop = 400;
});
await page.waitForTimeout(500);
await page.screenshot({ path: 'screenshots/svc-mid.png' });
console.log('📸 svc-mid');

// Scroll to bottom
await page.evaluate(() => {
  const sv = document.querySelector('.main-content');
  if (sv) sv.scrollTop = sv.scrollHeight;
});
await page.waitForTimeout(500);
await page.screenshot({ path: 'screenshots/svc-bottom.png' });
console.log('📸 svc-bottom');

// Also take home, chat, profile screenshots for review
for (const [name, url] of [
  ['home', 'http://localhost:3000/#/pages/home/index'],
  ['chat', 'http://localhost:3000/#/pages/chat/index'],
  ['profile', 'http://localhost:3000/#/pages/profile/index'],
]) {
  await page.goto(url, { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: `screenshots/review-${name}.png` });
  console.log(`📸 review-${name}`);
}

await browser.close();
console.log('=== Done ===');
