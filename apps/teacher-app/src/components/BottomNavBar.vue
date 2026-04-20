<template>
  <view class="bottom-nav-bar">
    <view 
      v-for="(tab, index) in tabs" 
      :key="index"
      class="tab-item"
      :class="{ 'tab-item--active': current === index }"
      @click="handleTabClick(index)"
    >
      <view class="icon-wrapper">
        <component 
          :is="tab.icon" 
          :size="24" 
          :color="current === index ? '#702ae1' : '#5d5b5f'"
          :stroke-width="current === index ? 2.5 : 2"
        />
        <view 
          v-if="index === 1 && badge && badge > 0" 
          class="badge"
        >
          {{ badge > 99 ? '99+' : badge }}
        </view>
      </view>
      <text class="tab-label">{{ tab.label }}</text>
      <view 
        v-if="current === index" 
        class="active-dot"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import IconDashboard from './icons/IconDashboard.vue'
import IconMessage from './icons/IconMessage.vue'
import IconBook from './icons/IconBook.vue'
import IconUser from './icons/IconUser.vue'

interface Props {
  current: number
  badge?: number
}

withDefaults(defineProps<Props>(), {
  current: 0,
  badge: 0
})

const tabs = [
  { label: '工作台', icon: IconDashboard, path: '/pages/dashboard/index' },
  { label: '学生提问', icon: IconMessage, path: '/pages/questions/index' },
  { label: '知识库', icon: IconBook, path: '/pages/knowledge/index' },
  { label: '我的', icon: IconUser, path: '/pages/profile/index' }
]

const handleTabClick = (index: number) => {
  const tab = tabs[index]
  uni.switchTab({ url: tab.path })
}
</script>

<style lang="scss" scoped>
.bottom-nav-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 9999;
  height: calc(76px + env(safe-area-inset-bottom));
  padding-bottom: env(safe-area-inset-bottom);
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
  border-radius: 16px 16px 0 0;
  box-shadow: 0 -4px 20px rgba(99, 14, 212, 0.05);
  isolation: isolate;
}

.tab-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 76px;
  position: relative;
}

.icon-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  margin-bottom: 8px;
}

.tab-label {
  font-family: $font-label;
  font-size: 10px;
  font-weight: 500;
  color: $on-surface-variant;
  opacity: 0.6;
  transition: all 0.2s ease;
}

.tab-item--active {
  .tab-label {
    color: $primary;
    opacity: 1;
    font-weight: 700;
  }
}

.active-dot {
  position: absolute;
  bottom: 8px;
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: $primary;
}

.badge {
  position: absolute;
  top: -6px;
  right: -8px;
  min-width: 16px;
  height: 16px;
  padding: 2px 6px;
  background: $error;
  color: white;
  font-size: 10px;
  font-weight: 700;
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 2px white;
}
</style>
