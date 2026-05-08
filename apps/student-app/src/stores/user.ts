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

type RequestError = Error & {
  statusCode?: number
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function init(): Promise<void> {
    const storedToken = uni.getStorageSync(TOKEN_KEY)
    const storedInfo = uni.getStorageSync(USER_INFO_KEY)
    if (storedToken) {
      token.value = storedToken
      if (storedInfo) {
        try { userInfo.value = JSON.parse(storedInfo) } catch { /* ignore */ }
      }
      _connectRealtime(storedToken)
      return
    }

    await tryPilotLogin()
  }

  async function tryPilotLogin(): Promise<boolean> {
    try {
      const [{ pilotAnonymousLogin, getMe }, { getDeviceId }] = await Promise.all([
        import('@/api/auth'),
        import('@/utils/device'),
      ])
      const deviceId = getDeviceId()
      const resp = await pilotAnonymousLogin(deviceId)

      setToken(resp.access_token)
      const info = await getMe()
      setUserInfo(info)
      _connectRealtime(resp.access_token)
      return true
    } catch (error) {
      if ((error as RequestError | undefined)?.statusCode === 403) {
        uni.reLaunch({ url: '/pages/login/index' })
      }
      return false
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

  return { token, userInfo, isLoggedIn, init, tryPilotLogin, setToken, setUserInfo, logout }
})
