import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const DIR = 'screenshots/teacher-test';
mkdirSync(DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
const page = await ctx.newPage();

// Collect console messages
const consoleLogs = [];
page.on('console', msg => {
  consoleLogs.push({ type: msg.type(), text: msg.text() });
});

const snap = async (name) => {
  await page.screenshot({ path: `${DIR}/${name}.png` });
  console.log(`📸 ${name}`);
};

// 1. Login page
await page.goto('http://localhost:5300', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await snap('01-login');

// 2. Login with teacher credentials
const inputs = await page.$$('input');
console.log(`  Found ${inputs.length} inputs`);
if (inputs.length >= 2) {
  await inputs[0].click();
  await page.keyboard.type('anjing', { delay: 15 });
  await inputs[1].click();
  await page.keyboard.type('Anjing@yxg2026', { delay: 15 });
  await snap('02-login-filled');
  
  // Submit
  const submitBtn = await page.$('button') || await page.$('.submit-btn') || await page.$('.login-btn');
  if (submitBtn) {
    await submitBtn.click();
  } else {
    // Try clicking any button-like element
    const btns = await page.$$('button, .btn, .submit-btn, .login-btn');
    console.log(`  Found ${btns.length} buttons`);
    if (btns.length > 0) await btns[0].click();
  }
  await page.waitForTimeout(3000);
  await snap('03-after-login');
}

// 3. Dashboard page
await page.goto('http://localhost:5300/#/pages/dashboard/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await snap('04-dashboard-top');

// Scroll down
await page.mouse.move(195, 500);
await page.mouse.wheel(0, 300);
await page.waitForTimeout(500);
await snap('05-dashboard-scroll1');

await page.mouse.wheel(0, 300);
await page.waitForTimeout(500);
await snap('06-dashboard-scroll2');

// 4. Questions page
await page.goto('http://localhost:5300/#/pages/questions/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await snap('07-questions-list');

await page.mouse.move(195, 500);
await page.mouse.wheel(0, 300);
await page.waitForTimeout(500);
await snap('08-questions-scroll');

// 5. Click first question to see detail
const questionCards = await page.$$('.question-card, .card, .list-item');
console.log(`  Found ${questionCards.length} question cards`);
if (questionCards.length > 0) {
  await questionCards[0].click();
  await page.waitForTimeout(2000);
  await snap('09-question-detail');
  
  // Scroll detail page
  await page.mouse.move(195, 500);
  await page.mouse.wheel(0, 300);
  await page.waitForTimeout(500);
  await snap('10-question-detail-scroll');
  
  // Go back
  const backBtn = await page.$('.back-btn, .app-bar-left, [class*=back]');
  if (backBtn) {
    await backBtn.click();
    await page.waitForTimeout(1000);
  }
}

// 6. Knowledge page
await page.goto('http://localhost:5300/#/pages/knowledge/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await snap('11-knowledge-list');

// 7. Profile page
await page.goto('http://localhost:5300/#/pages/profile/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
await snap('12-profile');

await page.mouse.move(195, 500);
await page.mouse.wheel(0, 300);
await page.waitForTimeout(500);
await snap('13-profile-scroll');

// 8. Check console logs for WebSocket noise
console.log('\n=== Console Logs Summary ===');
const wsLogs = consoleLogs.filter(l => l.text.toLowerCase().includes('websocket') || l.text.toLowerCase().includes('ws'));
const errorLogs = consoleLogs.filter(l => l.type === 'error');
const warnLogs = consoleLogs.filter(l => l.type === 'warning');
console.log(`  Total console messages: ${consoleLogs.length}`);
console.log(`  WebSocket-related: ${wsLogs.length}`);
console.log(`  Errors: ${errorLogs.length}`);
console.log(`  Warnings: ${warnLogs.length}`);

if (wsLogs.length > 0) {
  console.log('\n  WebSocket messages (first 10):');
  wsLogs.slice(0, 10).forEach(l => console.log(`    [${l.type}] ${l.text.slice(0, 120)}`));
}
if (errorLogs.length > 0) {
  console.log('\n  Error messages (first 10):');
  errorLogs.slice(0, 10).forEach(l => console.log(`    ${l.text.slice(0, 120)}`));
}

// Print ALL console logs (first 30)
console.log('\n  All console messages (first 30):');
consoleLogs.slice(0, 30).forEach(l => console.log(`    [${l.type}] ${l.text.slice(0, 150)}`));

await browser.close();
console.log('\n=== Teacher App Test Done ===');
