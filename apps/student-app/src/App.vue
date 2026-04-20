<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'

onLaunch(() => {
  const userStore = useUserStore()
  userStore.init()
})
</script>

<style lang="scss">
@import '@/styles/theme.scss';

:root {
  --color-primary: #{$primary-40};
}

page {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #F8FAFC;
  color: #0F172A;
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
