import { chromium } from 'playwright';
import { mkdirSync } from 'fs';

const DIR = 'screenshots/teacher-gradient-v2';
mkdirSync(DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true });
const page = await ctx.newPage();

// Login
await page.goto('http://localhost:5300', { waitUntil: 'networkidle' });
await page.waitForTimeout(2000);
const inputs = await page.$$('input');
console.log(`Found ${inputs.length} inputs`);
if (inputs.length >= 2) {
  await inputs[0].click();
  await page.keyboard.type('anjing', { delay: 15 });
  await inputs[1].click();
  await page.keyboard.type('Anjing@yxg2026', { delay: 15 });
  const btns = await page.$$('.login-btn');
  console.log(`Found ${btns.length} .login-btn`);
  if (btns[0]) await btns[0].click();
  await page.waitForTimeout(5000);
  
  // Screenshot whatever page we're on after login
  await page.screenshot({ path: `${DIR}/01-after-login.png` });
  console.log('📸 01-after-login');
  
  // Try profile too
  await page.goto('http://localhost:5300/#/pages/profile/index', { waitUntil: 'networkidle' });
  await page.waitForTimeout(2000);
  await page.screenshot({ path: `${DIR}/02-profile.png` });
  console.log('📸 02-profile');
}

await browser.close();
console.log('=== Done ===');
