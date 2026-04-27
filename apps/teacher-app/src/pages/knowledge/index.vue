<template>
  <view class="knowledge-page">
    <TopAppBar title="知识库" :showBack="true" action="add" />

    <view class="main-content">
      <!-- Search Bar Section -->
      <view class="section animate-fade-up delay-1">
        <view class="search-wrapper">
          <view class="search-icon">
            <text class="material-symbols-outlined search-symbol">search</text>
          </view>
          <input 
            v-model="searchText"
            class="search-input" 
            :placeholder="searchPlaceholder" 
            type="text"
            @confirm="handleSearch"
          />
        </view>
      </view>

      <!-- Category Tabs -->
      <view class="section tabs-section animate-fade-up delay-2">
        <scroll-view class="tabs-scroll" scroll-x show-scrollbar="false">
          <view class="tabs-wrapper">
            <view 
              v-for="(tab, index) in categories" 
              :key="index"
              class="tab-item"
              :class="{ 'tab-item--active': activeCategory === index }"
              @click="switchCategory(index)"
            >
              <text class="tab-text">{{ tab.label }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- Loading State -->
      <view v-if="loading" class="loading-state">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- Empty State -->
      <view v-else-if="currentItems.length === 0" class="empty-state">
        <text class="empty-text">{{ emptyText }}</text>
      </view>

      <!-- Knowledge List -->
      <view v-else class="knowledge-list">
        <template v-if="showUnansweredPane">
          <view 
            v-for="(item, index) in filteredUnansweredItems" 
            :key="item.id"
            class="knowledge-card animate-fade-up"
            :class="`delay-${Math.min(index + 3, 5)}`"
          >
            <view class="card-header">
              <view class="category-tag category-tag--secondary">
                <text class="tag-text">高频待补</text>
              </view>
              <view class="status-tag">
                <text class="hit-count">{{ item.hit_count }} 次命中</text>
              </view>
            </view>
            <text class="card-title">{{ item.question_text }}</text>
            <text class="card-summary">最近出现于 {{ formatTime(item.latest_at) }}</text>
            <view class="card-footer">
              <view class="author-info">
                <view class="avatar-placeholder"></view>
                <text class="author-name">样例会话 {{ (item.sample_conv_ids || []).slice(0, 3).join(' / ') || '暂无' }}</text>
              </view>
              <button class="mini-action-btn" @click.stop="toggleComposer(item.id)">
                <text class="mini-action-text">{{ selectedQuestionId === item.id ? '收起' : '去补充' }}</text>
              </button>
            </view>
            <view v-if="selectedQuestionId === item.id" class="composer-panel">
              <textarea
                v-model="draftAnswer"
                class="answer-input"
                maxlength="1000"
                placeholder="请输入教师答复，系统会自动润色后生成知识条目"
              />
              <view class="scope-list">
                <view
                  v-for="option in availableScopes"
                  :key="option.value"
                  class="scope-pill"
                  :class="{ 'scope-pill--active': selectedScope === option.value }"
                  @click="selectedScope = option.value"
                >
                  <text class="scope-pill-text">{{ option.label }}</text>
                </view>
              </view>
              <button class="submit-btn" :disabled="submitting" @click.stop="submitDraft(item.id)">
                <text class="submit-btn-text">{{ submitting ? '提交中...' : '提交答复' }}</text>
              </button>
            </view>
          </view>
        </template>

        <template v-else>
          <view 
            v-for="(item, index) in displayedKnowledgeItems" 
            :key="item.id"
            class="knowledge-card animate-fade-up"
            :class="`delay-${Math.min(index + 3, 5)}`"
          >
            <view class="card-header">
              <view class="category-tag" :class="getCategoryClass(item.scope)">
                <text class="tag-text">{{ getCategoryName(item.scope) }}</text>
              </view>
              <view class="status-tag">
                <view class="status-dot" :class="getStatusClass(item.status)"></view>
                <text class="status-text" :class="getStatusTextClass(item.status)">{{ getStatusText(item.status) }}</text>
              </view>
            </view>
            <text class="card-title">{{ item.title }}</text>
            <text class="card-summary">{{ getSummary(item.content) }}</text>
            <view v-if="item.reject_reason" class="reject-reason-inline">
              <text class="reject-reason-text">驳回原因：{{ item.reject_reason }}</text>
            </view>
            <view class="card-footer">
              <view class="author-info">
                <view class="avatar-placeholder"></view>
                <text class="author-name">{{ isAdmin && activeCategory === 0 ? `提交人 #${item.submitted_by || '-'}` : (item.representative_query || '知识条目') }}</text>
              </view>
              <view v-if="isAdmin && activeCategory === 0" class="review-actions">
                <button class="mini-action-btn mini-action-btn--approve" @click.stop="handleApprove(item.id)">
                  <text class="mini-action-text mini-action-text--light">通过</text>
                </button>
                <button class="mini-action-btn mini-action-btn--reject" @click.stop="toggleRejectComposer(item.id)">
                  <text class="mini-action-text mini-action-text--light">驳回</text>
                </button>
              </view>
              <button v-else class="mini-action-btn" @click.stop="goToDetail(item.id)">
                <text class="mini-action-text">查看详情</text>
              </button>
            </view>
            <view v-if="isAdmin && activeCategory === 0 && selectedReviewId === item.id" class="composer-panel">
              <textarea
                v-model="reviewRejectReason"
                class="answer-input"
                maxlength="120"
                placeholder="请输入驳回原因，留空则默认“管理员驳回”"
              />
              <view class="review-actions review-actions--inline">
                <button class="mini-action-btn mini-action-btn--ghost" @click.stop="cancelRejectComposer">
                  <text class="mini-action-text">取消</text>
                </button>
                <button class="mini-action-btn mini-action-btn--reject" @click.stop="handleReject(item.id)">
                  <text class="mini-action-text mini-action-text--light">确认驳回</text>
                </button>
              </view>
            </view>
          </view>
        </template>
      </view>
    </view>

    <BottomNavBar :current="2" />
  </view>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopAppBar from '../../components/TopAppBar.vue'
import BottomNavBar from '../../components/BottomNavBar.vue'
import { approveKnowledge, createKnowledgeDraft, getKnowledgeEntries, getPendingReviews, getUnansweredTop, rejectKnowledge } from '@/api/knowledge'
import { useUserStore } from '@/stores/user'
import type { KnowledgeEntry, KnowledgeScope, UnansweredTopItem } from '@/types/api'

const userStore = useUserStore()

const loading = ref(false)
const submitting = ref(false)
const activeCategory = ref(0)
const searchText = ref('')
const unansweredItems = ref<UnansweredTopItem[]>([])
const entries = ref<KnowledgeEntry[]>([])
const pendingEntries = ref<KnowledgeEntry[]>([])
const selectedQuestionId = ref<number | null>(null)
const draftAnswer = ref('')
const selectedScope = ref<KnowledgeScope>('college')
const selectedReviewId = ref<number | null>(null)
const reviewRejectReason = ref('')

const isAdmin = computed(() => userStore.isAdmin)
const categories = computed(() => isAdmin.value
  ? [{ label: '待审核' }, { label: '知识库' }]
  : [{ label: '高频待补' }, { label: '我的知识' }]
)
const showUnansweredPane = computed(() => !isAdmin.value && activeCategory.value === 0)
const searchPlaceholder = computed(() => showUnansweredPane.value ? '搜索待补问题...' : '搜索知识文档、指南或规章...')
const emptyText = computed(() => showUnansweredPane.value
  ? '暂无高频待补问题'
  : (isAdmin.value && activeCategory.value === 0 ? '暂无待审核条目' : '暂无知识文档')
)
const normalizedSearchText = computed(() => searchText.value.trim().toLowerCase())
const availableScopes = computed(() => {
  const scopes: Array<{ value: KnowledgeScope; label: string }> = []
  if (userStore.userInfo?.class_id) {
    scopes.push({ value: 'class', label: '班级发布' })
  }
  if (userStore.userInfo?.college_id) {
    scopes.push({ value: 'college', label: '学院发布' })
  }
  scopes.push({ value: 'global', label: '提交审核' })
  return scopes
})
const filteredUnansweredItems = computed(() => {
  if (!normalizedSearchText.value) return unansweredItems.value
  return unansweredItems.value.filter(item => item.question_text.toLowerCase().includes(normalizedSearchText.value))
})
const filteredEntries = computed(() => {
  if (!normalizedSearchText.value) return entries.value
  return entries.value.filter(item => (
    item.title.toLowerCase().includes(normalizedSearchText.value)
    || item.content.toLowerCase().includes(normalizedSearchText.value)
    || item.representative_query.toLowerCase().includes(normalizedSearchText.value)
  ))
})
const filteredPendingEntries = computed(() => {
  if (!normalizedSearchText.value) return pendingEntries.value
  return pendingEntries.value.filter(item => (
    item.title.toLowerCase().includes(normalizedSearchText.value)
    || item.content.toLowerCase().includes(normalizedSearchText.value)
    || item.representative_query.toLowerCase().includes(normalizedSearchText.value)
  ))
})
const displayedKnowledgeItems = computed<KnowledgeEntry[]>(() => {
  if (isAdmin.value && activeCategory.value === 0) return filteredPendingEntries.value
  return filteredEntries.value
})
const currentItems = computed(() => showUnansweredPane.value ? filteredUnansweredItems.value : displayedKnowledgeItems.value)


// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    if (showUnansweredPane.value) {
      const res = await getUnansweredTop(20)
      unansweredItems.value = res.items || []
      return
    }

    if (isAdmin.value && activeCategory.value === 0) {
      const res = await getPendingReviews(20)
      pendingEntries.value = res.items || []
      return
    }

    const res = await getKnowledgeEntries({
      title: searchText.value || undefined,
      pageNum: 1,
      pageSize: 20
    })
    entries.value = res.items || []
  } catch (e) {
    console.error('加载知识库失败', e)
    if (showUnansweredPane.value) unansweredItems.value = []
    else if (isAdmin.value && activeCategory.value === 0) pendingEntries.value = []
    else entries.value = []
  } finally {
    loading.value = false
  }
}

const refreshAdminLists = async () => {
  const [pendingRes, entryRes] = await Promise.all([
    getPendingReviews(20),
    getKnowledgeEntries({ pageNum: 1, pageSize: 20 })
  ])
  pendingEntries.value = pendingRes.items || []
  entries.value = entryRes.items || []
}

const handleApprove = async (entryId: number) => {
  try {
    await approveKnowledge(entryId)
    uni.showToast({ title: '审核通过，已发布', icon: 'success' })
    await refreshAdminLists()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '审核失败', icon: 'none' })
  }
}

const handleReject = async (entryId: number) => {
  try {
    await rejectKnowledge(entryId, reviewRejectReason.value.trim())
    uni.showToast({ title: '已驳回', icon: 'success' })
    cancelRejectComposer()
    await refreshAdminLists()
  } catch (e: any) {
    uni.showToast({ title: e?.message || '驳回失败', icon: 'none' })
  }
}

// 切换分类
const switchCategory = (index: number) => {
  activeCategory.value = index
  selectedQuestionId.value = null
  loadData()
}

// 搜索
const handleSearch = () => {
  loadData()
}

const toggleComposer = (questionId: number) => {
  if (selectedQuestionId.value === questionId) {
    selectedQuestionId.value = null
    return
  }
  selectedQuestionId.value = questionId
  draftAnswer.value = ''
  selectedScope.value = userStore.preferredKnowledgeScope
}

const toggleRejectComposer = (entryId: number) => {
  if (selectedReviewId.value === entryId) {
    selectedReviewId.value = null
    reviewRejectReason.value = ''
    return
  }
  selectedReviewId.value = entryId
  reviewRejectReason.value = ''
}

const cancelRejectComposer = () => {
  selectedReviewId.value = null
  reviewRejectReason.value = ''
}

const submitDraft = async (questionId: number) => {
  if (!draftAnswer.value.trim()) {
    uni.showToast({ title: '请输入教师答复', icon: 'none' })
    return
  }
  if (selectedScope.value === 'class' && !userStore.userInfo?.class_id) {
    uni.showToast({ title: '当前账号未绑定班级', icon: 'none' })
    return
  }
  if (selectedScope.value === 'college' && !userStore.userInfo?.college_id) {
    uni.showToast({ title: '当前账号未绑定学院', icon: 'none' })
    return
  }

  submitting.value = true
  try {
    const res = await createKnowledgeDraft({
      unanswered_question_id: questionId,
      raw_answer: draftAnswer.value.trim(),
      scope: selectedScope.value,
      scope_value: selectedScope.value === 'class'
        ? userStore.userInfo?.class_id
        : (selectedScope.value === 'college' ? userStore.userInfo?.college_id : null)
    })
    uni.showToast({
      title: res.publish_mode === 'published' ? '已发布到知识库' : '已提交管理员审核',
      icon: 'success'
    })
    selectedQuestionId.value = null
    draftAnswer.value = ''
    await Promise.all([
      getUnansweredTop(20).then((resp) => { unansweredItems.value = resp.items || [] }),
      getKnowledgeEntries({ pageNum: 1, pageSize: 20 }).then((resp) => { entries.value = resp.items || [] })
    ])
  } catch (e: any) {
    uni.showToast({ title: e?.message || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

// 跳转到详情
const goToDetail = (id: number) => {
  uni.navigateTo({ url: `/pages/knowledge/detail?id=${id}` })
}

// 获取分类样式
const getCategoryClass = (scope?: string) => {
  const map: Record<string, string> = {
    class: 'category-tag--secondary',
    college: 'category-tag--secondary',
    global: 'category-tag--tertiary'
  }
  return map[scope || 'college'] || 'category-tag--secondary'
}

// 获取分类名称
const getCategoryName = (scope?: string) => {
  const map: Record<string, string> = {
    class: '班级知识',
    college: '学院知识',
    global: '全校知识'
  }
  return map[scope || 'college'] || '知识条目'
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

// 获取状态文字样式
const getStatusTextClass = (status?: string) => {
  const map: Record<string, string> = {
    draft: 'status-text--draft',
    approved: 'status-text--published',
    pending: 'status-text--pending',
    rejected: 'status-text--offline',
    offline: 'status-text--offline'
  }
  return map[status || 'draft'] || 'status-text--draft'
}

// 获取状态文字
const getStatusText = (status?: string) => {
  const map: Record<string, string> = {
    draft: '草稿',
    approved: '已发布',
    pending: '审核中',
    rejected: '已驳回',
    offline: '已下线'
  }
  return map[status || 'draft'] || '未知'
}

// 获取摘要
const getSummary = (content?: string) => {
  if (!content) return ''
  return content.length > 100 ? content.substring(0, 100) + '...' : content
}

// 格式化时间
const formatTime = (time?: string) => {
  if (!time) return ''
  const date = new Date(time)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  // 一小时内
  if (diff < 3600000) {
    const mins = Math.floor(diff / 60000)
    return mins < 1 ? '刚刚' : `${mins}分钟前`
  }
  // 一天内
  if (diff < 86400000) {
    const hours = Math.floor(diff / 3600000)
    return `${hours}小时前`
  }
  // 一周内
  if (diff < 604800000) {
    const days = Math.floor(diff / 86400000)
    return `${days}天前`
  }
  
  return date.toLocaleDateString('zh-CN')
}

onMounted(() => loadData())
onShow(() => loadData())
</script>

<style lang="scss" scoped>
.knowledge-page {
  min-height: 100vh;
  padding-bottom: 112px;
  background: $background;
}

.main-content {
  position: relative;
  z-index: 1;
  padding-top: 72px;
  padding-left: 20px;
  padding-right: 20px;
}

.section {
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

// Search Bar
.search-wrapper {
  position: relative;
  height: 56px;
  background: $surface-container;
  border-radius: 16px;
  display: flex;
  align-items: center;
}

.search-icon {
  position: absolute;
  left: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.6;
}

.search-symbol {
  font-size: 20px;
  color: $on-surface-variant;
}

.search-input {
  flex: 1;
  height: 100%;
  padding-left: 48px;
  padding-right: 16px;
  background: transparent;
  border: none;
  font-size: 15px;
  color: $on-surface;
  
  &::placeholder {
    color: $on-surface-variant;
    opacity: 0.5;
  }
}

// Tabs
.tabs-section {
  margin-left: -20px;
  margin-right: -20px;
  padding-left: 20px;
  padding-right: 20px;

  :deep(.uni-scroll-view::-webkit-scrollbar) {
    display: none;
  }
  :deep(.uni-scroll-view) {
    scrollbar-width: none;
  }
}

.tabs-scroll {
  white-space: nowrap;
}

.tabs-wrapper {
  display: inline-flex;
  gap: 12px;
  padding-bottom: 8px;
}

.tab-item {
  flex-shrink: 0;
  white-space: nowrap;
  padding: 10px 24px;
  background: $surface-container-low;
  border-radius: 9999px;
  transition: all 0.2s ease;
  
  &:active {
    transform: scale(0.95);
  }
  
  &--active {
    background: $primary;
    box-shadow: 0 8px 16px -4px rgba($primary, 0.2);
    
    .tab-text {
      color: $on-primary;
    }
  }
}

.tab-text {
  font-size: 14px;
  font-weight: 500;
  color: $on-surface-variant;
  white-space: nowrap;
}

// Loading & Empty State
.loading-state,
.empty-state {
  padding: 60px 20px;
  text-align: center;
}

.loading-text,
.empty-text {
  font-size: 14px;
  color: $on-surface-variant;
}

// Knowledge Cards
.knowledge-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.knowledge-card {
  background: $surface-container-lowest;
  border-radius: 24px;
  padding: 24px;
  transition: all 0.2s ease;
  box-shadow: $elevation-1;
  
  &:active {
    transform: scale(0.98);
    background: $surface-container-low;
    box-shadow: $elevation-2;
  }
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.category-tag {
  padding: 4px 12px;
  border-radius: 9999px;
  
  &--secondary {
    background: $secondary-container;
    
    .tag-text {
      color: $on-secondary-container;
    }
  }
  
  &--tertiary {
    background: $tertiary-container;
    
    .tag-text {
      color: $on-tertiary-container;
    }
  }
}

.tag-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.status-tag {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  
  &--published {
    background: $primary;
  }

  &--pending {
    background: $warning;
  }
  
  &--draft {
    background: $outline-variant;
  }

  &--offline {
    background: $error;
  }
}

.status-text {
  font-size: 12px;
  font-weight: 500;
  
  &--published {
    color: $primary;
  }
  
  &--draft {
    color: $on-surface-variant;
  }

  &--pending {
    color: $warning;
  }

  &--offline {
    color: $error;
  }
}

.card-title {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: $on-surface;
  line-height: 1.3;
  margin-bottom: 8px;
}

.card-summary {
  display: block;
  font-size: 14px;
  color: $on-surface-variant;
  line-height: 1.6;
  margin-bottom: 16px;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid rgba($outline-variant, 0.1);
}

.author-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar-placeholder {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: $surface-container-highest;
}

.author-name {
  font-size: 12px;
  font-weight: 500;
  color: $on-surface-variant;
}

.time-text {
  font-size: 12px;
  color: $on-surface-variant;
  opacity: 0.6;
}

.hit-count {
  font-size: 12px;
  color: $primary;
  font-weight: 600;
}

.mini-action-btn {
  height: 32px;
  margin: 0;
  padding: 0 16px;
  border-radius: 9999px;
  border: none;
  background: $primary-container;
  display: inline-flex;
  align-items: center;
  justify-content: center;

  &::after {
    border: none;
  }
}

.mini-action-btn--approve {
  background: $success;
}

.mini-action-btn--reject {
  background: $error;
}

.mini-action-btn--ghost {
  background: $surface-container;
}

.mini-action-text {
  font-size: 12px;
  font-weight: 600;
  color: $on-primary-container;
}

.mini-action-text--light {
  color: $on-primary;
}

.composer-panel {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba($outline-variant, 0.12);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.answer-input {
  width: 100%;
  min-height: 120px;
  padding: 14px 16px;
  box-sizing: border-box;
  background: $surface-container;
  border-radius: 16px;
  font-size: 14px;
  color: $on-surface;
}

.scope-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.scope-pill {
  padding: 10px 14px;
  border-radius: 9999px;
  background: $surface-container;

  &--active {
    background: $primary;

    .scope-pill-text {
      color: $on-primary;
    }
  }
}

.scope-pill-text {
  font-size: 13px;
  font-weight: 600;
  color: $on-surface-variant;
}

.submit-btn {
  height: 44px;
  border: none;
  border-radius: 9999px;
  background: linear-gradient(135deg, $primary 0%, $primary-container 100%);

  &::after {
    border: none;
  }

  &[disabled] {
    opacity: 0.6;
  }
}

.submit-btn-text {
  font-size: 14px;
  font-weight: 700;
  color: $on-primary;
}

.review-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.review-actions--inline {
  justify-content: flex-end;
}

.reject-reason-inline {
  margin-bottom: 12px;
  padding: 10px 12px;
  background: rgba(239, 68, 68, 0.08);
  border-radius: 12px;
}

.reject-reason-text {
  font-size: 12px;
  line-height: 1.6;
  color: $error;
}
</style>
