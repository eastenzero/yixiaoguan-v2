<template>
  <view class="profile-page">
    <view class="top-bar">
      <view class="top-action" @click="goHome">
        <text class="material-symbols-outlined top-icon">arrow_back</text>
      </view>
      <text class="top-title">我的</text>
      <view class="top-action" @click="goChatHistory">
        <text class="material-symbols-outlined top-icon">notifications</text>
        <view class="notify-dot" />
      </view>
    </view>

    <view class="profile-content">
      <view class="hero-card">
        <view class="hero-main">
          <view class="avatar-wrap">
            <image
              v-if="userStore.userInfo?.avatar_url"
              class="avatar-image"
              :src="userStore.userInfo.avatar_url"
              mode="aspectFill"
            />
            <view v-else class="avatar-fallback">
              <text class="avatar-initial">{{ avatarInitial }}</text>
            </view>
            <view class="verified-badge">
              <text class="material-symbols-outlined verified-icon">verified</text>
            </view>
          </view>
          <view class="hero-copy">
            <text class="user-name">{{ displayName }}</text>
            <text class="user-meta">{{ studentMeta }}</text>
            <view class="identity-chip">
              <text class="identity-text">已认证身份</text>
            </view>
          </view>
        </view>
        <view class="hero-glow hero-glow-right" />
        <view class="hero-glow hero-glow-left" />
      </view>

      <view class="stats-grid">
        <view class="stat-card" @click="goChatHistory">
          <view class="stat-icon-wrap primary-soft">
            <text class="material-symbols-outlined stat-icon primary-icon">forum</text>
          </view>
          <text class="stat-value">{{ conversationCount }}</text>
          <text class="stat-label">咨询记录</text>
        </view>
        <view class="stat-card" @click="goChatHistory">
          <view class="stat-icon-wrap secondary-soft">
            <text class="material-symbols-outlined stat-icon secondary-icon">mark_chat_read</text>
          </view>
          <text class="stat-value">{{ totalUnread }}</text>
          <text class="stat-label">未读消息</text>
        </view>
      </view>

      <view class="feature-grid">
        <view class="ai-card" @click="goChat">
          <view class="ai-head">
            <view class="ai-icon-wrap">
              <text class="material-symbols-outlined ai-icon">smart_toy</text>
            </view>
            <text class="card-title">AI 智慧助手</text>
          </view>
          <text class="ai-preview">校园事务、办事流程、政策查询…有问题随时问我。</text>
          <view class="ai-action">
            <text class="ai-action-text">开始咨询</text>
            <text class="material-symbols-outlined ai-action-icon">arrow_forward</text>
          </view>
        </view>
      </view>

      <view class="settings-group">
        <view
          v-for="item in primarySettings"
          :key="item.label"
          class="settings-row"
          @click="handleSettingClick(item)"
        >
          <view class="settings-left">
            <view class="settings-icon-wrap">
              <text class="material-symbols-outlined settings-icon">{{ item.icon }}</text>
            </view>
            <text class="settings-label">{{ item.label }}</text>
          </view>
          <text class="material-symbols-outlined chevron-icon">chevron_right</text>
        </view>
      </view>

      <view class="settings-group">
        <view
          v-for="item in secondarySettings"
          :key="item.label"
          class="settings-row"
          @click="handleSettingClick(item)"
        >
          <view class="settings-left">
            <view class="settings-icon-wrap">
              <text class="material-symbols-outlined settings-icon">{{ item.icon }}</text>
            </view>
            <text class="settings-label">{{ item.label }}</text>
          </view>
          <text class="material-symbols-outlined chevron-icon">chevron_right</text>
        </view>
      </view>

      <view class="logout-section">
        <button class="logout-btn" @click="handleLogout">
          <text class="logout-text">退出登录</text>
        </button>
        <text class="version-text">Version v1.0.0</text>
      </view>
    </view>

    <CustomTabBar current="profile" />
    <FeatureNoticeSheet />
    <AppDialog />
    <FeedbackDrawer v-model:visible="feedbackDrawerVisible" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { listConversations } from '@/api/chat'
import { getUnreadSummary } from '@/api/notification'
import { openAiQuestion, showComingSoon } from '@/composables/useServiceNavigation'
import CustomTabBar from '@/components/CustomTabBar.vue'
import FeatureNoticeSheet from '@/components/FeatureNoticeSheet.vue'
import AppDialog from '@/components/AppDialog.vue'
import FeedbackDrawer from '@/components/FeedbackDrawer.vue'
import { useDialog } from '@/composables/useDialog'
import { trackEvent } from '@/utils/track'

const userStore = useUserStore()
const dialog = useDialog()
const conversationCount = ref(0)
const totalUnread = ref(0)
const feedbackDrawerVisible = ref(false)

interface SettingItem {
  label: string
  icon: string
  action: 'comingSoon' | 'aiQuestion' | 'about' | 'openFeedbackDrawer'
  aiQuestion?: string
}

const primarySettings: SettingItem[] = [
  { label: '消息通知', icon: 'notifications', action: 'comingSoon' },
  { label: '系统设置', icon: 'settings', action: 'comingSoon' },
]

const secondarySettings: SettingItem[] = [
  { label: '意见反馈', icon: 'rate_review', action: 'aiQuestion', aiQuestion: '我想反馈医小管使用问题，应该怎么说？' },
  { label: '帮助中心', icon: 'help', action: 'aiQuestion', aiQuestion: '医小管可以帮我做什么？' },
  { label: '关于 医小管', icon: 'info', action: 'about' },
]

const displayName = computed(() => userStore.userInfo?.name || '未登录')

const feedbackSetting = secondarySettings.find(item => item.icon === 'rate_review')
if (feedbackSetting) {
  feedbackSetting.action = 'openFeedbackDrawer'
  feedbackSetting.aiQuestion = undefined
}

const avatarInitial = computed(() => {
  const name = displayName.value.trim()
  return name ? name.slice(0, 1) : '医'
})

const studentMeta = computed(() => {
  const staffId = userStore.userInfo?.staff_id
  return staffId ? `学号 ${staffId}` : '学生'
})

function goHome() {
  uni.switchTab({ url: '/pages/home/index' })
}

function goChatHistory() {
  uni.navigateTo({ url: '/pages/chat/history' })
}

function goChat() {
  uni.switchTab({ url: '/pages/chat/index' })
}

function handleSettingClick(item: SettingItem) {
  if (item.action === 'openFeedbackDrawer') {
    feedbackDrawerVisible.value = true
  } else if (item.action === 'aiQuestion' && item.aiQuestion) {
    openAiQuestion(item.aiQuestion)
  } else if (item.action === 'about') {
    dialog.alert({
      title: '关于医小管',
      content: '医小管 v1.0.0\n校园事务 AI 咨询与人工兜底平台',
      icon: 'school',
      iconFill: true,
      confirmText: '知道了',
    })
  } else {
    showComingSoon(item.label)
  }
}

onShow(async () => {
  trackEvent('page_view', { path: '/pages/profile/index' })
  try {
    const res = await listConversations(1, 1)
    conversationCount.value = res.total || 0
  } catch { conversationCount.value = 0 }
  try {
    const unread = await getUnreadSummary()
    totalUnread.value = unread.total_unread || 0
  } catch { totalUnread.value = 0 }
})

async function handleLogout() {
  const confirmed = await dialog.confirm({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    icon: 'logout',
    confirmText: '退出',
    cancelText: '取消',
    confirmDanger: true,
  })
  if (confirmed) {
    userStore.logout()
    uni.reLaunch({ url: '/pages/login/index' })
  }
}
</script>

<style lang="scss" scoped>
@import '@/styles/tokens.scss';

.profile-page {
  min-height: 100vh;
  background: $surface;
  font-family: $font-family-sans;
  color: $text-primary;
  padding-bottom: calc(var(--tabbar-safe) + $space-6);  /* tab bar + breathing room */
}

.top-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top) + $space-4) $space-6 $space-4;
  background: rgba(247, 249, 251, 0.82);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
}

.top-action {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
}

.top-action:active {
  background: rgba($primary, 0.08);
}

.top-icon {
  font-size: 24px;
  color: $primary;
}

.top-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $primary;
}

.notify-dot {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 8px;
  height: 8px;
  border-radius: $radius-full;
  background: $danger;
}

.profile-content {
  padding: 88px $space-6 0;
}

.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: $radius-lg;
  background: linear-gradient(135deg, #5b21b6 0%, #b28cff 100%);
  color: $text-inverse;
  padding: $space-8;
  margin-bottom: $space-8;
}

.hero-main {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: $space-6;
}

.avatar-wrap {
  position: relative;
  width: 80px;
  height: 80px;
  flex-shrink: 0;
}

.avatar-image,
.avatar-fallback {
  width: 80px;
  height: 80px;
  border-radius: $radius-full;
  border: 4px solid rgba(255, 255, 255, 0.30);
  box-shadow: 0 8px 18px rgba(44, 0, 120, 0.20);
}

.avatar-fallback {
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.18);
}

.avatar-initial {
  font-size: 32px;
  font-weight: $font-weight-bold;
  color: $text-inverse;
}

.verified-badge {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 24px;
  height: 24px;
  border-radius: $radius-full;
  border: 2px solid #5b21b6;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.verified-icon {
  font-size: 15px;
  color: $primary;
  font-variation-settings: 'FILL' 1;
}

.hero-copy {
  flex: 1;
  min-width: 0;
}

.user-name {
  display: block;
  font-size: $font-size-2xl;
  line-height: $line-height-tight;
  font-weight: 800;
  color: $text-inverse;
}

.user-meta {
  display: block;
  margin-top: $space-1;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: rgba(255, 255, 255, 0.82);
}

.identity-chip {
  display: inline-flex;
  margin-top: $space-3;
  padding: $space-1 $space-3;
  border-radius: $radius-full;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.20);
}

.identity-text {
  font-size: 10px;
  line-height: 18px;
  font-weight: $font-weight-bold;
  color: $text-inverse;
}

.hero-glow {
  position: absolute;
  width: 192px;
  height: 192px;
  border-radius: $radius-full;
  background: rgba(255, 255, 255, 0.10);
  filter: blur(30px);
}

.hero-glow-right {
  top: -48px;
  right: -48px;
}

.hero-glow-left {
  left: -48px;
  bottom: -48px;
  background: rgba($primary, 0.22);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: $space-4;
  margin-bottom: $space-8;
}

.stat-card {
  background: $bg-card;
  border-radius: $radius-lg;
  padding: $space-5;
}

.stat-card:active {
  background: $surface-container-high;
}

.stat-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-3;
}

.primary-soft {
  background: rgba($primary, 0.10);
}

.secondary-soft {
  background: rgba($secondary, 0.10);
}

.stat-icon {
  font-size: 22px;
}

.primary-icon {
  color: $primary;
}

.secondary-icon {
  color: $secondary;
}

.stat-value {
  display: block;
  font-size: $font-size-2xl;
  line-height: $line-height-tight;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.stat-label {
  display: block;
  margin-top: $space-1;
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $text-secondary;
}

.feature-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: $space-4;
  margin-bottom: $space-8;
}

.progress-card,
.ai-card {
  border-radius: $radius-lg;
  padding: $space-6;
}

.progress-card {
  background: $surface-container-low;
}

.progress-head,
.progress-numbers,
.ai-head,
.ai-action,
.settings-row,
.settings-left {
  display: flex;
  align-items: center;
}

.progress-head,
.progress-numbers,
.settings-row {
  justify-content: space-between;
}

.card-title {
  display: block;
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.card-subtitle {
  display: block;
  margin-top: $space-1;
  font-size: $font-size-xs;
  color: $text-secondary;
}

.week-pill {
  border-radius: $radius-full;
  padding: $space-1 $space-3;
  border: 1px solid rgba($primary, 0.10);
  background: rgba(255, 255, 255, 0.80);
}

.week-text {
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $primary;
}

.progress-numbers {
  margin-top: $space-6;
  margin-bottom: $space-2;
}

.progress-percent {
  font-size: $font-size-3xl;
  line-height: $line-height-tight;
  font-weight: 800;
  color: $primary;
}

.progress-days {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: $text-muted;
}

.progress-track {
  height: 12px;
  border-radius: $radius-full;
  overflow: hidden;
  background: $surface-container-highest;
}

.progress-fill {
  width: 84%;
  height: 100%;
  border-radius: $radius-full;
  background: linear-gradient(90deg, $primary 0%, #b28cff 100%);
}

.ai-card {
  background: $bg-card;
  box-shadow: 0 -10px 40px rgba(124, 58, 237, 0.08);
}

.ai-head {
  gap: $space-3;
  margin-bottom: $space-4;
}

.ai-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: $radius-md;
  background: $primary;
  box-shadow: 0 8px 16px rgba($primary, 0.20);
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-icon {
  font-size: 22px;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1;
}

.ai-preview {
  display: block;
  font-size: $font-size-sm;
  line-height: $line-height-relaxed;
  color: $text-secondary;
}

.ai-action {
  justify-content: center;
  gap: $space-2;
  margin-top: $space-4;
  min-height: 44px;
  border-radius: $radius-full;
  background: $primary-soft;
}

.ai-action-text {
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $primary;
}

.ai-action-icon {
  font-size: 16px;
  color: $primary;
}

.settings-group {
  overflow: hidden;
  border-radius: $radius-lg;
  background: $bg-card;
  margin-bottom: $space-6;
}

.settings-row {
  min-height: 64px;
  padding: 0 $space-6;
  border-bottom: 1px solid $surface-container-low;
}

.settings-row:last-child {
  border-bottom: none;
}

.settings-row:active {
  background: $surface-container-high;
}

.settings-left {
  gap: $space-4;
}

.settings-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: $radius-full;
  background: $surface-container-low;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-icon {
  font-size: 22px;
  color: $on-surface-variant;
}

.settings-label {
  font-size: $font-size-base;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.chevron-icon {
  font-size: 22px;
  color: $outline-variant;
}

.logout-section {
  margin-top: $space-12;
  margin-bottom: $space-10;
}

.logout-btn {
  width: 100%;
  min-height: 56px;
  border-radius: $radius-lg;
  background: rgba($danger, 0.10);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:active {
  background: rgba($danger, 0.18);
}

.logout-text {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $danger;
}

.version-text {
  display: block;
  margin-top: $space-6;
  text-align: center;
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $text-muted;
}
</style>
