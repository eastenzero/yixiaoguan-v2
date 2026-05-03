<template>
  <view class="services-page">
    <view class="top-app-bar">
      <view class="bar-left">
        <text class="bar-title">服务大厅</text>
      </view>
    </view>

    <scroll-view class="main-content" scroll-y>
      <view class="hero-card">
        <view class="hero-inner">
          <text class="hero-label">CAMPUS SERVICES</text>
          <text class="hero-title">校园服务中心</text>
          <text class="hero-subtitle">便捷办事 · 智慧生活</text>
        </view>
        <view class="hero-blur" />
        <view class="hero-bg-icon">
          <text class="material-symbols-outlined hero-icon-bg">school</text>
        </view>
      </view>

      <view class="section">
        <view class="section-header">
          <text class="section-title">快捷入口</text>
          <text class="section-badge">QUICK LINKS</text>
        </view>
        <view class="quick-grid">
          <view class="quick-large" @click="openUrl('https://www.sdfmu.edu.cn')">
            <text class="material-symbols-outlined quick-icon text-primary">home</text>
            <text class="quick-label">校主页</text>
          </view>
          <view class="quick-stack">
            <view class="quick-row" @click="openUrl('http://portal.sdfmu.edu.cn')">
              <text class="material-symbols-outlined quick-icon text-secondary">gate</text>
              <text class="quick-label">信息门户</text>
            </view>
            <view class="quick-row" @click="openUrl('http://portal.sdfmu.edu.cn')">
              <text class="material-symbols-outlined quick-icon text-tertiary">cloud_done</text>
              <text class="quick-label">服务大厅</text>
            </view>
          </view>
        </view>
        <view class="quick-wide" @click="showDevToast">
          <view class="quick-wide-left">
            <text class="material-symbols-outlined quick-icon text-primary">message</text>
            <text class="quick-label">统一消息平台</text>
          </view>
          <text class="material-symbols-outlined text-outline-variant">chevron_right</text>
        </view>
      </view>

      <view class="section">
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

      <view class="section">
        <text class="section-title">学业</text>
        <view class="query-grid">
          <view class="query-card" @click="showDevToast">
            <view class="query-icon-box bg-secondary-light">
              <text class="material-symbols-outlined text-secondary">calendar_month</text>
            </view>
            <view class="query-info">
              <text class="query-name">学生课表</text>
              <text class="query-meta">本学期</text>
            </view>
          </view>
          <view class="query-card" @click="openUrl('http://jwc.sdfmu.edu.cn')">
            <view class="query-icon-box bg-tertiary-light">
              <text class="material-symbols-outlined text-tertiary">grade</text>
            </view>
            <view class="query-info">
              <text class="query-name">成绩查询</text>
              <text class="query-meta">教务系统</text>
            </view>
          </view>
          <view class="query-card" @click="openUrl('http://202.194.232.127/index.html')">
            <view class="query-icon-box bg-primary-light">
              <text class="material-symbols-outlined text-primary">library_books</text>
            </view>
            <view class="query-info">
              <text class="query-name">图书馆</text>
              <text class="query-meta">借阅状态</text>
            </view>
          </view>
          <view class="query-card" @click="openUrl('https://mail.sdfmu.edu.cn/')">
            <view class="query-icon-box bg-error-light">
              <text class="material-symbols-outlined text-error">mail</text>
            </view>
            <view class="query-info">
              <text class="query-name">学生邮箱</text>
              <text class="query-meta">收件箱</text>
            </view>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">个人</text>
        <view class="personal-list">
          <view class="personal-item border-bottom" @click="showDevToast">
            <view class="personal-left">
              <text class="material-symbols-outlined text-primary">event_note</text>
              <text class="personal-name">个人日程</text>
            </view>
            <text class="material-symbols-outlined text-outline-variant">chevron_right</text>
          </view>
          <view class="personal-item" @click="showDevToast">
            <view class="personal-left">
              <text class="material-symbols-outlined text-primary">help_center</text>
              <text class="personal-name">我的提问</text>
            </view>
            <view class="personal-right">
              <text class="material-symbols-outlined text-outline-variant">chevron_right</text>
            </view>
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

<style scoped>
.services-page {
  min-height: 100vh;
  background: #f7f9fb;
  display: flex;
  flex-direction: column;
}

.top-app-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1.5rem;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(247, 249, 251, 0.9);
  backdrop-filter: blur(10px);
  box-sizing: border-box;
}
.bar-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #630ed4;
  letter-spacing: -0.01563rem;
}

.main-content {
  height: 100vh;
  padding: calc(var(--status-bar-height, 44px) + 3rem) 1.5rem 6.25rem;
  box-sizing: border-box;
}

.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: 1rem;
  background: linear-gradient(135deg, #630ed4, #7c3aed);
  padding: 2rem;
  color: #fff;
  margin-bottom: 2rem;
}
.hero-inner { position: relative; z-index: 10; }
.hero-label { font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.2em; opacity: 0.8; margin-bottom: 0.5rem; display: block; }
.hero-title { font-size: 1.75rem; font-weight: 800; margin-bottom: 0.375rem; letter-spacing: -0.03125rem; display: block; }
.hero-subtitle { font-size: 0.875rem; font-weight: 500; color: rgba(255, 255, 255, 0.8); display: block; }
.hero-blur { position: absolute; right: -2.5rem; bottom: -2.5rem; width: 12rem; height: 12rem; background: rgba(255, 255, 255, 0.1); border-radius: 50%; filter: blur(1.875rem); }
.hero-bg-icon { position: absolute; right: 1rem; top: 50%; transform: translateY(-50%); }
.hero-icon-bg { font-size: 4.375rem; opacity: 0.2; color: #fff; }

.section { margin-bottom: 2rem; }
.section-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.section-title { font-size: 1.125rem; font-weight: 700; color: #191c1e; letter-spacing: -0.01563rem; display: block; margin-bottom: 1rem; }
.section-header .section-title { margin-bottom: 0; }
.section-badge { font-size: 0.625rem; font-weight: 700; color: #630ed4; padding: 0.25rem 0.75rem; background: rgba(99, 14, 212, 0.1); border-radius: 31.21875rem; }

.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem; }
.quick-large { background: #fff; padding: 1.25rem; border-radius: 0.75rem; display: flex; flex-direction: column; justify-content: space-between; aspect-ratio: 1; }
.quick-large:active { transform: scale(0.98); }
.quick-stack { display: flex; flex-direction: column; gap: 0.75rem; }
.quick-row { flex: 1; background: #fff; padding: 1rem; border-radius: 0.75rem; display: flex; align-items: center; gap: 0.75rem; }
.quick-row:active { transform: scale(0.98); }
.quick-icon { font-size: 1.5rem; }
.quick-label { font-size: 0.875rem; font-weight: 700; color: #191c1e; }
.quick-wide { background: #fff; padding: 1.25rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: space-between; }
.quick-wide:active { transform: scale(0.98); }
.quick-wide-left { display: flex; align-items: center; gap: 1rem; }

.campus-grid { background: #f2f4f6; border-radius: 0.75rem; padding: 1.5rem; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem 0.5rem; }
.campus-item { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
.campus-item:active .campus-icon-box { transform: scale(0.9); }
.campus-icon-box { width: 3rem; height: 3rem; border-radius: 1rem; background: #fff; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }
.campus-icon { font-size: 1.5rem; color: #630ed4; }
.campus-label { font-size: 0.6875rem; font-weight: 700; color: #4a4455; text-align: center; line-height: 1.3; }

.query-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.query-card { background: #fff; padding: 1rem; border-radius: 0.75rem; display: flex; align-items: center; gap: 0.75rem; }
.query-card:active { transform: scale(0.95); }
.query-icon-box { width: 2.5rem; height: 2.5rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; }
.query-info { display: flex; flex-direction: column; gap: 0.125rem; }
.query-name { font-size: 0.875rem; font-weight: 700; color: #191c1e; }
.query-meta { font-size: 0.625rem; color: #4a4455; }

.personal-list { background: #fff; border-radius: 0.75rem; overflow: hidden; }
.personal-item { padding: 1.25rem; display: flex; justify-content: space-between; align-items: center; }
.personal-item:active { background: #e6e8ea; }
.border-bottom { border-bottom: 0.0625rem solid #eceef0; }
.personal-left { display: flex; align-items: center; gap: 1rem; }
.personal-name { font-size: 0.875rem; font-weight: 700; color: #191c1e; }
.personal-right { display: flex; align-items: center; gap: 0.5rem; }

.text-primary { color: #630ed4; }
.text-secondary { color: #6e3aca; }
.text-tertiary { color: #a15100; }
.text-error { color: #ba1a1a; }
.text-outline-variant { color: #ccc3d8; }
.bg-primary-light { background: rgba(99, 14, 212, 0.1); }
.bg-secondary-light { background: rgba(110, 58, 202, 0.1); }
.bg-tertiary-light { background: rgba(161, 81, 0, 0.1); }
.bg-error-light { background: rgba(186, 26, 26, 0.1); }

.bottom-safe { height: 5rem; }
</style>
