/**
 * Centrifugo 客户端管理器 — 替代旧 websocket.ts
 * API 与旧 wsManager 兼容，方便平滑切换
 */
import { Centrifuge, Subscription } from 'centrifuge'

type EventHandler = (data: any) => void

class CentrifugeManager {
  private client: Centrifuge | null = null
  private subscriptions: Map<string, Subscription> = new Map()
  private handlers: Map<string, Set<EventHandler>> = new Map()
  private _isConnected = false

  get isConnected() { return this._isConnected }

  connect(centrifugoToken: string, getToken?: () => Promise<string>) {
    if (this.client) {
      this.disconnect()
    }
    const wsUrl = location.protocol === 'https:'
      ? `wss://${location.host}/centrifugo/connection/websocket`
      : `ws://${location.host}/centrifugo/connection/websocket`

    this.client = new Centrifuge(wsUrl, {
      token: centrifugoToken,
      getToken,
    })

    // 服务端订阅频道的消息通过顶层事件分发
    this.client.on('publication', (ctx) => {
      const msg = ctx.data
      this.dispatch(msg?.type || 'unknown', msg?.data || msg)
    })

    this.client.on('connected', () => {
      console.log('[Centrifuge] connected')
      this._isConnected = true
      this.dispatch('_connected', {})
    })

    this.client.on('disconnected', (ctx) => {
      console.log('[Centrifuge] disconnected', ctx.reason)
      this._isConnected = false
      this.dispatch('_disconnected', { reason: ctx.reason })
    })

    this.client.connect()
  }

  disconnect() {
    this.subscriptions.forEach(sub => sub.unsubscribe())
    this.subscriptions.clear()
    this.client?.disconnect()
    this.client = null
    this._isConnected = false
  }

  joinConversation(convId: number) {
    const channel = `conv:${convId}`
    if (this.subscriptions.has(channel) || !this.client) return

    const sub = this.client.newSubscription(channel, {
      recoverable: true,
    })

    sub.on('publication', (ctx) => {
      const msg = ctx.data
      this.dispatch(msg?.type || 'unknown', msg?.data || msg)
    })

    sub.subscribe()
    this.subscriptions.set(channel, sub)
  }

  leaveConversation(convId: number) {
    const channel = `conv:${convId}`
    const sub = this.subscriptions.get(channel)
    if (sub) {
      sub.unsubscribe()
      this.subscriptions.delete(channel)
    }
  }

  sendTyping(convId: number, userId: number, role: string) {
    const channel = `conv:${convId}`
    const sub = this.subscriptions.get(channel)
    sub?.publish({ type: 'typing', user_id: userId, role })
  }

  on(type: string, handler: EventHandler) {
    if (!this.handlers.has(type)) this.handlers.set(type, new Set())
    this.handlers.get(type)!.add(handler)
  }

  off(type: string, handler: EventHandler) {
    this.handlers.get(type)?.delete(handler)
  }

  private dispatch(type: string, data: any) {
    this.handlers.get(type)?.forEach(h => {
      try { h(data) } catch (e) { console.error('[Centrifuge dispatch]', e) }
    })
  }
}

export const centrifugeManager = new CentrifugeManager()
