type Callback = (data: any) => void

class WsManager {
  private ws: UniApp.SocketTask | null = null
  private listeners: Map<string, Set<Callback>> = new Map()
  private reconnectCount = 0
  private maxReconnect = 10
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private token = ''
  private closed = false
  private _isConnected = false

  // 房间追踪：重连后自动 re-join
  private joinedRooms: Set<number> = new Set()
  // 发送队列：未连接时排队，连上后 flush
  private sendQueue: object[] = []

  get isConnected() { return this._isConnected }

  connect(token: string) {
    this.token = token
    this.closed = false
    this.doConnect()
  }

  private doConnect() {
    if (this.closed) return
    const wsBase = location?.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = location?.host || '192.168.100.165:8100'
    const url = `${wsBase}//${wsHost}/ws?token=${this.token}`

    this.ws = uni.connectSocket({ url, complete: () => { } })

    this.ws.onOpen(() => {
      console.log('[WS] connected')
      this._isConnected = true
      this.reconnectCount = 0
      this.startHeartbeat()
      this.flushSendQueue()
      this.rejoinRooms()
      this.dispatch('_connected', {})
    })

    this.ws.onMessage((res: any) => {
      try {
        const msg = JSON.parse(typeof res.data === 'string' ? res.data : '')
        if (msg.type === 'pong') return
        // 统一分发：handler 收到 msg.data（与教师端一致）
        this.dispatch(msg.type, msg.data ?? {})
      } catch { /* ignore parse errors */ }
    })

    this.ws.onClose(() => {
      console.log('[WS] disconnected')
      this._isConnected = false
      this.stopHeartbeat()
      if (!this.closed) this.scheduleReconnect()
      this.dispatch('_disconnected', {})
    })

    this.ws.onError(() => {
      /* onClose will fire after onError */
    })
  }

  disconnect() {
    this.closed = true
    this.stopHeartbeat()
    try { this.ws?.close({}) } catch { /* ignore */ }
    this.ws = null
    this._isConnected = false
    this.reconnectCount = 0
    this.sendQueue = []
  }

  on(type: string, cb: Callback) {
    if (!this.listeners.has(type)) this.listeners.set(type, new Set())
    this.listeners.get(type)!.add(cb)
  }

  off(type: string, cb: Callback) {
    this.listeners.get(type)?.delete(cb)
  }

  joinRoom(convId: number) {
    this.joinedRooms.add(convId)
    this.send({ type: 'join_room', data: { conv_id: convId } })
  }

  leaveRoom(convId: number) {
    this.joinedRooms.delete(convId)
    this.send({ type: 'leave_room', data: { conv_id: convId } })
  }

  send(data: object) {
    if (this._isConnected && this.ws) {
      try {
        this.ws.send({ data: JSON.stringify(data) })
      } catch { /* ignore */ }
    } else {
      // 排队，等连上后 flush
      this.sendQueue.push(data)
    }
  }

  private dispatch(type: string, data: any) {
    this.listeners.get(type)?.forEach(cb => {
      try { cb(data) } catch (e) { console.error('[WS dispatch]', e) }
    })
  }

  private flushSendQueue() {
    while (this.sendQueue.length > 0) {
      const data = this.sendQueue.shift()!
      try {
        this.ws?.send({ data: JSON.stringify(data) })
      } catch { break }
    }
  }

  private rejoinRooms() {
    for (const convId of this.joinedRooms) {
      try {
        this.ws?.send({ data: JSON.stringify({ type: 'join_room', data: { conv_id: convId } }) })
      } catch { break }
    }
  }

  private scheduleReconnect() {
    if (this.reconnectCount >= this.maxReconnect) return
    const delay = Math.min(1000 * Math.pow(2, this.reconnectCount), 30000)
    this.reconnectCount++
    console.log(`[WS] reconnect #${this.reconnectCount} in ${delay}ms`)
    setTimeout(() => this.doConnect(), delay)
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

export const wsManager = new WsManager()
