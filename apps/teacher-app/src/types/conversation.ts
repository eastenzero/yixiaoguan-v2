/**
 * v2 会话状态 (string enum, 与后端 ConversationStatus 一致)
 */
export type ConversationStatus =
  | 'ai_serving'
  | 'pending_teacher'
  | 'teacher_serving'
  | 'resolved'
  | 'closed'

export const ConversationStatusLabel: Record<string, string> = {
  ai_serving: 'AI 服务中',
  pending_teacher: '待处理',
  teacher_serving: '处理中',
  resolved: '已解决',
  closed: '已关闭',
}
