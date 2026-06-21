import assert from 'node:assert/strict'
import { fileURLToPath } from 'node:url'
import path from 'node:path'
import { createServer } from 'vite'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const appRoot = path.resolve(__dirname, '..')
const srcRoot = path.join(appRoot, 'src')
const requestMockPath = path.join(appRoot, 'tests/mocks/request.ts')
const cacheKey = 'teacher-knowledge-cache'

const storage = new Map()

globalThis.uni = {
  getStorageSync(key) {
    return storage.get(key) || ''
  },
  setStorageSync(key, value) {
    storage.set(key, value)
  }
}

const server = await createServer({
  configFile: false,
  root: appRoot,
  logLevel: 'error',
  resolve: {
    alias: [
      { find: /^@\/utils\/request$/, replacement: requestMockPath },
      { find: '@', replacement: srcRoot }
    ]
  }
})

function cachedEntry(overrides = {}) {
  return {
    id: 7,
    title: '缓存条目',
    content: '缓存内容',
    scope: 'college',
    scope_value: null,
    representative_query: '缓存问题',
    status: 'approved',
    college_id: 1,
    submitted_by: 2,
    reject_reason: null,
    dify_document_id: null,
    created_at: '2026-06-20T00:00:00.000Z',
    published_at: null,
    reviewed_at: null,
    ...overrides
  }
}

async function loadModules() {
  const requestMock = await server.ssrLoadModule('/tests/mocks/request.ts')
  const api = await server.ssrLoadModule('/src/api/knowledge.ts')
  return { api, requestMock }
}

function resetStorage(entries = [cachedEntry()]) {
  storage.clear()
  storage.set(cacheKey, JSON.stringify(entries))
}

async function expectRejectsWithoutCacheMutation(action, expectedStatus = 'approved') {
  resetStorage()
  await assert.rejects(action, /backend unavailable/)
  const entries = JSON.parse(storage.get(cacheKey))
  assert.equal(entries[0].status, expectedStatus)
}

try {
  const { api, requestMock } = await loadModules()

  requestMock.__resetRequestMock()
  requestMock.__mockRequest('POST', '/api/v1/knowledge/entries/7/offline', () => {
    throw new Error('backend unavailable')
  })
  await expectRejectsWithoutCacheMutation(() => api.offlineEntry(7))

  requestMock.__resetRequestMock()
  requestMock.__mockRequest('POST', '/api/v1/knowledge/reviews/7/approve', () => {
    throw new Error('backend unavailable')
  })
  await expectRejectsWithoutCacheMutation(() => api.approveKnowledge(7))

  requestMock.__resetRequestMock()
  requestMock.__mockRequest('POST', '/api/v1/knowledge/reviews/7/reject', () => {
    throw new Error('backend unavailable')
  })
  await expectRejectsWithoutCacheMutation(() => api.rejectKnowledge(7, '资料不完整'))

  requestMock.__resetRequestMock()
  resetStorage([cachedEntry({ title: '接口失败时的缓存条目' })])
  const entriesRes = await api.getKnowledgeEntries({ pageNum: 1, pageSize: 20 })
  assert.equal(entriesRes.items.length, 1)
  assert.equal(entriesRes.items[0].title, '接口失败时的缓存条目')
  assert.equal(entriesRes.fallback?.source, 'localStorage')
  assert.match(entriesRes.fallback?.message || '', /接口失败/)

  requestMock.__resetRequestMock()
  resetStorage([cachedEntry({ status: 'pending' })])
  const reviewsRes = await api.getPendingReviews(20)
  assert.equal(reviewsRes.items.length, 1)
  assert.equal(reviewsRes.fallback?.source, 'localStorage')

  console.log('knowledge API fallback tests passed')
} finally {
  await server.close()
}
