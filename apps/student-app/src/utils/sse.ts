import { REQUEST_TIMEOUT_MS, toApiUrl } from '@/utils/runtime'
import type { Source } from '@/types/chat'

export interface SSECallbacks {
  onToken: (token: string) => void
  onEnd: (data: { full_content: string; sources: Source[]; message_id: number; answer_notice?: string }) => void
  onError: (msg: string) => void
  onSuggestions?: (questions: string[]) => void
  onUnansweredInvite?: (data: { message_id: number; conv_id: number }) => void
}

type SSEEventData = Record<string, any>

function dispatchEvent(eventName: string, data: SSEEventData, callbacks: SSECallbacks): void {
  if (eventName === 'message') {
    callbacks.onToken(data.token || '')
  } else if (eventName === 'message_end') {
    callbacks.onEnd({
      full_content: data.full_content || '',
      sources: data.sources || [],
      message_id: data.message_id || 0,
      answer_notice: data.answer_notice || '',
    })
  } else if (eventName === 'unanswered_invite') {
    callbacks.onUnansweredInvite?.({
      message_id: data.message_id || 0,
      conv_id: data.conv_id || 0,
    })
  } else if (eventName === 'suggestions') {
    callbacks.onSuggestions?.(data.questions || [])
  } else if (eventName === 'error') {
    callbacks.onError(data.message || 'AI 服务异常')
  }
}

function parseEventBlock(block: string, callbacks: SSECallbacks): void {
  const lines = block.split(/\r?\n/)
  let eventName = 'message'
  const dataLines: string[] = []

  for (const line of lines) {
    if (line.startsWith('event:')) {
      eventName = line.slice(6).trim()
    } else if (line.startsWith('data:')) {
      dataLines.push(line.slice(5).trimStart())
    }
  }

  if (eventName === 'done') return
  if (!dataLines.length) return

  try {
    const data = JSON.parse(dataLines.join('\n')) as SSEEventData
    dispatchEvent(eventName, data, callbacks)
  } catch {
    // Ignore malformed SSE data lines; the stream can continue.
  }
}

function consumeSSEText(text: string, callbacks: SSECallbacks): void {
  const normalized = text.replace(/\r\n/g, '\n')
  const blocks = normalized.split(/\n\n+/)
  for (const block of blocks) {
    if (block.trim()) parseEventBlock(block, callbacks)
  }
}

async function fetchStream(
  url: string,
  body: object,
  token: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'Accept': 'text/event-stream',
    },
    body: JSON.stringify(body),
    signal,
  })

  if (!resp.ok) {
    const text = await resp.text().catch(() => '')
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }

  if (!resp.body) {
    const text = await resp.text()
    consumeSSEText(text, callbacks)
    return
  }

  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const parts = buffer.replace(/\r\n/g, '\n').split(/\n\n+/)
    buffer = parts.pop() || ''
    for (const part of parts) {
      if (part.trim()) parseEventBlock(part, callbacks)
    }
  }

  buffer += decoder.decode()
  if (buffer.trim()) parseEventBlock(buffer, callbacks)
}

function bufferedRequest(url: string, body: object, token: string, callbacks: SSECallbacks): Promise<void> {
  return new Promise((resolve, reject) => {
    uni.request({
      url,
      method: 'POST',
      timeout: REQUEST_TIMEOUT_MS,
      responseType: 'text',
      header: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        'Accept': 'text/event-stream',
      },
      data: body,
      success: (res) => {
        if (res.statusCode < 200 || res.statusCode >= 300) {
          const data = res.data as any
          reject(new Error(data?.detail || data?.message || `HTTP ${res.statusCode}`))
          return
        }

        if (typeof res.data === 'string') {
          consumeSSEText(res.data, callbacks)
        } else if (res.data && typeof res.data === 'object') {
          const data = res.data as any
          callbacks.onEnd({
            full_content: data.full_content || data.content || '',
            sources: data.sources || [],
            message_id: data.message_id || 0,
            answer_notice: data.answer_notice || '',
          })
        }
        resolve()
      },
      fail: (err) => reject(new Error(err.errMsg || '网络连接失败')),
    })
  })
}

export async function fetchSSE(
  url: string,
  body: object,
  token: string,
  callbacks: SSECallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const requestUrl = toApiUrl(url)

  if (typeof fetch === 'function' && typeof TextDecoder !== 'undefined') {
    try {
      await fetchStream(requestUrl, body, token, callbacks, signal)
      return
    } catch (error) {
      // H5 can fail on CORS/proxy mismatch; fall through to uni.request when available.
      if (typeof uni === 'undefined' || typeof uni.request !== 'function') {
        throw error
      }
    }
  }

  await bufferedRequest(requestUrl, body, token, callbacks)
}
