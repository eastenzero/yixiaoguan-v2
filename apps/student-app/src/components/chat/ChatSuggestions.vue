<template>
  <view v-if="questions.length" class="suggestions">
    <view class="suggestions-title">
      <AppIcon name="lightbulb" class="suggestions-icon" />
      <text>你可能还想问</text>
    </view>
    <view class="suggestions-list">
      <view
        v-for="question in questions"
        :key="question"
        class="suggestion-chip"
        @click="$emit('select', question)"
      >
        <text class="suggestion-text">{{ question }}</text>
        <AppIcon name="arrow_forward" class="suggestion-icon" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'

defineProps<{
  questions: string[]
}>()

defineEmits<{
  (event: 'select', question: string): void
}>()
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.suggestions {
  margin: 0 4px 18px;
}

.suggestions-title {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 10px;
  color: #92400e;
  font-size: 12px;
  font-weight: 800;
}

.suggestions-icon {
  color: #d97706;
  font-size: 16px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-chip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 18px;
  background: rgba($primary, 0.06);
}

.suggestion-chip:active {
  background: rgba($primary, 0.11);
}

.suggestion-text {
  flex: 1;
  color: $primary;
  font-size: 13px;
  font-weight: 700;
  line-height: 1.45;
}

.suggestion-icon {
  color: $primary;
  font-size: 14px;
  flex-shrink: 0;
}
</style>
