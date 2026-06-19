<template>
  <view class="empty-state">
    <view class="empty-mark">
      <uni-icons type="sparkles" size="30" color="#ffffff" />
    </view>
    <text class="empty-title">智慧校园助理</text>
    <text class="empty-desc">同学你好！校园生活、选课安排和办事流程，都可以从这里开始问。</text>

    <view class="starter-list">
      <view
        v-for="question in questions"
        :key="question"
        class="starter-chip"
        @click="$emit('select', question)"
      >
        <text class="starter-text">{{ question }}</text>
        <uni-icons type="right" size="14" color="#5b21b6" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
defineProps<{
  questions: string[]
}>()

defineEmits<{
  (event: 'select', question: string): void
}>()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.empty-state {
  width: 100%;
  max-width: 520px;
  margin: 0 auto;
  box-sizing: border-box;
  padding: 38px 20px calc(var(--tabbar-safe) + 96px);
  display: flex;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.empty-mark {
  width: 64px;
  height: 64px;
  border-radius: 26px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 18px;
  background: $gradient-cta;
  box-shadow: 0 18px 36px rgba(91, 33, 182, 0.22);
}

.empty-title {
  color: $on-surface;
  font-size: 24px;
  font-weight: 800;
  line-height: 1.25;
}

.empty-desc {
  max-width: 300px;
  margin-top: 10px;
  color: $on-surface-variant;
  font-size: 14px;
  line-height: 1.7;
}

.starter-list {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 28px;
}

.starter-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  box-sizing: border-box;
  width: 100%;
  padding: 13px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
}

.starter-chip:active {
  background: $surface-container-low;
  transform: scale(0.99);
}

.starter-text {
  flex: 1;
  color: $primary;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.45;
  text-align: left;
}
</style>
