<template>
  <view class="history-page">
    <view class="top-nav">
      <view class="nav-left" @click="goBack">
        <AppIcon name="arrow_back" class="nav-back-icon" />
        <view><text class="nav-title">消息与历史</text><text class="nav-subtitle">继续之前的校园问答</text></view>
      </view>
      <view class="history-count"><text>{{ conversations.length }}</text></view>
    </view>

    <scroll-view class="list-container" scroll-y @scrolltolower="loadMore" refresher-enabled @refresherrefresh="onRefresh" :refresher-triggered="refreshing">
      <view class="history-intro">
        <text class="intro-kicker">CONVERSATIONS</text>
        <text class="intro-title">你的咨询记录</text>
        <text class="intro-copy">按时间排列，点击即可继续对话。</text>
      </view>

      <view v-if="loadError && !loading" class="empty-state">
        <AppIcon name="refresh" class="empty-icon" />
        <text class="empty-text">历史记录加载失败</text>
        <button class="retry-button" @click="loadData(true)">重新加载</button>
      </view>
      <view v-else-if="!conversations.length && !loading" class="empty-state">
        <AppIcon name="chat_bubble_outline" class="empty-icon" />
        <text class="empty-text">暂无对话记录</text>
      </view>

      <view
        v-for="conv in conversations"
        :key="conv.id"
        class="conv-card"
        @click="openConversation(conv)"
      >
        <view class="conv-icon"><AppIcon name="chat_bubble_outline" /></view>
        <view class="conv-main">
        <view class="conv-header">
          <text class="conv-title">{{ conv.title || '新对话' }}</text>
          <view :class="['status-badge', `status-${conv.status}`]">
            <text class="status-text">{{ statusLabel(conv.status) }}</text>
          </view>
        </view>
        <text class="conv-time">{{ formatDate(conv.updated_at) }}</text>
        </view>
        <AppIcon name="chevron_right" class="conv-chevron" />
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
import AppIcon from '@/components/AppIcon.vue'
import { ref, onMounted } from 'vue'
import { listConversations } from '@/api/chat'
import type { ConversationResponse } from '@/types/chat'

const conversations = ref<ConversationResponse[]>([])
const loading = ref(false)
const refreshing = ref(false)
const page = ref(1)
const noMore = ref(false)
const loadError = ref(false)

onMounted(() => { loadData(true) })

async function loadData(reset = false) {
  if (loading.value) return
  loading.value = true
  if (reset) { page.value = 1; noMore.value = false }
  try {
    loadError.value = false
    const res = await listConversations(page.value, 20)
    if (reset) {
      conversations.value = res.items
    } else {
      conversations.value.push(...res.items)
    }
    if (res.items.length < 20) noMore.value = true
  } catch (e) {
    loadError.value = true
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

.history-page { display: flex; flex-direction: column; height: 100dvh; width: min(100%, 430px); margin: 0 auto; background: radial-gradient(circle at 100% 0%, rgba(196,172,228,.28), transparent 34%), $surface; }
.top-nav { display: flex; align-items: center; justify-content: space-between; padding: calc(env(safe-area-inset-top) + 12px) 18px 12px; background: rgba(250,245,251,0.82); backdrop-filter: $backdrop-bar; -webkit-backdrop-filter: $backdrop-bar; z-index: 50; }
.nav-left { min-height: 44px; display: flex; align-items: center; gap: 12px; }
.nav-back-icon { font-size: 22px; color: $primary; }
.nav-title, .nav-subtitle { display: block; }
.nav-title { font-size: 16px; font-weight: 800; color: $on-surface; }
.nav-subtitle { margin-top: 2px; color: #918494; font-size: 9px; }
.history-count { min-width: 36px; height: 36px; padding: 0 8px; display: flex; align-items: center; justify-content: center; box-sizing: border-box; border-radius: 13px; color: $primary; background: rgba(255,255,255,.72); font-size: 11px; font-weight: 800; }

.list-container { flex: 1; height: 0; padding: 0 18px 24px; box-sizing: border-box; }
.history-intro { padding: 27px 3px 20px; }
.intro-kicker, .intro-title, .intro-copy { display: block; }
.intro-kicker { color: #9778b1; font-size: 8px; font-weight: 850; letter-spacing: .16em; }
.intro-title { margin-top: 7px; color: $on-surface; font-size: 27px; font-weight: 850; letter-spacing: -.045em; }
.intro-copy { margin-top: 6px; color: #887a8b; font-size: 11px; }

.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 190px; border-radius: 23px; background: rgba(255,255,255,.58); }
.empty-icon { font-size: 3rem; color: $outline-variant; margin-bottom: 1rem; }
.empty-text { font-size: 0.875rem; color: $on-surface-variant; }

.retry-button { margin-top: 14px; padding: 10px 16px; border-radius: 14px; color: #fff; background: $primary; font-size: 12px; font-weight: 750; }
.conv-card { min-height: 76px; padding: 10px 12px; margin-bottom: 10px; display: flex; align-items: center; gap: 11px; box-sizing: border-box; border-radius: 21px; background: rgba(255,255,255,.78); box-shadow: inset 0 1px 0 #fff, 0 10px 26px rgba(91,43,143,.05); transition: background .2s ease, transform .2s ease; }
.conv-card:active { background: #f2e8f1; transform: scale(.988); }
.conv-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 14px; color: $primary; background: #f0e5f2; }
.conv-main { flex: 1; min-width: 0; }
.conv-chevron { flex-shrink: 0; color: #a79aa9; font-size: 18px; }
.conv-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
.conv-title { font-size: 0.9375rem; font-weight: 600; color: $on-surface; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.5rem; }
.status-badge { padding: 3px 7px; border-radius: $radius-full; font-size: 8px; font-weight: 700; }
.status-ai_serving { background: rgba($primary-container, 0.30); color: $on-primary-container; }
.status-pending_teacher { background: rgba($tertiary-container, 0.30); color: $on-tertiary-container; }
.status-teacher_serving { background: rgba($success, 0.15); color: $success; }
.status-resolved { background: $surface-container; color: $on-surface-variant; }
.status-closed { background: $surface-container; color: $outline; }
.status-text { font-weight: 700; }
.conv-time { font-size: 10px; color: $on-surface-variant; }

.loading-indicator { display: flex; justify-content: center; padding: 1rem 0; }
.loading-text { font-size: 0.75rem; color: $on-surface-variant; }
.no-more { display: flex; justify-content: center; padding: 1rem 0; }
.no-more-text { font-size: 0.75rem; color: $outline-variant; }
</style>
