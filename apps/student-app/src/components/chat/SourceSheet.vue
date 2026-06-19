<template>
  <uni-popup ref="popupRef" type="bottom" background-color="transparent" @change="onPopupChange">
    <view class="source-sheet">
      <view class="drag-bar">
        <view class="drag-indicator" />
      </view>
      <view class="sheet-header">
        <text class="sheet-title">{{ title }}</text>
        <view class="close-btn" @click="$emit('close')">
          <uni-icons type="closeempty" size="22" color="#78767b" />
        </view>
      </view>
      <scroll-view class="sheet-body" scroll-y>
        <MarkdownContent class="markdown-body source-markdown" :content="content" variant="source" />
      </scroll-view>
    </view>
  </uni-popup>
</template>

<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import MarkdownContent from '@/components/MarkdownContent.vue'

const props = defineProps<{
  visible: boolean
  title: string
  content: string
}>()

const emit = defineEmits<{
  (event: 'close'): void
}>()

const popupRef = ref<any>(null)

watch(
  () => props.visible,
  (visible) => {
    nextTick(() => {
      if (visible) popupRef.value?.open('bottom')
      else popupRef.value?.close()
    })
  },
  { immediate: true },
)

function onPopupChange(event: { show?: boolean }) {
  if (!event.show) emit('close')
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.source-sheet {
  width: 100%;
  max-width: 720px;
  max-height: 78vh;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 28px 28px 0 0;
  background: $surface-container-lowest;
}

.drag-bar {
  display: flex;
  justify-content: center;
  padding: 10px 0 4px;
}

.drag-indicator {
  width: 36px;
  height: 4px;
  border-radius: 999px;
  background: $outline-variant;
}

.sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 18px 12px;
}

.sheet-title {
  flex: 1;
  overflow: hidden;
  color: $on-surface;
  font-size: 16px;
  font-weight: 800;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.close-btn {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 17px;
  background: $surface-container-low;
}

.sheet-body {
  flex: 1;
  min-height: 0;
  box-sizing: border-box;
  padding: 0 18px 22px;
}
</style>
