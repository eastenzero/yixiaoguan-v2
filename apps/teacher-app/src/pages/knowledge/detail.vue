<template>
  <view class="knowledge-detail-page">
    <TopAppBar title="知识详情" :showBack="true" action="edit" />

    <!-- Loading State -->
    <view v-if="loading" class="loading-container">
      <text class="loading-text">加载中...</text>
    </view>

    <template v-else-if="entry">
      <view class="main-content animate-fade-up">
        <!-- Hero Section -->
        <view class="hero-section">
          <view class="tags-row">
            <view class="category-tag">
              <text class="tag-text">{{ getCategoryName(entry) }}</text>
            </view>
            <view class="status-tag">
              <view class="status-dot" :class="getStatusClass(entry.status)"></view>
              <text class="status-text">{{ getStatusText(entry) }}</text>
            </view>
          </view>
          <text class="hero-title">{{ entry.title }}</text>
          <view class="governance-tags">
            <text class="governance-tag" :class="`governance-tag--${entry.freshness || 'unclassified'}`">
              {{ getFreshnessLabel(entry.freshness) }}
            </text>
            <text v-if="entry.policy_level" class="governance-tag governance-tag--neutral">
              {{ getPolicyLevelLabel(entry.policy_level) }}
            </text>
            <text v-if="entry.review_required" class="governance-tag governance-tag--review">需要复核</text>
          </view>
          <view class="author-row">
            <view class="author-avatar">
              <AppIcon name="person" class="author-icon" />
            </view>
            <view class="author-info">
              <text class="author-name">{{ getEntryMeta(entry) }}</text>
              <text v-if="entry.source_published_at" class="update-time">来源发布于 {{ formatDateOnly(entry.source_published_at) }}</text>
              <text v-if="entry.verified_at" class="update-time">资料核验于 {{ formatDateOnly(entry.verified_at) }}</text>
              <text v-if="!entry.source_published_at && !entry.verified_at" class="update-time update-time--pending">
                入库于 {{ formatDateOnly(entry.created_at) }} · 来源日期待补
              </text>
            </view>
          </view>
        </view>

        <view v-if="entry.reject_reason" class="reject-banner">
          <text class="reject-banner-text">驳回原因：{{ entry.reject_reason }}</text>
        </view>

        <view v-if="entry.fallback" class="api-warning">
          <text class="api-warning-text">{{ entry.fallback.message }}</text>
        </view>

        <view class="evidence-section">
          <text class="evidence-title">资料依据</text>
          <view v-if="entry.source_url" class="evidence-link" @click="copySourceUrl(entry.source_url)">
            <AppIcon name="link" class="evidence-icon" />
            <view class="evidence-copy">
              <text class="evidence-label">官方来源链接</text>
              <text class="evidence-value">{{ entry.source_url }}</text>
            </view>
            <text class="evidence-action">复制</text>
          </view>
          <view v-else class="evidence-pending">
            <AppIcon name="info" class="evidence-icon" />
            <text>原始资料可追溯，但公开来源链接仍待补充。</text>
          </view>
          <text class="evidence-notice">核验日期与来源发布日期含义不同；具体政策以当年度正式通知为准。</text>
        </view>

        <!-- Body Content -->
        <view class="content-section">
          <text class="content-text">{{ entry.content }}</text>
        </view>
      </view>

      <!-- Bottom Action Bar -->
      <view class="bottom-action-bar">
        <button class="action-btn action-btn--outline" @click="handleOffline">
          <text class="btn-text">下线</text>
        </button>
        <button class="action-btn action-btn--primary" @click="handleEdit">
          <AppIcon name="edit" class="btn-icon" />
          <text class="btn-text">编辑</text>
        </button>
      </view>
    </template>

    <!-- Empty State -->
    <view v-else class="empty-container">
      <text class="empty-text">文档不存在或已删除</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopAppBar from '../../components/TopAppBar.vue'
import { getKnowledgeDetail, offlineEntry } from '@/api/knowledge'

const entry = ref<any>(null)
const loading = ref(false)
const entryId = ref(0)

onLoad((options: any) => {
  entryId.value = Number(options?.id || 0)
  if (entryId.value) {
    loadDetail()
  } else {
    uni.showToast({ title: '无效的文档ID', icon: 'none' })
    setTimeout(() => uni.navigateBack(), 1500)
  }
})

const loadDetail = async () => {
  loading.value = true
  try {
    const res = await getKnowledgeDetail(entryId.value)
    entry.value = res
    if (res.fallback?.message) {
      uni.showToast({ title: res.fallback.message, icon: 'none' })
    }
  } catch (e) {
    console.error('加载详情失败', e)
    uni.showToast({ title: '加载失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

const handleOffline = async () => {
  uni.showModal({
    title: '确认下线',
    content: '确定要将该知识文档下线吗？',
    success: async (res) => {
      if (res.confirm) {
        try {
          await offlineEntry(entryId.value)
          uni.showToast({ title: '已下线', icon: 'success' })
          loadDetail()
        } catch (e: any) {
          uni.showToast({ title: e?.message || '操作失败', icon: 'none' })
        }
      }
    }
  })
}

const handleEdit = () => {
  uni.showToast({ title: '编辑功能开发中', icon: 'none' })
}

const isKbEntry = (item: any) => item?.source_type === 'kb_entry'

// 获取分类名称
const getCategoryName = (item: any) => {
  if (isKbEntry(item)) return item.category || '真实知识库'
  const map: Record<string, string> = {
    class: '班级知识',
    college: '学院知识',
    global: '全校知识'
  }
  return map[item?.scope || 'college'] || '知识条目'
}

// 获取状态样式
const getStatusClass = (status?: string) => {
  const map: Record<string, string> = {
    draft: 'status-dot--draft',
    approved: 'status-dot--published',
    pending: 'status-dot--pending',
    rejected: 'status-dot--offline',
    offline: 'status-dot--offline'
  }
  return map[status || 'draft'] || 'status-dot--draft'
}

// 获取状态文字
const getStatusText = (item: any) => {
  if (isKbEntry(item)) return '已入库'
  const map: Record<string, string> = {
    draft: '草稿',
    approved: '已发布',
    pending: '审核中',
    rejected: '已驳回',
    offline: '已下线'
  }
  return map[item?.status || 'draft'] || '未知'
}

const getEntryMeta = (item: any) => {
  if (!isKbEntry(item)) return item?.representative_query || '知识条目'
  return item.original_source || item.original_filename || item.material_id || item.campus || '真实知识库条目'
}

const getFreshnessLabel = (freshness?: string) => {
  const map: Record<string, string> = {
    stable: '长期有效',
    'current-year': '当年政策',
    'time-bound': '时效敏感',
    expired: '历史/过期',
    unclassified: '待分类'
  }
  return map[freshness || 'unclassified'] || '待分类'
}

const getPolicyLevelLabel = (level?: string) => {
  const map: Record<string, string> = {
    national: '国家级',
    provincial: '省级',
    school: '校级',
    college: '学院级'
  }
  return map[level || ''] || level || ''
}

const formatDateOnly = (time?: string) => {
  if (!time) return '待补充'
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return time.slice(0, 10)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric' })
}

const copySourceUrl = (url?: string | null) => {
  if (!url) return
  uni.setClipboardData({
    data: url,
    success: () => uni.showToast({ title: '来源链接已复制', icon: 'success' })
  })
}

// 格式化时间
const formatTime = (time?: string) => {
  if (!time) return '未知时间'
  const date = new Date(time)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
.knowledge-detail-page {
  min-height: 100vh;
  background: $surface;
  padding-bottom: 100px;
}

.loading-container,
.empty-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 50vh;
  padding-top: 80px;
}

.loading-text,
.empty-text {
  font-size: 14px;
  color: $on-surface-variant;
}

.main-content {
  padding-top: 80px;
  padding-left: 20px;
  padding-right: 20px;
}


// Hero Section
.hero-section {
  margin-bottom: 32px;
}

.tags-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
}

.category-tag {
  padding: 4px 12px;
  background: $primary-container;
  border-radius: 9999px;
  
  .tag-text {
    font-size: 11px;
    font-weight: 700;
    color: $on-primary-container;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  background: $surface-container;
  border-radius: 9999px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  
  &--published {
    background: $success;
  }
  
  &--draft {
    background: $outline-variant;
  }
  
  &--pending {
    background: $warning;
  }
  
  &--offline {
    background: $error;
  }
}

.status-text {
  font-size: 11px;
  font-weight: 500;
  color: $on-surface-variant;
}

.hero-title {
  display: block;
  font-size: 30px;
  font-weight: 800;
  color: $on-surface;
  line-height: 1.2;
  margin-bottom: 16px;
}

.governance-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin: -4px 0 10px;
}

.governance-tag {
  padding: 5px 9px;
  border-radius: 999px;
  color: $primary;
  background: rgba($primary, 0.09);
  font-size: 10px;
  font-weight: 700;
}

.governance-tag--time-bound,
.governance-tag--review {
  color: $warning;
  background: rgba($warning, 0.11);
}

.governance-tag--expired {
  color: $on-surface-variant;
  background: $surface-container;
}

.governance-tag--neutral,
.governance-tag--unclassified {
  color: $on-surface-variant;
  background: $surface-container-low;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 8px;
}

.author-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: $secondary-container;
  display: flex;
  align-items: center;
  justify-content: center;
}

.author-icon {
  font-size: 16px;
  color: $primary;
}

.author-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.author-name {
  font-size: 14px;
  font-weight: 600;
  color: $on-surface;
}

.update-time {
  font-size: 12px;
  color: $on-surface-variant;
}

.update-time--pending {
  color: $warning;
}

.evidence-section {
  margin-bottom: 22px;
  padding: 16px;
  border-radius: 18px;
  background: $surface-container-low;
}

.evidence-title,
.evidence-label,
.evidence-value,
.evidence-notice {
  display: block;
}

.evidence-title {
  margin-bottom: 12px;
  color: $on-surface;
  font-size: 14px;
  font-weight: 800;
}

.evidence-link,
.evidence-pending {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px;
  border-radius: 14px;
  background: $surface-container-lowest;
}

.evidence-pending {
  color: $on-surface-variant;
  font-size: 12px;
  line-height: 1.5;
}

.evidence-icon {
  flex-shrink: 0;
  color: $primary;
  font-size: 18px;
}

.evidence-copy {
  flex: 1;
  min-width: 0;
}

.evidence-label {
  color: $on-surface;
  font-size: 12px;
  font-weight: 700;
}

.evidence-value {
  margin-top: 3px;
  overflow: hidden;
  color: $on-surface-variant;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.evidence-action {
  flex-shrink: 0;
  color: $primary;
  font-size: 11px;
  font-weight: 700;
}

.evidence-notice {
  margin-top: 10px;
  color: $on-surface-variant;
  font-size: 10px;
  line-height: 1.55;
}

// Content Section
.content-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.reject-banner {
  margin-bottom: 24px;
  padding: 12px 16px;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 16px;
}

.api-warning {
  margin-bottom: 24px;
  padding: 12px 16px;
  background: rgba(245, 158, 11, 0.12);
  border-radius: 16px;
}

.api-warning-text {
  font-size: 13px;
  line-height: 1.6;
  color: $warning;
}

.reject-banner-text {
  font-size: 13px;
  line-height: 1.6;
  color: $error;
}

.content-text {
  font-size: 15px;
  color: $on-surface-variant;
  line-height: 1.8;
  white-space: pre-wrap;
}

// Blockquote style for quoted content
.quote-block {
  border-left: 4px solid $primary-container;
  background: rgba($primary-container, 0.1);
  padding: 12px 16px;
  border-radius: 0 12px 12px 0;
  margin: 8px 0;
  font-style: italic;
  color: $on-surface-variant;
}

// Bottom Action Bar
.bottom-action-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba($surface-container-lowest, 0.9);
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
  padding: 16px 20px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  box-shadow: $shadow-nav;                    // 紫色折射 nav lift 代替中性灰
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 48px;
  border-radius: 9999px;
  border: none;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.2s ease;
  
  &:active {
    transform: scale(0.95);
  }
  
  &::after {
    border: none;
  }
  
  &--outline {
    flex: 1;
    background: $surface-container-high;        // No-Line: 用 L3 tonal 替代 1px solid 边框
    
    .btn-text {
      color: $on-surface;
    }
    
    &:active {
      background: $surface-container-low;
    }
  }
  
  &--primary {
    flex: 2;
    background: linear-gradient(135deg, $primary 0%, $primary-container 100%);
    box-shadow: 0 4px 15px rgba($primary, 0.3);
    
    .btn-text {
      color: $on-primary;
    }
    
    &:active {
      opacity: 0.9;
    }
  }
}

.btn-icon {
  font-size: 20px;
  color: $on-primary;
}

.btn-text {
  font-size: 15px;
  font-weight: 600;
}
</style>
