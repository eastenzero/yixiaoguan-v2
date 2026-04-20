import { request } from '@/utils/request'
import type { ConversationResponse, MessageResponse } from '@/types/chat'

interface ListResponse<T> {
  items: T[]
  total: number
}

export function createConversation(title?: string): Promise<ConversationResponse> {
  return request<ConversationResponse>({
    url: '/api/conversations',
    method: 'POST',
    data: { title: title || null },
  })
}

export function listConversations(page = 1, size = 20): Promise<ListResponse<ConversationResponse>> {
  return request<ListResponse<ConversationResponse>>({
    url: `/api/conversations?page=${page}&size=${size}`,
  })
}

export function getConversation(id: number): Promise<ConversationResponse> {
  return request<ConversationResponse>({ url: `/api/conversations/${id}` })
}

export function getMessages(convId: number, page = 1, size = 100): Promise<ListResponse<MessageResponse>> {
  return request<ListResponse<MessageResponse>>({
    url: `/api/conversations/${convId}/messages?page=${page}&size=${size}`,
  })
}

export function escalate(convId: number): Promise<any> {
  return request({ url: `/api/conversations/${convId}/escalate`, method: 'POST' })
}
