/**
 * Lightweight browser automation helper for UI review.
 * Usage:
 *   node browser-tool.mjs open <url>        — open page & screenshot
 *   node browser-tool.mjs screenshot [name] — take screenshot
 *   node browser-tool.mjs snapshot          — get interactive elements
 *   node browser-tool.mjs click <selector>  — click element
 *   node browser-tool.mjs fill <selector> <text> — fill input
 *   node browser-tool.mjs eval <js>         — evaluate JS in page
 *   node browser-tool.mjs close             — close browser
 */
import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

const STATE_FILE = path.join(process.env.USERPROFILE || '', '.agent-browser', 'pw-state.json');
const SCREENSHOT_DIR = path.join(process.cwd(), '.tasks');

// Ensure dirs exist
fs.mkdirSync(path.dirname(STATE_FILE), { recursive: true });
fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

let browser, context, page;

async function getEndpoint() {
  try {
    const data = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8'));
    return data.wsEndpoint;
  } catch { return null; }
}

async function saveEndpoint(ws) {
  fs.writeFileSync(STATE_FILE, JSON.stringify({ wsEndpoint: ws }));
}

async function connectOrLaunch() {
  const ws = await getEndpoint();
  if (ws) {
    try {
      browser = await chromium.connectOverCDP(ws);
      context = browser.contexts()[0];
      page = context.pages()[0] || await context.newPage();
      return;
    } catch { /* stale endpoint, launch new */ }
  }
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 390, height: 844 } }); // iPhone-like viewport
  page = await context.newPage();
}

async function launchFresh(url) {
  browser = await chromium.launch({ headless: true });
  context = await browser.newContext({ viewport: { width: 390, height: 844 } });
  page = await context.newPage();
  // Save CDP endpoint for reconnection (not available in standard launch, so we skip)
  if (url) {
    await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
  }
}

async function screenshot(name) {
  const fname = name || `screenshot-${Date.now()}`;
  const fpath = path.join(SCREENSHOT_DIR, `${fname}.png`);
  await page.screenshot({ path: fpath, fullPage: false });
  console.log(`Screenshot saved: ${fpath}`);
  return fpath;
}

async function snapshot() {
  const elements = await page.evaluate(() => {
    const items = [];
    const interactive = document.querySelectorAll(
      'a, button, input, textarea, select, [role="button"], [onclick], [tabindex]'
    );
    interactive.forEach((el, i) => {
      const rect = el.getBoundingClientRect();
      if (rect.width === 0 && rect.height === 0) return;
      const tag = el.tagName.toLowerCase();
      const type = el.getAttribute('type') || '';
      const text = (el.textContent || '').trim().slice(0, 50);
      const placeholder = el.getAttribute('placeholder') || '';
      const id = el.id ? `#${el.id}` : '';
      const cls = el.className ? `.${String(el.className).split(' ')[0]}` : '';
      items.push({
        ref: `@e${i}`,
        tag,
        type,
        id,
        cls,
        text: text || placeholder,
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        w: Math.round(rect.width),
        h: Math.round(rect.height)
      });
    });
    return items;
  });
  elements.forEach(e => {
    console.log(`${e.ref} <${e.tag}${e.type ? ' type="'+e.type+'"' : ''}${e.id}${e.cls}> "${e.text}" [${e.x},${e.y} ${e.w}x${e.h}]`);
  });
  return elements;
}

async function clickElement(selector) {
  await page.click(selector, { timeout: 5000 });
  console.log(`Clicked: ${selector}`);
  await page.waitForLoadState('networkidle').catch(() => {});
}

async function fillElement(selector, text) {
  await page.fill(selector, text, { timeout: 5000 });
  console.log(`Filled: ${selector} with "${text}"`);
}

async function evalInPage(js) {
  const result = await page.evaluate(js);
  console.log(JSON.stringify(result, null, 2));
}

// Main
const [,, cmd, ...args] = process.argv;

try {
  if (cmd === 'open') {
    const url = args[0] || 'http://localhost:3000';
    await launchFresh(url);
    console.log(`Opened: ${url}`);
    console.log(`Title: ${await page.title()}`);
    console.log(`URL: ${page.url()}`);
    await screenshot('initial');
    // Keep running for subsequent commands via a server
    // For now, just close after screenshot
    await browser.close();
  } else if (cmd === 'login') {
    const url = args[0] || 'http://localhost:3000';
    const staffId = args[1];
    const password = args[2];
    await launchFresh(url);
    // Wait for page
    await page.waitForLoadState('networkidle');
    console.log(`Page loaded: ${page.url()}`);
    console.log(`Title: ${await page.title()}`);
    await screenshot('before-login');
    // Try to find login elements
    const snap = await snapshot();
    console.log(`\nFound ${snap.length} interactive elements`);
    
    if (staffId && password) {
      // Try to fill login form
      try {
        // Look for input fields
        const inputs = await page.$$('input');
        console.log(`\nFound ${inputs.length} input fields`);
        for (let i = 0; i < inputs.length; i++) {
          const type = await inputs[i].getAttribute('type');
          const placeholder = await inputs[i].getAttribute('placeholder');
          console.log(`  Input ${i}: type=${type}, placeholder=${placeholder}`);
        }
      } catch(e) {
        console.log('Error inspecting inputs:', e.message);
      }
    }
    await browser.close();
  } else if (cmd === 'tour') {
    // Take screenshots of all main pages
    const baseUrl = args[0] || 'http://localhost:3000';
    const staffId = args[1];
    const password = args[2];
    
    await launchFresh(baseUrl);
    await page.waitForLoadState('networkidle');
    console.log(`Loaded: ${page.url()}`);
    await screenshot('tour-01-landing');
    
    // Get page info
    const title = await page.title();
    const url = page.url();
    console.log(`Title: ${title}`);
    console.log(`URL: ${url}`);
    
    await browser.close();
  } else {
    console.log('Usage: node browser-tool.mjs <open|login|tour> [args...]');
  }
} catch (e) {
  console.error('Error:', e.message);
  if (browser) await browser.close().catch(() => {});
  process.exit(1);
}
