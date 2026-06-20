import request, { get, post } from '@/utils/request'
import type {
  CreateKnowledgeDraftPayload,
  CreateKnowledgeDraftResponse,
  FallbackPageResult,
  KnowledgeDraftPreviewResponse,
  KnowledgeEntry,
  PageResult,
  UnansweredTopResponse
} from '@/types/api'

const KNOWLEDGE_CACHE_KEY = 'teacher-knowledge-cache'
const LIST_FALLBACK_MESSAGE = '知识库接口失败，正在显示本地缓存'
const DETAIL_FALLBACK_MESSAGE = '知识详情接口失败，正在显示本地缓存'

function readKnowledgeCache(): KnowledgeEntry[] {
  try {
    const raw = uni.getStorageSync(KNOWLEDGE_CACHE_KEY)
    if (!raw) return []
    return JSON.parse(raw) as KnowledgeEntry[]
  } catch {
    return []
  }
}

function writeKnowledgeCache(entries: KnowledgeEntry[]) {
  try {
    uni.setStorageSync(KNOWLEDGE_CACHE_KEY, JSON.stringify(entries))
  } catch {
  }
}

function normalizeStatus(status: unknown): string {
  if (typeof status === 'string') return status
  if (status === 1) return 'approved'
  if (status === 2) return 'pending'
  if (status === 3) return 'offline'
  return 'draft'
}

function normalizeEntry(input: any): KnowledgeEntry {
  return {
    id: Number(input?.id || 0),
    title: String(input?.title || input?.representative_query || '未命名知识'),
    content: String(input?.content || ''),
    raw_content: input?.raw_content ?? input?.rawContent ?? null,
    scope: input?.scope || 'college',
    scope_value: input?.scope_value ?? input?.scopeValue ?? null,
    representative_query: String(input?.representative_query || input?.title || ''),
    status: normalizeStatus(input?.status),
    college_id: input?.college_id ?? input?.collegeId ?? null,
    submitted_by: Number(input?.submitted_by ?? input?.submittedBy ?? 0),
    reject_reason: input?.reject_reason ?? input?.rejectReason ?? null,
    dify_document_id: input?.dify_document_id ?? input?.difyDocumentId ?? null,
    dify_dataset_id: input?.dify_dataset_id ?? input?.difyDatasetId ?? null,
    source_type: input?.source_type ?? input?.sourceType ?? (input?.dify_dataset_id ? 'kb_entry' : 'suggestion'),
    category: input?.category ?? null,
    tags: Array.isArray(input?.tags) ? input.tags : null,
    original_source: input?.original_source ?? input?.originalSource ?? null,
    source_url: input?.source_url ?? input?.sourceUrl ?? null,
    material_id: input?.material_id ?? input?.materialId ?? null,
    campus: input?.campus ?? null,
    original_filename: input?.original_filename ?? input?.originalFilename ?? null,
    created_at: String(input?.created_at || input?.createdAt || new Date().toISOString()),
    published_at: input?.published_at ?? input?.publishedAt ?? null,
    reviewed_at: input?.reviewed_at ?? input?.reviewedAt ?? null
  }
}

function upsertKnowledgeEntry(entry: KnowledgeEntry) {
  const current = readKnowledgeCache()
  const next = [entry, ...current.filter(item => item.id !== entry.id)]
  writeKnowledgeCache(next)
}

function filterCachedEntries(params?: {
  status?: string
  title?: string
  pageNum?: number
  pageSize?: number
}): PageResult<KnowledgeEntry> {
  const keyword = (params?.title || '').trim().toLowerCase()
  const filtered = readKnowledgeCache().filter(item => {
    const matchesStatus = !params?.status || item.status === params.status
    const matchesKeyword = !keyword || item.title.toLowerCase().includes(keyword) || item.content.toLowerCase().includes(keyword)
    return matchesStatus && matchesKeyword
  })
  const pageNum = params?.pageNum || 1
  const pageSize = params?.pageSize || filtered.length || 20
  const start = (pageNum - 1) * pageSize
  return {
    items: filtered.slice(start, start + pageSize),
    total: filtered.length
  }
}

function withFallbackMeta(
  result: PageResult<KnowledgeEntry>,
  message = LIST_FALLBACK_MESSAGE
): FallbackPageResult<KnowledgeEntry> {
  return {
    ...result,
    fallback: {
      source: 'localStorage',
      message
    }
  }
}

// 分页查询知识条目
export function getKnowledgeEntries(params?: {
  categoryId?: number
  category?: string
  campus?: string
  source?: string
  collegeId?: number
  status?: string
  title?: string
  pageNum?: number
  pageSize?: number
}): Promise<FallbackPageResult<KnowledgeEntry>> {
  return get<any>('/api/v1/knowledge/entries', {
    pageNum: 1,
    pageSize: 10,
    ...params,
    college_id: params?.collegeId
  }).then((res) => {
    if (Array.isArray(res?.items)) {
      return {
        items: res.items.map(normalizeEntry),
        total: Number(res?.total || res.items.length)
      }
    }
    if (Array.isArray(res?.rows)) {
      return {
        items: res.rows.map(normalizeEntry),
        total: Number(res?.total || res.rows.length)
      }
    }
    return withFallbackMeta(filterCachedEntries(params), '知识库接口返回异常，正在显示本地缓存')
  }).catch(() => withFallbackMeta(filterCachedEntries(params)))
}

// 获取知识条目详情
export function getKnowledgeDetail(id: number): Promise<KnowledgeEntry> {
  return request<any>({
    url: `/api/v1/knowledge/entries/${id}`,
    method: 'GET'
  }).then((res) => normalizeEntry(res)).catch((error) => {
    const matched = readKnowledgeCache().find(item => item.id === id)
    if (!matched) {
      throw error
    }
    return {
      ...matched,
      fallback: {
        source: 'localStorage',
        message: DETAIL_FALLBACK_MESSAGE
      }
    }
  })
}

// 获取分类列表
export function getCategories() {
  return request({
    url: '/api/v1/knowledge/categories',
    method: 'GET'
  })
}

// 下线条目
export function offlineEntry(id: number) {
  return request({
    url: `/api/v1/knowledge/entries/${id}/offline`,
    method: 'POST'
  })
}

export function getUnansweredTop(limit = 20): Promise<UnansweredTopResponse> {
  return get<UnansweredTopResponse>('/api/v1/knowledge/unanswered-top', { limit })
}

export function createKnowledgeDraft(payload: CreateKnowledgeDraftPayload): Promise<CreateKnowledgeDraftResponse> {
  return post<CreateKnowledgeDraftResponse>('/api/v1/knowledge/drafts', payload).then((res) => {
    upsertKnowledgeEntry(normalizeEntry(res.entry))
    return {
      ...res,
      entry: normalizeEntry(res.entry)
    }
  })
}

export function previewKnowledgeDraft(payload: CreateKnowledgeDraftPayload): Promise<KnowledgeDraftPreviewResponse> {
  return post<KnowledgeDraftPreviewResponse>('/api/v1/knowledge/drafts/preview', payload)
}

export function getPendingReviews(limit = 20): Promise<FallbackPageResult<KnowledgeEntry>> {
  return get<any>('/api/v1/knowledge/reviews/pending', { limit }).then((res) => {
    const items = Array.isArray(res?.items) ? res.items.map(normalizeEntry) : []
    return {
      items,
      total: Number(res?.total || items.length)
    }
  }).catch(() => {
    const items = readKnowledgeCache().filter(item => item.status === 'pending').slice(0, limit)
    return withFallbackMeta({
      items,
      total: items.length
    })
  })
}

export function approveKnowledge(id: number) {
  return post(`/api/v1/knowledge/reviews/${id}/approve`)
}

export function rejectKnowledge(id: number, reject_reason: string) {
  return post(`/api/v1/knowledge/reviews/${id}/reject`, { reject_reason })
}
