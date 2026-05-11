// 必须在 vue mount 之前 sync 注入 Material Symbols FOUT 防御
// （uni-app vite build 会丢掉 index.html 里的 inline <style>/<script>，所以放这里）
import './utils/icons-ready'
import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)
  return { app }
}
