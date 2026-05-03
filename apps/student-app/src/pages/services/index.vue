<template>
  <view class="services-page">
    <TopAppBar title="服务大厅" />

    <scroll-view class="main-content" scroll-y>
      <view class="hero-card animate-fade-up">
        <view class="hero-inner">
          <text class="hero-label">CAMPUS SERVICES</text>
          <text class="hero-title">校园服务中心</text>
          <text class="hero-subtitle">便捷办事 · 智慧生活</text>
        </view>
        <view class="hero-glow hero-glow--bottom" />
        <view class="hero-glow hero-glow--top" />
        <view class="hero-bg-icon">
          <text class="material-symbols-outlined hero-icon-bg">school</text>
        </view>
      </view>

      <view class="section animate-fade-up delay-1">
        <view class="section-header">
          <text class="section-title">快捷入口</text>
          <text class="section-badge">QUICK LINKS</text>
        </view>
        <view class="quick-grid">
          <view class="quick-large" @click="openUrl('https://www.sdfmu.edu.cn')">
            <view class="quick-large-icon-wrap">
              <text class="material-symbols-outlined quick-large-icon">home</text>
            </view>
            <view class="quick-large-body">
              <text class="quick-label">校主页</text>
              <text class="quick-meta">官网入口</text>
            </view>
          </view>
          <view class="quick-stack">
            <view class="quick-row" @click="openUrl('http://portal.sdfmu.edu.cn')">
              <view class="quick-icon-wrap quick-icon-wrap--primary">
                <text class="material-symbols-outlined quick-icon">gate</text>
              </view>
              <text class="quick-label">信息门户</text>
            </view>
            <view class="quick-row" @click="openUrl('http://portal.sdfmu.edu.cn')">
              <view class="quick-icon-wrap quick-icon-wrap--success">
                <text class="material-symbols-outlined quick-icon">cloud_done</text>
              </view>
              <text class="quick-label">服务大厅</text>
            </view>
          </view>
        </view>
        <view class="quick-wide" @click="showDevToast">
          <view class="quick-wide-left">
            <view class="quick-icon-wrap quick-icon-wrap--primary">
              <text class="material-symbols-outlined quick-icon">message</text>
            </view>
            <view class="quick-wide-body">
              <text class="quick-label">统一消息平台</text>
              <text class="quick-meta">通知 · 公告 · 校园动态</text>
            </view>
          </view>
          <text class="material-symbols-outlined chevron-icon">chevron_right</text>
        </view>
      </view>

      <view class="section animate-fade-up delay-2">
        <text class="section-title">校园服务</text>
        <view class="campus-grid">
          <view
            v-for="(item, idx) in campusServices"
            :key="idx"
            class="campus-item"
            @click="handleServiceClick(item)"
          >
            <view class="campus-icon-box">
              <text class="material-symbols-outlined campus-icon">{{ item.icon }}</text>
            </view>
            <text class="campus-label">{{ item.label }}</text>
          </view>
        </view>
      </view>

      <view class="section animate-fade-up delay-3">
        <text class="section-title">学业</text>
        <view class="query-grid">
          <view class="query-card" @click="showDevToast">
            <view class="query-icon-box query-icon-box--primary">
              <text class="material-symbols-outlined query-icon">calendar_month</text>
            </view>
            <view class="query-info">
              <text class="query-name">学生课表</text>
              <text class="query-meta">本学期</text>
            </view>
          </view>
          <view class="query-card" @click="openUrl('http://jwc.sdfmu.edu.cn')">
            <view class="query-icon-box query-icon-box--warning">
              <text class="material-symbols-outlined query-icon">grade</text>
            </view>
            <view class="query-info">
              <text class="query-name">成绩查询</text>
              <text class="query-meta">教务系统</text>
            </view>
          </view>
          <view class="query-card" @click="openUrl('http://202.194.232.127/index.html')">
            <view class="query-icon-box query-icon-box--success">
              <text class="material-symbols-outlined query-icon">library_books</text>
            </view>
            <view class="query-info">
              <text class="query-name">图书馆</text>
              <text class="query-meta">借阅状态</text>
            </view>
          </view>
          <view class="query-card" @click="openUrl('https://mail.sdfmu.edu.cn/')">
            <view class="query-icon-box query-icon-box--info">
              <text class="material-symbols-outlined query-icon">mail</text>
            </view>
            <view class="query-info">
              <text class="query-name">学生邮箱</text>
              <text class="query-meta">收件箱</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section animate-fade-up delay-4">
        <text class="section-title">个人</text>
        <view class="personal-list">
          <view class="personal-item" @click="showDevToast">
            <view class="personal-left">
              <view class="personal-icon-wrap">
                <text class="material-symbols-outlined personal-icon">event_note</text>
              </view>
              <text class="personal-name">个人日程</text>
            </view>
            <text class="material-symbols-outlined chevron-icon">chevron_right</text>
          </view>
          <view class="personal-item" @click="showDevToast">
            <view class="personal-left">
              <view class="personal-icon-wrap">
                <text class="material-symbols-outlined personal-icon">help_center</text>
              </view>
              <text class="personal-name">我的提问</text>
            </view>
            <text class="material-symbols-outlined chevron-icon">chevron_right</text>
          </view>
        </view>
      </view>

      <view class="bottom-safe" />
    </scroll-view>

    <CustomTabBar current="services" />
  </view>
</template>

<script setup lang="ts">
import CustomTabBar from '@/components/CustomTabBar.vue'
import TopAppBar from '@/components/TopAppBar.vue'

interface ServiceItem {
  icon: string
  label: string
  url?: string
  wechatOnly?: boolean
}

const campusServices: ServiceItem[] = [
  { icon: 'meeting_room', label: '空教室申请', url: undefined },
  { icon: 'assignment', label: '我的申请', url: undefined },
  { icon: 'handyman', label: '网上报修', url: 'https://metc.sdfmu.edu.cn/info/1073/1954.htm' },
  { icon: 'feedback', label: '接诉即办', wechatOnly: true },
  { icon: 'wifi', label: '校园网', url: 'http://vpnportal.sdfmu.edu.cn' },
  { icon: 'local_hospital', label: '校医院', url: undefined },
  { icon: 'directions_bus', label: '班车查询', wechatOnly: true },
  { icon: 'more_horiz', label: '更多', url: undefined },
]

function openUrl(url: string) {
  // #ifdef H5
  window.open(url, '_blank')
  // #endif
  // #ifndef H5
  uni.navigateTo({ url: `/pages/services/webview?url=${encodeURIComponent(url)}` })
  // #endif
}

function wechatOnlyToast() {
  uni.showToast({ title: '请在山一大企业微信中使用', icon: 'none', duration: 2000 })
}

function showDevToast() {
  uni.showToast({ title: '功能开发中，敬请期待', icon: 'none', duration: 2000 })
}

function handleServiceClick(item: ServiceItem) {
  if (item.url) {
    openUrl(item.url)
  } else if (item.wechatOnly) {
    wechatOnlyToast()
  } else {
    showDevToast()
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/theme.scss';

$top-bar-h: 56px;
$tab-bar-h: 64px;

.services-page {
  min-height: 100vh;
  background: $bg-page;
  display: flex;
  flex-direction: column;
  font-family: $font-family-sans;
  color: $text-primary;
}

.main-content {
  height: 100vh;
  padding: calc(env(safe-area-inset-top) + #{$top-bar-h} + #{$space-4}) $space-4
    calc(env(safe-area-inset-bottom) + #{$tab-bar-h} + #{$space-6});
  box-sizing: border-box;
}

// ============================================================
// Hero card
// ============================================================
.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: $radius-lg;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 60%, $primary-10 100%);
  padding: $space-8 $space-6;
  color: $text-inverse;
  margin-bottom: $space-6;
  box-shadow: 0 12px 32px -8px rgba($primary, 0.40);
}

.hero-inner {
  position: relative;
  z-index: 2;
}

.hero-label {
  display: block;
  font-size: 11px;
  font-weight: $font-weight-bold;
  letter-spacing: 0.20em;
  opacity: 0.80;
  margin-bottom: $space-2;
}

.hero-title {
  display: block;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: $space-1;
}

.hero-subtitle {
  display: block;
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: rgba($bg-card, 0.80);
  letter-spacing: 0.02em;
}

.hero-glow {
  position: absolute;
  border-radius: $radius-full;
  pointer-events: none;
  filter: blur(30px);
}

.hero-glow--bottom {
  right: -40px;
  bottom: -40px;
  width: 192px;
  height: 192px;
  background: rgba($bg-card, 0.12);
}

.hero-glow--top {
  top: -32px;
  right: 40px;
  width: 128px;
  height: 128px;
  background: rgba($bg-card, 0.10);
}

.hero-bg-icon {
  position: absolute;
  right: $space-4;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
}

.hero-icon-bg {
  font-size: 70px;
  opacity: 0.16;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

// ============================================================
// Section
// ============================================================
.section {
  margin-bottom: $space-8;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $space-4;
}

.section-title {
  display: block;
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
  letter-spacing: -0.01em;
  margin-bottom: $space-4;
}

.section-header .section-title {
  margin-bottom: 0;
}

.section-badge {
  font-size: 10px;
  font-weight: $font-weight-bold;
  letter-spacing: 0.15em;
  color: $primary;
  padding: 3px $space-3;
  background: $primary-soft;
  border-radius: $radius-full;
}

// ============================================================
// Quick links
// ============================================================
.quick-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $space-3;
  margin-bottom: $space-3;
}

.quick-large,
.quick-row,
.quick-wide {
  background: $bg-card;
  border-radius: $radius-md;
  box-shadow: 0 1px 2px rgba($text-primary, 0.04),
              0 4px 12px -4px rgba($primary, 0.06);
  border: 1px solid rgba($primary, 0.04);
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;

  &:active {
    transform: scale(0.97);
    box-shadow: 0 2px 4px rgba($text-primary, 0.06),
                0 6px 18px -4px rgba($primary, 0.16);
  }
}

.quick-large {
  padding: $space-4;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  aspect-ratio: 1;
}

.quick-large-icon-wrap {
  width: 48px;
  height: 48px;
  border-radius: $radius-md;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
}

.quick-large-icon {
  font-size: 26px;
  color: $primary;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.quick-large-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.quick-stack {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.quick-row {
  flex: 1;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-3;
}

.quick-wide {
  margin-top: 0;
  padding: $space-4;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.quick-wide-left {
  display: flex;
  align-items: center;
  gap: $space-3;
  min-width: 0;
}

.quick-wide-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.quick-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &--primary {
    background: $primary-soft;
    .quick-icon { color: $primary; }
  }
  &--success {
    background: rgba($success, 0.12);
    .quick-icon { color: $success; }
  }
}

.quick-icon {
  font-size: 22px;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.quick-label {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.quick-meta {
  font-size: 11px;
  color: $text-secondary;
  font-weight: $font-weight-medium;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// ============================================================
// Campus grid (4×N icons in soft container)
// ============================================================
.campus-grid {
  background: $bg-card;
  border: 1px solid rgba($primary, 0.04);
  box-shadow: 0 1px 2px rgba($text-primary, 0.03),
              0 4px 12px -6px rgba($primary, 0.06);
  border-radius: $radius-lg;
  padding: $space-5 $space-3;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: $space-5 $space-2;
}

.campus-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-2;
  transition: transform 0.18s ease-out;
}

.campus-item:active {
  transform: scale(0.92);
}

.campus-icon-box {
  width: 48px;
  height: 48px;
  border-radius: $radius-md;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.18s ease-out;
}

.campus-item:active .campus-icon-box {
  background: $primary;
}

.campus-icon {
  font-size: 24px;
  color: $primary;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
  transition: color 0.18s ease-out;
}

.campus-item:active .campus-icon {
  color: $text-inverse;
}

.campus-label {
  font-size: 11px;
  font-weight: $font-weight-semibold;
  color: $text-secondary;
  text-align: center;
  line-height: $line-height-tight;
}

// ============================================================
// Query cards (academic)
// ============================================================
.query-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: $space-3;
}

.query-card {
  background: $bg-card;
  padding: $space-4;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  gap: $space-3;
  box-shadow: 0 1px 2px rgba($text-primary, 0.04),
              0 4px 12px -4px rgba($primary, 0.06);
  border: 1px solid rgba($primary, 0.04);
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out;
}

.query-card:active {
  transform: scale(0.96);
  box-shadow: 0 2px 4px rgba($text-primary, 0.06),
              0 6px 16px -4px rgba($primary, 0.14);
}

.query-icon-box {
  width: 40px;
  height: 40px;
  border-radius: $radius-md;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &--primary {
    background: $primary-soft;
    .query-icon { color: $primary; }
  }
  &--warning {
    background: rgba($warning, 0.12);
    .query-icon { color: $warning; }
  }
  &--success {
    background: rgba($success, 0.12);
    .query-icon { color: $success; }
  }
  &--info {
    background: rgba($info, 0.12);
    .query-icon { color: $info; }
  }
}

.query-icon {
  font-size: 22px;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.query-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.query-name {
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.query-meta {
  font-size: 11px;
  color: $text-secondary;
  font-weight: $font-weight-medium;
}

// ============================================================
// Personal list
// ============================================================
.personal-list {
  background: $bg-card;
  border-radius: $radius-lg;
  overflow: hidden;
  box-shadow: 0 1px 2px rgba($text-primary, 0.04),
              0 4px 12px -4px rgba($primary, 0.06);
  border: 1px solid rgba($primary, 0.04);
}

.personal-item {
  padding: $space-4 $space-5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: background 0.18s ease-out;
  border-bottom: 1px solid $divider;

  &:last-child {
    border-bottom: none;
  }

  &:active {
    background: $primary-soft;
  }
}

.personal-left {
  display: flex;
  align-items: center;
  gap: $space-4;
}

.personal-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: $radius-full;
  background: $primary-soft;
  display: flex;
  align-items: center;
  justify-content: center;
}

.personal-icon {
  font-size: 20px;
  color: $primary;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
}

.personal-name {
  font-size: $font-size-base;
  font-weight: $font-weight-semibold;
  color: $text-primary;
}

.chevron-icon {
  font-size: 20px;
  color: $text-muted;
}

.bottom-safe {
  height: $space-12;
}
</style>
