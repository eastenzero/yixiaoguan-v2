<template>
  <view class="profile-page">
    <TopAppBar title="我的" :showBack="true" action="settings" />

    <view class="main-content">
      <!-- Profile Header - 个人信息卡 -->
      <view class="hero-card animate-fade-up delay-1">
        <view class="hero-bg">
          <!-- 装饰光晕 -->
          <view class="glow glow-1"></view>
          <view class="glow glow-2"></view>
          
          <view class="profile-content">
            <!-- 头像占位 -->
            <view class="avatar-wrapper">
              <view class="avatar-placeholder"></view>
            </view>
            
            <!-- 姓名 -->
            <text class="user-name">{{ userName }}</text>
            
            <!-- 职称/院系 -->
            <text class="user-title">高级讲师 / {{ department }}</text>
            
            <!-- 工号标签 -->
            <view class="id-badge">
              <text class="id-text">ID: {{ userId }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- Stats Grid - 统计网格 -->
      <view class="stats-grid animate-fade-up delay-2">
        <view class="stat-item">
          <text class="stat-value">156</text>
          <text class="stat-label">累计处理</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">42</text>
          <text class="stat-label">本月审批</text>
        </view>
        <view class="stat-item">
          <text class="stat-value">28</text>
          <text class="stat-label">知识入库</text>
        </view>
      </view>

      <!-- Settings List - 系统设置列表 -->
      <view class="settings-section animate-fade-up delay-3">
        <text class="section-title">系统设置</text>
        
        <!-- 第一组：开关项 -->
        <view class="settings-group">
          <!-- 通知提醒 -->
          <view class="setting-item">
            <view class="item-left">
              <view class="icon-circle">
                <text class="material-symbols-outlined setting-icon">notifications</text>
              </view>
              <text class="item-label">通知提醒</text>
            </view>
            <view 
              class="toggle-switch"
              :class="{ 'toggle-switch--on': notificationOn }"
              @click="notificationOn = !notificationOn"
            >
              <view class="toggle-dot"></view>
            </view>
          </view>
          
          <!-- 声音提示 -->
          <view class="setting-item">
            <view class="item-left">
              <view class="icon-circle">
                <text class="material-symbols-outlined setting-icon">volume_up</text>
              </view>
              <text class="item-label">声音提示</text>
            </view>
            <view 
              class="toggle-switch"
              :class="{ 'toggle-switch--on': soundOn }"
              @click="soundOn = !soundOn"
            >
              <view class="toggle-dot"></view>
            </view>
          </view>
          
          <!-- AI 自动回复 -->
          <view class="setting-item">
            <view class="item-left">
              <view class="icon-circle">
                <text class="material-symbols-outlined setting-icon">smart_toy</text>
              </view>
              <text class="item-label">AI 自动回复</text>
            </view>
            <view 
              class="toggle-switch"
              :class="{ 'toggle-switch--on': aiReplyOn }"
              @click="aiReplyOn = !aiReplyOn"
            >
              <view class="toggle-dot"></view>
            </view>
          </view>
        </view>

        <!-- 第二组：导航项 -->
        <view class="settings-group">
          <!-- 修改密码 -->
          <view class="setting-item setting-item--nav">
            <view class="item-left">
              <view class="icon-circle">
                <text class="material-symbols-outlined setting-icon">lock</text>
              </view>
              <text class="item-label">修改密码</text>
            </view>
            <text class="material-symbols-outlined nav-chevron">chevron_right</text>
          </view>
          
          <!-- 关于我们 -->
          <view class="setting-item setting-item--nav">
            <view class="item-left">
              <view class="icon-circle">
                <text class="material-symbols-outlined setting-icon">info</text>
              </view>
              <text class="item-label">关于我们</text>
            </view>
            <text class="material-symbols-outlined nav-chevron">chevron_right</text>
          </view>
        </view>

        <!-- 退出登录按钮 -->
        <view class="logout-btn" @click="handleLogout">
          <text class="material-symbols-outlined logout-icon">logout</text>
          <text class="logout-text">退出登录</text>
        </view>
      </view>
    </view>

    <BottomNavBar :current="3" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import TopAppBar from '../../components/TopAppBar.vue'
import BottomNavBar from '../../components/BottomNavBar.vue'

// 用户状态
const userStore = useUserStore()

// 计算用户信息
const userName = computed(() => userStore.userInfo?.name || '教师')
const department = computed(() => {
  const collegeId = userStore.userInfo?.college_id
  return collegeId ? `学院 ${collegeId}` : '未知院系'
})
const userId = computed(() => userStore.userInfo?.staff_id || 'N/A')

// 开关状态
const notificationOn = ref(true)
const soundOn = ref(true)
const aiReplyOn = ref(false)

// 退出登录
const handleLogout = () => {
  userStore.clearAuth()
  uni.reLaunch({ url: '/pages/login/index' })
}
</script>

<style lang="scss" scoped>
.profile-page {
  min-height: 100vh;
  background: $background;
  padding-bottom: calc(var(--tabbar-safe) + $space-6);  /* tab bar + 24px */
}

.main-content {
  position: relative;
  z-index: 1;
  padding-top: 72px;
  padding-left: 20px;
  padding-right: 20px;
}

// 个人信息卡
.hero-card {
  margin-bottom: 24px;
}

.material-symbols-outlined {
  font-family: 'Material Symbols Outlined';
  font-weight: normal;
  font-style: normal;
  line-height: 1;
  letter-spacing: normal;
  text-transform: none;
  display: inline-flex;
  white-space: nowrap;
  word-wrap: normal;
  direction: ltr;
  -webkit-font-feature-settings: 'liga';
  -webkit-font-smoothing: antialiased;
  font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}

.hero-bg {
  position: relative;
  overflow: hidden;
  border-radius: $radius-lg;                  // 2rem MD3 大半径
  padding: 32px;
  background: $gradient-hero;
  box-shadow: $shadow-fab;                    // hero 允许紫色折射阐级氛围
}

// 装饰光晕
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
}

.glow-1 {
  width: 160px;
  height: 160px;
  background: rgba(255, 255, 255, 0.1);
  top: -40px;
  right: -40px;
}

.glow-2 {
  width: 192px;
  height: 192px;
  background: rgba(46, 0, 108, 0.1);
  bottom: -40px;
  left: -40px;
}

.profile-content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

// 头像
.avatar-wrapper {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  border: 4px solid rgba(255, 255, 255, 0.2);
  padding: 4px;
  margin-bottom: 16px;
}

.avatar-placeholder {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: $surface-container-highest;
}

// 姓名
.user-name {
  font-size: 24px;
  font-weight: 700;
  color: $on-primary;
  margin-bottom: 4px;
}

// 职称
.user-title {
  font-size: 14px;
  color: rgba(248, 240, 255, 0.9);
  font-weight: 500;
  margin-bottom: 12px;
}

// 工号标签
.id-badge {
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(10px);
  border-radius: 9999px;
}

.id-text {
  font-size: 10px;
  color: $on-primary;
  letter-spacing: 0.1em;
  font-weight: 700;
}

// 统计网格
.stats-grid {
  display: flex;
  gap: 12px;
  margin-bottom: 32px;
}

.stat-item {
  flex: 1;
  background: $surface-container-low;
  border-radius: 16px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: $elevation-1;                    // [CA957F5] 双层紫折射, 提升"悬浮卡片"观感
}

.stat-value {
  font-size: 20px;
  font-weight: 800;
  color: $primary;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 10px;
  color: $on-surface-variant;
  font-weight: 500;
}

// 设置区域
.settings-section {
  margin-bottom: 24px;
}

.section-title {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: $on-surface-variant;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 12px;
  padding-left: 8px;
}

// 设置组
.settings-group {
  background: $surface-container-low;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 16px;
}

// 设置项
.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
}

.setting-item + .setting-item {
  border-top: 1px solid rgba($outline-variant, 0.08);
}

.item-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.icon-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: $surface-container-lowest;
  display: flex;
  align-items: center;
  justify-content: center;
}

.setting-icon {
  font-size: 20px;
  color: $primary;
}

.nav-chevron {
  font-size: 20px;
  color: $on-surface-variant;
}

.item-label {
  font-size: 14px;
  font-weight: 500;
  color: $on-surface;
}

// 模拟开关
.toggle-switch {
  width: 48px;
  height: 24px;
  background: $surface-container-highest;
  border-radius: 9999px;
  padding: 4px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  transition: background 0.2s ease;
}

.toggle-switch--on {
  background: $primary;
  justify-content: flex-end;
}

.toggle-dot {
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

// 退出登录按钮
.logout-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba($error-container, 0.1);
  border-radius: 16px;
  padding: 20px;
  margin-top: 8px;
}

.logout-text {
  font-size: 16px;
  font-weight: 700;
  color: $error;
}

.logout-icon {
  font-size: 20px;
  color: $error;
}

// 动画
.animate-fade-up {
  opacity: 0;
  animation: fadeUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

.delay-1 {
  animation-delay: 0.1s;
}

.delay-2 {
  animation-delay: 0.2s;
}

.delay-3 {
  animation-delay: 0.3s;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
