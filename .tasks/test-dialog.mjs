import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const DIR = 'screenshots/dialog-test';
mkdirSync(DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
const page = await ctx.newPage();

// Login
await page.goto('http://localhost:3000', { waitUntil: 'networkidle' });
const inputs = await page.$$('input');
await inputs[0].click();
await page.keyboard.type('4125150012', { delay: 15 });
await inputs[1].click();
await page.keyboard.type('4125150012', { delay: 15 });
await page.click('.submit-btn');
await page.waitForTimeout(3000);

// Go to profile
await page.goto('http://localhost:3000/#/pages/profile/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await page.screenshot({ path: `${DIR}/01-profile.png` });
console.log('📸 01-profile');

// Scroll to find settings
await page.mouse.move(195, 500);
await page.mouse.wheel(0, 300);
await page.waitForTimeout(500);

// Click '关于 医小管' (last settings item)
const settingsRows = await page.$$('.settings-row');
console.log(`  Found ${settingsRows.length} settings rows`);
if (settingsRows.length >= 5) {
  await settingsRows[4].click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${DIR}/02-about-dialog.png` });
  console.log('📸 02-about-dialog');

  // Close by clicking confirm
  const confirmBtn = await page.$('.btn-confirm');
  if (confirmBtn) {
    await confirmBtn.click();
    await page.waitForTimeout(500);
  }
}

// Click '消息通知' (first settings item) to test Coming Soon Sheet
await page.mouse.move(195, 500);
await page.mouse.wheel(0, -300);
await page.waitForTimeout(500);
if (settingsRows.length >= 1) {
  await settingsRows[0].click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${DIR}/03-coming-soon.png` });
  console.log('📸 03-coming-soon');

  // Close
  const sheetSecondary = await page.$('.btn-secondary');
  if (sheetSecondary) {
    await sheetSecondary.click();
    await page.waitForTimeout(500);
  }
}

// Scroll down to logout button
await page.mouse.wheel(0, 500);
await page.waitForTimeout(500);

// Click logout
const logoutBtn = await page.$('.logout-btn');
if (logoutBtn) {
  await logoutBtn.click();
  await page.waitForTimeout(800);
  await page.screenshot({ path: `${DIR}/04-logout-dialog.png` });
  console.log('📸 04-logout-dialog');

  // Click cancel
  const cancelBtn = await page.$('.btn-cancel');
  if (cancelBtn) {
    await cancelBtn.click();
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${DIR}/05-after-cancel.png` });
    console.log('📸 05-after-cancel');
  }
}

// Also test home page greeting
await page.goto('http://localhost:3000/#/pages/home/index', { waitUntil: 'networkidle' });
await page.waitForTimeout(1500);
await page.screenshot({ path: `${DIR}/06-home-greeting.png` });
console.log('📸 06-home-greeting');

await browser.close();
console.log('=== Done ===');
