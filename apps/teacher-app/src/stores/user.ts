import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { UserInfo } from '@/types/api'

const TOKEN_KEY = 'teacher-token'
const USER_INFO_KEY = 'teacher-user-info'

export const useUserStore = defineStore('user', () => {
  // ===== State =====
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)

  // ===== Getters =====
  const isLoggedIn = computed(() => !!token.value)
  const displayName = computed(() => userInfo.value?.name || '老师')

  // ===== Actions =====

  const init = () => {
    try {
      const storedToken = uni.getStorageSync(TOKEN_KEY)
      const storedUserInfo = uni.getStorageSync(USER_INFO_KEY)
      if (storedToken) token.value = storedToken
      if (storedUserInfo) userInfo.value = JSON.parse(storedUserInfo)
    } catch (error) {
      console.error('[UserStore] 初始化失败', error)
    }
  }

  const setToken = (newToken: string) => {
    token.value = newToken
    try { uni.setStorageSync(TOKEN_KEY, newToken) } catch { /* */ }
  }

  const setUserInfo = (info: UserInfo) => {
    userInfo.value = info
    try { uni.setStorageSync(USER_INFO_KEY, JSON.stringify(info)) } catch { /* */ }
  }

  const clearAuth = () => {
    token.value = ''
    userInfo.value = null
    try {
      uni.removeStorageSync(TOKEN_KEY)
      uni.removeStorageSync(USER_INFO_KEY)
    } catch { /* */ }
  }

  const logout = () => { clearAuth() }

  return {
    token,
    userInfo,
    isLoggedIn,
    displayName,
    init,
    setToken,
    setUserInfo,
    clearAuth,
    logout
  }
})
