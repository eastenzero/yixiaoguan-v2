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
          <AppIcon name="school" class="hero-icon-bg" />
        </view>
      </view>

      <view class="section">
        <view class="section-header">
          <text class="section-title">快捷入口</text>
          <text class="section-badge">QUICK LINKS</text>
        </view>
        <view class="quick-grid">
          <view class="quick-large" @click="openExternal('https://www.sdfmu.edu.cn')">
            <AppIcon name="home" class="quick-icon text-primary" />
            <view class="quick-label-row">
              <text class="quick-label">校主页</text>
              <AppIcon name="open_in_new" class="meta-external" />
            </view>
          </view>
          <view class="quick-stack">
            <view class="quick-row" @click="openExternal('http://portal.sdfmu.edu.cn', { useSso: true })">
              <AppIcon name="gate" class="quick-icon text-secondary" />
              <text class="quick-label">信息门户</text>
              <AppIcon name="open_in_new" class="meta-external" />
            </view>
            <view class="quick-row" @click="openExternal('https://ehall.sdfmu.edu.cn/v2/site/index', { useSso: true })">
              <AppIcon name="cloud_done" class="quick-icon text-tertiary" />
              <text class="quick-label">服务大厅</text>
              <AppIcon name="open_in_new" class="meta-external" />
            </view>
          </view>
        </view>
        <!-- 统一消息平台: 企业微信原生应用，暂无 Web URL，暂时隐藏 -->
        <view v-if="false" class="quick-wide" @click="handleComingSoon('统一消息平台', '我在哪里查看学校通知和老师回复？')">
          <view class="quick-wide-left">
            <AppIcon name="message" class="quick-icon text-primary" />
            <text class="quick-label">统一消息平台</text>
          </view>
          <AppIcon name="chevron_right" class="text-outline-variant" />
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
              <AppIcon :name="item.icon" class="campus-icon" />
              <AppIcon v-if="item.url" name="open_in_new" class="badge-external" />
            </view>
            <text class="campus-label">{{ item.label }}</text>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">学业</text>
        <view class="query-grid">
          <view class="query-card" @click="openExternal('https://app.sdfmu.edu.cn/site/schedule/index', { useSso: true })">
            <view class="query-icon-box bg-secondary-light">
              <AppIcon name="calendar_month" class="text-secondary" />
            </view>
            <view class="query-info">
              <text class="query-name">学生课表</text>
              <view class="query-meta">课表查询 <AppIcon name="open_in_new" class="meta-external" /></view>
            </view>
          </view>
          <view class="query-card" @click="openExternal('http://jwc.sdfmu.edu.cn', { useSso: true })">
            <view class="query-icon-box bg-tertiary-light">
              <AppIcon name="grade" class="text-tertiary" />
            </view>
            <view class="query-info">
              <text class="query-name">成绩查询</text>
              <view class="query-meta">教务系统 <AppIcon name="open_in_new" class="meta-external" /></view>
            </view>
          </view>
          <view class="query-card" @click="openExternal('http://202.194.232.127/index.html')">
            <view class="query-icon-box bg-primary-light">
              <AppIcon name="library_books" class="text-primary" />
            </view>
            <view class="query-info">
              <text class="query-name">图书馆</text>
              <view class="query-meta">借阅状态 <AppIcon name="open_in_new" class="meta-external" /></view>
            </view>
          </view>
          <view class="query-card" @click="openExternal('https://mail.sdfmu.edu.cn/', { useSso: true })">
            <view class="query-icon-box bg-error-light">
              <AppIcon name="mail" class="text-error" />
            </view>
            <view class="query-info">
              <text class="query-name">学生邮箱</text>
              <view class="query-meta">收件箱 <AppIcon name="open_in_new" class="meta-external" /></view>
            </view>
          </view>
        </view>
      </view>

      <view class="section">
        <text class="section-title">个人</text>
        <view class="personal-list">
          <view class="personal-item" @click="openExternal('https://app.sdfmu.edu.cn/site/agenda/index', { useSso: true })">
            <view class="personal-left">
              <AppIcon name="event_note" class="text-primary" />
              <text class="personal-name">个人日程</text>
            </view>
            <AppIcon name="open_in_new" class="meta-external" />
          </view>
          <view class="personal-item" @click="goChatHistory">
            <view class="personal-left">
              <AppIcon name="help_center" class="text-primary" />
              <text class="personal-name">我的提问</text>
            </view>
            <view class="personal-right">
              <AppIcon name="chevron_right" class="text-outline-variant" />
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
import AppIcon from '@/components/AppIcon.vue'
import { onShow } from '@dcloudio/uni-app'
import CustomTabBar from '@/components/CustomTabBar.vue'
import FeatureNoticeSheet from '@/components/FeatureNoticeSheet.vue'
import { openAiQuestion, openExternal, showComingSoon } from '@/composables/useServiceNavigation'
import { trackEvent } from '@/utils/track'

interface ServiceItem {
  icon: string
  label: string
  url?: string
  useSso?: boolean
  aiQuestion?: string
  comingSoon?: boolean
}

const campusServices: ServiceItem[] = [
  // 行 1：最高频学生事务（教务/团委）
  { icon: 'meeting_room', label: '空教室申请', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=383', useSso: true },
  { icon: 'feedback', label: '接诉即办', url: 'https://ehall.sdfmu.edu.cn/v2/matter/start?id=378', useSso: true },
  { icon: 'handyman', label: '网上报修', url: 'https://metc.sdfmu.edu.cn/info/1073/1954.htm' },
  { icon: 'school', label: '学籍办理', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=369', useSso: true },
  // 行 2：学生工作部申请类
  { icon: 'home_work', label: '校外住宿', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=394', useSso: true },
  { icon: 'volunteer_activism', label: '困难补助', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=417', useSso: true },
  { icon: 'groups', label: '活动室预约', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=445', useSso: true },
  { icon: 'credit_card', label: '校园卡服务', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=443', useSso: true },
  // 行 3：校园生活与公共资源
  { icon: 'wifi', label: '校园网', url: 'http://vpnportal.sdfmu.edu.cn', useSso: true },
  { icon: 'podium', label: '学术讲座', url: 'http://academic.sdfmu.edu.cn/index.php?redirect=apply/showlist', useSso: true },
  { icon: 'event_available', label: '预约中心', url: 'https://ehall.sdfmu.edu.cn/v2/reserve/special_info?id=3', useSso: true },
  { icon: 'qr_code', label: '访客预约', url: 'https://ehall.sdfmu.edu.cn/v2/reserve/special_info?id=2', useSso: true },
  // 行 4：证件采集 + 体育健康
  { icon: 'face_retouching_natural', label: '人脸采集', url: 'https://fpc.sdfmu.edu.cn/#/home', useSso: true },
  { icon: 'photo_camera', label: '证件照采集', url: 'https://ppu.sdfmu.edu.cn', useSso: true },
  { icon: 'badge', label: '体育保健课', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=368', useSso: true },
  { icon: 'book', label: '校史馆预约', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=407', useSso: true },
  // 行 5：媒体 + 应用中心兜底
  { icon: 'history', label: '我的申请', url: 'https://ehall.sdfmu.edu.cn/v2/matter/launch', useSso: true },
  { icon: 'live_tv', label: '直播山一大', url: 'https://qjjern.vnet.weizan.cn/live/channelpage-253967?v=1764637917204' },
  { icon: 'apps', label: '更多服务', url: 'https://ehall.sdfmu.edu.cn/v2/site/serviceList', useSso: true },
]

onShow(() => {
  trackEvent('page_view', { path: '/pages/services/index' })
})

function handleServiceClick(item: ServiceItem) {
  trackEvent('service_card_click', { card: item.label, source: 'services' })
  if (item.url) {
    openExternal(item.url, { useSso: item.useSso })
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
  left: var(--student-fixed-left, 0);
  right: var(--student-fixed-right, 0);
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
