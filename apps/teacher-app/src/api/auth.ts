/**
 * 认证相关 API — v2 FastAPI
 * POST /api/auth/login  → { access_token, token_type, user }
 * GET  /api/auth/me      → UserInfo
 */
import { post, get } from '@/utils/request'

// ── 响应类型 ──────────────────────────────────────────────

export interface LoginResult {
  access_token: string
  token_type: string
}

export interface UserInfoResult {
  id: number
  staff_id: string
  name: string
  role: string
  college_id: number | null
  class_id: number | null
  avatar_url: string | null
}

// ── 接口函数 ──────────────────────────────────────────────

/**
 * 教师登录
 */
export function login(params: {
  staff_id: string
  password: string
}): Promise<LoginResult> {
  return post<LoginResult>('/api/auth/login', params)
}

/**
 * 获取当前用户信息
 */
export function getUserInfo(): Promise<UserInfoResult> {
  return get<UserInfoResult>('/api/auth/me')
}
