<template>
  <view class="home-page">
    <view class="header-area">
      <view class="greeting">
        <text class="greeting-text">你好，{{ displayName }}</text>
        <text class="greeting-sub">有什么可以帮助你的？</text>
      </view>
    </view>

    <view class="hero-card" @click="goChat()">
      <view class="hero-icon-box">
        <text class="material-symbols-outlined hero-icon">auto_awesome</text>
      </view>
      <view class="hero-text">
        <text class="hero-title">问 AI 助手</text>
        <text class="hero-desc">关于校园生活的一切问题</text>
      </view>
      <text class="material-symbols-outlined hero-arrow">arrow_forward</text>
    </view>

    <view class="section-title">快捷提问</view>
    <view class="preset-list">
      <view
        v-for="q in presetQuestions"
        :key="q"
        class="preset-card"
        @click="goChat(q)"
      >
        <text class="material-symbols-outlined preset-icon">chat</text>
        <text class="preset-text">{{ q }}</text>
      </view>
    </view>

    <view v-if="recentConversations.length" class="section-title">最近对话</view>
    <view v-for="conv in recentConversations" :key="conv.id" class="recent-card" @click="openConversation(conv)">
      <text class="recent-title">{{ conv.title || '新对话' }}</text>
      <text class="recent-time">{{ formatDate(conv.updated_at) }}</text>
    </view>

    <view class="bottom-spacer" />
    <CustomTabBar current="home" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { listConversations } from '@/api/chat'
import CustomTabBar from '@/components/CustomTabBar.vue'
import type { ConversationResponse } from '@/types/chat'

const userStore = useUserStore()
const recentConversations = ref<ConversationResponse[]>([])

const displayName = computed(() => userStore.userInfo?.name || userStore.userInfo?.staff_id || '同学')

const presetQuestions = [
  '选课有什么注意事项？',
  '教室预约流程是什么？',
  '学分绩点怎么计算？',
  '图书馆借阅规则？',
  '如何申请奖学金？',
]

onShow(() => { loadRecent() })

async function loadRecent() {
  try {
    const res = await listConversations(1, 5)
    recentConversations.value = res.items
  } catch { /* ignore */ }
}

function goChat(query?: string) {
  if (query) {
    uni.setStorageSync('chat_init_query', query)
  }
  uni.switchTab({ url: '/pages/chat/index' })
}

function openConversation(conv: ConversationResponse) {
  uni.setStorageSync('pendingConversationId', String(conv.id))
  uni.switchTab({ url: '/pages/chat/index' })
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  if (d.toDateString() === now.toDateString()) {
    return `今天 ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
  }
  return `${d.getMonth() + 1}/${d.getDate()}`
}
</script>

<style scoped>
.home-page { min-height: 100vh; background: #f8fafc; padding: 0 1rem; }

.header-area { padding: calc(env(safe-area-inset-top) + 1.5rem) 0.5rem 1rem; }
.greeting-text { font-size: 1.5rem; font-weight: 800; color: #0f172a; display: block; margin-bottom: 0.25rem; }
.greeting-sub { font-size: 0.875rem; color: #64748b; }

.hero-card { display: flex; align-items: center; background: linear-gradient(135deg, #630ed4, #8b5cf6); border-radius: 1rem; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 0.5rem 1.5rem rgba(99,14,212,0.2); }
.hero-card:active { opacity: 0.9; transform: scale(0.98); }
.hero-icon-box { width: 3rem; height: 3rem; background: rgba(255,255,255,0.2); border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; margin-right: 1rem; }
.hero-icon { font-size: 1.5rem; color: #fff; }
.hero-text { flex: 1; }
.hero-title { font-size: 1.125rem; font-weight: 700; color: #fff; display: block; }
.hero-desc { font-size: 0.75rem; color: rgba(255,255,255,0.7); }
.hero-arrow { font-size: 1.25rem; color: rgba(255,255,255,0.6); }

.section-title { font-size: 0.875rem; font-weight: 700; color: #0f172a; margin-bottom: 0.75rem; padding: 0 0.25rem; }

.preset-list { display: flex; flex-direction: column; gap: 0.5rem; margin-bottom: 1.5rem; }
.preset-card { display: flex; align-items: center; gap: 0.75rem; background: #fff; border-radius: 0.75rem; padding: 0.875rem 1rem; box-shadow: 0 0.0625rem 0.25rem rgba(0,0,0,0.03); }
.preset-card:active { background: #f5f3ff; }
.preset-icon { font-size: 1.25rem; color: #7c3aed; }
.preset-text { font-size: 0.875rem; color: #334155; flex: 1; }

.recent-card { display: flex; justify-content: space-between; align-items: center; background: #fff; border-radius: 0.75rem; padding: 0.875rem 1rem; margin-bottom: 0.5rem; box-shadow: 0 0.0625rem 0.25rem rgba(0,0,0,0.03); }
.recent-card:active { opacity: 0.8; }
.recent-title { font-size: 0.875rem; font-weight: 500; color: #0f172a; flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; margin-right: 0.5rem; }
.recent-time { font-size: 0.75rem; color: #94a3b8; white-space: nowrap; }

.bottom-spacer { height: 5rem; }
</style>
