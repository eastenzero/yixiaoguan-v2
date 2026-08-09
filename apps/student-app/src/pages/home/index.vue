<template>
  <view class="home-page">
    <view class="campus-hero">
      <swiper
        class="campus-swiper"
        :current="activeCampusSlide"
        :autoplay="true"
        :circular="true"
        :interval="4800"
        :duration="760"
        @change="onCampusSlideChange"
      >
        <swiper-item v-for="(slide, index) in campusSlides" :key="slide.id">
          <image
            class="campus-visual"
            :class="{ 'is-active': activeCampusSlide === index }"
            :src="slide.image"
            mode="aspectFill"
          />
        </swiper-item>
      </swiper>
      <view class="hero-shade" />

      <view class="hero-top">
        <view class="brand-lockup">
          <view class="brand-mark">
            <text class="material-symbols-outlined brand-icon">local_hospital</text>
          </view>
          <view>
            <text class="brand-name">医小管</text>
            <text class="brand-sub">SDFMU · CAMPUS AI</text>
          </view>
        </view>
        <view class="hero-actions">
          <view class="online-pill"><view class="online-dot" /><text>AI 在线</text></view>
          <view class="glass-icon-btn" @click="goHistory">
            <text class="material-symbols-outlined top-icon">notifications</text>
            <view v-if="totalUnread > 0" class="notif-dot" />
          </view>
        </view>
      </view>

      <view class="hero-copy animate-fade-up delay-1">
        <text class="hero-greeting">{{ greeting }}，{{ displayName }}</text>
        <text class="hero-title">在山一大，<br />让每件事更简单</text>
        <text class="hero-meta">AI + 校园服务，随时回应你的需要</text>
      </view>

      <view class="campus-caption animate-fade-up delay-2">
        <view class="caption-copy">
          <text class="caption-kicker">CAMPUS / 0{{ activeCampusSlide + 1 }}</text>
          <text class="caption-title">{{ activeCampus.title }}</text>
          <text class="caption-sub">{{ activeCampus.subtitle }}</text>
        </view>
        <view class="slide-selector">
          <view
            v-for="(slide, index) in campusSlides"
            :key="`selector-${slide.id}`"
            class="slide-number"
            :class="{ active: activeCampusSlide === index }"
            @click.stop="selectCampusSlide(index)"
          >0{{ index + 1 }}</view>
        </view>
      </view>

    </view>

    <view class="content-sheet">
      <view class="glass-search animate-fade-up delay-2" @click="goChat()">
        <view class="search-orb"><text class="material-symbols-outlined search-icon">auto_awesome</text></view>
        <view class="search-copy">
          <text class="search-label">AI CAMPUS ASSISTANT</text>
          <text class="search-placeholder">想问什么？我现在就回答</text>
        </view>
        <view class="ask-btn"><text class="material-symbols-outlined ask-icon">arrow_upward</text></view>
      </view>

      <view class="quick-grid animate-fade-up delay-3">
        <view v-for="item in quickActions" :key="item.id" class="quick-item" @click="handleQuick(item)">
          <view class="quick-icon-wrap">
            <text class="material-symbols-outlined quick-icon">{{ item.icon }}</text>
          </view>
          <text class="quick-label">{{ item.label }}</text>
          <text class="quick-caption">{{ item.caption }}</text>
        </view>
      </view>

      <view class="feature-banner animate-fade-up delay-4" @click="goServices">
        <view class="feature-copy">
          <text class="feature-kicker">YELLOW RIVER LIBRARY</text>
          <text class="feature-title">黄河图书馆专属服务</text>
          <text class="feature-desc">预约座位、馆藏查询，一站式找到学习空间</text>
        </view>
        <view class="feature-action"><text>去看看</text><text class="material-symbols-outlined">arrow_forward</text></view>
      </view>

      <scroll-view scroll-x class="tag-scroll animate-fade-up delay-5" show-scrollbar="false">
        <view class="tag-list">
          <view v-for="tag in tags" :key="tag.id" class="tag-chip" @click="askQuestion(tag.label)">
            <text class="tag-text">{{ tag.label }}</text>
          </view>
        </view>
      </scroll-view>

      <view class="section animate-fade-up delay-6">
        <view class="section-head">
          <view>
            <text class="eyebrow">CAMPUS SERVICES</text>
            <text class="section-title">常用服务</text>
          </view>
          <text class="section-more" @click="goServices">全部服务</text>
        </view>
        <view class="service-grid">
          <view v-for="svc in services" :key="svc.id" class="service-card" @click="onServiceClick(svc)">
            <view class="service-icon-wrap">
              <text class="material-symbols-outlined service-icon">{{ svc.icon }}</text>
            </view>
            <text class="service-label">{{ svc.label }}</text>
            <text class="service-desc">{{ svc.desc }}</text>
          </view>
        </view>
      </view>

      <view class="assistant-card animate-fade-up delay-7" @click="goChat()">
        <view class="assistant-orb">
          <text class="material-symbols-outlined assistant-icon">graphic_eq</text>
        </view>
        <view class="assistant-copy">
          <text class="assistant-title">AI 小管随时在线</text>
          <text class="assistant-desc">答案会边生成边呈现，你也可以随时停止。</text>
        </view>
        <text class="material-symbols-outlined assistant-arrow">arrow_forward</text>
      </view>

      <view v-if="recentConversations.length" class="section animate-fade-up delay-8">
        <view class="section-head">
          <text class="section-title">继续咨询</text>
          <text class="section-more" @click="goHistory">全部记录</text>
        </view>
        <view class="recent-list">
          <view v-for="conv in recentConversations" :key="conv.id" class="recent-row" @click="goConversation(conv.id)">
            <view class="recent-icon-wrap">
              <text class="material-symbols-outlined recent-icon">{{ getConvIcon(conv.status) }}</text>
            </view>
            <view class="recent-copy">
              <text class="recent-title">{{ conv.title || '未命名对话' }}</text>
              <text class="recent-status">{{ getStatusLabel(conv.status) }}</text>
            </view>
            <text class="material-symbols-outlined recent-arrow">chevron_right</text>
          </view>
        </view>
      </view>
    </view>

    <CustomTabBar current="home" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { getUnreadSummary } from '@/api/notification'
import { listConversations } from '@/api/chat'
import { openExternal } from '@/composables/useServiceNavigation'
import CustomTabBar from '@/components/CustomTabBar.vue'
import { trackEvent } from '@/utils/track'
import type { ConversationResponse } from '@/types/chat'

const userStore = useUserStore()
const totalUnread = ref(0)
const recentConversations = ref<ConversationResponse[]>([])
const activeCampusSlide = ref(0)

const campusSlides = [
  { id: 'library', title: '黄河图书馆', subtitle: '书香与科技，在这里相遇', image: '/static/images/sdfmu-campus-library.jpg' },
  { id: 'avenue', title: '校园主轴', subtitle: '从这里走向每一种可能', image: '/static/images/sdfmu-campus-avenue.jpg' },
  { id: 'activity', title: '大学生活动中心', subtitle: '让热爱在校园真实发生', image: '/static/images/sdfmu-campus-activity-center.jpg' },
  { id: 'lake', title: '湖畔校园', subtitle: '一座会呼吸的医学学府', image: '/static/images/sdfmu-campus-lake.jpg' },
]

const activeCampus = computed(() => campusSlides[activeCampusSlide.value] || campusSlides[0])

const displayName = computed(() => {
  const name = userStore.userInfo?.name
  const pilot = (userStore.userInfo?.staff_id || '').startsWith('pilot:')
  return name && !pilot ? name : '林小依'
})
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 9) return '早上好'
  if (hour < 12) return '上午好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  if (hour < 22) return '晚上好'
  return '夜深了'
})

const quickActions = [
  { id: 'q1', label: '找服务', caption: '校园入口', icon: 'grid_view', action: 'services' },
  { id: 'q2', label: '问小管', caption: '流式问答', icon: 'auto_awesome', action: 'chat' },
  { id: 'q3', label: '扫一扫', caption: '识别办理', icon: 'qr_code_scanner', action: 'scan' },
  { id: 'q4', label: '校园卡', caption: '卡务服务', icon: 'credit_card', action: 'card' },
]

const tags = [
  { id: 't1', label: '宿舍电费怎么交？' },
  { id: 't2', label: '补考重修怎么办？' },
  { id: 't3', label: '图书馆几点开？' },
  { id: 't4', label: '校园网怎么连？' },
]

const services = [
  { id: 's1', label: '教务系统', desc: '课表与成绩', icon: 'school', url: 'http://jwc.sdfmu.edu.cn' },
  { id: 's2', label: '黄河图书馆', desc: '馆藏与空间', icon: 'local_library', url: 'http://202.194.232.127/index.html' },
  { id: 's3', label: '校园邮箱', desc: '学生邮件', icon: 'mail', url: 'https://mail.sdfmu.edu.cn/' },
  { id: 's4', label: '信息门户', desc: '统一身份入口', icon: 'account_balance', url: 'https://www.sdfmu.edu.cn/xxmh.htm' },
]

onShow(() => {
  void refreshData()
  trackEvent('page_view', { path: '/pages/home/index' })
})

async function refreshData() {
  try {
    const unread = await getUnreadSummary()
    totalUnread.value = unread.total_unread || 0
  } catch { totalUnread.value = 0 }
  try {
    const conversations = await listConversations(1, 3)
    recentConversations.value = conversations.items || []
  } catch { recentConversations.value = [] }
}

function goChat(query?: string) {
  if (query) uni.setStorageSync('chat_init_query', query)
  uni.switchTab({ url: '/pages/chat/index' })
}

function askQuestion(question: string) {
  trackEvent('quick_question_click', { label: question })
  goChat(question)
}

function handleQuick(item: { action: string; label: string }) {
  if (item.action === 'services') return goServices()
  if (item.action === 'chat') return goChat()
  if (item.action === 'scan') {
    uni.scanCode({ success: () => undefined, fail: () => undefined })
    return
  }
  uni.showToast({ title: `${item.label}即将开放`, icon: 'none' })
}

function goServices() { uni.switchTab({ url: '/pages/services/index' }) }
function goHistory() { uni.navigateTo({ url: '/pages/chat/history' }) }

function onCampusSlideChange(event: { detail?: { current?: number } }) {
  activeCampusSlide.value = Number(event.detail?.current || 0)
}

function selectCampusSlide(index: number) {
  activeCampusSlide.value = index
}

function onServiceClick(service: { label: string; url: string }) {
  trackEvent('service_card_click', { card: service.label, source: 'home' })
  openExternal(service.url)
}

function goConversation(id: number) {
  uni.setStorageSync('pendingConversationId', String(id))
  uni.switchTab({ url: '/pages/chat/index' })
}

function getConvIcon(status: string): string {
  const icons: Record<string, string> = {
    ai_serving: 'auto_awesome',
    pending_teacher: 'hourglass_top',
    teacher_serving: 'support_agent',
    resolved: 'check_circle',
    closed: 'cancel',
  }
  return icons[status] || 'chat'
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    ai_serving: 'AI 解答中',
    pending_teacher: '等待老师接入',
    teacher_serving: '老师服务中',
    resolved: '已解决',
    closed: '已关闭',
  }
  return labels[status] || status
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.home-page {
  min-height: 100dvh;
  width: min(100%, 390px);
  margin: 0 auto;
  overflow-x: hidden;
  color: $on-surface;
  background: #f3efe9;
  padding-bottom: calc(var(--tabbar-safe) + 24px);
}

.campus-hero {
  position: relative;
  height: 366px;
  overflow: hidden;
  background: #24103f;
  border-radius: 0 0 32px 32px;
  box-shadow: 0 22px 48px rgba(42,18,74,.22);
}

.campus-swiper,
.hero-shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.campus-swiper { z-index: 0; }
.campus-visual { width: 100%; height: 100%; opacity: .68; transform: scale(1.08); object-position: center center; transition: opacity .75s ease, transform 1.2s cubic-bezier(.2,.75,.2,1); }
.campus-visual.is-active { opacity: .94; transform: scale(1.01); }
.hero-shade { z-index: 1; background: rgba(27,9,51,.34); box-shadow: inset 0 120px 90px rgba(22,6,43,.4), inset 0 -140px 100px rgba(18,5,36,.68); pointer-events: none; }

.hero-top,
.hero-copy,
.glass-search { position: relative; z-index: 2; }

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: calc(env(safe-area-inset-top) + 18px) 20px 0;
}

.brand-lockup { display: flex; align-items: center; gap: 10px; }
.brand-mark {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(255,255,255,.14);
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.42);
}
.brand-icon { color: #fff; font-size: 21px; font-variation-settings: 'FILL' 1; }
.brand-name { display: block; color: #fff; font-size: 16px; font-weight: 850; letter-spacing: .08em; }
.brand-sub { display: block; margin-top: 3px; color: rgba(255,255,255,.58); font-size: 7px; font-weight: 700; letter-spacing: .12em; }
.hero-actions { display: flex; align-items: center; gap: 8px; }
.online-pill { height: 38px; padding: 0 12px; display: flex; align-items: center; gap: 6px; border: 1px solid rgba(255,255,255,.16); border-radius: 14px; color: rgba(255,255,255,.84); background: rgba(31,10,57,.22); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); font-size: 9px; font-weight: 750; }
.online-dot { width: 6px; height: 6px; border-radius: 50%; background: #d8ff9f; box-shadow: 0 0 12px rgba(216,255,159,.9); }
.glass-icon-btn {
  position: relative;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: rgba(255,255,255,.13);
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.4);
}
.top-icon { color: #fff; font-size: 21px; }
.notif-dot { position: absolute; top: 9px; right: 9px; width: 7px; height: 7px; border-radius: 50%; background: #ffcf70; }

.hero-copy { padding: 42px 22px 0; }
.hero-greeting { display: block; color: rgba(255,255,255,.76); font-size: 12px; font-weight: 720; letter-spacing: .02em; }
.hero-title { display: block; margin-top: 9px; color: #fff; font-size: 27px; line-height: 1.18; font-weight: 830; letter-spacing: -.045em; text-shadow: 0 8px 30px rgba(20,4,42,.34); }
.hero-meta { display: block; margin-top: 9px; color: rgba(255,255,255,.66); font-size: 9px; letter-spacing: .03em; }

.campus-caption {
  position: absolute;
  z-index: 2;
  left: 20px;
  right: 20px;
  bottom: 20px;
  min-height: 62px;
  padding: 10px 13px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  border: 1px solid rgba(255,255,255,.2);
  border-radius: 20px;
  background: rgba(24,7,46,.34);
  backdrop-filter: blur(22px) saturate(135%);
  -webkit-backdrop-filter: blur(22px) saturate(135%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.16), 0 14px 32px rgba(20,4,40,.18);
}
.caption-copy { flex: 1; min-width: 0; }
.caption-kicker { display: block; color: rgba(255,255,255,.48); font-size: 7px; font-weight: 800; letter-spacing: .14em; }
.caption-title { display: block; color: #fff; font-size: 13px; font-weight: 800; letter-spacing: .04em; }
.caption-kicker + .caption-title { margin-top: 4px; }
.caption-sub { display: block; margin-top: 3px; color: rgba(255,255,255,.58); font-size: 8px; }
.slide-selector { display: flex; align-items: center; flex-shrink: 0; gap: 4px; }
.slide-number { min-width: 23px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 9px; color: rgba(255,255,255,.42); font-size: 7px; font-weight: 800; transition: color .25s ease, background .25s ease, transform .25s ease; }
.slide-number.active { color: #32104f; background: rgba(255,255,255,.92); transform: translateY(-2px); }

.glass-search {
  min-height: 72px;
  padding: 8px 8px 8px 10px;
  display: flex;
  align-items: center;
  gap: 11px;
  border: 1px solid rgba(255,255,255,.82);
  border-radius: 24px;
  background: rgba(255,255,255,.82);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  box-shadow: inset 0 1px 0 #fff, 0 18px 42px rgba(49,22,83,.16);
}
.search-orb { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 17px; background: #efe5f8; box-shadow: inset 0 1px 0 #fff; }
.search-icon { color: #5b2b8f; font-size: 22px; font-variation-settings: 'FILL' 1; }
.search-copy { flex: 1; min-width: 0; }
.search-label { display: block; color: #9a82ad; font-size: 7px; font-weight: 850; letter-spacing: .14em; }
.search-placeholder { display: block; margin-top: 5px; color: #33273c; font-size: 13px; font-weight: 750; }
.ask-btn { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 17px; background: #4c217e; box-shadow: 0 9px 18px rgba(76,33,126,.26); }
.ask-icon { color: #fff; font-size: 20px; }

.content-sheet {
  position: relative;
  z-index: 3;
  margin-top: -1px;
  padding: 18px 18px 16px;
  border-radius: 0;
  background: #f3efe9;
}

.quick-grid { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: 8px; margin-top: 22px; }
.quick-item { min-width: 0; text-align: center; }
.quick-icon-wrap {
  width: 52px;
  height: 52px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  color: #5b2b8f;
  background: rgba(255,255,255,.72);
  backdrop-filter: blur(18px);
  -webkit-backdrop-filter: blur(18px);
  box-shadow: inset 0 1px 0 #fff, 0 8px 18px rgba(91,43,143,.08);
}
.quick-icon { font-size: 23px; color: #5b2b8f; }
.quick-label { display: block; margin-top: 8px; font-size: 12px; font-weight: 800; color: #342d35; }
.quick-caption { display: block; margin-top: 2px; font-size: 9px; color: #978c98; }

.feature-banner {
  min-height: 88px;
  margin-top: 20px;
  padding: 16px 15px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  overflow: hidden;
  border-radius: 18px;
  color: #fff;
  background: #5b2b8f;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.18), 0 14px 28px rgba(91,43,143,.16);
}
.feature-copy { min-width: 0; }
.feature-kicker { display: block; color: rgba(255,255,255,.58); font-size: 8px; font-weight: 800; letter-spacing: .14em; }
.feature-title { display: block; margin-top: 6px; color: #fff; font-size: 16px; font-weight: 800; }
.feature-desc { display: block; margin-top: 4px; color: rgba(255,255,255,.68); font-size: 9px; }
.feature-action { display: flex; align-items: center; gap: 3px; flex-shrink: 0; padding: 8px 10px; border-radius: 999px; background: rgba(255,255,255,.18); font-size: 10px; font-weight: 800; }
.feature-action .material-symbols-outlined { font-size: 14px; }

.tag-scroll { margin: 22px -18px 0; white-space: nowrap; }
.tag-list { display: inline-flex; gap: 8px; padding: 0 18px; }
.tag-chip { padding: 9px 13px; border-radius: 999px; background: #e9e0d9; }
.tag-text { color: #675a68; font-size: 11px; font-weight: 650; }

.section { margin-top: 28px; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 14px; }
.eyebrow { display: block; color: #aa76a5; font-size: 8px; font-weight: 800; letter-spacing: .16em; }
.section-title { display: block; margin-top: 3px; color: #2e282f; font-size: 19px; font-weight: 800; }
.section-more { color: #5b2b8f; font-size: 11px; font-weight: 750; }
.service-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 10px; }
.service-card { min-width: 0; padding: 15px; border-radius: 18px; background: rgba(255,255,255,.82); box-shadow: inset 0 1px 0 #fff; }
.service-card:active { transform: scale(.98); }
.service-icon-wrap { width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 14px; background: #f2dcef; }
.service-icon { color: #5b2b8f; font-size: 20px; }
.service-label { display: block; margin-top: 12px; color: #332c34; font-size: 13px; font-weight: 800; }
.service-desc { display: block; margin-top: 3px; color: #958a96; font-size: 10px; }

.assistant-card {
  margin-top: 24px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 13px;
  border-radius: 25px;
  color: #fff;
  background: #5b2b8f;
  box-shadow: 0 18px 42px rgba(91,43,143,.20), inset 0 1px 0 rgba(255,255,255,.2);
}
.assistant-orb { width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 17px; background: rgba(255,255,255,.17); }
.assistant-icon { color: #fff; font-size: 23px; }
.assistant-copy { flex: 1; min-width: 0; }
.assistant-title { display: block; color: #fff; font-size: 14px; font-weight: 800; }
.assistant-desc { display: block; margin-top: 4px; color: rgba(255,255,255,.68); font-size: 10px; line-height: 1.5; }
.assistant-arrow { color: rgba(255,255,255,.82); font-size: 20px; }

.recent-list { overflow: hidden; border-radius: 22px; background: rgba(255,255,255,.76); }
.recent-row { display: flex; align-items: center; gap: 12px; min-height: 68px; padding: 0 15px; }
.recent-row + .recent-row { box-shadow: inset 0 1px 0 rgba(91,43,143,.06); }
.recent-icon-wrap { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 13px; background: #f2dcef; }
.recent-icon { color: #5b2b8f; font-size: 18px; }
.recent-copy { flex: 1; min-width: 0; }
.recent-title { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #342d35; font-size: 12px; font-weight: 750; }
.recent-status { display: block; margin-top: 4px; color: #9b909c; font-size: 9px; }
.recent-arrow { color: #b7abb7; font-size: 19px; }
</style>
