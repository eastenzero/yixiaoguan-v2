import { get, post } from '@/utils/request'

export interface AdminUserItem {
  id: number
  staff_id: string
  name: string
  role: string
  college_id: number | null
  college_name: string | null
  class_id: number | null
  class_name: string | null
  is_active: boolean
  created_at: string
}

export interface AdminUserListResponse {
  items: AdminUserItem[]
  total: number
  page: number
  size: number
}

export interface BatchImportRequest {
  college_id: number
  class_id?: number | null
  role?: string
  users: { staff_id: string; name: string }[]
}

export interface BatchImportResponse {
  created: number
  skipped: number
}

export function getUsers(params: {
  page?: number
  size?: number
  role?: string
  college_id?: number
  class_id?: number
  keyword?: string
}) {
  return get<AdminUserListResponse>('/api/admin/users', params)
}

export function batchImport(data: BatchImportRequest) {
  return post<BatchImportResponse>('/api/admin/users/batch-import', data)
}

export function resetPassword(userId: number) {
  return post<{ ok: boolean }>(`/api/admin/users/${userId}/reset-password`)
}

export function toggleActive(userId: number) {
  // uni.request doesn't natively support PATCH, use request directly
  return post<{ id: number; is_active: boolean }>(`/api/admin/users/${userId}/toggle-active`)
}
