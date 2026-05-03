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
  console.log(`  📸 ${name}.png`);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 390, height: 844 } });
  const page = await ctx.newPage();

  // Listen for API responses
  page.on('response', resp => {
    if (resp.url().includes('/api/')) {
      console.log(`  API: ${resp.status()} ${resp.url().split('/api')[1]}`);
    }
  });

  // 1. Open login
  console.log('=== Login ===');
  await page.goto(BASE, { waitUntil: 'networkidle', timeout: 30000 });
  await shot(page, 'login-01-page');

  // 2. Fill & submit
  const inputs = await page.$$('input');
  console.log(`  Inputs found: ${inputs.length}`);
  if (inputs.length >= 2) {
    await inputs[0].fill(STAFF_ID);
    await inputs[1].fill(PASSWORD);
    await shot(page, 'login-02-filled');

    // Find and click the login button
    // Try multiple selectors
    let clicked = false;
    for (const sel of ['.login-btn', 'button:has-text("登录")', 'text=登录 →', 'text=登录']) {
      try {
        await page.click(sel, { timeout: 2000 });
        console.log(`  Clicked: ${sel}`);
        clicked = true;
        break;
      } catch { /* try next */ }
    }
    
    if (!clicked) {
      // Fallback: click by evaluating
      await page.evaluate(() => {
        const btns = document.querySelectorAll('button, [class*="btn"], [class*="login"]');
        for (const b of btns) {
          if (b.textContent.includes('登录')) { b.click(); return; }
        }
      });
      console.log('  Clicked via evaluate fallback');
    }

    // Wait for response
    await page.waitForTimeout(3000);
    await page.waitForLoadState('networkidle').catch(() => {});
    
    const url = page.url();
    console.log(`  After login URL: ${url}`);
    await shot(page, 'login-03-result');

    // 3. If login successful, tour all pages
    if (url.includes('home') || !url.endsWith('#/')) {
      console.log('\n=== Login SUCCESS! Touring pages... ===');
    } else {
      console.log('\n=== Still on login page, trying direct navigation... ===');
    }

    // Tour pages regardless
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
      await page.waitForTimeout(1000);
      console.log(`  URL: ${page.url()}`);
      await shot(page, `tour-${p.name}`);
    }
  }

  console.log('\n=== Done ===');
  await browser.close();
})();
