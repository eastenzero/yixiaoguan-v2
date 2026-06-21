<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { trackEvent } from '@/utils/track'

onLaunch(() => {
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
  :root {
    --student-frame-ratio-width: 56.25vh;
    --student-frame-width: min(100vw, var(--student-frame-max-width), var(--student-frame-ratio-width));
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
