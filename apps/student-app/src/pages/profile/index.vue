<template>
  <view class="profile-page">
    <view class="header-area">
      <view class="avatar-box">
        <text class="material-symbols-outlined avatar-icon">person</text>
      </view>
      <text class="user-name">{{ userStore.userInfo?.name || '未登录' }}</text>
      <text class="user-staff-id">{{ userStore.userInfo?.staff_id || '' }}</text>
    </view>

    <view class="info-section">
      <view class="info-card">
        <view class="info-row">
          <text class="info-label">姓名</text>
          <text class="info-value">{{ userStore.userInfo?.name || '-' }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">学号</text>
          <text class="info-value">{{ userStore.userInfo?.staff_id || '-' }}</text>
        </view>
        <view class="info-row">
          <text class="info-label">角色</text>
          <text class="info-value">{{ roleLabel }}</text>
        </view>
      </view>
    </view>

    <view class="action-section">
      <button class="logout-btn" @click="handleLogout">
        <text class="material-symbols-outlined logout-icon">logout</text>
        <text class="logout-text">退出登录</text>
      </button>
    </view>

    <CustomTabBar current="profile" />
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'
import CustomTabBar from '@/components/CustomTabBar.vue'

const userStore = useUserStore()

const roleLabel = computed(() => {
  const map: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' }
  return map[userStore.userInfo?.role || ''] || '学生'
})

function handleLogout() {
  uni.showModal({
    title: '提示',
    content: '确定退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        userStore.logout()
        uni.reLaunch({ url: '/pages/login/index' })
      }
    },
  })
}
</script>

<style scoped>
.profile-page { min-height: 100vh; background: #f8fafc; }

.header-area { display: flex; flex-direction: column; align-items: center; padding: calc(env(safe-area-inset-top) + 2rem) 1rem 2rem; background: linear-gradient(135deg, #630ed4, #8b5cf6); }
.avatar-box { width: 4.5rem; height: 4.5rem; border-radius: 2.25rem; background: rgba(255,255,255,0.2); display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; }
.avatar-icon { font-size: 2.5rem; color: #fff; }
.user-name { font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 0.25rem; }
.user-staff-id { font-size: 0.875rem; color: rgba(255,255,255,0.7); }

.info-section { padding: 1.25rem 1rem 0; }
.info-card { background: #fff; border-radius: 0.75rem; overflow: hidden; box-shadow: 0 0.125rem 0.5rem rgba(0,0,0,0.03); }
.info-row { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.25rem; border-bottom: 1px solid #f1f5f9; }
.info-row:last-child { border-bottom: none; }
.info-label { font-size: 0.875rem; color: #64748b; }
.info-value { font-size: 0.875rem; font-weight: 600; color: #0f172a; }

.action-section { padding: 2rem 1rem; }
.logout-btn { display: flex; align-items: center; justify-content: center; gap: 0.5rem; width: 100%; height: 3rem; background: #fff; border: 1px solid #fca5a5; border-radius: 0.75rem; }
.logout-btn:active { background: #fef2f2; }
.logout-icon { font-size: 1.25rem; color: #dc2626; }
.logout-text { font-size: 0.9375rem; font-weight: 600; color: #dc2626; }
</style>
