"""
Quick diagnostic: take VIEWPORT-only screenshots (full_page=False) of 3 pages
to see if tabBar truly floats in middle, or if the earlier full_page screenshot
was a Playwright rendering artifact for fixed elements.

Run from repo root:
  C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python314\\python.exe \\
    .tasks/e2e-pilot-smoke/diagnose_tabbar.py
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent / "diag"
OUT.mkdir(exist_ok=True)

STUDENT = "http://192.168.100.165/"
SID = "4125150001"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 390, "height": 844},
        locale="zh-CN",
    )
    page = context.new_page()

    # 1. Open + login
    page.goto(STUDENT, wait_until="domcontentloaded", timeout=15_000)
    page.locator("input").nth(0).fill(SID)
    page.locator("input").nth(1).fill(SID)
    page.locator("uni-button.submit-btn").click()
    page.wait_for_url(lambda u: "/pages/home" in u or "/index" in u, timeout=15_000)
    page.wait_for_timeout(1500)  # let layout settle

    # 2. Viewport-only screenshot of home
    page.screenshot(path=str(OUT / "home-viewport.png"), full_page=False)

    # 3. Probe computed style + bounding box of .tab-bar
    info_home = page.evaluate("""() => {
        const el = document.querySelector('.tab-bar');
        if (!el) return { found: false };
        const rect = el.getBoundingClientRect();
        const cs = getComputedStyle(el);
        return {
            found: true,
            position: cs.position,
            bottom: cs.bottom,
            top: cs.top,
            zIndex: cs.zIndex,
            transform: cs.transform,
            rect: { x: rect.x, y: rect.y, w: rect.width, h: rect.height },
            viewportH: window.innerHeight,
            documentH: document.documentElement.scrollHeight,
            parentChain: (() => {
                const chain = [];
                let cur = el.parentElement;
                while (cur && chain.length < 8) {
                    const pc = getComputedStyle(cur);
                    chain.push({
                        tag: cur.tagName.toLowerCase(),
                        cls: cur.className,
                        pos: pc.position,
                        transform: pc.transform,
                        overflow: pc.overflow,
                    });
                    cur = cur.parentElement;
                }
                return chain;
            })(),
        };
    }""")
    (OUT / "home-tabbar-info.json").write_text(__import__("json").dumps(info_home, indent=2, ensure_ascii=False), encoding="utf-8")

    # 4. Switch to chat tab
    page.locator(".tab-bar .tab-item").nth(1).click()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / "chat-viewport.png"), full_page=False)

    # 5. Switch to profile
    page.locator(".tab-bar .tab-item").nth(3).click()
    page.wait_for_timeout(1500)
    page.screenshot(path=str(OUT / "profile-viewport.png"), full_page=False)

    browser.close()
    print("DONE. See", OUT)
