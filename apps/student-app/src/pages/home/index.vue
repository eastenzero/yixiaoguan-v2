<template>
  <view class="home-page">
    <TopAppBar
      brand
      title="医小管"
      action-icon="notifications"
      :action-badge="totalUnread"
      action-accent
      @action="goNotifications"
    />

    <view class="greeting-section animate-fade-up">
      <text class="greeting-sub">{{ greetingPrefix }}，{{ displayName }}</text>
      <text class="greeting-title">智慧校园助理</text>
    </view>

    <!-- 2. Search pill (links to chat) -->
    <view class="search-pill animate-fade-up delay-1" @click="goChat()">
      <view class="search-icon-box">
        <text class="material-symbols-outlined search-icon">auto_awesome</text>
      </view>
      <input class="search-input" placeholder="有什么可以帮你的？" disabled />
      <view class="search-action">
        <text class="search-action-text">提问</text>
      </view>
    </view>

    <!-- 3. Horizontal category tags -->
    <scroll-view scroll-x class="tag-scroll animate-fade-up delay-2" show-scrollbar="false">
      <view class="tag-list">
        <view v-for="t in tags" :key="t.id" class="tag-chip" @click="onTagClick(t)">
          <text class="tag-text">{{ t.label }}</text>
        </view>
      </view>
    </scroll-view>

    <!-- 4. Bento grid of quick services -->
    <view class="bento-grid animate-fade-up delay-3">
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
    <view class="service-section animate-fade-up delay-4">
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
    <view v-if="notice" class="notice-banner animate-fade-up delay-5" @click="goNotifications">
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
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { getUnreadSummary } from '@/api/notification'
import CustomTabBar from '@/components/CustomTabBar.vue'
import TopAppBar from '@/components/TopAppBar.vue'

const userStore = useUserStore()

const displayName = computed(() => userStore.userInfo?.name || userStore.userInfo?.staff_id || '同学')
const totalUnread = ref(0)

const greetingPrefix = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 11) return '早上好'
  if (h < 13) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

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
@import '@/styles/theme.scss';

$top-bar-h: 56px;
$tab-bar-h: 64px;

.home-page {
  min-height: 100vh;
  padding: calc(env(safe-area-inset-top) + #{$top-bar-h} + #{$space-3}) $space-4
    calc(env(safe-area-inset-bottom) + #{$tab-bar-h} + #{$space-6});
  background: $bg-page;
  font-family: $font-family-sans;
}

/* Greeting */
.greeting-section {
  margin-bottom: $space-5;
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
  box-shadow: 0 10px 30px -8px rgba($primary, 0.10),
              0 1px 2px rgba($text-primary, 0.04);
  border: 1px solid rgba($primary, 0.06);
  margin-bottom: $space-5;
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;
}

.search-pill:active {
  transform: scale(0.99);
  box-shadow: 0 6px 20px -8px rgba($primary, 0.14),
              0 1px 2px rgba($text-primary, 0.06);
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
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  border-radius: $radius-full;
  padding: $space-2 $space-4;
  box-shadow: 0 4px 12px -4px rgba($primary, 0.40);
}

.search-action-text {
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $text-inverse;
  letter-spacing: 0.02em;
}

/* 3. Horizontal tags */
.tag-scroll {
  margin-left: -$space-4;
  margin-right: -$space-4;
  padding-left: $space-4;
  padding-right: $space-4;
  margin-bottom: $space-5;
  scrollbar-width: none;

  &::-webkit-scrollbar,
  :deep(::-webkit-scrollbar) {
    display: none;
    width: 0;
    height: 0;
  }
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
  border: 1px solid transparent;
  transition: background 0.18s ease-out, border-color 0.18s ease-out, transform 0.18s ease-out;
}

.tag-chip:active {
  background: $primary-soft;
  border-color: rgba($primary, 0.20);
  transform: scale(0.96);

  .tag-text {
    color: $primary;
  }
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
  background: linear-gradient(135deg, $primary 0%, $secondary 60%, $primary-hover 100%);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: $space-5;
  box-shadow: 0 8px 24px -8px rgba($primary, 0.40);
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;
}

.bento-large:active {
  transform: scale(0.98);
  box-shadow: 0 4px 16px -8px rgba($primary, 0.50);
}

.bento-large-top {
  position: relative;
  z-index: 2;
}

.bento-large-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: $radius-md;
  background: rgba($bg-card, 0.20);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
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
  color: rgba($bg-card, 0.90);
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
  background: rgba($bg-card, 0.10);
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
  background: $bg-card;
  padding: $space-4;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 1px 2px rgba($text-primary, 0.04),
              0 4px 16px -4px rgba($primary, 0.06);
  border: 1px solid rgba($primary, 0.04);
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;
}

.bento-small:active {
  transform: scale(0.97);
  box-shadow: 0 2px 4px rgba($text-primary, 0.06),
              0 6px 18px -4px rgba($primary, 0.14);
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
  background: rgba($warning, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
}

.bento-small-icon {
  font-size: 20px;
  color: $warning;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.bento-badge {
  font-size: 10px;
  font-weight: $font-weight-bold;
  color: $warning;
  background: rgba($warning, 0.14);
  padding: 2px 8px;
  border-radius: $radius-full;
  letter-spacing: 0.05em;
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
  background: $bg-card;
  border-radius: $radius-md;
  padding: $space-4;
  transition: background 0.18s ease-out, transform 0.18s ease-out;
}

.service-row:active {
  background: $primary-soft;
  transform: scale(0.99);
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
  transition: background 0.18s ease-out, transform 0.18s ease-out;
}

.notice-banner:active {
  background: rgba($primary, 0.10);
  transform: scale(0.99);
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
  height: $space-12;
}
</style>
