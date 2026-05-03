<template>
  <view class="tab-bar">
    <view
      v-for="tab in tabs"
      :key="tab.key"
      :class="['tab-item', { 'tab-item--active': current === tab.key }]"
      @click="switchTab(tab)"
    >
      <view class="icon-wrap">
        <text class="material-symbols-outlined tab-icon">{{ tab.icon }}</text>
        <view
          v-if="tab.badge && tab.badge > 0"
          class="tab-badge"
        >
          <text class="tab-badge-text">{{ tab.badge > 99 ? '99+' : tab.badge }}</text>
        </view>
      </view>
      <text class="tab-label">{{ tab.label }}</text>
      <view v-if="current === tab.key" class="active-dot" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  current: string
  /** 各 tab 的 badge 数字，按 key 索引（如 { assistant: 3 }） */
  badges?: Record<string, number>
}

const props = withDefaults(defineProps<Props>(), {
  badges: () => ({}),
})

interface TabConfig {
  key: string
  icon: string
  label: string
  path: string
  badge?: number
}

const tabs = computed<TabConfig[]>(() => [
  { key: 'home', icon: 'home', label: '首页', path: '/pages/home/index' },
  { key: 'assistant', icon: 'chat_bubble', label: '智能问答', path: '/pages/chat/index' },
  { key: 'services', icon: 'business_center', label: '事务导办', path: '/pages/services/index' },
  { key: 'profile', icon: 'person', label: '我的', path: '/pages/profile/index' },
].map((t) => ({ ...t, badge: props.badges[t.key] || 0 })))

function switchTab(tab: { path: string; key: string }) {
  uni.switchTab({ url: tab.path })
}
</script>

<style lang="scss" scoped>
@import '@/styles/tokens.scss';

.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 100;
  display: flex;
  justify-content: space-around;
  align-items: stretch;
  padding-bottom: env(safe-area-inset-bottom);
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(20px) saturate(180%);
  -webkit-backdrop-filter: blur(20px) saturate(180%);
  border-radius: $radius-xl $radius-xl 0 0;
  box-shadow: 0 -4px 20px rgba($primary, 0.08);
  isolation: isolate;
}

.tab-item {
  position: relative;
  flex: 1;
  height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $space-1;
  transition: transform 0.18s ease-out;

  &:active {
    transform: scale(0.92);
  }

  .tab-icon {
    font-size: 24px;
    color: $text-secondary;
    transition: color 0.2s ease, font-variation-settings 0.2s ease;
  }

  .tab-label {
    font-size: 11px;
    color: $text-secondary;
    font-weight: $font-weight-medium;
    transition: color 0.2s ease, font-weight 0.2s ease;
    line-height: 1;
  }

  &--active {
    .tab-icon {
      color: $primary;
      font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
    }
    .tab-label {
      color: $primary;
      font-weight: $font-weight-bold;
    }
  }
}

.icon-wrap {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
}

.tab-badge {
  position: absolute;
  top: -6px;
  right: -10px;
  min-width: 16px;
  height: 16px;
  padding: 0 4px;
  border-radius: $radius-full;
  background: $danger;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.96);
}

.tab-badge-text {
  font-size: 10px;
  line-height: 1;
  font-weight: $font-weight-bold;
  color: $text-inverse;
}

.active-dot {
  position: absolute;
  bottom: 6px;
  width: 4px;
  height: 4px;
  border-radius: $radius-full;
  background: $primary;
}
</style>
