<template>
  <view v-if="notice.state.visible" class="sheet-overlay" @click="notice.hide()">
    <view class="sheet-panel" @click.stop>
      <view class="sheet-handle" />

      <view class="sheet-icon-wrap">
        <text class="material-symbols-outlined sheet-icon">{{ notice.state.icon }}</text>
      </view>

      <text class="sheet-title">{{ notice.state.title }}</text>
      <text class="sheet-desc">{{ notice.state.description }}</text>

      <view class="sheet-actions">
        <view
          v-if="notice.state.suggestedQuestion"
          class="btn-primary"
          @click="notice.onPrimary()"
        >
          <text class="material-symbols-outlined btn-primary-icon">auto_awesome</text>
          <text class="btn-primary-text">{{ notice.state.primaryText }}</text>
        </view>
        <view class="btn-secondary" @click="notice.hide()">
          <text class="btn-secondary-text">{{ notice.state.secondaryText }}</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useFeatureNotice } from '@/composables/useFeatureNotice'

const notice = useFeatureNotice()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.sheet-overlay {
  position: fixed;
  inset: 0;
  z-index: $z-modal;
  background: rgba(0, 0, 0, 0.32);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: fade-in 0.2s ease;
}

.sheet-panel {
  width: 100%;
  max-width: 480px;
  background: $surface-container-lowest;
  border-radius: $radius-xl $radius-xl 0 0;
  padding: $space-3 $space-6 calc(env(safe-area-inset-bottom, 0px) + $space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  animation: slide-up 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}

.sheet-handle {
  width: 32px;
  height: 4px;
  border-radius: $radius-full;
  background: $outline-variant;
  margin-bottom: $space-6;
}

.sheet-icon-wrap {
  width: 56px;
  height: 56px;
  border-radius: $radius-full;
  background: rgba($primary, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-4;
}

.sheet-icon {
  font-size: 28px;
  color: $primary;
  font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}

.sheet-title {
  font-family: $font-headline;
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $on-surface;
  text-align: center;
  margin-bottom: $space-2;
}

.sheet-desc {
  font-size: $body-md-size;
  font-weight: $font-weight-medium;
  color: $on-surface-variant;
  text-align: center;
  line-height: 1.6;
  white-space: pre-line;
  margin-bottom: $space-6;
  padding: 0 $space-4;
}

.sheet-actions {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.btn-primary {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;
  background: $primary;
  border-radius: $radius-full;
  padding: $space-4;
  transition: transform 0.15s ease;

  &:active {
    transform: scale(0.98);
  }
}

.btn-primary-icon {
  font-size: 18px;
  color: $on-primary;
  font-variation-settings: 'FILL' 1, 'wght' 300, 'GRAD' 0, 'opsz' 24;
}

.btn-primary-text {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $on-primary;
}

.btn-secondary {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $surface-container-low;
  border-radius: $radius-full;
  padding: $space-4;
  transition: transform 0.15s ease;

  &:active {
    transform: scale(0.98);
    background: $surface-container-high;
  }
}

.btn-secondary-text {
  font-size: $body-md-size;
  font-weight: $font-weight-bold;
  color: $on-surface-variant;
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
