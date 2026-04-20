<template>
  <view class="dashboard-page">
    <!-- 自定义顶栏 -->
    <view class="custom-app-bar">
      <view class="app-bar-content">
        <view class="app-bar-left">
          <IconDashboard :size="24" :color="primaryColor" />
          <text class="app-bar-title">工作台</text>
        </view>
        <view class="app-bar-right" @click="handleNotification">
          <IconBell :size="24" :color="onSurfaceColor" />
          <view class="notification-dot"></view>
        </view>
      </view>
    </view>

    <!-- 主内容区域 -->
    <view class="main-content">
      <!-- 欢迎横幅 -->
      <view class="welcome-banner animate-fade-up">
        <view class="welcome-content">
          <view class="welcome-text">
            <text class="welcome-greeting">早上好，{{ displayName }} 👋</text>
            <text class="welcome-subtitle">今天有 {{ pendingCount }} 条待处理提问</text>
          </view>
          <view class="avatar-placeholder"></view>
        </view>
        <view class="welcome-decoration"></view>
      </view>

      <!-- 快捷操作 -->
      <view class="quick-actions animate-fade-up delay-1">
        <scroll-view scroll-x class="quick-actions-scroll" show-scrollbar="false">
          <view class="quick-actions-content">
            <view class="quick-action-btn" @click="handleQuickAction('knowledge')">
              <IconPlus :size="20" :color="primaryColor" />
              <text class="quick-action-text">新建知识</text>
            </view>
            <view class="quick-action-btn" @click="handleQuickAction('notice')">
              <IconMegaphone :size="20" :color="primaryColor" />
              <text class="quick-action-text">发布通知</text>
            </view>
            <view class="quick-action-btn" @click="handleQuickAction('report')">
              <IconChart :size="20" :color="primaryColor" />
              <text class="quick-action-text">数据报告</text>
            </view>
            <view class="quick-action-btn" @click="handleQuickAction('settings')">
              <IconSettings :size="20" :color="primaryColor" />
              <text class="quick-action-text">系统设置</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 统计网格 -->
      <view class="stats-grid animate-fade-up delay-2">
        <view class="stat-card stat-card-1">
          <view class="stat-header">
            <IconDashboard :size="24" :color="primaryColor" />
            <text class="stat-number">{{ stats.todayQuestions }}</text>
          </view>
          <text class="stat-label">今日提问</text>
        </view>
        <view class="stat-card stat-card-2">
          <view class="stat-header">
            <IconAlert :size="24" :color="errorColor" />
            <text class="stat-number">{{ pendingCount }}</text>
          </view>
          <text class="stat-label">待处理</text>
        </view>
        <view class="stat-card stat-card-3">
          <view class="stat-header">
            <IconBook :size="24" :color="emeraldColor" />
            <text class="stat-number">{{ stats.knowledgeCount }}</text>
          </view>
          <text class="stat-label">知识条目</text>
        </view>
        <view class="stat-card stat-card-4">
          <view class="stat-header">
            <IconCheck :size="24" :color="amberColor" />
            <text class="stat-number">{{ stats.todayApprovals }}</text>
          </view>
          <text class="stat-label">今日审批</text>
        </view>
      </view>

      <!-- 待处理提问列表 -->
      <view class="questions-section animate-fade-up delay-3">
        <view class="section-header">
          <text class="section-title">待处理提问</text>
          <text class="section-link" @click="viewAllQuestions">查看全部</text>
        </view>

        <!-- Loading State -->
        <view v-if="loading" class="loading-container">
          <text class="loading-text">加载中...</text>
        </view>

        <!-- Empty State -->
        <view v-else-if="pendingQuestions.length === 0" class="empty-container">
          <text class="empty-text">暂无待处理提问</text>
        </view>

        <view v-else class="question-list">
          <view
            v-for="(question, index) in pendingQuestions"
            :key="question.id"
            class="question-card"
            @click="viewQuestion(question.id)"
          >
            <view class="question-header">
              <view class="question-author">
                <text class="author-name">学生 #{{ question.student_id }}</text>
                <view class="department-tag">
                  <text class="department-text">{{ question.title || '对话' }}</text>
                </view>
              </view>
              <text class="question-time">{{ formatTime(question.updated_at) }}</text>
            </view>
            <text class="question-content">{{ question.title || '无标题' }}</text>
            <view class="question-footer">
              <view class="status-badge">
                <view class="status-dot" :class="question.status"></view>
                <text class="status-text" :class="question.status">{{ getStatusText(question.status) }}</text>
              </view>
              <IconArrowRight :size="16" :color="onSurfaceVariantColor" />
            </view>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部导航栏 -->
    <BottomNavBar :current="0" :badge="pendingCount > 99 ? 99 : pendingCount" />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import IconDashboard from '../../components/icons/IconDashboard.vue'
import IconBell from '../../components/icons/IconBell.vue'
import IconPlus from '../../components/icons/IconPlus.vue'
import IconMegaphone from '../../components/icons/IconMegaphone.vue'
import IconChart from '../../components/icons/IconChart.vue'
import IconSettings from '../../components/icons/IconSettings.vue'
import IconAlert from '../../components/icons/IconAlert.vue'
import IconBook from '../../components/icons/IconBook.vue'
import IconCheck from '../../components/icons/IconCheck.vue'
import IconArrowRight from '../../components/icons/IconArrowRight.vue'
import BottomNavBar from '../../components/BottomNavBar.vue'
import { listConversations } from '@/api/conversations'
import { getStatusText } from '@/utils/status-map'

// 用户状态
const userStore = useUserStore()
const displayName = computed(() => userStore.displayName)

// 主题色
const primaryColor = '#702ae1'
const onSurfaceColor = '#2f2e32'
const onSurfaceVariantColor = '#5d5b5f'
const errorColor = '#b41340'
const emeraldColor = '#059669'
const amberColor = '#d97706'

// 统计数据
const stats = ref({
  todayQuestions: 0,
  knowledgeCount: 0,
  todayApprovals: 0
})

// 待处理提问列表
const pendingQuestions = ref<any[]>([])
const loading = ref(false)
const pendingCount = computed(() => pendingQuestions.value.length)

// 格式化时间
const formatTime = (timeStr: string) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  if (diff < 3600000) {
    const minutes = Math.floor(diff / 60000)
    return minutes < 1 ? '刚刚' : `${minutes}分钟前`
  }
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)}小时前`
  }
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)}天前`
  }
  return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

// 加载待处理提问 (v2: pending_teacher 状态的会话)
const loadPendingQuestions = async () => {
  loading.value = true
  try {
    const res = await listConversations(1, 5, 'pending_teacher')
    pendingQuestions.value = res.items || []
  } catch (e) {
    console.error('加载待处理提问失败', e)
  } finally {
    loading.value = false
  }
}

// 通知点击
const handleNotification = () => {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

// 快捷操作
const handleQuickAction = (type: string) => {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}

// 查看全部提问
const viewAllQuestions = () => {
  uni.switchTab({ url: '/pages/questions/index' })
}

// 查看单个提问
const viewQuestion = (id: number) => {
  uni.navigateTo({ url: `/pages/questions/detail?id=${id}` })
}

// 加载统计数据（v2: 从会话列表统计）
const loadStats = async () => {
  try {
    const allRes = await listConversations(1, 1)
    stats.value.todayQuestions = allRes.total || 0
  } catch (e) {
    console.error('加载统计数据失败', e)
  }
}

onMounted(() => {
  loadStats()
  loadPendingQuestions()
})

onShow(() => {
  loadStats()
  loadPendingQuestions()
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
  background: $surface;
  padding-bottom: calc(80px + env(safe-area-inset-bottom));
}

// 自定义顶栏
.custom-app-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  height: 56px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
}

.app-bar-content {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
}

.app-bar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-bar-title {
  font-family: $font-headline;
  font-size: 20px;
  font-weight: 700;
  color: $on-surface;
}

.app-bar-right {
  position: relative;
  padding: 8px;
  
  &:active {
    transform: scale(0.9);
  }
}

.notification-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  background: $error;
  border-radius: 50%;
  border: 2px solid white;
}

// 主内容区域
.main-content {
  position: relative;
  z-index: 1;
  padding-top: 72px;
  padding-left: 20px;
  padding-right: 20px;
}

// 欢迎横幅
.welcome-banner {
  position: relative;
  overflow: hidden;
  background: $gradient-hero;
  border-radius: 24px;
  padding: 24px;
  box-shadow: $elevation-3;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 10;
}

.welcome-text {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.welcome-greeting {
  font-family: $font-headline;
  font-size: 20px;
  font-weight: 700;
  color: $on-primary;
}

.welcome-subtitle {
  font-family: $font-body;
  font-size: 14px;
  font-weight: 400;
  color: rgba($on-primary, 0.8);
}

.avatar-placeholder {
  width: 64px;
  height: 64px;
  background: $surface-container-high;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.welcome-decoration {
  position: absolute;
  right: -16px;
  bottom: -16px;
  width: 128px;
  height: 128px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 50%;
  filter: blur(30px);
}

// 快捷操作
.quick-actions {
  margin-top: 32px;
}

.quick-actions-scroll {
  white-space: nowrap;
}

.quick-actions-content {
  display: inline-flex;
  gap: 12px;
  padding-bottom: 8px;
}

.quick-action-btn {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  gap: 8px;
  background: $surface-container-low;
  padding: 12px 16px;
  border-radius: 9999px;
  
  &:active {
    background: $surface-container;
    transform: scale(0.95);
  }
}

.quick-action-text {
  font-family: $font-body;
  font-size: 12px;
  font-weight: 700;
  color: $on-surface;
  white-space: nowrap;
}

// 统计网格
.stats-grid {
  margin-top: 32px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-card {
  padding: 16px;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-shadow: $elevation-1;
}

.stat-card-1 {
  background: rgba($secondary-container, 0.3);
}

.stat-card-2 {
  background: rgba($error-container, 0.1);
}

.stat-card-3 {
  background: #e2f5ec;
}

.stat-card-4 {
  background: #fef3c7;
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stat-number {
  font-family: $font-headline;
  font-size: 24px;
  font-weight: 900;
  color: $on-surface;
}

.stat-label {
  font-family: $font-body;
  font-size: 12px;
  font-weight: 500;
  color: $on-surface-variant;
}

// 待处理提问
.questions-section {
  margin-top: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  padding: 0 4px;
  margin-bottom: 16px;
}

.section-title {
  font-family: $font-headline;
  font-size: 20px;
  font-weight: 700;
  color: $on-surface;
}

.section-link {
  font-family: $font-body;
  font-size: 12px;
  font-weight: 700;
  color: $primary;
}

// Loading & Empty State
.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  background: $surface-container-low;
  border-radius: 16px;
}

.loading-text,
.empty-text {
  font-family: $font-body;
  font-size: 14px;
  color: $on-surface-variant;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.question-card {
  background: $surface-container-low;
  border-radius: 16px;
  padding: 16px;
  box-shadow: $elevation-1;
  
  &:active {
    background: $surface-container;
    box-shadow: $elevation-2;
  }
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 8px;
}

.question-author {
  display: flex;
  align-items: center;
  gap: 8px;
}

.author-name {
  font-family: $font-body;
  font-size: 14px;
  font-weight: 700;
  color: $on-surface;
}

.department-tag {
  background: $surface-container-highest;
  padding: 2px 8px;
  border-radius: 9999px;
}

.department-text {
  font-family: $font-body;
  font-size: 10px;
  color: $on-surface-variant;
}

.question-time {
  font-family: $font-body;
  font-size: 11px;
  color: $on-surface-variant;
}

.question-content {
  font-family: $font-body;
  font-size: 14px;
  color: rgba($on-surface, 0.8);
  margin-bottom: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: block;
}

.question-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-0 {
  background: $error;
}

.status-1 {
  background: #f59e0b;
}

.status-2 {
  background: #10b981;
}

.status-3 {
  background: $on-surface-variant;
}

.status-text {
  font-family: $font-body;
  font-size: 11px;
  font-weight: 700;
}

.status-text-0 {
  color: $error;
}

.status-text-1 {
  color: #d97706;
}

.status-text-2 {
  color: #10b981;
}

.status-text-3 {
  color: $on-surface-variant;
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
  animation-delay: 0.15s;
}

.delay-3 {
  animation-delay: 0.2s;
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
