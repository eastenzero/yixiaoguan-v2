import request from '@/utils/request'

// 分页查询知识条目
export function getKnowledgeEntries(params?: {
  categoryId?: number
  status?: number
  title?: string
  pageNum?: number
  pageSize?: number
}) {
  return request({
    url: '/api/v1/knowledge/entries',
    method: 'get',
    params: {
      pageNum: 1,
      pageSize: 10,
      ...params
    }
  })
}

// 获取知识条目详情
export function getKnowledgeDetail(id: number) {
  return request({
    url: `/api/v1/knowledge/entries/${id}`,
    method: 'get'
  })
}

// 获取分类列表
export function getCategories() {
  return request({
    url: '/api/v1/knowledge/categories',
    method: 'get'
  })
}

// 下线条目
export function offlineEntry(id: number) {
  return request({
    url: `/api/v1/knowledge/entries/${id}/offline`,
    method: 'post'
  })
}
