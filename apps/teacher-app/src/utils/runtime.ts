const DEFAULT_REQUEST_TIMEOUT_MS = 30000

let DEFAULT_API_BASE_URL = ''
let DEFAULT_WS_BASE_URL = ''

// #ifdef MP-WEIXIN
DEFAULT_API_BASE_URL = 'https://yxg.xiaoguan.site'
DEFAULT_WS_BASE_URL = 'wss://yxg.xiaoguan.site'
// #endif

// #ifdef H5
if (typeof window !== 'undefined' && window.location) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  DEFAULT_WS_BASE_URL = `${protocol}//${window.location.host}`
}
// #endif

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '')
}

function normalizeBaseUrl(value: unknown, fallback: string): string {
  if (typeof value !== 'string') return fallback
  const normalized = trimTrailingSlash(value.trim())
  return normalized || fallback
}

function normalizeTimeout(value: unknown): number {
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : DEFAULT_REQUEST_TIMEOUT_MS
}

function isAbsoluteHttpUrl(url: string): boolean {
  return /^https?:\/\//i.test(url)
}

function isAbsoluteWsUrl(url: string): boolean {
  return /^wss?:\/\//i.test(url)
}

export const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_BASE_URL,
  DEFAULT_API_BASE_URL,
)

export const WS_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_WS_BASE_URL,
  DEFAULT_WS_BASE_URL,
)

export const CENTRIFUGE_WS_URL = normalizeBaseUrl(
  import.meta.env.VITE_CENTRIFUGE_WS_URL,
  `${WS_BASE_URL}/centrifugo/connection/websocket`,
)

export const REQUEST_TIMEOUT_MS = normalizeTimeout(import.meta.env.VITE_REQUEST_TIMEOUT_MS)

export function toApiUrl(url: string): string {
  if (isAbsoluteHttpUrl(url)) return url
  return `${API_BASE_URL}${url.startsWith('/') ? url : `/${url}`}`
}

export function toWsUrl(path: string): string {
  if (isAbsoluteWsUrl(path)) return path
  return `${WS_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`
}

export function appendQuery(url: string, params: Record<string, string | number | boolean | null | undefined>): string {
  const entries = Object.entries(params).filter(([, value]) => value !== undefined && value !== null)
  if (!entries.length) return url
  const query = entries.map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`).join('&')
  return `${url}${url.includes('?') ? '&' : '?'}${query}`
}
