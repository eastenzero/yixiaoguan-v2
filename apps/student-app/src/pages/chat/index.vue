<template>
  <view class="chat-page">
    <TopAppBar
      title="智能助理"
      action-icon="history"
      @action="goToHistory"
    />

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
        :scroll-with-animation="true"
      >
        <view
          v-for="msg in messages"
          :key="msg.id"
          class="msg-wrapper"
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
              <view v-if="msg.isStreaming && !msg.content" class="typing-dots">
                <view class="dot" /><view class="dot" /><view class="dot" />
              </view>
              <!-- Markdown 渲染 -->
              <view v-else class="markdown-body" v-html="renderMarkdown(msg.content)" />
              <!-- 流式光标 -->
              <text v-if="msg.isStreaming && msg.content" class="blink-cursor">|</text>
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
              <view class="typing-dots">
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

        <view class="bottom-spacer" />
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
          <view class="markdown-body markdown-body--rich" v-html="renderMarkdown(sourcePopup.content)" />
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
import CustomTabBar from '@/components/CustomTabBar.vue'
import TopAppBar from '@/components/TopAppBar.vue'
import type { Message, Source, ConversationStatus, MessageResponse } from '@/types/chat'

const userStore = useUserStore()

// ============ Markdown 渲染器 ============
const md = new MarkdownIt({ html: true, linkify: true, typographer: true })
function renderMarkdown(content: string): string {
  if (!content) return ''
  return md.render(content)
}

// ============ 响应式状态 ============
const messages = ref<Message[]>([])
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
  }
})

onHide(() => {
  if (conversationId.value) {
    wsManager.send({ type: 'leave_room', data: { conv_id: conversationId.value } })
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
  wsManager.on('new_message', onNewMessage)
  wsManager.on('status_changed', onStatusChanged)
}
function unregisterWsListeners() {
  wsManager.off('new_message', onNewMessage)
  wsManager.off('status_changed', onStatusChanged)
}

// ============ 加载会话 ============
async function loadConversation() {
  if (!conversationId.value) return
  try {
    const conv = await getConversation(conversationId.value)
    conversationStatus.value = (conv.status as ConversationStatus) || 'ai_serving'
    await loadHistory()
    wsManager.send({ type: 'join_room', data: { conv_id: conversationId.value } })
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
  } catch (e) {
    console.error('加载消息失败:', e)
  }
}

function mapServerMessage(m: MessageResponse): Message {
  const roleMap: Record<string, Message['role']> = {
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
function goToHistory() { uni.navigateTo({ url: '/pages/chat/history' }) }

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
    } catch (e) {
      console.error('创建会话失败:', e)
      uni.showToast({ title: '创建会话失败', icon: 'none' })
      return
    }
  }

  const userMessage: Message = {
    id: `user-${Date.now()}`,
    role: 'user',
    content,
    timestamp: Date.now(),
  }
  suggestedQuestions.value = []
  messages.value.push(userMessage)
  inputMessage.value = ''
  scrollToBottom()

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

  const aiMessage: Message = {
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
          msg.content = data.full_content || msg.content
          msg.sources = data.sources || []
          msg.isStreaming = false
          scrollToBottom()
        },
        onSuggestions: (questions: string[]) => {
          suggestedQuestions.value = questions
          scrollToBottom()
        },
        onError: (errMsg: string) => {
          getReactive().content = errMsg || '抱歉，AI 服务暂时不可用。'
          getReactive().isStreaming = false
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
function isRefusalMsg(msg: Message): boolean {
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
  nextTick(() => { scrollTop.value = 9999999 + Math.random() })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

// Layout constants synchronised with shared components
$top-bar-h: 56px;
$tab-bar-h: 64px;
$input-bar-h: 60px;

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-page;
  font-family: $font-family-sans;
  color: $text-primary;
}

// ============================================================
// Welcome empty state
// ============================================================
.welcome-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: calc(env(safe-area-inset-top) + #{$top-bar-h} + #{$space-6});
  padding-bottom: calc(env(safe-area-inset-bottom) + #{$tab-bar-h} + #{$space-12});
  padding-left: $space-6;
  padding-right: $space-6;
}

.welcome-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  margin-bottom: $space-10;
  opacity: 0;
  animation: fadeUp 0.55s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.welcome-input-area {
  width: 100%;
  max-width: 320px;
  opacity: 0;
  animation: fadeUp 0.55s cubic-bezier(0.22, 1, 0.36, 1) 0.12s forwards;
}

.empty-icon {
  position: relative;
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  border-radius: $radius-xl;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-5;
  box-shadow: 0 12px 32px -8px rgba($primary, 0.45),
              0 4px 10px -2px rgba($primary, 0.25);
  transform: rotate(-3deg);
}

.empty-icon::after {
  content: '';
  position: absolute;
  inset: -10px;
  border-radius: $radius-full;
  background: radial-gradient(circle at center, rgba($primary, 0.18) 0%, transparent 60%);
  z-index: -1;
}

.empty-sparkle-icon {
  font-size: 28px;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.empty-title {
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  color: $text-primary;
  letter-spacing: -0.01em;
  margin-bottom: $space-2;
}

.empty-desc {
  font-size: $font-size-sm;
  color: $text-secondary;
  line-height: $line-height-relaxed;
  max-width: 260px;
}

// ============================================================
// Chat container & messages
// ============================================================
.chat-container {
  flex: 1;
  padding: calc(env(safe-area-inset-top) + #{$top-bar-h} + #{$space-3}) $space-4 0;
  box-sizing: border-box;
}

.msg-wrapper {
  display: flex;
  flex-direction: column;
  margin-bottom: $space-5;
  opacity: 0;
  animation: fadeUp 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.bottom-spacer {
  height: calc(#{$tab-bar-h} + #{$input-bar-h} + #{$space-6});
}

// ── User bubble ───────────────────────────────────────
.user-msg {
  align-items: flex-end;
}

.user-bubble {
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  color: $text-inverse;
  border-radius: $radius-md $radius-md $space-1 $radius-md;
  max-width: 85%;
  padding: $space-3 $space-4;
  font-size: $font-size-sm;
  line-height: $line-height-normal;
  box-shadow: 0 6px 18px -6px rgba($primary, 0.45),
              0 2px 4px -2px rgba($primary, 0.20);
}

// ── Time stamp ────────────────────────────────────────
.msg-time {
  font-size: 11px;
  font-weight: $font-weight-semibold;
  color: $text-muted;
  margin-top: $space-1;
  padding: 0 $space-2;
}

// ── AI bubble ─────────────────────────────────────────
.ai-msg {
  align-items: flex-start;
}

.ai-header {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-2;
  padding: 0 $space-2;
}

.ai-avatar {
  width: 24px;
  height: 24px;
  border-radius: $radius-full;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba($primary, 0.30);
}

.bot-icon {
  font-size: 14px;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.ai-name {
  font-size: 11px;
  font-weight: $font-weight-bold;
  color: $primary;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.ai-bubble {
  background: $bg-card;
  color: $text-primary;
  border-radius: $radius-md $radius-md $radius-md $space-1;
  max-width: 90%;
  padding: $space-4;
  font-size: $font-size-sm;
  line-height: $line-height-normal;
  box-shadow: 0 1px 2px rgba($text-primary, 0.04),
              0 4px 16px -4px rgba($primary, 0.08);
  border: 1px solid rgba($primary, 0.06);
}

// ── Teacher bubble ────────────────────────────────────
.teacher-avatar {
  width: 24px;
  height: 24px;
  border-radius: $radius-full;
  // emerald-700 (#047857) is the canonical darker shade of $success
  // (#059669); kept inline because tokens.scss has no $success-hover.
  background: linear-gradient(135deg, $success 0%, #047857 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba($success, 0.30);
}

.teacher-icon {
  font-size: 14px;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.teacher-name {
  font-size: 11px;
  font-weight: $font-weight-bold;
  color: $success;
  letter-spacing: 0.08em;
}

.teacher-bubble {
  background: $bg-card;
  color: $text-primary;
  border-radius: $radius-md $radius-md $radius-md $space-1;
  max-width: 90%;
  padding: $space-4;
  font-size: $font-size-sm;
  line-height: $line-height-normal;
  box-shadow: 0 1px 2px rgba($text-primary, 0.04),
              0 4px 16px -4px rgba($success, 0.10);
  border: 1px solid rgba($success, 0.10);
}

// ── Citations ─────────────────────────────────────────
.citations {
  margin-top: $space-3;
  padding: $space-3;
  background: $primary-soft;
  border-radius: $radius-md;
}

.cit-header {
  display: flex;
  align-items: center;
  gap: $space-1;
  margin-bottom: $space-2;
  color: $primary;
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  letter-spacing: 0.02em;
}

.book-icon {
  font-size: 14px;
  color: $primary;
}

.cit-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.cit-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $space-2 $space-3;
  background: $bg-card;
  border-radius: $radius-sm;
  font-size: $font-size-xs;
  color: $primary-hover;
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;
}

.cit-item:active {
  transform: scale(0.98);
  box-shadow: 0 2px 8px rgba($primary, 0.12);
}

.cit-text {
  flex: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-right: $space-2;
  font-weight: $font-weight-medium;
}

.ext-link-icon {
  font-size: 14px;
  color: $primary;
  flex-shrink: 0;
}

// ── System messages (status, escalation hints) ────────
.system-message {
  display: flex;
  justify-content: center;
  padding: $space-2 0;
  font-size: $font-size-xs;
  color: $text-muted;
  font-style: italic;
}

// ── Inline call-teacher button & confirmation ─────────
.inline-call-teacher {
  display: inline-flex;
  align-items: center;
  gap: $space-2;
  margin-top: $space-3;
  padding: $space-2 $space-4;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  color: $text-inverse;
  border-radius: $radius-full;
  box-shadow: 0 6px 18px -6px rgba($primary, 0.50),
              0 2px 4px -2px rgba($primary, 0.20);
  transition: transform 0.18s ease-out, opacity 0.18s ease-out;
}

.inline-call-teacher:active {
  transform: scale(0.96);
  opacity: 0.92;
}

.call-inline-icon {
  font-size: 18px;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.call-inline-text {
  font-size: 13px;
  font-weight: $font-weight-bold;
  color: $text-inverse;
}

.inline-call-done {
  display: inline-flex;
  align-items: center;
  gap: $space-2;
  margin-top: $space-3;
  padding: $space-2 $space-4;
  background: rgba($success, 0.10);
  border: 1px solid rgba($success, 0.18);
  border-radius: $radius-full;
}

.call-done-icon {
  font-size: 18px;
  color: $success;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.call-done-text {
  font-size: 13px;
  font-weight: $font-weight-bold;
  color: $success;
}

// ============================================================
// Suggestions (R10 follow-up questions)
// ============================================================
.suggestions-area {
  padding: 0 $space-2;
  margin-bottom: $space-5;
  opacity: 0;
  animation: fadeUp 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.suggestions-header {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-3;
  padding: 0 $space-1;
}

.suggestions-icon {
  font-size: 16px;
  color: $warning;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.suggestions-title {
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $text-secondary;
  letter-spacing: 0.02em;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.suggestion-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: $space-3 $space-4;
  background: $bg-card;
  border: 1px solid rgba($primary, 0.14);
  border-radius: $radius-md;
  box-shadow: 0 1px 3px rgba($primary, 0.06);
  transition: transform 0.18s ease-out, background 0.18s ease-out, border-color 0.18s ease-out;
}

.suggestion-chip:active {
  background: $primary-soft;
  border-color: $primary;
  transform: scale(0.98);
}

.suggestion-text {
  flex: 1;
  font-size: 13px;
  color: $primary-hover;
  line-height: $line-height-normal;
  font-weight: $font-weight-medium;
}

.suggestion-arrow {
  font-size: 16px;
  color: $primary;
  margin-left: $space-2;
  flex-shrink: 0;
}

// ============================================================
// Bottom input bar (sits above CustomTabBar)
// ============================================================
.bottom-area {
  position: fixed;
  bottom: calc(#{$tab-bar-h} + env(safe-area-inset-bottom));
  left: 0;
  right: 0;
  z-index: 40;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  padding: $space-3 $space-4;
  border-top: 1px solid rgba($primary, 0.06);
}

.call-menu-overlay {
  position: absolute;
  bottom: 100%;
  left: 0;
  right: 0;
  display: flex;
  justify-content: flex-end;
  padding: 0 $space-4 $space-2;
  z-index: 50;
}

.call-menu {
  background: $bg-card;
  border-radius: $radius-md;
  box-shadow: 0 8px 24px rgba($text-primary, 0.12),
              0 2px 6px rgba($text-primary, 0.06);
  overflow: hidden;
  min-width: 140px;
}

.call-menu-item {
  display: flex;
  align-items: center;
  gap: $space-2;
  padding: $space-3 $space-4;
  transition: background 0.15s ease-out;
}

.call-menu-item:active {
  background: $primary-soft;
}

.call-menu-icon {
  font-size: 18px;
  color: $primary;
}

.call-menu-text {
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  color: $text-primary;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: $space-2;
  background: $surface-container-low;
  border-radius: $radius-full;
  padding: $space-1 $space-1 $space-1 $space-4;
  border: 1px solid transparent;
  transition: border-color 0.18s ease-out, background 0.18s ease-out;
}

.input-wrapper:focus-within {
  background: $bg-card;
  border-color: rgba($primary, 0.30);
  box-shadow: 0 0 0 4px rgba($primary, 0.08);
}

.input {
  flex: 1;
  background: transparent;
  border: none;
  font-size: $font-size-sm;
  color: $text-primary;
  font-family: $font-family-sans;
}

.input::placeholder {
  color: $text-muted;
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: $radius-full;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px -4px rgba($primary, 0.40);
  transition: transform 0.18s ease-out, opacity 0.18s ease-out, box-shadow 0.18s ease-out;
}

.send-btn:active {
  transform: scale(0.92);
}

.send-btn.disabled {
  opacity: 0.40;
  box-shadow: none;
}

.send-icon {
  font-size: 20px;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

// ============================================================
// Markdown rendering — shared by ai-bubble, teacher-bubble,
// and source popup (use modifier .markdown-body--rich for the
// fuller code/blockquote/table styles in popup).
// ============================================================
.markdown-body {
  font-size: $font-size-sm;
  line-height: $line-height-relaxed;

  :deep(p) {
    margin-bottom: $space-2;
  }
  :deep(p:last-child) {
    margin-bottom: 0;
  }
  :deep(ul) {
    padding-left: $space-4;
    margin-bottom: $space-2;
    list-style-type: disc;
  }
  :deep(ol) {
    padding-left: $space-4;
    margin-bottom: $space-2;
    list-style-type: decimal;
  }
  :deep(li) {
    margin-bottom: $space-1;
  }
  :deep(strong) {
    font-weight: $font-weight-bold;
    color: $primary;
  }
  :deep(em) {
    font-style: italic;
    color: $text-primary;
  }
  :deep(a) {
    color: $primary;
    text-decoration: underline;
    text-underline-offset: 2px;
  }
  :deep(code) {
    background: $surface-container-low;
    padding: 2px 6px;
    border-radius: $radius-sm;
    font-family: 'SF Mono', 'Roboto Mono', Menlo, Consolas, monospace;
    font-size: 13px;
    color: $primary-hover;
  }
}

.markdown-body--rich {
  font-size: $font-size-sm;
  color: $text-secondary;
  line-height: $line-height-relaxed;

  :deep(h1),
  :deep(h2),
  :deep(h3) {
    font-weight: $font-weight-bold;
    color: $text-primary;
    margin: $space-3 0 $space-2;
  }
  :deep(h1) { font-size: $font-size-lg; }
  :deep(h2) { font-size: $font-size-base; }
  :deep(h3) { font-size: $font-size-sm; }
  :deep(pre) {
    background: $surface-container-low;
    padding: $space-3;
    border-radius: $radius-md;
    overflow-x: auto;
    margin-bottom: $space-3;
    font-size: 13px;
    line-height: $line-height-normal;
  }
  :deep(pre code) {
    background: transparent;
    padding: 0;
    color: $text-primary;
  }
  :deep(blockquote) {
    border-left: 3px solid $primary;
    padding-left: $space-3;
    color: $text-secondary;
    margin: $space-3 0;
  }
  :deep(table) {
    width: 100%;
    border-collapse: collapse;
    margin-bottom: $space-3;
    font-size: 13px;
  }
  :deep(th),
  :deep(td) {
    border: 1px solid $border;
    padding: $space-2 $space-3;
    text-align: left;
  }
  :deep(th) {
    background: $surface-container-low;
    font-weight: $font-weight-semibold;
  }
}

// ============================================================
// Source popup (drag-to-fullscreen sheet)
// ============================================================
.source-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba($text-primary, 0.55);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: fadeIn 0.2s ease-out;
}

.source-popup {
  width: 100%;
  max-width: 480px;
  background: $bg-card;
  border-radius: $radius-xl $radius-xl 0 0;
  display: flex;
  flex-direction: column;
  transition: height 0.2s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 -16px 48px -12px rgba($text-primary, 0.25);
}

.source-popup-drag-bar {
  display: flex;
  justify-content: center;
  padding: $space-2 0 0;
  cursor: grab;
}

.drag-indicator {
  width: 36px;
  height: 4px;
  border-radius: $radius-full;
  background: $border-strong;
}

.source-popup-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $space-3 $space-5 $space-3;
  border-bottom: 1px solid $divider;
}

.source-popup-title {
  font-size: $font-size-base;
  font-weight: $font-weight-bold;
  color: $text-primary;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-header-actions {
  display: flex;
  align-items: center;
  gap: $space-3;
  flex-shrink: 0;
}

.source-expand,
.source-close {
  font-size: 22px;
  color: $text-muted;
  padding: $space-1;
  border-radius: $radius-full;
  transition: background 0.15s ease-out, color 0.15s ease-out;
}

.source-expand:active,
.source-close:active {
  background: $surface-container-low;
  color: $text-primary;
}

.source-popup-body {
  padding: $space-5;
  flex: 1;
  overflow: hidden;
}
</style>
