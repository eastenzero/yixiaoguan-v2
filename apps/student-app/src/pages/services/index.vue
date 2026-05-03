<template>
  <view class="services-page">
    <view class="top-app-bar">
      <view class="bar-left">
        <text class="bar-title">服务指南</text>
      </view>
    </view>

    <scroll-view class="main-content" scroll-y>
      <view class="hero-card">
        <view class="hero-inner">
          <text class="hero-label">CAMPUS SERVICES</text>
          <text class="hero-title">校园服务指南</text>
          <text class="hero-subtitle">常见事务 · 流程咨询 · 入口导航</text>
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
          <view class="quick-large" @click="openExternal('https://www.sdfmu.edu.cn')">
            <text class="material-symbols-outlined quick-icon text-primary">home</text>
            <view class="quick-label-row">
              <text class="quick-label">校主页</text>
              <text class="material-symbols-outlined meta-external">open_in_new</text>
            </view>
          </view>
          <view class="quick-stack">
            <view class="quick-row" @click="openExternal('http://portal.sdfmu.edu.cn')">
              <text class="material-symbols-outlined quick-icon text-secondary">gate</text>
              <text class="quick-label">信息门户</text>
              <text class="material-symbols-outlined meta-external">open_in_new</text>
            </view>
            <view class="quick-row" @click="openExternal('http://portal.sdfmu.edu.cn')">
              <text class="material-symbols-outlined quick-icon text-tertiary">cloud_done</text>
              <text class="quick-label">服务大厅</text>
              <text class="material-symbols-outlined meta-external">open_in_new</text>
            </view>
          </view>
        </view>
        <view class="quick-wide" @click="handleComingSoon('统一消息平台', '我在哪里查看学校通知和老师回复？')">
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
              <text v-if="item.url" class="material-symbols-outlined badge-external">open_in_new</text>
            </view>
            <text class="campus-label">{{ item.label }}</text>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">学业</text>
        <view class="query-grid">
          <view class="query-card" @click="handleAiQuestion('学生课表在哪里查看？')">
            <view class="query-icon-box bg-secondary-light">
              <text class="material-symbols-outlined text-secondary">calendar_month</text>
            </view>
            <view class="query-info">
              <text class="query-name">学生课表</text>
              <text class="query-meta">问医小管</text>
            </view>
          </view>
          <view class="query-card" @click="openExternal('http://jwc.sdfmu.edu.cn')">
            <view class="query-icon-box bg-tertiary-light">
              <text class="material-symbols-outlined text-tertiary">grade</text>
            </view>
            <view class="query-info">
              <text class="query-name">成绩查询</text>
              <text class="query-meta">教务系统 <text class="material-symbols-outlined meta-external">open_in_new</text></text>
            </view>
          </view>
          <view class="query-card" @click="openExternal('http://202.194.232.127/index.html')">
            <view class="query-icon-box bg-primary-light">
              <text class="material-symbols-outlined text-primary">library_books</text>
            </view>
            <view class="query-info">
              <text class="query-name">图书馆</text>
              <text class="query-meta">借阅状态 <text class="material-symbols-outlined meta-external">open_in_new</text></text>
            </view>
          </view>
          <view class="query-card" @click="openExternal('https://mail.sdfmu.edu.cn/')">
            <view class="query-icon-box bg-error-light">
              <text class="material-symbols-outlined text-error">mail</text>
            </view>
            <view class="query-info">
              <text class="query-name">学生邮箱</text>
              <text class="query-meta">收件箱 <text class="material-symbols-outlined meta-external">open_in_new</text></text>
            </view>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">个人</text>
        <view class="personal-list">
          <view class="personal-item border-bottom" @click="handleComingSoon('个人日程', '学校重要日程在哪里查看？')">
            <view class="personal-left">
              <text class="material-symbols-outlined text-primary">event_note</text>
              <text class="personal-name">个人日程</text>
            </view>
            <text class="material-symbols-outlined text-outline-variant">chevron_right</text>
          </view>
          <view class="personal-item" @click="goChatHistory">
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
    <FeatureNoticeSheet />
  </view>
</template>

<script setup lang="ts">
import CustomTabBar from '@/components/CustomTabBar.vue'
import FeatureNoticeSheet from '@/components/FeatureNoticeSheet.vue'
import { openAiQuestion, openExternal, showComingSoon } from '@/composables/useServiceNavigation'

interface ServiceItem {
  icon: string
  label: string
  url?: string
  aiQuestion?: string
  comingSoon?: boolean
}

const campusServices: ServiceItem[] = [
  { icon: 'meeting_room', label: '空教室申请', aiQuestion: '我想申请空教室，办理流程是什么？' },
  { icon: 'assignment', label: '我的申请', comingSoon: true, aiQuestion: '我想查看或跟进自己的校园事务申请，应该去哪里？' },
  { icon: 'handyman', label: '网上报修', url: 'https://metc.sdfmu.edu.cn/info/1073/1954.htm' },
  { icon: 'feedback', label: '接诉即办', aiQuestion: '我想反馈校园问题或投诉建议，应该怎么提交？' },
  { icon: 'wifi', label: '校园网', url: 'http://vpnportal.sdfmu.edu.cn' },
  { icon: 'local_hospital', label: '校医院', aiQuestion: '校医院就诊流程和开放时间是什么？' },
  { icon: 'directions_bus', label: '班车查询', aiQuestion: '班车时刻表在哪里查询？' },
  { icon: 'more_horiz', label: '更多', aiQuestion: '医小管可以帮我做什么？' },
]

function handleServiceClick(item: ServiceItem) {
  if (item.url) {
    openExternal(item.url)
  } else if (item.comingSoon) {
    showComingSoon(item.label, item.aiQuestion)
  } else if (item.aiQuestion) {
    openAiQuestion(item.aiQuestion)
  }
}

function handleAiQuestion(question: string) {
  openAiQuestion(question)
}

function handleComingSoon(name: string, question?: string) {
  showComingSoon(name, question)
}

function goChatHistory() {
  uni.navigateTo({ url: '/pages/chat/history' })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.services-page {
  min-height: 100vh;
  background: $surface;
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
  background: rgba(250, 245, 251, 0.90);    /* ivory/90 跟着 $surface */
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
  box-sizing: border-box;
}
.bar-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: #5b21b6;
  letter-spacing: -0.01563rem;
}

.main-content {
  height: 100vh;
  padding: calc(var(--status-bar-height, 44px) + 3rem) 1.5rem 0;
  /* 底部空间由 .bottom-safe spacer 通过 var(--tabbar-safe) 提供 */
  box-sizing: border-box;
}

.hero-card {
  position: relative;
  overflow: hidden;
  border-radius: $radius-lg;
  background: linear-gradient(135deg, $primary, $secondary);
  padding: 2rem;
  color: #fff;
  margin-bottom: 2rem;
  box-shadow: $shadow-fab;
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
.section-title { font-size: 1.125rem; font-weight: 700; color: $on-surface; letter-spacing: -0.01563rem; display: block; margin-bottom: 1rem; }
.section-header .section-title { margin-bottom: 0; }
.section-badge { font-size: 0.625rem; font-weight: 700; color: $primary; padding: 0.25rem 0.75rem; background: rgba($primary, 0.10); border-radius: 31.21875rem; }

.quick-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; margin-bottom: 0.75rem; }
.quick-large { background: #fff; padding: 1.25rem; border-radius: 0.75rem; display: flex; flex-direction: column; justify-content: space-between; aspect-ratio: 1; }
.quick-large:active { transform: scale(0.98); }
.quick-stack { display: flex; flex-direction: column; gap: 0.75rem; }
.quick-row { flex: 1; background: #fff; padding: 1rem; border-radius: 0.75rem; display: flex; align-items: center; gap: 0.75rem; }
.quick-row:active { transform: scale(0.98); }
.quick-icon { font-size: 1.5rem; }
.quick-label { font-size: 0.875rem; font-weight: 700; color: $on-surface; }
.quick-label-row { display: flex; align-items: center; gap: 4px; }
.quick-wide { background: #fff; padding: 1.25rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: space-between; }
.quick-wide:active { transform: scale(0.98); }
.quick-wide-left { display: flex; align-items: center; gap: 1rem; }

.campus-grid { background: $surface-container-low; border-radius: $radius-md; padding: 1.5rem; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem 0.5rem; }
.campus-item { display: flex; flex-direction: column; align-items: center; gap: 0.5rem; }
.campus-item:active .campus-icon-box { transform: scale(0.9); }
.campus-icon-box { position: relative; width: 3rem; height: 3rem; border-radius: 1rem; background: #fff; display: flex; align-items: center; justify-content: center; transition: transform 0.2s; }

.badge-external {
  position: absolute;
  top: -2px;
  right: -6px;
  font-size: 12px;
  color: $outline;
  font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 20;
}

.meta-external {
  font-size: 10px;
  color: $outline;
  vertical-align: middle;
  margin-left: 2px;
  font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 20;
}
.campus-icon { font-size: 1.5rem; color: $primary; }
.campus-label { font-size: 0.6875rem; font-weight: 700; color: $on-surface; text-align: center; line-height: 1.3; }

.query-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.query-card { background: #fff; padding: 1rem; border-radius: 0.75rem; display: flex; align-items: center; gap: 0.75rem; }
.query-card:active { transform: scale(0.95); }
.query-icon-box { width: 2.5rem; height: 2.5rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; }
.query-info { display: flex; flex-direction: column; gap: 0.125rem; }
.query-name { font-size: 0.875rem; font-weight: 700; color: $on-surface; }
.query-meta { font-size: 0.625rem; color: $on-surface; }

.personal-list { background: #fff; border-radius: 0.75rem; overflow: hidden; }
.personal-item { padding: 1.25rem; display: flex; justify-content: space-between; align-items: center; }
.personal-item:active { background: $surface; }
.personal-left { display: flex; align-items: center; gap: 1rem; }
.personal-name { font-size: 0.875rem; font-weight: 700; color: $on-surface; }
.personal-right { display: flex; align-items: center; gap: 0.5rem; }

.text-primary         { color: $primary; }
.text-secondary       { color: $secondary; }
.text-tertiary        { color: $tertiary; }
.text-error           { color: $error; }
.text-outline-variant { color: $outline-variant; }
.bg-primary-light     { background: rgba($primary, 0.10); }
.bg-secondary-light   { background: rgba($secondary, 0.10); }
.bg-tertiary-light    { background: rgba($tertiary, 0.10); }
.bg-error-light       { background: rgba($error, 0.10); }

.bottom-safe { height: calc(var(--tabbar-safe) + $space-2); }  /* tab bar + 8px breathing room */
</style>
