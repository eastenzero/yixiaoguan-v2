/**
 * WebSocket 管理器 — v2 单连接 + room 模式
 * H5: 原生 WebSocket
 * 小程序: uni.connectSocket
 */

type MessageHandler = (data: any) => void

class WsManager {
  private task: UniApp.SocketTask | null = null
  private token = ''
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private reconnectCount = 0
  private maxReconnect = 10
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private _isConnected = false

  // 房间追踪：重连后自动 re-join
  private joinedRooms: Set<number> = new Set()
  // 发送队列：未连接时排队，连上后 flush
  private sendQueue: object[] = []

  get isConnected() { return this._isConnected }

  connect(token: string) {
    this.token = token
    this.reconnectCount = 0
    this.doConnect()
  }

  disconnect() {
    this.reconnectCount = this.maxReconnect // prevent reconnect
    this.cleanup()
  }

  on(type: string, handler: MessageHandler) {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set())
    this.handlers.get(type)!.add(handler)
  }

  off(type: string, handler: MessageHandler) {
    this.handlers.get(type)?.delete(handler)
  }

  joinRoom(convId: number) {
    this.joinedRooms.add(convId)
    this.send({ type: 'join_room', data: { conv_id: convId } })
  }

  leaveRoom(convId: number) {
    this.joinedRooms.delete(convId)
    this.send({ type: 'leave_room', data: { conv_id: convId } })
  }

  send(data: any) {
    if (this.task && this._isConnected) {
      try {
        this.task.send({ data: JSON.stringify(data) })
      } catch { /* ignore */ }
    } else {
      this.sendQueue.push(data)
    }
  }

  private doConnect() {
    this.cleanup()
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = location.host
    const url = `${protocol}//${host}/ws?token=${this.token}`

    try {
      this.task = uni.connectSocket({
        url,
        complete: () => { }
      })

      this.task.onOpen(() => {
        // silent: WS connected
        this._isConnected = true
        this.reconnectCount = 0
        this.startHeartbeat()
        this.flushSendQueue()
        this.rejoinRooms()
        this.emit('_connected', {})
      })

      this.task.onMessage((res: { data: string | ArrayBuffer }) => {
        try {
          const msg = JSON.parse(res.data as string)
          const type = msg.type
          if (type === 'pong') return
          // 统一分发：handler 收到 msg.data（与学生端一致）
          this.emit(type, msg.data ?? {})
          this.emit('*', msg)
        } catch { /* ignore non-json */ }
      })

      this.task.onClose(() => {
        // silent: WS disconnected
        this._isConnected = false
        this.stopHeartbeat()
        this.emit('_disconnected', {})
        this.scheduleReconnect()
      })

      this.task.onError((err: any) => {
        // silent: WS errors are expected during reconnect
      })
    } catch (e) {
      // silent: connect failure triggers reconnect
      this.scheduleReconnect()
    }
  }

  private emit(type: string, data: any) {
    this.handlers.get(type)?.forEach(h => h(data))
  }

  private flushSendQueue() {
    while (this.sendQueue.length > 0) {
      const data = this.sendQueue.shift()!
      try {
        this.task?.send({ data: JSON.stringify(data) })
      } catch { break }
    }
  }

  private rejoinRooms() {
    for (const convId of this.joinedRooms) {
      try {
        this.task?.send({ data: JSON.stringify({ type: 'join_room', data: { conv_id: convId } }) })
      } catch { break }
    }
  }

  private cleanup() {
    this.stopHeartbeat()
    if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null }
    if (this.task) {
      try { this.task.close({}) } catch { /* ignore */ }
      this.task = null
    }
    this._isConnected = false
    this.sendQueue = []
  }

  private scheduleReconnect() {
    if (this.reconnectCount >= this.maxReconnect) return
    const delay = Math.min(1000 * Math.pow(2, this.reconnectCount), 30000)
    this.reconnectCount++
    // silent: reconnecting
    this.reconnectTimer = setTimeout(() => this.doConnect(), delay)
  }

  private startHeartbeat() {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'ping' })
    }, 30000)
  }

  private stopHeartbeat() {
    if (this.heartbeatTimer) { clearInterval(this.heartbeatTimer); this.heartbeatTimer = null }
  }
}

export const wsManager = new WsManager()
