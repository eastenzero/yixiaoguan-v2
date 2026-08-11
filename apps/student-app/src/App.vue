<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { trackEvent } from '@/utils/track'

onLaunch(() => {
  // #ifdef H5
  document.documentElement.classList.toggle('yxg-reduced-motion', uni.getStorageSync('yxg-reduced-motion') === '1')
  // #endif
  const userStore = useUserStore()
  void userStore.init().then(() => {
    trackEvent('app_start', {
      role: userStore.userInfo?.role || 'unknown',
      has_stored_session: !!userStore.token,
    })
  })
})
</script>

<style lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/global.scss';
@import '@/styles/theme.scss';

@font-face {
  font-family: 'Manrope';
  font-style: normal;
  font-weight: 400 800;
  font-display: swap;
  src: url('/static/fonts/Manrope-Variable.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

page {
  @include token-css-vars;
  font-family: 'Manrope', 'PingFang SC', system-ui, sans-serif;
  background: $bg-page;
  color: $text-primary;
  --window-bottom: 0px;
}

.yxg-reduced-motion *,
.yxg-reduced-motion *::before,
.yxg-reduced-motion *::after {
  animation-duration: 0.001ms !important;
  animation-iteration-count: 1 !important;
  scroll-behavior: auto !important;
  transition-duration: 0.001ms !important;
}

/* #ifdef H5 */
:root {
  --student-frame-max-width: 480px;
  --student-frame-width: 100vw;
  --student-frame-offset: 0px;
  --student-fixed-left: 0px;
  --student-fixed-right: 0px;
}

html,
body,
#app {
  min-height: 100%;
}

/* uni-app 按浏览器全宽写入根字号；桌面窄框模式下同步封顶，
   避免使用 rem 的页面内容仍按整块桌面画布被放大。 */
html {
  font-size: min(4.266667vw, 18.3467px) !important;
}

body {
  margin: 0;
  background: $surface;
}

#app {
  width: 100%;
  min-height: 100vh;
  margin: 0 auto;
  background: $surface;
  overflow-x: hidden;
}

@media (min-width: 768px) and (min-aspect-ratio: 4 / 3) {
  html {
    font-size: min(4.266667vw, 2.4vh, 20.48px) !important;
  }

  :root {
    --student-frame-ratio-width: 56.25vh;
    /* 矮横屏仍保持竖版 UI，但不允许内容框被 56.25vh 压成不可读窄栏。 */
    --student-frame-width: min(100vw, var(--student-frame-max-width), max(360px, var(--student-frame-ratio-width)));
    --student-frame-offset: max(0px, calc((100vw - var(--student-frame-width)) / 2));
    --student-fixed-left: var(--student-frame-offset);
    --student-fixed-right: var(--student-frame-offset);
  }

  @supports (height: 100dvh) {
    :root {
      --student-frame-ratio-width: 56.25dvh;
    }
  }

  body {
    background:
      linear-gradient(135deg, #f7f9fb 0%, #f5f0f8 46%, #eef7f3 100%);
  }

  #app {
    width: var(--student-frame-width);
    min-height: 100vh;
    box-shadow:
      0 0 0 1px rgba(91, 33, 182, 0.06),
      0 24px 80px rgba(15, 23, 42, 0.12);
  }
}
/* #endif */

uni-tabbar,
.uni-tabbar {
  display: none !important;
  height: 0 !important;
  overflow: hidden !important;
}

button {
  background: none;
  border: none;
  padding: 0;
  margin: 0;
  font: inherit;
  color: inherit;
}

button::after {
  border: none;
}
</style>
