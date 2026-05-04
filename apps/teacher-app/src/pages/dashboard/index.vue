<template>
  <view class="dashboard-page">
    <!-- 自定义顶栏 -->
    <view class="custom-app-bar">
      <view class="app-bar-content">
        <view class="app-bar-left">
          <text class="material-symbols-outlined app-bar-icon app-bar-icon--primary">dashboard</text>
          <text class="app-bar-title">工作台</text>
        </view>
        <view class="app-bar-right" @click="handleNotification">
          <text class="material-symbols-outlined app-bar-icon">notifications</text>
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
            <text class="welcome-greeting">{{ greeting }}，{{ displayName }} 👋</text>
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
              <text class="material-symbols-outlined quick-action-icon">add_circle</text>
              <text class="quick-action-text">新建知识</text>
            </view>
            <view class="quick-action-btn" @click="handleQuickAction('notice')">
              <text class="material-symbols-outlined quick-action-icon">campaign</text>
              <text class="quick-action-text">发布通知</text>
            </view>
            <view class="quick-action-btn" @click="handleQuickAction('report')">
              <text class="material-symbols-outlined quick-action-icon">analytics</text>
              <text class="quick-action-text">数据报告</text>
            </view>
            <view class="quick-action-btn" @click="handleQuickAction('settings')">
              <text class="material-symbols-outlined quick-action-icon">settings</text>
              <text class="quick-action-text">系统设置</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 统计网格 -->
      <view class="stats-grid animate-fade-up delay-2">
        <view class="stat-card stat-card-1">
          <view class="stat-header">
            <text class="material-symbols-outlined stat-icon stat-icon--primary">dashboard</text>
            <text class="stat-number">{{ stats.todayQuestions }}</text>
          </view>
          <text class="stat-label">今日提问</text>
        </view>
        <view class="stat-card stat-card-2">
          <view class="stat-header">
            <text class="material-symbols-outlined stat-icon stat-icon--danger">priority_high</text>
            <text class="stat-number">{{ pendingCount }}</text>
          </view>
          <text class="stat-label">待处理</text>
        </view>
        <view class="stat-card stat-card-3">
          <view class="stat-header">
            <text class="material-symbols-outlined stat-icon stat-icon--success">menu_book</text>
            <text class="stat-number">{{ stats.knowledgeCount }}</text>
          </view>
          <text class="stat-label">知识条目</text>
        </view>
        <view class="stat-card stat-card-4">
          <view class="stat-header">
            <text class="material-symbols-outlined stat-icon stat-icon--warning">task_alt</text>
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
              <text class="material-symbols-outlined card-arrow">arrow_forward</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 管理员快捷入口 (仅 admin 可见) -->
      <view v-if="isAdmin" class="admin-section animate-fade-up delay-3">
        <view class="section-header">
          <text class="section-title">系统管理</text>
        </view>
        <view class="admin-grid">
          <view class="admin-card" @click="goAdminUsers">
            <text class="material-symbols-outlined admin-card-icon">group</text>
            <text class="admin-card-label">用户管理</text>
          </view>
          <view class="admin-card" @click="goAdminImport">
            <text class="material-symbols-outlined admin-card-icon">person_add</text>
            <text class="admin-card-label">批量导入</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部导航栏 -->
    <BottomNavBar :current="0" :badge="pendingCount > 99 ? 99 : pendingCount" />

    <FeatureNoticeSheet
      :visible="sheetVisible"
      :title="sheetTitle"
      :description="sheetDesc"
      icon="hourglass_empty"
      @close="sheetVisible = false"
    />
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useUserStore } from '@/stores/user'
import BottomNavBar from '../../components/BottomNavBar.vue'
import FeatureNoticeSheet from '../../components/FeatureNoticeSheet.vue'
import { listConversations } from '@/api/conversations'
import { getStatusText } from '@/utils/status-map'
import { wsManager } from '@/utils/websocket'

// 用户状态
const userStore = useUserStore()
const displayName = computed(() => userStore.displayName)
const isAdmin = computed(() => userStore.isAdmin)
const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 9) return '早上好'
  if (h < 12) return '上午好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  if (h < 22) return '晚上好'
  return '夜深了'
})

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

// 弹层状态
const sheetVisible = ref(false)
const sheetTitle = ref('')
const sheetDesc = ref('该功能正在建设中，敬请期待。')

function showSheet(title: string, desc?: string) {
  sheetTitle.value = title
  sheetDesc.value = desc || '该功能正在建设中，敬请期待。'
  sheetVisible.value = true
}

// 通知点击
const handleNotification = () => {
  showSheet('消息通知')
}

// 快捷操作
const handleQuickAction = (type: string) => {
  if (type === 'knowledge') {
    uni.switchTab({ url: '/pages/knowledge/index' })
    return
  }
  if (type === 'report') {
    uni.navigateTo({ url: '/pages/analytics/index' })
    return
  }
  const nameMap: Record<string, string> = {
    notice: '发布通知',
    settings: '系统设置',
  }
  showSheet(nameMap[type] || type)
}

// 查看全部提问
const viewAllQuestions = () => {
  uni.switchTab({ url: '/pages/questions/index' })
}

// 查看单个提问
const viewQuestion = (id: number) => {
  uni.navigateTo({ url: `/pages/questions/detail?id=${id}` })
}

// 管理员入口
const goAdminUsers = () => {
  uni.navigateTo({ url: '/pages/admin/users' })
}
const goAdminImport = () => {
  uni.navigateTo({ url: '/pages/admin/import' })
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

const handleEscalationNotify = () => {
  loadPendingQuestions()
}
const handleStatusChanged = () => {
  loadPendingQuestions()
}

let pollingTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadStats()
  loadPendingQuestions()
  wsManager.on('escalation_notify', handleEscalationNotify)
  wsManager.on('status_changed', handleStatusChanged)
  pollingTimer = setInterval(() => loadPendingQuestions(), 30000)
})

onShow(() => {
  loadStats()
  loadPendingQuestions()
})

onUnmounted(() => {
  wsManager.off('escalation_notify', handleEscalationNotify)
  wsManager.off('status_changed', handleStatusChanged)
  if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
  background: $background;
  padding-bottom: calc(var(--tabbar-safe) + $space-2);  /* tab bar + 8px */
}

// 自定义顶栏
.custom-app-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  height: 56px;
  background: rgba($surface-container-lowest, 0.8);
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

.app-bar-icon {
  font-size: 24px;
  color: $on-surface;
}

.app-bar-icon--primary {
  color: $primary;
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
  border: 2px solid $surface-container-lowest;
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
// 像素级复刻 ca957f5 commit (2026-05-02 用户截图时 HK 线上部署版本):
//   - background: $gradient-hero 已改成 tailwind violet/pink legacy 色系
//   - box-shadow: ca957f5 的 $elevation-3 = 双层 rgba(91, 33, 182, ...) 紫折射
//     (rgb 值对应 violet-800 #5b21b6, 不是 v1 的 #702ae1/rgb 112,42,225)
//   - border-radius: 24px (ca957f5 值, 非 $radius-lg 32px)
.welcome-banner {
  position: relative;
  overflow: hidden;
  background: $gradient-hero;
  border-radius: 24px;
  padding: $space-6;
  box-shadow:
    0 4px 12px rgba(91, 33, 182, 0.10),
    0 16px 40px -8px rgba(91, 33, 182, 0.16);
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
  filter: blur(30px);                          // v1 原值 (MD3 rework 错误放大到 48px 把高光糊掉了)
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

.quick-action-icon {
  font-size: 20px;
  color: $primary;
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
  padding: $space-4;
  border-radius: $radius-md;                    // 1rem — MD3 DEFAULT
  display: flex;
  flex-direction: column;
  gap: $space-2;
  box-shadow: $elevation-1;                     // [CA957F5] 双层紫折射, 让色块悬浮于底板
}

.stat-card-1 {
  background: rgba($secondary-container, 0.3);
}

.stat-card-2 {
  background: rgba($error-container, 0.1);
}

.stat-card-3 {
  background: rgba($success, 0.1);
}

.stat-card-4 {
  background: rgba($warning, 0.16);
}

.stat-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stat-icon {
  font-size: 24px;
}

.stat-icon--primary {
  color: $primary;
}

.stat-icon--danger {
  color: $error;
}

.stat-icon--success {
  color: $success;
}

.stat-icon--warning {
  color: $warning;
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
  border-radius: $radius-md;                    // 1rem — MD3 DEFAULT
  padding: $space-4;
  box-shadow: $elevation-1;                     // [CA957F5] 双层紫折射
  transition: background 0.2s ease, box-shadow 0.2s ease;

  &:active {
    background: $surface-container;
    box-shadow: $elevation-2;                   // [CA957F5] 按下时抬一层
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
  background: $warning;
}

.status-2 {
  background: $success;
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
  color: $warning;
}

.status-text-2 {
  color: $success;
}

.status-text-3 {
  color: $on-surface-variant;
}

.card-arrow {
  font-size: 16px;
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

// 管理员区块
.admin-section {
  margin-top: 1rem;
}

.admin-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.admin-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $space-2;
  padding: $space-5 $space-2;
  background: $surface-container-low;           // No-Line: 用 L1 tonal container 替代渐变+边框
  border-radius: $radius-md;                    // 1rem
  transition: background 0.2s ease, transform 0.2s ease;

  &:active {
    transform: scale(0.97);
    background: rgba($primary, 0.10);
  }
}

.admin-card-icon {
  font-size: 1.75rem;
  color: $primary;
}

.admin-card-label {
  font-size: 0.8125rem;
  font-weight: 700;
  color: $on-surface;
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
