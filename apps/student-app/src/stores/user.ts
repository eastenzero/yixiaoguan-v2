import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { wsManager } from '@/utils/websocket'
import { centrifugeManager } from '@/utils/centrifuge'

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

  async function init(): Promise<void> {
    const storedToken = uni.getStorageSync(TOKEN_KEY)
    const storedInfo = uni.getStorageSync(USER_INFO_KEY)
    if (storedToken) {
      setToken(storedToken)
      if (storedInfo) {
        try { userInfo.value = JSON.parse(storedInfo) } catch { /* ignore */ }
      }
      _connectRealtime(storedToken)
      return
    }
    await startPilotTrial()
  }

  async function startPilotTrial(): Promise<void> {
    try {
      const [{ pilotAnonymousLogin, getMe }, { getDeviceId }] = await Promise.all([
        import('@/api/auth'),
        import('@/utils/device'),
      ])

      const loginRes = await pilotAnonymousLogin(getDeviceId())
      setToken(loginRes.access_token)

      const me = await getMe()
      setUserInfo(me)
    } catch {
      token.value = ''
      userInfo.value = null
      uni.removeStorageSync(TOKEN_KEY)
      uni.removeStorageSync(USER_INFO_KEY)
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
    centrifugeManager.disconnect()
  }

  function shouldConnectRealtime(): boolean {
    return !userInfo.value?.staff_id?.startsWith('pilot:')
  }

  function _connectRealtime(nextToken: string): void {
    wsManager.connect(nextToken)
    void import('@/api/auth')
      .then(({ getCentrifugoToken }) => getCentrifugoToken())
      .then(res => {
        centrifugeManager.connect(res.token, async () => {
          const { getCentrifugoToken } = await import('@/api/auth')
          const refreshed = await getCentrifugoToken()
          return refreshed.token
        })
      })
      .catch(() => { /* centrifugo unavailable, degrade silently */ })
  }

  return { token, userInfo, isLoggedIn, init, startPilotTrial, setToken, setUserInfo, logout }
})
