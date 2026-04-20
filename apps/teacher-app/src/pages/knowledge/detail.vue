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
              <text class="tag-text">{{ entry.categoryName || getCategoryName(entry.categoryId) }}</text>
            </view>
            <view class="status-tag">
              <view class="status-dot" :class="getStatusClass(entry.status)"></view>
              <text class="status-text">{{ getStatusText(entry.status) }}</text>
            </view>
          </view>
          <text class="hero-title">{{ entry.title }}</text>
          <view class="author-row">
            <view class="author-avatar">
              <IconUser :size="16" color="#612c90" />
            </view>
            <view class="author-info">
              <text class="author-name">{{ entry.authorName || '未知作者' }}</text>
              <text class="update-time">最后更新于 {{ formatTime(entry.updatedAt || entry.createdAt) }}</text>
            </view>
          </view>
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
          <IconEdit :size="20" color="#f8f0ff" />
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
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import TopAppBar from '../../components/TopAppBar.vue'
import IconUser from '../../components/icons/IconUser.vue'
import IconEdit from '../../components/icons/IconEdit.vue'
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

// 获取分类名称
const getCategoryName = (categoryId?: number) => {
  const map: Record<number, string> = {
    1: '教务管理',
    2: '学生服务',
    3: '生活指南'
  }
  return map[categoryId || 0] || '其他'
}

// 获取状态样式
const getStatusClass = (status?: number) => {
  const map: Record<number, string> = {
    0: 'status-dot--draft',
    1: 'status-dot--published',
    2: 'status-dot--pending',
    3: 'status-dot--offline'
  }
  return map[status || 0] || 'status-dot--draft'
}

// 获取状态文字
const getStatusText = (status?: number) => {
  const map: Record<number, string> = {
    0: '草稿',
    1: '已发布',
    2: '审核中',
    3: '已下线'
  }
  return map[status || 0] || '未知'
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
    background: #22c55e;
  }
  
  &--draft {
    background: $outline-variant;
  }
  
  &--pending {
    background: #f59e0b;
  }
  
  &--offline {
    background: #ef4444;
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

// Content Section
.content-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.content-text {
  font-size: 15px;
  color: $on-surface-variant;
  line-height: 1.8;
  white-space: pre-wrap;
}

// Blockquote style for quoted content
:deep(blockquote),
.blockquote {
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
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
  padding: 16px 20px;
  padding-bottom: calc(16px + env(safe-area-inset-bottom));
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.04);
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
    background: transparent;
    border: 1px solid $outline-variant;
    
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

.btn-text {
  font-size: 15px;
  font-weight: 600;
}
</style>
