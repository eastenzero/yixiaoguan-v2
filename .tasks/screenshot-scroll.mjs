import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
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

// Screenshot 1: Top
await page.screenshot({ path: 'screenshots/svc-1-top.png' });
console.log('📸 svc-1-top');

// Swipe up using touch
async function swipeUp(px = 400) {
  await page.touchscreen.tap(195, 500);
  await page.waitForTimeout(100);
  // Use mouse wheel as fallback
  await page.mouse.move(195, 500);
  await page.mouse.wheel(0, px);
  await page.waitForTimeout(600);
}

// Screenshot 2: After first scroll
await swipeUp(500);
await page.screenshot({ path: 'screenshots/svc-2-scroll1.png' });
console.log('📸 svc-2-scroll1');

// Screenshot 3: After second scroll
await swipeUp(500);
await page.screenshot({ path: 'screenshots/svc-3-scroll2.png' });
console.log('📸 svc-3-scroll2');

// Screenshot 4: After third scroll
await swipeUp(500);
await page.screenshot({ path: 'screenshots/svc-4-scroll3.png' });
console.log('📸 svc-4-scroll3');

// Also try JS-based scroll on all possible elements
await page.evaluate(() => {
  document.querySelectorAll('*').forEach(el => {
    if (el.scrollHeight > el.clientHeight + 10) {
      console.log('Scrollable:', el.tagName, el.className, el.scrollHeight, el.clientHeight);
      el.scrollTop = el.scrollHeight;
    }
  });
});
await page.waitForTimeout(500);
await page.screenshot({ path: 'screenshots/svc-5-jsscroll.png' });
console.log('📸 svc-5-jsscroll');

await browser.close();
console.log('=== Done ===');
