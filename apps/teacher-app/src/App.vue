<script setup lang="ts">
import { onLaunch, onShow, onHide } from "@dcloudio/uni-app";
import { useUserStore } from '@/stores/user'
import { useWsStore } from '@/stores/websocket'

onLaunch(() => {
  console.log("Teacher App Launch");
  const userStore = useUserStore()
  userStore.init()
  if (userStore.token) {
    const wsStore = useWsStore()
    wsStore.init(userStore.token)
  }
});
onShow(() => {
  console.log("Teacher App Show");
});
onHide(() => {
  console.log("Teacher App Hide");
});
</script>

<style lang="scss">
@import './styles/tokens.scss';
@import './styles/global.scss';

@font-face {
  font-family: 'Manrope';
  font-style: normal;
  font-weight: 400 800;
  font-display: swap;
  src: url('/static/fonts/Manrope-Variable.woff2') format('woff2');
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD;
}

:root {
  --color-primary: #{$primary};
}

page {
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: $surface;
  color: $on-surface;
  -webkit-tap-highlight-color: transparent;
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

.hover-effect {
  opacity: 0.7;
  transition: opacity 0.2s;
}
</style>
