/**
 * v2 状态枚举映射工具
 */

export type ConvStatus = 'ai_serving' | 'pending_teacher' | 'teacher_serving' | 'resolved' | 'closed'

const statusTextMap: Record<string, string> = {
  ai_serving: 'AI 服务中',
  pending_teacher: '待处理',
  teacher_serving: '处理中',
  resolved: '已解决',
  closed: '已关闭',
}

const statusClassMap: Record<string, string> = {
  ai_serving: 'status-ai-serving',
  pending_teacher: 'status-pending',
  teacher_serving: 'status-serving',
  resolved: 'status-resolved',
  closed: 'status-closed',
}

export function getStatusText(status: string): string {
  return statusTextMap[status] || '未知'
}

export function getStatusClass(status: string): string {
  return statusClassMap[status] || 'status-unknown'
}
