<template>
  <view class="chat-page">
    <view class="top-nav">
      <view class="nav-left" @click="goBack">
        <AppIcon name="arrow_back" class="nav-icon" />
        <text class="nav-title">医小管</text>
      </view>
      <view class="nav-right" @click="goToHistory">
        <AppIcon name="history" class="nav-history-icon" />
      </view>
    </view>

    <view class="chat-body">
      <ChatEmptyState
        v-if="!messages.length"
        :questions="starterQuestions"
        @select="handleSuggestionClick"
      />
      <ChatThread
        v-else
        :messages="messages"
        :scroll-top="scrollTop"
        :is-typing="isTyping"
        :is-streaming="isStreaming"
        :suggested-questions="suggestedQuestions"
        :conversation-status="conversationStatus"
        :escalate-loading="escalateLoading"
        :format-time="formatTime"
        :is-refusal-msg="isRefusalMsg"
        @source-click="handleSourceClick"
        @unanswered-closed="onUnansweredCardClosed"
        @call-teacher="handleCallTeacher"
        @suggestion-click="handleSuggestionClick"
      />
    </view>

    <ChatComposer
      v-model="inputMessage"
      :placeholder="inputPlaceholder"
      :disabled="isStreaming"
      :can-send="canSend"
      :show-call-menu="showCallMenu"
      @send="sendMessage"
      @longpress-send="onSendLongPress"
      @close-call-menu="showCallMenu = false"
      @call-teacher="handleCallTeacher"
    />

    <CustomTabBar current="assistant" />

    <SourceSheet
      :visible="sourcePopup.visible"
      :title="sourcePopup.title"
      :content="sourcePopup.content"
      @close="closeSourcePopup"
    />
  </view>
</template>

<script setup lang="ts">
import CustomTabBar from '@/components/CustomTabBar.vue'
import AppIcon from '@/components/AppIcon.vue'
import ChatComposer from '@/components/chat/ChatComposer.vue'
import ChatEmptyState from '@/components/chat/ChatEmptyState.vue'
import ChatThread from '@/components/chat/ChatThread.vue'
import SourceSheet from '@/components/chat/SourceSheet.vue'
import { useChatSession } from '@/composables/useChatSession'

const starterQuestions = [
  '奖助学金申请流程怎么走？',
  '选课调整一般在哪里办理？',
  '校园卡丢了应该怎么处理？',
]

const {
  messages,
  inputMessage,
  isStreaming,
  isTyping,
  scrollTop,
  conversationStatus,
  escalateLoading,
  suggestedQuestions,
  showCallMenu,
  sourcePopup,
  canSend,
  inputPlaceholder,
  closeSourcePopup,
  formatTime,
  goBack,
  goToHistory,
  handleCallTeacher,
  handleSourceClick,
  handleSuggestionClick,
  isRefusalMsg,
  onSendLongPress,
  onUnansweredCardClosed,
  sendMessage,
} = useChatSession()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.chat-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background:
    radial-gradient(circle at 50% -12%, rgba(178, 140, 255, 0.20), transparent 34%),
    $surface;
}

.top-nav {
  position: relative;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  padding: calc(env(safe-area-inset-top) + 12px) 18px 12px;
  background: rgba(250, 245, 251, 0.86);
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
}

.nav-left,
.nav-right {
  display: flex;
  align-items: center;
}

.nav-left {
  gap: 8px;
}

.nav-right {
  width: 38px;
  height: 38px;
  justify-content: center;
  border-radius: 19px;
  background: rgba($primary, 0.08);
}

.nav-right:active {
  transform: scale(0.94);
}

.nav-title {
  color: $primary;
  font-size: 20px;
  font-weight: 800;
  line-height: 1;
}

.nav-icon,
.nav-history-icon {
  color: $primary;
}

.nav-icon {
  font-size: 24px;
}

.nav-history-icon {
  font-size: 22px;
}

.chat-body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
</style>
