<template>
  <view class="webview-page">
    <!-- #ifdef MP-WEIXIN -->
    <web-view v-if="canEmbed" :src="targetUrl" @error="onLoadError" />
    <view v-else class="fallback">
      <view class="fallback-icon">
        <AppIcon name="open_in_new" class="fallback-icon-text" />
      </view>
      <text class="fallback-title">链接无法直接打开</text>
      <text class="fallback-url">{{ targetUrl || '链接为空' }}</text>
      <view class="fallback-actions">
        <view class="primary-btn" @click="copyLink">
          <text class="primary-text">复制链接</text>
        </view>
        <view class="secondary-btn" @click="goBack">
          <text class="secondary-text">返回</text>
        </view>
      </view>
    </view>
    <!-- #endif -->
    <!-- #ifndef MP-WEIXIN -->
    <view class="fallback">
      <view class="fallback-icon">
        <AppIcon name="open_in_new" class="fallback-icon-text" />
      </view>
      <text class="fallback-title">外部链接</text>
      <text class="fallback-url">{{ targetUrl || '链接为空' }}</text>
      <view class="fallback-actions">
        <view class="primary-btn" @click="copyLink">
          <text class="primary-text">复制链接</text>
        </view>
        <view class="secondary-btn" @click="goBack">
          <text class="secondary-text">返回</text>
        </view>
      </view>
    </view>
    <!-- #endif -->
  </view>
</template>

<script setup lang="ts">
import AppIcon from '@/components/AppIcon.vue'
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const targetUrl = ref('')
const hasLoadError = ref(false)

const canEmbed = computed(() => /^https:\/\//i.test(targetUrl.value) && !hasLoadError.value)

onLoad((query: Record<string, string | undefined> = {}) => {
  const rawUrl = typeof query.url === 'string' ? query.url : ''
  try {
    targetUrl.value = decodeURIComponent(rawUrl)
  } catch {
    targetUrl.value = rawUrl
  }
})

function onLoadError() {
  hasLoadError.value = true
}

function copyLink() {
  if (!targetUrl.value) return
  uni.setClipboardData({
    data: targetUrl.value,
    success: () => uni.showToast({ title: '已复制链接', icon: 'none' }),
  })
}

function goBack() {
  uni.navigateBack({
    delta: 1,
    fail: () => uni.switchTab({ url: '/pages/services/index' }),
  })
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';

.webview-page {
  min-height: 100vh;
  background: $surface;
}

.fallback {
  min-height: 100vh;
  padding: calc(env(safe-area-inset-top) + 6rem) $space-6 $space-8;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.fallback-icon {
  width: 4rem;
  height: 4rem;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba($primary, 0.10);
  margin-bottom: $space-5;
}

.fallback-icon-text {
  font-size: 2rem;
  color: $primary;
}

.fallback-title {
  font-size: $font-size-xl;
  font-weight: $font-weight-bold;
  color: $on-surface;
  margin-bottom: $space-4;
}

.fallback-url {
  width: 100%;
  padding: $space-4;
  border-radius: $radius-md;
  background: $surface-container-low;
  color: $on-surface-variant;
  font-size: $font-size-sm;
  line-height: 1.6;
  word-break: break-all;
  box-sizing: border-box;
}

.fallback-actions {
  width: 100%;
  display: flex;
  gap: $space-3;
  margin-top: $space-6;
}

.primary-btn,
.secondary-btn {
  flex: 1;
  min-height: 3rem;
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
}

.primary-btn {
  background: $primary;
}

.secondary-btn {
  background: $surface-container-low;
}

.primary-text,
.secondary-text {
  font-size: $font-size-base;
  font-weight: $font-weight-bold;
}

.primary-text {
  color: $on-primary;
}

.secondary-text {
  color: $on-surface-variant;
}
</style>