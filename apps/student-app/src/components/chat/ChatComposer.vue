<template>
  <view class="composer-shell">
    <view v-if="showCallMenu" class="call-menu-overlay" @click="$emit('close-call-menu')">
      <view class="call-menu" @click.stop>
        <view class="call-menu-item" @click="$emit('call-teacher')">
          <uni-icons type="staff" size="18" color="#5b21b6" />
          <text class="call-menu-text">呼叫老师</text>
        </view>
      </view>
    </view>

    <view class="composer">
      <input
        class="composer-input"
        :value="modelValue"
        :placeholder="placeholder"
        :disabled="disabled"
        confirm-type="send"
        @input="onInput"
        @confirm="$emit('send')"
      />
      <view
        :class="['send-btn', { disabled: !canSend }]"
        @click="$emit('send')"
        @longpress="$emit('longpress-send')"
      >
        <uni-icons type="paperplane" size="20" color="#ffffff" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  modelValue: string
  placeholder: string
  disabled: boolean
  canSend: boolean
  showCallMenu: boolean
}>()

const emit = defineEmits<{
  (event: 'update:modelValue', value: string): void
  (event: 'send'): void
  (event: 'longpress-send'): void
  (event: 'close-call-menu'): void
  (event: 'call-teacher'): void
}>()

function onInput(event: any) {
  const value = event?.detail?.value ?? event?.target?.value ?? ''
  emit('update:modelValue', String(value))
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.composer-shell {
  position: fixed;
  left: 0;
  right: 0;
  bottom: var(--tabbar-safe);
  z-index: 45;
  padding: 10px 16px 12px;
  background: rgba(250, 245, 251, 0.92);
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
}

.composer {
  width: 100%;
  max-width: 720px;
  min-height: 52px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 8px;
  box-sizing: border-box;
  padding: 6px 6px 6px 16px;
  border-radius: 28px;
  background: $surface-container-high;
}

.composer-input {
  flex: 1;
  min-width: 0;
  height: 40px;
  color: $on-surface;
  font-size: 14px;
}

.send-btn {
  width: 40px;
  height: 40px;
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $gradient-cta;
  box-shadow: 0 8px 20px rgba(91, 33, 182, 0.20);
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.send-btn:active {
  transform: scale(0.94);
}

.send-btn.disabled {
  opacity: 0.45;
}

.call-menu-overlay {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 100%;
  display: flex;
  justify-content: flex-end;
  padding: 0 16px 8px;
}

.call-menu {
  min-width: 132px;
  border-radius: 16px;
  background: $surface-container-lowest;
  box-shadow: $shadow-fab;
  overflow: hidden;
}

.call-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
}

.call-menu-item:active {
  background: $surface-container-low;
}

.call-menu-text {
  color: $on-surface;
  font-size: 14px;
  font-weight: 700;
}
</style>
