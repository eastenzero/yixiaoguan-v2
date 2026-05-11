<template>
  <view
    class="user-avatar"
    :style="{ width: sizePx, height: sizePx, borderRadius: sizePx }"
  >
    <view
      v-if="imageLoaded && imageSrc"
      class="user-avatar__img"
      :style="{ backgroundImage: `url('${imageSrc}')` }"
    />
    <view
      v-else
      class="user-avatar__fallback"
      :class="fallbackColorClass"
    >
      <text class="user-avatar__initial" :style="{ fontSize: initialFontSize }">{{ initial }}</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

interface Props {
  name?: string
  staffId?: string | number | null
  avatarUrl?: string | null
  size?: number
  diceBearStyle?: string
  noDiceBear?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  name: '',
  staffId: null,
  avatarUrl: null,
  size: 44,
  diceBearStyle: 'notionists-neutral',
  noDiceBear: false,
})

const imageLoaded = ref(false)
const imageFailed = ref(false)

const seed = computed(() => {
  const sid = props.staffId
  if (sid !== null && sid !== undefined && String(sid).length > 0) {
    return String(sid)
  }
  return (props.name || 'anonymous').trim() || 'anonymous'
})

const diceBearUrl = computed(() => {
  if (props.noDiceBear) return ''
  const s = encodeURIComponent(seed.value)
  return `https://api.dicebear.com/9.x/${props.diceBearStyle}/svg?seed=${s}&radius=50&backgroundType=gradientLinear&backgroundColor=ddd6fe,fbcfe8,c4e0c9,ffe1cc,d4e4fb`
})

const imageSrc = computed(() => {
  if (imageFailed.value) return ''
  if (props.avatarUrl) return props.avatarUrl
  if (!props.noDiceBear) return diceBearUrl.value
  return ''
})

const initial = computed(() => {
  const n = (props.name || '').trim()
  if (n) return n.slice(0, 1).toUpperCase()
  const s = String(props.staffId ?? '').trim()
  return s ? s.slice(0, 1).toUpperCase() : '?'
})

const fallbackColorClass = computed(() => {
  const s = seed.value
  let hash = 0
  for (let i = 0; i < s.length; i++) {
    hash = (hash * 31 + s.charCodeAt(i)) & 0xffffffff
  }
  const palette = ['avatar-c1', 'avatar-c2', 'avatar-c3', 'avatar-c4', 'avatar-c5']
  return palette[Math.abs(hash) % palette.length]
})

const sizePx = computed(() => `${props.size}px`)
const initialFontSize = computed(() => `${Math.round(props.size * 0.42)}px`)

// JS-side preload: 避开 uni-app 模板编译器对 <img>/<image> 的改写，
// 并让 <view> + background-image 等待图片加载完成后再显示（避免闪烁空容器）。
watch(
  () => imageSrc.value,
  (url) => {
    imageLoaded.value = false
    imageFailed.value = false
    if (!url) return
    if (typeof Image === 'undefined') return  // 非 H5 环境：直接假设加载成功
    const img = new Image()
    img.onload = () => { imageLoaded.value = true }
    img.onerror = () => { imageFailed.value = true }
    img.src = url
  },
  { immediate: true }
)
</script>

<style scoped lang="scss">
.user-avatar {
  flex-shrink: 0;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: $surface-container;
}

.user-avatar__img {
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}

.user-avatar__fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-avatar__initial {
  font-weight: 700;
  line-height: 1;
}

.avatar-c1 {
  background: $primary-container;
  .user-avatar__initial { color: $on-primary-container; }
}
.avatar-c2 {
  background: $secondary-container;
  .user-avatar__initial { color: $on-secondary-container; }
}
.avatar-c3 {
  background: $tertiary-container;
  .user-avatar__initial { color: $on-tertiary-container; }
}
.avatar-c4 {
  background: rgba($primary, 0.14);
  .user-avatar__initial { color: $primary; }
}
.avatar-c5 {
  background: rgba($tertiary, 0.14);
  .user-avatar__initial { color: $tertiary; }
}
</style>
