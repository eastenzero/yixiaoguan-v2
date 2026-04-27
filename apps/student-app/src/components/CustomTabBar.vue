<template>
  <view class="tab-bar">
    <view
      v-for="tab in tabs"
      :key="tab.key"
      :class="['tab-item', { active: current === tab.key }]"
      @click="switchTab(tab)"
    >
      <text :class="['material-symbols-outlined', 'tab-icon', { active: current === tab.key }]">{{ tab.icon }}</text>
      <text :class="['tab-label', { active: current === tab.key }]">{{ tab.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{ current: string }>()

const tabs = [
  { key: 'home', icon: 'home', label: '首页', path: '/pages/home/index' },
  { key: 'assistant', icon: 'chat_bubble', label: '智能问答', path: '/pages/chat/index' },
  { key: 'services', icon: 'business_center', label: '事务导办', path: '/pages/services/index' },
  { key: 'profile', icon: 'person', label: '我的', path: '/pages/profile/index' },
]

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
  align-items: center;
  padding: $space-2 $space-3 calc(env(safe-area-inset-bottom, 0) + #{$space-2});
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: $radius-xl $radius-xl 0 0;
  box-shadow: 0 -4px 12px rgba(91, 33, 182, 0.08);
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: $space-2 $space-3;
  border-radius: $radius-lg;
  transition: background 0.2s, color 0.2s;
  flex: 1;

  .tab-icon {
    font-size: 24px;
    color: $text-secondary;
    transition: color 0.2s;
  }

  .tab-label {
    font-size: $font-size-xs;
    color: $text-secondary;
    transition: color 0.2s;
    font-weight: $font-weight-medium;
  }

  &.active {
    background: $primary-soft;

    .tab-icon,
    .tab-label {
      color: $primary;
      font-weight: $font-weight-semibold;
    }
  }
}
</style>
