import { request } from '@/utils/request'
import type { UserInfo } from '@/stores/user'

interface LoginResponse {
  access_token: string
  token_type: string
}

export function login(staff_id: string, password: string): Promise<LoginResponse> {
  return request<LoginResponse>({
    url: '/api/auth/login',
    method: 'POST',
    data: { staff_id, password, expected_role: 'student' },
  })
}

export function getMe(): Promise<UserInfo> {
  return request<UserInfo>({ url: '/api/auth/me' })
}
