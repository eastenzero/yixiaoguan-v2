<template>
  <view class="import-page">
    <view class="custom-app-bar">
      <view class="app-bar-content">
        <view class="app-bar-left" @click="handleBack">
          <text class="material-symbols-outlined app-bar-icon">arrow_back</text>
          <text class="app-bar-title">批量导入用户</text>
        </view>
      </view>
    </view>

    <view class="main-content">
      <!-- 步骤提示 -->
      <view class="tips-card animate-fade-up">
        <text class="material-symbols-outlined tips-icon">info</text>
        <view class="tips-content">
          <text class="tips-title">导入格式说明</text>
          <text class="tips-text">1. 请输入 JSON 格式的用户列表</text>
          <text class="tips-text">2. 每个用户包含 staff_id（学号）和 name（姓名）</text>
          <text class="tips-text">3. 初始密码默认为学号，可后续重置</text>
          <text class="tips-text">4. 已存在的学号会自动跳过</text>
        </view>
      </view>

      <!-- 角色选择 -->
      <view class="form-section animate-fade-up delay-1">
        <text class="form-label">用户角色</text>
        <view class="role-selector">
          <view
            v-for="r in roles"
            :key="r.value"
            class="role-option"
            :class="{ 'role-option--active': role === r.value }"
            @click="role = r.value"
          >
            <text class="role-option-text">{{ r.label }}</text>
          </view>
        </view>
      </view>

      <!-- 学院 ID -->
      <view class="form-section animate-fade-up delay-1">
        <text class="form-label">学院 ID</text>
        <input v-model="collegeId" class="form-input" type="number" placeholder="如 17" />
      </view>

      <!-- 班级 ID -->
      <view class="form-section animate-fade-up delay-1">
        <text class="form-label">班级 ID（可选）</text>
        <input v-model="classId" class="form-input" type="number" placeholder="留空则不绑定班级" />
      </view>

      <!-- JSON 输入 -->
      <view class="form-section animate-fade-up delay-2">
        <text class="form-label">用户数据 (JSON)</text>
        <textarea
          v-model="jsonInput"
          class="json-textarea"
          :placeholder="placeholder"
          :maxlength="-1"
        />
      </view>

      <!-- 预览 -->
      <view v-if="parsedUsers.length > 0" class="preview-section animate-fade-up">
        <text class="preview-title">预览：{{ parsedUsers.length }} 条记录</text>
        <view class="preview-list">
          <view v-for="(u, i) in parsedUsers.slice(0, 5)" :key="i" class="preview-item">
            <text class="preview-sid">{{ u.staff_id }}</text>
            <text class="preview-name">{{ u.name }}</text>
          </view>
          <text v-if="parsedUsers.length > 5" class="preview-more">...还有 {{ parsedUsers.length - 5 }} 条</text>
        </view>
      </view>

      <view v-if="parseError" class="error-bar">
        <text class="material-symbols-outlined error-icon">error</text>
        <text class="error-text">{{ parseError }}</text>
      </view>

      <!-- 导入按钮 -->
      <view class="submit-section animate-fade-up delay-2">
        <view
          class="submit-btn"
          :class="{ 'submit-btn--disabled': !canSubmit || submitting }"
          @click="handleSubmit"
        >
          <text v-if="submitting" class="submit-text">导入中...</text>
          <text v-else class="submit-text">确认导入</text>
        </view>
      </view>

      <!-- 结果 -->
      <view v-if="result" class="result-card animate-fade-up">
        <text class="material-symbols-outlined result-icon">check_circle</text>
        <text class="result-text">成功创建 {{ result.created }} 人，跳过 {{ result.skipped }} 人</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { batchImport, type BatchImportResponse } from '@/api/admin'

const role = ref('student')
const collegeId = ref('')
const classId = ref('')
const jsonInput = ref('')
const submitting = ref(false)
const result = ref<BatchImportResponse | null>(null)
const parseError = ref('')

const roles = [
  { label: '学生', value: 'student' },
  { label: '教师', value: 'teacher' },
]

const placeholder = `[
  { "staff_id": "4125150001", "name": "张三" },
  { "staff_id": "4125150002", "name": "李四" }
]`

const parsedUsers = computed(() => {
  parseError.value = ''
  if (!jsonInput.value.trim()) return []
  try {
    const arr = JSON.parse(jsonInput.value.trim())
    if (!Array.isArray(arr)) { parseError.value = 'JSON 必须是数组格式'; return [] }
    for (const item of arr) {
      if (!item.staff_id || !item.name) { parseError.value = '每条记录需包含 staff_id 和 name'; return [] }
    }
    return arr as { staff_id: string; name: string }[]
  } catch (e: any) {
    parseError.value = 'JSON 解析失败：' + (e.message || '')
    return []
  }
})

const canSubmit = computed(() => {
  return parsedUsers.value.length > 0 && collegeId.value && !parseError.value
})

const handleSubmit = async () => {
  if (!canSubmit.value || submitting.value) return
  result.value = null
  submitting.value = true
  try {
    const res = await batchImport({
      college_id: parseInt(collegeId.value),
      class_id: classId.value ? parseInt(classId.value) : null,
      role: role.value,
      users: parsedUsers.value,
    })
    result.value = res
    uni.showToast({ title: `创建 ${res.created} 人`, icon: 'success' })
  } catch (e) {
    console.error('导入失败', e)
  } finally {
    submitting.value = false
  }
}

const handleBack = () => {
  uni.navigateBack()
}
</script>

<style scoped>
.import-page { min-height: 100vh; background: #faf5fb; }
.custom-app-bar { position: sticky; top: 0; z-index: 100; background: rgba(250, 245, 251, 0.95); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px); }
.app-bar-content { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1rem; padding-top: calc(env(safe-area-inset-top) + 0.75rem); }
.app-bar-left { display: flex; align-items: center; gap: 0.5rem; }
.app-bar-icon { font-size: 1.5rem; color: #5d5b5f; }
.app-bar-title { font-size: 1.125rem; font-weight: 700; color: #191c1e; }
.main-content { padding: 0.5rem 1rem 2rem; }

.tips-card { display: flex; gap: 0.75rem; background: #eff6ff; border-radius: 0.75rem; padding: 1rem; margin-bottom: 1rem; }
.tips-icon { font-size: 1.25rem; color: #3b82f6; flex-shrink: 0; }
.tips-content { display: flex; flex-direction: column; gap: 0.25rem; }
.tips-title { font-size: 0.8125rem; font-weight: 700; color: #1e40af; }
.tips-text { font-size: 0.75rem; color: #3b82f6; }

.form-section { margin-bottom: 1rem; }
.form-label { font-size: 0.8125rem; font-weight: 700; color: #374151; margin-bottom: 0.375rem; display: block; }
.form-input { width: 100%; padding: 0.625rem 0.875rem; background: #fff; border: 1px solid #e2e8f0; border-radius: 0.625rem; font-size: 0.875rem; box-sizing: border-box; }

.role-selector { display: flex; gap: 0.5rem; }
.role-option { padding: 0.5rem 1rem; border-radius: 0.625rem; background: #fff; border: 1px solid #e2e8f0; }
.role-option--active { background: #702ae1; border-color: #702ae1; }
.role-option--active .role-option-text { color: #fff; }
.role-option-text { font-size: 0.8125rem; font-weight: 600; color: #64748b; }

.json-textarea { width: 100%; min-height: 10rem; padding: 0.75rem; background: #fff; border: 1px solid #e2e8f0; border-radius: 0.625rem; font-size: 0.8125rem; font-family: monospace; line-height: 1.6; box-sizing: border-box; }

.preview-section { background: #f0fdf4; border-radius: 0.75rem; padding: 0.75rem; margin-bottom: 1rem; }
.preview-title { font-size: 0.8125rem; font-weight: 700; color: #16a34a; margin-bottom: 0.5rem; display: block; }
.preview-list { display: flex; flex-direction: column; gap: 0.25rem; }
.preview-item { display: flex; gap: 0.75rem; }
.preview-sid { font-size: 0.75rem; color: #64748b; font-family: monospace; }
.preview-name { font-size: 0.75rem; color: #374151; font-weight: 600; }
.preview-more { font-size: 0.75rem; color: #94a3b8; margin-top: 0.25rem; }

.error-bar { display: flex; align-items: center; gap: 0.375rem; background: #fef2f2; border-radius: 0.625rem; padding: 0.625rem 0.75rem; margin-bottom: 1rem; }
.error-icon { font-size: 1.125rem; color: #ef4444; }
.error-text { font-size: 0.8125rem; color: #dc2626; }

.submit-section { margin-top: 0.5rem; margin-bottom: 1rem; }
.submit-btn { display: flex; align-items: center; justify-content: center; padding: 0.875rem; background: linear-gradient(135deg, #702ae1, #9333ea); border-radius: 0.75rem; box-shadow: 0 4px 12px rgba(112, 42, 225, 0.3); }
.submit-btn--disabled { opacity: 0.4; }
.submit-text { font-size: 0.9375rem; font-weight: 700; color: #fff; }

.result-card { display: flex; align-items: center; gap: 0.5rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 0.75rem; padding: 1rem; }
.result-icon { font-size: 1.5rem; color: #16a34a; }
.result-text { font-size: 0.875rem; font-weight: 600; color: #16a34a; }

.animate-fade-up { animation: fadeUp 0.3s ease-out both; }
.delay-1 { animation-delay: 0.05s; }
.delay-2 { animation-delay: 0.1s; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
