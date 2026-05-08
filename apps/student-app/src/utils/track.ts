interface TrackEvent {
  event: string
  props?: Record<string, any>
  client_ts?: string
}

const FLUSH_INTERVAL_MS = 5000
const FLUSH_THRESHOLD = 10
const MAX_BATCH = 50

let queue: TrackEvent[] = []
let flushTimer: ReturnType<typeof setTimeout> | null = null

function getStoredToken(): string {
  try {
    return uni.getStorageSync('v2-token') || ''
  } catch {
    return ''
  }
}

async function flush(): Promise<void> {
  if (queue.length === 0) {
    return
  }

  if (flushTimer) {
    clearTimeout(flushTimer)
    flushTimer = null
  }

  const batch = queue.splice(0, MAX_BATCH)
  const token = getStoredToken()

  if (!token) {
    if (queue.length > 0) {
      scheduleFlush()
    }
    return
  }

  try {
    await new Promise<void>((resolve) => {
      uni.request({
        url: '/api/track',
        method: 'POST',
        header: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        data: { events: batch },
        success: () => resolve(),
        fail: () => resolve(),
      })
    })
  } catch {
    // fire-and-forget
  } finally {
    if (queue.length > 0) {
      scheduleFlush()
    }
  }
}

function scheduleFlush(): void {
  if (flushTimer) {
    return
  }

  flushTimer = setTimeout(() => {
    flushTimer = null
    void flush()
  }, FLUSH_INTERVAL_MS)
}

export function trackEvent(event: string, props?: Record<string, any>): void {
  queue.push({
    event: event.slice(0, 64),
    props: props || {},
    client_ts: new Date().toISOString(),
  })

  if (queue.length >= FLUSH_THRESHOLD) {
    void flush()
    return
  }

  scheduleFlush()
}

export function trackFlushNow(): Promise<void> {
  return flush()
}
