<template>
  <scroll-view
    class="thread"
    scroll-y
    :scroll-top="scrollTop"
    :scroll-with-animation="true"
  >
    <view class="thread-inner">
      <ChatMessageBubble
        v-for="message in messages"
        :key="message.id"
        :message="message"
        :conversation-status="conversationStatus"
        :escalate-loading="escalateLoading"
        :format-time="formatTime"
        :is-refusal-msg="isRefusalMsg"
        @source-click="$emit('source-click', $event)"
        @unanswered-closed="(msg, submitted) => $emit('unanswered-closed', msg, submitted)"
        @call-teacher="$emit('call-teacher')"
      />

      <view v-if="isTyping" class="typing-row">
        <view class="typing-avatar">
          <uni-icons type="chatboxes" size="14" color="#ffffff" />
        </view>
        <view class="typing-bubble">
          <view class="typing-dot" /><view class="typing-dot" /><view class="typing-dot" />
        </view>
      </view>

      <ChatSuggestions
        v-if="suggestedQuestions.length && !isStreaming"
        :questions="suggestedQuestions"
        @select="$emit('suggestion-click', $event)"
      />

      <view class="bottom-spacer" />
    </view>
  </scroll-view>
</template>

<script setup lang="ts">
import ChatMessageBubble from './ChatMessageBubble.vue'
import ChatSuggestions from './ChatSuggestions.vue'
import type { ChatMessage, ConversationStatus, Source } from '@/types/chat'

defineProps<{
  messages: ChatMessage[]
  scrollTop: number
  isTyping: boolean
  isStreaming: boolean
  suggestedQuestions: string[]
  conversationStatus: ConversationStatus
  escalateLoading: boolean
  formatTime: (timestamp: number) => string
  isRefusalMsg: (message: ChatMessage) => boolean
}>()

defineEmits<{
  (event: 'source-click', source: Source): void
  (event: 'unanswered-closed', message: ChatMessage, submitted: boolean): void
  (event: 'call-teacher'): void
  (event: 'suggestion-click', question: string): void
}>()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.thread {
  flex: 1;
  min-height: 0;
  box-sizing: border-box;
}

.thread-inner {
  width: 100%;
  max-width: 720px;
  margin: 0 auto;
  box-sizing: border-box;
  padding: 14px 16px 0;
}

.typing-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 18px;
}

.typing-avatar {
  width: 26px;
  height: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 13px;
  background: $gradient-cta;
}

.typing-bubble {
  display: flex;
  gap: 4px;
  padding: 15px 18px;
  border-radius: 20px 20px 20px 6px;
  background: rgba(255, 255, 255, 0.86);
}

.typing-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: $primary;
  animation: typing 1.4s infinite ease-in-out;
}

.typing-dot:nth-child(1) { animation-delay: -0.32s; }
.typing-dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.bottom-spacer {
  height: calc(var(--tabbar-safe) + 88px);
}
</style>
