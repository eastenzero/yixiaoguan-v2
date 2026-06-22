import { computed, nextTick, onMounted, onUnmounted, reactive, ref } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import { createConversation, getConversation, getMessages, escalate } from '@/api/chat'
import { useUserStore } from '@/stores/user'
import { fetchSSE } from '@/utils/sse'
import { request } from '@/utils/request'
import { wsManager } from '@/utils/websocket'
import { centrifugeManager } from '@/utils/centrifuge'
import { trackEvent } from '@/utils/track'
import type {
  ChatMessage,
  ConversationStatus,
  Message,
  MessageResponse,
  Source,
} from '@/types/chat'

const DISMISSED_KEY = 'dismissed_unanswered_msg_ids'
const REFUSAL_KEYWORDS = [
  '尚未学习到', '请咨询您的辅导员', '无法回答', '暂时无法',
  '超出了我的知识范围', '建议您直接咨询', '暂时不可用', '请稍后重试',
  '无法为您提供', '没有找到相关', '不在我的服务范围',
  '转人工请求', '转接人工客服', '转人工服务', '转接人工',
]

function loadDismissedSet(): Set<number> {
  try {
    const raw = uni.getStorageSync(DISMISSED_KEY) || '[]'
    const arr = JSON.parse(raw) as number[]
    return new Set(arr.filter(n => typeof n === 'number'))
  } catch {
    return new Set()
  }
}

function saveDismissedId(id: number): void {
  try {
    const set = loadDismissedSet()
    set.add(id)
    const arr = Array.from(set).slice(-500)
    uni.setStorageSync(DISMISSED_KEY, JSON.stringify(arr))
  } catch {
    // Storage failures should not block the conversation flow.
  }
}

function mapServerMessage(m: MessageResponse): ChatMessage {
  const roleMap: Record<string, Message['role']> = {
    student: 'user',
    ai: 'assistant',
    teacher: 'teacher',
    system: 'system',
  }
  return {
    id: String(m.id),
    role: roleMap[m.sender_type] || 'system',
    content: m.content || '',
    sources: m.metadata_?.sources || [],
    timestamp: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
  }
}

function getViewportHeight(): number {
  try {
    return uni.getSystemInfoSync().windowHeight || 667
  } catch {
    return 667
  }
}

export function formatChatTime(timestamp: number): string {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (date.toDateString() === now.toDateString()) {
    return `今天 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
  }
  return `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

export function isRefusalMessage(msg: Message): boolean {
  if (msg.role !== 'assistant' || !msg.content) return false
  if (REFUSAL_KEYWORDS.some(kw => msg.content.includes(kw))) return true
  if (msg.content.includes('抱歉') && (!msg.sources || msg.sources.length === 0)) return true
  return false
}

export function useChatSession() {
  const userStore = useUserStore()

  const messages = ref<ChatMessage[]>([])
  const inputMessage = ref('')
  const isStreaming = ref(false)
  const isTyping = ref(false)
  const scrollTop = ref(0)
  const conversationId = ref<number | null>(null)
  const conversationStatus = ref<ConversationStatus>('ai_serving')
  const escalateLoading = ref(false)
  const suggestedQuestions = ref<string[]>([])
  const showCallMenu = ref(false)
  const sourcePopup = reactive({ visible: false, title: '', content: '' })
  const sourceSheetHeight = ref(50)

  let sheetTouchStartY = 0
  let sheetHeightAtStart = 50

  const canSend = computed(() => inputMessage.value.trim().length > 0 && !isStreaming.value)

  const inputPlaceholder = computed(() => {
    if (conversationStatus.value === 'teacher_serving') return '发送消息给老师...'
    if (conversationStatus.value === 'pending_teacher') return '等待老师接入...'
    return '输入你的问题...'
  })

  function scrollToBottom() {
    nextTick(() => { scrollTop.value = 9999999 + Math.random() })
  }

  function onNewMessage(data: any) {
    if (data.conversation_id !== conversationId.value && data.conv_id !== conversationId.value) return
    const senderType = data.sender_type || ''
    if (senderType === 'teacher') {
      messages.value.push({
        id: `teacher-${data.id || Date.now()}`,
        role: 'teacher',
        content: data.content || '',
        timestamp: data.created_at ? new Date(data.created_at).getTime() : Date.now(),
      })
      scrollToBottom()
    } else if (senderType === 'system') {
      messages.value.push({
        id: `system-ws-${data.id || Date.now()}`,
        role: 'system',
        content: data.content || '',
        timestamp: data.created_at ? new Date(data.created_at).getTime() : Date.now(),
      })
      scrollToBottom()
    }
  }

  function onStatusChanged(data: any) {
    const convId = data.conversationId || data.conversation_id || data.conv_id
    if (convId !== conversationId.value) return
    const newStatus = (data.newStatus || data.new_status || data.status) as ConversationStatus
    conversationStatus.value = newStatus

    let systemMsg = ''
    if (newStatus === 'teacher_serving') systemMsg = '老师已接入，你可以直接向老师提问。'
    else if (newStatus === 'resolved') systemMsg = '问题已解决。如有新问题，可继续提问。'
    else if (newStatus === 'ai_serving' && data.previous_status === 'resolved') systemMsg = '已恢复 AI 服务，你可以继续提问。'
    else if (newStatus === 'closed') systemMsg = '会话已关闭。'

    if (systemMsg) {
      messages.value.push({ id: `sys-${Date.now()}`, role: 'system', content: systemMsg, timestamp: Date.now() })
      scrollToBottom()
    }
  }

  function registerWsListeners() {
    wsManager.on('new_message', onNewMessage)
    wsManager.on('status_changed', onStatusChanged)
    centrifugeManager.on('new_message', onNewMessage)
    centrifugeManager.on('status_changed', onStatusChanged)
  }

  function unregisterWsListeners() {
    wsManager.off('new_message', onNewMessage)
    wsManager.off('status_changed', onStatusChanged)
    centrifugeManager.off('new_message', onNewMessage)
    centrifugeManager.off('status_changed', onStatusChanged)
  }

  async function loadHistory() {
    if (!conversationId.value) return
    try {
      const res = await getMessages(conversationId.value)
      messages.value = res.items.map(mapServerMessage)
      scrollToBottom()
    } catch (e) {
      console.error('加载消息失败:', e)
    }
  }

  async function loadConversation() {
    if (!conversationId.value) return
    try {
      const conv = await getConversation(conversationId.value)
      conversationStatus.value = (conv.status as ConversationStatus) || 'ai_serving'
      await loadHistory()
      wsManager.send({ type: 'join_room', data: { conv_id: conversationId.value } })
      centrifugeManager.joinConversation(conversationId.value)
    } catch (e) {
      console.error('加载会话失败:', e)
    }
  }

  function onUnansweredCardClosed(msg: ChatMessage, submitted: boolean) {
    void submitted
    if (msg.unanswered_invite) {
      msg.unanswered_invite.dismissed = true
      const id = msg.unanswered_invite.message_id
      if (typeof id === 'number' && id > 0) {
        saveDismissedId(id)
      }
    }
  }

  async function sendToTeacher(content: string) {
    try {
      await request({
        url: '/api/chat/send',
        method: 'POST',
        data: { conv_id: conversationId.value, content },
      })
    } catch (e: any) {
      console.error('发送消息失败:', e)
      uni.showToast({ title: '发送失败', icon: 'none' })
    }
  }

  async function streamResponse(userContent: string) {
    isStreaming.value = true
    isTyping.value = true

    const aiMessage: ChatMessage = {
      id: `assistant-${Date.now()}`,
      role: 'assistant',
      content: '',
      sources: [],
      timestamp: Date.now(),
      isStreaming: true,
    }

    try {
      await new Promise(r => setTimeout(r, 300))
      isTyping.value = false
      messages.value.push(aiMessage)
      scrollToBottom()

      const getReactive = () => messages.value.find(m => m.id === aiMessage.id) || aiMessage

      await fetchSSE(
        '/api/chat/send',
        { conv_id: conversationId.value, content: userContent },
        userStore.token,
        {
          onToken: (token: string) => {
            getReactive().content += token
            scrollToBottom()
          },
          onEnd: (data) => {
            const msg = getReactive()
            if (data.message_id) {
              msg.id = String(data.message_id)
            }
            msg.content = data.full_content || msg.content
            msg.sources = data.sources || []
            msg.isStreaming = false
            trackEvent('chat_response_ok', {
              conv_id: conversationId.value,
              message_id: data.message_id,
              content_length: (data.full_content || '').length,
              sources_count: (data.sources || []).length,
            })
            scrollToBottom()
          },
          onUnansweredInvite: ({ message_id, conv_id }) => {
            const dismissed = loadDismissedSet()
            if (dismissed.has(message_id)) return

            const target =
              messages.value.find(message => message.id === String(message_id)) ||
              messages.value.find(message => message.id === aiMessage.id) ||
              getReactive()

            if (target) {
              target.unanswered_invite = {
                message_id,
                conv_id,
                dismissed: false,
              }
            }

            trackEvent('unanswered_card_shown', { conv_id, message_id })
          },
          onSuggestions: (questions: string[]) => {
            suggestedQuestions.value = questions
            scrollToBottom()
          },
          onError: (errMsg: string) => {
            getReactive().content = errMsg || '抱歉，AI 服务暂时不可用。'
            getReactive().isStreaming = false
            trackEvent('chat_response_error', {
              conv_id: conversationId.value,
              error_msg: (errMsg || '').slice(0, 200),
            })
            scrollToBottom()
          },
        }
      )
    } catch (e: any) {
      console.error('Stream error:', e)
      isTyping.value = false
      const msg = messages.value.find(m => m.id === aiMessage.id)
      if (msg) {
        msg.content = '抱歉，AI 服务暂时不可用，请稍后重试。'
        msg.isStreaming = false
      }
      scrollToBottom()
      trackEvent('chat_response_error', {
        conv_id: conversationId.value,
        error_msg: String(e?.message || e || '').slice(0, 200),
      })
    } finally {
      isStreaming.value = false
      isTyping.value = false
      nextTick(() => consumeInitQuery())
    }
  }

  async function sendMessage() {
    const content = inputMessage.value.trim()
    if (!content || isStreaming.value) return

    if (!conversationId.value) {
      try {
        const conv = await createConversation(content.slice(0, 20))
        conversationId.value = conv.id
        conversationStatus.value = 'ai_serving'
        wsManager.send({ type: 'join_room', data: { conv_id: conv.id } })
        centrifugeManager.joinConversation(conv.id)
      } catch (e) {
        console.error('创建会话失败:', e)
        uni.showToast({ title: '创建会话失败', icon: 'none' })
        return
      }
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      timestamp: Date.now(),
    }
    suggestedQuestions.value = []
    messages.value.push(userMessage)
    inputMessage.value = ''
    scrollToBottom()
    trackEvent('chat_send', {
      conv_id: conversationId.value,
      content_length: content.length,
    })

    if (conversationStatus.value === 'teacher_serving' || conversationStatus.value === 'pending_teacher') {
      await sendToTeacher(content)
    } else {
      await streamResponse(content)
    }
  }

  function handleSourceClick(source: Source) {
    sourcePopup.title = source.title || '参考资料'
    sourcePopup.content = source.content || '暂无详细内容'
    sourceSheetHeight.value = 50
    trackEvent('kb_doc_clicked', {
      conv_id: conversationId.value,
      source_title: source.title || '',
    })
    sourcePopup.visible = true
  }

  function closeSourcePopup() {
    sourcePopup.visible = false
  }

  function onSheetTouchStart(e: TouchEvent) {
    sheetTouchStartY = e.touches[0].clientY
    sheetHeightAtStart = sourceSheetHeight.value
  }

  function onSheetTouchMove(e: TouchEvent) {
    const dy = sheetTouchStartY - e.touches[0].clientY
    const dvh = (dy / getViewportHeight()) * 100
    sourceSheetHeight.value = Math.min(95, Math.max(30, sheetHeightAtStart + dvh))
  }

  function onSheetTouchEnd() {
    if (sourceSheetHeight.value > 75) sourceSheetHeight.value = 95
    else if (sourceSheetHeight.value < 35) closeSourcePopup()
    else sourceSheetHeight.value = 50
  }

  function handleSuggestionClick(question: string) {
    inputMessage.value = question
    nextTick(() => sendMessage())
  }

  function onSendLongPress() {
    if (!conversationId.value || conversationStatus.value !== 'ai_serving') return
    showCallMenu.value = true
  }

  async function handleCallTeacher() {
    showCallMenu.value = false
    if (escalateLoading.value || conversationStatus.value !== 'ai_serving') return
    if (!conversationId.value) return

    escalateLoading.value = true
    try {
      await escalate(conversationId.value)
      conversationStatus.value = 'pending_teacher'
      messages.value.push({
        id: `sys-escalate-${Date.now()}`,
        role: 'system',
        content: '已提交人工服务请求，请耐心等待回复。',
        timestamp: Date.now(),
      })
      scrollToBottom()
      uni.showToast({ title: '已提交人工请求', icon: 'success' })
    } catch (e: any) {
      console.error('呼叫老师失败:', e)
      uni.showToast({ title: e?.message || '呼叫失败', icon: 'none' })
    } finally {
      escalateLoading.value = false
    }
  }

  function goBack() { uni.navigateBack() }
  function goToHistory() { uni.navigateTo({ url: '/pages/chat/history' }) }

  function consumeInitQuery() {
    if (isStreaming.value) return
    const initQuery = uni.getStorageSync('chat_init_query')
    if (initQuery) {
      uni.removeStorageSync('chat_init_query')
      inputMessage.value = String(initQuery)
      nextTick(() => sendMessage())
    }
  }

  onMounted(() => {
    consumeInitQuery()
  })

  onShow(() => {
    trackEvent('page_view', { path: '/pages/chat/index' })
    consumeInitQuery()
    const pendingId = uni.getStorageSync('pendingConversationId')
    if (pendingId) {
      uni.removeStorageSync('pendingConversationId')
      const newId = Number(pendingId)
      if (newId !== conversationId.value) {
        messages.value = []
        conversationStatus.value = 'ai_serving'
      }
      conversationId.value = newId
      loadConversation()
    }
    registerWsListeners()
    if (conversationId.value) {
      wsManager.send({ type: 'join_room', data: { conv_id: conversationId.value } })
      centrifugeManager.joinConversation(conversationId.value)
    }
  })

  onHide(() => {
    if (conversationId.value) {
      wsManager.send({ type: 'leave_room', data: { conv_id: conversationId.value } })
      centrifugeManager.leaveConversation(conversationId.value)
    }
    unregisterWsListeners()
  })

  onUnmounted(() => {
    unregisterWsListeners()
  })

  return {
    messages,
    inputMessage,
    isStreaming,
    isTyping,
    scrollTop,
    conversationId,
    conversationStatus,
    escalateLoading,
    suggestedQuestions,
    showCallMenu,
    sourcePopup,
    sourceSheetHeight,
    canSend,
    inputPlaceholder,
    closeSourcePopup,
    formatTime: formatChatTime,
    goBack,
    goToHistory,
    handleCallTeacher,
    handleSourceClick,
    handleSuggestionClick,
    isRefusalMsg: isRefusalMessage,
    onSendLongPress,
    onSheetTouchEnd,
    onSheetTouchMove,
    onSheetTouchStart,
    onUnansweredCardClosed,
    sendMessage,
  }
}
