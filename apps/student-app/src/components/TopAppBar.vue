<template>
  <view class="top-app-bar">
    <view class="bar-inner">
      <view class="left-area">
        <view
          v-if="showBack"
          class="icon-btn"
          @click="handleBack"
        >
          <text class="material-symbols-outlined icon-glyph">arrow_back</text>
        </view>
      </view>

      <text class="bar-title" :class="{ 'bar-title--brand': brand }">{{ title }}</text>

      <view class="right-area">
        <slot name="right">
          <view
            v-if="actionIcon"
            class="icon-btn"
            :class="{ 'icon-btn--accent': actionAccent }"
            @click="handleAction"
          >
            <text class="material-symbols-outlined icon-glyph" :class="{ 'icon-glyph--accent': actionAccent }">{{ actionIcon }}</text>
            <view v-if="actionBadge && actionBadge > 0" class="badge">
              <text class="badge-text">{{ actionBadge > 99 ? '99+' : actionBadge }}</text>
            </view>
          </view>
        </slot>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useAttrs } from 'vue'

interface Props {
  title?: string
  showBack?: boolean
  actionIcon?: string | null
  actionBadge?: number
  /** 主色高亮 action 图标（用于通知未读小红点情境） */
  actionAccent?: boolean
  /** brand 模式：title 字号偏大 + 主色（home 顶栏 logo 风） */
  brand?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: '',
  showBack: false,
  actionIcon: null,
  actionBadge: 0,
  actionAccent: false,
  brand: false,
})

const attrs = useAttrs()

const emit = defineEmits<{
  action: []
  back: []
}>()

function handleBack() {
  if (attrs.onBack) {
    emit('back')
  } else {
    uni.navigateBack()
  }
}

function handleAction() {
  emit('action')
}
</script>

<style lang="scss" scoped>
@import '@/styles/tokens.scss';

.top-app-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  padding-top: env(safe-area-inset-top);
  background: rgba(249, 250, 251, 0.85);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
}

.bar-inner {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $space-4;
}

.left-area,
.right-area {
  width: 40px;
  display: flex;
  align-items: center;
}

.right-area {
  justify-content: flex-end;
}

.bar-title {
  flex: 1;
  text-align: center;
  font-size: $font-size-lg;
  font-weight: $font-weight-bold;
  color: $text-primary;
  letter-spacing: -0.01em;

  &--brand {
    font-size: $font-size-xl;
    font-weight: $font-weight-bold;
    color: $primary;
    text-align: left;
    padding-left: $space-2;
  }
}

.icon-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: $radius-full;
  transition: background 0.18s ease-out, transform 0.18s ease-out;

  &:active {
    background: rgba($primary, 0.10);
    transform: scale(0.92);
  }

  &--accent {
    background: rgba($primary, 0.10);

    &:active {
      background: rgba($primary, 0.18);
    }
  }
}

.icon-glyph {
  font-size: 22px;
  color: $text-primary;

  &--accent {
    color: $primary;
  }
}

.badge {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: $radius-full;
  background: $danger;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px rgba(249, 250, 251, 0.95);
}

.badge-text {
  font-size: 10px;
  line-height: 1;
  font-weight: $font-weight-bold;
  color: $text-inverse;
}
</style>
