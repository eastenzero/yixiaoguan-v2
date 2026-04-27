<template>
  <view class="profile-page">
    <view class="top-bar">
      <view class="top-action" @click="goHome">
        <text class="material-symbols-outlined top-icon">arrow_back</text>
      </view>
      <text class="top-title">我的</text>
      <view class="top-action" @click="showComingSoon">
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
          <text class="stat-value">128</text>
          <text class="stat-label">问答历史</text>
        </view>
        <view class="stat-card" @click="showComingSoon">
          <view class="stat-icon-wrap secondary-soft">
            <text class="material-symbols-outlined stat-icon secondary-icon">assignment</text>
          </view>
          <text class="stat-value">12</text>
          <text class="stat-label">我的申请</text>
        </view>
      </view>

      <view class="feature-grid">
        <view class="progress-card">
          <view class="progress-head">
            <view>
              <text class="card-title">学期进度</text>
              <text class="card-subtitle">2023-2024 秋季学期</text>
            </view>
            <view class="week-pill">
              <text class="week-text">第 14 周</text>
            </view>
          </view>
          <view class="progress-numbers">
            <text class="progress-percent">84%</text>
            <text class="progress-days">剩余 23 天</text>
          </view>
          <view class="progress-track">
            <view class="progress-fill" />
          </view>
        </view>

        <view class="ai-card" @click="goChatHistory">
          <view class="ai-head">
            <view class="ai-icon-wrap">
              <text class="material-symbols-outlined ai-icon">smart_toy</text>
            </view>
            <text class="card-title">AI 助手</text>
          </view>
          <text class="ai-preview">“关于《病理生理学》期末考点的总结已经为您准备好了...”</text>
          <view class="ai-action">
            <text class="ai-action-text">查看对话记录</text>
            <text class="material-symbols-outlined ai-action-icon">arrow_forward</text>
          </view>
        </view>
      </view>

      <view class="settings-group">
        <view
          v-for="item in primarySettings"
          :key="item.label"
          class="settings-row"
          @click="showComingSoon"
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
          @click="showComingSoon"
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
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import CustomTabBar from '@/components/CustomTabBar.vue'

const userStore = useUserStore()

const primarySettings = [
  { label: '消息通知', icon: 'notifications' },
  { label: '系统设置', icon: 'settings' },
]

const secondarySettings = [
  { label: '意见反馈', icon: 'rate_review' },
  { label: '帮助中心', icon: 'help' },
  { label: '关于 医小管', icon: 'info' },
]

const displayName = computed(() => userStore.userInfo?.name || '未登录')

const avatarInitial = computed(() => {
  const name = displayName.value.trim()
  return name ? name.slice(0, 1) : '医'
})

const studentMeta = computed(() => {
  const staffId = userStore.userInfo?.staff_id
  return staffId ? `临床医学系 · ${staffId}` : '临床医学系 · 2021级本科'
})

function goHome() {
  uni.switchTab({ url: '/pages/home/index' })
}

function goChatHistory() {
  uni.navigateTo({ url: '/pages/chat/history' })
}

function showComingSoon() {
  uni.showToast({ title: '即将上线', icon: 'none' })
}

function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        uni.reLaunch({ url: '/pages/login/index' })
      }
    },
  })
}
</script>

<style lang="scss" scoped>
@import '@/styles/tokens.scss';

.profile-page {
  min-height: 100vh;
  background: #f7f9fb;
  font-family: $font-family-sans;
  color: $text-primary;
  padding-bottom: calc(env(safe-area-inset-bottom) + 6rem);
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
  background: linear-gradient(135deg, #630ed4 0%, #7c3aed 100%);
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
  border: 2px solid #630ed4;
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
  background: linear-gradient(90deg, $primary 0%, #7c3aed 100%);
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
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-icon {
  font-size: 22px;
  color: #64748b;
}

.settings-label {
  font-size: $font-size-base;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.chevron-icon {
  font-size: 22px;
  color: #cbd5e1;
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
