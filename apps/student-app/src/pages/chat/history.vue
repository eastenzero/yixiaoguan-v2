<template>
  <view class="history-page">
    <TopAppBar title="历史对话" show-back />

    <scroll-view
      class="list-container"
      scroll-y
      @scrolltolower="loadMore"
      refresher-enabled
      @refresherrefresh="onRefresh"
      :refresher-triggered="refreshing"
    >
      <view v-if="!conversations.length && !loading" class="empty-state animate-fade-up">
        <view class="empty-icon-wrap">
          <text class="material-symbols-outlined empty-icon">forum</text>
        </view>
        <text class="empty-title">还没有对话记录</text>
        <text class="empty-desc">回到智能助理页随时开启你的第一次提问</text>
      </view>

      <view
        v-for="(conv, idx) in conversations"
        :key="conv.id"
        class="conv-card animate-fade-up"
        :class="`delay-${Math.min(idx + 1, 6)}`"
        @click="openConversation(conv)"
      >
        <view class="conv-main">
          <view class="conv-icon-wrap" :class="iconClassFor(conv.status)">
            <text class="material-symbols-outlined conv-icon">{{ iconNameFor(conv.status) }}</text>
          </view>
          <view class="conv-body">
            <view class="conv-header">
              <text class="conv-title">{{ conv.title || '新对话' }}</text>
              <view :class="['status-badge', statusModifier(conv.status)]">
                <view class="status-dot" />
                <text class="status-text">{{ statusLabel(conv.status) }}</text>
              </view>
            </view>
            <text class="conv-time">{{ formatDate(conv.updated_at) }}</text>
          </view>
          <text class="material-symbols-outlined conv-arrow">chevron_right</text>
        </view>
      </view>

      <view v-if="loading" class="loading-indicator">
        <view class="typing-dots">
          <view class="dot" /><view class="dot" /><view class="dot" />
        </view>
      </view>
      <view v-if="noMore && conversations.length" class="no-more">
        <text class="no-more-text">— 没有更多了 —</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { listConversations } from '@/api/chat'
import type { ConversationResponse } from '@/types/chat'
import TopAppBar from '@/components/TopAppBar.vue'

const conversations = ref<ConversationResponse[]>([])
const loading = ref(false)
const refreshing = ref(false)
const page = ref(1)
const noMore = ref(false)

onMounted(() => { loadData(true) })

async function loadData(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) { page.value = 1; noMore.value = false }
  try {
    const res = await listConversations(page.value, 20)
    if (reset) {
      conversations.value = res.items
    } else {
      conversations.value.push(...res.items)
    }
    if (res.items.length < 20) noMore.value = true
  } catch (e) {
    console.error('加载对话列表失败:', e)
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

function loadMore() {
  if (noMore.value || loading.value) return
  page.value++
  loadData()
}

function onRefresh() {
  refreshing.value = true
  loadData(true)
}

function openConversation(conv: ConversationResponse) {
  uni.setStorageSync('pendingConversationId', String(conv.id))
  uni.switchTab({ url: '/pages/chat/index' })
}

function statusLabel(status: string): string {
  const map: Record<string, string> = {
    ai_serving: 'AI 服务中',
    pending_teacher: '等待老师',
    teacher_serving: '老师服务中',
    resolved: '已解决',
    closed: '已关闭',
  }
  return map[status] || status
}

function statusModifier(status: string): string {
  return `status-badge--${status.replace(/_/g, '-')}`
}

function iconNameFor(status: string): string {
  if (status === 'pending_teacher') return 'hourglass_top'
  if (status === 'teacher_serving') return 'support_agent'
  if (status === 'resolved') return 'task_alt'
  if (status === 'closed') return 'lock'
  return 'auto_awesome'
}

function iconClassFor(status: string): string {
  if (status === 'pending_teacher') return 'conv-icon-wrap--warning'
  if (status === 'teacher_serving') return 'conv-icon-wrap--success'
  if (status === 'resolved') return 'conv-icon-wrap--neutral'
  if (status === 'closed') return 'conv-icon-wrap--muted'
  return 'conv-icon-wrap--primary'
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) {
    return `今天 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  return `${d.getMonth() + 1}月${d.getDate()}日 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

$top-bar-h: 56px;

.history-page {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: $bg-page;
  font-family: $font-family-sans;
  color: $text-primary;
}

.list-container {
  flex: 1;
  padding: calc(env(safe-area-inset-top) + #{$top-bar-h} + #{$space-4}) $space-4
    calc(env(safe-area-inset-bottom) + #{$space-6});
  box-sizing: border-box;
}

// ── Empty state ──────────────────────────────────────
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding-top: $space-12;
  padding-bottom: $space-12;
  text-align: center;
}

.empty-icon-wrap {
  width: 88px;
  height: 88px;
  border-radius: $radius-full;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-5;
}

.empty-icon {
  font-size: 44px;
  color: $primary;
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

.empty-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
  margin-bottom: $space-2;
}

.empty-desc {
  font-size: $font-size-sm;
  color: $text-secondary;
  line-height: $line-height-relaxed;
  max-width: 240px;
}

// ── Conversation card ────────────────────────────────
.conv-card {
  background: $bg-card;
  border-radius: $radius-lg;
  padding: $space-4;
  margin-bottom: $space-3;
  box-shadow: 0 1px 2px rgba($text-primary, 0.04),
              0 4px 12px -4px rgba($primary, 0.06);
  border: 1px solid rgba($primary, 0.04);
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;
}

.conv-card:active {
  transform: scale(0.98);
  box-shadow: 0 2px 4px rgba($text-primary, 0.06),
              0 8px 20px -6px rgba($primary, 0.18);
}

.conv-main {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.conv-icon-wrap {
  width: 44px;
  height: 44px;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &--primary {
    background: $primary-soft;
    .conv-icon { color: $primary; }
  }
  &--warning {
    background: rgba($warning, 0.12);
    .conv-icon { color: $warning; }
  }
  &--success {
    background: rgba($success, 0.12);
    .conv-icon { color: $success; }
  }
  &--neutral {
    background: $surface-container-low;
    .conv-icon { color: $text-secondary; }
  }
  &--muted {
    background: $surface-container;
    .conv-icon { color: $text-muted; }
  }
}

.conv-icon {
  font-size: 22px;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.conv-body {
  flex: 1;
  min-width: 0;
}

.conv-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-1;
}

.conv-title {
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  color: $text-primary;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.conv-time {
  font-size: $font-size-xs;
  color: $text-muted;
  font-weight: $font-weight-medium;
}

.conv-arrow {
  font-size: 20px;
  color: $text-muted;
  flex-shrink: 0;
}

// ── Status badge ─────────────────────────────────────
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px $space-2;
  border-radius: $radius-full;
  flex-shrink: 0;
  border: 1px solid transparent;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: $radius-full;
  background: currentColor;
}

.status-text {
  font-size: 11px;
  font-weight: $font-weight-bold;
  letter-spacing: 0.02em;
}

.status-badge--ai-serving {
  background: $primary-soft;
  color: $primary;
}
.status-badge--pending-teacher {
  background: rgba($warning, 0.12);
  color: $warning;
}
.status-badge--teacher-serving {
  background: rgba($success, 0.12);
  color: $success;
}
.status-badge--resolved {
  background: $surface-container-low;
  color: $text-secondary;
}
.status-badge--closed {
  background: $surface-container;
  color: $text-muted;
}

// ── Loading & no-more indicators ─────────────────────
.loading-indicator {
  display: flex;
  justify-content: center;
  padding: $space-4 0;
}

.no-more {
  display: flex;
  justify-content: center;
  padding: $space-4 0;
}

.no-more-text {
  font-size: $font-size-xs;
  color: $text-muted;
  letter-spacing: 0.05em;
}
</style>
