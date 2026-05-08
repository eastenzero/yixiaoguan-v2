import { useUserStore } from '@/stores/user'

const API_BASE = ''

type RequestError = Error & {
  statusCode?: number
}

function createRequestError(message: string, statusCode?: number): RequestError {
  const error = new Error(message) as RequestError
  if (typeof statusCode === 'number') {
    error.statusCode = statusCode
  }
  return error
}

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
          void (async () => {
            const ok = await userStore.tryPilotLogin()
            if (!ok) {
              userStore.logout()
              uni.reLaunch({ url: '/pages/login/index' })
            }
          })()
          reject(createRequestError('未授权', 401))
        } else if (res.statusCode === 422) {
          const detail = (res.data as any)?.detail
          const message = Array.isArray(detail) ? detail[0]?.msg : (detail || '请求参数错误')
          reject(createRequestError(String(message), res.statusCode))
        } else {
          const errData = res.data as any
          reject(createRequestError(errData?.detail || errData?.message || `HTTP ${res.statusCode}`, res.statusCode))
        }
      },
      fail: (err) => {
        reject(createRequestError(err.errMsg || '网络连接失败'))
      },
    })
  })
}
