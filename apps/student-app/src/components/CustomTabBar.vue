<template>
  <view class="tab-bar">
    <view
      v-for="tab in tabs"
      :key="tab.key"
      :class="['tab-item', { active: current === tab.key }]"
      hover-class="tab-item--pressed"
      :hover-start-time="0"
      :hover-stay-time="80"
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
  { key: 'services', icon: 'business_center', label: '服务大厅', path: '/pages/services/index' },
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
  left: var(--student-fixed-left, 0);
  right: var(--student-fixed-right, 0);
  z-index: 50;
  box-sizing: border-box;
  height: var(--tabbar-safe);                         // 76px + safe-area
  padding: $space-2 $space-4 env(safe-area-inset-bottom, 0);
  display: flex;
  justify-content: space-around;
  align-items: center;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255,255,255,.88), rgba(255,255,255,.72));
  backdrop-filter: blur(26px) saturate(165%);
  -webkit-backdrop-filter: blur(26px) saturate(165%);
  border-top: 1px solid rgba(255,255,255,.9);
  border-radius: $radius-lg $radius-lg 0 0;           // rounded-t-[2rem]
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.96),
    0 -12px 42px rgba(91,43,143,.09);
}

.tab-bar::before {
  content: '';
  position: absolute;
  inset: 0 8% auto;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,1), rgba(199,158,226,.72), transparent);
  opacity: .9;
}

.tab-bar::after {
  content: '';
  position: absolute;
  top: -70%;
  left: -18%;
  width: 36%;
  height: 150%;
  pointer-events: none;
  filter: blur(10px);
  transform: skewX(-18deg);
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.74), transparent);
  animation: tabMirrorSweep 12s cubic-bezier(.3,.02,.2,1) infinite;
}

.tab-item {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: $space-2 $space-3;
  border-radius: $radius-full;
  transition:
    background var(--yxg-touch-out) var(--yxg-spring-out),
    color .24s ease,
    transform var(--yxg-touch-out) var(--yxg-spring-out),
    box-shadow var(--yxg-touch-out) var(--yxg-spring-out);

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

  &:active,
  &.tab-item--pressed {
    transform: translateY(1px) scale(.965);
    transition-duration: var(--yxg-touch-in);
  }

  &.active {
    background:
      linear-gradient(145deg, rgba(255,255,255,.58), rgba(91,43,143,.10));
    padding: $space-2 $space-5;                       // px-5 py-2
    border-radius: 24px;                              // rounded-[24px] per stitch
    box-shadow:
      inset 0 1px 0 rgba(255,255,255,.78),
      inset 0 -1px 0 rgba(91,43,143,.08);

    .tab-icon {
      color: $primary;
      font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    }
    .tab-label {
      color: $primary;
    }
  }
}

@keyframes tabMirrorSweep {
  0%, 52% { opacity: 0; transform: translateX(0) skewX(-18deg); }
  58% { opacity: .75; }
  72% { opacity: 0; transform: translateX(360%) skewX(-18deg); }
  100% { opacity: 0; transform: translateX(360%) skewX(-18deg); }
}

@media (prefers-reduced-motion: reduce) {
  .tab-bar::after { animation: none; }
}
</style>
