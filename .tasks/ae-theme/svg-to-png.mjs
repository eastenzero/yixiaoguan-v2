import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'fs';
import { resolve } from 'path';

const SVG_PATH = resolve('logo-yxg-final.svg');
const OUT_PNG = resolve('logo-yxg-4k.png');

const svgContent = readFileSync(SVG_PATH, 'utf-8');

// Render at 4K resolution (the SVG viewBox is 1672×941, scale to ~4x)
const SCALE = 4;
const W = 1672;
const H = 941;

const html = `<!DOCTYPE html>
<html><head><style>
  html, body { margin:0; padding:0; background: transparent; overflow:hidden; }
  body { width:${W}px; height:${H}px; }
</style></head>
<body>${svgContent}</body></html>`;

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: W, height: H },
  deviceScaleFactor: SCALE,
});
await page.setContent(html, { waitUntil: 'networkidle' });
const buf = await page.screenshot({ type: 'png', omitBackground: true });
writeFileSync(OUT_PNG, buf);
console.log(`Saved ${OUT_PNG} (${(buf.length / 1024).toFixed(0)} KB, ${W * SCALE}x${H * SCALE})`);
await browser.close();
