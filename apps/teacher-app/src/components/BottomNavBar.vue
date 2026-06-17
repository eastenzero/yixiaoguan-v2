<template>
  <view class="bottom-nav-bar">
    <view
      v-for="(tab, index) in tabs"
      :key="index"
      class="tab-item"
      :class="{ 'tab-item--active': props.current === index }"
      @click="handleTabClick(index)"
    >
      <view class="icon-wrapper">
        <IconDashboard
          v-if="tab.key === 'dashboard'"
          :size="24"
          :color="props.current === index ? '#5b21b6' : '#5d5b5f'"
          :stroke-width="props.current === index ? 2.5 : 2"
        />
        <IconMessage
          v-else-if="tab.key === 'questions'"
          :size="24"
          :color="props.current === index ? '#5b21b6' : '#5d5b5f'"
          :stroke-width="props.current === index ? 2.5 : 2"
        />
        <IconBook
          v-else-if="tab.key === 'knowledge'"
          :size="24"
          :color="props.current === index ? '#5b21b6' : '#5d5b5f'"
          :stroke-width="props.current === index ? 2.5 : 2"
        />
        <IconUser
          v-else
          :size="24"
          :color="props.current === index ? '#5b21b6' : '#5d5b5f'"
          :stroke-width="props.current === index ? 2.5 : 2"
        />
        <view
          v-if="index === 1 && props.badge && props.badge > 0"
          class="badge"
        >
          {{ props.badge > 99 ? '99+' : props.badge }}
        </view>
      </view>
      <text class="tab-label">{{ tab.label }}</text>
      <view
        v-if="props.current === index"
        class="active-dot"
      />
    </view>
  </view>
</template>

<script setup lang="ts">
import IconDashboard from './icons/IconDashboard.vue'
import IconMessage from './icons/IconMessage.vue'
import IconBook from './icons/IconBook.vue'
import IconUser from './icons/IconUser.vue'

interface Props {
  current: number
  badge?: number
}

const props = withDefaults(defineProps<Props>(), {
  current: 0,
  badge: 0
})

const tabs = [
  { key: 'dashboard', label: '工作台', path: '/pages/dashboard/index' },
  { key: 'questions', label: '学生提问', path: '/pages/questions/index' },
  { key: 'knowledge', label: '知识库', path: '/pages/knowledge/index' },
  { key: 'profile', label: '我的', path: '/pages/profile/index' }
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
  height: var(--tabbar-safe);                      // tokens.scss single source of truth
  padding-bottom: env(safe-area-inset-bottom, 0);
  display: flex;
  align-items: center;
  justify-content: space-around;
  background: $glass-bg;                     // white/80
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
  border-radius: $radius-lg $radius-lg 0 0;  // 2rem 上圆 per DESIGN.md
  box-shadow: $shadow-nav;                   // 紫色折射 nav lift
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
