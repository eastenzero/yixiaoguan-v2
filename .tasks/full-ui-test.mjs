import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const DIR = 'screenshots/full-test';
mkdirSync(DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
const page = await ctx.newPage();
let idx = 0;

async function snap(name) {
  idx++;
  const file = `${DIR}/${String(idx).padStart(2, '0')}-${name}.png`;
  await page.screenshot({ path: file });
  console.log(`📸 ${file}`);
}

async function scrollDown(px = 400) {
  await page.mouse.move(195, 500);
  await page.mouse.wheel(0, px);
  await page.waitForTimeout(400);
}

async function scrollUp(px = 400) {
  await page.mouse.move(195, 500);
  await page.mouse.wheel(0, -px);
  await page.waitForTimeout(400);
}

// ============================================
// 1. LOGIN PAGE
// ============================================
console.log('\n=== 1. LOGIN PAGE ===');
await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await snap('login-empty');

// Test empty submit
await page.click('.submit-btn');
await page.waitForTimeout(500);
await snap('login-empty-submit');

// Type credentials
const inputs = await page.$$('input');
await inputs[0].click();
await page.keyboard.type('4125150012', { delay: 15 });
await snap('login-staffid-filled');

await inputs[1].click();
await page.keyboard.type('4125150012', { delay: 15 });
await snap('login-both-filled');

// Submit
await page.click('.submit-btn');
await page.waitForTimeout(3000);
await snap('login-success');

// ============================================
// 2. HOME PAGE
// ============================================
console.log('\n=== 2. HOME PAGE ===');
await page.goto('http://localhost:3000/#/pages/home/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await snap('home-top');

await scrollDown(400);
await snap('home-scroll1');

await scrollDown(400);
await snap('home-scroll2');

await scrollDown(400);
await snap('home-scroll3');

// Scroll back to top
await scrollUp(1200);
await page.waitForTimeout(300);

// Test tag chips scroll
await snap('home-tags');

// ============================================
// 3. CHAT PAGE (empty state)
// ============================================
console.log('\n=== 3. CHAT PAGE ===');
await page.goto('http://localhost:3000/#/pages/chat/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await snap('chat-empty');

// Test input focus
const chatInput = await page.$('.chat-input input, .input-bar input, textarea, .msg-input input');
if (chatInput) {
  await chatInput.click();
  await page.waitForTimeout(300);
  await snap('chat-input-focused');
  await page.keyboard.type('测试消息');
  await snap('chat-input-typed');
  // Don't actually send - just test the UI
  await page.keyboard.press('Escape');
}

// ============================================
// 4. SERVICES PAGE (full scroll)
// ============================================
console.log('\n=== 4. SERVICES PAGE ===');
await page.goto('http://localhost:3000/#/pages/services/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await snap('services-top');

await scrollDown(300);
await snap('services-scroll1');

await scrollDown(300);
await snap('services-scroll2');

await scrollDown(300);
await snap('services-scroll3');

await scrollDown(300);
await snap('services-scroll4');

// Scroll back to test clicking an AI-question item
await scrollUp(1200);
await page.waitForTimeout(300);

// Test clicking 空教室申请 (AI question item - first in grid)
const campusItems = await page.$$('.campus-item');
if (campusItems.length > 0) {
  await campusItems[0].click(); // 空教室申请
  await page.waitForTimeout(1000);
  await snap('services-ai-redirect');
  // Go back to services
  await page.goto('http://localhost:3000/#/pages/services/index', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1000);
}

// Test clicking 更多 (last campus item)
await scrollDown(400);
await page.waitForTimeout(300);
if (campusItems.length > 0) {
  const moreBtn = campusItems[campusItems.length - 1];
  if (moreBtn) {
    await moreBtn.click();
    await page.waitForTimeout(1000);
    await snap('services-more-click');
    await page.goto('http://localhost:3000/#/pages/services/index', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);
  }
}

// ============================================
// 5. PROFILE PAGE
// ============================================
console.log('\n=== 5. PROFILE PAGE ===');
await page.goto('http://localhost:3000/#/pages/profile/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await snap('profile-top');

await scrollDown(300);
await snap('profile-scroll1');

await scrollDown(300);
await snap('profile-scroll2');

await scrollDown(300);
await snap('profile-scroll3');

// Test clicking 消息通知 (comingSoon)
await scrollUp(600);
await page.waitForTimeout(300);
const settingsRows = await page.$$('.settings-row');
if (settingsRows.length > 0) {
  await settingsRows[0].click(); // 消息通知
  await page.waitForTimeout(800);
  await snap('profile-coming-soon-sheet');

  // Close the sheet
  const overlay = await page.$('.sheet-overlay');
  if (overlay) {
    await overlay.click();
    await page.waitForTimeout(500);
  }
}

// Test clicking 关于医小管
if (settingsRows.length >= 5) {
  await settingsRows[4].click(); // 关于医小管
  await page.waitForTimeout(800);
  await snap('profile-about-modal');

  // Close modal
  const confirmBtn = await page.$('.uni-modal__btn_primary');
  if (confirmBtn) {
    await confirmBtn.click();
    await page.waitForTimeout(500);
  }
}

// ============================================
// 6. CHAT HISTORY PAGE
// ============================================
console.log('\n=== 6. CHAT HISTORY PAGE ===');
await page.goto('http://localhost:3000/#/pages/chat/history', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await snap('history-list');

await scrollDown(300);
await snap('history-scroll1');

// ============================================
// 7. TAB BAR TESTS
// ============================================
console.log('\n=== 7. TAB BAR ===');
await page.goto('http://localhost:3000/#/pages/home/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await snap('tabbar-home-active');

// Click each tab
const tabItems = await page.$$('.tab-item, .tabbar-item');
console.log(`  Found ${tabItems.length} tab items`);

// ============================================
// 8. RESPONSIVE CHECK (wider viewport)
// ============================================
console.log('\n=== 8. WIDER VIEWPORT (414px) ===');
await page.setViewportSize({ width: 414, height: 896 }); // iPhone 11 Pro Max
await page.goto('http://localhost:3000/#/pages/home/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await snap('wide-home');

await page.goto('http://localhost:3000/#/pages/services/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await snap('wide-services');

// ============================================
// 9. NARROW VIEWPORT (320px)
// ============================================
console.log('\n=== 9. NARROW VIEWPORT (320px) ===');
await page.setViewportSize({ width: 320, height: 568 }); // iPhone SE
await page.goto('http://localhost:3000/#/pages/home/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await snap('narrow-home');

await page.goto('http://localhost:3000/#/pages/services/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await snap('narrow-services');

await scrollDown(400);
await snap('narrow-services-scroll');

await page.goto('http://localhost:3000/#/pages/profile/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1000);
await snap('narrow-profile');

await browser.close();
console.log('\n=== ALL TESTS COMPLETE ===');
console.log(`Total screenshots: ${idx}`);
