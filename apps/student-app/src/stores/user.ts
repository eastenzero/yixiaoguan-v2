import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { wsManager } from '@/utils/websocket'

export interface UserInfo {
  id: number
  staff_id: string
  name: string
  role: string
  college_id: number | null
  class_id: number | null
  avatar_url: string | null
}

const TOKEN_KEY = 'v2-token'
const USER_INFO_KEY = 'v2-user-info'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function init() {
    const storedToken = uni.getStorageSync(TOKEN_KEY)
    const storedInfo = uni.getStorageSync(USER_INFO_KEY)
    if (storedToken) {
      token.value = storedToken
      if (storedInfo) {
        try { userInfo.value = JSON.parse(storedInfo) } catch { /* ignore */ }
      }
      wsManager.connect(storedToken)
    }
  }

  function setToken(newToken: string) {
    token.value = newToken
    uni.setStorageSync(TOKEN_KEY, newToken)
  }

  function setUserInfo(info: UserInfo) {
    userInfo.value = info
    uni.setStorageSync(USER_INFO_KEY, JSON.stringify(info))
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    uni.removeStorageSync(TOKEN_KEY)
    uni.removeStorageSync(USER_INFO_KEY)
    wsManager.disconnect()
  }

  return { token, userInfo, isLoggedIn, init, setToken, setUserInfo, logout }
})
