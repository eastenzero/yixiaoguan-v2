/**
 * Material Symbols FOUT (Flash Of Unstyled Text) 防御
 *
 * 问题：uni-app vite-plugin-uni 在 H5 build 时会重写 index.html，把里面的 inline
 * <style> / <script> 全部丢弃（参见 dist/build/h5/index.html）。导致虽然 index.html
 * 已经写了 visibility:hidden + document.fonts.load 防御，build 出来的产物里这段防御
 * **完全消失**，结果就是启动的最初 2-3 秒 Material Symbols 图标显示为英文 ligature
 * 字符串（"home" / "chat_bubble" / "person" 等），3-5 秒后字体加载完才变回真图标。
 *
 * 解决：把防御逻辑放进 ES module，作为 main.ts bundle 的一部分被打包进去，build
 * 后绝不会被丢弃。module top-level 在 vue mount 前同步执行，DOM 创建图标元素时
 * `.material-symbols-outlined { visibility: hidden }` 规则已经生效，直到字体真正
 * 加载完才放出来。
 *
 * 同时与 index.html 里的同名防御兼容 — id 锁了 idempotency，重复 inject 无害。
 */

if (typeof document !== 'undefined') {
  const STYLE_ID = '__icons-fout-guard__'
  const READY_CLASS = 'icons-ready'

  // 1. 注入 visibility:hidden 防御样式（如果还没注入过）
  if (!document.getElementById(STYLE_ID)) {
    const style = document.createElement('style')
    style.id = STYLE_ID
    style.textContent =
      '.material-symbols-outlined{visibility:hidden;}' +
      'html.' + READY_CLASS + ' .material-symbols-outlined{visibility:visible;}'
    // 用 head 优先，没有就 body，再没有就 documentElement
    const target = document.head || document.body || document.documentElement
    target.appendChild(style)
  }

  // 2. 字体加载完成后放出图标
  const markReady = () => {
    document.documentElement.classList.add(READY_CLASS)
  }

  // 优先用 FontFace API：等到 Material Symbols 真正可用再展示
  if (document.fonts && typeof document.fonts.load === 'function') {
    // 测多个常用 size，确保 variable font 各 axis 都加载
    Promise.all([
      document.fonts.load('24px "Material Symbols Outlined"'),
      document.fonts.load('20px "Material Symbols Outlined"'),
    ])
      .then(markReady)
      .catch(markReady)
  }

  // 安全兜底：5s 后强制显示，避免字体加载异常导致永久不可见
  // （3s 在慢网络下不够，实测 dev server 也要 3.5s 左右）
  setTimeout(markReady, 5000)
}

export {}
