<template>
  <view class="questions-page">
    <TopAppBar title="学生提问" showBack action="search" />

    <view class="main-content">
      <!-- Filter Tabs -->
      <scroll-view scroll-x class="filter-section animate-fade-up delay-1" show-scrollbar="false">
        <view class="filter-tabs">
          <view 
            v-for="(tab, index) in filterTabs" 
            :key="index"
            class="filter-tab"
            :class="{ 'filter-tab--active': activeTab === index }"
            @click="switchTab(index)"
          >
            <text class="tab-text">{{ tab.label }}</text>
            <view
              v-if="tab.status === PENDING_STATUS && pendingCount > 0"
              class="pending-badge"
            >
              <text class="pending-badge-text">{{ pendingCount > 99 ? '99+' : pendingCount }}</text>
            </view>
          </view>
        </view>
      </scroll-view>

      <!-- Loading State -->
      <view v-if="loading" class="loading-container">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- Empty State -->
      <view v-else-if="questions.length === 0" class="empty-container">
        <text class="empty-text">暂无工单</text>
      </view>

      <!-- Question List -->
      <view v-else class="question-list">
        <view 
          v-for="(item, index) in questions" 
          :key="item.id"
          class="question-card animate-fade-up"
          :class="`delay-${Math.min(index + 2, 4)}`"
          @click="goToDetail(item.id)"
        >
          <view class="card-header">
            <view class="student-info">
              <UserAvatar
                :staff-id="item.student_id"
                :size="44"
              />
              <view class="student-meta">
                <text class="student-name">{{ item.student_name || `学号 ${item.student_id}` }}</text>
                <text class="student-major">{{ formatTime(item.updated_at) }}</text>
              </view>
            </view>
            <view 
              class="status-tag"
              :class="getStatusClass(item.status)"
            >
              <text class="status-text">{{ getStatusText(item.status) }}</text>
            </view>
          </view>

          <text class="question-content">{{ item.title || '无标题' }}</text>

          <!-- AI Confidence Section（仅当后端有真实 confidence 字段时展示）-->
          <view v-if="typeof item.confidence === 'number' && item.confidence > 0" class="ai-confidence">
            <view class="confidence-header">
              <view class="confidence-label">
                <text class="material-symbols-outlined confidence-icon">psychology</text>
                <text class="label-text">AI 匹配度</text>
              </view>
              <text class="confidence-value">{{ item.confidence }}%</text>
            </view>
            <view class="progress-bar">
              <view 
                class="progress-fill"
                :class="getProgressColorClass(item.confidence)"
                :style="{ width: `${item.confidence}%` }"
              ></view>
            </view>
          </view>
        </view>
      </view>
    </view>

    <BottomNavBar :current="1" :badge="total > 99 ? 99 : total" />
  </view>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, onActivated } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopAppBar from '../../components/TopAppBar.vue'
import BottomNavBar from '../../components/BottomNavBar.vue'
import UserAvatar from '../../components/UserAvatar.vue'
import { listConversations } from '@/api/conversations'
import { getStatusText, getStatusClass } from '@/utils/status-map'
import { wsManager } from '@/utils/websocket'
import { centrifugeManager } from '@/utils/centrifuge'

const PENDING_STATUS = 'pending_teacher'

// Filter tabs: 全部 / 待处理 / 处理中 / 已解决
const filterTabs = [
  { label: '全部', status: undefined as string | undefined },
  { label: '待处理', status: PENDING_STATUS },
  { label: '处理中', status: 'teacher_serving' },
  { label: '已解决', status: 'resolved' }
]

const avatarClassNames = ['avatar-primary', 'avatar-success', 'avatar-warning', 'avatar-info', 'avatar-danger']
const activeTab = ref(0)
const questions = ref<any[]>([])
const loading = ref(false)
const total = ref(0)
const pendingCount = ref(0)

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

const getProgressColorClass = (confidence: number) => {
  if (confidence >= 80) return 'progress-green'
  if (confidence >= 60) return 'progress-amber'
  return 'progress-red'
}

// 加载数据 (v2: 使用 listConversations + status 过滤)
const loadData = async () => {
  loading.value = true
  try {
    const tab = filterTabs[activeTab.value]
    const res = await listConversations(1, 20, tab.status)
    const items = res.items || []
    questions.value = items
    total.value = res.total || 0
    pendingCount.value = tab.status === PENDING_STATUS
      ? (res.total || items.length)
      : items.filter((item) => item.status === PENDING_STATUS).length
  } catch (e) {
    console.error('加载工单失败', e)
    questions.value = []
    total.value = 0
    pendingCount.value = 0
  } finally {
    loading.value = false
  }
}

// Tab 切换
const switchTab = (index: number) => {
  activeTab.value = index
  loadData()
}

const goToDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/questions/detail?id=${id}` })
}

const handleEscalationNotify = () => {
  loadData()
}

const handleStatusChanged = () => {
  loadData()
}

let pollingTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  loadData()
  wsManager.on('escalation_notify', handleEscalationNotify)
  wsManager.on('status_changed', handleStatusChanged)
  // Centrifugo dual-subscribe（legacy ws 已弃用，实际事件由 Centrifugo 推送）
  centrifugeManager.on('escalation_notify', handleEscalationNotify)
  centrifugeManager.on('status_changed', handleStatusChanged)
  // 轮询兜底：30s 一次，防止 WS 事件丢失
  pollingTimer = setInterval(() => loadData(), 30000)
})

onShow(() => {
  loadData()
})

onUnmounted(() => {
  wsManager.off('escalation_notify', handleEscalationNotify)
  wsManager.off('status_changed', handleStatusChanged)
  centrifugeManager.off('escalation_notify', handleEscalationNotify)
  centrifugeManager.off('status_changed', handleStatusChanged)
  if (pollingTimer) { clearInterval(pollingTimer); pollingTimer = null }
})
</script>

<style lang="scss" scoped>
.questions-page {
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

// Loading & Empty State
.loading-container,
.empty-container {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 60px 20px;
}

.loading-text,
.empty-text {
  font-size: 14px;
  color: $on-surface-variant;
}

// Filter Tabs
.filter-section {
  margin-left: -20px;
  margin-right: -20px;
  padding-left: 20px;
  padding-right: 20px;
  // 注意：垂直内边距移到 .filter-tabs（scroll content）内部，
  // uni-app H5 的 <scroll-view> 内层 .uni-scroll-view 有 overflow:hidden，
  // 给外层 host 加 padding 不会让超出 .filter-tab 顶沿的 badge 在内层可见。
  white-space: nowrap;

  :deep(.uni-scroll-view::-webkit-scrollbar) {
    display: none;
  }
  :deep(.uni-scroll-view) {
    scrollbar-width: none;
  }
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

.filter-tabs {
  display: flex;
  gap: 12px;
  // 12px = 4(.pending-badge top:-4 凸出) + 2(box-shadow ring) + 6 缓冲。
  // 必须放在 scroll content（.filter-tabs）而非 scroll-view host（.filter-section），
  // 才能突破内层 .uni-scroll-view overflow:hidden 的裁剪。
  padding-top: 12px;
  padding-bottom: 8px;
}

.filter-tab {
  position: relative;
  flex-shrink: 0;
  padding: 10px 24px;
  border-radius: 9999px;
  background: $surface-container-low;
  transition: all 0.2s ease;
  white-space: nowrap;

  .tab-text {
    font-size: 14px;
    font-weight: 500;
    color: $on-surface-variant;
  }

  &--active {
    background: $primary;
    box-shadow: 0 8px 16px -4px rgba($primary, 0.2);

    .tab-text {
      color: $on-primary;
    }
  }
}

.pending-badge {
  position: absolute;
  top: -4px;
  right: 8px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: 9999px;
  background: $error;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  box-shadow: 0 0 0 2px $background;
}

.pending-badge-text {
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  color: $on-primary;
}

// Question List
.question-list {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

// Question Card
.question-card {
  background: $surface-container-lowest;
  border-radius: $radius-md;                   // 1rem MD3 DEFAULT
  padding: 20px;
  box-shadow: $elevation-1;                    // [CA957F5] 双层紫折射, 让 card 悬浮于底板
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;

  &:active {
    transform: scale(0.98);
    background: $surface-container;
    box-shadow: $elevation-2;                  // [CA957F5] 按下时抬一层
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}

.student-info {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.avatar-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-primary {
  background: $primary;
}

.avatar-success {
  background: $success;
}

.avatar-warning {
  background: $warning;
}

.avatar-info {
  background: $info;
}

.avatar-danger {
  background: $error;
}

.avatar-initial {
  font-size: 18px;
  font-weight: 700;
  color: $on-primary;
}

.student-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.student-name {
  font-size: 16px;
  font-weight: 700;
  color: $on-surface;
}

.student-major {
  font-size: 12px;
  color: $on-surface-variant;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.status-tag {
  padding: 4px 12px;
  border-radius: 9999px;
  white-space: nowrap;
  flex-shrink: 0;
  margin-left: 8px;

  .status-text {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  &.status-pending {
    background: rgba($error-container, 0.1);

    .status-text {
      color: $error;
    }
  }

  &.status-serving,
  &.status-ai-serving {
    background: rgba($primary-container, 0.2);

    .status-text {
      color: $primary;
    }
  }

  &.status-resolved {
    background: rgba($success, 0.1);

    .status-text {
      color: $success;
    }
  }

  &.status-closed {
    background: rgba($on-surface-variant, 0.1);

    .status-text {
      color: $on-surface-variant;
    }
  }
}

.question-content {
  font-size: 14px;
  line-height: 1.6;
  color: $on-surface-variant;
  margin-bottom: 16px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

// AI Confidence
.ai-confidence {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.confidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.confidence-label {
  display: flex;
  align-items: center;
  gap: 4px;

  .label-text {
    font-size: 10px;
    font-weight: 700;
    color: rgba($on-surface-variant, 0.6);
  }
}

.confidence-icon {
  font-size: 12px;
  color: $on-surface-variant;
}

.confidence-value {
  font-size: 10px;
  font-weight: 700;
  color: rgba($on-surface-variant, 0.6);
}

.progress-bar {
  height: 4px;
  width: 100%;
  background: $surface-container;
  border-radius: 9999px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 9999px;
  transition: width 0.3s ease;

  &.progress-green {
    background: $success;
  }

  &.progress-amber {
    background: $warning;
  }

  &.progress-red {
    background: $error;
  }
}

// Animation delays
.delay-1 { animation-delay: 0.1s; }
.delay-2 { animation-delay: 0.2s; }
.delay-3 { animation-delay: 0.3s; }
.delay-4 { animation-delay: 0.4s; }
</style>
