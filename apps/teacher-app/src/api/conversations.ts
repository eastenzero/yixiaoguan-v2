/**
 * 会话 API — v2 FastAPI
 */
import { get, post } from '@/utils/request'
import type { Conversation, Message, PageResult } from '@/types/api'

/** 获取会话列表（教师看到 pending_teacher + 自己已接的） */
export function listConversations(
  page = 1,
  size = 20,
  status?: string
): Promise<PageResult<Conversation>> {
  return get<PageResult<Conversation>>('/api/conversations', { page, size, status })
}

/** 获取会话详情 */
export function getConversation(convId: number): Promise<Conversation> {
  return get<Conversation>(`/api/conversations/${convId}`)
}

/** 获取会话消息列表 */
export function listMessages(
  convId: number,
  page = 1,
  size = 50
): Promise<PageResult<Message>> {
  return get<PageResult<Message>>(`/api/conversations/${convId}/messages`, { page, size })
}

/** 教师发送消息 */
export function sendMessage(convId: number, content: string): Promise<Message> {
  return post<Message>(`/api/conversations/${convId}/messages`, { content })
}

/** 教师接单 (pending_teacher → teacher_serving) */
export function acceptConversation(convId: number): Promise<Conversation> {
  return post<Conversation>(`/api/conversations/${convId}/accept`)
}

/** 教师解决 (teacher_serving → resolved) */
export function resolveConversation(convId: number): Promise<Conversation> {
  return post<Conversation>(`/api/conversations/${convId}/resolve`)
}
