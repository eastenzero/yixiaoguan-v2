import { createSSRApp } from 'vue'
import { pinia } from './stores'
import App from './App.vue'

export function createApp() {
  const app = createSSRApp(App)
  app.use(pinia)

  import('./stores/user').then(({ useUserStore }) => {
    const userStore = useUserStore()
    userStore.init()
    // 如果已登录，自动建立 WS 连接
    if (userStore.token) {
      import('./stores/websocket').then(({ useWsStore }) => {
        const wsStore = useWsStore()
        wsStore.init(userStore.token)
      })
    }
  })

  return {
    app
  }
}
