<template>
  <view class="invite-card">
    <view class="invite-header">
      <view class="invite-icon-wrap">
        <text class="material-symbols-outlined invite-icon">help</text>
      </view>
      <text class="invite-title">这次回答没帮到你？告诉我们一些信息，让医小管做得更好</text>
    </view>

    <text class="invite-desc">学院 / 年级 / 类别 都可选填，不会泄露给其他同学。</text>

    <text class="field-label">你所在的学院</text>
    <picker mode="selector" :range="pickerOptions" range-key="label" @change="onCollegePick">
      <view class="picker-display" :class="{ placeholder: !selectedCollegeName }">
        <text>{{ selectedCollegeName || '请选择（可选）' }}</text>
        <text class="material-symbols-outlined picker-icon">expand_more</text>
      </view>
    </picker>

    <text class="field-label">你的年级</text>
    <scroll-view class="chip-scroll" scroll-x>
      <view class="chip-row">
        <view
          v-for="grade in GRADES"
          :key="grade.value"
          class="chip"
          :class="{ active: selectedGrade === grade.value }"
          @click="toggleGrade(grade.value)"
        >
          <text class="chip-text">{{ grade.label }}</text>
        </view>
      </view>
    </scroll-view>

    <text class="field-label">问题类别</text>
    <scroll-view class="chip-scroll" scroll-x>
      <view class="chip-row">
        <view
          v-for="category in CATEGORIES"
          :key="category.value"
          class="chip"
          :class="{ active: selectedCategory === category.value }"
          @click="toggleCategory(category.value)"
        >
          <text class="chip-text">{{ category.label }}</text>
        </view>
      </view>
    </scroll-view>

    <text class="field-label">补充说明（可选）</text>
    <textarea
      v-model="note"
      class="note-input"
      maxlength="300"
      placeholder="比如：希望医小管能告诉我 XX..."
    />

    <view class="invite-actions">
      <button class="btn-secondary" :disabled="submitting" @click="onDismiss">以后再说</button>
      <button class="btn-primary" :disabled="!canSubmit || submitting" @click="onSubmit">
        {{ submitting ? '提交中...' : '提交' }}
      </button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listColleges, type CollegeOption } from '@/api/college'
import { submitUnansweredFeedback } from '@/api/feedback'
import { trackEvent } from '@/utils/track'

const props = defineProps<{ conv_id: number; message_id: number }>()

const emit = defineEmits<{
  (e: 'submitted'): void
  (e: 'dismissed'): void
}>()

const GRADES = [
  { value: 'grade_1', label: '大一' },
  { value: 'grade_2', label: '大二' },
  { value: 'grade_3', label: '大三' },
  { value: 'grade_4', label: '大四' },
  { value: 'grad', label: '研究生' },
  { value: 'other', label: '其他' },
] as const

const CATEGORIES = [
  { value: 'scholarship', label: '奖助学金' },
  { value: 'course', label: '课程教务' },
  { value: 'registration', label: '学籍手续' },
  { value: 'dorm', label: '宿舍生活' },
  { value: 'medical', label: '医疗保健' },
  { value: 'network', label: '校园网络' },
  { value: 'activity', label: '活动赛事' },
  { value: 'other', label: '其他' },
] as const

type GradeValue = typeof GRADES[number]['value']
type CategoryValue = typeof CATEGORIES[number]['value']

const colleges = ref<CollegeOption[]>([])
const selectedCollegeId = ref<number | null>(null)
const selectedGrade = ref<GradeValue | null>(null)
const selectedCategory = ref<CategoryValue | null>(null)
const note = ref('')
const submitting = ref(false)

const pickerOptions = computed(() =>
  colleges.value.map(college => ({
    ...college,
    label: college.campus ? `${college.name}（${college.campus}）` : college.name,
  }))
)

const selectedCollegeName = computed(() => {
  if (!selectedCollegeId.value) return ''
  return pickerOptions.value.find(college => college.id === selectedCollegeId.value)?.label || ''
})

const canSubmit = computed(() => {
  return Boolean(
    selectedCollegeId.value ||
    selectedGrade.value ||
    selectedCategory.value ||
    note.value.trim()
  )
})

onMounted(async () => {
  try {
    colleges.value = await listColleges()
  } catch {
    colleges.value = []
  }
})

function onCollegePick(event: any) {
  const index = Number(event?.detail?.value)
  if (index >= 0 && index < pickerOptions.value.length) {
    selectedCollegeId.value = pickerOptions.value[index].id
  }
}

function toggleGrade(value: GradeValue) {
  selectedGrade.value = selectedGrade.value === value ? null : value
}

function toggleCategory(value: CategoryValue) {
  selectedCategory.value = selectedCategory.value === value ? null : value
}

async function onSubmit() {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true

  try {
    await submitUnansweredFeedback({
      conv_id: props.conv_id,
      message_id: props.message_id,
      college_id: selectedCollegeId.value,
      grade: selectedGrade.value,
      category: selectedCategory.value,
      note: note.value.trim() || null,
    })

    trackEvent('unanswered_invite_submitted', {
      conv_id: props.conv_id,
      message_id: props.message_id,
      has_college: Boolean(selectedCollegeId.value),
      has_grade: Boolean(selectedGrade.value),
      has_category: Boolean(selectedCategory.value),
      has_note: note.value.trim().length > 0,
    })

    uni.showToast({ title: '感谢你的反馈', icon: 'success' })
    emit('submitted')
  } catch (error: any) {
    uni.showToast({ title: error?.message || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function onDismiss() {
  trackEvent('unanswered_invite_dismissed', {
    conv_id: props.conv_id,
    message_id: props.message_id,
  })
  emit('dismissed')
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.invite-card {
  margin-top: $space-4;
  padding: $space-5;
  border-radius: $radius-lg;
  background: $surface-container-lowest;
  box-shadow: 0 12px 32px rgba(91, 33, 182, 0.08);
}

.invite-header {
  display: flex;
  align-items: flex-start;
  gap: $space-3;
}

.invite-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: $radius-full;
  background: rgba($primary, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.invite-icon {
  font-size: 18px;
  color: $primary;
  font-variation-settings: 'FILL' 1, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}

.invite-title {
  flex: 1;
  font-size: $font-size-base;
  line-height: 1.55;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.invite-desc {
  display: block;
  margin-top: $space-3;
  font-size: $font-size-sm;
  line-height: 1.6;
  color: $text-secondary;
}

.field-label {
  display: block;
  margin-top: $space-4;
  margin-bottom: $space-2;
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $text-secondary;
}

.picker-display {
  min-height: 44px;
  border-radius: $radius-md;
  background: $surface-container-low;
  padding: 0 $space-4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $space-2;
  color: $text-primary;
}

.picker-display.placeholder {
  color: $text-muted;
}

.picker-icon {
  font-size: 18px;
  color: $text-muted;
}

.chip-scroll {
  width: 100%;
  white-space: nowrap;
}

.chip-row {
  display: inline-flex;
  gap: $space-2;
  min-width: 100%;
}

.chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 36px;
  padding: 0 $space-4;
  border-radius: $radius-full;
  background: $surface-container-low;
  color: $text-secondary;
}

.chip.active {
  background: $primary;
  color: $on-primary;
}

.chip-text {
  font-size: $font-size-sm;
  font-weight: $font-weight-semibold;
  white-space: nowrap;
}

.note-input {
  width: 100%;
  min-height: 92px;
  margin-top: 0;
  padding: $space-4;
  border-radius: $radius-md;
  background: $surface-container-low;
  color: $text-primary;
  font-size: $font-size-sm;
  line-height: 1.6;
  box-sizing: border-box;
}

.invite-actions {
  display: flex;
  justify-content: flex-end;
  gap: $space-3;
  margin-top: $space-5;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  min-height: 44px;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-sm;
  font-weight: $font-weight-bold;
}

.btn-primary {
  background: $primary;
  color: $on-primary;
}

.btn-primary[disabled] {
  opacity: 0.5;
}

.btn-secondary {
  background: $surface-container-low;
  color: $text-secondary;
}
</style>
