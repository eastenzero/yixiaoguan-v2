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
import { ref, onMounted } from 'vue'
import { listConversations } from '@/api/chat'
import type { ConversationResponse } from '@/types/chat'

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

<style scoped>
.history-page { display: flex; flex-direction: column; height: 100vh; background: #f8fafc; }
.top-nav { display: flex; align-items: center; padding: calc(env(safe-area-inset-top) + 1rem) 1.5rem 1rem; background: rgba(248,250,252,0.8); backdrop-filter: blur(20px); z-index: 50; }
.nav-left { display: flex; align-items: center; gap: 0.75rem; }
.nav-back-icon { font-size: 1.5rem; color: #630ed4; }
.nav-title { font-size: 1.25rem; font-weight: 700; color: #0f172a; }

.list-container { flex: 1; padding: 0 1rem 1rem; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding-top: 6rem; }
.empty-icon { font-size: 3rem; color: #cbd5e1; margin-bottom: 1rem; }
.empty-text { font-size: 0.875rem; color: #94a3b8; }

.conv-card { background: #fff; border-radius: 0.75rem; padding: 1rem 1.25rem; margin-bottom: 0.75rem; box-shadow: 0 0.125rem 0.5rem rgba(0,0,0,0.03); }
.conv-card:active { opacity: 0.8; }
.conv-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
.conv-title { font-size: 0.9375rem; font-weight: 600; color: #0f172a; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.5rem; }
.status-badge { padding: 0.125rem 0.5rem; border-radius: 1rem; font-size: 0.6875rem; }
.status-ai_serving { background: #ede9fe; color: #7c3aed; }
.status-pending_teacher { background: #fef3c7; color: #d97706; }
.status-teacher_serving { background: #d1fae5; color: #059669; }
.status-resolved { background: #f1f5f9; color: #64748b; }
.status-closed { background: #f1f5f9; color: #94a3b8; }
.status-text { font-weight: 600; }
.conv-time { font-size: 0.75rem; color: #94a3b8; }

.loading-indicator { display: flex; justify-content: center; padding: 1rem 0; }
.loading-text { font-size: 0.75rem; color: #94a3b8; }
.no-more { display: flex; justify-content: center; padding: 1rem 0; }
.no-more-text { font-size: 0.75rem; color: #cbd5e1; }
</style>
