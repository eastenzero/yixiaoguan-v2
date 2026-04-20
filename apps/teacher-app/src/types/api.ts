/**
 * v2 用户信息（FastAPI 返回）
 */
export interface UserInfo {
  id: number
  staff_id: string
  name: string
  role: string
  college_id: number | null
  class_id: number | null
  avatar_url: string | null
}

/**
 * v2 会话
 */
export interface Conversation {
  id: number
  student_id: number
  teacher_id?: number | null
  status: string
  title?: string
  dify_conversation_id?: string | null
  created_at: string
  updated_at: string
  // joined fields
  student_name?: string
  student_class?: string
}

/**
 * v2 消息
 */
export interface Message {
  id: number
  conversation_id: number
  sender_type: string   // student | ai | teacher | system
  sender_id?: number | null
  content: string
  created_at: string
  metadata_?: any
}

/**
 * 分页响应
 */
export interface PageResult<T> {
  items: T[]
  total: number
}
