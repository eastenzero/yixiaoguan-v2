<template>
  <view class="home-page">
    <!-- TopAppBar — fixed, ivory glass, brand + notifications only -->
    <view class="top-app-bar">
      <text class="brand-logo">医小管</text>
      <view class="top-actions">
        <view class="notif-btn" @click="goNotifications">
          <text class="material-symbols-outlined notif-icon">notifications</text>
          <view v-if="totalUnread > 0" class="notif-dot" />
        </view>
      </view>
    </view>

    <view class="main">
      <!-- 1. Personalized Greeting -->
      <view class="greeting animate-fade-up delay-1">
        <text class="greeting-sub">下午好，{{ displayName }}</text>
        <text class="greeting-title">智慧校园助理</text>
      </view>

      <!-- 2. AI Search Pill (No-Line; relies on ivory→white tonal shift) -->
      <view class="search-pill animate-fade-up delay-2" @click="goChat()">
        <view class="search-icon-box">
          <text class="material-symbols-outlined search-icon">auto_awesome</text>
        </view>
        <input class="search-input" placeholder="有什么可以帮你的？" disabled />
        <view class="search-action">
          <text class="search-action-text">提问</text>
        </view>
      </view>

      <!-- 3. Horizontal Scrollable Tag Chips -->
      <scroll-view scroll-x class="tag-scroll animate-fade-up delay-3" show-scrollbar="false">
        <view class="tag-list">
          <view v-for="t in tags" :key="t.id" class="tag-chip" @click="onTagClick(t)">
            <text class="tag-text">{{ t.label }}</text>
          </view>
        </view>
      </scroll-view>

      <!-- 4. Bento Feature Grid -->
      <view class="bento-grid animate-fade-up delay-4">
        <!-- Large: AI Assistant (gradient, 2 rows) -->
        <view class="bento-large" @click="goChat()">
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
          <view class="glow glow-secondary" />
          <view class="glow glow-corner" />
        </view>

        <!-- Small 1: Chat History (tertiary tint) -->
        <view class="bento-small" @click="onBentoClick(bentoItems[1])">
          <view class="icon-wrap icon-wrap-tertiary">
            <text class="material-symbols-outlined icon-tertiary">history</text>
          </view>
          <view class="bento-small-body">
            <text class="bento-small-title">对话历史</text>
            <text class="bento-small-desc">回顾过往提问</text>
          </view>
        </view>

        <!-- Small 2: Campus Services (primary tint) -->
        <view class="bento-small" @click="onBentoClick(bentoItems[2])">
          <view class="icon-wrap icon-wrap-primary">
            <text class="material-symbols-outlined icon-primary">grid_view</text>
          </view>
          <view class="bento-small-body">
            <text class="bento-small-title">校园服务</text>
            <text class="bento-small-desc">一站式办事入口</text>
          </view>
        </view>
      </view>

      <!-- 5. Quick Links List (Common Services) -->
      <view class="service-section animate-fade-up delay-5">
        <view class="service-header">
          <text class="section-title">常用服务</text>
          <text class="section-more" @click="showToastSoon">查看全部</text>
        </view>
        <view class="service-list">
          <view
            v-for="svc in services"
            :key="svc.id"
            class="service-row"
            @click="onServiceClick(svc)"
          >
            <view class="service-row-left">
              <text class="material-symbols-outlined service-icon">{{ svc.icon }}</text>
              <text class="service-label">{{ svc.label }}</text>
            </view>
            <text class="material-symbols-outlined service-arrow">chevron_right</text>
          </view>
        </view>
      </view>

      <!-- 6. Notification Banner -->
      <view v-if="notice" class="notice-banner animate-fade-up delay-6" @click="goNotifications">
        <view class="notice-left">
          <view class="notice-icon-wrap">
            <text class="material-symbols-outlined notice-icon">campaign</text>
          </view>
          <text class="notice-text">{{ notice }}</text>
        </view>
        <text class="material-symbols-outlined notice-arrow">arrow_forward</text>
      </view>
    </view>

    <view class="bottom-spacer" />
    <CustomTabBar current="home" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { getUnreadSummary } from '@/api/notification'
import CustomTabBar from '@/components/CustomTabBar.vue'

const userStore = useUserStore()

const displayName = computed(() => userStore.userInfo?.name || userStore.userInfo?.staff_id || '同学')
const totalUnread = ref(0)

// Static placeholder data for new sections
const tags = ref([
  { id: 't1', label: '奖学金政策' },
  { id: 't2', label: '选课指南' },
  { id: 't3', label: '图书馆开放' },
  { id: 't4', label: '校园卡充值' },
])

const bentoItems = ref([
  { id: 'b1', label: 'AI 问答', icon: 'auto_awesome', route: '/pages/chat/index' },
  { id: 'b2', label: '对话历史', icon: 'history', route: '/pages/chat/history' },
  { id: 'b3', label: '校园服务', icon: 'grid_view', route: '/pages/services/index' },
  { id: 'b4', label: '个人中心', icon: 'person', route: '/pages/profile/index' },
])

const services = ref([
  { id: 's1', label: '教务管理系统', icon: 'school', url: 'http://jwc.sdfmu.edu.cn' },
  { id: 's2', label: '图书馆', icon: 'library_books', url: 'http://202.194.232.127/index.html' },
  { id: 's3', label: '学生邮箱', icon: 'mail', url: 'https://mail.sdfmu.edu.cn/' },
  { id: 's4', label: '学校官网', icon: 'language', url: 'https://www.sdfmu.edu.cn' },
])

const notice = ref('你有 3 条未读通知')

onShow(() => {
  refreshUnreadSummary()
})

async function refreshUnreadSummary() {
  try {
    const response = await getUnreadSummary()
    totalUnread.value = response.total_unread || 0
  } catch {
    totalUnread.value = 0
  }
}

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

function openUrl(url: string) {
  // #ifdef H5
  window.open(url, '_blank')
  // #endif
  // #ifndef H5
  uni.navigateTo({ url: `/pages/services/webview?url=${encodeURIComponent(url)}` })
  // #endif
}

function onServiceClick(svc: { id: string; label: string; icon: string; url?: string }) {
  if (svc.url) {
    openUrl(svc.url)
  } else {
    uni.showToast({ title: '功能开发中', icon: 'none' })
  }
}

function goNotifications() {
  uni.showToast({ title: '即将上线', icon: 'none' })
}

function showToastSoon() {
  uni.switchTab({ url: '/pages/services/index' })
}
</script>

<style lang="scss" scoped>
@import '@/styles/tokens.scss';

// ─────────────────────────────────────────────────────────
// Aether Academic Home — 1:1 per docs/design/ui-references/
//   student-app-stitch/stitch_yixiaoguan_campus_assistant/
//   home_page/code.html
// 严守: No-Line · No-Shadow-as-default · wght 300 · 大半径
// ─────────────────────────────────────────────────────────

.home-page {
  min-height: 100vh;
  background: $surface;           // #faf5fb ivory canvas (L0)
  color: $on-surface;
  font-family: $font-body;
  padding-bottom: calc(var(--tabbar-safe) + $space-8);  /* tab bar + breathing room */
}

// ── TopAppBar (fixed glass; No-Line) ──
.top-app-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top) + $space-4) $space-6 $space-4;
  background: rgba(250, 245, 251, 0.80);   // ivory/80
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
}

.brand-logo {
  font-family: $font-headline;
  font-size: 20px;
  font-weight: 900;               // stitch: font-black
  letter-spacing: -0.01em;
  color: $primary;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: $space-2;
}

.notif-btn {
  position: relative;
  width: 40px;
  height: 40px;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease, transform 0.2s ease;

  &:active {
    background: rgba($primary, 0.08);
    transform: scale(0.95);
  }
}

.notif-icon {
  font-size: 24px;
  color: $on-surface-variant;
}

.notif-dot {
  position: absolute;
  top: 9px;
  right: 9px;
  width: 8px;
  height: 8px;
  border-radius: $radius-full;
  background: $error;
  box-shadow: 0 0 0 2px $surface;  // ring-2 ring-background
}

// ── Main canvas ──
.main {
  padding: calc(env(safe-area-inset-top) + 72px) $space-6 0;
  display: flex;
  flex-direction: column;
  gap: $space-8;                  // space-y-8
}

// 1. Greeting
.greeting {
  display: flex;
  flex-direction: column;
  gap: $space-1;
}

.greeting-sub {
  font-size: $body-md-size;
  font-weight: $font-weight-medium;
  color: $on-surface-variant;
  letter-spacing: -0.01em;
}

.greeting-title {
  font-family: $font-headline;
  font-size: 1.875rem;            // text-3xl = 30px
  font-weight: $font-weight-bold;
  color: $on-surface;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

// 2. AI Search Pill
.search-pill {
  position: relative;
  display: flex;
  align-items: center;
  gap: $space-2;
  background: $surface-container-lowest;     // pure white on ivory — tonal lift
  border-radius: $radius-full;
  padding: 6px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);  // very subtle ambient
}

.search-icon-box {
  width: 40px;
  height: 40px;
  border-radius: $radius-full;
  background: $primary-container;     // pastel lavender (stitch: bg-primary-container)
  color: $on-primary;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.search-icon {
  font-size: 20px;
  color: $on-primary;
  font-variation-settings: 'FILL' 1, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: $body-md-size;
  font-weight: $font-weight-medium;
  color: $on-surface-variant;
  padding: 0 $space-4;

  &::placeholder {
    color: $outline;
  }
}

.search-action {
  flex-shrink: 0;
  background: $surface-container-high;
  border-radius: $radius-full;
  padding: $space-2 $space-4;
  transition: transform 0.2s ease;

  &:active {
    transform: scale(0.95);
  }
}

.search-action-text {
  font-size: $label-md-size;
  font-weight: $font-weight-bold;
  color: $on-surface-variant;
}

// 3. Horizontal tag chips
.tag-scroll {
  margin: 0 (-$space-6);
  padding: 0 $space-6;
  white-space: nowrap;

  &::-webkit-scrollbar,
  :deep(::-webkit-scrollbar) {
    display: none;
  }
}

.tag-list {
  display: inline-flex;
  gap: $space-3;
}

.tag-chip {
  flex-shrink: 0;
  background: $surface-container-low;
  border-radius: $radius-full;
  padding: 10px $space-5;
  transition: background 0.2s ease, color 0.2s ease;

  &:active {
    background: $primary-container;
    .tag-text { color: $on-primary; }
  }
}

.tag-text {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $on-surface-variant;
}

// 4. Bento grid
.bento-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: $space-4;
  height: 280px;
}

.bento-large {
  grid-row: span 2;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, $primary 0%, $secondary 100%);  // stitch: from-primary to-secondary
  border-radius: $radius-lg;        // 2rem per MD3 DEFAULT lg
  padding: $space-6;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.2s ease;

  &:active {
    transform: scale(0.98);
  }
}

.bento-large-top {
  position: relative;
  z-index: 2;
}

.bento-large-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: $radius-md;        // rounded-2xl (1rem)
  background: rgba(255, 255, 255, 0.20);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-4;
}

.bento-large-icon {
  font-size: 24px;
  color: #ffffff;
  font-variation-settings: 'FILL' 1, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}

.bento-large-title {
  display: block;
  font-family: $font-headline;
  font-size: $font-size-xl;         // 20px
  font-weight: $font-weight-bold;
  color: #ffffff;
  margin-bottom: $space-2;
}

.bento-large-desc {
  display: block;
  font-size: $body-md-size;
  color: $primary-fixed;            // stitch: text-primary-fixed
  opacity: 0.90;
  line-height: 1.6;
}

.bento-large-action {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: $space-2;
  font-size: $label-md-size;
  font-weight: $font-weight-bold;
  color: #ffffff;
}

.bento-large-action-icon {
  font-size: 14px;
}

.glow {
  position: absolute;
  border-radius: $radius-full;
  pointer-events: none;
}

.glow-secondary {
  right: -16px;
  bottom: -16px;
  width: 96px;
  height: 96px;
  background: rgba(255, 255, 255, 0.10);
  filter: blur(32px);
}

.glow-corner {
  top: 0;
  right: 0;
  width: 128px;
  height: 128px;
  background: rgba($secondary-container, 0.20);
  filter: blur(48px);
}

.bento-small {
  position: relative;
  background: $surface-container-lowest;
  border-radius: $radius-lg;
  padding: $space-5;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: background 0.2s ease, transform 0.2s ease;

  &:active {
    background: $surface-container-high;
    transform: scale(0.98);
  }
}

.bento-small-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: $radius-md;        // rounded-xl (1rem)
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-wrap-tertiary {
  background: rgba($tertiary, 0.10);
}

.icon-tertiary {
  font-size: 20px;
  color: $tertiary;
}

.icon-wrap-primary {
  background: rgba($primary, 0.10);
}

.icon-primary {
  font-size: 20px;
  color: $primary;
}

.badge-hot {
  font-size: 10px;
  font-weight: $font-weight-bold;
  color: $tertiary;
  background: rgba($tertiary, 0.10);
  padding: 2px 8px;
  border-radius: $radius-full;
}

.bento-small-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.bento-small-title {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $on-surface;
}

.bento-small-desc {
  font-size: 11px;
  color: $on-surface-variant;
}

.bento-small-desc-active {
  font-size: 11px;
  font-weight: $font-weight-bold;
  color: $primary;
}

// 5. Quick links list (nested tonal tiers)
.service-section {
  display: flex;
  flex-direction: column;
  gap: $space-4;
}

.service-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.section-title {
  font-family: $font-headline;
  font-size: $font-size-lg;         // 18px
  font-weight: $font-weight-bold;
  color: $on-surface;
  letter-spacing: -0.01em;
}

.section-more {
  font-size: $label-md-size;
  font-weight: $font-weight-bold;
  color: $primary;
}

.service-list {
  background: $surface-container-low;   // L1 tonal nesting
  border-radius: $radius-lg;            // 2rem
  padding: $space-2;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.service-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: $surface-container-lowest; // white on L1 ivory
  border-radius: $radius-md;             // 1rem rounded-md
  padding: $space-4;
  transition: background 0.2s ease;

  &:active {
    background: rgba($primary-fixed, 0.30);
    .service-icon,
    .service-arrow,
    .service-label { color: $primary; }
    .service-arrow { transform: translateX(4px); }
  }
}

.service-row-left {
  display: flex;
  align-items: center;
  gap: $space-4;
}

.service-icon {
  font-size: 22px;
  color: $on-surface-variant;
  transition: color 0.2s ease;
}

.service-label {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $on-surface;
}

.service-arrow {
  font-size: 20px;
  color: #cbd5e1;                        // slate-300 等价
  transition: color 0.2s ease, transform 0.2s ease;
}

// 6. Notification banner
.notice-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba($primary, 0.05);
  border-radius: $radius-lg;             // 2rem; No-Line (ghost border removed)
  padding: $space-4;
  transition: transform 0.2s ease;

  &:active {
    transform: scale(0.99);
  }
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
  background: rgba($primary-container, 0.20);  // stitch: bg-primary-container/20
  display: flex;
  align-items: center;
  justify-content: center;
}

.notice-icon {
  font-size: 18px;
  color: $primary;
}

.notice-text {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $primary;
}

.notice-arrow {
  font-size: 14px;
  color: $primary;
}

.bottom-spacer {
  height: 2rem;
}
</style>
