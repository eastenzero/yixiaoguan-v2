<template>
  <view class="question-detail-page">
    <TopAppBar title="提问详情" showBack @back="handleBack" />

    <scroll-view scroll-y class="main-content">
      <!-- Loading State -->
      <view v-if="loading" class="loading-container">
        <text class="loading-text">加载中...</text>
      </view>

      <template v-else-if="escalation">
        <!-- Student Info Card -->
        <view class="student-card animate-fade-up delay-1">
          <view class="avatar-wrapper">
            <view class="avatar-placeholder"></view>
            <view class="online-indicator"></view>
          </view>
          <view class="student-meta">
            <view class="student-header">
              <text class="student-name">学生 #{{ escalation.student_id }}</text>
              <view class="status-tag" :class="`status-${escalation.status}`">
                <text class="status-text">{{ getStatusText(escalation.status) }}</text>
              </view>
            </view>
            <text class="student-info-text">{{ escalation.title || '对话' }}</text>
          </view>
        </view>

        <!-- 完整会话消息（动态加载） -->
        <view class="chat-section">
          <view v-for="msg in conversationMessages" :key="msg.id" class="msg-item">
            <!-- 学生消息 -->
            <view v-if="msg.sender_type === 'student'" class="message-wrapper student-message">
              <view class="message-bubble student-bubble">
                <text class="message-text student-text">{{ msg.content }}</text>
              </view>
              <text class="message-time">{{ formatTime(msg.created_at) }}</text>
            </view>

            <!-- AI 消息 -->
            <view v-else-if="msg.sender_type === 'ai'" class="message-wrapper ai-message">
              <view class="ai-avatar">
                <IconBot :size="24" color="#702ae1" />
              </view>
              <view class="ai-content">
                <view class="message-bubble ai-bubble">
                  <text class="message-text ai-text">{{ msg.content }}</text>
                </view>
                <text class="message-time">{{ formatTime(msg.created_at) }}</text>
              </view>
            </view>

            <!-- 教师消息 -->
            <view v-else-if="msg.sender_type === 'teacher'" class="message-wrapper teacher-message">
              <view class="ai-avatar">
                <IconUserCheck :size="20" color="#702ae1" />
              </view>
              <view class="ai-content">
                <view class="message-bubble teacher-bubble">
                  <text class="message-text teacher-text">{{ msg.content }}</text>
                </view>
                <text class="message-time">{{ formatTime(msg.created_at) }}</text>
              </view>
            </view>

            <!-- 系统消息 -->
            <view v-else class="system-message">
              <view class="system-badge">
                <IconBell :size="16" color="#5d5b5f" />
                <text class="system-text">{{ msg.content }}</text>
              </view>
            </view>
          </view>

          <!-- 无消息时显示工单摘要作为兜底 -->
          <view v-if="conversationMessages.length === 0" class="message-wrapper student-message">
            <view class="message-bubble student-bubble">
              <text class="message-text student-text">{{ escalation.title }}</text>
            </view>
            <text class="message-time">{{ formatTime(escalation.created_at) }}</text>
          </view>

          <!-- 工单系统提示 -->
          <view class="system-message">
            <view class="system-badge">
              <IconBell :size="16" color="#5d5b5f" />
              <text class="system-text">学生已呼叫老师 — {{ formatTime(escalation.created_at) }}</text>
            </view>
          </view>
        </view>

        <!-- 刷新按钮（处理中时显示） -->
        <view v-if="escalation.status === 'teacher_serving'" class="refresh-bar" @click="loadMessages">
          <text class="refresh-text">{{ refreshing ? '刷新中...' : '↻ 点击刷新（已启用实时推送）' }}</text>
        </view>
      </template>

      <!-- Bottom padding for fixed action bar -->
      <view class="bottom-padding"></view>
    </scroll-view>

    <!-- Fixed Bottom Action Bar -->
    <view class="action-bar animate-fade-up delay-5">
      <!-- Status 0: 待处理 - 显示接单按钮 -->
      <view v-if="escalation && escalation.status === 'pending_teacher'" class="action-button" @click="handleAssign">
        <IconUserCheck :size="24" color="#f8f0ff" />
        <text class="action-text">{{ submitting ? '接单中...' : '接单处理' }}</text>
      </view>

      <!-- Status 1: 处理中 - 显示回复输入框和两个按钮 -->
      <view v-else-if="escalation && escalation.status === 'teacher_serving'" class="reply-section">
        <textarea
          v-model="replyText"
          class="reply-input"
          placeholder="请输入回复内容..."
          :maxlength="500"
          :disabled="submitting"
        />
        <view class="reply-buttons-row">
          <view class="reply-button reply-button--secondary" :class="{ 'reply-button--disabled': !replyText.trim() || submitting }" @click="handleReplyOnly">
            <IconMessage :size="20" color="#702ae1" />
            <text class="action-text-secondary">{{ submitting ? '发送中...' : '仅回复' }}</text>
          </view>
          <view class="reply-button" :class="{ 'reply-button--disabled': !replyText.trim() || submitting }" @click="handleResolve">
            <IconCheck :size="20" color="#f8f0ff" />
            <text class="action-text">{{ submitting ? '提交中...' : '回复并解决' }}</text>
          </view>
        </view>
      </view>

      <!-- Status 2: 已解决 - 显示已解决状态 -->
      <view v-else-if="escalation && escalation.status === 'resolved'" class="action-button action-button--disabled">
        <IconCheck :size="24" color="#f8f0ff" />
        <text class="action-text">已解决</text>
      </view>

      <!-- Status 3: 已关闭 -->
      <view v-else-if="escalation && escalation.status === 'closed'" class="action-button action-button--disabled">
        <text class="action-text">已关闭</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, onUnmounted, nextTick } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopAppBar from '../../components/TopAppBar.vue'
import { IconBot, IconBell, IconUserCheck, IconMessage, IconCheck } from '../../components/icons'
import { getConversation, listMessages, sendMessage, acceptConversation, resolveConversation } from '@/api/conversations'
import { getStatusText } from '@/utils/status-map'
import { wsManager } from '@/utils/websocket'

const escalation = ref<any>(null)
const loading = ref(false)
const convId = ref(0)
const replyText = ref('')
const submitting = ref(false)
const conversationMessages = ref<any[]>([])
const refreshing = ref(false)

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleString('zh-CN', { 
    month: '2-digit', 
    day: '2-digit', 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 加载详情
const loadDetail = async () => {
  if (!convId.value) return
  loading.value = true
  try {
    const res = await getConversation(convId.value)
    escalation.value = res
    await loadMessages()
    // WebSocket: join room for real-time updates
    wsManager.joinRoom(convId.value)
  } catch (e) {
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// 加载会话消息
const loadMessages = async () => {
  if (!convId.value) return
  refreshing.value = true
  try {
    const res = await listMessages(convId.value, 1, 200)
    conversationMessages.value = res.items || []
  } catch (e) {
    console.error('加载消息失败:', e)
  } finally {
    refreshing.value = false
  }
}

// WebSocket: 监听新消息
// dispatch 传入 msg.data（内层），直接访问字段
const onNewMessage = (data: any) => {
  if (data?.conv_id === convId.value) {
    conversationMessages.value.push({
      id: data.id,
      conversation_id: data.conv_id,
      sender_type: data.sender_type,
      sender_id: data.sender_id,
      content: data.content,
      created_at: data.created_at,
    })
  }
}

// WebSocket: 监听状态变更
const onStatusChange = (data: any) => {
  if (data?.conv_id === convId.value && escalation.value) {
    escalation.value.status = data.status || data.new_status
    loadMessages()
  }
}

const onEscalationNotify = (data: any) => {
  if (data?.conv_id === convId.value) {
    loadDetail()
  }
}

// 接单操作
const handleAssign = async () => {
  if (submitting.value) return
  submitting.value = true
  try {
    const res = await acceptConversation(convId.value)
    escalation.value = res
    uni.showToast({ title: '接单成功', icon: 'success' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '接单失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

// 仅回复（不结案）
const handleReplyOnly = async () => {
  if (!replyText.value.trim()) {
    uni.showToast({ title: '请输入回复内容', icon: 'none' })
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    await sendMessage(convId.value, replyText.value)
    uni.showToast({ title: '回复已发送', icon: 'success' })
    replyText.value = ''
  } catch (e: any) {
    uni.showToast({ title: e?.message || '回复失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

// 回复并解决
const handleResolve = async () => {
  if (!replyText.value.trim()) {
    uni.showToast({ title: '请输入回复内容', icon: 'none' })
    return
  }
  if (submitting.value) return
  submitting.value = true
  try {
    await sendMessage(convId.value, replyText.value)
    const res = await resolveConversation(convId.value)
    escalation.value = res
    uni.showToast({ title: '已解决', icon: 'success' })
    replyText.value = ''
  } catch (e: any) {
    uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

const handleBack = () => {
  uni.switchTab({ url: '/pages/questions/index' })
}

onLoad((options: any) => {
  convId.value = Number(options?.id || 0)
  if (convId.value) {
    loadDetail()
    // Register WS handlers
    wsManager.on('new_message', onNewMessage)
    wsManager.on('status_changed', onStatusChange)
    wsManager.on('escalation_notify', onEscalationNotify)
  }
})

onUnmounted(() => {
  if (convId.value) {
    wsManager.leaveRoom(convId.value)
  }
  wsManager.off('new_message', onNewMessage)
  wsManager.off('status_changed', onStatusChange)
  wsManager.off('escalation_notify', onEscalationNotify)
})
</script>

<style lang="scss" scoped>
.question-detail-page {
  min-height: 100vh;
  background: $surface;
}

.main-content {
  padding-top: 80px;
  padding-left: 16px;
  padding-right: 16px;
  padding-bottom: 160px;
  height: 100vh;
  box-sizing: border-box;
}

// Loading State
.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
}

.loading-text {
  font-size: 14px;
  color: $on-surface-variant;
}

// Student Card
.student-card {
  background: $surface-container-lowest;
  border-radius: 24px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 32px;
}

.avatar-wrapper {
  position: relative;
}

.avatar-placeholder {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: $surface-container;
  border: 2px solid rgba($primary, 0.1);
}

.online-indicator {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  background: #22c55e;
  border: 2px solid white;
  border-radius: 50%;
}

.student-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.student-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.student-name {
  font-size: 20px;
  font-weight: 700;
  color: $on-surface;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 9999px;

  .status-text {
    font-size: 12px;
    font-weight: 700;
  }

  &.status-pending_teacher {
    background: rgba($error-container, 0.1);
    .status-text { color: $error; }
  }

  &.status-teacher_serving,
  &.status-ai_serving {
    background: rgba($primary-container, 0.2);
    .status-text { color: $primary; }
  }

  &.status-resolved {
    background: rgba(#10b981, 0.1);
    .status-text { color: #10b981; }
  }

  &.status-closed {
    background: rgba($on-surface-variant, 0.1);
    .status-text { color: $on-surface-variant; }
  }
}

.student-info-text {
  font-size: 14px;
  color: $on-surface-variant;
}

// Chat Section
.chat-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

// Message Wrapper
.message-wrapper {
  display: flex;
  flex-direction: column;
}

.student-message {
  align-items: flex-end;
}

.ai-message,
.teacher-message {
  flex-direction: row;
  align-items: flex-start;
  gap: 12px;
}

// AI Avatar
.ai-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: $secondary-container;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.ai-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

// Message Bubbles
.message-bubble {
  max-width: 85%;
  padding: 16px;
  position: relative;
  overflow: hidden;
}

.student-bubble {
  background: $primary;
  border-radius: 16px 16px 0 16px;
  box-shadow: 0 8px 24px -4px rgba($primary, 0.12);
  align-self: flex-end;
}

.ai-bubble {
  background: white;
  border: 1px solid rgba($error, 0.2);
  border-radius: 16px 16px 16px 0;
  max-width: 90%;
}

.teacher-bubble {
  background: rgba($primary-container, 0.3);
  border: 1px solid rgba($primary, 0.2);
  border-radius: 16px 16px 16px 0;
  max-width: 90%;
}

.red-indicator {
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: $error;
}

.message-text {
  font-size: 14px;
  line-height: 1.6;
}

.student-text {
  color: $on-primary;
}

.ai-text {
  color: $on-surface;
  padding-left: 8px;
}

.teacher-text {
  color: $on-surface;
}

.message-time {
  font-size: 10px;
  color: $on-surface-variant;
  margin-top: 8px;
  padding-left: 4px;
}

// Refresh bar
.refresh-bar {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}

.refresh-text {
  font-size: 13px;
  color: $primary;
  font-weight: 600;
  padding: 6px 16px;
  background: rgba($primary, 0.08);
  border-radius: 9999px;
}

.msg-item {
  margin-bottom: 16px;
}

// System Message
.system-message {
  display: flex;
  justify-content: center;
}

.system-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  background: $surface-container;
  border-radius: 9999px;
  padding: 6px 16px;
}

.system-text {
  font-size: 12px;
  font-weight: 500;
  color: $on-surface-variant;
}

// Bottom padding
.bottom-padding {
  height: 40px;
}

// Action Bar
.action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px 24px calc(16px + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  z-index: 50;
}

.action-button {
  height: 56px;
  border-radius: 9999px;
  background: linear-gradient(135deg, $primary, $primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 12px 32px -4px rgba($primary, 0.2);
  transition: transform 0.2s ease;

  &:active {
    transform: scale(0.95);
  }

  &--disabled {
    background: linear-gradient(135deg, #9ca3af, #d1d5db);
    box-shadow: none;
    pointer-events: none;
  }
}

.action-text {
  font-size: 18px;
  font-weight: 700;
  color: $on-primary;
}

// Reply Section
.reply-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.reply-input {
  width: 100%;
  min-height: 80px;
  max-height: 120px;
  background: $surface-container;
  border-radius: 16px;
  padding: 12px 16px;
  font-size: 14px;
  color: $on-surface;
  box-sizing: border-box;
}

.reply-buttons-row {
  display: flex;
  gap: 12px;
}

.reply-button {
  flex: 1;
  height: 48px;
  border-radius: 9999px;
  background: linear-gradient(135deg, $primary, $primary-container);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 8px 24px -4px rgba($primary, 0.2);
  transition: all 0.2s ease;

  &:active {
    transform: scale(0.95);
  }

  &--secondary {
    background: white;
    border: 2px solid $primary;
    box-shadow: none;
  }

  &--disabled {
    background: linear-gradient(135deg, #9ca3af, #d1d5db);
    box-shadow: none;
    pointer-events: none;

    &.reply-button--secondary {
      background: white;
      border-color: #d1d5db;
    }
  }
}

.action-text-secondary {
  font-size: 16px;
  font-weight: 700;
  color: $primary;
}

// Animation delays
.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }
.delay-3 { animation-delay: 0.3s; }
.delay-4 { animation-delay: 0.4s; }
.delay-5 { animation-delay: 0.5s; }
</style>
