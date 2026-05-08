<template>
  <view v-if="props.visible" class="drawer-mask" @click.self="onClose">
    <view class="drawer-panel">
      <view class="drawer-handle" />

      <view class="drawer-header">
        <text class="drawer-title">意见反馈</text>
        <text class="material-symbols-outlined drawer-close" @click="onClose">close</text>
      </view>

      <text class="drawer-desc">遇到问题、有建议或想吐槽，都可以告诉我们。我们会认真看每一条。</text>

      <textarea
        v-model="content"
        class="drawer-textarea"
        maxlength="2000"
        placeholder="说说你的意见或建议..."
      />

      <text class="field-label">联系方式（可选）</text>
      <input
        v-model="contact"
        class="drawer-input"
        maxlength="120"
        placeholder="QQ / 微信 / 邮箱（如希望我们回复）"
      />

      <view class="drawer-actions">
        <button class="btn-secondary" :disabled="submitting" @click="onClose">取消</button>
        <button class="btn-primary" :disabled="!canSubmit || submitting" @click="onSubmit">
          {{ submitting ? '提交中...' : '提交' }}
        </button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { submitGeneralFeedback } from '@/api/feedback'
import { getDeviceId } from '@/utils/device'
import { trackEvent } from '@/utils/track'

const props = defineProps<{ visible: boolean }>()

const emit = defineEmits<{
  (e: 'update:visible', value: boolean): void
  (e: 'submitted'): void
}>()

const content = ref('')
const contact = ref('')
const submitting = ref(false)

const canSubmit = computed(() => content.value.trim().length > 0)

watch(
  () => props.visible,
  visible => {
    if (!visible) return
    content.value = ''
    contact.value = ''
    trackEvent('feedback_drawer_opened')
  }
)

function onClose() {
  emit('update:visible', false)
}

async function onSubmit() {
  if (!canSubmit.value || submitting.value) return

  submitting.value = true

  try {
    await submitGeneralFeedback({
      content: content.value.trim(),
      contact: contact.value.trim() || undefined,
      device_id: getDeviceId(),
    })

    trackEvent('feedback_submitted', {
      has_contact: contact.value.trim().length > 0,
    })

    uni.showToast({ title: '感谢反馈', icon: 'success' })
    emit('submitted')
    emit('update:visible', false)
  } catch (error: any) {
    uni.showToast({ title: error?.message || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.drawer-mask {
  position: fixed;
  inset: 0;
  z-index: $z-modal;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: fade-in 0.2s ease;
}

.drawer-panel {
  width: 100%;
  max-width: 480px;
  background: $surface-container-lowest;
  border-radius: $radius-xl $radius-xl 0 0;
  padding: $space-3 $space-6 calc(env(safe-area-inset-bottom, 0px) + $space-6);
  animation: slide-up 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}

.drawer-handle {
  width: 32px;
  height: 4px;
  border-radius: $radius-full;
  background: $outline-variant;
  margin: 0 auto $space-5;
}

.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $space-3;
}

.drawer-title {
  font-family: $font-headline;
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
}

.drawer-close {
  font-size: 22px;
  color: $text-secondary;
}

.drawer-desc {
  display: block;
  margin-top: $space-2;
  font-size: $font-size-sm;
  line-height: 1.65;
  color: $text-secondary;
}

.drawer-textarea,
.drawer-input {
  width: 100%;
  box-sizing: border-box;
  border-radius: $radius-md;
  background: $surface-container-low;
  color: $text-primary;
  font-size: $font-size-sm;
}

.drawer-textarea {
  min-height: 156px;
  margin-top: $space-5;
  padding: $space-4;
  line-height: 1.65;
}

.field-label {
  display: block;
  margin-top: $space-4;
  margin-bottom: $space-2;
  font-size: $font-size-xs;
  font-weight: $font-weight-bold;
  color: $text-secondary;
}

.drawer-input {
  min-height: 44px;
  padding: 0 $space-4;
}

.drawer-actions {
  display: flex;
  gap: $space-3;
  margin-top: $space-6;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  min-height: 48px;
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

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slide-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
</style>
