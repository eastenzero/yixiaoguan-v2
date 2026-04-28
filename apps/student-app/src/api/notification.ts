import { request } from '@/utils/request'

export interface UnreadSummaryItem {
  conv_id: number
  title: string
  status: string
  unread_count: number
  last_message_at: string | null
  last_message_sender_type: 'student' | 'ai' | 'teacher' | 'system' | null
  last_read_at: string | null
}

export interface UnreadSummaryResponse {
  items: UnreadSummaryItem[]
  total_unread: number
}

export function getUnreadSummary(): Promise<UnreadSummaryResponse> {
  return request<UnreadSummaryResponse>({ url: '/api/conversations/unread-summary' })
}

export function markRead(convId: number): Promise<void> {
  return request<void>({
    url: `/api/conversations/${convId}/mark-read`,
    method: 'POST',
  })
}
