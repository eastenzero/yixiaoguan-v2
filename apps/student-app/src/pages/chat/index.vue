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

    <!-- 来源弹层 -->
    <view v-if="sourcePopup.visible" class="source-overlay" @click="sourcePopup.visible = false">
      <view class="source-popup" @click.stop>
        <view class="source-popup-header">
          <text class="source-popup-title">{{ sourcePopup.title }}</text>
          <text class="material-symbols-outlined source-close" @click="sourcePopup.visible = false">close</text>
        </view>
        <scroll-view class="source-popup-body" scroll-y>
          <text class="source-popup-content">{{ sourcePopup.content }}</text>
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
const showCallMenu = ref(false)
const sourcePopup = reactive({ visible: false, title: '', content: '' })

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
function goBack() { uni.navigateBack() }
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
  sourcePopup.visible = true
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

<style scoped>
.chat-page { display: flex; flex-direction: column; height: 100vh; background: #f7f9fb; }

.top-nav { display: flex; justify-content: space-between; align-items: center; padding: calc(env(safe-area-inset-top) + 1rem) 1.5rem 1rem; background: rgba(247,249,251,0.8); backdrop-filter: blur(20px); z-index: 50; }
.nav-left { display: flex; align-items: center; gap: 0.75rem; }
.nav-title { font-size: 1.25rem; font-weight: 700; color: #630ed4; }
.nav-back-icon, .nav-history-icon { font-size: 1.5rem; color: #630ed4; }

.welcome-center { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 0 1.5rem 7.5rem; }
.welcome-content { display: flex; flex-direction: column; align-items: center; text-align: center; margin-bottom: 2.5rem; }
.welcome-input-area { width: 100%; max-width: 20rem; }
.empty-icon { width: 3.75rem; height: 3.75rem; background: linear-gradient(135deg, #630ed4, #7c3aed); border-radius: 1.875rem; display: flex; align-items: center; justify-content: center; margin-bottom: 1.25rem; box-shadow: 0 0.5rem 1.5rem rgba(99,14,212,0.2); }
.empty-sparkle-icon { font-size: 1.75rem; color: #fff; }
.empty-title { font-size: 1.5rem; font-weight: 800; color: #191c1e; margin-bottom: 0.625rem; }
.empty-desc { font-size: 0.875rem; color: #64748b; line-height: 1.7; max-width: 16.25rem; }

.chat-container { flex: 1; padding: 0 1rem; box-sizing: border-box; }
.msg-wrapper { display: flex; flex-direction: column; margin-bottom: 1.5rem; }

.user-msg { align-items: flex-end; }
.user-bubble { background: linear-gradient(135deg, #630ed4, #7c3aed); color: #fff; border-radius: 0.75rem 0.75rem 0 0.75rem; max-width: 85%; padding: 0.75rem 1rem; box-shadow: 0 0.5rem 1rem rgba(99,14,212,0.1); font-size: 0.875rem; line-height: 1.6; }
.msg-time { font-size: 0.6875rem; font-weight: 700; color: #94a3b8; margin-top: 0.5rem; padding: 0 0.5rem; }

.ai-msg { align-items: flex-start; }
.ai-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; padding: 0 0.5rem; }
.ai-avatar { width: 1.5rem; height: 1.5rem; border-radius: 0.75rem; background: linear-gradient(135deg, #630ed4, #7c3aed); display: flex; align-items: center; justify-content: center; }
.bot-icon { font-size: 0.875rem; color: #fff; }
.ai-name { font-size: 0.75rem; font-weight: 700; color: #630ed4; letter-spacing: 0.0625rem; }
.ai-bubble { background: #fff; color: #191c1e; border-radius: 0.75rem 0.75rem 0.75rem 0; max-width: 90%; padding: 1rem; box-shadow: 0 0.125rem 0.5rem rgba(0,0,0,0.02); border-left: 0.25rem solid #630ed4; font-size: 0.875rem; line-height: 1.6; }

.teacher-avatar { width: 1.5rem; height: 1.5rem; border-radius: 0.75rem; background: linear-gradient(135deg, #059669, #34d399); display: flex; align-items: center; justify-content: center; }
.teacher-icon { font-size: 0.875rem; color: #fff; }
.teacher-name { font-size: 0.75rem; font-weight: 700; color: #059669; letter-spacing: 0.0625rem; }
.teacher-bubble { background: #fff; color: #191c1e; border-radius: 0.75rem 0.75rem 0.75rem 0; max-width: 90%; padding: 1rem; box-shadow: 0 0.125rem 0.5rem rgba(0,0,0,0.02); border-left: 0.25rem solid #059669; font-size: 0.875rem; line-height: 1.6; }

.citations { margin-top: 1rem; padding: 0.75rem; background: #f2f4f6; border-radius: 0.5rem; }
.cit-header { display: flex; align-items: center; gap: 0.25rem; margin-bottom: 0.5rem; color: #630ed4; font-size: 0.75rem; font-weight: 700; }
.book-icon { font-size: 0.875rem; color: #630ed4; }
.cit-list { display: flex; flex-direction: column; gap: 0.5rem; }
.cit-item { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem; background: rgba(255,255,255,0.5); border-radius: 0.25rem; font-size: 0.75rem; color: #6e3aca; text-decoration: underline; }
.cit-text { flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; margin-right: 0.5rem; }
.ext-link-icon { font-size: 0.75rem; color: #6e3aca; }

.typing-animation { display: flex; gap: 0.25rem; padding: 0.25rem 0; }
.dot { width: 0.375rem; height: 0.375rem; background: #630ed4; border-radius: 50%; animation: typing 1.4s infinite ease-in-out; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.cursor { display: inline-block; color: #630ed4; animation: blink 1s infinite; margin-left: 0.125rem; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }

.bottom-spacer { height: 10rem; }

.bottom-area { position: fixed; bottom: 3.5rem; left: 0; right: 0; z-index: 40; background: rgba(255,255,255,0.8); backdrop-filter: blur(20px); padding: 0.75rem 1rem; padding-bottom: calc(0.75rem + env(safe-area-inset-bottom)); }
.call-menu-overlay { position: absolute; bottom: 100%; left: 0; right: 0; display: flex; justify-content: flex-end; padding: 0 1rem 0.5rem; z-index: 50; }
.call-menu { background: #fff; border-radius: 0.75rem; box-shadow: 0 0.25rem 1.5rem rgba(0,0,0,0.12); overflow: hidden; min-width: 8rem; }
.call-menu-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; }
.call-menu-item:active { background: #f2f4f6; }
.call-menu-icon { font-size: 1.125rem; color: #630ed4; }
.call-menu-text { font-size: 0.875rem; font-weight: 600; color: #191c1e; }

.system-message { display: flex; justify-content: center; padding: 0.5rem 0; font-size: 0.75rem; color: #94a3b8; font-style: italic; }

.input-wrapper { display: flex; align-items: center; gap: 0.5rem; background: #e6e8ea; border-radius: 1.5rem; padding: 0.375rem 0.375rem 0.375rem 1rem; }
.input { flex: 1; background: transparent; border: none; font-size: 0.875rem; color: #191c1e; }
.send-btn { width: 2.5rem; height: 2.5rem; border-radius: 1.25rem; background: linear-gradient(135deg, #630ed4, #7c3aed); display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.send-btn.disabled { opacity: 0.5; }
.send-icon { font-size: 1.25rem; color: #fff; }

.markdown-body { font-size: 0.875rem; line-height: 1.6; }
.markdown-body :deep(p) { margin-bottom: 0.5rem; }
.markdown-body :deep(ul) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: disc; }
.markdown-body :deep(ol) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: decimal; }
.markdown-body :deep(li) { margin-bottom: 0.25rem; }
.markdown-body :deep(strong) { font-weight: 700; color: #630ed4; }

.inline-call-teacher { display: inline-flex; align-items: center; gap: 0.375rem; margin-top: 0.75rem; padding: 0.5rem 1rem; background: linear-gradient(135deg, #630ed4, #7c3aed); color: #fff; border-radius: 1.5rem; transition: all 0.2s; box-shadow: 0 0.25rem 0.75rem rgba(99,14,212,0.25); }
.inline-call-teacher:active { transform: scale(0.95); opacity: 0.9; }
.call-inline-icon { font-size: 1.125rem; color: #fff; }
.call-inline-text { font-size: 0.8125rem; font-weight: 700; color: #fff; }
.inline-call-done { display: inline-flex; align-items: center; gap: 0.375rem; margin-top: 0.75rem; padding: 0.5rem 1rem; background: rgba(30,200,60,0.1); border-radius: 1.5rem; }
.call-done-icon { font-size: 1.125rem; color: #1e8e3e; }
.call-done-text { font-size: 0.8125rem; font-weight: 700; color: #1e8e3e; }

/* 来源弹层 */
.source-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: flex-end; justify-content: center; }
.source-popup { width: 100%; max-width: 30rem; background: #fff; border-radius: 1rem 1rem 0 0; max-height: 60vh; display: flex; flex-direction: column; }
.source-popup-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.25rem; border-bottom: 1px solid #e2e8f0; }
.source-popup-title { font-size: 1rem; font-weight: 700; color: #191c1e; flex: 1; }
.source-close { font-size: 1.25rem; color: #94a3b8; }
.source-popup-body { padding: 1.25rem; flex: 1; }
.source-popup-content { font-size: 0.875rem; color: #475569; line-height: 1.8; white-space: pre-wrap; }
</style>
