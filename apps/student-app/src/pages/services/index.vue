<template>
  <view class="services-page">
    <view class="services-shell">
      <view class="services-topbar">
        <view class="topbar-brand">
          <view class="topbar-mark"><text class="material-symbols-outlined">school</text></view>
          <view>
            <text class="topbar-title">服务大厅</text>
            <text class="topbar-subtitle">山一大 · Campus Desk</text>
          </view>
        </view>
        <view class="topbar-action" @click="showAiGuide">
          <text class="material-symbols-outlined">auto_awesome</text>
        </view>
      </view>

      <scroll-view class="services-scroll" scroll-y>
        <view class="services-intro animate-fade-up delay-1">
          <text class="intro-kicker">YOUR CAMPUS, ORGANIZED</text>
          <text class="intro-title">一站式校园服务</text>
          <text class="intro-copy">从课程、证件到校园生活，找到下一步该做什么。</text>
          <view class="service-search">
            <text class="material-symbols-outlined search-icon">search</text>
            <input v-model="serviceQuery" class="search-input" placeholder="搜索服务或关键词" />
            <text v-if="serviceQuery" class="material-symbols-outlined clear-icon" @click="serviceQuery = ''">close</text>
          </view>
        </view>

        <scroll-view scroll-x class="category-scroll" show-scrollbar="false">
          <view class="category-list">
            <view
              v-for="category in categories"
              :key="category.id"
              :class="['category-pill', { active: activeCategory === category.id }]"
              @click="activeCategory = category.id"
            >
              <text>{{ category.label }}</text>
            </view>
          </view>
        </scroll-view>

        <view class="library-spotlight animate-fade-up delay-2" @click="openExternal('http://202.194.232.127/index.html')">
          <image class="spotlight-image" src="/static/images/yellow-river-library-hero.jpg" mode="aspectFill" />
          <view class="spotlight-shade" />
          <view class="spotlight-copy">
            <text class="spotlight-kicker">CROWN OF MEDICINE · LIBRARY</text>
            <text class="spotlight-title">黄河图书馆</text>
            <text class="spotlight-desc">馆藏查询 · 空间预约 · 学习服务</text>
          </view>
          <view class="spotlight-arrow"><text class="material-symbols-outlined">arrow_forward</text></view>
        </view>

        <view v-if="filteredServices.length" class="service-section animate-fade-up delay-3">
          <view class="section-heading">
            <view>
              <text class="section-kicker">SERVICES</text>
              <text class="section-title">{{ activeCategory === 'all' ? '校园事务' : categoryLabel }}</text>
            </view>
            <text class="section-count">{{ filteredServices.length }} 项</text>
          </view>
          <view class="service-grid">
            <view v-for="item in filteredServices" :key="item.label" class="service-card" @click="handleServiceClick(item)">
              <view class="service-card-top">
                <view class="service-icon-box"><text class="material-symbols-outlined">{{ item.icon }}</text></view>
                <text v-if="item.sso" class="service-tag">统一认证</text>
                <text v-else class="material-symbols-outlined service-external">open_in_new</text>
              </view>
              <text class="service-name">{{ item.label }}</text>
              <text class="service-caption">{{ item.caption }}</text>
            </view>
          </view>
        </view>

        <view v-else class="empty-state">
          <text class="material-symbols-outlined empty-icon">search_off</text>
          <text class="empty-title">没有找到相关服务</text>
          <text class="empty-copy">试试搜索“成绩”“校园卡”或“报修”</text>
        </view>

        <view class="ai-help-card animate-fade-up delay-4" @click="showAiGuide">
          <view class="ai-help-icon"><text class="material-symbols-outlined">auto_awesome</text></view>
          <view class="ai-help-copy">
            <text class="ai-help-title">不知道从哪里开始？</text>
            <text class="ai-help-desc">让 AI 小管帮你找到办理路径</text>
          </view>
          <text class="material-symbols-outlined ai-help-arrow">arrow_forward</text>
        </view>

        <view class="bottom-safe" />
      </scroll-view>
    </view>
    <CustomTabBar current="services" />
    <FeatureNoticeSheet />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import CustomTabBar from '@/components/CustomTabBar.vue'
import FeatureNoticeSheet from '@/components/FeatureNoticeSheet.vue'
import { openAiQuestion, openExternal, openSsoExternal, showComingSoon } from '@/composables/useServiceNavigation'
import { trackEvent } from '@/utils/track'

interface ServiceItem {
  icon: string
  label: string
  caption: string
  category: string
  url?: string
  sso?: boolean
  aiQuestion?: string
  comingSoon?: boolean
}

const serviceQuery = ref('')
const activeCategory = ref('all')
const categories = [
  { id: 'all', label: '全部服务' },
  { id: 'affairs', label: '校园事务' },
  { id: 'study', label: '学业资源' },
  { id: 'life', label: '校园生活' },
]

const campusServices: ServiceItem[] = [
  { icon: 'meeting_room', label: '空教室申请', caption: '申请与查看开放教室', category: 'affairs', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=383', sso: true },
  { icon: 'feedback', label: '接诉即办', caption: '校园问题快速反馈', category: 'affairs', url: 'https://ehall.sdfmu.edu.cn/v2/matter/start?id=378', sso: true },
  { icon: 'handyman', label: '网上报修', caption: '宿舍与公共设施报修', category: 'life', url: 'https://metc.sdfmu.edu.cn/info/1073/1954.htm' },
  { icon: 'school', label: '学籍办理', caption: '证明与学籍事务', category: 'study', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=369', sso: true },
  { icon: 'home_work', label: '校外住宿', caption: '住宿申请与备案', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=394', sso: true },
  { icon: 'volunteer_activism', label: '困难补助', caption: '学生资助申请', category: 'affairs', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=417', sso: true },
  { icon: 'groups', label: '活动室预约', caption: '场地预约与管理', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=445', sso: true },
  { icon: 'credit_card', label: '校园卡服务', caption: '卡务、充值与挂失', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=443', sso: true },
  { icon: 'wifi', label: '校园网', caption: '网络连接与服务', category: 'life', url: 'http://vpnportal.sdfmu.edu.cn' },
  { icon: 'podium', label: '学术讲座', caption: '讲座报名与日程', category: 'study', url: 'http://academic.sdfmu.edu.cn/index.php?redirect=apply/showlist' },
  { icon: 'event_available', label: '预约中心', caption: '场地与资源预约', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/reserve/special_info?id=3', sso: true },
  { icon: 'qr_code', label: '访客预约', caption: '访客入校申请', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/reserve/special_info?id=2', sso: true },
  { icon: 'face_retouching_natural', label: '人脸采集', caption: '身份信息采集', category: 'affairs', url: 'https://fpc.sdfmu.edu.cn/#/home', sso: true },
  { icon: 'photo_camera', label: '证件照采集', caption: '在线采集证件照', category: 'affairs', url: 'https://ppu.sdfmu.edu.cn', sso: true },
  { icon: 'live_tv', label: '直播山一大', caption: '校园活动直播', category: 'life', url: 'https://qjjern.vnet.weizan.cn/live/channelpage-253967?v=1764637917204' },
  { icon: 'apps', label: '更多服务', caption: '查看全部校园应用', category: 'all', url: 'https://ehall.sdfmu.edu.cn/v2/site/serviceList', sso: true },
]

const categoryLabel = computed(() => categories.find(item => item.id === activeCategory.value)?.label || '校园事务')
const filteredServices = computed(() => {
  const query = serviceQuery.value.trim().toLowerCase()
  return campusServices.filter(item => {
    const categoryMatch = activeCategory.value === 'all' || item.category === activeCategory.value
    const queryMatch = !query || `${item.label}${item.caption}`.toLowerCase().includes(query)
    return categoryMatch && queryMatch
  })
})

onShow(() => trackEvent('page_view', { path: '/pages/services/index' }))

function handleServiceClick(item: ServiceItem) {
  trackEvent('service_card_click', { card: item.label, source: 'services' })
  if (item.url) item.sso ? openSsoExternal(item.url) : openExternal(item.url)
  else if (item.comingSoon) showComingSoon(item.label, item.aiQuestion)
  else if (item.aiQuestion) openAiQuestion(item.aiQuestion)
}

function showAiGuide() { openAiQuestion('我不知道应该办理哪项校园服务，可以帮我判断吗？') }
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.services-page { min-height: 100dvh; width: min(100%, 390px); margin: 0 auto; background: #f4efe9; color: #302937; }
.services-shell { min-height: 100dvh; display: flex; flex-direction: column; }
.services-topbar { padding: calc(env(safe-area-inset-top) + 16px) 20px 14px; display: flex; align-items: center; justify-content: space-between; background: #f4efe9; }
.topbar-brand { display: flex; align-items: center; gap: 10px; }
.topbar-mark { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border-radius: 12px; background: #5b2b8f; color: #fff; }
.topbar-mark .material-symbols-outlined { font-size: 18px; }
.topbar-title { display: block; color: #302937; font-size: 17px; font-weight: 850; }
.topbar-subtitle { display: block; margin-top: 2px; color: #9c909d; font-size: 8px; letter-spacing: .08em; }
.topbar-action { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 13px; color: #5b2b8f; background: #e9deeb; }
.topbar-action .material-symbols-outlined { font-size: 19px; }
.services-scroll { flex: 1; height: 0; padding: 0 18px; box-sizing: border-box; }
.services-intro { padding: 15px 2px 0; }
.intro-kicker, .section-kicker { display: block; color: #9b7bb7; font-size: 8px; font-weight: 850; letter-spacing: .16em; }
.intro-title { display: block; margin-top: 8px; color: #302937; font-size: 27px; line-height: 1.15; font-weight: 850; letter-spacing: -.05em; }
.intro-copy { display: block; margin-top: 7px; color: #857888; font-size: 11px; }
.service-search { height: 50px; margin-top: 18px; padding: 0 14px; display: flex; align-items: center; gap: 9px; border-radius: 16px; background: rgba(255,255,255,.90); box-shadow: inset 0 1px 0 #fff, 0 8px 22px rgba(68,42,84,.06); }
.search-icon { color: #5b2b8f; font-size: 20px; }
.search-input { flex: 1; height: 100%; color: #302937; font-size: 12px; }
.clear-icon { color: #b7abb9; font-size: 17px; }
.category-scroll { margin: 19px -18px 0; white-space: nowrap; }
.category-list { display: inline-flex; gap: 8px; padding: 0 18px; }
.category-pill { padding: 9px 14px; border-radius: 999px; color: #8e8190; background: #e9e0d9; font-size: 10px; font-weight: 800; }
.category-pill.active { color: #fff; background: #5b2b8f; box-shadow: 0 7px 16px rgba(91,43,143,.18); }
.library-spotlight { position: relative; min-height: 132px; margin-top: 20px; overflow: hidden; border-radius: 20px; background: #3e236d; box-shadow: 0 16px 32px rgba(62,35,109,.17); }
.spotlight-image, .spotlight-shade { position: absolute; inset: 0; width: 100%; height: 100%; }
.spotlight-image { opacity: .50; object-position: center 45%; }
.spotlight-shade { background: rgba(62,35,109,.40); }
.spotlight-copy { position: relative; z-index: 2; padding: 19px; color: #fff; }
.spotlight-kicker { display: block; color: rgba(255,255,255,.58); font-size: 8px; font-weight: 800; letter-spacing: .13em; }
.spotlight-title { display: block; margin-top: 9px; font-size: 22px; font-weight: 850; }
.spotlight-desc { display: block; margin-top: 5px; color: rgba(255,255,255,.72); font-size: 10px; }
.spotlight-arrow { position: absolute; right: 16px; bottom: 16px; z-index: 2; width: 31px; height: 31px; display: flex; align-items: center; justify-content: center; border-radius: 11px; color: #fff; background: rgba(255,255,255,.17); }
.spotlight-arrow .material-symbols-outlined { font-size: 17px; }
.service-section { margin-top: 28px; }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 13px; }
.section-title { display: block; margin-top: 4px; color: #302937; font-size: 19px; font-weight: 850; }
.section-count { color: #a99ca9; font-size: 10px; font-weight: 700; }
.service-grid { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 10px; }
.service-card { min-height: 122px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; border-radius: 18px; background: rgba(255,255,255,.82); box-shadow: inset 0 1px 0 #fff; }
.service-card:active { transform: scale(.98); }
.service-card-top { display: flex; align-items: flex-start; justify-content: space-between; }
.service-icon-box { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border-radius: 12px; color: #5b2b8f; background: #e9ddf0; }
.service-icon-box .material-symbols-outlined { font-size: 19px; }
.service-tag { padding: 4px 6px; border-radius: 6px; color: #8f78a0; background: #f0eaf4; font-size: 7px; font-weight: 800; }
.service-external { color: #b2a6b4; font-size: 16px; }
.service-name { display: block; margin-top: 14px; color: #393040; font-size: 13px; font-weight: 800; }
.service-caption { display: block; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #a095a1; font-size: 9px; }
.empty-state { padding: 48px 20px; text-align: center; }
.empty-icon { color: #b0a0b4; font-size: 32px; }
.empty-title { display: block; margin-top: 12px; color: #5d5160; font-size: 14px; font-weight: 800; }
.empty-copy { display: block; margin-top: 5px; color: #a59aa5; font-size: 10px; }
.ai-help-card { margin: 25px 0 0; padding: 15px; display: flex; align-items: center; gap: 11px; border-radius: 18px; color: #fff; background: #5b2b8f; box-shadow: 0 14px 28px rgba(91,43,143,.16); }
.ai-help-icon { width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; border-radius: 12px; background: rgba(255,255,255,.16); }
.ai-help-icon .material-symbols-outlined { font-size: 19px; }
.ai-help-copy { flex: 1; min-width: 0; }
.ai-help-title { display: block; font-size: 12px; font-weight: 800; }
.ai-help-desc { display: block; margin-top: 3px; color: rgba(255,255,255,.65); font-size: 9px; }
.ai-help-arrow { color: rgba(255,255,255,.8); font-size: 19px; }
.bottom-safe { height: calc(var(--tabbar-safe) + 18px); }
</style>
