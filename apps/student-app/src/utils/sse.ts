export interface Source {
  title: string
  score?: number
  content?: string
}

export interface SSECallbacks {
  onToken: (token: string) => void
  onEnd: (data: { full_content: string; sources: Source[]; message_id: number }) => void
  onError: (msg: string) => void
  onSuggestions?: (questions: string[]) => void
}

export async function fetchSSE(
  url: string,
  body: object,
  token: string,
  callbacks: SSECallbacks
): Promise<void> {
  const resp = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  })

  if (!resp.ok) {
    const text = await resp.text().catch(() => '')
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }

  const reader = resp.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentEvent = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEvent = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6))
          if (currentEvent === 'message') {
            callbacks.onToken(data.token || '')
          } else if (currentEvent === 'message_end') {
            callbacks.onEnd({
              full_content: data.full_content || '',
              sources: data.sources || [],
              message_id: data.message_id || 0,
            })
          } else if (currentEvent === 'suggestions') {
            callbacks.onSuggestions?.(data.questions || [])
          } else if (currentEvent === 'error') {
            callbacks.onError(data.message || 'AI 服务异常')
          }
          // event: done → no action needed, stream ends naturally
        } catch { /* ignore JSON parse errors for non-data lines */ }
      }
    }
  }
}
