<template>
  <view class="chat-page">
    <view class="top-nav">
      <view class="nav-left" @click="goBack">
        <text class="material-symbols-outlined nav-back-icon">arrow_back</text>
        <text class="nav-title">医小管</text>
      </view>
      <view class="nav-right" @click="goToHistory">
        <text class="material-symbols-outlined nav-history-icon">history</text>
      </view>
    </view>

    <!-- 欢迎空状态 -->
    <view v-if="!messages.length" class="welcome-center">
      <view class="welcome-content">
        <view class="empty-icon">
          <text class="material-symbols-outlined empty-sparkle-icon">auto_awesome</text>
        </view>
        <text class="empty-title">智慧校园助理</text>
        <text class="empty-desc">同学你好！关于校园生活、选课安排或办事流程，你都可以问我。</text>
      </view>
      <view class="welcome-input-area">
        <view class="input-wrapper">
          <input
            v-model="inputMessage"
            class="input"
            placeholder="输入你的问题..."
            confirm-type="send"
            @confirm="sendMessage"
          />
          <view :class="['send-btn', { disabled: !canSend }]" @click="sendMessage">
            <text class="material-symbols-outlined send-icon">send</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 聊天消息列表 -->
    <template v-else>
      <scroll-view
        class="chat-container"
        scroll-y
        :scroll-top="scrollTop"
        :scroll-into-view="scrollAnchor"
        :scroll-with-animation="true"
      >
        <view
          v-for="msg in messages"
          :key="msg.id"
          class="msg-wrapper"
          :class="{ 'msg-animate': animateMessages }"
        >
          <!-- 用户消息 -->
          <view v-if="msg.role === 'user'" class="user-msg">
            <view class="msg-bubble user-bubble">
              <text>{{ msg.content }}</text>
            </view>
            <text class="msg-time">{{ formatTime(msg.timestamp) }}</text>
          </view>

          <!-- system 消息 -->
          <view v-else-if="msg.role === 'system'" class="system-message">
            <text>{{ msg.content }}</text>
          </view>

          <!-- teacher 消息 -->
          <view v-else-if="msg.role === 'teacher'" class="ai-msg">
            <view class="ai-header">
              <view class="teacher-avatar">
                <text class="material-symbols-outlined teacher-icon">support_agent</text>
              </view>
              <text class="teacher-name">老师回复</text>
            </view>
            <view class="msg-bubble teacher-bubble">
              <view class="markdown-body" v-html="renderMarkdown(msg.content)" />
            </view>
            <text class="msg-time">{{ formatTime(msg.timestamp) }}</text>
          </view>

          <!-- AI 消息 -->
          <view v-else-if="msg.role === 'assistant'" class="ai-msg">
            <view class="ai-header">
              <view class="ai-avatar">
                <text class="material-symbols-outlined bot-icon">smart_toy</text>
              </view>
              <text class="ai-name">MEDICAL ASSISTANT</text>
            </view>
            <view class="msg-bubble ai-bubble">
              <!-- 等待中动画 -->
              <view v-if="msg.isStreaming && !msg.content" class="typing-animation">
                <view class="dot" /><view class="dot" /><view class="dot" />
              </view>
              <!-- Markdown 渲染 -->
              <view v-else class="markdown-body" v-html="renderMarkdown(msg.content)" />
              <!-- 流式光标 -->
              <text v-if="msg.isStreaming && msg.content" class="cursor">|</text>
              <!-- 来源引用 -->
              <view v-if="msg.sources && msg.sources.length && !msg.isStreaming" class="citations">
                <view class="cit-header">
                  <text class="material-symbols-outlined book-icon">menu_book</text>
                  <text>参考资料</text>
                </view>
                <view class="cit-list">
                  <view
                    v-for="(source, si) in msg.sources"
                    :key="si"
                    class="cit-item"
                    @click="handleSourceClick(source)"
                  >
                    <text class="cit-text">{{ si + 1 }}. {{ source.title }}</text>
                    <text class="material-symbols-outlined ext-link-icon">open_in_new</text>
                  </view>
                </view>
              </view>
            </view>
            <text class="msg-time">{{ formatTime(msg.timestamp) }}</text>
            <!-- 拒答时显示内联呼叫老师按钮 -->
            <UnansweredInviteCard
              v-if="msg.unanswered_invite && !msg.unanswered_invite.dismissed"
              :conv_id="msg.unanswered_invite.conv_id"
              :message_id="msg.unanswered_invite.message_id"
              @submitted="onUnansweredCardClosed(msg, true)"
              @dismissed="onUnansweredCardClosed(msg, false)"
            />
            <view
              v-if="!msg.isStreaming && isRefusalMsg(msg) && conversationStatus === 'ai_serving'"
              class="inline-call-teacher"
              @click="handleCallTeacher"
            >
              <text class="material-symbols-outlined call-inline-icon">support_agent</text>
              <text class="call-inline-text">{{ escalateLoading ? '呼叫中...' : '转人工服务' }}</text>
            </view>
            <view v-if="conversationStatus === 'pending_teacher' && isRefusalMsg(msg)" class="inline-call-done">
              <text class="material-symbols-outlined call-done-icon">check_circle</text>
              <text class="call-done-text">已通知老师，请耐心等待</text>
            </view>
          </view>
        </view>

        <!-- AI 思考中 -->
        <view v-if="isTyping" class="msg-wrapper">
          <view class="ai-msg">
            <view class="ai-header">
              <view class="ai-avatar">
                <text class="material-symbols-outlined bot-icon">smart_toy</text>
              </view>
              <text class="ai-name">MEDICAL ASSISTANT</text>
            </view>
            <view class="msg-bubble ai-bubble">
              <view class="typing-animation">
                <view class="dot" /><view class="dot" /><view class="dot" />
              </view>
            </view>
          </view>
        </view>

        <!-- R10: 关联问题推荐 -->
        <view v-if="suggestedQuestions.length && !isStreaming" class="suggestions-area">
          <view class="suggestions-header">
            <text class="material-symbols-outlined suggestions-icon">lightbulb</text>
            <text class="suggestions-title">你可能还想问</text>
          </view>
          <view class="suggestions-list">
            <view
              v-for="(q, qi) in suggestedQuestions"
              :key="qi"
              class="suggestion-chip"
              @click="handleSuggestionClick(q)"
            >
              <text class="suggestion-text">{{ q }}</text>
              <text class="material-symbols-outlined suggestion-arrow">arrow_forward</text>
            </view>
          </view>
        </view>

        <view id="chat-bottom-sentinel" class="bottom-spacer" />
      </scroll-view>

      <!-- 底部输入区 -->
      <view class="bottom-area">
        <view v-if="showCallMenu" class="call-menu-overlay" @click="showCallMenu = false">
          <view class="call-menu" @click.stop>
            <view class="call-menu-item" @click="handleCallTeacher">
              <text class="material-symbols-outlined call-menu-icon">call</text>
              <text class="call-menu-text">呼叫老师</text>
            </view>
          </view>
        </view>
        <view class="input-wrapper">
          <input
            v-model="inputMessage"
            class="input"
            :placeholder="inputPlaceholder"
            :disabled="isStreaming"
            confirm-type="send"
            @confirm="sendMessage"
          />
          <view
            :class="['send-btn', { disabled: !canSend }]"
            @click="sendMessage"
            @longpress="onSendLongPress"
          >
            <text class="material-symbols-outlined send-icon">send</text>
          </view>
        </view>
      </view>
    </template>

    <CustomTabBar current="assistant" />

    <!-- 来源弹层 (可拖拽全屏) -->
    <view v-if="sourcePopup.visible" class="source-overlay" @click="closeSourcePopup">
      <view
        class="source-popup"
        :style="{ height: sourceSheetHeight + 'vh' }"
        @click.stop
        @touchstart="onSheetTouchStart"
        @touchmove="onSheetTouchMove"
        @touchend="onSheetTouchEnd"
      >
        <view class="source-popup-drag-bar">
          <view class="drag-indicator" />
        </view>
        <view class="source-popup-header">
          <text class="source-popup-title">{{ sourcePopup.title }}</text>
          <view class="source-header-actions">
            <text
              v-if="sourceSheetHeight < 95"
              class="material-symbols-outlined source-expand"
              @click="sourceSheetHeight = 95"
            >open_in_full</text>
            <text
              v-else
              class="material-symbols-outlined source-expand"
              @click="sourceSheetHeight = 50"
            >close_fullscreen</text>
            <text class="material-symbols-outlined source-close" @click="closeSourcePopup">close</text>
          </view>
        </view>
        <scroll-view class="source-popup-body" scroll-y>
          <view class="markdown-body source-markdown" v-html="renderMarkdown(sourcePopup.content)" />
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onUnmounted, reactive } from 'vue'
import { onShow, onHide } from '@dcloudio/uni-app'
import MarkdownIt from 'markdown-it'
import { useUserStore } from '@/stores/user'
import { createConversation, getConversation, getMessages, escalate } from '@/api/chat'
import { fetchSSE } from '@/utils/sse'
import { wsManager } from '@/utils/websocket'
import { centrifugeManager } from '@/utils/centrifuge'
import CustomTabBar from '@/components/CustomTabBar.vue'
import UnansweredInviteCard from '@/components/UnansweredInviteCard.vue'
import { trackEvent } from '@/utils/track'
import type { Message as BaseMessage, Source, ConversationStatus, MessageResponse } from '@/types/chat'

const userStore = useUserStore()

interface UnansweredInviteState {
  message_id: number
  conv_id: number
  dismissed: boolean
}

type ChatMessage = BaseMessage & {
  unanswered_invite?: UnansweredInviteState
}

// ============ Markdown 渲染器 ============
const md = new MarkdownIt({ html: true, linkify: true, typographer: true })
function renderMarkdown(content: string): string {
  if (!content) return ''
  return md.render(content)
}

// ============ 响应式状态 ============
const messages = ref<ChatMessage[]>([])
const inputMessage = ref('')
const isStreaming = ref(false)
const isTyping = ref(false)
const scrollTop = ref(0)
const scrollAnchor = ref('')
// 控制新消息入场动效：首次 mount 加载 history 时不动画（避免一次性全部淡入），
// 加载完后开启 → 之后每条新消息（push 时）的 v-for 元素 mount 都会播放动画。
const animateMessages = ref(false)
const conversationId = ref<number | null>(null)
const conversationStatus = ref<ConversationStatus>('ai_serving')
const escalateLoading = ref(false)
const suggestedQuestions = ref<string[]>([])
const showCallMenu = ref(false)
const sourcePopup = reactive({ visible: false, title: '', content: '' })
const sourceSheetHeight = ref(50)
const DISMISSED_KEY = 'dismissed_unanswered_msg_ids'
let sheetTouchStartY = 0
let sheetHeightAtStart = 50

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
    // silent
  }
}

// ============ 计算属性 ============
const canSend = computed(() => inputMessage.value.trim().length > 0 && !isStreaming.value)

const inputPlaceholder = computed(() => {
  if (conversationStatus.value === 'teacher_serving') return '发送消息给老师...'
  if (conversationStatus.value === 'pending_teacher') return '等待老师接入...'
  return '输入你的问题...'
})

// ============ 生命周期 ============
onMounted(() => {
  const initQuery = uni.getStorageSync('chat_init_query')
  if (initQuery) {
    uni.removeStorageSync('chat_init_query')
    inputMessage.value = initQuery
    nextTick(() => sendMessage())
  }
})

onShow(() => {
  trackEvent('page_view', { path: '/pages/chat/index' })
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

// ============ WebSocket 监听 ============
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
  // 直接订阅 uni 全局事件总线（store 层在 _attachGlobalListeners 已对 wsManager / centrifugeManager
  // 做了一次性挂载 + 去重转发）。这样无论后端推送走 conv:{id} 还是 user#{student_id} 频道，
  // chat 页都能收到，且不会重复触发。
  uni.$on('rt:new_message', onNewMessage)
  uni.$on('rt:status_changed', onStatusChanged)
}
function unregisterWsListeners() {
  uni.$off('rt:new_message', onNewMessage)
  uni.$off('rt:status_changed', onStatusChanged)
}

// ============ 加载会话 ============
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

async function loadHistory() {
  if (!conversationId.value) return
  try {
    const res = await getMessages(conversationId.value)
    messages.value = res.items.map(mapServerMessage)
    scrollToBottom()
    // history 加载完成 → 之后任何 push 进来的新消息都会触发入场动效
    // 双 nextTick 保证首批 history v-for 元素的 mount 阶段都没有 msg-animate class
    nextTick(() => nextTick(() => { animateMessages.value = true }))
  } catch (e) {
    console.error('加载消息失败:', e)
  }
}

function mapServerMessage(m: MessageResponse): ChatMessage {
  const roleMap: Record<string, BaseMessage['role']> = {
    student: 'user', ai: 'assistant', teacher: 'teacher', system: 'system',
  }
  return {
    id: String(m.id),
    role: roleMap[m.sender_type] || 'system',
    content: m.content || '',
    sources: m.metadata_?.sources || [],
    timestamp: m.created_at ? new Date(m.created_at).getTime() : Date.now(),
  }
}

// ============ 导航 ============
function goBack() { uni.navigateBack() }
function goToHistory() { uni.navigateTo({ url: '/pages/chat/history' }) }

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

// ============ 发送消息 ============
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

// ============ teacher_serving: JSON 发送 ============
async function sendToTeacher(content: string) {
  try {
    const resp = await fetch('/api/chat/send', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userStore.token}`,
      },
      body: JSON.stringify({ conv_id: conversationId.value, content }),
    })
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`)
    // JSON response — message already persisted server-side
  } catch (e: any) {
    console.error('发送消息失败:', e)
    uni.showToast({ title: '发送失败', icon: 'none' })
  }
}

// ============ ai_serving: SSE 流式响应 ============
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
          if (dismissed.has(message_id)) {
            return
          }

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
  }
}

// ============ 来源点击 — 弹层展示 ============
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
  const dvh = (dy / window.innerHeight) * 100
  sourceSheetHeight.value = Math.min(95, Math.max(30, sheetHeightAtStart + dvh))
}
function onSheetTouchEnd() {
  if (sourceSheetHeight.value > 75) sourceSheetHeight.value = 95
  else if (sourceSheetHeight.value < 35) closeSourcePopup()
  else sourceSheetHeight.value = 50
}

// ============ 拒答检测 ============
const REFUSAL_KEYWORDS = [
  '尚未学习到', '请咨询您的辅导员', '无法回答', '暂时无法',
  '超出了我的知识范围', '建议您直接咨询', '暂时不可用', '请稍后重试',
  '无法为您提供', '没有找到相关', '不在我的服务范围',
  '转人工请求', '转接人工客服', '转人工服务', '转接人工',
]
function isRefusalMsg(msg: BaseMessage): boolean {
  if (msg.role !== 'assistant' || !msg.content) return false
  if (REFUSAL_KEYWORDS.some(kw => msg.content.includes(kw))) return true
  if (msg.content.includes('抱歉') && (!msg.sources || msg.sources.length === 0)) return true
  return false
}

// ============ R10: 推荐问题点击 ============
function handleSuggestionClick(question: string) {
  inputMessage.value = question
  nextTick(() => sendMessage())
}

// ============ 长按弹出 ============
function onSendLongPress() {
  if (!conversationId.value || conversationStatus.value !== 'ai_serving') return
  showCallMenu.value = true
}

// ============ 呼叫老师 ============
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
      content: '已通知老师，请耐心等待回复。',
      timestamp: Date.now(),
    })
    scrollToBottom()
    uni.showToast({ title: '已呼叫老师', icon: 'success' })
  } catch (e: any) {
    console.error('呼叫老师失败:', e)
    uni.showToast({ title: e?.message || '呼叫失败', icon: 'none' })
  } finally {
    escalateLoading.value = false
  }
}

// ============ 工具函数 ============
function formatTime(timestamp: number): string {
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

function scrollToBottom() {
  // 用 scroll-into-view + sentinel 比 scroll-top hack 更可靠；
  // 双 nextTick 让 DOM patch + layout 完成；
  // anchor 先清空再 set，保证 prop watcher 一定被触发（uni-app scroll-view 同值不触发）。
  nextTick(() => {
    scrollAnchor.value = ''
    nextTick(() => {
      scrollAnchor.value = 'chat-bottom-sentinel'
      // H5 双保险：直接对真 DOM 调 scrollIntoView（小程序时 document 不存在自然走 scroll-view 路径）
      if (typeof document !== 'undefined') {
        requestAnimationFrame(() => {
          const anchor = document.querySelector('#chat-bottom-sentinel') as HTMLElement | null
          if (anchor && typeof anchor.scrollIntoView === 'function') {
            try { anchor.scrollIntoView({ behavior: 'smooth', block: 'end' }) } catch { /* IE11+ has no options support */ anchor.scrollIntoView(false) }
          }
        })
      } else {
        // 非 H5 兜底：保留 scroll-top hack
        scrollTop.value = 9999999 + Math.random() * 1000
      }
    })
  })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.chat-page { display: flex; flex-direction: column; height: 100vh; background: $surface; }

.top-nav { display: flex; justify-content: space-between; align-items: center; padding: calc(env(safe-area-inset-top) + 1rem) 1.5rem 1rem; background: rgba(250,245,251,0.80); backdrop-filter: blur(20px) saturate(180%); -webkit-backdrop-filter: blur(20px) saturate(180%); z-index: 50; }
.nav-left { display: flex; align-items: center; gap: 0.75rem; }
.nav-title { font-size: 1.25rem; font-weight: 700; color: #5b21b6; }
.nav-back-icon, .nav-history-icon { font-size: 1.5rem; color: #5b21b6; }

.welcome-center { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 1.5rem; padding-bottom: calc(var(--tabbar-safe) + 2rem); }
.welcome-content { display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 2.5rem; }
.welcome-input-area { width: 100%; max-width: 20rem; }
.empty-icon { width: 3.75rem; height: 3.75rem; background: linear-gradient(135deg, #5b21b6, #b28cff); border-radius: 1.875rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1.25rem; box-shadow: 0 0.5rem 1.5rem rgba(91,33,182,0.20); }
.empty-sparkle-icon { font-size: 1.75rem; color: #fff; }
.empty-title { font-size: 1.5rem; font-weight: 800; color: #2f2e32; margin-bottom: 0.625rem; }
.empty-desc { font-size: 0.875rem; color: #64748b; line-height: 1.7; max-width: 16.25rem; }

.chat-container { flex: 1; padding: 0 1rem; box-sizing: border-box; }
.msg-wrapper { display: flex; flex-direction: column; margin-bottom: 1.5rem; }

// 新消息入场动效：history 加载阶段不带 .msg-animate，避免一次性全部淡入；
// loadHistory 完成后开启，之后每条 push 的新消息（v-for mount 时）都会 fadeUp 一次。
.msg-wrapper.msg-animate {
  animation: msgFadeUp 320ms cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes msgFadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to   { opacity: 1; transform: translateY(0); }
}

.user-msg { align-items: flex-end; }
.user-bubble { background: linear-gradient(135deg, #5b21b6, #b28cff); color: #fff; border-radius: 1rem 1rem 0 1rem; max-width: 85%; padding: 1rem 1.25rem; box-shadow: 0 0.5rem 1rem rgba(91,33,182,0.10); font-size: 0.9375rem; line-height: 1.7; }
.msg-time { font-size: 0.6875rem; font-weight: 700; color: #94a3b8; margin-top: 0.5rem; padding: 0 0.5rem; }

.ai-msg { align-items: flex-start; }
.ai-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; padding: 0 0.5rem; }
.ai-avatar { width: 1.5rem; height: 1.5rem; border-radius: 0.75rem; background: linear-gradient(135deg, #5b21b6, #b28cff); display: flex; align-items: center; justify-content: center; }
.bot-icon { font-size: 0.875rem; color: #fff; }
.ai-name { font-size: 0.75rem; font-weight: 700; color: #5b21b6; letter-spacing: 0.0625rem; }
.ai-bubble { background: #ffffff; color: #2f2e32; border-radius: 1rem 1rem 1rem 0; max-width: 90%; padding: 1.25rem 1.5rem; box-shadow: 0 0.125rem 0.5rem rgba(0,0,0,0.02); border-left: 0.25rem solid #5b21b6; font-size: 0.9375rem; line-height: 1.7; }

.teacher-avatar { width: 1.5rem; height: 1.5rem; border-radius: 0.75rem; background: linear-gradient(135deg, #059669, #34d399); display: flex; align-items: center; justify-content: center; }
.teacher-icon { font-size: 0.875rem; color: #fff; }
.teacher-name { font-size: 0.75rem; font-weight: 700; color: #059669; letter-spacing: 0.0625rem; }
.teacher-bubble { background: #ffffff; color: #2f2e32; border-radius: 1rem 1rem 1rem 0; max-width: 90%; padding: 1.25rem 1.5rem; box-shadow: 0 0.125rem 0.5rem rgba(0,0,0,0.02); border-left: 0.25rem solid #059669; font-size: 0.9375rem; line-height: 1.7; }

.citations { margin-top: 1rem; padding: 0.75rem; background: #f4eff5; border-radius: 0.5rem; }
.cit-header { display: flex; align-items: center; gap: 0.25rem; margin-bottom: 0.5rem; color: #5b21b6; font-size: 0.75rem; font-weight: 700; }
.book-icon { font-size: 0.875rem; color: #5b21b6; }
.cit-list { display: flex; flex-direction: column; gap: 0.5rem; }
.cit-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.5); border-radius: 0.25rem; font-size: 0.75rem; color: #7742a6; text-decoration: underline; }
.cit-text { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-right: 0.5rem; }
.ext-link-icon { font-size: 0.75rem; color: #7742a6; }

.typing-animation { display: flex; gap: 0.25rem; padding: 0.25rem 0; }
.dot { width: 0.375rem; height: 0.375rem; background: #5b21b6; border-radius: 50%; animation: typing 1.4s infinite ease-in-out; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.cursor { display: inline-block; color: #5b21b6; animation: blink 1s infinite; margin-left: 0.125rem; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }

/* 预留 input-bar 自身 ~5.5rem (padding 1.5 + input-wrapper ~3.625 + 安全余量) + tab bar(var) 的滚动空间 */
.bottom-spacer { height: calc(var(--tabbar-safe) + 5.5rem); }

/* input bar 停在 tab bar 正上方 — 通过 var(--tabbar-safe) 消费 tokens.scss
   的单一源, 不再硬编码 3.5rem 这类会脱节的值 */
.bottom-area {
  position: fixed;
  bottom: var(--tabbar-safe);
  left: 0;
  right: 0;
  z-index: 40;
  background: rgba(250, 245, 251, 0.80);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  padding: 0.75rem 1rem;
}
.call-menu-overlay { position: absolute; bottom: 100%; left: 0; right: 0; display: flex; justify-content: flex-end; padding: 0 1rem 0.5rem; z-index: 50; }
.call-menu { background: #fff; border-radius: 0.75rem; box-shadow: 0 0.25rem 1.5rem rgba(0,0,0,0.12); overflow: hidden; min-width: 8rem; }
.call-menu-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; }
.call-menu-item:active { background: #f4eff5; }
.call-menu-icon { font-size: 1.125rem; color: #5b21b6; }
.call-menu-text { font-size: 0.875rem; font-weight: 600; color: #2f2e32; }

.system-message { display: flex; justify-content: center; padding: 0.5rem 0; font-size: 0.75rem; color: #94a3b8; font-style: italic; }

.input-wrapper { display: flex; align-items: center; gap: 0.5rem; background: #e5e1e8; border-radius: 1.5rem; padding: 0.375rem 0.375rem 0.375rem 1rem; }
.input { flex: 1; background: transparent; border: none; font-size: 0.875rem; color: #2f2e32; }
.send-btn { width: 2.5rem; height: 2.5rem; border-radius: 1.25rem; background: linear-gradient(135deg, #5b21b6, #b28cff); display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.send-btn.disabled { opacity: 0.5; }
.send-icon { font-size: 1.25rem; color: #fff; }

.markdown-body { font-size: 0.875rem; line-height: 1.6; }
.markdown-body :deep(p) { margin-bottom: 0.5rem; }
.markdown-body :deep(ul) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: disc; }
.markdown-body :deep(ol) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: decimal; }
.markdown-body :deep(li) { margin-bottom: 0.25rem; }
.markdown-body :deep(strong) { font-weight: 700; color: #5b21b6; }

.inline-call-teacher { display: inline-flex; align-items: center; gap: 0.375rem; margin-top: 0.75rem; padding: 0.5rem 1rem; background: linear-gradient(135deg, #5b21b6, #b28cff); color: #fff; border-radius: 1.5rem; transition: all 0.2s; box-shadow: 0 0.25rem 0.75rem rgba(91,33,182,0.25); }
.inline-call-teacher:active { transform: scale(0.95); opacity: 0.9; }
.call-inline-icon { font-size: 1.125rem; color: #fff; }
.call-inline-text { font-size: 0.8125rem; font-weight: 700; color: #fff; }
.inline-call-done { display: inline-flex; align-items: center; gap: 0.375rem; margin-top: 0.75rem; padding: 0.5rem 1rem; background: rgba(30,200,60,0.1); border-radius: 1.5rem; }
.call-done-icon { font-size: 1.125rem; color: #1e8e3e; }
.call-done-text { font-size: 0.8125rem; font-weight: 700; color: #1e8e3e; }

/* R10: 关联问题推荐 */
.suggestions-area { padding: 0 0.5rem; margin-bottom: 1.5rem; }
.suggestions-header { display: flex; align-items: center; gap: 0.375rem; margin-bottom: 0.625rem; padding: 0 0.25rem; }
.suggestions-icon { font-size: 1rem; color: #f59e0b; }
.suggestions-title { font-size: 0.75rem; font-weight: 700; color: #92400e; }
.suggestions-list { display: flex; flex-direction: column; gap: 0.5rem; }
.suggestion-chip { display: flex; align-items: center; justify-content: space-between; padding: 0.75rem 1rem; background: rgba(91,33,182,0.05); border-radius: 9999px; transition: all 0.2s; } /* No-Line: 去掉 1px solid border, 用 primary/5 tonal tint 替代 */
.suggestion-chip:active { background: rgba(91,33,182,0.10); transform: scale(0.98); }
.suggestion-text { flex: 1; font-size: 0.8125rem; font-weight: 700; color: #5b21b6; line-height: 1.5; }
.suggestion-arrow { font-size: 0.875rem; color: #5b21b6; margin-left: 0.5rem; flex-shrink: 0; opacity: 0.6; }

/* 来源弹层 (可拖拽全屏) */
.source-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.45); z-index: 1000; display: flex; align-items: flex-end; justify-content: center; }
.source-popup { width: 100%; max-width: 30rem; background: #fff; border-radius: 1rem 1rem 0 0; display: flex; flex-direction: column; transition: height 0.15s ease-out; }
.source-popup-drag-bar { display: flex; justify-content: center; padding: 0.5rem 0 0.25rem; cursor: grab; }
.drag-indicator { width: 2rem; height: 0.25rem; border-radius: 0.125rem; background: #d1d5db; }
.source-popup-header { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 1.25rem 0.75rem; } /* No-Line: 去掉 border-bottom 1px solid */
.source-popup-title { font-size: 1rem; font-weight: 700; color: #2f2e32; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-header-actions { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }
.source-expand { font-size: 1.125rem; color: #94a3b8; }
.source-close { font-size: 1.25rem; color: #94a3b8; }
.source-popup-body { padding: 1.25rem; flex: 1; overflow: hidden; }
.source-markdown { font-size: 0.875rem; color: #475569; line-height: 1.8; }
.source-markdown :deep(p) { margin-bottom: 0.5rem; }
.source-markdown :deep(ul) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: disc; }
.source-markdown :deep(ol) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: decimal; }
.source-markdown :deep(li) { margin-bottom: 0.25rem; }
.source-markdown :deep(strong) { font-weight: 700; color: #5b21b6; }
.source-markdown :deep(code) { background: #f3f4f6; padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-size: 0.8125rem; }
.source-markdown :deep(pre) { background: #f3f4f6; padding: 0.75rem; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 0.5rem; }
.source-markdown :deep(a) { color: #5b21b6; text-decoration: underline; }
.source-markdown :deep(h1), .source-markdown :deep(h2), .source-markdown :deep(h3) { font-weight: 700; color: #2f2e32; margin: 0.75rem 0 0.375rem; }
.source-markdown :deep(blockquote) { border-left: 3px solid #5b21b6; padding-left: 0.75rem; color: #6b7280; margin: 0.5rem 0; }
.source-markdown :deep(table) { width: 100%; border-collapse: collapse; margin-bottom: 0.5rem; font-size: 0.8125rem; }
.source-markdown :deep(th), .source-markdown :deep(td) { border: 1px solid #e5e7eb; padding: 0.375rem 0.5rem; text-align: left; }
</style>
