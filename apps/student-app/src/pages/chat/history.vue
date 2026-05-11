<template>
  <view class="history-page">
    <view class="top-nav">
      <view class="nav-left" @click="goBack">
        <text class="material-symbols-outlined nav-back-icon">arrow_back</text>
        <text class="nav-title">历史对话</text>
      </view>
    </view>

    <scroll-view class="list-container" scroll-y @scrolltolower="loadMore" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view v-if="!conversations.length && !loading" class="empty-state">
        <text class="material-symbols-outlined empty-icon">chat_bubble_outline</text>
        <text class="empty-text">暂无对话记录</text>
      </view>

      <view
        v-for="conv in conversations"
        :key="conv.id"
        class="conv-card"
        @click="openConversation(conv)"
      >
        <view class="conv-header">
          <text class="conv-title">{{ conv.title || '新对话' }}</text>
          <view :class="['status-badge', `status-${conv.status}`]">
            <text class="status-text">{{ statusLabel(conv.status) }}</text>
          </view>
        </view>
        <text class="conv-time">{{ formatDate(conv.updated_at) }}</text>
      </view>

      <view v-if="loading" class="loading-indicator">
        <text class="loading-text">加载中...</text>
      </view>
      <view v-if="noMore && conversations.length" class="no-more">
        <text class="no-more-text">没有更多了</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { listConversations } from '@/api/chat'
import type { ConversationResponse } from '@/types/chat'

const conversations = ref<ConversationResponse[]>([])
const loading = ref(false)
const refreshing = ref(false)
const page = ref(1)
const noMore = ref(false)

// 收到老师回复 / 状态变化（来自全局 uni event bus）时刷新列表，让最新会话排到顶部、未读状态实时更新
const onRealtimeRefresh = () => { loadData(true) }

onMounted(() => {
  loadData(true)
  uni.$on('rt:new_message', onRealtimeRefresh)
  uni.$on('rt:status_changed', onRealtimeRefresh)
})
onShow(() => { loadData(true) })
onUnmounted(() => {
  uni.$off('rt:new_message', onRealtimeRefresh)
  uni.$off('rt:status_changed', onRealtimeRefresh)
})

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

function goBack() { uni.navigateBack() }

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

.history-page { display: flex; flex-direction: column; height: 100vh; background: $surface; }
.top-nav { display: flex; align-items: center; padding: calc(env(safe-area-inset-top) + 1rem) 1.5rem 1rem; background: rgba(250,245,251,0.80); backdrop-filter: $backdrop-bar; -webkit-backdrop-filter: $backdrop-bar; z-index: 50; }
.nav-left { display: flex; align-items: center; gap: 0.75rem; }
.nav-back-icon { font-size: 1.5rem; color: $primary; }
.nav-title { font-size: 1.25rem; font-weight: 700; color: $on-surface; }

.list-container { flex: 1; padding: 0 1rem 1rem; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 6rem; }
.empty-icon { font-size: 3rem; color: $outline-variant; margin-bottom: 1rem; }
.empty-text { font-size: 0.875rem; color: $on-surface-variant; }

.conv-card { background: $surface-container-lowest; border-radius: $radius-md; padding: 1rem 1.25rem; margin-bottom: 0.75rem; transition: background 0.2s ease; }
.conv-card:active { background: $surface-container-low; }
.conv-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
.conv-title { font-size: 0.9375rem; font-weight: 600; color: $on-surface; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.5rem; }
.status-badge { padding: 0.125rem 0.5rem; border-radius: $radius-full; font-size: 0.6875rem; font-weight: 700; }
.status-ai_serving { background: rgba($primary-container, 0.30); color: $on-primary-container; }
.status-pending_teacher { background: rgba($tertiary-container, 0.30); color: $on-tertiary-container; }
.status-teacher_serving { background: rgba($success, 0.15); color: $success; }
.status-resolved { background: $surface-container; color: $on-surface-variant; }
.status-closed { background: $surface-container; color: $outline; }
.status-text { font-weight: 700; }
.conv-time { font-size: 0.75rem; color: $on-surface-variant; }

.loading-indicator { display: flex; justify-content: center; padding: 1rem 0; }
.loading-text { font-size: 0.75rem; color: $on-surface-variant; }
.no-more { display: flex; justify-content: center; padding: 1rem 0; }
.no-more-text { font-size: 0.75rem; color: $outline-variant; }
</style>
