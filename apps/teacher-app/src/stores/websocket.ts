import { defineStore } from 'pinia'
import { ref } from 'vue'
import { wsManager } from '@/utils/websocket'

export const useWsStore = defineStore('websocket', () => {
  const isConnected = ref(false)
  const unreadCount = ref(0)

  function init(token: string) {
    wsManager.connect(token)
    wsManager.on('*', () => {
      isConnected.value = wsManager.isConnected
    })
  }

  function destroy() {
    wsManager.disconnect()
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
