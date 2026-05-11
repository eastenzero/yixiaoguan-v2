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

<style scoped lang="scss">
// 全部对齐 MD3 tonal palette / 8pt grid / 大半径 / no-shadow-as-default
// 标杆：dashboard/index.vue + admin/users.vue (本次同步重构)

.import-page {
  min-height: 100vh;
  background: $background;
}

.custom-app-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba($surface-container-lowest, 0.8);
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
.app-bar-icon {
  font-size: 24px;
  color: $on-surface;
}
.app-bar-title {
  font-family: $font-headline;
  font-size: 18px;
  font-weight: 700;
  color: $on-surface;
}

.main-content {
  padding: $space-2 $space-5 $space-8;
}

// ── Tips card ──
// info 色用 MD3 secondary-container（淡紫）替代 Tailwind blue，避免突兀
.tips-card {
  display: flex;
  gap: $space-3;
  background: $secondary-container;
  border-radius: $radius-md;
  padding: $space-4;
  margin-bottom: $space-4;
}
.tips-icon {
  font-size: 20px;
  color: $on-secondary-container;
  flex-shrink: 0;
}
.tips-content {
  display: flex;
  flex-direction: column;
  gap: $space-1;
}
.tips-title {
  font-size: 13px;
  font-weight: 700;
  color: $on-secondary-container;
}
.tips-text {
  font-size: 12px;
  color: rgba($on-secondary-container, 0.85);
  line-height: 1.6;
}

// ── Form ──
.form-section { margin-bottom: $space-4; }
.form-label {
  font-size: 13px;
  font-weight: 700;
  color: $on-surface;
  margin-bottom: $space-1;
  display: block;
}
.form-input {
  width: 100%;
  padding: $space-3 $space-4;
  background: $surface-container-low;                 // No-Line: tonal 替代白底+1px solid
  border: none;
  border-radius: $radius-md;
  font-size: 14px;
  color: $on-surface;
  box-sizing: border-box;
}

.role-selector {
  display: flex;
  gap: $space-2;
}
.role-option {
  padding: $space-2 $space-4;
  border-radius: $radius-md;
  background: $surface-container-low;
  transition: all 0.2s ease;

  &:active { transform: scale(0.97); }
}
.role-option--active {
  background: $primary;
  box-shadow: 0 8px 16px -4px rgba($primary, 0.2);
}
.role-option--active .role-option-text { color: $on-primary; }
.role-option-text {
  font-size: 13px;
  font-weight: 600;
  color: $on-surface-variant;
}

.json-textarea {
  width: 100%;
  min-height: 160px;
  padding: $space-3;
  background: $surface-container-low;
  border: none;
  border-radius: $radius-md;
  font-size: 13px;
  font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
  line-height: 1.6;
  color: $on-surface;
  box-sizing: border-box;
}

// ── Preview ──
.preview-section {
  background: rgba($success, 0.10);
  border-radius: $radius-md;
  padding: $space-3;
  margin-bottom: $space-4;
}
.preview-title {
  font-size: 13px;
  font-weight: 700;
  color: $success;
  margin-bottom: $space-2;
  display: block;
}
.preview-list {
  display: flex;
  flex-direction: column;
  gap: $space-1;
}
.preview-item {
  display: flex;
  gap: $space-3;
}
.preview-sid {
  font-size: 12px;
  color: $on-surface-variant;
  font-family: 'Menlo', 'Consolas', 'Courier New', monospace;
}
.preview-name {
  font-size: 12px;
  color: $on-surface;
  font-weight: 600;
}
.preview-more {
  font-size: 12px;
  color: $on-surface-variant;
  margin-top: $space-1;
}

// ── Error ──
.error-bar {
  display: flex;
  align-items: center;
  gap: $space-2;
  background: rgba($error-container, 0.4);
  border-radius: $radius-md;
  padding: $space-2 $space-3;
  margin-bottom: $space-4;
}
.error-icon {
  font-size: 18px;
  color: $error;
}
.error-text {
  font-size: 13px;
  color: $error;
}

// ── Submit ──
.submit-section {
  margin-top: $space-2;
  margin-bottom: $space-4;
}
.submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $space-3 $space-4;
  background: $gradient-cta;                          // signature CTA 渐变
  border-radius: $radius-full;                        // pill
  box-shadow: 0 8px 20px -4px rgba($primary, 0.3);
  transition: transform 0.2s ease;

  &:active {
    transform: scale(0.97);
  }
}
.submit-btn--disabled {
  opacity: 0.4;
  pointer-events: none;
}
.submit-text {
  font-size: 15px;
  font-weight: 700;
  color: $on-primary;
}

// ── Result ──
.result-card {
  display: flex;
  align-items: center;
  gap: $space-2;
  background: rgba($success, 0.10);
  border-radius: $radius-md;
  padding: $space-4;                                  // No-Line: 去掉 1px solid
}
.result-icon {
  font-size: 24px;
  color: $success;
}
.result-text {
  font-size: 14px;
  font-weight: 600;
  color: $success;
}

// ── Animation ──
.animate-fade-up { animation: fadeUp 0.3s ease-out both; }
.delay-1 { animation-delay: 0.05s; }
.delay-2 { animation-delay: 0.1s; }
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
