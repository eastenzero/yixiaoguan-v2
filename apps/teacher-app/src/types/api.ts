/**
 * v2 用户信息（FastAPI 返回）
 */
export interface UserInfo {
  id: number
  staff_id: string
  name: string
  role: string
  college_id: number | null
  class_id: number | null
  avatar_url: string | null
}

/**
 * v2 会话
 */
export interface Conversation {
  id: number
  student_id: number
  teacher_id?: number | null
  status: string
  title?: string
  dify_conversation_id?: string | null
  created_at: string
  updated_at: string
  // joined fields
  student_name?: string
  student_class?: string
}

/**
 * v2 消息
 */
export interface Message {
  id: number
  conversation_id: number
  sender_type: string   // student | ai | teacher | system
  sender_id?: number | null
  content: string
  created_at: string
  metadata_?: any
}

/**
 * 分页响应
 */
export interface PageResult<T> {
  items: T[]
  total: number
}

export interface ApiFallbackMeta {
  source: 'localStorage'
  message: string
}

export interface FallbackPageResult<T> extends PageResult<T> {
  fallback?: ApiFallbackMeta
}

export type KnowledgeScope = 'class' | 'college' | 'global'

export type KnowledgePublishMode = 'published' | 'pending_review'

export interface UnansweredTopItem {
  id: number
  question_text: string
  hit_count: number
  latest_at: string
  college_id: number | null
  class_id: number | null
  sample_conv_ids: number[]
}

export interface UnansweredTopResponse {
  items: UnansweredTopItem[]
  total: number
}

export interface KnowledgeEntry {
  id: number
  title: string
  content: string
  raw_content: string | null
  scope: KnowledgeScope
  scope_value: number | null
  representative_query: string
  status: string
  college_id: number | null
  submitted_by: number
  reject_reason: string | null
  dify_document_id: string | null
  dify_dataset_id?: string | null
  source_type?: 'kb_entry' | 'suggestion'
  category?: string | null
  tags?: string[] | null
  original_source?: string | null
  source_url?: string | null
  material_id?: string | null
  campus?: string | null
  original_filename?: string | null
  created_at: string
  published_at: string | null
  reviewed_at: string | null
  fallback?: ApiFallbackMeta
}

export interface CreateKnowledgeDraftPayload {
  unanswered_question_id: number
  raw_answer: string
  confirmed_content?: string | null
  scope: KnowledgeScope
  scope_value?: number | null
}

export interface CreateKnowledgeDraftResponse {
  entry: KnowledgeEntry
  publish_mode: KnowledgePublishMode
}

export interface KnowledgeDraftPreviewResponse {
  unanswered_question_id: number
  title: string
  content: string
  raw_content: string
  scope: KnowledgeScope
  scope_value: number | null
  scope_label: string
  representative_query: string
  college_id: number | null
  publish_mode: 'requires_confirmation'
}
