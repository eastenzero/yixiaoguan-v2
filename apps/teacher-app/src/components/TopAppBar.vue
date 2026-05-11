<template>
  <view class="top-app-bar">
    <view class="left-area">
      <view 
        v-if="showBack" 
        class="back-btn"
        @click="handleBack"
      >
        <IconArrowLeft :size="20" />
      </view>
    </view>
    
    <text class="title">{{ title }}</text>
    
    <view class="right-area">
      <view 
        v-if="action === 'search'" 
        class="action-btn"
        @click="handleAction"
      >
        <IconSearch :size="20" />
      </view>
      <view 
        v-else-if="action === 'settings'" 
        class="action-btn"
        @click="handleAction"
      >
        <IconSettings :size="20" />
      </view>
      <view 
        v-else-if="action === 'add'" 
        class="action-btn action-btn--primary"
        @click="handleAction"
      >
        <IconPlus :size="20" />
      </view>
      <view 
        v-else-if="action === 'edit'" 
        class="action-btn"
        @click="handleAction"
      >
        <IconEdit :size="20" />
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { useAttrs } from 'vue'
import IconArrowLeft from './icons/IconArrowLeft.vue'
import IconSearch from './icons/IconSearch.vue'
import IconSettings from './icons/IconSettings.vue'
import IconPlus from './icons/IconPlus.vue'
import IconEdit from './icons/IconEdit.vue'

interface Props {
  title: string
  showBack?: boolean
  action?: 'search' | 'settings' | 'add' | 'edit' | 'none'
}

const props = withDefaults(defineProps<Props>(), {
  showBack: false,
  action: 'none'
})

const attrs = useAttrs()

const emit = defineEmits<{
  action: []
  back: []
}>()

const handleBack = () => {
  if (attrs.onBack) {
    emit('back')
  } else {
    uni.navigateBack()
  }
}

const handleAction = () => {
  emit('action')
}
</script>

<style lang="scss" scoped>
.top-app-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $space-4;
  background: rgba($surface-container-lowest, 0.8); // 与各页 custom-app-bar 一致
  backdrop-filter: $backdrop-bar;
  -webkit-backdrop-filter: $backdrop-bar;
}

.left-area {
  width: 40px;
  display: flex;
  align-items: center;
}

.back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: $on-surface;                          // icon currentColor
  
  &:active {
    background: $surface-container-low;
  }
}

.title {
  font-family: $font-headline;
  font-weight: 700;
  font-size: 20px;
  color: $on-surface;
  flex: 1;
  text-align: center;
}

.right-area {
  width: 40px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  color: $on-surface;                          // icon currentColor
  
  &:active {
    background: $surface-container-low;
  }
  
  &--primary {
    background: rgba($primary, 0.1);
    color: $primary;                           // 覆盖父级 color，加号用主色
    
    &:active {
      background: rgba($primary, 0.2);
    }
  }
}
</style>
