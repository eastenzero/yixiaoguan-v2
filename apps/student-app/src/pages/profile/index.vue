<template>
  <view class="profile-page">
    <view class="identity-hero">
      <view class="profile-topbar">
        <text class="topbar-title">我的</text>
        <view class="glass-action" @click="showIdentityCode">
          <text class="material-symbols-outlined topbar-icon">qr_code_2</text>
        </view>
      </view>

      <view class="identity-main animate-fade-up delay-1">
        <view class="avatar-shell">
          <image class="avatar" :src="avatarSource" mode="aspectFill" />
          <view class="verified-badge">
            <text class="material-symbols-outlined verified-icon">verified</text>
          </view>
        </view>
        <view class="identity-copy">
          <text class="user-name">{{ displayName }}</text>
          <text class="user-meta">{{ studentMeta }}</text>
          <view class="status-chip"><text class="status-text">在校生 · 已认证</text></view>
        </view>
      </view>

      <view class="identity-stats animate-fade-up delay-2">
        <view class="identity-stat" @click="goChatHistory">
          <text class="stat-value">{{ conversationCount }}</text>
          <text class="stat-label">咨询记录</text>
        </view>
        <view class="stat-separator" />
        <view class="identity-stat" @click="goChatHistory">
          <text class="stat-value">{{ totalUnread }}</text>
          <text class="stat-label">未读消息</text>
        </view>
        <view class="stat-separator" />
        <view class="identity-stat" @click="goChat">
          <text class="stat-value">AI</text>
          <text class="stat-label">随时咨询</text>
        </view>
      </view>
    </view>

    <view class="profile-content">
      <view class="section-label animate-fade-up delay-3">校园身份</view>
      <view class="settings-card animate-fade-up delay-3">
        <view v-for="item in campusSettings" :key="item.label" class="settings-row" @click="handleSettingClick(item)">
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

      <view class="ai-entry animate-fade-up delay-4" @click="goChat">
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
        <view v-for="item in moreSettings" :key="item.label" class="settings-row" @click="handleSettingClick(item)">
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
    <FeatureNoticeSheet />
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
import { openAiQuestion, showComingSoon } from '@/composables/useServiceNavigation'
import CustomTabBar from '@/components/CustomTabBar.vue'
import FeatureNoticeSheet from '@/components/FeatureNoticeSheet.vue'
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
  action: 'comingSoon' | 'aiQuestion' | 'about' | 'feedback' | 'history'
  aiQuestion?: string
}

const campusSettings: SettingItem[] = [
  { label: '个人信息', caption: '姓名、学号与联系方式', icon: 'person', action: 'comingSoon' },
  { label: '校园绑定', caption: '山东第一医科大学', icon: 'account_balance', action: 'comingSoon' },
  { label: '我的卡包', caption: '校园卡与电子凭证', icon: 'wallet', action: 'comingSoon' },
]

const moreSettings: SettingItem[] = [
  { label: '我的消息', icon: 'notifications', action: 'history' },
  { label: '意见反馈', icon: 'rate_review', action: 'feedback' },
  { label: '帮助中心', icon: 'help', action: 'aiQuestion', aiQuestion: '医小管可以帮我做什么？' },
  { label: '设置', icon: 'settings', action: 'comingSoon' },
  { label: '关于医小管', icon: 'info', action: 'about' },
]

const displayName = computed(() => {
  const name = userStore.userInfo?.name
  const pilot = (userStore.userInfo?.staff_id || '').startsWith('pilot:')
  return name && !pilot ? name : '林小依'
})
const avatarSource = computed(() => userStore.userInfo?.avatar_url || '/static/images/lin-xiaoyi-avatar.jpg')
const studentMeta = computed(() => {
  const staffId = userStore.userInfo?.staff_id
  return staffId ? `山东第一医科大学 · ${staffId}` : '山东第一医科大学 · 本科生'
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

function showIdentityCode() { uni.showToast({ title: '校园身份码即将开放', icon: 'none' }) }
function goChatHistory() { uni.navigateTo({ url: '/pages/chat/history' }) }
function goChat() { uni.switchTab({ url: '/pages/chat/index' }) }

function handleSettingClick(item: SettingItem) {
  if (item.action === 'feedback') feedbackDrawerVisible.value = true
  else if (item.action === 'history') goChatHistory()
  else if (item.action === 'aiQuestion' && item.aiQuestion) openAiQuestion(item.aiQuestion)
  else if (item.action === 'about') {
    dialog.alert({
      title: '关于医小管',
      content: '医小管 v2.0\n山东第一医科大学智慧校园 AI 服务平台',
      icon: 'school',
      iconFill: true,
      confirmText: '知道了',
    })
  } else showComingSoon(item.label)
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
  background: #f4efe9;
  padding-bottom: calc(var(--tabbar-safe) + 28px);
}

.identity-hero {
  position: relative;
  overflow: hidden;
  padding: calc(env(safe-area-inset-top) + 12px) 20px 22px;
  color: #fff;
  background: #3e236d;
  border-radius: 0 0 30px 30px;
  box-shadow: 0 18px 44px rgba(91,18,91,.22);
}

.profile-topbar { display: flex; align-items: center; justify-content: space-between; }
.topbar-title { color: rgba(255,255,255,.86); font-size: 15px; font-weight: 800; letter-spacing: .08em; }
.glass-action { width: 40px; height: 40px; display: flex; align-items: center; justify-content: center; border-radius: 15px; background: rgba(255,255,255,.15); backdrop-filter: blur(18px); -webkit-backdrop-filter: blur(18px); box-shadow: inset 0 1px 0 rgba(255,255,255,.3); }
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

.identity-stats { margin-top: 22px; padding: 14px 8px; display: flex; align-items: center; border-radius: 20px; background: rgba(255,255,255,.12); backdrop-filter: blur(18px) saturate(150%); -webkit-backdrop-filter: blur(18px) saturate(150%); box-shadow: inset 0 1px 0 rgba(255,255,255,.22); }
.identity-stat { flex: 1; text-align: center; }
.stat-value { display: block; color: #fff; font-size: 17px; font-weight: 800; }
.stat-label { display: block; margin-top: 3px; color: rgba(255,255,255,.58); font-size: 8px; }
.stat-separator { width: 1px; height: 25px; background: rgba(255,255,255,.16); }

.profile-content { padding: 24px 18px 0; }
.section-label { margin: 0 4px 9px; color: #9d8f9e; font-size: 10px; font-weight: 750; letter-spacing: .08em; }
.settings-card { overflow: hidden; margin-bottom: 22px; border-radius: 23px; background: rgba(255,255,255,.78); box-shadow: inset 0 1px 0 #fff; }
.settings-row { min-height: 66px; padding: 0 15px; display: flex; align-items: center; justify-content: space-between; }
.settings-row + .settings-row { box-shadow: inset 0 1px 0 rgba(91,43,143,.06); }
.settings-row:active { background: #f2e8f1; }
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

.ai-entry { margin-bottom: 24px; padding: 17px; display: flex; align-items: center; gap: 12px; border-radius: 23px; color: #fff; background: #5b2b8f; box-shadow: 0 15px 34px rgba(91,43,143,.18), inset 0 1px 0 rgba(255,255,255,.2); }
.ai-entry-icon { width: 42px; height: 42px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; border-radius: 15px; background: rgba(255,255,255,.15); }
.ai-icon { color: #fff; font-size: 21px; font-variation-settings: 'FILL' 1; }
.ai-entry-copy { flex: 1; min-width: 0; }
.ai-entry-title { display: block; color: #fff; font-size: 13px; font-weight: 800; }
.ai-entry-caption { display: block; margin-top: 3px; color: rgba(255,255,255,.66); font-size: 9px; }
.ai-entry-arrow { color: #fff; font-size: 19px; }

.logout-btn { width: 100%; min-height: 52px; display: flex; align-items: center; justify-content: center; border-radius: 20px; background: #efe4eb; }
.logout-text { color: #a42950; font-size: 13px; font-weight: 800; }
.version-text { display: block; margin-top: 16px; text-align: center; color: #b3a7b3; font-size: 9px; letter-spacing: .06em; }
</style>
