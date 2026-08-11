export interface Source {
  title: string
  score?: number
  content?: string
  document_id?: string
  dataset_id?: string
  source_url?: string
  original_source?: string
  category?: string
  campus?: string
  college?: string
  published_at?: string
  academic_year?: string
  effective_status?: string
  screenshot_url?: string
  attachment_url?: string
  source_type?: 'official_web' | 'official_wechat' | 'wechat_pending' | 'knowledge_base'
  source_label?: string
  verified?: boolean
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'teacher'
  content: string
  sources?: Source[]
  answer_notice?: string
  knowledge_updated_at?: string
  timestamp: number
  isStreaming?: boolean
  refusal?: boolean
}

export interface UnansweredInviteState {
  message_id: number
  conv_id: number
  dismissed: boolean
}

export type ChatMessage = Message & {
  unanswered_invite?: UnansweredInviteState
}

export type ChatStreamEvent =
  | { event: 'message'; token: string }
  | { event: 'message_end'; full_content: string; sources: Source[]; message_id: number; answer_notice?: string; knowledge_updated_at?: string }
  | { event: 'suggestions'; questions: string[] }
  | { event: 'unanswered_invite'; message_id: number; conv_id: number }
  | { event: 'error'; message: string }
  | { event: 'done' }

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
