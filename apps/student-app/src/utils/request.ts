import { useUserStore } from '@/stores/user'

const API_BASE = ''  // vite proxy handles /api → 165:8100

export function request<T = any>(options: {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: any
  header?: Record<string, string>
}): Promise<T> {
  const userStore = useUserStore()
  return new Promise((resolve, reject) => {
    uni.request({
      url: API_BASE + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...(userStore.token ? { Authorization: `Bearer ${userStore.token}` } : {}),
        ...options.header,
      },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data as T)
        } else if (res.statusCode === 401) {
          userStore.logout()
          uni.reLaunch({ url: '/pages/login/index' })
          reject(new Error('未授权，请重新登录'))
        } else if (res.statusCode === 422) {
          const detail = (res.data as any)?.detail
          const msg = Array.isArray(detail) ? detail[0]?.msg : (detail || '请求参数错误')
          reject(new Error(String(msg)))
        } else {
          const errData = res.data as any
          reject(new Error(errData?.detail || errData?.message || `HTTP ${res.statusCode}`))
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || '网络连接失败'))
      },
    })
  })
}
