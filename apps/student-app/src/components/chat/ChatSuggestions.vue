<template>
  <view v-if="questions.length" class="suggestions">
    <view class="suggestions-title">
      <uni-icons type="help" size="16" color="#d97706" />
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
</style>
