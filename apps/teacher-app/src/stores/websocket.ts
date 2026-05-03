import { defineStore } from 'pinia'
import { ref } from 'vue'
import { wsManager } from '@/utils/websocket'
import { centrifugeManager } from '@/utils/centrifuge'
import { getCentrifugoToken } from '@/api/auth'

const _getToken = async () => {
  const r = await getCentrifugoToken()
  return r.token
}

export const useWsStore = defineStore('websocket', () => {
  const isConnected = ref(false)
  const unreadCount = ref(0)

  function init(token: string, centrifugoToken?: string) {
    wsManager.connect(token)
    wsManager.on('*', () => {
      isConnected.value = wsManager.isConnected
    })
    if (centrifugoToken) {
      centrifugeManager.connect(centrifugoToken, _getToken)
    } else {
      // 刷新页面时无 centrifugoToken，从 API 获取
      getCentrifugoToken()
        .then(res => centrifugeManager.connect(res.token, _getToken))
        .catch(() => { /* centrifugo unavailable, degrade silently */ })
    }
  }

  function destroy() {
    wsManager.disconnect()
    centrifugeManager.disconnect()
    isConnected.value = false
    unreadCount.value = 0
  }

  function incrementUnread() {
    unreadCount.value++
  }

  function resetUnread() {
    unreadCount.value = 0
  }

  return { isConnected, unreadCount, init, destroy, incrementUnread, resetUnread }
})
