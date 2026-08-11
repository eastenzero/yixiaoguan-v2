<template>
  <view class="home-page">
    <view class="campus-hero">
      <swiper
        class="campus-swiper"
        :current="activeCampusSlide"
        :autoplay="campusAutoplay"
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
            :style="{ objectPosition: slide.focal }"
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
        <view class="slide-selector" aria-label="校园图片切换">
          <button
            v-for="(slide, index) in campusSlides"
            :key="`selector-${slide.id}`"
            class="slide-number"
            :class="{ active: activeCampusSlide === index }"
            :aria-label="`查看${slide.title}`"
            :aria-current="activeCampusSlide === index ? 'true' : undefined"
            @click.stop="selectCampusSlide(index)"
          >
            <text class="slide-number-label">0{{ index + 1 }}</text>
          </button>
        </view>
      </view>

    </view>

    <view class="content-sheet">
      <view
        class="glass-search animate-fade-up delay-2"
        hover-class="glass-search--pressed"
        :hover-start-time="0"
        :hover-stay-time="140"
        @click="goChat()"
      >
        <view class="search-orb"><text class="material-symbols-outlined search-icon">auto_awesome</text></view>
        <view class="search-copy">
          <text class="search-label">AI CAMPUS ASSISTANT</text>
          <text class="search-placeholder">想问什么？我现在就回答</text>
        </view>
        <view class="ask-btn"><text class="material-symbols-outlined ask-icon">arrow_upward</text></view>
      </view>

      <view class="quick-grid animate-fade-up delay-3">
        <view
          v-for="item in quickActions"
          :key="item.id"
          class="quick-item"
          hover-class="quick-item--pressed"
          :hover-start-time="0"
          :hover-stay-time="140"
          @click="handleQuick(item)"
        >
          <view class="quick-icon-wrap">
            <text class="material-symbols-outlined quick-icon">{{ item.icon }}</text>
          </view>
          <view class="quick-copy">
            <text class="quick-label">{{ item.label }}</text>
            <text class="quick-caption">{{ item.caption }}</text>
          </view>
          <text class="material-symbols-outlined quick-arrow">arrow_forward</text>
        </view>
      </view>

      <view
        class="feature-banner animate-fade-up delay-4"
      >
        <view class="feature-copy">
          <text class="feature-kicker">YELLOW RIVER LIBRARY</text>
          <text class="feature-title">黄河图书馆专属服务</text>
          <text class="feature-desc">直达预约与馆藏系统，不再经过资讯页面</text>
        </view>
        <view class="feature-actions">
          <view
            class="feature-action"
            hover-class="feature-action--pressed"
            :hover-start-time="0"
            :hover-stay-time="120"
            @click.stop="openLibraryService('seat')"
          >
            <text>座位预约</text><text class="material-symbols-outlined">event_seat</text>
          </view>
          <view
            class="feature-action"
            hover-class="feature-action--pressed"
            :hover-start-time="0"
            :hover-stay-time="120"
            @click.stop="openLibraryService('catalog')"
          >
            <text>馆藏查询</text><text class="material-symbols-outlined">search</text>
          </view>
        </view>
      </view>

      <view class="section animate-fade-up delay-6">
        <view class="section-head">
          <view>
            <text class="eyebrow">CAMPUS SERVICES</text>
            <text class="section-title">常用服务</text>
          </view>
          <text class="section-more" @click="goServices">全部服务</text>
        </view>
        <view class="service-grid">
          <view
            v-for="svc in services"
            :key="svc.id"
            class="service-card"
            hover-class="service-card--pressed"
            :hover-start-time="0"
            :hover-stay-time="140"
            @click="onServiceClick(svc)"
          >
            <view class="service-icon-wrap">
              <text class="material-symbols-outlined service-icon">{{ svc.icon }}</text>
            </view>
            <text class="service-label">{{ svc.label }}</text>
            <text class="service-desc">{{ svc.desc }}</text>
          </view>
        </view>
      </view>

      <view
        class="assistant-card animate-fade-up delay-7"
        hover-class="assistant-card--pressed"
        :hover-start-time="0"
        :hover-stay-time="140"
        @click="goChat()"
      >
        <view class="assistant-orb">
          <text class="material-symbols-outlined assistant-icon">graphic_eq</text>
        </view>
        <view class="assistant-copy">
          <text class="assistant-title">AI 小管随时在线</text>
          <text class="assistant-desc">回答自动保存到历史记录，方便随时回来继续。</text>
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
import { computed, onBeforeUnmount, ref } from 'vue'
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
const campusAutoplay = ref(true)
let campusAutoplayTimer: ReturnType<typeof setTimeout> | null = null

const campusSlides = [
  { id: 'yellow-river-library', title: '黄河图书馆', subtitle: '济南校区 · 医学之冠', image: '/static/images/sdfmu-official-yellow-river-library.jpg', focal: '50% 52%' },
  { id: 'tongli-bridge', title: '同力桥', subtitle: '泰安校区 · 同心同行', image: '/static/images/sdfmu-official-tongli-bridge.jpg', focal: '50% 52%' },
  { id: 'taishan-library', title: '泰山图书馆', subtitle: '泰安校区 · 书香医脉', image: '/static/images/sdfmu-official-taishan-library.jpg', focal: '50% 48%' },
  { id: 'qindu-building', title: '勤笃楼', subtitle: '济南校区 · 勤学笃行', image: '/static/images/sdfmu-official-jinan-qindu-building.jpg', focal: '50% 46%' },
]

const activeCampus = computed(() => campusSlides[activeCampusSlide.value] || campusSlides[0])

const isBoundAccount = computed(() => !!userStore.userInfo?.staff_id && !userStore.userInfo.staff_id.startsWith('pilot:'))
const displayName = computed(() => {
  const name = userStore.userInfo?.name
  return name && isBoundAccount.value ? name : '医小管体验用户'
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
  { id: 'q3', label: '校园缴费', caption: '学费与住宿费', icon: 'payments', action: 'external', url: 'https://cwpt.sdfmu.edu.cn/xysf/' },
  { id: 'q4', label: '本科教务', caption: '课表与成绩', icon: 'menu_book', action: 'external', url: 'https://jwc.sdfmu.edu.cn/academic/common/security/login.jsp' },
]

const services = [
  { id: 's1', label: '学术讲座', desc: '报名与日程', icon: 'podium', url: 'http://academic.sdfmu.edu.cn/index.php?redirect=apply/showlist' },
  { id: 's2', label: '馆藏查询', desc: '图书检索', icon: 'local_library', url: 'http://opac.sdfmu.edu.cn:8080/opac/' },
  { id: 's3', label: '校园邮箱', desc: '学生邮件', icon: 'mail', url: 'https://mail.sdfmu.edu.cn/' },
  { id: 's4', label: '信息门户', desc: '统一身份入口', icon: 'account_balance', url: 'http://portal.sdfmu.edu.cn' },
]

const libraryLinks = {
  seat: 'http://seat.sdfmu.edu.cn/home/web/f_second',
  catalog: 'http://opac.sdfmu.edu.cn:8080/opac/',
} as const

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

function handleQuick(item: { action: string; label: string; url?: string }) {
  if (item.action === 'services') return goServices()
  if (item.action === 'chat') return goChat()
  if (item.url) {
    trackEvent('service_card_click', { card: item.label, source: 'home_quick' })
    return openExternal(item.url)
  }
  uni.showToast({ title: `${item.label}即将开放`, icon: 'none' })
}

function openLibraryService(type: keyof typeof libraryLinks) {
  trackEvent('service_card_click', { card: type === 'seat' ? '黄河图书馆座位预约' : '黄河图书馆馆藏查询', source: 'home_feature' })
  openExternal(libraryLinks[type])
}

function goServices() { uni.switchTab({ url: '/pages/services/index' }) }
function goHistory() { uni.navigateTo({ url: '/pages/chat/history' }) }

function onCampusSlideChange(event: { detail?: { current?: number } }) {
  activeCampusSlide.value = Number(event.detail?.current || 0)
}

function selectCampusSlide(index: number) {
  campusAutoplay.value = false
  activeCampusSlide.value = index
  if (campusAutoplayTimer) clearTimeout(campusAutoplayTimer)
  campusAutoplayTimer = setTimeout(() => {
    campusAutoplay.value = true
    campusAutoplayTimer = null
  }, 5200)
}

onBeforeUnmount(() => {
  if (campusAutoplayTimer) clearTimeout(campusAutoplayTimer)
})

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
  width: min(100%, 430px);
  margin: 0 auto;
  overflow-x: hidden;
  color: $on-surface;
  background:
    radial-gradient(circle at 92% 3%, rgba(91, 43, 143, .09), transparent 30%),
    linear-gradient(180deg, #faf7fb 0%, #f7f2f7 38%, #f6f1ec 100%);
  padding-bottom: calc(var(--tabbar-safe) + 24px);
}

.campus-hero {
  position: relative;
  height: clamp(340px, 94vw, 382px);
  margin: 10px 10px 0;
  overflow: hidden;
  background: #2f1748;
  border: 1px solid rgba(91,43,143,.18);
  border-radius: 32px 32px 22px 12px;
  box-shadow: 0 20px 48px rgba(47,23,72,.16), inset 0 1px 0 rgba(255,255,255,.28);
}

.campus-swiper,
.hero-shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.campus-swiper { z-index: 0; }
.campus-visual { width: 100%; height: 100%; opacity: .86; transform: scale(1.06); object-position: center center; transition: opacity .75s ease, transform 1.2s cubic-bezier(.2,.75,.2,1); }
.campus-visual.is-active { opacity: 1; transform: scale(1.01); }
.hero-shade {
  z-index: 1;
  background: linear-gradient(135deg, rgba(47,23,72,.42) 0%, rgba(47,23,72,.10) 52%, rgba(47,23,72,.44) 100%);
  box-shadow: inset 0 104px 80px rgba(47,23,72,.30), inset 0 -154px 112px rgba(47,23,72,.60);
  pointer-events: none;
}

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

.hero-copy { width: calc(100% - 36px); padding: clamp(30px, 8vw, 42px) 22px 0; }
.hero-greeting { display: block; color: rgba(255,255,255,.76); font-size: 12px; font-weight: 720; letter-spacing: .02em; }
.hero-title { display: block; margin-top: 10px; color: #fff; font-size: clamp(26px, 7.2vw, 30px); line-height: 1.16; font-weight: 780; letter-spacing: -.04em; text-shadow: 0 8px 30px rgba(20,4,42,.34); }
.hero-meta { display: block; margin-top: 9px; color: rgba(255,255,255,.66); font-size: 9px; letter-spacing: .03em; }

.campus-caption {
  position: absolute;
  z-index: 2;
  left: 18px;
  right: 14px;
  bottom: 14px;
  min-height: 64px;
  padding: 0;
  display: grid;
  grid-template-columns: minmax(96px, .72fr) minmax(0, 1.28fr);
  align-items: end;
  gap: 12px;
}
.caption-copy {
  min-width: 0;
  padding: 10px 0 9px 2px;
  filter: drop-shadow(0 5px 14px rgba(24,7,42,.5));
}
.caption-kicker { display: block; color: rgba(255,255,255,.58); font-size: 7px; font-weight: 800; letter-spacing: .14em; }
.caption-title { display: block; color: #fff; font-size: 14px; font-weight: 800; letter-spacing: .035em; }
.caption-kicker + .caption-title { margin-top: 4px; }
.caption-sub { display: block; max-width: 116px; margin-top: 3px; color: rgba(255,255,255,.67); font-size: 8px; line-height: 1.35; }
.slide-selector {
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(44px, 1fr));
  align-items: end;
  gap: 7px;
  height: 48px;
  padding: 0;
}
.slide-number {
  position: relative;
  min-width: 44px;
  height: 44px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid transparent;
  border-radius: 12px;
  color: rgba(255,255,255,.46);
  background: transparent;
  cursor: pointer;
  touch-action: manipulation;
  transition: color .22s ease, transform .22s cubic-bezier(.2,.8,.2,1), background .22s ease, border-color .22s ease, box-shadow .22s ease;
}
.slide-number::after {
  content: '';
  position: absolute;
  left: 11px;
  right: 11px;
  bottom: 6px;
  height: 1px;
  border-radius: 999px;
  background: rgba(255,255,255,.18);
  transform: scaleX(.72);
  transform-origin: center;
  transition: transform .26s cubic-bezier(.2,.8,.2,1), background .22s ease, box-shadow .22s ease;
}
.slide-number-label {
  transform: translateY(-3px);
  font-size: 9px;
  font-weight: 760;
  letter-spacing: .04em;
  line-height: 1;
  transition: font-size .22s ease, transform .22s cubic-bezier(.2,.8,.2,1), text-shadow .22s ease;
}
.slide-number.active { color: #fff; }
.slide-number.active .slide-number-label {
  font-size: 12px;
  font-weight: 820;
  transform: translateY(-4px);
  text-shadow: 0 0 12px rgba(236,215,251,.5);
}
.slide-number.active::after {
  background: rgba(255,255,255,.94);
  transform: scaleX(1);
  box-shadow: 0 0 8px rgba(238,219,252,.62);
}
.slide-number:active {
  transform: scale(.96);
  border-color: rgba(255,255,255,.18);
  background: rgba(255,255,255,.09);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.14);
}
.slide-number:focus-visible { outline: 3px solid rgba(255,255,255,.9); outline-offset: 1px; }

.glass-search {
  position: relative;
  overflow: hidden;
  min-height: 72px;
  padding: 8px 8px 8px 10px;
  display: flex;
  align-items: center;
  gap: 11px;
  border: 1px solid rgba(91,43,143,.18);
  border-radius: 24px;
  background: rgba(255,255,255,.82);
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  box-shadow: inset 0 1px 0 #fff, 0 14px 32px rgba(91,43,143,.10);
  transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s ease;
}
.glass-search::before,
.quick-item::before,
.feature-banner::before,
.service-card::before,
.assistant-card::before {
  content: '';
  position: absolute;
  z-index: 1;
  inset: -35% -55%;
  pointer-events: none;
  opacity: 0;
  transform: translateX(-70%) rotate(8deg);
  background: linear-gradient(100deg, transparent 35%, rgba(255,255,255,.82) 50%, transparent 65%);
}
.glass-search > *,
.quick-item > *,
.feature-banner > *,
.service-card > *,
.assistant-card > * { position: relative; z-index: 2; }
.search-orb { width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 17px; background: #efe5f8; box-shadow: inset 0 1px 0 #fff; }
.search-icon { color: #5b2b8f; font-size: 22px; font-variation-settings: 'FILL' 1; }
.search-copy { flex: 1; min-width: 0; }
.search-label { display: block; color: #9a82ad; font-size: 7px; font-weight: 850; letter-spacing: .14em; }
.search-placeholder { display: block; margin-top: 5px; color: #33273c; font-size: 13px; font-weight: 750; }
.ask-btn { position: relative; width: 48px; height: 48px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; overflow: hidden; border: 1px solid transparent; border-radius: 17px; background: linear-gradient(#5b2b8f,#5b2b8f) padding-box, linear-gradient(115deg, rgba(255,255,255,.20) 0 38%, rgba(238,221,252,.95) 48%, rgba(91,43,143,.85) 56%, rgba(255,255,255,.20) 66%) border-box; background-size: 100% 100%, 260% 100%; animation: violetEdgeFlow 5.4s linear infinite; box-shadow: 0 9px 18px rgba(91,43,143,.22), inset 0 1px 0 rgba(255,255,255,.20); transition: transform .16s cubic-bezier(.2,.8,.2,1), box-shadow .16s ease; }
.ask-btn:active { transform: translateY(2px) scale(.96); box-shadow: 0 4px 10px rgba(91,43,143,.16), inset 0 2px 8px rgba(40,15,68,.22); }
.ask-icon { color: #fff; font-size: 20px; }
.glass-search--pressed,
.glass-search:active {
  transform: translateY(2px) scale(.97);
  border-color: rgba(255,255,255,.72);
  background: #5b2b8f;
  box-shadow: inset 0 2px 9px rgba(38,14,66,.24), 0 5px 14px rgba(91,43,143,.14);
}
.glass-search--pressed::before,
.glass-search:active::before { animation: pressSheen .52s ease-out both; }
.glass-search--pressed .search-orb,
.glass-search:active .search-orb { background: #fff; box-shadow: 0 5px 14px rgba(36,13,62,.15); }
.glass-search--pressed .search-label,
.glass-search:active .search-label { color: rgba(255,255,255,.64); }
.glass-search--pressed .search-placeholder,
.glass-search:active .search-placeholder { color: #fff; }
.glass-search--pressed .ask-btn,
.glass-search:active .ask-btn { border-color: rgba(255,255,255,.7); background: #fff; box-shadow: 0 5px 14px rgba(36,13,62,.16); }
.glass-search--pressed .ask-icon,
.glass-search:active .ask-icon { color: #5b2b8f; }

.content-sheet {
  position: relative;
  z-index: 3;
  margin-top: -9px;
  padding: 27px 18px 16px;
  border-radius: 20px 30px 0 0;
  background: linear-gradient(180deg, rgba(247,242,248,.98), #f3efe9 190px);
}

.quick-grid { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 10px; margin-top: 22px; }
.quick-item { position: relative; min-width: 0; min-height: 82px; padding: 13px 12px; display: grid; grid-template-columns: 44px minmax(0, 1fr) 18px; align-items: center; gap: 10px; overflow: hidden; border: 1px solid transparent; border-radius: 22px; background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(247,240,250,.92)) padding-box, linear-gradient(110deg, rgba(91,43,143,.16) 0 38%, rgba(210,177,235,.88) 48%, rgba(91,43,143,.60) 54%, rgba(91,43,143,.16) 64%) border-box; background-size: 100% 100%, 260% 100%; box-shadow: inset 0 1px 0 #fff, 0 10px 24px rgba(91,43,143,.07); animation: violetEdgeFlow 7.2s linear infinite; transition: transform .16s cubic-bezier(.2,.8,.2,1), box-shadow .16s ease; }
.quick-item::after { content: ''; position: absolute; z-index: 1; width: 76px; height: 76px; right: 15%; top: 50%; border-radius: 50%; pointer-events: none; opacity: 0; transform: translate(50%,-50%) scale(.18); background: rgba(255,255,255,.44); transition: opacity .18s ease, transform .36s cubic-bezier(.2,.8,.2,1); }
.quick-item--pressed,
.quick-item:active { transform: translateY(2px) scale(.97); border-color: rgba(255,255,255,.78); background: #5b2b8f; box-shadow: inset 0 2px 9px rgba(38,14,66,.22), 0 5px 14px rgba(91,43,143,.12); }
.quick-item--pressed::before,
.quick-item:active::before { animation: pressSheen .52s ease-out both; }
.quick-item--pressed::after,
.quick-item:active::after { opacity: .2; transform: translate(50%,-50%) scale(1.7); }
.quick-item--pressed .quick-icon-wrap,
.quick-item:active .quick-icon-wrap { color: #5b2b8f; border-color: rgba(255,255,255,.92); background: #fff; box-shadow: 0 6px 14px rgba(40,15,68,.18); }
.quick-item--pressed .quick-icon,
.quick-item:active .quick-icon { color: #5b2b8f; }
.quick-item--pressed .quick-label,
.quick-item:active .quick-label { color: #fff; }
.quick-item--pressed .quick-caption,
.quick-item:active .quick-caption { color: rgba(255,255,255,.65); }
.quick-item--pressed .quick-arrow,
.quick-item:active .quick-arrow { color: #fff; transform: translateX(2px); }
.quick-icon-wrap {
  width: 44px;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255,255,255,.74);
  border-radius: 15px;
  color: #fff;
  background: #5b2b8f;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 7px 15px rgba(91,43,143,.16);
}
.quick-icon { font-size: 21px; color: #fff; }
.quick-copy { min-width: 0; }
.quick-label { display: block; font-size: 13px; font-weight: 800; color: #3d2849; }
.quick-caption { display: block; margin-top: 4px; font-size: 9px; color: #927b9c; }
.quick-arrow { color: #75349f; font-size: 17px; }

.feature-banner {
  position: relative;
  min-height: 88px;
  margin-top: 20px;
  padding: 16px 15px;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  overflow: hidden;
  border-radius: 18px;
  border: 1px solid rgba(91,43,143,.18);
  color: #44234f;
  background: linear-gradient(120deg, rgba(255,255,255,.94), rgba(242,231,248,.90));
  box-shadow: inset 0 1px 0 #fff, 0 10px 24px rgba(91,43,143,.08);
  transition: transform .16s cubic-bezier(.2,.8,.2,1), box-shadow .16s ease;
}
.feature-banner--pressed,
.feature-banner:active { transform: translateY(2px) scale(.97); border-color: rgba(255,255,255,.76); color: #fff; background: #5b2b8f; box-shadow: inset 0 2px 9px rgba(38,14,66,.22), 0 5px 14px rgba(91,43,143,.12); }
.feature-banner--pressed::before,
.feature-banner:active::before { animation: pressSheen .52s ease-out both; }
.feature-banner--pressed .feature-kicker,
.feature-banner:active .feature-kicker,
.feature-banner--pressed .feature-desc,
.feature-banner:active .feature-desc { color: rgba(255,255,255,.68); }
.feature-banner--pressed .feature-title,
.feature-banner:active .feature-title { color: #fff; }
.feature-banner--pressed .feature-action,
.feature-banner:active .feature-action { color: #5b2b8f; border-color: #fff; background: #fff; }
.feature-copy { min-width: 0; flex: 1; padding-right: 10px; }
.feature-kicker { display: block; color: #9d79ad; font-size: 8px; font-weight: 800; letter-spacing: .14em; }
.feature-title { display: block; margin-top: 6px; color: #43264f; font-size: 16px; font-weight: 800; }
.feature-desc { display: block; margin-top: 4px; color: #8b7494; font-size: 9px; }
.feature-actions { display: flex; flex-direction: column; align-items: stretch; gap: 7px; flex-shrink: 0; }
.feature-action { min-width: 82px; display: flex; align-items: center; justify-content: space-between; gap: 4px; flex-shrink: 0; padding: 7px 9px; border: 1px solid rgba(115,54,158,.18); border-radius: 999px; color: #6d2d98; background: rgba(255,255,255,.62); font-size: 9px; font-weight: 800; transition: transform .18s cubic-bezier(.22,.78,.22,1), box-shadow .18s ease, color .18s ease, background .18s ease; }
.feature-action--pressed,
.feature-action:active { transform: scale(.96); color: #fff; border-color: rgba(255,255,255,.74); background: #5b2b8f; box-shadow: inset 0 2px 7px rgba(38,14,66,.20); }
.feature-action .material-symbols-outlined { font-size: 14px; }

.section { margin-top: 28px; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 14px; }
.eyebrow { display: block; color: #aa76a5; font-size: 8px; font-weight: 800; letter-spacing: .16em; }
.section-title { display: block; margin-top: 3px; color: #2e282f; font-size: 19px; font-weight: 800; }
.section-more { color: #5b2b8f; font-size: 11px; font-weight: 750; }
.service-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 10px; }
.service-card { position: relative; min-width: 0; padding: 15px; overflow: hidden; border: 1px solid rgba(91,43,143,.15); border-radius: 20px; background: rgba(255,255,255,.78); box-shadow: inset 0 1px 0 #fff, 0 8px 20px rgba(91,43,143,.05); transition: transform .16s cubic-bezier(.2,.8,.2,1), box-shadow .16s ease; }
.service-card--pressed,
.service-card:active { transform: translateY(2px) scale(.97); border-color: rgba(255,255,255,.76); background: #5b2b8f; box-shadow: inset 0 2px 9px rgba(38,14,66,.22), 0 5px 14px rgba(91,43,143,.10); }
.service-card--pressed::before,
.service-card:active::before { animation: pressSheen .52s ease-out both; }
.service-card--pressed .service-icon-wrap,
.service-card:active .service-icon-wrap { background: #fff; }
.service-card--pressed .service-label,
.service-card:active .service-label { color: #fff; }
.service-card--pressed .service-desc,
.service-card:active .service-desc { color: rgba(255,255,255,.66); }
.service-icon-wrap { width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 14px; background: #f2dcef; }
.service-icon { color: #5b2b8f; font-size: 20px; }
.service-label { display: block; margin-top: 12px; color: #332c34; font-size: 13px; font-weight: 800; }
.service-desc { display: block; margin-top: 3px; color: #958a96; font-size: 10px; }

.assistant-card {
  position: relative;
  margin-top: 24px;
  padding: 18px;
  display: flex;
  align-items: center;
  gap: 13px;
  overflow: hidden;
  border-radius: 25px;
  border: 1px solid rgba(91,43,143,.18);
  color: #43264f;
  background: linear-gradient(115deg, #fbf8fc 0%, #eee2f5 100%);
  box-shadow: 0 10px 26px rgba(91,43,143,.08), inset 0 1px 0 #fff;
  transition: transform .16s cubic-bezier(.2,.8,.2,1), box-shadow .16s ease;
}
.assistant-card--pressed,
.assistant-card:active { transform: translateY(2px) scale(.97); border-color: rgba(255,255,255,.76); color: #fff; background: #5b2b8f; box-shadow: inset 0 2px 9px rgba(38,14,66,.22), 0 5px 14px rgba(91,43,143,.12); }
.assistant-card--pressed::before,
.assistant-card:active::before { animation: pressSheen .52s ease-out both; }
.assistant-card--pressed .assistant-orb,
.assistant-card:active .assistant-orb { color: #5b2b8f; background: #fff; box-shadow: 0 6px 14px rgba(40,15,68,.18); }
.assistant-card--pressed .assistant-icon,
.assistant-card:active .assistant-icon { color: #5b2b8f; }
.assistant-card--pressed .assistant-title,
.assistant-card:active .assistant-title { color: #fff; }
.assistant-card--pressed .assistant-desc,
.assistant-card:active .assistant-desc { color: rgba(255,255,255,.66); }
.assistant-card--pressed .assistant-arrow,
.assistant-card:active .assistant-arrow { color: #fff; transform: translateX(2px); }
.assistant-orb { width: 46px; height: 46px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 17px; background: #5b2b8f; box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 8px 18px rgba(91,43,143,.16); }
.assistant-icon { color: #fff; font-size: 23px; }
.assistant-copy { flex: 1; min-width: 0; }
.assistant-title { display: block; color: #43264f; font-size: 14px; font-weight: 800; }
.assistant-desc { display: block; margin-top: 4px; color: #8b7494; font-size: 10px; line-height: 1.5; }
.assistant-arrow { color: #71339b; font-size: 20px; }

@media (max-width: 350px) {
  .campus-caption { left: 14px; right: 12px; grid-template-columns: 84px minmax(0, 1fr); gap: 8px; }
  .slide-selector { gap: 4px; }
  .slide-number { min-width: 40px; }
  .quick-grid { grid-template-columns: 1fr; }
}

.recent-list { overflow: hidden; border-radius: 22px; background: rgba(255,255,255,.76); }
.recent-row { display: flex; align-items: center; gap: 12px; min-height: 68px; padding: 0 15px; }
.recent-row + .recent-row { box-shadow: inset 0 1px 0 rgba(91,43,143,.06); }
.recent-icon-wrap { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 13px; background: #f2dcef; }
.recent-icon { color: #5b2b8f; font-size: 18px; }
.recent-copy { flex: 1; min-width: 0; }
.recent-title { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #342d35; font-size: 12px; font-weight: 750; }
.recent-status { display: block; margin-top: 4px; color: #9b909c; font-size: 9px; }
.recent-arrow { color: #b7abb7; font-size: 19px; }

@keyframes violetEdgeFlow {
  from { background-position: 0 0, 100% 0; }
  to { background-position: 0 0, -160% 0; }
}

@keyframes pressSheen {
  0% { opacity: 0; transform: translateX(-70%) rotate(8deg); }
  22% { opacity: .72; }
  100% { opacity: 0; transform: translateX(70%) rotate(8deg); }
}

/* Apple-inspired liquid glass: light keeps moving, touch interrupts it naturally. */
.glass-search,
.quick-item,
.feature-banner,
.service-card,
.assistant-card {
  border: 1px solid transparent;
  background:
    linear-gradient(135deg, rgba(255,255,255,.84), rgba(248,242,251,.66)) padding-box,
    linear-gradient(108deg, rgba(91,43,143,.17) 0%, rgba(255,255,255,.96) 24%, rgba(194,155,224,.62) 45%, rgba(91,43,143,.34) 62%, rgba(255,255,255,.88) 82%, rgba(91,43,143,.16) 100%) border-box;
  background-size: 100% 100%, 280% 100%;
  backdrop-filter: blur(22px) saturate(155%);
  -webkit-backdrop-filter: blur(22px) saturate(155%);
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.96),
    inset 0 -1px 0 rgba(91,43,143,.07),
    0 10px 26px rgba(91,43,143,.075);
  animation: glassEdgeDrift 10.8s ease-in-out infinite alternate;
  transition:
    transform var(--yxg-touch-out) var(--yxg-spring-out),
    box-shadow var(--yxg-touch-out) var(--yxg-spring-out),
    border-color .24s ease,
    background .38s ease;
  transform: translateZ(0);
}

.glass-search::before,
.quick-item::before,
.feature-banner::before,
.service-card::before,
.assistant-card::before {
  inset: -55% auto -55% -48%;
  width: 46%;
  opacity: 0;
  transform: translateX(0) skewX(-18deg);
  filter: blur(7px);
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.76), rgba(229,207,246,.35), transparent);
  animation: glassGlint 8.6s cubic-bezier(.3,.02,.2,1) infinite;
  will-change: transform, opacity;
}

.quick-item:nth-child(2)::before { animation-delay: -2.15s; }
.quick-item:nth-child(3)::before { animation-delay: -4.3s; }
.quick-item:nth-child(4)::before { animation-delay: -6.45s; }
.quick-item:nth-child(2) { animation-delay: -2.7s; }
.quick-item:nth-child(3) { animation-delay: -5.4s; }
.quick-item:nth-child(4) { animation-delay: -8.1s; }
.feature-banner::before { animation-delay: -3.2s; }
.feature-banner { animation-delay: -4.1s; }
.service-card:nth-child(2)::before { animation-delay: -2.8s; }
.service-card:nth-child(3)::before { animation-delay: -5.6s; }
.service-card:nth-child(4)::before { animation-delay: -7.4s; }
.service-card:nth-child(2) { animation-delay: -3.6s; }
.service-card:nth-child(3) { animation-delay: -7.2s; }
.service-card:nth-child(4) { animation-delay: -9.4s; }
.assistant-card::before { animation-delay: -4.5s; }
.assistant-card { animation-delay: -5.8s; }

/* 持续流光只留给搜索与 AI 主入口，信息卡保持安静。 */
.quick-item,
.feature-banner,
.service-card { animation: none; }
.quick-item::before,
.feature-banner::before,
.service-card::before { animation: none; opacity: 0; }

.glass-search--pressed,
.glass-search:active,
.quick-item--pressed,
.quick-item:active,
.feature-banner--pressed,
.feature-banner:active,
.service-card--pressed,
.service-card:active,
.assistant-card--pressed,
.assistant-card:active {
  transform: translateY(1px) scale(.985);
  transition-duration: var(--yxg-touch-in);
  border-color: rgba(255,255,255,.82);
  color: inherit;
  background:
    linear-gradient(135deg, rgba(255,255,255,.78), rgba(241,231,248,.72)) padding-box,
    linear-gradient(108deg, rgba(91,43,143,.32), rgba(255,255,255,1), rgba(189,142,225,.78), rgba(91,43,143,.28)) border-box;
  background-size: 100% 100%, 220% 100%;
  box-shadow:
    inset 0 2px 10px rgba(91,43,143,.09),
    inset 0 -1px 0 rgba(255,255,255,.92),
    0 5px 15px rgba(91,43,143,.08);
  animation-play-state: paused;
}

.glass-search--pressed::before,
.glass-search:active::before,
.quick-item--pressed::before,
.quick-item:active::before,
.feature-banner--pressed::before,
.feature-banner:active::before,
.service-card--pressed::before,
.service-card:active::before,
.assistant-card--pressed::before,
.assistant-card:active::before {
  animation: glassTouchGlow .42s ease-out both;
}

.glass-search--pressed .search-orb,
.glass-search:active .search-orb,
.quick-item--pressed .quick-icon-wrap,
.quick-item:active .quick-icon-wrap,
.service-card--pressed .service-icon-wrap,
.service-card:active .service-icon-wrap,
.assistant-card--pressed .assistant-orb,
.assistant-card:active .assistant-orb {
  transform: scale(.965);
  color: #fff;
  background: #5b2b8f;
  box-shadow: inset 0 2px 8px rgba(39,14,66,.18), 0 4px 10px rgba(91,43,143,.12);
}

.glass-search--pressed .search-label,
.glass-search:active .search-label { color: #9a82ad; }
.glass-search--pressed .search-placeholder,
.glass-search:active .search-placeholder { color: #33273c; }
.glass-search--pressed .ask-btn,
.glass-search:active .ask-btn { border-color: rgba(255,255,255,.42); background: #5b2b8f; box-shadow: inset 0 2px 8px rgba(39,14,66,.18), 0 4px 10px rgba(91,43,143,.13); }
.glass-search--pressed .ask-icon,
.glass-search:active .ask-icon,
.quick-item--pressed .quick-icon,
.quick-item:active .quick-icon,
.assistant-card--pressed .assistant-icon,
.assistant-card:active .assistant-icon { color: #fff; }
.quick-item--pressed .quick-label,
.quick-item:active .quick-label { color: #3d2849; }
.quick-item--pressed .quick-caption,
.quick-item:active .quick-caption { color: #927b9c; }
.quick-item--pressed .quick-arrow,
.quick-item:active .quick-arrow { color: #75349f; transform: translateX(1px); }
.quick-item--pressed::after,
.quick-item:active::after { opacity: .08; transform: translate(50%,-50%) scale(1.15); }
.feature-banner--pressed .feature-kicker,
.feature-banner:active .feature-kicker { color: #9d79ad; }
.feature-banner--pressed .feature-title,
.feature-banner:active .feature-title,
.assistant-card--pressed .assistant-title,
.assistant-card:active .assistant-title { color: #43264f; }
.feature-banner--pressed .feature-desc,
.feature-banner:active .feature-desc,
.assistant-card--pressed .assistant-desc,
.assistant-card:active .assistant-desc { color: #8b7494; }
.feature-banner--pressed .feature-action,
.feature-banner:active .feature-action { color: #6d2d98; border-color: rgba(115,54,158,.24); background: rgba(255,255,255,.7); }
.service-card--pressed .service-label,
.service-card:active .service-label { color: #332c34; }
.service-card--pressed .service-desc,
.service-card:active .service-desc { color: #958a96; }
.assistant-card--pressed .assistant-arrow,
.assistant-card:active .assistant-arrow { color: #71339b; transform: translateX(1px); }
.ask-btn:active { transform: translateY(1px) scale(.97); }

.search-orb,
.ask-btn,
.quick-icon-wrap,
.quick-arrow,
.feature-action,
.service-icon-wrap,
.assistant-orb,
.assistant-arrow {
  transition: transform .3s cubic-bezier(.22,.78,.22,1), box-shadow .3s ease, color .24s ease, background .24s ease;
}

@keyframes glassEdgeDrift {
  from { background-position: 0 0, 100% 50%; }
  to { background-position: 0 0, -80% 50%; }
}

@keyframes glassGlint {
  0%, 9% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  14% { opacity: .55; }
  29% { opacity: 0; transform: translateX(345%) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(345%) skewX(-18deg); }
}

@keyframes glassTouchGlow {
  0% { opacity: .18; transform: translateX(120%) skewX(-18deg) scaleX(.85); }
  52% { opacity: .6; }
  100% { opacity: .22; transform: translateX(205%) skewX(-18deg) scaleX(1.2); }
}

/* Campus photo deck v7 — preserve each official photo's focal subject. */
.campus-hero {
  isolation: isolate;
  height: clamp(340px, 94vw, 382px);
  border-radius: 32px 32px 22px 12px;
}

.campus-visual {
  transform: scale(1.025);
  filter: saturate(.9) contrast(1.02);
}

.campus-visual.is-active {
  transform: scale(1);
}

.hero-shade {
  background:
    linear-gradient(90deg, rgba(34,15,55,.43) 0%, rgba(34,15,55,.08) 67%, rgba(34,15,55,.18) 100%),
    linear-gradient(180deg, rgba(30,13,48,.26) 0%, transparent 42%, rgba(30,13,48,.72) 100%);
  box-shadow: inset 0 92px 72px rgba(37,16,59,.23);
}

.hero-copy {
  max-width: 310px;
  padding-top: clamp(30px, 8vw, 40px);
}

.hero-title {
  max-width: 8.8em;
  font-size: clamp(27px, 7.35vw, 31px);
  line-height: 1.12;
  text-wrap: balance;
}

.hero-meta {
  max-width: 17em;
  font-size: 10px;
  line-height: 1.55;
}

@media (max-width: 360px) {
  .campus-caption { grid-template-columns: 84px minmax(0, 1fr); }
  .caption-sub { display: none; }
}

@media (prefers-reduced-motion: reduce) {
  .campus-visual,
  .slide-number,
  .ask-btn,
  .quick-item,
  .glass-search,
  .feature-banner,
  .service-card,
  .assistant-card { animation: none; }
  .glass-search::before,
  .quick-item::before,
  .feature-banner::before,
  .service-card::before,
  .assistant-card::before { animation: none !important; }
}
</style>
