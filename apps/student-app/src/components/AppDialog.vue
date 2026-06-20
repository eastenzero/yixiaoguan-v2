<template>
  <view v-if="dialog.state.visible" class="dialog-overlay" @click="dialog.close(false)">
    <view class="dialog-card" @click.stop>
      <view v-if="dialog.state.icon" class="dialog-icon-wrap">
        <AppIcon :name="dialog.state.icon" class="dialog-icon" />
      </view>

      <text class="dialog-title">{{ dialog.state.title }}</text>
      <text class="dialog-content">{{ dialog.state.content }}</text>

      <view class="dialog-actions" :class="{ 'single': dialog.state.mode === 'alert' }">
        <view
          v-if="dialog.state.mode === 'confirm'"
          class="dialog-btn btn-cancel"
          @click="dialog.close(false)"
        >
          <text class="btn-cancel-text">{{ dialog.state.cancelText }}</text>
        </view>
        <view
          class="dialog-btn btn-confirm"
          :class="{ 'btn-danger': dialog.state.confirmDanger }"
          @click="dialog.close(true)"
        >
          <text class="btn-confirm-text">{{ dialog.state.confirmText }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import { useDialog } from '@/composables/useDialog'

const dialog = useDialog()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.dialog-overlay {
  position: fixed;
  top: 0;
  right: var(--student-fixed-right, 0);
  bottom: 0;
  left: var(--student-fixed-left, 0);
  z-index: $z-modal;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $space-8;
  animation: fade-in 0.2s ease;
}

.dialog-card {
  width: 100%;
  max-width: 320px;
  background: $surface-container-lowest;
  border-radius: $radius-lg;
  padding: $space-8 $space-6 $space-6;
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: scale-in 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}

.dialog-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: $radius-full;
  background: rgba($primary, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-4;
}

.dialog-icon {
  font-size: 28px;
  color: $primary;
}

.dialog-title {
  font-family: $font-headline;
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $on-surface;
  text-align: center;
  margin-bottom: $space-2;
}

.dialog-content {
  font-size: $body-md-size;
  font-weight: $font-weight-medium;
  color: $on-surface-variant;
  text-align: center;
  line-height: 1.6;
  white-space: pre-line;
  margin-bottom: $space-6;
  padding: 0 $space-2;
}

.dialog-actions {
  width: 100%;
  display: flex;
  gap: $space-3;

  &.single {
    flex-direction: column;
  }
}

.dialog-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $space-3 $space-4;
  border-radius: $radius-full;
  transition: transform 0.15s ease;

  &:active {
    transform: scale(0.97);
  }
}

.btn-cancel {
  background: $surface-container-low;

  &:active {
    background: $surface-container-high;
  }
}

.btn-cancel-text {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $on-surface-variant;
}

.btn-confirm {
  background: $primary;
}

.btn-confirm-text {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $on-primary;
}

.btn-danger {
  background: $error;
}

@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes scale-in {
  from { opacity: 0; transform: scale(0.9); }
  to { opacity: 1; transform: scale(1); }
}
</style>
