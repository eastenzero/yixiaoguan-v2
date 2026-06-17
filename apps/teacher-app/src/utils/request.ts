import { useUserStore } from '@/stores/user'
import { REQUEST_TIMEOUT_MS, toApiUrl } from '@/utils/runtime'

// ===== 配置区 =====
const REQUEST_TIMEOUT = REQUEST_TIMEOUT_MS

export type RequestOptions = UniApp.RequestOptions & {
  params?: Record<string, any>
}

/**
 * 统一请求封装（v2 FastAPI — 直接返回 JSON，无 {code, data} 包装）
 */
export function request<T = any>(options: RequestOptions): Promise<T> {
  return new Promise((resolve, reject) => {
    const userStore = useUserStore()
    const { params, ...uniOptions } = options

    // 构建完整 URL
    let url = toApiUrl(uniOptions.url)

    // 将 params 拼接到 URL query string
    if (params) {
      const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
      if (entries.length > 0) {
        const qs = entries
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
          .join('&')
        url += (url.includes('?') ? '&' : '?') + qs
      }
    }

    // 请求配置
    const requestOptions: UniApp.RequestOptions = {
      ...uniOptions,
      url,
      timeout: uniOptions.timeout || REQUEST_TIMEOUT,
      header: {
        'Content-Type': 'application/json',
        ...uniOptions.header
      },
      success: (res) => {
        // 401 未授权 → 跳登录
        if (res.statusCode === 401) {
          uni.showToast({ title: '登录已过期', icon: 'none' })
          userStore.logout()
          setTimeout(() => { uni.reLaunch({ url: '/pages/login/index' }) }, 1500)
          reject(new Error('登录已过期'))
          return
        }
        // HTTP 错误
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const detail = (res.data as any)?.detail || `请求失败(${res.statusCode})`
          uni.showToast({ title: detail, icon: 'none' })
          reject(new Error(detail))
          return
        }
        // FastAPI 直接返回 JSON
        resolve(res.data as T)
      },
      fail: (err) => {
        console.error('[Request Error]', err)
        uni.showToast({ title: '网络连接失败', icon: 'none' })
        reject(err)
      }
    }

    // 注入 JWT Token
    if (userStore.token) {
      requestOptions.header = {
        ...requestOptions.header,
        'Authorization': `Bearer ${userStore.token}`
      }
    }

    uni.request(requestOptions)
  })
}

// ===== HTTP 方法封装 =====

export function get<T = any>(url: string, params?: Record<string, any>, options?: Partial<UniApp.RequestOptions>): Promise<T> {
  let fullUrl = url
  if (params) {
    const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
    if (entries.length > 0) {
      const qs = entries
        .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
        .join('&')
      fullUrl += (url.includes('?') ? '&' : '?') + qs
    }
  }
  return request<T>({ url: fullUrl, method: 'GET', ...options })
}

export function post<T = any>(url: string, data?: any, options?: Partial<UniApp.RequestOptions>): Promise<T> {
  return request<T>({ url, method: 'POST', data, ...options })
}

export function put<T = any>(url: string, data?: any, options?: Partial<UniApp.RequestOptions>): Promise<T> {
  return request<T>({ url, method: 'PUT', data, ...options })
}

export function del<T = any>(url: string, data?: any, options?: Partial<UniApp.RequestOptions>): Promise<T> {
  return request<T>({ url, method: 'DELETE', data, ...options })
}

export default request
