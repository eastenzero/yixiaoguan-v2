<template>
  <view class="admin-users-page">
    <view class="custom-app-bar">
      <view class="app-bar-content">
        <view class="app-bar-left" @click="handleBack">
          <text class="material-symbols-outlined app-bar-icon">arrow_back</text>
          <text class="app-bar-title">用户管理</text>
        </view>
        <view class="app-bar-right" @click="goImport">
          <text class="material-symbols-outlined app-bar-icon app-bar-icon--primary">person_add</text>
        </view>
      </view>
    </view>

    <view class="main-content">
      <!-- 搜索 + 筛选 -->
      <view class="search-bar animate-fade-up">
        <view class="search-input-wrap">
          <text class="material-symbols-outlined search-icon">search</text>
          <input
            v-model="keyword"
            class="search-input"
            placeholder="搜索学号或姓名"
            confirm-type="search"
            @confirm="reload"
          />
        </view>
      </view>

      <view class="filter-row animate-fade-up delay-1">
        <view
          v-for="r in roleFilters"
          :key="r.value"
          class="filter-chip"
          :class="{ 'filter-chip--active': roleFilter === r.value }"
          @click="setRole(r.value)"
        >
          <text class="chip-text">{{ r.label }}</text>
        </view>
      </view>

      <view class="filter-row filter-row--pilot animate-fade-up delay-1">
        <view class="filter-toggle" @click="showPilot = !showPilot">
          <text class="material-symbols-outlined toggle-icon" :class="{ active: showPilot }">
            {{ showPilot ? 'check_box' : 'check_box_outline_blank' }}
          </text>
          <text class="toggle-text">显示内测访客（{{ pilotCount }}）</text>
        </view>
      </view>

      <!-- 统计 -->
      <view class="count-bar animate-fade-up delay-1">
        <text class="count-text">共 {{ total }} 人</text>
      </view>

      <!-- 列表 -->
      <view v-if="loading" class="loading-wrap">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="visibleUsers.length === 0" class="empty-wrap">
        <text class="material-symbols-outlined empty-icon">person_off</text>
        <text class="empty-text">暂无用户</text>
      </view>

      <view v-else class="user-list">
        <view
          v-for="u in visibleUsers"
          :key="u.id"
          class="user-card animate-fade-up"
        >
          <view class="user-info">
            <view class="user-top">
              <text class="user-name">{{ u.name }}</text>
              <view class="role-badge" :class="'role-' + u.role">
                <text class="role-text">{{ roleLabel(u.role) }}</text>
              </view>
              <view v-if="!u.is_active" class="disabled-badge">
                <text class="disabled-text">已禁用</text>
              </view>
            </view>
            <view class="user-staff-id-row">
              <text class="user-staff-id">{{ u.staff_id }}</text>
              <view v-if="isPilotUser(u)" class="pilot-badge">
                内测
              </view>
            </view>
            <text class="user-org">{{ u.college_name || '' }}{{ u.class_name ? ' / ' + u.class_name : '' }}</text>
          </view>
          <view class="user-actions">
            <view class="action-btn" @click="handleResetPwd(u)">
              <text class="material-symbols-outlined action-icon">lock_reset</text>
            </view>
            <view class="action-btn" :class="{ 'action-btn--danger': u.is_active }" @click="handleToggle(u)">
              <text class="material-symbols-outlined action-icon">{{ u.is_active ? 'block' : 'check_circle' }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 分页 -->
      <view v-if="total > pageSize" class="pagination">
        <view class="page-btn" :class="{ 'page-btn--disabled': page <= 1 }" @click="prevPage">
          <text class="material-symbols-outlined">chevron_left</text>
        </view>
        <text class="page-info">{{ page }} / {{ totalPages }}</text>
        <view class="page-btn" :class="{ 'page-btn--disabled': page >= totalPages }" @click="nextPage">
          <text class="material-symbols-outlined">chevron_right</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getUsers, resetPassword, toggleActive, type AdminUserItem } from '@/api/admin'

const keyword = ref('')
const roleFilter = ref('')
const page = ref(1)
const pageSize = 20
const total = ref(0)
const users = ref<AdminUserItem[]>([])
const loading = ref(false)
const showPilot = ref(false)

const roleFilters = [
  { label: '全部', value: '' },
  { label: '学生', value: 'student' },
  { label: '教师', value: 'teacher' },
  { label: '管理员', value: 'admin' },
]

const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

const isPilotUser = (user: Pick<AdminUserItem, 'staff_id'>) =>
  (user.staff_id || '').toLowerCase().startsWith('pilot:')

const visibleUsers = computed(() => {
  if (showPilot.value) return users.value
  return users.value.filter((u) => !isPilotUser(u))
})

const pilotCount = computed(() =>
  users.value.filter((u) => isPilotUser(u)).length
)

const roleLabel = (role: string) => {
  const map: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' }
  return map[role] || role
}

const loadUsers = async () => {
  loading.value = true
  try {
    const res = await getUsers({
      page: page.value,
      size: pageSize,
      role: roleFilter.value || undefined,
      keyword: keyword.value || undefined,
    })
    users.value = res.items
    total.value = res.total
  } catch (e) {
    console.error('加载用户失败', e)
  } finally {
    loading.value = false
  }
}

const reload = () => {
  page.value = 1
  loadUsers()
}

const setRole = (role: string) => {
  roleFilter.value = role
  reload()
}

const prevPage = () => {
  if (page.value > 1) { page.value--; loadUsers() }
}

const nextPage = () => {
  if (page.value < totalPages.value) { page.value++; loadUsers() }
}

const handleResetPwd = async (u: AdminUserItem) => {
  uni.showModal({
    title: '重置密码',
    content: `确认将 ${u.name}(${u.staff_id}) 的密码重置为学号？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        await resetPassword(u.id)
        uni.showToast({ title: '已重置', icon: 'success' })
      } catch (e) {
        console.error(e)
      }
    }
  })
}

const handleToggle = async (u: AdminUserItem) => {
  const action = u.is_active ? '禁用' : '启用'
  uni.showModal({
    title: `${action}用户`,
    content: `确认${action} ${u.name}(${u.staff_id})？`,
    success: async (res) => {
      if (!res.confirm) return
      try {
        const result = await toggleActive(u.id)
        u.is_active = result.is_active
        uni.showToast({ title: `已${action}`, icon: 'success' })
      } catch (e) {
        console.error(e)
      }
    }
  })
}

const goImport = () => {
  uni.navigateTo({ url: '/pages/admin/import' })
}

const handleBack = () => {
  uni.navigateBack()
}

onMounted(() => {
  loadUsers()
})
</script>

<style scoped lang="scss">
// 全部对齐 MD3 tonal palette / 8pt grid / 大半径 / no-shadow-as-default
// 标杆：dashboard/index.vue + 学生端 tokens.scss

.admin-users-page {
  min-height: 100vh;
  background: $background;
}

.custom-app-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba($surface-container-lowest, 0.8);   // glass，与 dashboard custom-app-bar 一致
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
}
.app-bar-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: $space-3 $space-4;
  padding-top: calc(env(safe-area-inset-top) + #{$space-3});
}
.app-bar-left {
  display: flex;
  align-items: center;
  gap: $space-2;
}
.app-bar-right { display: flex; align-items: center; }
.app-bar-icon {
  font-size: 24px;
  color: $on-surface;
}
.app-bar-icon--primary { color: $primary; }
.app-bar-title {
  font-family: $font-headline;
  font-size: 18px;
  font-weight: 700;
  color: $on-surface;
}

.main-content {
  padding: $space-2 $space-5 $space-8;
}

// ── Search ──
.search-bar { margin-bottom: $space-3; }
.search-input-wrap {
  display: flex;
  align-items: center;
  background: $surface-container;                     // No-Line: 用 L2 tonal 替代白底+灰阴影
  border-radius: $radius-md;
  padding: $space-2 $space-3;
}
.search-icon {
  font-size: 20px;
  color: $on-surface-variant;
  margin-right: $space-2;
}
.search-input {
  flex: 1;
  font-size: 14px;
  border: none;
  background: none;
  color: $on-surface;
}

// ── Filter chips ──
.filter-row {
  display: flex;
  gap: $space-2;
  margin-bottom: $space-3;
  flex-wrap: wrap;
}
.filter-chip {
  padding: $space-2 $space-4;
  border-radius: $radius-full;
  background: $surface-container-low;                 // No-Line: 不要 1px solid
  transition: background 0.2s ease, transform 0.2s ease;

  &:active { transform: scale(0.97); }
}
.filter-chip--active {
  background: $primary;
  box-shadow: 0 8px 16px -4px rgba($primary, 0.2);
}
.filter-chip--active .chip-text { color: $on-primary; }
.chip-text {
  font-size: 12px;
  font-weight: 600;
  color: $on-surface-variant;
}

// ── Pilot toggle ──
.filter-row--pilot { margin-bottom: $space-2; }
.filter-toggle {
  display: inline-flex;
  align-items: center;
  gap: $space-1;
  padding: $space-1 $space-2;
}
.toggle-icon {
  font-size: 18px;
  color: $on-surface-variant;
}
.toggle-icon.active { color: $primary; }
.toggle-text {
  font-size: 13px;
  color: $on-surface-variant;
}

// ── Count bar ──
.count-bar { margin-bottom: $space-3; }
.count-text {
  font-size: 12px;
  color: $on-surface-variant;
}

// ── Loading / Empty ──
.loading-wrap,
.empty-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $space-12 0;
  background: $surface-container-low;                 // 与 dashboard empty-container 风格一致
  border-radius: $radius-md;
}
.loading-text,
.empty-text {
  font-size: 14px;
  color: $on-surface-variant;
}
.empty-icon {
  font-size: 48px;
  color: $outline-variant;
  margin-bottom: $space-2;
}

// ── User card ──
.user-list {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}
.user-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: $surface-container-lowest;
  border-radius: $radius-md;
  padding: $space-4 $space-4;
  box-shadow: $elevation-1;                           // [CA957F5] 双层紫折射，让卡片悬浮
  transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;

  &:active {
    transform: scale(0.99);
    background: $surface-container-low;
    box-shadow: $elevation-2;
  }
}
.user-info { flex: 1; min-width: 0; }
.user-top {
  display: flex;
  align-items: center;
  gap: $space-2;
  margin-bottom: $space-1;
}
.user-name {
  font-size: 15px;
  font-weight: 700;
  color: $on-surface;
}

// ── Role / status badges ──
// 用 MD3 container tier 颜色，pill 化，no-line
.role-badge {
  padding: 2px $space-2;
  border-radius: $radius-full;
}
.role-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
}
.role-student {
  background: $secondary-container;
  .role-text { color: $on-secondary-container; }
}
.role-teacher {
  background: rgba($success, 0.16);
  .role-text { color: $success; }
}
.role-admin {
  background: rgba($warning, 0.16);
  .role-text { color: $warning; }
}

.disabled-badge {
  padding: 2px $space-2;
  border-radius: $radius-full;
  background: rgba($error-container, 0.4);
}
.disabled-text {
  font-size: 10px;
  font-weight: 700;
  color: $error;
}

.user-staff-id-row {
  display: flex;
  align-items: center;
  gap: $space-2;
}
.user-staff-id {
  font-size: 12px;
  color: $on-surface-variant;
  display: block;
  font-family: $font-body;
}
.pilot-badge {
  display: inline-block;
  padding: 2px $space-1;
  border-radius: $radius-sm;
  background: rgba($warning, 0.16);
  color: $warning;
  font-size: 10px;
  font-weight: 600;
  line-height: 1;
}
.user-org {
  font-size: 11px;
  color: $on-surface-variant;
  display: block;
  margin-top: 2px;
}

// ── Actions ──
.user-actions {
  display: flex;
  gap: $space-2;
  flex-shrink: 0;
  margin-left: $space-2;
}
.action-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-sm;
  background: $surface-container;
  color: $on-surface-variant;                         // icon currentColor

  &:active {
    background: $surface-container-high;
    transform: scale(0.95);
  }
}
.action-btn--danger {
  background: rgba($error-container, 0.4);
  color: $error;
}
.action-icon {
  font-size: 18px;
  color: inherit;                                     // 沿用 .action-btn 的 color
}

// ── Pagination ──
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-4;
  padding: $space-4 0;
}
.page-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-sm;
  background: $surface-container-lowest;
  color: $on-surface;
  box-shadow: $elevation-1;

  &:active { transform: scale(0.95); }
}
.page-btn--disabled {
  opacity: 0.3;
  pointer-events: none;
}
.page-info {
  font-size: 13px;
  color: $on-surface-variant;
  font-weight: 600;
}

// ── Animation ──
.animate-fade-up { animation: fadeUp 0.3s ease-out both; }
.delay-1 { animation-delay: 0.05s; }
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
