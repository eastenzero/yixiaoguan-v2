/**
 * Full tour: login → visit all student-app pages → screenshot each.
 */
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHOT_DIR = path.join(__dirname, 'screenshots');
fs.mkdirSync(SHOT_DIR, { recursive: true });

const BASE = process.argv[2] || 'http://localhost:3000';
const STAFF_ID = process.argv[3] || '4124150001';
const PASSWORD = process.argv[4] || '4124150001';

let browser, page;

async function shot(name) {
  const p = path.join(SHOT_DIR, `${name}.png`);
  await page.screenshot({ path: p, fullPage: true });
  console.log(`  📸 ${p}`);
}

async function waitIdle() {
  await page.waitForLoadState('networkidle', { timeout: 10000 }).catch(() => {});
  await page.waitForTimeout(500);
}

(async () => {
  browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  page = await ctx.newPage();

  // 1. Open login page
  console.log('=== 1. Login Page ===');
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 30000 });
  console.log(`  URL: ${page.url()}`);
  await shot('01-login');

  // 2. Fill credentials & submit
  console.log('\n=== 2. Logging in ===');
  const inputs = await page.$$('input');
  console.log(`  Found ${inputs.length} inputs`);
  
  // Fill staff ID (first input)
  if (inputs.length >= 2) {
    await inputs[0].fill(STAFF_ID);
    await inputs[1].fill(PASSWORD);
    console.log(`  Filled: ${STAFF_ID} / ****`);
    await shot('02-filled');
    
    // Click login button
    const loginBtn = await page.$('button, .login-btn, [class*="login"]');
    if (loginBtn) {
      await loginBtn.click();
      console.log('  Clicked login button');
    } else {
      // Try finding by text
      await page.click('text=登录');
      console.log('  Clicked 登录 text');
    }
    
    await waitIdle();
    await page.waitForTimeout(2000);
    console.log(`  After login URL: ${page.url()}`);
    await shot('03-after-login');
  }

  // 3. Check what page we're on
  console.log('\n=== 3. Current State ===');
  const currentUrl = page.url();
  console.log(`  URL: ${currentUrl}`);
  const title = await page.title();
  console.log(`  Title: ${title}`);
  
  // Take snapshot of interactive elements
  const elCount = await page.evaluate(() => {
    return document.querySelectorAll('a, button, input, [role="button"], [class*="tab"]').length;
  });
  console.log(`  Interactive elements: ${elCount}`);

  // 4. Navigate to key pages via hash routes
  const pages = [
    { name: 'home', hash: '#/pages/home/index' },
    { name: 'chat', hash: '#/pages/chat/index' },
    { name: 'services', hash: '#/pages/services/index' },
    { name: 'profile', hash: '#/pages/profile/index' },
    { name: 'chat-history', hash: '#/pages/chat/history' },
  ];

  for (let i = 0; i < pages.length; i++) {
    const p = pages[i];
    console.log(`\n=== ${4 + i}. ${p.name} ===`);
    try {
      await page.goto(`${BASE}/${p.hash}`, { waitUntil: 'networkidle', timeout: 15000 });
      await waitIdle();
      console.log(`  URL: ${page.url()}`);
      await shot(`${String(4 + i).padStart(2, '0')}-${p.name}`);
    } catch (e) {
      console.log(`  Error: ${e.message}`);
    }
  }

  console.log('\n=== Done! ===');
  console.log(`Screenshots saved to: ${SHOT_DIR}`);
  await browser.close();
})();
