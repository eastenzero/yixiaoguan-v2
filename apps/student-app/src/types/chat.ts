export interface Source {
  title: string
  score?: number
  content?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'teacher'
  content: string
  sources?: Source[]
  timestamp: number
  isStreaming?: boolean
}

export interface ConversationResponse {
  id: number
  student_id: number
  teacher_id: number | null
  status: string
  dify_conversation_id: string | null
  title: string
  created_at: string
  updated_at: string
  resolved_at: string | null
  closed_at: string | null
}

export interface MessageResponse {
  id: number
  conversation_id: number
  sender_type: string
  sender_id: number | null
  content: string
  metadata_: Record<string, any> | null
  created_at: string
}

export type ConversationStatus =
  | 'ai_serving'
  | 'pending_teacher'
  | 'teacher_serving'
  | 'resolved'
  | 'closed'
