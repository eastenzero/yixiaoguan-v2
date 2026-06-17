import request from '@/utils/request'

// 获取待处理工单列表
export function getPendingEscalations(pageNum = 1, pageSize = 10) {
  return request({
    url: '/api/v1/escalations/pending',
    method: 'GET',
    params: { pageNum, pageSize }
  })
}

// 获取教师已接工单列表
export function getAssignedEscalations(status?: number, pageNum = 1, pageSize = 10) {
  return request({
    url: '/api/v1/escalations/assigned',
    method: 'GET',
    params: { status, pageNum, pageSize }
  })
}

// 获取工单详情
export function getEscalationDetail(id: number) {
  return request({
    url: `/api/v1/escalations/${id}`,
    method: 'GET'
  })
}

// 教师接单
export function assignEscalation(id: number) {
  return request({
    url: `/api/v1/escalations/${id}/assign`,
    method: 'PUT'
  })
}

// 教师仅回复（不结案）
export function replyEscalation(id: number, teacherReply: string) {
  return request({
    url: `/api/v1/escalations/${id}/reply`,
    method: 'PUT',
    data: { teacherReply }
  })
}

// 获取工单关联会话的全部消息（教师接单后可访问）
export function getConversationMessages(conversationId: number) {
  return request({
    url: `/api/v1/conversations/${conversationId}/messages`,
    method: 'GET'
  })
}

// 教师回复并解决
export function resolveEscalation(id: number, teacherReply: string) {
  return request({
    url: `/api/v1/escalations/${id}/resolve`,
    method: 'PUT',
    data: { teacherReply }
  })
}
