<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'

onLaunch(() => {
  const userStore = useUserStore()
  userStore.init()
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
  src: url('https://fonts.gstatic.com/s/manrope/v15/xn7_YHE41ni1AdIRqAuZuw1Bx9mbZk59FO_F87jxeN7B.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

:root {
  --color-primary: #{$primary};
}

page {
  font-family: 'Manrope', 'PingFang SC', system-ui, sans-serif;
  background: $bg-page;
  color: $text-primary;
  --window-bottom: 0px;
}

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
