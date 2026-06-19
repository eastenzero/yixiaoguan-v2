<template>
  <view class="msg-wrapper">
    <view v-if="message.role === 'user'" class="user-msg">
      <view class="msg-bubble user-bubble">
        <text>{{ message.content }}</text>
      </view>
      <text class="msg-time">{{ formatTime(message.timestamp) }}</text>
    </view>

    <view v-else-if="message.role === 'system'" class="system-message">
      <text>{{ message.content }}</text>
    </view>

    <view v-else class="assistant-msg">
      <view class="assistant-header">
        <view :class="['avatar', message.role === 'teacher' ? 'avatar-teacher' : 'avatar-ai']">
          <uni-icons :type="message.role === 'teacher' ? 'staff' : 'chatboxes'" size="14" color="#ffffff" />
        </view>
        <text :class="['assistant-name', message.role === 'teacher' ? 'teacher-name' : 'ai-name']">
          {{ message.role === 'teacher' ? '老师回复' : '医小管 AI' }}
        </text>
      </view>

      <view :class="['msg-bubble', message.role === 'teacher' ? 'teacher-bubble' : 'ai-bubble']">
        <view v-if="message.isStreaming && !message.content" class="typing-animation">
          <view class="dot" /><view class="dot" /><view class="dot" />
        </view>
        <MarkdownContent v-else class="markdown-body" :content="message.content" />
        <text v-if="message.isStreaming && message.content" class="cursor">|</text>

        <view v-if="message.sources && message.sources.length && !message.isStreaming" class="citations">
          <view class="cit-header">
            <uni-icons type="paperclip" size="14" color="#5b21b6" />
            <text>参考资料</text>
          </view>
          <view class="cit-list">
            <view
              v-for="(source, index) in message.sources"
              :key="`${source.title}-${index}`"
              class="cit-item"
              @click="$emit('source-click', source)"
            >
              <text class="cit-text">{{ index + 1 }}. {{ source.title }}</text>
              <uni-icons type="right" size="13" color="#7742a6" />
            </view>
          </view>
        </view>
      </view>

      <text class="msg-time">{{ formatTime(message.timestamp) }}</text>

      <UnansweredInviteCard
        v-if="message.unanswered_invite && !message.unanswered_invite.dismissed"
        :conv_id="message.unanswered_invite.conv_id"
        :message_id="message.unanswered_invite.message_id"
        @submitted="$emit('unanswered-closed', message, true)"
        @dismissed="$emit('unanswered-closed', message, false)"
      />

      <view
        v-if="!message.isStreaming && isRefusal && conversationStatus === 'ai_serving'"
        class="inline-call-teacher"
        @click="$emit('call-teacher')"
      >
        <uni-icons type="staff" size="17" color="#ffffff" />
        <text class="call-inline-text">{{ escalateLoading ? '呼叫中...' : '转人工服务' }}</text>
      </view>
      <view v-if="conversationStatus === 'pending_teacher' && isRefusal" class="inline-call-done">
        <uni-icons type="checkmarkempty" size="17" color="#059669" />
        <text class="call-done-text">已通知老师，请耐心等待</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import MarkdownContent from '@/components/MarkdownContent.vue'
import UnansweredInviteCard from '@/components/UnansweredInviteCard.vue'
import type { ChatMessage, ConversationStatus, Source } from '@/types/chat'

const props = defineProps<{
  message: ChatMessage
  conversationStatus: ConversationStatus
  escalateLoading: boolean
  formatTime: (timestamp: number) => string
  isRefusalMsg: (message: ChatMessage) => boolean
}>()

defineEmits<{
  (event: 'source-click', source: Source): void
  (event: 'unanswered-closed', message: ChatMessage, submitted: boolean): void
  (event: 'call-teacher'): void
}>()

const isRefusal = computed(() => props.isRefusalMsg(props.message))
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.msg-wrapper {
  display: flex;
  flex-direction: column;
  margin-bottom: 18px;
}

.user-msg {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.assistant-msg {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.msg-bubble {
  box-sizing: border-box;
  max-width: 88%;
  padding: 14px 16px;
  font-size: 14px;
  line-height: 1.7;
}

.user-bubble {
  color: $on-primary;
  border-radius: 20px 20px 6px 20px;
  background: $gradient-cta;
}

.ai-bubble,
.teacher-bubble {
  color: $on-surface;
  border-radius: 20px 20px 20px 6px;
  background: rgba(255, 255, 255, 0.86);
}

.ai-bubble {
  border-left: 4px solid $primary;
}

.teacher-bubble {
  border-left: 4px solid $success;
}

.assistant-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-left: 4px;
}

.avatar {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 13px;
}

.avatar-ai {
  background: $gradient-cta;
}

.avatar-teacher {
  background: linear-gradient(135deg, #059669, #34d399);
}

.assistant-name {
  font-size: 12px;
  font-weight: 800;
}

.ai-name {
  color: $primary;
}

.teacher-name {
  color: $success;
}

.msg-time {
  margin-top: 6px;
  padding: 0 6px;
  color: $outline;
  font-size: 11px;
  font-weight: 700;
}

.system-message {
  align-self: center;
  max-width: 90%;
  padding: 7px 12px;
  border-radius: 999px;
  background: $surface-container-low;
  color: $on-surface-variant;
  font-size: 12px;
  line-height: 1.45;
}

.typing-animation {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: $primary;
  animation: typing 1.4s infinite ease-in-out;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.cursor {
  display: inline-block;
  margin-left: 2px;
  color: $primary;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.citations {
  margin-top: 12px;
  padding: 10px;
  border-radius: 14px;
  background: $surface-container-low;
}

.cit-header {
  display: flex;
  align-items: center;
  gap: 5px;
  margin-bottom: 8px;
  color: $primary;
  font-size: 12px;
  font-weight: 800;
}

.cit-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.cit-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.62);
}

.cit-text {
  flex: 1;
  overflow: hidden;
  color: $secondary;
  font-size: 12px;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.inline-call-teacher,
.inline-call-done {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  padding: 9px 14px;
  border-radius: 999px;
}

.inline-call-teacher {
  color: #fff;
  background: $gradient-cta;
  box-shadow: 0 8px 18px rgba(91, 33, 182, 0.22);
}

.inline-call-teacher:active {
  transform: scale(0.97);
}

.call-inline-text,
.call-done-text {
  font-size: 13px;
  font-weight: 800;
}

.inline-call-done {
  background: rgba(5, 150, 105, 0.12);
}

.call-done-text {
  color: $success;
}
</style>
