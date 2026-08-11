<template>
  <view class="profile-page">
    <view class="identity-hero">
      <view class="profile-topbar">
        <text class="topbar-title">我的</text>
        <view class="glass-action" hover-class="glass-action--pressed" :hover-start-time="0" :hover-stay-time="80" @click="showIdentityCode">
          <text class="material-symbols-outlined topbar-icon">qr_code_2</text>
        </view>
      </view>

      <view class="identity-main animate-fade-up delay-1">
        <view class="avatar-shell">
          <image class="avatar" :src="avatarSource" mode="aspectFill" />
          <view v-if="isBoundAccount" class="verified-badge">
            <text class="material-symbols-outlined verified-icon">verified</text>
          </view>
        </view>
        <view class="identity-copy">
          <text class="user-name">{{ displayName }}</text>
          <text class="user-meta">{{ studentMeta }}</text>
          <view class="status-chip"><text class="status-text">{{ identityStatus }}</text></view>
        </view>
      </view>

      <view class="identity-stats animate-fade-up delay-2">
        <view class="identity-stat" hover-class="identity-stat--pressed" :hover-start-time="0" :hover-stay-time="80" @click="goChatHistory">
          <text class="stat-value">{{ conversationCount }}</text>
          <text class="stat-label">咨询记录</text>
        </view>
        <view class="stat-separator" />
        <view class="identity-stat" hover-class="identity-stat--pressed" :hover-start-time="0" :hover-stay-time="80" @click="goChatHistory">
          <text class="stat-value">{{ totalUnread }}</text>
          <text class="stat-label">未读消息</text>
        </view>
        <view class="stat-separator" />
        <view class="identity-stat" hover-class="identity-stat--pressed" :hover-start-time="0" :hover-stay-time="80" @click="goChat">
          <text class="stat-value">AI</text>
          <text class="stat-label">随时咨询</text>
        </view>
      </view>
    </view>

    <view class="profile-content">
      <view class="section-label animate-fade-up delay-3">校园身份</view>
      <view class="settings-card animate-fade-up delay-3">
        <view v-for="item in campusSettings" :key="item.label" class="settings-row" hover-class="settings-row--pressed" :hover-start-time="0" :hover-stay-time="70" @click="handleSettingClick(item)">
          <view class="settings-left">
            <view class="settings-icon-wrap">
              <text class="material-symbols-outlined settings-icon">{{ item.icon }}</text>
            </view>
            <view class="settings-copy">
              <text class="settings-label">{{ item.label }}</text>
              <text class="settings-caption">{{ item.caption }}</text>
            </view>
          </view>
          <text class="material-symbols-outlined chevron-icon">chevron_right</text>
        </view>
      </view>

      <view class="ai-entry animate-fade-up delay-4" hover-class="ai-entry--pressed" :hover-start-time="0" :hover-stay-time="90" @click="goChat">
        <view class="ai-entry-icon">
          <text class="material-symbols-outlined ai-icon">auto_awesome</text>
        </view>
        <view class="ai-entry-copy">
          <text class="ai-entry-title">问问 AI 小管</text>
          <text class="ai-entry-caption">校园事务与政策，一句话就能开始</text>
        </view>
        <text class="material-symbols-outlined ai-entry-arrow">arrow_forward</text>
      </view>

      <view class="section-label animate-fade-up delay-5">更多</view>
      <view class="settings-card animate-fade-up delay-5">
        <view v-for="item in moreSettings" :key="item.label" class="settings-row" hover-class="settings-row--pressed" :hover-start-time="0" :hover-stay-time="70" @click="handleSettingClick(item)">
          <view class="settings-left">
            <view class="settings-icon-wrap subtle">
              <text class="material-symbols-outlined settings-icon">{{ item.icon }}</text>
            </view>
            <text class="settings-label">{{ item.label }}</text>
          </view>
          <view class="settings-end">
            <view v-if="item.icon === 'notifications' && totalUnread" class="message-badge">
              <text class="message-count">{{ totalUnread }}</text>
            </view>
            <text class="material-symbols-outlined chevron-icon">chevron_right</text>
          </view>
        </view>
      </view>

      <button class="logout-btn animate-fade-up delay-6" @click="handleLogout">
        <text class="logout-text">退出登录</text>
      </button>
      <text class="version-text">医小管 · AI Campus v2.0</text>
    </view>

    <CustomTabBar current="profile" />
    <AppDialog />
    <FeedbackDrawer v-model:visible="feedbackDrawerVisible" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import { listConversations } from '@/api/chat'
import { getUnreadSummary } from '@/api/notification'
import { openAiQuestion } from '@/composables/useServiceNavigation'
import CustomTabBar from '@/components/CustomTabBar.vue'
import AppDialog from '@/components/AppDialog.vue'
import FeedbackDrawer from '@/components/FeedbackDrawer.vue'
import { useDialog } from '@/composables/useDialog'
import { trackEvent } from '@/utils/track'

const userStore = useUserStore()
const dialog = useDialog()
const conversationCount = ref(0)
const totalUnread = ref(0)
const feedbackDrawerVisible = ref(false)

interface SettingItem {
  label: string
  caption?: string
  icon: string
  action: 'detail' | 'aiQuestion' | 'feedback' | 'history'
  detail?: 'personal' | 'campus' | 'wallet' | 'help' | 'settings' | 'about'
  aiQuestion?: string
}

const campusSettings: SettingItem[] = [
  { label: '个人信息', caption: '账号与身份信息', icon: 'person', action: 'detail', detail: 'personal' },
  { label: '校园绑定', caption: '学校账号与校园服务', icon: 'account_balance', action: 'detail', detail: 'campus' },
  { label: '我的卡包', caption: '校园卡与常用凭证入口', icon: 'wallet', action: 'detail', detail: 'wallet' },
]

const moreSettings: SettingItem[] = [
  { label: '我的消息', icon: 'notifications', action: 'history' },
  { label: '意见反馈', icon: 'rate_review', action: 'feedback' },
  { label: '帮助中心', icon: 'help', action: 'detail', detail: 'help' },
  { label: '设置', icon: 'settings', action: 'detail', detail: 'settings' },
  { label: '关于医小管', icon: 'info', action: 'detail', detail: 'about' },
]

const isBoundAccount = computed(() => !!userStore.userInfo?.staff_id && !userStore.userInfo.staff_id.startsWith('pilot:'))
const identityStatus = computed(() => isBoundAccount.value ? '在校生 · 已认证' : '访客体验 · 未绑定校园账号')
const displayName = computed(() => {
  const name = userStore.userInfo?.name
  return name && isBoundAccount.value ? name : '医小管体验用户'
})
const avatarSource = computed(() => userStore.userInfo?.avatar_url || '/static/images/lin-xiaoyi-avatar.jpg')
const studentMeta = computed(() => {
  const staffId = userStore.userInfo?.staff_id
  return isBoundAccount.value && staffId ? `山东第一医科大学 · ${staffId}` : '山东第一医科大学 · 访客体验'
})

onShow(async () => {
  trackEvent('page_view', { path: '/pages/profile/index' })
  try {
    const res = await listConversations(1, 1)
    conversationCount.value = res.total || 0
  } catch { conversationCount.value = 0 }
  try {
    const unread = await getUnreadSummary()
    totalUnread.value = unread.total_unread || 0
  } catch { totalUnread.value = 0 }
})

function showIdentityCode() { openDetail('campus') }
function goChatHistory() { uni.navigateTo({ url: '/pages/chat/history' }) }
function goChat() { uni.switchTab({ url: '/pages/chat/index' }) }
function openDetail(detail: NonNullable<SettingItem['detail']>) {
  uni.navigateTo({ url: `/pages/profile/detail?type=${detail}` })
}

function handleSettingClick(item: SettingItem) {
  if (item.action === 'feedback') feedbackDrawerVisible.value = true
  else if (item.action === 'history') goChatHistory()
  else if (item.action === 'aiQuestion' && item.aiQuestion) openAiQuestion(item.aiQuestion)
  else if (item.action === 'detail' && item.detail) openDetail(item.detail)
}

async function handleLogout() {
  const confirmed = await dialog.confirm({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    icon: 'logout',
    confirmText: '退出',
    cancelText: '取消',
    confirmDanger: true,
  })
  if (confirmed) {
    userStore.logout()
    uni.reLaunch({ url: '/pages/login/index' })
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.profile-page {
  min-height: 100dvh;
  width: min(100%, 390px);
  margin: 0 auto;
  color: #322b33;
  background: var(--yxg-canvas);
  padding-bottom: calc(var(--tabbar-safe) + 28px);
}

.identity-hero {
  position: relative;
  overflow: hidden;
  padding: calc(env(safe-area-inset-top) + 12px) 20px 22px;
  color: #fff;
  background: linear-gradient(145deg, #66369a 0%, var(--yxg-violet) 48%, #45206d 100%);
  border-radius: 0 0 30px 30px;
  box-shadow: 0 18px 44px rgba(91,18,91,.22);
}

.profile-topbar { display: flex; align-items: center; justify-content: space-between; }
.topbar-title { color: rgba(255,255,255,.86); font-size: 15px; font-weight: 800; letter-spacing: .08em; }
.glass-action { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,.24); border-radius: 15px; background: linear-gradient(145deg, rgba(255,255,255,.22), rgba(255,255,255,.09)); backdrop-filter: blur(20px) saturate(160%); -webkit-backdrop-filter: blur(20px) saturate(160%); box-shadow: inset 0 1px 0 rgba(255,255,255,.36), 0 8px 18px rgba(33,10,55,.12); transform: translateZ(0); transition: transform var(--yxg-touch-out) var(--yxg-spring-out), box-shadow var(--yxg-touch-out) var(--yxg-spring-out); }
.glass-action:active, .glass-action--pressed { transform: translateY(1px) scale(.94); transition-duration: var(--yxg-touch-in); box-shadow: inset 0 3px 9px rgba(34,11,55,.2), 0 3px 8px rgba(33,10,55,.10); }
.topbar-icon { color: #fff; font-size: 22px; }

.identity-main { display: flex; align-items: center; gap: 16px; margin-top: 22px; }
.avatar-shell { position: relative; width: 76px; height: 76px; flex-shrink: 0; }
.avatar { width: 76px; height: 76px; border-radius: 25px; box-shadow: 0 10px 28px rgba(39,4,43,.28), 0 0 0 3px rgba(255,255,255,.25); }
.verified-badge { position: absolute; right: -4px; bottom: -4px; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; border-radius: 50%; background: #fff; box-shadow: 0 4px 12px rgba(39,4,43,.20); }
.verified-icon { color: #5b2b8f; font-size: 16px; font-variation-settings: 'FILL' 1; }
.identity-copy { flex: 1; min-width: 0; }
.user-name { display: block; color: #fff; font-size: 25px; line-height: 1.2; font-weight: 800; letter-spacing: -.03em; }
.user-meta { display: block; margin-top: 5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: rgba(255,255,255,.68); font-size: 10px; }
.status-chip { display: inline-flex; margin-top: 10px; padding: 5px 10px; border-radius: 999px; background: rgba(255,255,255,.16); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); }
.status-text { color: rgba(255,255,255,.90); font-size: 9px; font-weight: 750; }

.identity-stats { position: relative; overflow: hidden; margin-top: 22px; padding: 14px 8px; display: flex; align-items: center; border: 1px solid rgba(255,255,255,.18); border-radius: 20px; background: linear-gradient(145deg, rgba(255,255,255,.18), rgba(255,255,255,.08)); backdrop-filter: blur(22px) saturate(155%); -webkit-backdrop-filter: blur(22px) saturate(155%); box-shadow: inset 0 1px 0 rgba(255,255,255,.28), inset 0 -1px 0 rgba(44,15,70,.10); }
.identity-stats::before { content: ''; position: absolute; inset: -60% auto -60% -35%; width: 32%; pointer-events: none; filter: blur(9px); transform: skewX(-18deg); background: linear-gradient(90deg, transparent, rgba(255,255,255,.34), transparent); animation: identityMirrorSweep 11.6s cubic-bezier(.3,.02,.2,1) infinite; }
.identity-stat { position: relative; z-index: 1; flex: 1; padding: 5px 0; border-radius: 14px; text-align: center; transform: translateZ(0); transition: transform var(--yxg-touch-out) var(--yxg-spring-out), background .24s ease; }
.identity-stat:active, .identity-stat--pressed { transform: scale(.95); transition-duration: var(--yxg-touch-in); background: rgba(255,255,255,.1); }
.stat-value { display: block; color: #fff; font-size: 17px; font-weight: 800; }
.stat-label { display: block; margin-top: 3px; color: rgba(255,255,255,.58); font-size: 8px; }
.stat-separator { width: 1px; height: 25px; background: rgba(255,255,255,.16); }

.profile-content { padding: 24px 18px 0; }
.section-label { margin: 0 4px 9px; color: #9d8f9e; font-size: 10px; font-weight: 750; letter-spacing: .08em; }
.settings-card { overflow: hidden; margin-bottom: 22px; border-radius: 23px; background: rgba(255,255,255,.78); box-shadow: inset 0 1px 0 #fff; }
.settings-row { min-height: 66px; padding: 0 15px; display: flex; align-items: center; justify-content: space-between; transform: translateZ(0); transition: transform var(--yxg-touch-out) var(--yxg-spring-out), background .24s ease; }
.settings-row + .settings-row { box-shadow: inset 0 1px 0 rgba(91,43,143,.06); }
.settings-row:active, .settings-row--pressed { transform: scale(.985); transition-duration: var(--yxg-touch-in); background: #f2e8f1; }
.settings-left, .settings-end { display: flex; align-items: center; gap: 11px; }
.settings-icon-wrap { width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 14px; background: #f2dcef; }
.settings-icon-wrap.subtle { background: #f1eaef; }
.settings-icon { color: #5b2b8f; font-size: 20px; }
.settings-copy { min-width: 0; }
.settings-label { display: block; color: #3a323b; font-size: 13px; font-weight: 750; }
.settings-caption { display: block; margin-top: 3px; color: #a095a1; font-size: 9px; }
.chevron-icon { color: #b9adb9; font-size: 20px; }
.message-badge { min-width: 20px; height: 20px; padding: 0 6px; display: flex; align-items: center; justify-content: center; border-radius: 999px; background: #5b2b8f; }
.message-count { color: #fff; font-size: 9px; font-weight: 800; }

.ai-entry { position: relative; overflow: hidden; margin-bottom: 24px; padding: 17px; display: flex; align-items: center; gap: 12px; border: 1px solid rgba(255,255,255,.22); border-radius: 23px; color: #fff; background: linear-gradient(145deg, #7140a2, var(--yxg-violet) 56%, #482170); box-shadow: 0 15px 34px rgba(91,43,143,.18), inset 0 1px 0 rgba(255,255,255,.24); transform: translateZ(0); transition: transform var(--yxg-touch-out) var(--yxg-spring-out), box-shadow var(--yxg-touch-out) var(--yxg-spring-out), filter .24s ease; }
.ai-entry::before { content: ''; position: absolute; inset: -55% auto -55% -32%; width: 30%; pointer-events: none; filter: blur(8px); transform: skewX(-18deg); background: linear-gradient(90deg, transparent, rgba(255,255,255,.34), transparent); animation: aiEntryMirrorSweep 9.6s cubic-bezier(.3,.02,.2,1) infinite; }
.ai-entry > * { position: relative; z-index: 1; }
.ai-entry:active, .ai-entry--pressed { transform: translateY(1px) scale(.975); transition-duration: var(--yxg-touch-in); box-shadow: inset 0 4px 12px rgba(36,12,59,.22), 0 6px 16px rgba(91,43,143,.12); filter: saturate(1.05); }
.ai-entry-icon { width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 15px; background: rgba(255,255,255,.15); }
.ai-icon { color: #fff; font-size: 21px; font-variation-settings: 'FILL' 1; }
.ai-entry-copy { flex: 1; min-width: 0; }
.ai-entry-title { display: block; color: #fff; font-size: 13px; font-weight: 800; }
.ai-entry-caption { display: block; margin-top: 3px; color: rgba(255,255,255,.66); font-size: 9px; }
.ai-entry-arrow { color: #fff; font-size: 19px; }

.logout-btn { width: 100%; min-height: 52px; display: flex; align-items: center; justify-content: center; border-radius: 20px; background: #efe4eb; }
.logout-text { color: #a42950; font-size: 13px; font-weight: 800; }
.version-text { display: block; margin-top: 16px; text-align: center; color: #b3a7b3; font-size: 9px; letter-spacing: .06em; }

@keyframes identityMirrorSweep {
  0%, 54% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  61% { opacity: .72; }
  76% { opacity: 0; transform: translateX(430%) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(430%) skewX(-18deg); }
}
@keyframes aiEntryMirrorSweep {
  0%, 43% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  50% { opacity: .8; }
  68% { opacity: 0; transform: translateX(520%) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(520%) skewX(-18deg); }
}

@media (prefers-reduced-motion: reduce) {
  .identity-stats::before,
  .ai-entry::before { animation: none; }
}
</style>
