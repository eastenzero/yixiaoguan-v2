export interface Source {
  title: string
  score?: number
  content?: string
  document_id?: string | null
  dataset_id?: string | null
  source_url?: string | null
  source_label?: string
  source_type?: string
  verified?: boolean
  published_at?: string | null
  last_verified?: string | null
  academic_year?: string | null
  effective_status?: string | null
  freshness?: string | null
  policy_level?: string | null
  source_paths?: string[]
  review_required?: boolean
}

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'teacher'
  content: string
  sources?: Source[]
  timestamp: number
  isStreaming?: boolean
  refusal?: boolean
  answer_notice?: string
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
  | { event: 'message_end'; full_content: string; sources: Source[]; message_id: number; answer_notice?: string }
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
