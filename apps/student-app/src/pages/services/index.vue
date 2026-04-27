<script setup lang="ts">
import { ref } from 'vue'
import CustomTabBar from '@/components/CustomTabBar.vue'

const upcoming = ref([
  { id: 's1', label: '空教室预约', icon: 'meeting_room' },
  { id: 's2', label: '请假申请',   icon: 'event_busy' },
  { id: 's3', label: '宿舍维修',   icon: 'build' },
  { id: 's4', label: '校园卡充值', icon: 'credit_card' },
  { id: 's5', label: '图书馆',     icon: 'menu_book' },
  { id: 's6', label: '学生邮箱',   icon: 'mail' },
])

function comingSoon() {
  uni.showToast({ title: '即将上线', icon: 'none' })
}
</script>

<template>
  <view class="services-page">
    <view class="page-header">
      <text class="page-title">事务导办</text>
      <text class="page-subtitle">校园生活一站式办理</text>
    </view>

    <view class="services-grid">
      <view
        v-for="item in upcoming"
        :key="item.id"
        class="service-card"
        @click="comingSoon"
      >
        <view class="icon-wrap">
          <text class="material-symbols-outlined">{{ item.icon }}</text>
        </view>
        <text class="service-label">{{ item.label }}</text>
        <text class="service-status">即将上线</text>
      </view>
    </view>

    <CustomTabBar current="services" />
  </view>
</template>

<style lang="scss" scoped>
@import '@/styles/tokens.scss';

.services-page {
  min-height: 100vh;
  padding: $space-4;
  padding-top: 64px;
  padding-bottom: calc(env(safe-area-inset-bottom) + 6rem);
  background: $bg-page;
  font-family: $font-family-sans;
}

.page-header {
  margin-bottom: $space-6;

  .page-title {
    display: block;
    font-size: $font-size-2xl;
    font-weight: $font-weight-bold;
    color: $text-primary;
  }

  .page-subtitle {
    display: block;
    margin-top: $space-1;
    font-size: $font-size-sm;
    color: $text-secondary;
  }
}

.services-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: $space-3;
}

.service-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: $space-5 $space-3;
  background: $bg-card;
  border-radius: $radius-lg;
  box-shadow: $shadow-sm;

  .icon-wrap {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: $primary-soft;
    border-radius: $radius-md;
    margin-bottom: $space-2;

    .material-symbols-outlined {
      font-size: 28px;
      color: $primary;
    }
  }

  .service-label {
    font-size: $font-size-base;
    font-weight: $font-weight-semibold;
    color: $text-primary;
  }

  .service-status {
    margin-top: $space-1;
    font-size: $font-size-xs;
    color: $text-muted;
  }
}
</style>
