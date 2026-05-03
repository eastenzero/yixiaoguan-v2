import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SHOT_DIR = path.join(__dirname, 'screenshots');
fs.mkdirSync(SHOT_DIR, { recursive: true });

const BASE = 'http://localhost:3000';
const STAFF_ID = '4125150012';
const PASSWORD = '4125150012';

async function shot(pg, name) {
  const p = path.join(SHOT_DIR, `${name}.png`);
  await pg.screenshot({ path: p, fullPage: true });
  console.log(`  📸 ${name}`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();

  // Log API calls
  page.on('response', resp => {
    const u = resp.url();
    if (u.includes('/api/auth') || u.includes('/api/conversations')) {
      resp.text().then(t => {
        console.log(`  API ${resp.status()} ${u.split('/api')[1]} → ${t.slice(0, 200)}`);
      }).catch(() => {});
    }
  });

  // 1. Open login page
  console.log('=== 1. Load login page ===');
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 30000 });
  await shot(page, 'v2-01-login');

  // 2. Type credentials using keyboard (triggers v-model properly)
  console.log('\n=== 2. Type credentials ===');
  const inputs = await page.$$('input');
  console.log(`  Found ${inputs.length} input elements`);

  // Click first input and type staff ID
  await inputs[0].click();
  await inputs[0].press('Control+a');
  await page.keyboard.type(STAFF_ID, { delay: 30 });
  
  // Click second input and type password
  await inputs[1].click();
  await inputs[1].press('Control+a');
  await page.keyboard.type(PASSWORD, { delay: 30 });
  
  await shot(page, 'v2-02-filled');

  // 3. Click login button
  console.log('\n=== 3. Click login ===');
  // The button has class "submit-btn"
  await page.click('.submit-btn');
  console.log('  Clicked .submit-btn');

  // Wait for login API response and navigation
  await page.waitForTimeout(4000);
  await page.waitForLoadState('networkidle').catch(() => {});

  const urlAfter = page.url();
  console.log(`  URL after login: ${urlAfter}`);
  await shot(page, 'v2-03-after-login');

  // Check if we're on home page
  if (urlAfter.includes('home')) {
    console.log('  ✅ Login SUCCESS!');
  } else {
    console.log('  ⚠️ May still be on login page');
    // Try checking for errors on page
    const bodyText = await page.evaluate(() => document.body.innerText);
    if (bodyText.includes('失败') || bodyText.includes('错误')) {
      console.log('  Error on page detected');
    }
  }

  // 4. Tour all pages
  console.log('\n=== 4. Tour pages ===');
  const pages = [
    { name: 'home', hash: '#/pages/home/index' },
    { name: 'chat', hash: '#/pages/chat/index' },
    { name: 'services', hash: '#/pages/services/index' },
    { name: 'profile', hash: '#/pages/profile/index' },
    { name: 'history', hash: '#/pages/chat/history' },
  ];

  for (const p of pages) {
    console.log(`\n--- ${p.name} ---`);
    await page.goto(`${BASE}/${p.hash}`, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(1500);
    const currentUrl = page.url();
    console.log(`  URL: ${currentUrl}`);
    // Check if redirected to login (401)
    if (currentUrl.endsWith('#/') && !p.hash.endsWith('#/')) {
      console.log('  ⚠️ Redirected to login (auth required)');
    }
    await shot(page, `v2-tour-${p.name}`);
  }

  console.log('\n=== Done ===');
  await browser.close();
})();
