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
  { key: 'assistant', icon: 'smart_toy', label: '智能问答', path: '/pages/chat/index' },
  { key: 'profile', icon: 'person', label: '我的', path: '/pages/profile/index' },
]

function switchTab(tab: { path: string; key: string }) {
  uni.switchTab({ url: tab.path })
}
</script>

<style scoped>
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 3.5rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  display: flex;
  align-items: center;
  justify-content: space-around;
  border-top: 1px solid #E2E8F0;
  padding-bottom: env(safe-area-inset-bottom);
  z-index: 999;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.125rem;
  flex: 1;
  padding: 0.375rem 0;
  transition: all 0.2s;
}

.tab-icon {
  font-size: 1.5rem;
  color: #94A3B8;
  transition: color 0.2s;
}
.tab-icon.active {
  color: #7C3AED;
}

.tab-label {
  font-size: 0.625rem;
  font-weight: 600;
  color: #94A3B8;
  transition: color 0.2s;
}
.tab-label.active {
  color: #7C3AED;
}
</style>
