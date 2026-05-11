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
    // R11 pilot 用户没有真实师生关系（无 college/class），实时通道（教师答复推送等）
    // 在 pilot 模式下永远不会有消息，连接只会产生持续的 WS 报错噪音 —— 直接跳过。
    const staffId = userInfo.value?.staff_id || ''
    if (staffId.startsWith('pilot:')) {
      return
    }
    wsManager.connect(nextToken)
    _attachGlobalListeners()
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

  // —— 全局实时事件分发 ——
  // 后端（services.conversation_service.notify_conversation_parties）会同时把 new_message /
  // status_changed 推送到 conv:{id} 和 user#{student_id} 两个 Centrifugo 频道。
  // 这里在 store 层挂一次 listener，把事件 fanout 到 uni 全局事件总线，
  // 任何页面（chat / history / home / profile…）都可以通过 uni.$on('rt:new_message') 订阅，
  // 不再依赖"必须停留在 chat 详情页 + 必须订阅了 conv:{id} channel"才能收到推送。
  let _globalListenersAttached = false
  // 去重：后端同时把同一条消息推到 conv:{id} 和 user#{id} 两个频道，
  // centrifugeManager 的 publication dispatch 是按 type 分发（不区分 channel），
  // 所以同一条消息会被 dispatch 两次。这里用 type + payload 指纹做幂等。
  const _seenKeys = new Set<string>()
  const SEEN_MAX = 500

  function _addSeen(key: string): boolean {
    if (_seenKeys.has(key)) return false
    _seenKeys.add(key)
    if (_seenKeys.size > SEEN_MAX) {
      const oldest = _seenKeys.values().next().value
      if (oldest !== undefined) _seenKeys.delete(oldest)
    }
    return true
  }

  function _attachGlobalListeners(): void {
    if (_globalListenersAttached) return
    _globalListenersAttached = true
    const fanout = (type: string) => (data: any) => {
      let key: string
      try { key = type + ':' + JSON.stringify(data) } catch { key = type + ':' + Math.random() }
      if (!_addSeen(key)) return
      try { uni.$emit('rt:' + type, data) } catch { /* ignore */ }
    }
    const onNewMessage = fanout('new_message')
    const onStatusChanged = fanout('status_changed')
    wsManager.on('new_message', onNewMessage)
    wsManager.on('status_changed', onStatusChanged)
    centrifugeManager.on('new_message', onNewMessage)
    centrifugeManager.on('status_changed', onStatusChanged)
  }

  return { token, userInfo, isLoggedIn, init, tryPilotLogin, setToken, setUserInfo, logout }
})
