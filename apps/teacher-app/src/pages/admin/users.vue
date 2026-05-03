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

      <!-- 统计 -->
      <view class="count-bar animate-fade-up delay-1">
        <text class="count-text">共 {{ total }} 人</text>
      </view>

      <!-- 列表 -->
      <view v-if="loading" class="loading-wrap">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="users.length === 0" class="empty-wrap">
        <text class="material-symbols-outlined empty-icon">person_off</text>
        <text class="empty-text">暂无用户</text>
      </view>

      <view v-else class="user-list">
        <view
          v-for="u in users"
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
            <text class="user-staff-id">{{ u.staff_id }}</text>
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

const roleFilters = [
  { label: '全部', value: '' },
  { label: '学生', value: 'student' },
  { label: '教师', value: 'teacher' },
  { label: '管理员', value: 'admin' },
]

const totalPages = computed(() => Math.ceil(total.value / pageSize) || 1)

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

<style scoped>
.admin-users-page { min-height: 100vh; background: #faf5fb; }
.custom-app-bar { position: sticky; top: 0; z-index: 100; background: rgba(250, 245, 251, 0.95); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
.app-bar-content { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; padding-top: calc(env(safe-area-inset-top) + 0.75rem); }
.app-bar-left { display: flex; align-items: center; gap: 0.5rem; }
.app-bar-right { display: flex; align-items: center; }
.app-bar-icon { font-size: 1.5rem; color: #5d5b5f; }
.app-bar-icon--primary { color: #702ae1; }
.app-bar-title { font-size: 1.125rem; font-weight: 700; color: #191c1e; }
.main-content { padding: 0.5rem 1rem 2rem; }

.search-bar { margin-bottom: 0.75rem; }
.search-input-wrap { display: flex; align-items: center; background: #fff; border-radius: 0.75rem; padding: 0.5rem 0.75rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.search-icon { font-size: 1.25rem; color: #94a3b8; margin-right: 0.5rem; }
.search-input { flex: 1; font-size: 0.875rem; border: none; background: none; }

.filter-row { display: flex; gap: 0.5rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.filter-chip { padding: 0.375rem 0.875rem; border-radius: 1rem; background: #fff; border: 1px solid #e2e8f0; }
.filter-chip--active { background: #702ae1; border-color: #702ae1; }
.filter-chip--active .chip-text { color: #fff; }
.chip-text { font-size: 0.75rem; font-weight: 600; color: #64748b; }

.count-bar { margin-bottom: 0.75rem; }
.count-text { font-size: 0.75rem; color: #94a3b8; }

.loading-wrap, .empty-wrap { display: flex; flex-direction: column; align-items: center; padding: 3rem 0; }
.loading-text { font-size: 0.875rem; color: #94a3b8; }
.empty-icon { font-size: 3rem; color: #cbd5e1; margin-bottom: 0.5rem; }
.empty-text { font-size: 0.875rem; color: #94a3b8; }

.user-list { display: flex; flex-direction: column; gap: 0.5rem; }
.user-card { display: flex; justify-content: space-between; align-items: center; background: #fff; border-radius: 0.75rem; padding: 0.875rem 1rem; box-shadow: 0 1px 4px rgba(0,0,0,0.04); }
.user-info { flex: 1; min-width: 0; }
.user-top { display: flex; align-items: center; gap: 0.375rem; margin-bottom: 0.25rem; }
.user-name { font-size: 0.9375rem; font-weight: 700; color: #191c1e; }
.role-badge { padding: 0.125rem 0.5rem; border-radius: 0.5rem; }
.role-student { background: #ede9fe; }
.role-student .role-text { color: #7c3aed; }
.role-teacher { background: #dcfce7; }
.role-teacher .role-text { color: #16a34a; }
.role-admin { background: #fef3c7; }
.role-admin .role-text { color: #d97706; }
.role-text { font-size: 0.625rem; font-weight: 700; }
.disabled-badge { padding: 0.125rem 0.5rem; border-radius: 0.5rem; background: #fee2e2; }
.disabled-text { font-size: 0.625rem; font-weight: 700; color: #dc2626; }
.user-staff-id { font-size: 0.75rem; color: #64748b; display: block; }
.user-org { font-size: 0.6875rem; color: #94a3b8; display: block; margin-top: 0.125rem; }

.user-actions { display: flex; gap: 0.5rem; flex-shrink: 0; margin-left: 0.5rem; }
.action-btn { width: 2rem; height: 2rem; display: flex; align-items: center; justify-content: center; border-radius: 0.5rem; background: #f1f5f9; }
.action-btn:active { background: #e2e8f0; }
.action-btn--danger { background: #fef2f2; }
.action-icon { font-size: 1.125rem; color: #64748b; }
.action-btn--danger .action-icon { color: #ef4444; }

.pagination { display: flex; align-items: center; justify-content: center; gap: 1rem; padding: 1rem 0; }
.page-btn { width: 2rem; height: 2rem; display: flex; align-items: center; justify-content: center; border-radius: 0.5rem; background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.06); }
.page-btn--disabled { opacity: 0.3; }
.page-info { font-size: 0.8125rem; color: #64748b; font-weight: 600; }

.animate-fade-up { animation: fadeUp 0.3s ease-out both; }
.delay-1 { animation-delay: 0.05s; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
