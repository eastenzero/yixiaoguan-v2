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
        <view
          class="topbar-action"
          hover-class="topbar-action--pressed"
          :hover-start-time="0"
          :hover-stay-time="140"
          @click="showAiGuide"
        >
          <text class="material-symbols-outlined">auto_awesome</text>
        </view>
      </view>

      <scroll-view class="services-scroll" scroll-y>
        <view class="services-intro animate-fade-up delay-1">
          <text class="intro-kicker">YOUR CAMPUS, ORGANIZED</text>
          <text class="intro-title">一站式校园服务</text>
          <text class="intro-copy">只收录可直接办理、查询、缴费或预约的官方入口。</text>
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
              hover-class="category-pill--pressed"
              :hover-start-time="0"
              :hover-stay-time="120"
              @click="activeCategory = category.id"
            >
              <text>{{ category.label }}</text>
            </view>
          </view>
        </scroll-view>

        <view
          class="library-spotlight animate-fade-up delay-2"
          hover-class="library-spotlight--pressed"
          :hover-start-time="0"
          :hover-stay-time="140"
          @click="openExternal('http://202.194.232.127/index.html')"
        >
          <image class="spotlight-image" src="/static/images/sdfmu-official-library-exterior.jpg" mode="aspectFill" />
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
            <view
              v-for="item in filteredServices"
              :key="item.label"
              class="service-card"
              hover-class="service-card--pressed"
              :hover-start-time="0"
              :hover-stay-time="140"
              @click="handleServiceClick(item)"
            >
              <view class="service-card-top">
                <view class="service-icon-box"><text class="material-symbols-outlined">{{ item.icon }}</text></view>
                <text class="service-tag">{{ item.actionLabel || (item.sso ? '统一认证' : '进入系统') }}</text>
              </view>
              <text class="service-name">{{ item.label }}</text>
              <text class="service-caption">{{ item.caption }}</text>
            </view>
          </view>
        </view>

        <view v-else class="empty-state">
          <text class="material-symbols-outlined empty-icon">search_off</text>
          <text class="empty-title">没有找到相关服务</text>
          <text class="empty-copy">试试搜索“成绩”“缴费”或“预约”</text>
        </view>

        <view
          class="ai-help-card animate-fade-up delay-4"
          hover-class="ai-help-card--pressed"
          :hover-start-time="0"
          :hover-stay-time="140"
          @click="showAiGuide"
        >
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
  actionLabel?: string
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
  { icon: 'payments', label: '校园缴费', caption: '学费、住宿费及其他费用', category: 'life', url: 'https://cwpt.sdfmu.edu.cn/xysf/', actionLabel: '去缴费' },
  { icon: 'menu_book', label: '本科教务', caption: '选课、课表与成绩查询', category: 'study', url: 'https://jwc.sdfmu.edu.cn/academic/common/security/login.jsp', actionLabel: '进系统' },
  { icon: 'mail', label: '校园邮箱', caption: '学生邮件与校园通知', category: 'affairs', url: 'https://mail.sdfmu.edu.cn/', actionLabel: '去登录' },
  { icon: 'work', label: '就业服务', caption: '招聘信息与就业服务', category: 'study', url: 'https://school.gxjy.sdei.edu.cn/sdfmu', actionLabel: '查岗位' },
  { icon: 'meeting_room', label: '空教室申请', caption: '申请与查看开放教室', category: 'affairs', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=383', sso: true, actionLabel: '去申请' },
  { icon: 'feedback', label: '接诉即办', caption: '校园问题快速反馈', category: 'affairs', url: 'https://ehall.sdfmu.edu.cn/v2/matter/start?id=378', sso: true, actionLabel: '去反馈' },
  { icon: 'school', label: '学籍办理', caption: '证明与学籍事务', category: 'study', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=369', sso: true, actionLabel: '去办理' },
  { icon: 'home_work', label: '校外住宿', caption: '住宿申请与备案', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=394', sso: true, actionLabel: '去申请' },
  { icon: 'volunteer_activism', label: '困难补助', caption: '学生资助申请', category: 'affairs', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=417', sso: true, actionLabel: '去申请' },
  { icon: 'groups', label: '活动室预约', caption: '场地预约与管理', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=445', sso: true, actionLabel: '去预约' },
  { icon: 'credit_card', label: '校园卡服务', caption: '卡务、充值与挂失', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=443', sso: true, actionLabel: '去办理' },
  { icon: 'language', label: '信息门户', caption: '校外访问校园应用', category: 'affairs', url: 'http://vpnportal.sdfmu.edu.cn', actionLabel: '去登录' },
  { icon: 'podium', label: '学术讲座', caption: '讲座报名与日程', category: 'study', url: 'http://academic.sdfmu.edu.cn/index.php?redirect=apply/showlist', actionLabel: '去报名' },
  { icon: 'event_available', label: '预约中心', caption: '场地与资源预约', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/reserve/special_info?id=3', sso: true, actionLabel: '去预约' },
  { icon: 'qr_code', label: '访客预约', caption: '访客入校申请', category: 'life', url: 'https://ehall.sdfmu.edu.cn/v2/reserve/special_info?id=2', sso: true, actionLabel: '去预约' },
  { icon: 'face_retouching_natural', label: '人脸采集', caption: '身份信息在线采集', category: 'affairs', url: 'https://fpc.sdfmu.edu.cn/#/home', sso: true, actionLabel: '去采集' },
  { icon: 'photo_camera', label: '证件照采集', caption: '在线采集证件照', category: 'affairs', url: 'https://ppu.sdfmu.edu.cn', sso: true, actionLabel: '去采集' },
  { icon: 'apps', label: '更多服务', caption: '进入学校网上服务大厅', category: 'all', url: 'https://ehall.sdfmu.edu.cn/v2/site/serviceList', sso: true, actionLabel: '全部应用' },
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

.services-page { min-height: 100vh; min-height: 100dvh; width: min(100%, 430px); margin: 0 auto; overflow: hidden; background: radial-gradient(circle at 96% 0%, rgba(186,150,226,.20), transparent 30%), #f4efe9; color: #302937; }
.services-shell { height: 100vh; height: 100dvh; min-height: 0; display: flex; flex-direction: column; overflow: hidden; }
.services-topbar { padding: calc(env(safe-area-inset-top) + 16px) 20px 14px; display: flex; align-items: center; justify-content: space-between; background: #f4efe9; }
.topbar-brand { display: flex; align-items: center; gap: 10px; }
.topbar-mark { width: 34px; height: 34px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,.65); border-radius: 12px; background: #5b2b8f; color: #fff; box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 7px 16px rgba(91,43,143,.15); }
.topbar-mark .material-symbols-outlined { font-size: 18px; }
.topbar-title { display: block; color: #302937; font-size: 17px; font-weight: 850; }
.topbar-subtitle { display: block; margin-top: 2px; color: #9c909d; font-size: 8px; letter-spacing: .08em; }
.topbar-action { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(130,70,175,.28); border-radius: 13px; color: #6f329a; background: linear-gradient(145deg, #fff, #ead9f3); box-shadow: inset 0 -2px 0 rgba(122,60,167,.16); transition: transform .16s cubic-bezier(.2,.8,.2,1), color .16s ease, background .16s ease, box-shadow .16s ease; }
.topbar-action--pressed,
.topbar-action:active { transform: translateY(2px) scale(.94); color: #fff; border-color: rgba(255,255,255,.72); background: #5b2b8f; box-shadow: inset 0 2px 7px rgba(38,14,66,.24); }
.topbar-action .material-symbols-outlined { font-size: 19px; }
.services-scroll { flex: 1 1 auto; width: 100%; height: auto; min-height: 0; padding: 0 18px; box-sizing: border-box; -webkit-overflow-scrolling: touch; }
.services-intro { padding: 15px 2px 0; }
.intro-kicker, .section-kicker { display: block; color: #9b7bb7; font-size: 8px; font-weight: 850; letter-spacing: .16em; }
.intro-title { display: block; margin-top: 8px; color: #302937; font-size: 27px; line-height: 1.15; font-weight: 850; letter-spacing: -.05em; }
.intro-copy { display: block; margin-top: 7px; color: #857888; font-size: 11px; }
.service-search { height: 50px; margin-top: 18px; padding: 0 14px; display: flex; align-items: center; gap: 9px; border: 1px solid rgba(135,76,181,.24); border-radius: 18px; background: linear-gradient(145deg, rgba(255,255,255,.96), rgba(241,226,248,.76)); box-shadow: inset 0 1px 0 #fff, inset 0 -2px 0 rgba(124,59,170,.14), 0 8px 22px rgba(68,42,84,.06); }
.search-icon { color: #5b2b8f; font-size: 20px; }
.search-input { flex: 1; height: 100%; color: #302937; font-size: 12px; }
.clear-icon { color: #b7abb9; font-size: 17px; }
.category-scroll { margin: 19px -18px 0; white-space: nowrap; }
.category-list { display: inline-flex; gap: 8px; padding: 0 18px; }
.category-pill { padding: 9px 14px; border: 1px solid rgba(132,74,174,.18); border-radius: 999px; color: #826b8c; background: rgba(255,255,255,.62); font-size: 10px; font-weight: 800; transition: transform .16s cubic-bezier(.2,.8,.2,1), color .16s ease, background .16s ease; }
.category-pill.active { color: #fff; border-color: rgba(255,255,255,.55); background: #5b2b8f; box-shadow: inset 0 1px 0 rgba(255,255,255,.22), 0 7px 16px rgba(91,43,143,.15); }
.category-pill--pressed,
.category-pill:active { transform: scale(.94); color: #fff; background: #5b2b8f; }
.library-spotlight { position: relative; min-height: 132px; margin-top: 20px; overflow: hidden; border: 1px solid transparent; border-radius: 20px; background: #3e236d; box-shadow: 0 16px 32px rgba(62,35,109,.17); transition: transform .18s cubic-bezier(.2,.8,.2,1), box-shadow .18s ease, border-color .18s ease; }
.library-spotlight::after,
.service-card::before,
.ai-help-card::before {
  content: '';
  position: absolute;
  z-index: 3;
  inset: -35% -55%;
  pointer-events: none;
  opacity: 0;
  transform: translateX(-70%) rotate(8deg);
  background: linear-gradient(100deg, transparent 35%, rgba(255,255,255,.82) 50%, transparent 65%);
}
.library-spotlight--pressed,
.library-spotlight:active { transform: translateY(2px) scale(.97); border-color: rgba(255,255,255,.78); box-shadow: inset 0 2px 9px rgba(38,14,66,.20), 0 6px 16px rgba(62,35,109,.12); }
.library-spotlight--pressed::after,
.library-spotlight:active::after { animation: pressSheen .52s ease-out both; }
.library-spotlight--pressed .spotlight-arrow,
.library-spotlight:active .spotlight-arrow { color: #5b2b8f; background: #fff; transform: translateX(2px); }
.spotlight-image, .spotlight-shade { position: absolute; inset: 0; width: 100%; height: 100%; }
.spotlight-image { opacity: .82; object-position: center 45%; }
.spotlight-shade { background: linear-gradient(90deg, rgba(47,23,72,.76), rgba(47,23,72,.22)); }
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
.service-card { position: relative; min-height: 126px; padding: 14px; display: flex; flex-direction: column; justify-content: space-between; overflow: hidden; border: 1px solid transparent; border-radius: 21px; background: linear-gradient(135deg, rgba(255,255,255,.96), rgba(247,240,250,.92)) padding-box, linear-gradient(110deg, rgba(91,43,143,.15) 0 38%, rgba(210,177,235,.84) 48%, rgba(91,43,143,.58) 54%, rgba(91,43,143,.15) 64%) border-box; background-size: 100% 100%, 260% 100%; box-shadow: inset 0 1px 0 #fff, 0 10px 24px rgba(91,43,143,.06); animation: violetEdgeFlow 7.6s linear infinite; transition: transform .16s cubic-bezier(.2,.8,.2,1), box-shadow .16s ease; }
.service-card::after { content: ''; position: absolute; z-index: 1; width: 78px; height: 78px; right: 12%; top: 42%; border-radius: 50%; pointer-events: none; opacity: 0; transform: translate(50%,-50%) scale(.18); background: rgba(255,255,255,.44); transition: opacity .18s ease, transform .36s cubic-bezier(.2,.8,.2,1); }
.service-card > * { position: relative; z-index: 2; }
.service-card--pressed,
.service-card:active { transform: translateY(2px) scale(.97); border-color: rgba(255,255,255,.78); background: #5b2b8f; box-shadow: inset 0 2px 9px rgba(38,14,66,.22), 0 5px 14px rgba(91,43,143,.12); }
.service-card--pressed::before,
.service-card:active::before { animation: pressSheen .52s ease-out both; }
.service-card--pressed::after,
.service-card:active::after { opacity: .2; transform: translate(50%,-50%) scale(1.7); }
.service-card--pressed .service-icon-box,
.service-card:active .service-icon-box { color: #5b2b8f; border-color: #fff; background: #fff; box-shadow: 0 6px 14px rgba(40,15,68,.18); }
.service-card--pressed .service-tag,
.service-card:active .service-tag { color: #5b2b8f; background: #fff; }
.service-card--pressed .service-name,
.service-card:active .service-name { color: #fff; }
.service-card--pressed .service-caption,
.service-card:active .service-caption { color: rgba(255,255,255,.66); }
.service-card-top { display: flex; align-items: flex-start; justify-content: space-between; }
.service-icon-box { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,.68); border-radius: 14px; color: #fff; background: #5b2b8f; box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 8px 16px rgba(91,43,143,.15); }
.service-icon-box .material-symbols-outlined { font-size: 19px; }
.service-tag { padding: 4px 7px; border-radius: 7px; color: #7c648e; background: #f0eaf4; font-size: 8px; font-weight: 800; }
.service-name { display: block; margin-top: 14px; color: #393040; font-size: 13px; font-weight: 800; }
.service-caption { display: block; margin-top: 4px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: #a095a1; font-size: 9px; }
.empty-state { padding: 48px 20px; text-align: center; }
.empty-icon { color: #b0a0b4; font-size: 32px; }
.empty-title { display: block; margin-top: 12px; color: #5d5160; font-size: 14px; font-weight: 800; }
.empty-copy { display: block; margin-top: 5px; color: #a59aa5; font-size: 10px; }
.ai-help-card { position: relative; margin: 25px 0 0; padding: 15px; display: flex; align-items: center; gap: 11px; overflow: hidden; border: 1px solid rgba(91,43,143,.18); border-radius: 21px; color: #43264f; background: linear-gradient(115deg, #fbf8fc, #eee2f5); box-shadow: inset 0 1px 0 #fff, 0 10px 24px rgba(91,43,143,.08); transition: transform .16s cubic-bezier(.2,.8,.2,1), box-shadow .16s ease; }
.ai-help-card > * { position: relative; z-index: 2; }
.ai-help-card--pressed,
.ai-help-card:active { transform: translateY(2px) scale(.97); border-color: rgba(255,255,255,.76); color: #fff; background: #5b2b8f; box-shadow: inset 0 2px 9px rgba(38,14,66,.22), 0 5px 14px rgba(91,43,143,.12); }
.ai-help-card--pressed::before,
.ai-help-card:active::before { animation: pressSheen .52s ease-out both; }
.ai-help-card--pressed .ai-help-icon,
.ai-help-card:active .ai-help-icon { color: #5b2b8f; background: #fff; box-shadow: 0 6px 14px rgba(40,15,68,.18); }
.ai-help-card--pressed .ai-help-desc,
.ai-help-card:active .ai-help-desc { color: rgba(255,255,255,.66); }
.ai-help-card--pressed .ai-help-arrow,
.ai-help-card:active .ai-help-arrow { color: #fff; transform: translateX(2px); }
.ai-help-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 14px; color: #fff; background: #5b2b8f; box-shadow: inset 0 1px 0 rgba(255,255,255,.24), 0 8px 16px rgba(91,43,143,.15); }
.ai-help-icon .material-symbols-outlined { font-size: 19px; }
.ai-help-copy { flex: 1; min-width: 0; }
.ai-help-title { display: block; font-size: 12px; font-weight: 800; }
.ai-help-desc { display: block; margin-top: 3px; color: #8b7494; font-size: 9px; }
.ai-help-arrow { color: #71339b; font-size: 19px; }
.bottom-safe { height: calc(var(--tabbar-safe) + 18px); }

@keyframes violetEdgeFlow {
  from { background-position: 0 0, 100% 0; }
  to { background-position: 0 0, -160% 0; }
}

@keyframes pressSheen {
  0% { opacity: 0; transform: translateX(-70%) rotate(8deg); }
  22% { opacity: .72; }
  100% { opacity: 0; transform: translateX(70%) rotate(8deg); }
}

/* Coordinated liquid-glass motion for the service flow. */
.topbar-action {
  color: #6f329a;
  border-color: rgba(125,66,170,.22);
  background: linear-gradient(145deg, rgba(255,255,255,.82), rgba(235,220,245,.58));
  backdrop-filter: blur(18px) saturate(150%);
  -webkit-backdrop-filter: blur(18px) saturate(150%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), inset 0 -1px 0 rgba(91,43,143,.08), 0 7px 16px rgba(91,43,143,.08);
  transition: transform var(--yxg-touch-out) var(--yxg-spring-out), box-shadow var(--yxg-touch-out) var(--yxg-spring-out);
}
.topbar-action--pressed,
.topbar-action:active {
  transform: translateY(1px) scale(.97);
  transition-duration: var(--yxg-touch-in);
  color: #6f329a;
  border-color: rgba(255,255,255,.82);
  background: linear-gradient(145deg, rgba(255,255,255,.76), rgba(231,211,243,.66));
  box-shadow: inset 0 2px 8px rgba(91,43,143,.10), 0 3px 9px rgba(91,43,143,.07);
}

.category-pill--pressed,
.category-pill:active { transform: scale(.97); }
.category-pill:not(.active).category-pill--pressed,
.category-pill:not(.active):active { color: #826b8c; background: rgba(245,236,249,.82); }

.service-card,
.ai-help-card {
  border: 1px solid transparent;
  background:
    linear-gradient(135deg, rgba(255,255,255,.84), rgba(248,242,251,.66)) padding-box,
    linear-gradient(108deg, rgba(91,43,143,.17) 0%, rgba(255,255,255,.96) 24%, rgba(194,155,224,.62) 45%, rgba(91,43,143,.34) 62%, rgba(255,255,255,.88) 82%, rgba(91,43,143,.16) 100%) border-box;
  background-size: 100% 100%, 280% 100%;
  backdrop-filter: blur(22px) saturate(155%);
  -webkit-backdrop-filter: blur(22px) saturate(155%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), inset 0 -1px 0 rgba(91,43,143,.07), 0 10px 26px rgba(91,43,143,.07);
  animation: glassEdgeDrift 11.2s ease-in-out infinite alternate;
  transition: transform var(--yxg-touch-out) var(--yxg-spring-out), box-shadow var(--yxg-touch-out) var(--yxg-spring-out), border-color .24s ease, background .38s ease;
  transform: translateZ(0);
}

.library-spotlight::after,
.service-card::before,
.ai-help-card::before {
  inset: -55% auto -55% -48%;
  width: 46%;
  opacity: 0;
  transform: translateX(0) skewX(-18deg);
  filter: blur(7px);
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.72), rgba(229,207,246,.34), transparent);
  animation: glassGlint 8.8s cubic-bezier(.3,.02,.2,1) infinite;
  will-change: transform, opacity;
}

.service-card:nth-child(2)::before { animation-delay: -1.6s; }
.service-card:nth-child(3)::before { animation-delay: -3.2s; }
.service-card:nth-child(4)::before { animation-delay: -4.8s; }
.service-card:nth-child(5)::before { animation-delay: -6.4s; }
.service-card:nth-child(6)::before { animation-delay: -8s; }
.service-card:nth-child(2) { animation-delay: -2.2s; }
.service-card:nth-child(3) { animation-delay: -4.4s; }
.service-card:nth-child(4) { animation-delay: -6.6s; }
.service-card:nth-child(5) { animation-delay: -8.8s; }
.service-card:nth-child(6) { animation-delay: -10.1s; }
.ai-help-card::before { animation-delay: -4.4s; }
.ai-help-card { animation-delay: -5.7s; }
.library-spotlight::after { animation-delay: -2.4s; }

/* 服务条目不持续闪烁，流光只留给焦点入口。 */
.service-card { animation: none; }
.service-card::before { animation: none; opacity: 0; }

.library-spotlight--pressed,
.library-spotlight:active,
.service-card--pressed,
.service-card:active,
.ai-help-card--pressed,
.ai-help-card:active {
  transform: translateY(1px) scale(.985);
  transition-duration: var(--yxg-touch-in);
  border-color: rgba(255,255,255,.82);
  color: inherit;
  box-shadow: inset 0 2px 10px rgba(91,43,143,.09), inset 0 -1px 0 rgba(255,255,255,.92), 0 5px 15px rgba(91,43,143,.08);
  animation-play-state: paused;
}

.service-card--pressed,
.service-card:active,
.ai-help-card--pressed,
.ai-help-card:active {
  background:
    linear-gradient(135deg, rgba(255,255,255,.78), rgba(241,231,248,.72)) padding-box,
    linear-gradient(108deg, rgba(91,43,143,.32), rgba(255,255,255,1), rgba(189,142,225,.78), rgba(91,43,143,.28)) border-box;
  background-size: 100% 100%, 220% 100%;
}

.library-spotlight--pressed::after,
.library-spotlight:active::after,
.service-card--pressed::before,
.service-card:active::before,
.ai-help-card--pressed::before,
.ai-help-card:active::before { animation: glassTouchGlow .42s ease-out both; }

.library-spotlight--pressed .spotlight-arrow,
.library-spotlight:active .spotlight-arrow {
  color: #fff;
  background: rgba(255,255,255,.2);
  transform: translateX(1px) scale(.96);
}
.service-card--pressed::after,
.service-card:active::after { opacity: .08; transform: translate(50%,-50%) scale(1.15); }
.service-card--pressed .service-icon-box,
.service-card:active .service-icon-box,
.ai-help-card--pressed .ai-help-icon,
.ai-help-card:active .ai-help-icon {
  transform: scale(.965);
  color: #fff;
  border-color: rgba(255,255,255,.7);
  background: #5b2b8f;
  box-shadow: inset 0 2px 8px rgba(39,14,66,.18), 0 4px 10px rgba(91,43,143,.12);
}
.service-card--pressed .service-tag,
.service-card:active .service-tag { color: #8f78a0; background: #f0eaf4; }
.service-card--pressed .service-name,
.service-card:active .service-name { color: #393040; }
.service-card--pressed .service-caption,
.service-card:active .service-caption { color: #a095a1; }
.ai-help-card--pressed .ai-help-title,
.ai-help-card:active .ai-help-title { color: #43264f; }
.ai-help-card--pressed .ai-help-desc,
.ai-help-card:active .ai-help-desc { color: #8b7494; }
.ai-help-card--pressed .ai-help-arrow,
.ai-help-card:active .ai-help-arrow { color: #71339b; transform: translateX(1px); }

.spotlight-arrow,
.service-icon-box,
.service-tag,
.ai-help-icon,
.ai-help-arrow {
  transition: transform .3s cubic-bezier(.22,.78,.22,1), box-shadow .3s ease, color .24s ease, background .24s ease;
}

@keyframes glassEdgeDrift {
  from { background-position: 0 0, 100% 50%; }
  to { background-position: 0 0, -80% 50%; }
}

@keyframes glassGlint {
  0%, 9% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  14% { opacity: .52; }
  29% { opacity: 0; transform: translateX(345%) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(345%) skewX(-18deg); }
}

@keyframes glassTouchGlow {
  0% { opacity: .18; transform: translateX(120%) skewX(-18deg) scaleX(.85); }
  52% { opacity: .58; }
  100% { opacity: .2; transform: translateX(205%) skewX(-18deg) scaleX(1.2); }
}

@media (prefers-reduced-motion: reduce) {
  .service-card,
  .ai-help-card { animation: none; }
  .library-spotlight::after,
  .service-card::before,
  .ai-help-card::before { animation: none !important; }
}
</style>
