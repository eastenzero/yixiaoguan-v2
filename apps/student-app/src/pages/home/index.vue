<template>
  <view class="home-page">
    <!-- 1. Brand bar + greeting -->
    <view class="brand-bar">
      <text class="brand-logo">医小管</text>
      <view class="brand-actions">
        <view class="notif-btn" @click="goNotifications">
          <text class="material-symbols-outlined notif-btn-icon">notifications</text>
          <view class="notif-dot" />
        </view>
      </view>
    </view>

    <view class="greeting-section">
      <text class="greeting-sub">下午好，{{ displayName }}</text>
      <text class="greeting-title">智慧校园助理</text>
    </view>

    <!-- 2. Search pill (links to chat) -->
    <view class="search-pill" @click="goChat()">
      <view class="search-icon-box">
        <text class="material-symbols-outlined search-icon">auto_awesome</text>
      </view>
      <input class="search-input" placeholder="有什么可以帮你的？" disabled />
      <view class="search-action">
        <text class="search-action-text">提问</text>
      </view>
    </view>

    <!-- 3. Horizontal category tags -->
    <scroll-view scroll-x class="tag-scroll" show-scrollbar="false">
      <view class="tag-list">
        <view v-for="t in tags" :key="t.id" class="tag-chip" @click="onTagClick(t)">
          <text class="tag-text">{{ t.label }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- 4. Bento grid of quick services -->
    <view class="bento-grid">
      <view class="bento-card bento-large" @click="goChat()">
        <view class="bento-large-top">
          <view class="bento-large-icon-wrap">
            <text class="material-symbols-outlined bento-large-icon">auto_awesome</text>
          </view>
          <text class="bento-large-title">AI 智能助手</text>
          <text class="bento-large-desc">您的全天候校园百科全书</text>
        </view>
        <view class="bento-large-action">
          <text class="bento-large-action-text">立即开启</text>
          <text class="material-symbols-outlined bento-large-action-icon">arrow_forward</text>
        </view>
        <view class="bento-large-glow" />
        <view class="bento-large-glow-secondary" />
      </view>

      <view class="bento-card bento-small" @click="onBentoClick(bentoItems[1])">
        <view class="bento-small-header">
          <view class="bento-small-icon-wrap">
            <text class="material-symbols-outlined bento-small-icon">calendar_month</text>
          </view>
          <text class="bento-badge">HOT</text>
        </view>
        <view class="bento-small-body">
          <text class="bento-small-title">空教室预约</text>
          <text class="bento-small-desc">可预约 12 间</text>
        </view>
      </view>

      <view class="bento-card bento-small" @click="onBentoClick(bentoItems[2])">
        <view class="bento-small-icon-wrap">
          <text class="material-symbols-outlined bento-small-icon">assignment</text>
        </view>
        <view class="bento-small-body">
          <text class="bento-small-title">我的申请</text>
          <text class="bento-small-desc-status">2 项进行中</text>
        </view>
      </view>
    </view>

    <!-- 5. Service list / cards -->
    <view class="service-section">
      <view class="service-section-header">
        <text class="section-title">常用服务</text>
        <text class="section-more" @click="showToastSoon">查看全部</text>
      </view>
      <view class="service-list">
        <view v-for="svc in services" :key="svc.id" class="service-row" @click="onServiceClick(svc)">
          <view class="service-row-left">
            <text class="material-symbols-outlined service-icon">{{ svc.icon }}</text>
            <text class="service-label">{{ svc.label }}</text>
          </view>
          <text class="material-symbols-outlined service-arrow">chevron_right</text>
        </view>
      </view>
    </view>

    <!-- 6. Notification banner -->
    <view v-if="notice" class="notice-banner" @click="goNotifications">
      <view class="notice-left">
        <view class="notice-icon-wrap">
          <text class="material-symbols-outlined notice-icon">campaign</text>
        </view>
        <text class="notice-text">{{ notice }}</text>
      </view>
      <text class="material-symbols-outlined notice-arrow">arrow_forward</text>
    </view>

    <view class="bottom-spacer" />
    <CustomTabBar current="home" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import CustomTabBar from '@/components/CustomTabBar.vue'

const userStore = useUserStore()

const displayName = computed(() => userStore.userInfo?.name || userStore.userInfo?.staff_id || '同学')

// Static placeholder data for new sections
const tags = ref([
  { id: 't1', label: '奖学金政策' },
  { id: 't2', label: '选课指南' },
  { id: 't3', label: '图书馆开放' },
  { id: 't4', label: '校园卡充值' },
])

const bentoItems = ref([
  { id: 'b1', label: 'AI 问答', icon: 'auto_awesome', route: '/pages/chat/index' },
  { id: 'b2', label: '空教室预约', icon: 'calendar_month', route: '' },
  { id: 'b3', label: '我的申请', icon: 'assignment', route: '' },
  { id: 'b4', label: '个人中心', icon: 'person', route: '/pages/profile/index' },
])

const services = ref([
  { id: 's1', label: '教务管理系统', icon: 'school' },
  { id: 's2', label: '图书馆', icon: 'library_books' },
  { id: 's3', label: '学生邮箱', icon: 'mail' },
  { id: 's4', label: '学校官网', icon: 'language' },
])

const notice = ref('你有 3 条未读通知')

function goChat(query?: string) {
  if (query) {
    uni.setStorageSync('chat_init_query', query)
  }
  uni.switchTab({ url: '/pages/chat/index' })
}

function onTagClick(tag: { id: string; label: string }) {
  uni.setStorageSync('chat_init_query', tag.label)
  uni.switchTab({ url: '/pages/chat/index' })
}

function onBentoClick(item: { id: string; label: string; icon: string; route: string }) {
  if (!item.route) {
    uni.showToast({ title: '即将上线', icon: 'none' })
    return
  }
  const tabBarPaths = ['/pages/home/index', '/pages/chat/index', '/pages/services/index', '/pages/profile/index']
  if (tabBarPaths.includes(item.route)) {
    uni.switchTab({ url: item.route })
  } else {
    uni.navigateTo({ url: item.route })
  }
}

function onServiceClick(svc: { id: string; label: string; icon: string }) {
  uni.showToast({ title: '即将上线', icon: 'none' })
}

function goNotifications() {
  uni.showToast({ title: '即将上线', icon: 'none' })
}

function showToastSoon() {
  uni.showToast({ title: '即将上线', icon: 'none' })
}
</script>

<style lang="scss" scoped>
@import '@/styles/tokens.scss';

.home-page {
  min-height: 100vh;
  padding: 0 $space-4 calc(env(safe-area-inset-bottom) + 5rem);
  padding-top: 64px;
  background: $bg-page;
  font-family: $font-family-sans;
}

/* 1. Brand bar */
.brand-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: calc(env(safe-area-inset-top) + $space-4);
  padding-bottom: $space-3;
  padding-left: $space-4;
  padding-right: $space-4;
  background: rgba(249, 250, 251, 0.85);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.brand-logo {
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: $primary;
}

.notif-btn {
  position: relative;
  padding: $space-2;
  color: $text-secondary;
}

.notif-btn-icon {
  font-size: 20px;
}

.notif-dot {
  position: absolute;
  top: $space-2;
  right: $space-2;
  width: 8px;
  height: 8px;
  border-radius: $radius-full;
  background: $danger;
  box-shadow: 0 0 0 2px $bg-page;
}

/* Greeting */
.greeting-section {
  margin-bottom: $space-4;
}

.greeting-sub {
  display: block;
  font-size: $font-size-sm;
  color: $text-secondary;
  font-weight: $font-weight-medium;
  margin-bottom: $space-1;
}

.greeting-title {
  display: block;
  font-size: $font-size-2xl;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

/* 2. Search pill */
.search-pill {
  display: flex;
  align-items: center;
  gap: $space-2;
  background: $bg-card;
  border-radius: $radius-full;
  padding: $space-1;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
  border: 1px solid rgba($border, 0.10);
  margin-bottom: $space-5;
}

.search-icon-box {
  width: 36px;
  height: 36px;
  border-radius: $radius-full;
  background: $primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.search-icon {
  font-size: 18px;
  color: $primary-on;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: $font-size-sm;
  color: $text-primary;
  padding: 0 $space-2;

  &::placeholder {
    color: $text-muted;
  }
}

.search-action {
  flex-shrink: 0;
  background: $surface-container-high;
  color: $text-secondary;
  border-radius: $radius-full;
  padding: $space-2 $space-4;
}

.search-action-text {
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
}

/* 3. Horizontal tags */
.tag-scroll {
  margin-left: -$space-4;
  margin-right: -$space-4;
  padding-left: $space-4;
  padding-right: $space-4;
  margin-bottom: $space-5;
}

.tag-list {
  display: flex;
  gap: $space-3;
}

.tag-chip {
  flex-shrink: 0;
  background: $surface-container-low;
  border-radius: $radius-full;
  padding: $space-2 $space-5;
}

.tag-text {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: $text-secondary;
  white-space: nowrap;
}

/* 4. Bento grid */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: $space-4;
  height: 280px;
  margin-bottom: $space-6;
}

.bento-card {
  border-radius: $radius-lg;
  overflow: hidden;
  position: relative;
}

.bento-large {
  grid-row: span 2;
  background: linear-gradient(135deg, $primary 0%, $secondary 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: $space-5;
}

.bento-large-top {
  position: relative;
  z-index: 2;
}

.bento-large-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: $radius-md;
  background: rgba(255, 255, 255, 0.20);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-4;
}

.bento-large-icon {
  font-size: 24px;
  color: $text-inverse;
}

.bento-large-title {
  display: block;
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: $text-inverse;
  margin-bottom: $space-2;
}

.bento-large-desc {
  display: block;
  font-size: $font-size-sm;
  color: rgba(255, 255, 255, 0.90);
  line-height: $line-height-relaxed;
}

.bento-large-action {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: $space-2;
  color: $text-inverse;
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
}

.bento-large-action-icon {
  font-size: 14px;
}

.bento-large-glow {
  position: absolute;
  right: -16px;
  bottom: -16px;
  width: 96px;
  height: 96px;
  border-radius: $radius-full;
  background: rgba(255, 255, 255, 0.10);
  filter: blur(16px);
}

.bento-large-glow-secondary {
  position: absolute;
  top: 0;
  right: 0;
  width: 128px;
  height: 128px;
  border-radius: $radius-full;
  background: rgba($secondary-container, 0.20);
  filter: blur(24px);
}

.bento-small {
  background: $surface-container-lowest;
  padding: $space-4;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 20px rgba($primary, 0.04);
}

.bento-small-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.bento-small-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: $radius-md;
  background: rgba($tertiary, 0.10);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bento-small-icon {
  font-size: 20px;
  color: $tertiary;
}

.bento-badge {
  font-size: 10px;
  font-weight: $font-weight-bold;
  color: $tertiary;
  background: rgba($tertiary, 0.10);
  padding: 2px 8px;
  border-radius: $radius-full;
}

.bento-small-title {
  display: block;
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: $text-primary;
  margin-bottom: 2px;
}

.bento-small-desc {
  display: block;
  font-size: 11px;
  color: $text-secondary;
}

.bento-small-desc-status {
  display: block;
  font-size: 11px;
  font-weight: $font-weight-bold;
  color: $primary;
}

/* 5. Service list */
.service-section {
  margin-bottom: $space-6;
}

.service-section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: $space-4;
}

.section-title {
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.section-more {
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $primary;
}

.service-list {
  background: $surface-container-low;
  border-radius: $radius-lg;
  padding: $space-2;
  display: flex;
  flex-direction: column;
  gap: $space-1;
}

.service-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: $surface-container-lowest;
  border-radius: $radius-md;
  padding: $space-4;
}

.service-row:active {
  background: rgba($primary-soft, 0.30);
}

.service-row-left {
  display: flex;
  align-items: center;
  gap: $space-4;
}

.service-icon {
  font-size: 20px;
  color: $text-secondary;
}

.service-row:active .service-icon {
  color: $primary;
}

.service-label {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.service-arrow {
  font-size: 18px;
  color: $text-muted;
  transition: transform 0.2s;
}

.service-row:active .service-arrow {
  color: $primary;
  transform: translateX(4px);
}

/* 6. Notification banner */
.notice-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba($primary, 0.05);
  border: 1px solid rgba($primary, 0.10);
  border-radius: $radius-lg;
  padding: $space-4;
  margin-bottom: $space-6;
}

.notice-left {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.notice-icon-wrap {
  width: 32px;
  height: 32px;
  border-radius: $radius-full;
  background: rgba($primary, 0.10);
  display: flex;
  align-items: center;
  justify-content: center;
}

.notice-icon {
  font-size: 18px;
  color: $primary;
}

.notice-text {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: $primary;
}

.notice-arrow {
  font-size: 14px;
  color: $primary;
}

.bottom-spacer {
  height: 5rem;
}
</style>
