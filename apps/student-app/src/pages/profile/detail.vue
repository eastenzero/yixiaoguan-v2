<template>
  <view class="detail-page">
    <view class="detail-topbar">
      <view class="back-action" hover-class="back-action--pressed" @click="goBack">
        <text class="material-symbols-outlined">arrow_back</text>
      </view>
      <text class="topbar-title">{{ page.title }}</text>
      <view class="topbar-space" />
    </view>

    <scroll-view class="detail-scroll" scroll-y>
      <view class="detail-hero">
        <view class="hero-icon"><text class="material-symbols-outlined">{{ page.icon }}</text></view>
        <text class="hero-title">{{ page.title }}</text>
        <text class="hero-caption">{{ page.caption }}</text>
      </view>

      <view v-if="type === 'settings'" class="detail-card">
        <view class="detail-row static-row">
          <view class="row-icon"><text class="material-symbols-outlined">motion_photos_off</text></view>
          <view class="row-copy">
            <text class="row-label">减少动效</text>
            <text class="row-caption">关闭流光与页面过渡动画</text>
          </view>
          <switch color="#5b2b8f" :checked="reducedMotion" @change="setReducedMotion" />
        </view>
        <view class="detail-row" hover-class="detail-row--pressed" @click="clearLocalState">
          <view class="row-icon"><text class="material-symbols-outlined">cleaning_services</text></view>
          <view class="row-copy">
            <text class="row-label">清理本机临时状态</text>
            <text class="row-caption">不删除服务器上的历史对话</text>
          </view>
          <text class="material-symbols-outlined row-chevron">chevron_right</text>
        </view>
      </view>

      <view v-else class="detail-card">
        <view
          v-for="row in rows"
          :key="row.label"
          :class="['detail-row', { 'static-row': !row.action }]"
          hover-class="detail-row--pressed"
          @click="handleRow(row)"
        >
          <view class="row-icon"><text class="material-symbols-outlined">{{ row.icon }}</text></view>
          <view class="row-copy">
            <text class="row-label">{{ row.label }}</text>
            <text v-if="row.value" class="row-value">{{ row.value }}</text>
            <text v-if="row.caption" class="row-caption">{{ row.caption }}</text>
          </view>
          <text v-if="row.action" class="material-symbols-outlined row-chevron">
            {{ row.action === 'external' ? 'arrow_outward' : 'chevron_right' }}
          </text>
        </view>
      </view>

      <view v-if="type === 'wallet' && !isBoundAccount" class="context-note">
        <text class="material-symbols-outlined">info</text>
        <text>当前为访客体验模式，不展示或虚构校园卡余额、卡号等个人数据。</text>
      </view>

      <view v-if="type === 'about'" class="context-note">
        <text class="material-symbols-outlined">verified_user</text>
        <text>医小管根据公开材料提供校园事务参考，不构成学校官方解释。</text>
      </view>
      <view class="page-safe-space" />
    </scroll-view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { openAiQuestion, openExternal, openSsoExternal } from '@/composables/useServiceNavigation'

type DetailType = 'personal' | 'campus' | 'wallet' | 'help' | 'settings' | 'about'
type RowAction = 'external' | 'question'
interface DetailRow {
  label: string
  icon: string
  value?: string
  caption?: string
  action?: RowAction
  url?: string
  sso?: boolean
  question?: string
}

const userStore = useUserStore()
const type = ref<DetailType>('personal')
const reducedMotion = ref(uni.getStorageSync('yxg-reduced-motion') === '1')
const isBoundAccount = computed(() => !!userStore.userInfo?.staff_id && !userStore.userInfo.staff_id.startsWith('pilot:'))

const pageMap: Record<DetailType, { title: string; caption: string; icon: string }> = {
  personal: { title: '个人信息', caption: '查看当前账号与校园身份信息', icon: 'person' },
  campus: { title: '校园绑定', caption: '管理学校账号与常用身份服务', icon: 'account_balance' },
  wallet: { title: '我的卡包', caption: '集中访问校园卡与常用电子服务', icon: 'wallet' },
  help: { title: '帮助中心', caption: '常见问题与智能问答快捷入口', icon: 'help' },
  settings: { title: '设置', caption: '调整本机显示与临时数据', icon: 'settings' },
  about: { title: '关于医小管', caption: '校园事务导办与知识问答助手', icon: 'info' },
}
const page = computed(() => pageMap[type.value])

const rows = computed<DetailRow[]>(() => {
  const info = userStore.userInfo
  if (type.value === 'personal') return [
    { label: '姓名', value: isBoundAccount.value ? (info?.name || '未提供') : '体验用户', icon: 'badge' },
    { label: '账号', value: isBoundAccount.value ? (info?.staff_id || '未提供') : '访客体验账号', icon: 'id_card' },
    { label: '身份类型', value: isBoundAccount.value ? '在校生账号' : '未绑定校园账号', icon: 'verified_user' },
  ]
  if (type.value === 'campus') return [
    { label: '山东第一医科大学', value: isBoundAccount.value ? '校园账号已绑定' : '尚未绑定校园账号', icon: 'school' },
    { label: '信息门户', caption: '使用学校统一身份认证登录', icon: 'language', action: 'external', url: 'http://portal.sdfmu.edu.cn' },
    { label: '校园卡服务', caption: '校园卡办理、充值与挂失', icon: 'credit_card', action: 'external', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=443', sso: true },
  ]
  if (type.value === 'wallet') return [
    { label: '校园卡服务', caption: '办卡、充值、挂失与业务查询', icon: 'credit_card', action: 'external', url: 'https://ehall.sdfmu.edu.cn/v2/matter/detail?id=443', sso: true },
    { label: '黄河图书馆馆藏', caption: '检索馆藏与借阅资源', icon: 'local_library', action: 'external', url: 'http://opac.sdfmu.edu.cn:8080/opac/' },
    { label: '校园邮箱', caption: '进入学校邮箱', icon: 'mail', action: 'external', url: 'https://mail.sdfmu.edu.cn/' },
  ]
  if (type.value === 'help') return [
    { label: '医小管可以回答什么？', caption: '了解当前知识覆盖范围', icon: 'auto_awesome', action: 'question', question: '医小管目前可以准确回答哪些校园问题？' },
    { label: '如何查看历史回答？', caption: '继续以前的智能问答', icon: 'history', action: 'question', question: '如何查看和继续我的历史对话？' },
    { label: '答案来源是否可靠？', caption: '了解来源与核验规则', icon: 'fact_check', action: 'question', question: '医小管如何核验回答中的参考来源？' },
  ]
  return [
    { label: '医小管', value: 'AI Campus v2.0', icon: 'auto_awesome' },
    { label: '产品定位', value: '校园事务导办与知识问答', icon: 'school' },
    { label: '学校官网', caption: '访问山东第一医科大学官方网站', icon: 'language', action: 'external', url: 'https://www.sdfmu.edu.cn/' },
  ]
})

onLoad((query) => {
  const requested = String(query?.type || '') as DetailType
  if (requested in pageMap) type.value = requested
})

function goBack() { uni.navigateBack() }
function handleRow(row: DetailRow) {
  if (row.action === 'external' && row.url) row.sso ? openSsoExternal(row.url) : openExternal(row.url)
  if (row.action === 'question' && row.question) openAiQuestion(row.question)
}
function setReducedMotion(event: Event) {
  reducedMotion.value = Boolean((event as Event & { detail?: { value?: boolean } }).detail?.value)
  uni.setStorageSync('yxg-reduced-motion', reducedMotion.value ? '1' : '0')
  // #ifdef H5
  document.documentElement.classList.toggle('yxg-reduced-motion', reducedMotion.value)
  // #endif
}
function clearLocalState() {
  uni.showModal({
    title: '清理本机临时状态',
    content: '将清除未发送草稿和本机提示记录，不会删除服务器上的历史对话。',
    success: ({ confirm }) => {
      if (!confirm) return
      ['chat_init_query', 'pendingConversationId', 'dismissed_unanswered_msg_ids'].forEach(key => uni.removeStorageSync(key))
      uni.showToast({ title: '已清理', icon: 'success' })
    },
  })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.detail-page { min-height: 100dvh; width: min(100%, 430px); margin: 0 auto; color: $on-surface; background: radial-gradient(circle at 100% 0%, rgba(196,172,228,.32), transparent 34%), $surface; }
.detail-topbar { height: calc(env(safe-area-inset-top) + 62px); padding: env(safe-area-inset-top) 18px 0; display: flex; align-items: center; justify-content: space-between; box-sizing: border-box; background: rgba(250,245,251,.82); backdrop-filter: $backdrop-bar; -webkit-backdrop-filter: $backdrop-bar; }
.back-action, .topbar-space { width: 44px; height: 44px; }
.back-action { display: flex; align-items: center; justify-content: center; border-radius: 15px; color: $primary; transition: background .2s ease, transform .2s ease; }
.back-action--pressed, .back-action:active { background: rgba(91,43,143,.1); transform: scale(.95); }
.back-action .material-symbols-outlined { font-size: 22px; }
.topbar-title { font-size: 15px; font-weight: 800; }
.detail-scroll { height: calc(100dvh - env(safe-area-inset-top) - 62px); padding: 0 18px; box-sizing: border-box; }
.detail-hero { padding: 30px 4px 24px; }
.hero-icon { width: 52px; height: 52px; display: flex; align-items: center; justify-content: center; border-radius: 18px; color: #fff; background: linear-gradient(145deg, #7140a2, $primary 60%, #43216d); box-shadow: 0 12px 28px rgba(91,43,143,.18), inset 0 1px 0 rgba(255,255,255,.28); }
.hero-icon .material-symbols-outlined { font-size: 25px; }
.hero-title { display: block; margin-top: 18px; font-size: 28px; line-height: 1.15; font-weight: 850; letter-spacing: -.04em; }
.hero-caption { display: block; margin-top: 7px; color: $on-surface-variant; font-size: 12px; line-height: 1.55; }
.detail-card { overflow: hidden; border-radius: 23px; background: rgba(255,255,255,.82); box-shadow: inset 0 1px 0 #fff, 0 14px 36px rgba(91,43,143,.06); }
.detail-row { min-height: 72px; padding: 10px 15px; display: flex; align-items: center; gap: 12px; box-sizing: border-box; transition: background .2s ease, transform .2s ease; touch-action: manipulation; }
.detail-row + .detail-row { box-shadow: inset 0 1px 0 rgba(91,43,143,.07); }
.detail-row--pressed:not(.static-row), .detail-row:active:not(.static-row) { background: #f2e8f1; transform: scale(.988); }
.row-icon { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 14px; color: $primary; background: #f2e7f3; }
.row-icon .material-symbols-outlined { font-size: 20px; }
.row-copy { flex: 1; min-width: 0; }
.row-label, .row-value, .row-caption { display: block; }
.row-label { color: $on-surface; font-size: 13px; font-weight: 780; }
.row-value { margin-top: 3px; color: #705e73; font-size: 11px; line-height: 1.45; overflow-wrap: anywhere; }
.row-caption { margin-top: 3px; color: #887a8b; font-size: 10px; line-height: 1.45; }
.row-chevron { flex-shrink: 0; color: #9b8e9d; font-size: 20px; }
.context-note { margin-top: 16px; padding: 14px 15px; display: flex; align-items: flex-start; gap: 9px; border-radius: 18px; color: #716475; background: rgba(241,232,243,.76); font-size: 10px; line-height: 1.6; }
.context-note .material-symbols-outlined { flex-shrink: 0; color: $primary; font-size: 18px; }
.page-safe-space { height: calc(env(safe-area-inset-bottom) + 32px); }

@media (prefers-reduced-motion: reduce) {
  .back-action, .detail-row { transition: none; }
}
</style>
