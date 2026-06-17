<template>
  <view class="tab-bar">
    <view
      v-for="tab in tabs"
      :key="tab.key"
      :class="['tab-item', { active: current === tab.key }]"
      @click="switchTab(tab)"
    >
      <AppIcon :name="tab.icon" :class="['tab-icon', { active: current === tab.key }]" />
      <text :class="['tab-label', { active: current === tab.key }]">{{ tab.label }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
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

// Aether Academic BottomNavBar — 1:1 复刻 stitch home_page/code.html
// Single source of truth: 高度由 tokens.scss 的 $tabbar-h + env(safe-area)
// 决定, 总高 = var(--tabbar-safe)。页面通过同一变量消费, 不再估算。
.tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  z-index: 50;
  box-sizing: border-box;
  height: var(--tabbar-safe);                         // 76px + safe-area
  padding: $space-2 $space-4 env(safe-area-inset-bottom, 0);
  display: flex;
  justify-content: space-around;
  align-items: center;
  background: $glass-bg;                              // white/80
  backdrop-filter: $backdrop-bar;                     // blur(20px) saturate(180%)
  -webkit-backdrop-filter: $backdrop-bar;
  border-radius: $radius-lg $radius-lg 0 0;           // rounded-t-[2rem]
  box-shadow: 0 -10px 40px rgba(124, 58, 237, 0.08);  // 紫色折射 glow
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: $space-2 $space-3;
  border-radius: $radius-full;
  transition: background 0.2s ease, color 0.2s ease, transform 0.2s ease;

  .tab-icon {
    font-size: 24px;
    color: $outline;                                  // slate-400 等价 → outline
    transition: color 0.2s ease;
  }

  .tab-label {
    font-size: 10px;
    letter-spacing: 0.02em;
    color: $outline;
    font-weight: $font-weight-bold;
    transition: color 0.2s ease;
  }

  &:active {
    transform: scale(0.90);
  }

  &.active {
    background: rgba($primary, 0.10);                 // primary/10 tint
    padding: $space-2 $space-5;                       // px-5 py-2
    border-radius: 24px;                              // rounded-[24px] per stitch

    .tab-icon {
      color: $primary;
      font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
    .tab-label {
      color: $primary;
    }
  }
}
</style>
