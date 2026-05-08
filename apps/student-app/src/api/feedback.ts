import { request } from '@/utils/request'

export function submitGeneralFeedback(payload: {
  content: string
  contact?: string
  device_id?: string
}): Promise<{ id: number; ok: boolean }> {
  return request({
    url: '/api/feedback/general',
    method: 'POST',
    data: payload,
  })
}

export function submitUnansweredFeedback(payload: {
  conv_id: number
  message_id: number
  college_id?: number | null
  grade?: string | null
  category?: string | null
  note?: string | null
}): Promise<{ id: number; ok: boolean }> {
  return request({
    url: '/api/feedback/unanswered',
    method: 'POST',
    data: payload,
  })
}
