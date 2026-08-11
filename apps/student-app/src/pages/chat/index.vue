<template>
  <view class="chat-page">
    <view class="top-nav">
      <view class="nav-left" @click="goBack">
        <text class="material-symbols-outlined nav-back-icon">arrow_back</text>
        <view class="nav-title-group">
          <text class="nav-title">智能问答</text>
          <text class="nav-subtitle">SDFMU · CAMPUS AI</text>
        </view>
      </view>
      <view class="nav-right" @click="goToHistory">
        <view class="nav-online"><view class="nav-online-dot" /><text>在线</text></view>
        <text class="material-symbols-outlined nav-history-icon">history</text>
      </view>
    </view>

    <!-- 欢迎空状态 -->
    <view v-if="!messages.length" class="welcome-center">
      <view class="welcome-content">
        <view class="assistant-dock">
          <view class="assistant-dock-icon">
            <text class="material-symbols-outlined assistant-sparkle">auto_awesome</text>
          </view>
          <view class="assistant-dock-copy">
            <text class="assistant-dock-title">医小管 AI 助理</text>
            <text class="assistant-dock-caption">你的校园，随时有回应</text>
          </view>
          <view class="assistant-dock-action"><text class="material-symbols-outlined">verified</text></view>
        </view>

        <view class="knowledge-strip">
          <view class="knowledge-strip-leading">
            <text class="material-symbols-outlined knowledge-strip-icon">fact_check</text>
            <view class="knowledge-strip-copy">
              <text class="knowledge-strip-title">医小管知识库</text>
              <text class="knowledge-strip-status">回答附材料</text>
            </view>
          </view>
          <view class="knowledge-sync-badge">
            <text class="material-symbols-outlined knowledge-sync-icon">sync</text>
            <text>同步至 2026.08.10</text>
          </view>
        </view>

        <view class="focus-heading">
          <text class="focus-title">你的校园，随时有回应</text>
        </view>

        <view class="welcome-composer">
          <view class="input-wrapper">
            <input
              v-model="inputMessage"
              class="input"
              placeholder="输入你的问题..."
              confirm-type="send"
              @focus="sendError = ''"
              @confirm="sendMessage"
            />
            <view
              :class="['send-btn', { disabled: !canSend }]"
              hover-class="send-btn--pressed"
              :hover-start-time="0"
              :hover-stay-time="90"
              @click="sendMessage"
            >
              <text class="material-symbols-outlined send-icon">arrow_upward</text>
            </view>
          </view>
          <view v-if="sendError" class="send-error">
            <text class="material-symbols-outlined send-error-icon">cloud_off</text>
            <text class="send-error-text">{{ sendError }}</text>
            <text class="send-error-action" @click="sendMessage">重试</text>
          </view>
        </view>

        <view class="recent-block">
          <view class="recent-heading">
            <text>最近提问</text>
            <text class="recent-heading-action" @click="goToHistory">查看全部</text>
          </view>
          <view v-if="recentConversations.length" class="recent-list">
            <view
              v-for="conv in recentConversations"
              :key="conv.id"
              class="recent-item"
              hover-class="recent-item--pressed"
              @click="openRecentConversation(conv.id)"
            >
              <view class="recent-empty-icon"><text class="material-symbols-outlined">chat_bubble</text></view>
              <view class="recent-empty-copy">
                <text class="recent-empty-title">{{ conv.title || '校园问答' }}</text>
                <text class="recent-empty-caption">{{ formatRecentTime(conv.updated_at) }}</text>
              </view>
              <text class="material-symbols-outlined recent-empty-arrow">chevron_right</text>
            </view>
          </view>
          <view v-else class="recent-empty">
            <view class="recent-empty-icon">
              <text class="material-symbols-outlined">chat_bubble</text>
            </view>
            <view class="recent-empty-copy">
              <text class="recent-empty-title">暂无提问记录</text>
              <text class="recent-empty-caption">开始提问后，可在这里继续上一次对话</text>
            </view>
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
            <view :class="['msg-bubble', 'ai-bubble', { streaming: msg.isStreaming }]">
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
                  <view class="cit-heading">
                    <text class="cit-title">回答附加参考资料</text>
                  </view>
                </view>
                <view class="cit-list">
                  <view
                    v-for="(source, si) in mixedEvidenceSources(msg.sources)"
                    :key="source.source_url || source.document_id || si"
                    class="cit-item"
                    @click="handleSourceClick(source)"
                  >
                    <view :class="['cit-index', { official: !!source.source_url }]">0{{ si + 1 }}</view>
                    <view class="cit-copy">
                      <text class="cit-text">{{ source.title }}</text>
                      <view class="cit-meta-row">
                        <text :class="['cit-badge', { verified: source.verified }]">
                          {{ source.source_label || '医小管知识库' }}
                        </text>
                        <text v-if="source.screenshot_url" class="cit-meta screenshot">官网截图</text>
                        <text v-if="source.college" class="cit-meta">{{ source.college }}</text>
                        <text v-if="source.published_at" class="cit-meta">{{ source.published_at }}</text>
                        <text v-if="isHistoricalSource(source)" class="cit-meta historical">历史参考</text>
                      </view>
                    </view>
                    <view :class="['cit-action', { official: !!source.source_url }]">
                      <text class="material-symbols-outlined ext-link-icon">
                        {{ source.source_url ? 'arrow_outward' : 'description' }}
                      </text>
                    </view>
                  </view>
                </view>
              </view>
              <view v-if="msg.answer_notice && !msg.isStreaming" class="answer-notice">
                <text class="material-symbols-outlined notice-icon">info</text>
                <text>{{ msg.answer_notice }}</text>
              </view>
            </view>
            <view v-if="!msg.isStreaming" class="answer-freshness">
              <text class="material-symbols-outlined answer-freshness-icon">sync</text>
              <text>医小管知识库更新于 {{ formatKnowledgeDate(msg.knowledge_updated_at) }}</text>
            </view>
            <text class="msg-time">{{ formatTime(msg.timestamp) }}</text>
            <view
              v-if="!msg.isStreaming && isLatestAssistantMessage(msg.id) && conversationStatus === 'ai_serving'"
              class="answer-support"
              @click="handleCallTeacher"
            >
              <view class="support-icon-wrap"><text class="material-symbols-outlined support-icon">support_agent</text></view>
              <view class="support-copy">
                <text class="support-kicker">NEED MORE HELP?</text>
                <text class="support-title">还没有解决？为你转接老师</text>
              </view>
              <view class="support-action">
                <text>{{ escalateLoading ? '呼叫中' : '转人工' }}</text>
                <text class="material-symbols-outlined support-arrow">arrow_forward</text>
              </view>
            </view>
            <view v-if="conversationStatus === 'pending_teacher' && isLatestAssistantMessage(msg.id)" class="answer-support answer-support-done">
              <text class="material-symbols-outlined call-done-icon">check_circle</text>
              <view class="support-copy">
                <text class="support-kicker">TEACHER SERVICE</text>
                <text class="support-title">已通知老师，请耐心等待回复</text>
              </view>
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
            <text class="material-symbols-outlined suggestions-icon">route</text>
            <view class="suggestions-heading">
              <text class="suggestions-kicker">NEXT STEPS</text>
              <text class="suggestions-title">继续了解 / 下一步</text>
            </view>
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
            :class="['send-btn', { disabled: !canSend && !isStreaming, streaming: isStreaming }]"
            hover-class="send-btn--pressed"
            :hover-start-time="0"
            :hover-stay-time="90"
            @click="isStreaming ? stopStreaming() : sendMessage()"
            @longpress="onSendLongPress"
          >
            <text class="material-symbols-outlined send-icon">{{ isStreaming ? 'stop' : 'send' }}</text>
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
          <view class="source-proof">
            <view class="source-destination">
              <view class="source-destination-icon">
                <text class="material-symbols-outlined">verified</text>
              </view>
              <view class="source-destination-copy">
                <text class="source-destination-kicker">即将前往</text>
                <text class="source-destination-title">
                  {{ sourcePopup.source.source_label || '资料来源' }}
                </text>
                <text v-if="sourcePopup.source.source_url" class="source-destination-host">
                  {{ sourceHost(sourcePopup.source.source_url) }}
                </text>
              </view>
            </view>
            <view class="source-proof-meta">
              <text :class="['source-proof-badge', { verified: sourcePopup.source.verified }]">
                {{ sourcePopup.source.source_label || '校园知识库' }}
              </text>
              <text v-if="sourcePopup.source.college">{{ sourcePopup.source.college }}</text>
              <text v-if="sourcePopup.source.campus">{{ sourcePopup.source.campus }}</text>
              <text v-if="sourcePopup.source.published_at">发布于 {{ sourcePopup.source.published_at }}</text>
              <text v-if="sourcePopup.source.academic_year">适用学年 {{ sourcePopup.source.academic_year }}</text>
            </view>
            <image
              v-if="sourcePopup.source.screenshot_url"
              class="source-proof-image"
              :src="sourcePopup.source.screenshot_url"
              mode="widthFix"
              @click="previewSourceImage"
            />
            <view
              v-if="sourcePopup.source.source_url"
              class="source-open-button"
              hover-class="source-open-button--pressed"
              :hover-start-time="0"
              :hover-stay-time="120"
              @click="openOfficialSource"
            >
              <view>
                <text class="source-open-kicker">OFFICIAL SOURCE</text>
                <text class="source-open-label">打开学校或学院官网原文</text>
              </view>
              <text class="material-symbols-outlined">arrow_outward</text>
            </view>
            <view v-else class="source-link-missing">
              <text class="material-symbols-outlined">info</text>
              <text>此条暂未关联官网原文，仅展示知识库摘录。</text>
            </view>
          </view>
          <view
            class="source-excerpt-toggle"
            :aria-expanded="sourceExcerptExpanded"
            @click="sourceExcerptExpanded = !sourceExcerptExpanded"
          >
            <view>
              <text class="source-excerpt-title">知识摘录</text>
              <text class="source-excerpt-caption">用于快速核对，不替代官网原文</text>
            </view>
            <text class="material-symbols-outlined">
              {{ sourceExcerptExpanded ? 'expand_less' : 'expand_more' }}
            </text>
          </view>
          <view
            v-if="sourceExcerptExpanded"
            class="markdown-body source-markdown"
            v-html="renderMarkdown(sourcePopup.content)"
          />
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
import { createConversation, getConversation, getMessages, listConversations, escalate } from '@/api/chat'
import { fetchSSE } from '@/utils/sse'
import { wsManager } from '@/utils/websocket'
import { centrifugeManager } from '@/utils/centrifuge'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { trackEvent } from '@/utils/track'
import {
  mixedEvidenceSources,
  presentSource,
  presentSources,
} from '@/utils/sourcePresentation'
import { openExternal } from '@/composables/useServiceNavigation'
import type { Message as BaseMessage, Source, ConversationStatus, MessageResponse, ConversationResponse } from '@/types/chat'

const userStore = useUserStore()
const KNOWLEDGE_UPDATED_AT = '2026-08-10'

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
const conversationId = ref<number | null>(null)
const conversationStatus = ref<ConversationStatus>('ai_serving')
const escalateLoading = ref(false)
const suggestedQuestions = ref<string[]>([])
const recentConversations = ref<ConversationResponse[]>([])
const showCallMenu = ref(false)
const sendError = ref('')
let activeController: AbortController | null = null
const sourcePopup = reactive<{ visible: boolean; title: string; content: string; source: Source }>({
  visible: false,
  title: '',
  content: '',
  source: { title: '' },
})
const sourceSheetHeight = ref(50)
const sourceExcerptExpanded = ref(false)
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
  void loadRecentConversations()
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

async function loadRecentConversations() {
  try {
    const res = await listConversations(1, 3)
    recentConversations.value = res.items
  } catch {
    recentConversations.value = []
  }
}

function openRecentConversation(id: number) {
  messages.value = []
  conversationId.value = id
  void loadConversation()
}

function formatRecentTime(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '继续对话'
  return `${date.getMonth() + 1}月${date.getDate()}日 · 继续对话`
}

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
    sources: presentSources(m.metadata_?.sources),
    answer_notice: m.metadata_?.answer_notice || undefined,
    knowledge_updated_at: m.metadata_?.knowledge_updated_at || KNOWLEDGE_UPDATED_AT,
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
  sendError.value = ''

  if (!conversationId.value) {
    try {
      const conv = await createConversation(content.slice(0, 20))
      conversationId.value = conv.id
      conversationStatus.value = 'ai_serving'
      wsManager.send({ type: 'join_room', data: { conv_id: conv.id } })
      centrifugeManager.joinConversation(conv.id)
    } catch (e) {
      console.error('创建会话失败:', e)
      sendError.value = '问答服务暂未连接，你的问题已保留'
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
  activeController = new AbortController()

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
          msg.sources = presentSources(data.sources)
          msg.answer_notice = data.answer_notice
          msg.knowledge_updated_at = data.knowledge_updated_at || KNOWLEDGE_UPDATED_AT
          msg.isStreaming = false
          if (!suggestedQuestions.value.length) {
            suggestedQuestions.value = buildContextualQuestions(userContent, msg.content)
          }
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
          suggestedQuestions.value = normalizeSuggestedQuestions(questions, userContent, getReactive().content)
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
      , activeController.signal
    )
  } catch (e: any) {
    console.error('Stream error:', e)
    isTyping.value = false
    const msg = messages.value.find(m => m.id === aiMessage.id)
    if (msg && e?.name !== 'AbortError') {
      msg.content = '抱歉，AI 服务暂时不可用，请稍后重试。'
      msg.isStreaming = false
    } else if (msg) {
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
    activeController = null
  }
}

function stopStreaming() {
  if (!isStreaming.value) return
  activeController?.abort()
  const current = messages.value.find(message => message.isStreaming)
  if (current) {
    current.isStreaming = false
    if (current.content) current.content += '\n\n_已停止生成，你可以继续追问。_'
  }
  isStreaming.value = false
  isTyping.value = false
  uni.showToast({ title: '已停止生成', icon: 'none' })
}

// ============ 来源点击 — 弹层展示 ============
function handleSourceClick(source: Source) {
  const presented = presentSource(source)
  sourcePopup.title = presented.title || '参考资料'
  sourcePopup.content = presented.content || '暂无详细内容'
  sourcePopup.source = presented
  sourceSheetHeight.value = 50
  sourceExcerptExpanded.value = !presented.source_url
  trackEvent('kb_doc_clicked', {
    conv_id: conversationId.value,
    source_title: source.title || '',
  })
  sourcePopup.visible = true
}

function isHistoricalSource(source: Source) {
  return String(source.effective_status || '').startsWith('historical')
}
function previewSourceImage() {
  if (!sourcePopup.source.screenshot_url) return
  uni.previewImage({
    current: sourcePopup.source.screenshot_url,
    urls: [sourcePopup.source.screenshot_url],
  })
}
function openOfficialSource() {
  const url = sourcePopup.source.source_url
  if (!url) return
  trackEvent('official_source_opened', {
    conv_id: conversationId.value,
    source_title: sourcePopup.title,
    source_url: url,
  })
  openExternal(url)
}
function sourceHost(url?: string) {
  if (!url) return ''
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return '官方网页'
  }
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

function isLatestAssistantMessage(id: ChatMessage['id']): boolean {
  for (let index = messages.value.length - 1; index >= 0; index -= 1) {
    if (messages.value[index].role === 'assistant') return messages.value[index].id === id
  }
  return false
}

function buildContextualQuestions(question: string, answer: string): string[] {
  const context = `${question} ${answer}`
  if (/\u5956\u5b66\u91d1|\u52a9\u5b66\u91d1|\u8d44\u52a9|\u8bc4\u5956\u8bc4\u4f18/.test(context)) {
    return ['\u5206\u522b\u8bf4\u660e\u56fd\u5bb6\u7ea7\u3001\u7701\u7ea7\u548c\u6821\u7ea7\u5956\u5b66\u91d1', '\u5bf9\u6bd4\u5404\u7c7b\u5956\u5b66\u91d1\u7684\u6761\u4ef6\u548c\u91d1\u989d', '\u6302\u79d1\u3001\u8865\u8003\u6216\u91cd\u4fee\u4f1a\u6709\u4ec0\u4e48\u5f71\u54cd\uff1f']
  }
  if (/\u5165\u515a|\u515a\u5458|\u79ef\u6781\u5206\u5b50|\u53d1\u5c55\u5bf9\u8c61|\u56e2\u5458\u63a8\u4f18/.test(context)) {
    return ['\u6309\u6211\u7684\u5b66\u9662\u8bf4\u660e\u57f9\u517b\u6d41\u7a0b', '\u6302\u79d1\u4f1a\u5f71\u54cd\u5165\u515a\u5417\uff1f', '\u5217\u51fa\u6bcf\u4e2a\u9636\u6bb5\u9700\u8981\u7684\u6750\u6599']
  }
  if (/\u6302\u79d1|\u8865\u8003|\u91cd\u4fee|\u7f13\u8003|\u6210\u7ee9|\u5b66\u7c4d/.test(context)) {
    return ['\u8865\u8003\u548c\u91cd\u4fee\u7684\u533a\u522b\u662f\u4ec0\u4e48\uff1f', '\u8fd9\u4f1a\u5f71\u54cd\u8bc4\u5956\u8bc4\u4f18\u5417\uff1f', '\u6309\u6211\u7684\u5165\u5b66\u5e74\u7ea7\u7ee7\u7eed\u5224\u65ad']
  }
  if (/\u56fe\u4e66\u9986|\u5f00\u9986|\u95ed\u9986|\u501f\u9605|\u7eed\u501f/.test(context)) {
    return ['\u5bf9\u6bd4\u4e24\u4e2a\u6821\u533a\u7684\u5f00\u653e\u65f6\u95f4', '\u8bf4\u660e\u501f\u9605\u3001\u7eed\u501f\u548c\u903e\u671f\u89c4\u5219', '\u7ed9\u6211\u53ef\u4ee5\u76f4\u63a5\u6253\u5f00\u7684\u5b98\u65b9\u5165\u53e3']
  }
  if (/\u90ae\u7bb1|\u6821\u56ed\u7f51|VPN|\u8eab\u4efd\u8ba4\u8bc1|\u5bc6\u7801/.test(context)) {
    return ['\u7ed9\u6211\u5b98\u65b9\u767b\u5f55\u6216\u529e\u7406\u5165\u53e3', '\u628a\u64cd\u4f5c\u6b65\u9aa4\u6309\u987a\u5e8f\u5217\u51fa\u6765', '\u767b\u5f55\u5931\u8d25\u65f6\u5e94\u8be5\u627e\u8c01\uff1f']
  }
  return ['\u628a\u529e\u7406\u6b65\u9aa4\u5217\u6e05\u695a', '\u7ed9\u6211\u6700\u65b0\u7684\u5b98\u65b9\u4f9d\u636e', '\u6309\u6211\u7684\u5b66\u9662\u548c\u5e74\u7ea7\u7ee7\u7eed\u8bf4\u660e']
}

function normalizeSuggestedQuestions(questions: string[], question: string, answer: string): string[] {
  const profileRequest = /(?:\u8bf7\u63d0\u4f9b|\u8bf7\u544a\u8bc9|\u544a\u8bc9\u6211\u4f60\u7684|\u8bf7\u8865\u5145|\u8865\u5145\u4f60\u7684|\u8bf7\u586b\u5199|\u8bf7\u9009\u62e9).*(?:\u5b66\u9662|\u5e74\u7ea7|\u4e13\u4e1a|\u73ed\u7ea7|\u8eab\u4efd|\u804c\u4f4d|\u5b66\u751f\u7c7b\u578b)/
  const result = questions.map(item => item.trim()).filter(item => item && !profileRequest.test(item))
  for (const fallback of buildContextualQuestions(question, answer)) {
    if (!result.includes(fallback)) result.push(fallback)
    if (result.length === 3) break
  }
  return result.slice(0, 3)
}

// ============ R10: 推荐问题点击 ============
function handleSuggestionClick(question: string) {
  trackEvent('chat_followup_click', { question_length: question.length })
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

function formatKnowledgeDate(value?: string): string {
  return (value || KNOWLEDGE_UPDATED_AT).replace(/-/g, '.')
}

function scrollToBottom() {
  nextTick(() => { scrollTop.value = 9999999 + Math.random() })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.chat-page {
  display: flex;
  flex-direction: column;
  width: min(100%, 430px);
  height: 100dvh;
  margin: 0 auto;
  overflow: hidden;
  background: var(--yxg-canvas);
  color: #332a38;
}

.top-nav { position: relative; display: flex; justify-content: space-between; align-items: center; padding: calc(env(safe-area-inset-top) + .75rem) 1.25rem .75rem; background: linear-gradient(180deg, rgba(255,255,255,.72), rgba(244,239,233,.62)); backdrop-filter: blur(26px) saturate(165%); -webkit-backdrop-filter: blur(26px) saturate(165%); box-shadow: inset 0 -1px 0 rgba(255,255,255,.7); z-index: 50; }
.top-nav::after { content: ''; position: absolute; left: 16%; right: 16%; bottom: 0; height: 1px; background: linear-gradient(90deg, transparent, rgba(91,43,143,.16), rgba(255,255,255,.9), transparent); }
.nav-left, .nav-right { display: flex; align-items: center; }
.nav-left { gap: .75rem; }
.nav-right { gap: .7rem; }
.nav-title-group { display: flex; flex-direction: column; gap: .18rem; }
.nav-title { font-size: 1rem; line-height: 1.1; font-weight: 820; color: #35203f; letter-spacing: .02em; }
.nav-subtitle { color: #aa96af; font-size: .5rem; font-weight: 800; letter-spacing: .13em; }
.nav-back-icon, .nav-history-icon { font-size: 1.35rem; color: #5b2b8f; }
.nav-online { display: flex; align-items: center; gap: .3rem; padding: .42rem .55rem; border-radius: .7rem; color: #6c5772; background: rgba(255,255,255,.62); font-size: .58rem; font-weight: 800; }
.nav-online-dot, .panel-status-dot { width: .32rem; height: .32rem; border-radius: 50%; background: #aee65e; box-shadow: 0 0 8px rgba(174,230,94,.8); }

.welcome-center { flex: 1; padding: .95rem 1rem calc(var(--tabbar-safe) + 1rem); overflow-y: auto; box-sizing: border-box; }
.welcome-content { width: 100%; display: flex; flex-direction: column; align-items: stretch; }

.assistant-dock {
  position: relative;
  overflow: hidden;
  min-height: 4.6rem;
  padding: .62rem .7rem;
  display: flex;
  align-items: center;
  gap: .78rem;
  border: 1px solid rgba(255,255,255,.25);
  border-radius: 2rem;
  color: #fff;
  background: linear-gradient(145deg, #7241a4 0%, var(--yxg-violet) 48%, #48216f 100%);
  box-shadow: 0 1.05rem 2.25rem rgba(91,43,143,.18), inset 0 1px 0 rgba(255,255,255,.27);
  transform: translateZ(0);
  transition: transform var(--yxg-touch-out) var(--yxg-spring-out), box-shadow var(--yxg-touch-out) var(--yxg-spring-out);
}
.assistant-dock::before {
  content: '';
  position: absolute;
  inset: -55% auto -55% -35%;
  width: 34%;
  pointer-events: none;
  filter: blur(9px);
  transform: skewX(-18deg);
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.36), transparent);
  animation: heroMirrorSweep 10.5s cubic-bezier(.3,.02,.2,1) infinite;
}
.assistant-dock > * { position: relative; z-index: 1; }
.assistant-dock-icon { width: 3.25rem; height: 3.25rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border: 1px solid rgba(255,255,255,.2); border-radius: 1.35rem; background: linear-gradient(145deg, rgba(255,255,255,.2), rgba(255,255,255,.08)); box-shadow: inset 0 1px 0 rgba(255,255,255,.28); }
.assistant-sparkle { color: #fff; font-size: 1.55rem; font-variation-settings: 'FILL' 1; }
.assistant-dock-copy { flex: 1; min-width: 0; }
.assistant-dock-title { display: block; color: #fff; font-size: .94rem; font-weight: 820; letter-spacing: -.015em; }
.assistant-dock-caption { display: block; margin-top: .24rem; color: rgba(255,255,255,.64); font-size: .62rem; font-weight: 650; }
.assistant-dock-action { width: 3rem; height: 3rem; display: flex; align-items: center; justify-content: center; border-radius: 1.5rem; background: rgba(255,255,255,.08); box-shadow: inset 0 1px 0 rgba(255,255,255,.16); }

.knowledge-strip {
  margin-top: .65rem;
  min-height: 3.2rem;
  padding: 0 .78rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid rgba(255,255,255,.86);
  border-radius: 1.3rem;
  background: linear-gradient(145deg, rgba(255,255,255,.86), rgba(248,242,251,.66));
  backdrop-filter: blur(20px) saturate(155%);
  -webkit-backdrop-filter: blur(20px) saturate(155%);
  box-shadow: inset 0 1px 0 #fff, inset 0 -1px 0 rgba(91,43,143,.07), 0 .55rem 1.25rem rgba(91,43,143,.06);
  transform: translateZ(0);
  transition: transform var(--yxg-touch-out) var(--yxg-spring-out), background .3s ease;
}
.knowledge-strip-leading,
.knowledge-strip-action { display: flex; align-items: center; }
.knowledge-strip-leading { gap: .56rem; }
.knowledge-strip-icon { color: var(--yxg-violet); font-size: 1.14rem; }
.knowledge-strip-copy { display: flex; align-items: baseline; gap: .4rem; }
.knowledge-strip-title { color: #55475b; font-size: .69rem; font-weight: 790; }
.knowledge-strip-status { color: #a190a7; font-size: .55rem; }
.knowledge-sync-badge { min-height: 1.72rem; padding: 0 .52rem; display: flex; align-items: center; gap: .22rem; border: 1px solid rgba(91,43,143,.1); border-radius: .86rem; color: #796780; background: rgba(255,255,255,.58); font-size: .47rem; font-weight: 720; white-space: nowrap; }
.knowledge-sync-icon { color: var(--yxg-violet); font-size: .72rem; }

.focus-heading { padding: 1.45rem .35rem 1rem; text-align: center; }
.focus-title { display: block; color: #3e2848; font-size: 1.45rem; line-height: 1.16; font-weight: 830; letter-spacing: -.045em; }

.welcome-composer { width: 100%; }
.welcome-composer .input-wrapper { min-height: 3.65rem; border-color: rgba(91,43,143,.17); border-radius: 1.85rem; padding: .35rem .35rem .35rem 1rem; box-shadow: inset 0 1px 0 #fff, inset 0 -1px 0 rgba(91,43,143,.08), 0 0 0 2px rgba(221,202,235,.34), 0 .95rem 2rem rgba(91,43,143,.12); }
.welcome-composer .send-btn { width: 2.95rem; height: 2.95rem; border-radius: 1.5rem; }
.send-error { margin: .55rem .4rem 0; display: flex; align-items: center; gap: .35rem; color: #9b6575; font-size: .58rem; }
.send-error-icon { font-size: .9rem; }
.send-error-text { flex: 1; }
.send-error-action { color: var(--yxg-violet); font-weight: 800; }

.recent-block { margin-top: 1rem; }
.recent-heading { padding: 0 .28rem .52rem; display: flex; align-items: center; justify-content: space-between; color: #786a7c; font-size: .62rem; font-weight: 790; letter-spacing: .04em; }
.recent-heading-action { color: #927b9c; font-size: .58rem; font-weight: 720; letter-spacing: 0; }
.recent-empty { position: relative; min-height: 7.25rem; padding: .85rem; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: .4rem; border: 1px solid rgba(91,43,143,.06); border-radius: 1.25rem; text-align: center; background: rgba(255,255,255,.44); box-shadow: inset 0 1px 0 rgba(255,255,255,.78); }
.recent-list { overflow: hidden; border-radius: 1.25rem; background: rgba(255,255,255,.58); box-shadow: inset 0 1px 0 rgba(255,255,255,.84); }
.recent-item { position: relative; min-height: 3.8rem; padding: .5rem .72rem; display: flex; align-items: center; gap: .62rem; transition: background .2s ease, transform .2s ease; }
.recent-item + .recent-item { box-shadow: inset 0 1px 0 rgba(91,43,143,.07); }
.recent-item--pressed, .recent-item:active { background: rgba(239,226,247,.68); transform: scale(.988); }
.recent-empty-icon { width: 2.5rem; height: 2.5rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: .9rem; color: #aa8cbd; background: rgba(238,224,247,.7); }
.recent-empty-icon .material-symbols-outlined { font-size: 1.15rem; }
.recent-empty-copy { min-width: 0; }
.recent-empty-title { display: block; color: #66576c; font-size: .67rem; font-weight: 790; }
.recent-empty-caption { display: block; margin-top: .22rem; color: #a293a7; font-size: .53rem; line-height: 1.45; }
.recent-empty-arrow { position: absolute; right: .78rem; top: 50%; color: #b3a4b8; font-size: 1rem; transform: translateY(-50%); }

.chat-container {
  /* uni-app 的 scroll-view 在 flex 布局中默认 min-height:auto，会被长回答
     直接撑到内容高度；父级 overflow:hidden 后，超出的回答就无法触达。 */
  flex: 1 1 0;
  width: 100%;
  height: 0;
  min-height: 0;
  padding: 0 1rem;
  box-sizing: border-box;
  overflow: hidden;
  overscroll-behavior-y: contain;
}
.msg-wrapper { display: flex; flex-direction: column; margin-bottom: 1.5rem; }

.user-msg { align-items: flex-end; }
.user-bubble { background: #5b2b8f; color: #fff; border-radius: 1rem 1rem 0 1rem; max-width: 85%; padding: 1rem 1.25rem; box-shadow: 0 0.5rem 1rem rgba(91,33,143,.12); font-size: 0.9375rem; line-height: 1.7; }
.msg-time { font-size: 0.6875rem; font-weight: 700; color: #94a3b8; margin-top: 0.5rem; padding: 0 0.5rem; }

.ai-msg { width: 100%; align-items: flex-start; }
.ai-header { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.5rem; padding: 0 0.5rem; }
.ai-avatar { width: 1.5rem; height: 1.5rem; border-radius: 0.75rem; background: #5b2b8f; display: flex; align-items: center; justify-content: center; }
.bot-icon { font-size: 0.875rem; color: #fff; }
.ai-name { font-size: 0.75rem; font-weight: 700; color: #5b21b6; letter-spacing: 0.0625rem; }
.ai-bubble { width: 100%; box-sizing: border-box; background: rgba(255,255,255,.86); color: #2f2e32; border-radius: 1.15rem 1.15rem 1.15rem .22rem; padding: 1.25rem 1.15rem 1.1rem; box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 .6rem 1.8rem rgba(91,43,143,.07); border-left: .22rem solid #5b2b8f; font-size: 0.9375rem; line-height: 1.7; backdrop-filter: blur(14px); -webkit-backdrop-filter: blur(14px); }
.ai-bubble.streaming { box-shadow: inset 0 1px 0 rgba(255,255,255,.94), 0 0 0 1px rgba(91,43,143,.10), 0 10px 26px rgba(91,43,143,.10); }

.teacher-avatar { width: 1.5rem; height: 1.5rem; border-radius: 0.75rem; background: linear-gradient(135deg, #059669, #34d399); display: flex; align-items: center; justify-content: center; }
.teacher-icon { font-size: 0.875rem; color: #fff; }
.teacher-name { font-size: 0.75rem; font-weight: 700; color: #059669; letter-spacing: 0.0625rem; }
.teacher-bubble { background: #ffffff; color: #2f2e32; border-radius: 1rem 1rem 1rem 0; max-width: 90%; padding: 1.25rem 1.5rem; box-shadow: 0 0.125rem 0.5rem rgba(0,0,0,0.02); border-left: 0.25rem solid #059669; font-size: 0.9375rem; line-height: 1.7; }

.citations { margin-top: 1.1rem; padding: .9rem .85rem .35rem; border-radius: .95rem; background: #f4eff7; box-shadow: inset 0 1px 0 rgba(255,255,255,.84); animation: sourceReveal .45s cubic-bezier(.2,.75,.2,1) both; }
.cit-header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: .55rem; }
.cit-heading { display: flex; flex-direction: column; gap: .18rem; }
.cit-kicker { color: #a88ab9; font-size: .46rem; font-weight: 850; letter-spacing: .15em; }
.cit-title { color: #4d296c; font-size: .74rem; font-weight: 850; }
.cit-count { padding: .25rem .45rem; border-radius: .5rem; color: #765889; background: rgba(255,255,255,.65); font-size: .5rem; font-weight: 800; }
.cit-list { display: flex; flex-direction: column; }
.cit-item { display: flex; align-items: center; gap: .65rem; min-height: 3.35rem; padding: .28rem .1rem; color: #4d296c; cursor: pointer; }
.cit-item + .cit-item { box-shadow: inset 0 1px 0 rgba(91,43,143,.08); }
.cit-item:active { opacity: .72; transform: translateX(2px); }
.cit-index { width: 1.55rem; height: 1.55rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: .55rem; color: #5b2b8f; background: rgba(255,255,255,.82); font-size: .52rem; font-weight: 900; box-shadow: inset 0 1px 0 #fff; }
.cit-index.official { color: #fff; background: #5b2b8f; box-shadow: inset 0 1px 0 rgba(255,255,255,.25), 0 .3rem .7rem rgba(91,43,143,.15); }
.cit-copy { flex: 1; min-width: 0; }
.cit-text { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #4b3a52; font-size: .68rem; font-weight: 760; }
.cit-meta-row { display: flex; align-items: center; flex-wrap: wrap; gap: .24rem; margin-top: .28rem; }
.cit-meta { color: #9a8ca0; font-size: .48rem; }
.cit-meta.historical { color: #9b6b43; }
.cit-meta.screenshot { color: #5b2b8f; font-weight: 780; }
.cit-badge { padding: .14rem .28rem; border-radius: .32rem; color: #7c6b84; background: rgba(255,255,255,.64); font-size: .45rem; font-weight: 780; }
.cit-badge.verified { color: #56306e; background: rgba(225,208,237,.72); }
.cit-action { min-width: 2.7rem; min-height: 2rem; padding: .28rem .4rem; display: flex; align-items: center; justify-content: center; gap: .18rem; flex-shrink: 0; border-radius: .62rem; color: #807487; background: rgba(255,255,255,.58); font-size: .48rem; font-weight: 800; }
.cit-action.official { color: #5b2b8f; background: rgba(230,215,241,.72); }
.ext-link-icon { flex-shrink: 0; font-size: .72rem; color: currentColor; }
.answer-notice { display: flex; align-items: flex-start; gap: .38rem; margin-top: .72rem; padding: .62rem .68rem; border-radius: .72rem; color: #88788d; background: rgba(248,245,249,.86); font-size: .52rem; line-height: 1.55; }
.notice-icon { flex-shrink: 0; margin-top: .02rem; color: #8d6aa2; font-size: .72rem; }
.answer-freshness { display: flex; align-items: center; gap: .28rem; margin: .48rem .5rem 0; color: #95879a; font-size: .56rem; font-weight: 650; line-height: 1.4; }
.answer-freshness-icon { color: #826691; font-size: .72rem; }
@keyframes sourceReveal { from { opacity: 0; transform: translateY(.5rem); } to { opacity: 1; transform: translateY(0); } }

.typing-animation { display: flex; gap: 0.25rem; padding: 0.25rem 0; }
.dot { width: 0.375rem; height: 0.375rem; background: #5b21b6; border-radius: 50%; animation: typing 1.4s infinite ease-in-out; }
.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.cursor { display: inline-block; color: #5b21b6; animation: blink 1s infinite; margin-left: 0.125rem; }
@keyframes blink { 0%, 50% { opacity: 1; } 51%, 100% { opacity: 0; } }

/* 预留 input-bar 自身 ~4.5rem + tab bar(var) 的滚动空间 */
.bottom-spacer { height: calc(var(--tabbar-safe) + 6rem); }

/* input bar 停在 tab bar 正上方 — 通过 var(--tabbar-safe) 消费 tokens.scss
   的单一源, 不再硬编码 3.5rem 这类会脱节的值 */
.bottom-area {
  position: fixed;
  bottom: var(--tabbar-safe);
  left: 50%;
  right: auto;
  width: min(100vw, 430px);
  max-width: 100vw;
  transform: translateX(-50%);
  z-index: 40;
  background: linear-gradient(180deg, rgba(244,239,233,.18), rgba(255,255,255,.62));
  backdrop-filter: blur(26px) saturate(165%);
  -webkit-backdrop-filter: blur(26px) saturate(165%);
  padding: 0.75rem 1rem;
}
.call-menu-overlay { position: absolute; bottom: 100%; left: 0; right: 0; display: flex; justify-content: flex-end; padding: 0 1rem 0.5rem; z-index: 50; }
.call-menu { background: #fff; border-radius: 0.75rem; box-shadow: 0 0.25rem 1.5rem rgba(0,0,0,0.12); overflow: hidden; min-width: 8rem; }
.call-menu-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; }
.call-menu-item:active { background: #f4eff5; }
.call-menu-icon { font-size: 1.125rem; color: #5b21b6; }
.call-menu-text { font-size: 0.875rem; font-weight: 600; color: #2f2e32; }

.system-message { display: flex; justify-content: center; padding: 0.5rem 0; font-size: 0.75rem; color: #94a3b8; font-style: italic; }

.input-wrapper { position: relative; overflow: hidden; display: flex; align-items: center; gap: 0.5rem; background: linear-gradient(145deg, rgba(255,255,255,.94), rgba(250,245,252,.76)); border: 1px solid rgba(255,255,255,.92); border-radius: 1.25rem; padding: 0.38rem 0.38rem 0.38rem 1rem; backdrop-filter: blur(24px) saturate(155%); -webkit-backdrop-filter: blur(24px) saturate(155%); box-shadow: inset 0 1px 0 #fff, inset 0 -1px 0 rgba(91,43,143,.08), 0 .75rem 1.8rem rgba(91,43,143,.11); }
.input-wrapper::before { content: ''; position: absolute; inset: 0 auto 0 -28%; width: 24%; pointer-events: none; filter: blur(7px); transform: skewX(-18deg); background: linear-gradient(90deg, transparent, rgba(255,255,255,.9), rgba(214,180,235,.34), transparent); animation: composerMirrorSweep 8.8s cubic-bezier(.3,.02,.2,1) infinite; }
.input-wrapper > * { position: relative; z-index: 1; }
.input { flex: 1; background: transparent; border: none; font-size: 0.875rem; color: #2f2e32; }
.send-btn { width: 2.5rem; height: 2.5rem; border-radius: 1.25rem; background: linear-gradient(145deg, #7140a1, var(--yxg-violet) 58%, #48216f); display: flex; align-items: center; justify-content: center; box-shadow: inset 0 1px 0 rgba(255,255,255,.28), 0 7px 16px rgba(91,43,143,.18); transform: translateZ(0); transition: transform var(--yxg-touch-out) var(--yxg-spring-out), box-shadow var(--yxg-touch-out) var(--yxg-spring-out), filter .24s ease; }
.send-btn:active, .send-btn--pressed { transform: translateY(1px) scale(.94); transition-duration: var(--yxg-touch-in); box-shadow: inset 0 3px 9px rgba(35,12,58,.26), 0 3px 8px rgba(91,43,143,.13); filter: saturate(1.06) brightness(.98); }
.send-btn.disabled { opacity: 0.5; }
.send-btn.streaming { background: #b22b89; box-shadow: 0 0 0 5px rgba(178,43,137,.14); animation: stopPulse 1.4s ease-in-out infinite; }
@keyframes stopPulse { 0%,100% { transform: scale(1); } 50% { transform: scale(.94); } }
.send-icon { font-size: 1.25rem; color: #fff; }

.markdown-body { font-size: 0.875rem; line-height: 1.6; }
.markdown-body :deep(p) { margin-bottom: 0.5rem; }
.markdown-body :deep(ul) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: disc; }
.markdown-body :deep(ol) { padding-left: 1rem; margin-bottom: 0.5rem; list-style-type: decimal; }
.markdown-body :deep(li) { margin-bottom: 0.25rem; }
.markdown-body :deep(strong) { font-weight: 700; color: #5b21b6; }

.answer-support { width: 100%; box-sizing: border-box; display: flex; align-items: center; gap: .65rem; margin-top: .65rem; padding: .7rem .7rem; border-radius: 1rem; color: #fff; background: #5b2b8f; box-shadow: 0 .7rem 1.6rem rgba(91,43,143,.16), inset 0 1px 0 rgba(255,255,255,.16); animation: sourceReveal .5s .08s cubic-bezier(.2,.75,.2,1) both; }
.answer-support:active { transform: scale(.985); }
.support-icon-wrap { width: 2.3rem; height: 2.3rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: .8rem; background: rgba(255,255,255,.15); }
.support-icon { color: #fff; font-size: 1.15rem; }
.support-copy { flex: 1; min-width: 0; }
.support-kicker { display: block; color: rgba(255,255,255,.5); font-size: .44rem; font-weight: 850; letter-spacing: .12em; }
.support-title { display: block; margin-top: .22rem; color: #fff; font-size: .68rem; font-weight: 790; }
.support-action { display: flex; align-items: center; gap: .12rem; flex-shrink: 0; padding: .55rem .65rem; border-radius: .7rem; color: #4a1c75; background: rgba(255,255,255,.92); font-size: .58rem; font-weight: 850; }
.support-arrow { font-size: .75rem; }
.answer-support-done { color: #315d2e; background: #edf7e8; box-shadow: inset 0 1px 0 #fff; }
.answer-support-done .support-kicker { color: #79a470; }
.answer-support-done .support-title { color: #315d2e; }
.call-done-icon { font-size: 1.125rem; color: #1e8e3e; }

@keyframes heroMirrorSweep {
  0%, 56% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  62% { opacity: .75; }
  76% { opacity: 0; transform: translateX(410%) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(410%) skewX(-18deg); }
}
@keyframes composerMirrorSweep {
  0%, 42% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  49% { opacity: .86; }
  67% { opacity: 0; transform: translateX(560%) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(560%) skewX(-18deg); }
}

/* R10: 关联问题推荐 */
.suggestions-area { padding: 0 .5rem; margin-bottom: 1.5rem; animation: sourceReveal .42s cubic-bezier(.2,.75,.2,1) both; }
.suggestions-header { display: flex; align-items: center; gap: 0.375rem; margin-bottom: 0.625rem; padding: 0 0.25rem; }
.suggestions-icon { font-size: 1rem; color: #6f3a91; }
.suggestions-heading { display: flex; flex-direction: column; gap: .08rem; }
.suggestions-kicker { color: #a88ab9; font-size: .44rem; font-weight: 850; letter-spacing: .13em; }
.suggestions-title { font-size: 0.75rem; font-weight: 760; color: #56306e; }
.suggestions-list { display: flex; flex-direction: column; gap: .55rem; }
.suggestion-chip { position: relative; min-height: 2.75rem; box-sizing: border-box; overflow: hidden; display: flex; align-items: center; justify-content: space-between; padding: .68rem .88rem .68rem 1rem; border: 1px solid rgba(255,255,255,.82); border-radius: 1rem; background: linear-gradient(145deg, rgba(255,255,255,.82), rgba(239,229,247,.58)); box-shadow: inset 0 1px 0 #fff, 0 .38rem 1rem rgba(91,43,143,.08); backdrop-filter: blur(16px) saturate(145%); -webkit-backdrop-filter: blur(16px) saturate(145%); transition: transform .2s cubic-bezier(.22,.78,.22,1), box-shadow .2s ease, background .2s ease; }
.suggestion-chip:first-child::before { content: ''; position: absolute; inset: -45% auto -45% -28%; width: 24%; pointer-events: none; transform: skewX(-18deg); background: linear-gradient(90deg, transparent, rgba(255,255,255,.86), rgba(206,177,226,.26), transparent); animation: followupGlint 7.2s ease-in-out infinite; }
.suggestion-chip > * { position: relative; z-index: 1; }
.suggestion-chip:active { background: linear-gradient(145deg, rgba(238,226,247,.86), rgba(255,255,255,.72)); transform: translateY(1px) scale(.985); box-shadow: inset 0 2px 6px rgba(74,31,104,.11), 0 .18rem .55rem rgba(91,43,143,.07); }
.suggestion-text { flex: 1; font-size: .78rem; font-weight: 720; color: #56306e; line-height: 1.45; }
.suggestion-arrow { font-size: 0.875rem; color: #5b21b6; margin-left: 0.5rem; flex-shrink: 0; opacity: 0.6; }
@keyframes followupGlint { 0%, 54% { opacity: 0; transform: translateX(0) skewX(-18deg); } 61% { opacity: .82; } 75%, 100% { opacity: 0; transform: translateX(560%) skewX(-18deg); } }

@media (prefers-reduced-motion: reduce) {
  .welcome-panel::before,
  .input-wrapper::before,
  .suggestion-chip:first-child::before { animation: none; }
  .suggestions-area { animation: none; }
}

@media (max-width: 350px) {
  .welcome-center { padding-left: .82rem; padding-right: .82rem; }
  .assistant-dock { min-height: 4.25rem; }
  .assistant-dock-icon { width: 2.9rem; height: 2.9rem; }
  .focus-heading { padding-top: 1.1rem; }
  .focus-title { font-size: 1.28rem; }
  .recent-empty { min-height: 7rem; }
}

/* 来源弹层 (可拖拽全屏) */
.source-overlay {
  position: fixed;
  top: 0;
  bottom: 0;
  left: 50%;
  width: min(100vw, 430px);
  max-width: 100vw;
  transform: translateX(-50%);
  background: rgba(0,0,0,0.45);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}
.source-popup { width: 100%; max-width: 100%; overflow: hidden; border: 1px solid rgba(255,255,255,.78); border-bottom: 0; background: rgba(252,249,253,.96); border-radius: 1.5rem 1.5rem 0 0; display: flex; flex-direction: column; box-shadow: 0 -1.2rem 3rem rgba(45,21,63,.16), inset 0 1px 0 #fff; backdrop-filter: blur(24px) saturate(150%); -webkit-backdrop-filter: blur(24px) saturate(150%); transition: height .24s cubic-bezier(.22,.78,.22,1); }
.source-popup-drag-bar { display: flex; justify-content: center; padding: 0.5rem 0 0.25rem; cursor: grab; }
.drag-indicator { width: 2rem; height: 0.25rem; border-radius: 0.125rem; background: #d1d5db; }
.source-popup-header { display: flex; justify-content: space-between; align-items: center; gap: .7rem; padding: .55rem 1.15rem .8rem; }
.source-popup-title { font-size: .92rem; font-weight: 820; line-height: 1.35; color: #302735; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-header-actions { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }
.source-expand { font-size: 1.125rem; color: #94a3b8; }
.source-close { font-size: 1.25rem; color: #94a3b8; }
.source-popup-body { padding: .2rem 1.05rem 1.4rem; flex: 1; overflow: hidden; }
.source-proof { margin-bottom: .7rem; padding: .82rem; border: 1px solid rgba(91,43,143,.10); border-radius: 1.05rem; background: rgba(255,255,255,.72); box-shadow: inset 0 1px 0 #fff; }
.source-destination { display: flex; align-items: center; gap: .7rem; margin-bottom: .72rem; }
.source-destination-icon { width: 2.45rem; height: 2.45rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: .82rem; color: #fff; background: #5b2b8f; box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 .42rem 1rem rgba(91,43,143,.16); }
.source-destination-icon .material-symbols-outlined { font-size: 1.15rem; font-variation-settings: 'FILL' 1; }
.source-destination-copy { min-width: 0; display: flex; flex-direction: column; }
.source-destination-kicker { color: #9c86a7; font-size: .48rem; font-weight: 850; letter-spacing: .12em; }
.source-destination-title { margin-top: .18rem; color: #3d2b45; font-size: .76rem; font-weight: 850; }
.source-destination-host { margin-top: .12rem; overflow: hidden; color: #8b7b91; font-size: .54rem; text-overflow: ellipsis; white-space: nowrap; }
.source-proof-meta { display: flex; flex-wrap: wrap; align-items: center; gap: .35rem .5rem; color: #8d7e92; font-size: .56rem; line-height: 1.4; }
.source-proof-badge { padding: .2rem .36rem; border-radius: .38rem; color: #75657c; background: rgba(255,255,255,.8); font-weight: 780; }
.source-proof-badge.verified { color: #56306e; background: #e8dced; }
.source-proof-image { display: block; width: 100%; margin-top: .72rem; border-radius: .72rem; box-shadow: 0 .4rem 1.1rem rgba(65,36,80,.1); }
.source-open-button { position: relative; margin-top: .72rem; min-height: 3.35rem; padding: .62rem .75rem .62rem .82rem; display: flex; align-items: center; justify-content: space-between; overflow: hidden; border: 1px solid rgba(255,255,255,.26); border-radius: .92rem; color: #fff; background: #5b2b8f; box-shadow: 0 .5rem 1.15rem rgba(91,43,143,.18), inset 0 1px 0 rgba(255,255,255,.2); cursor: pointer; transition: transform .18s cubic-bezier(.22,.78,.22,1), background .18s ease, box-shadow .18s ease; }
.source-open-button::after { content: ''; position: absolute; inset: -50% auto -50% -30%; width: 34%; transform: skewX(-18deg); background: linear-gradient(90deg, transparent, rgba(255,255,255,.34), transparent); animation: sourceCtaGlint 5.8s ease-in-out infinite; }
.source-open-button--pressed,
.source-open-button:active { transform: scale(.985); background: #4d2379; box-shadow: 0 .25rem .7rem rgba(91,43,143,.14), inset 0 2px 8px rgba(32,10,52,.22); }
.source-open-button > * { position: relative; z-index: 1; }
.source-open-button > view { min-width: 0; display: flex; flex-direction: column; }
.source-open-kicker { color: rgba(255,255,255,.58); font-size: .43rem; font-weight: 850; letter-spacing: .14em; }
.source-open-label { margin-top: .15rem; color: #fff; font-size: .68rem; font-weight: 850; }
.source-open-button .material-symbols-outlined { font-size: 1rem; }
.source-link-missing { margin-top: .72rem; min-height: 2.65rem; padding: .58rem .65rem; display: flex; align-items: center; gap: .48rem; border-radius: .82rem; color: #7b6b82; background: #f4eff6; font-size: .56rem; line-height: 1.45; }
.source-link-missing .material-symbols-outlined { flex-shrink: 0; color: #8f6ba2; font-size: .86rem; }
.source-excerpt-toggle { min-height: 3.1rem; padding: .65rem .72rem; display: flex; align-items: center; justify-content: space-between; border-radius: .9rem; color: #493a50; background: rgba(255,255,255,.62); cursor: pointer; }
.source-excerpt-toggle > view { display: flex; flex-direction: column; }
.source-excerpt-title { font-size: .68rem; font-weight: 850; }
.source-excerpt-caption { margin-top: .16rem; color: #95899a; font-size: .5rem; }
.source-excerpt-toggle .material-symbols-outlined { color: #6d4084; font-size: 1rem; }
.source-markdown { margin-top: .62rem; padding: .82rem; border-radius: .9rem; background: rgba(255,255,255,.7); font-size: 0.875rem; color: #475569; line-height: 1.8; animation: sourceReveal .3s cubic-bezier(.2,.75,.2,1) both; }
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
@keyframes sourceCtaGlint {
  0%, 52% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  58% { opacity: .72; }
  70%, 100% { opacity: 0; transform: translateX(430%) skewX(-18deg); }
}

@media (prefers-reduced-motion: reduce) {
  .source-open-button::after { animation: none; }
  .source-popup,
  .source-markdown { transition: none; animation: none; }
}
</style>
