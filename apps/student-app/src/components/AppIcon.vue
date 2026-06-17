<template>
  <view :class="['app-icon', iconClass]" aria-hidden="true">
    <view class="icon-part p1"></view>
    <view class="icon-part p2"></view>
    <view class="icon-part p3"></view>
    <view class="icon-part p4"></view>
  </view>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  name?: string | null
}>()

const aliases: Record<string, string> = {
  apps: 'grid',
  auto_awesome: 'sparkle',
  business_center: 'briefcase',
  calendar_month: 'calendar',
  campaign: 'megaphone',
  cancel: 'close',
  chat: 'chat',
  chat_bubble: 'chat',
  chat_bubble_outline: 'chat',
  check_circle: 'check',
  chevron_right: 'chevron-right',
  construction: 'handyman',
  close_fullscreen: 'corners-in',
  cloud_done: 'cloud-check',
  credit_card: 'card',
  event_available: 'calendar-check',
  event_note: 'calendar',
  expand_more: 'chevron-down',
  feedback: 'chat',
  forum: 'chat',
  grade: 'badge',
  grid_view: 'grid',
  help_center: 'help',
  history: 'history',
  home_work: 'home',
  hourglass_empty: 'hourglass',
  hourglass_top: 'hourglass',
  library_books: 'book',
  live_tv: 'screen',
  lock: 'lock',
  logout: 'logout',
  mark_chat_read: 'chat-check',
  menu_book: 'book',
  message: 'chat',
  notifications: 'bell',
  open_in_full: 'corners-out',
  open_in_new: 'external',
  photo_camera: 'camera',
  podium: 'podium',
  qr_code: 'qr',
  rate_review: 'edit',
  school: 'school',
  settings: 'settings',
  smart_toy: 'bot',
  support_agent: 'headset',
  verified: 'check',
  verified_user: 'check',
  visibility: 'eye',
  visibility_off: 'eye-off',
  volunteer_activism: 'heart',
}

const supported = new Set([
  'arrow_back',
  'arrow_forward',
  'badge',
  'bell',
  'book',
  'bot',
  'briefcase',
  'calendar',
  'calendar-check',
  'call',
  'camera',
  'card',
  'chat',
  'chat-check',
  'check',
  'chevron-down',
  'chevron-right',
  'close',
  'cloud-check',
  'corners-in',
  'corners-out',
  'edit',
  'external',
  'eye',
  'eye-off',
  'face_retouching_natural',
  'gate',
  'grid',
  'groups',
  'handyman',
  'headset',
  'heart',
  'help',
  'history',
  'home',
  'hourglass',
  'info',
  'language',
  'lightbulb',
  'lock',
  'logout',
  'mail',
  'megaphone',
  'meeting_room',
  'person',
  'podium',
  'qr',
  'school',
  'screen',
  'send',
  'settings',
  'sparkle',
  'wifi',
])

const iconClass = computed(() => {
  const key = String(props.name || '').trim()
  const icon = aliases[key] || key
  return `icon-${supported.has(icon) ? icon : 'info'}`
})
</script>

<style scoped lang="scss">
.app-icon {
  position: relative;
  display: inline-block;
  width: 1em;
  height: 1em;
  min-width: 1em;
  min-height: 1em;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  color: inherit;
  line-height: 1;
  vertical-align: middle;
  flex-shrink: 0;
}

.icon-part {
  position: absolute;
  box-sizing: border-box;
  color: inherit;
  border-color: currentColor;
}

.p1,
.p2,
.p3,
.p4 {
  display: none;
}

.icon-home .p1 {
  display: block;
  width: 0.58em;
  height: 0.58em;
  left: 0.21em;
  top: 0.12em;
  border-left: 0.13em solid currentColor;
  border-top: 0.13em solid currentColor;
  transform: rotate(45deg);
  border-radius: 0.04em;
}

.icon-home .p2 {
  display: block;
  width: 0.58em;
  height: 0.43em;
  left: 0.21em;
  bottom: 0.11em;
  border: 0.13em solid currentColor;
  border-top: 0;
  border-radius: 0.05em;
}

.icon-home .p3 {
  display: block;
  width: 0.13em;
  height: 0.25em;
  left: 0.44em;
  bottom: 0.11em;
  background: currentColor;
  border-radius: 0.05em 0.05em 0 0;
}

.icon-chat .p1,
.icon-chat-check .p1 {
  display: block;
  width: 0.78em;
  height: 0.58em;
  left: 0.11em;
  top: 0.16em;
  border: 0.12em solid currentColor;
  border-radius: 0.22em;
}

.icon-chat .p2,
.icon-chat-check .p2 {
  display: block;
  width: 0.24em;
  height: 0.24em;
  left: 0.25em;
  bottom: 0.10em;
  border-left: 0.12em solid currentColor;
  border-bottom: 0.12em solid currentColor;
  transform: rotate(-20deg);
}

.icon-chat-check .p3 {
  display: block;
  width: 0.34em;
  height: 0.18em;
  right: 0.10em;
  bottom: 0.13em;
  border-left: 0.11em solid currentColor;
  border-bottom: 0.11em solid currentColor;
  transform: rotate(-45deg);
}

.icon-person .p1,
.icon-groups .p1,
.icon-face_retouching_natural .p1 {
  display: block;
  width: 0.34em;
  height: 0.34em;
  left: 0.33em;
  top: 0.12em;
  background: currentColor;
  border-radius: 50%;
}

.icon-person .p2,
.icon-groups .p2,
.icon-face_retouching_natural .p2 {
  display: block;
  width: 0.70em;
  height: 0.36em;
  left: 0.15em;
  bottom: 0.10em;
  border: 0.12em solid currentColor;
  border-radius: 0.38em 0.38em 0.16em 0.16em;
  border-bottom-width: 0.10em;
}

.icon-groups .p3 {
  display: block;
  width: 0.24em;
  height: 0.24em;
  left: 0.12em;
  top: 0.22em;
  background: currentColor;
  border-radius: 50%;
  opacity: 0.65;
}

.icon-sparkle .p1 {
  display: block;
  width: 0.14em;
  height: 0.82em;
  left: 0.43em;
  top: 0.09em;
  background: currentColor;
  border-radius: 0.20em;
}

.icon-sparkle .p2 {
  display: block;
  width: 0.82em;
  height: 0.14em;
  left: 0.09em;
  top: 0.43em;
  background: currentColor;
  border-radius: 0.20em;
}

.icon-sparkle .p3 {
  display: block;
  width: 0.18em;
  height: 0.18em;
  right: 0.05em;
  top: 0.10em;
  background: currentColor;
  transform: rotate(45deg);
  border-radius: 0.04em;
  opacity: 0.82;
}

.icon-sparkle .p4 {
  display: block;
  width: 0.13em;
  height: 0.13em;
  left: 0.08em;
  bottom: 0.12em;
  background: currentColor;
  transform: rotate(45deg);
  border-radius: 0.03em;
  opacity: 0.72;
}

.icon-briefcase .p1 {
  display: block;
  width: 0.78em;
  height: 0.55em;
  left: 0.11em;
  top: 0.31em;
  border: 0.12em solid currentColor;
  border-radius: 0.12em;
}

.icon-briefcase .p2 {
  display: block;
  width: 0.34em;
  height: 0.23em;
  left: 0.33em;
  top: 0.16em;
  border: 0.11em solid currentColor;
  border-bottom: 0;
  border-radius: 0.12em 0.12em 0 0;
}

.icon-briefcase .p3 {
  display: block;
  width: 0.78em;
  height: 0.10em;
  left: 0.11em;
  top: 0.52em;
  background: currentColor;
  opacity: 0.65;
}

.icon-grid .p1,
.icon-grid .p2,
.icon-grid .p3,
.icon-grid .p4,
.icon-qr .p1,
.icon-qr .p2,
.icon-qr .p3,
.icon-qr .p4 {
  display: block;
  width: 0.30em;
  height: 0.30em;
  border: 0.10em solid currentColor;
  border-radius: 0.08em;
}

.icon-grid .p1,
.icon-qr .p1 {
  left: 0.12em;
  top: 0.12em;
}

.icon-grid .p2,
.icon-qr .p2 {
  right: 0.12em;
  top: 0.12em;
}

.icon-grid .p3,
.icon-qr .p3 {
  left: 0.12em;
  bottom: 0.12em;
}

.icon-grid .p4,
.icon-qr .p4 {
  right: 0.12em;
  bottom: 0.12em;
}

.icon-history .p1 {
  display: block;
  width: 0.74em;
  height: 0.74em;
  left: 0.13em;
  top: 0.13em;
  border: 0.12em solid currentColor;
  border-radius: 50%;
}

.icon-history .p2 {
  display: block;
  width: 0.12em;
  height: 0.28em;
  left: 0.45em;
  top: 0.28em;
  background: currentColor;
  border-radius: 0.12em;
}

.icon-history .p3 {
  display: block;
  width: 0.26em;
  height: 0.12em;
  left: 0.45em;
  top: 0.50em;
  background: currentColor;
  border-radius: 0.12em;
  transform-origin: left center;
  transform: rotate(25deg);
}

.icon-bell .p1 {
  display: block;
  width: 0.62em;
  height: 0.58em;
  left: 0.19em;
  top: 0.16em;
  border: 0.12em solid currentColor;
  border-bottom: 0;
  border-radius: 0.36em 0.36em 0.14em 0.14em;
}

.icon-bell .p2 {
  display: block;
  width: 0.76em;
  height: 0.12em;
  left: 0.12em;
  top: 0.70em;
  background: currentColor;
  border-radius: 0.12em;
}

.icon-bell .p3 {
  display: block;
  width: 0.18em;
  height: 0.10em;
  left: 0.41em;
  bottom: 0.09em;
  background: currentColor;
  border-radius: 0 0 0.10em 0.10em;
}

.icon-book .p1 {
  display: block;
  width: 0.76em;
  height: 0.78em;
  left: 0.12em;
  top: 0.11em;
  border: 0.11em solid currentColor;
  border-radius: 0.10em;
}

.icon-book .p2 {
  display: block;
  width: 0.10em;
  height: 0.74em;
  left: 0.47em;
  top: 0.13em;
  background: currentColor;
  opacity: 0.75;
}

.icon-book .p3,
.icon-calendar .p3 {
  display: block;
  width: 0.22em;
  height: 0.08em;
  right: 0.20em;
  top: 0.34em;
  background: currentColor;
  border-radius: 0.08em;
  opacity: 0.72;
}

.icon-mail .p1 {
  display: block;
  width: 0.82em;
  height: 0.62em;
  left: 0.09em;
  top: 0.19em;
  border: 0.11em solid currentColor;
  border-radius: 0.10em;
}

.icon-mail .p2,
.icon-mail .p3 {
  display: block;
  width: 0.44em;
  height: 0.11em;
  top: 0.46em;
  background: currentColor;
  border-radius: 0.11em;
}

.icon-mail .p2 {
  left: 0.13em;
  transform: rotate(34deg);
  transform-origin: left center;
}

.icon-mail .p3 {
  right: 0.13em;
  transform: rotate(-34deg);
  transform-origin: right center;
}

.icon-language .p1,
.icon-wifi .p1 {
  display: block;
  width: 0.76em;
  height: 0.76em;
  left: 0.12em;
  top: 0.12em;
  border: 0.11em solid currentColor;
  border-radius: 50%;
}

.icon-language .p2 {
  display: block;
  width: 0.11em;
  height: 0.70em;
  left: 0.445em;
  top: 0.15em;
  background: currentColor;
  border-radius: 0.10em;
  opacity: 0.72;
}

.icon-language .p3 {
  display: block;
  width: 0.66em;
  height: 0.11em;
  left: 0.17em;
  top: 0.445em;
  background: currentColor;
  border-radius: 0.10em;
  opacity: 0.72;
}

.icon-school .p1 {
  display: block;
  width: 0.72em;
  height: 0.40em;
  left: 0.14em;
  top: 0.20em;
  background: currentColor;
  transform: skewY(-16deg);
  border-radius: 0.06em;
}

.icon-school .p2 {
  display: block;
  width: 0.54em;
  height: 0.14em;
  left: 0.23em;
  bottom: 0.20em;
  background: currentColor;
  border-radius: 0.08em;
}

.icon-school .p3 {
  display: block;
  width: 0.10em;
  height: 0.32em;
  right: 0.18em;
  top: 0.42em;
  background: currentColor;
  border-radius: 0.08em;
}

.icon-lock .p1 {
  display: block;
  width: 0.42em;
  height: 0.32em;
  left: 0.29em;
  top: 0.12em;
  border: 0.11em solid currentColor;
  border-bottom: 0;
  border-radius: 0.26em 0.26em 0 0;
}

.icon-lock .p2 {
  display: block;
  width: 0.70em;
  height: 0.48em;
  left: 0.15em;
  bottom: 0.12em;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}

.icon-lock .p3 {
  display: block;
  width: 0.12em;
  height: 0.18em;
  left: 0.44em;
  top: 0.58em;
  background: currentColor;
  border-radius: 0.10em;
}

.icon-eye .p1,
.icon-eye-off .p1 {
  display: block;
  width: 0.78em;
  height: 0.48em;
  left: 0.11em;
  top: 0.26em;
  border: 0.11em solid currentColor;
  border-radius: 50%;
}

.icon-eye .p2,
.icon-eye-off .p2 {
  display: block;
  width: 0.20em;
  height: 0.20em;
  left: 0.40em;
  top: 0.40em;
  background: currentColor;
  border-radius: 50%;
}

.icon-eye-off .p3 {
  display: block;
  width: 0.90em;
  height: 0.12em;
  left: 0.05em;
  top: 0.44em;
  background: currentColor;
  border-radius: 0.12em;
  transform: rotate(-42deg);
}

.icon-chevron-down .p1 {
  display: block;
  width: 0.46em;
  height: 0.46em;
  left: 0.27em;
  top: 0.18em;
  border-right: 0.13em solid currentColor;
  border-bottom: 0.13em solid currentColor;
  transform: rotate(45deg);
}

.icon-card .p1 {
  display: block;
  width: 0.82em;
  height: 0.58em;
  left: 0.09em;
  top: 0.22em;
  border: 0.11em solid currentColor;
  border-radius: 0.10em;
}

.icon-card .p2 {
  display: block;
  width: 0.78em;
  height: 0.12em;
  left: 0.11em;
  top: 0.38em;
  background: currentColor;
}

.icon-card .p3 {
  display: block;
  width: 0.24em;
  height: 0.08em;
  left: 0.22em;
  bottom: 0.28em;
  background: currentColor;
  border-radius: 0.08em;
}

.icon-arrow_forward .p1,
.icon-arrow_back .p1,
.icon-chevron-right .p1,
.icon-external .p3,
.icon-corners-out .p1,
.icon-corners-in .p1,
.icon-logout .p1 {
  display: block;
  width: 0.50em;
  height: 0.50em;
  border-right: 0.13em solid currentColor;
  border-top: 0.13em solid currentColor;
}

.icon-arrow_forward .p1,
.icon-chevron-right .p1 {
  right: 0.22em;
  top: 0.25em;
  transform: rotate(45deg);
}

.icon-arrow_forward .p2 {
  display: block;
  width: 0.62em;
  height: 0.13em;
  left: 0.18em;
  top: 0.44em;
  background: currentColor;
  border-radius: 0.12em;
}

.icon-arrow_back .p1 {
  left: 0.22em;
  top: 0.25em;
  transform: rotate(-135deg);
}

.icon-arrow_back .p2 {
  display: block;
  width: 0.62em;
  height: 0.13em;
  right: 0.18em;
  top: 0.44em;
  background: currentColor;
  border-radius: 0.12em;
}

.icon-external .p1 {
  display: block;
  width: 0.58em;
  height: 0.58em;
  left: 0.12em;
  bottom: 0.12em;
  border: 0.10em solid currentColor;
  border-radius: 0.08em;
}

.icon-external .p2 {
  display: block;
  width: 0.48em;
  height: 0.12em;
  right: 0.12em;
  top: 0.28em;
  background: currentColor;
  border-radius: 0.10em;
  transform: rotate(-45deg);
}

.icon-external .p3 {
  right: 0.12em;
  top: 0.12em;
  width: 0.35em;
  height: 0.35em;
}

.icon-send .p1 {
  display: block;
  left: 0.13em;
  top: 0.16em;
  width: 0;
  height: 0;
  border-top: 0.34em solid transparent;
  border-bottom: 0.34em solid transparent;
  border-left: 0.76em solid currentColor;
}

.icon-send .p2 {
  display: block;
  width: 0.44em;
  height: 0.10em;
  left: 0.26em;
  top: 0.45em;
  background: rgba(255, 255, 255, 0.78);
  border-radius: 0.08em;
  transform: rotate(-10deg);
}

.icon-close .p1,
.icon-close .p2 {
  display: block;
  width: 0.76em;
  height: 0.13em;
  left: 0.12em;
  top: 0.44em;
  background: currentColor;
  border-radius: 0.12em;
}

.icon-close .p1 {
  transform: rotate(45deg);
}

.icon-close .p2 {
  transform: rotate(-45deg);
}

.icon-check .p1,
.icon-calendar-check .p4,
.icon-cloud-check .p4 {
  display: block;
  width: 0.62em;
  height: 0.33em;
  left: 0.20em;
  top: 0.31em;
  border-left: 0.13em solid currentColor;
  border-bottom: 0.13em solid currentColor;
  transform: rotate(-45deg);
  border-radius: 0.04em;
}

.icon-calendar .p1,
.icon-calendar-check .p1 {
  display: block;
  width: 0.78em;
  height: 0.72em;
  left: 0.11em;
  top: 0.16em;
  border: 0.11em solid currentColor;
  border-radius: 0.10em;
}

.icon-calendar .p2,
.icon-calendar-check .p2 {
  display: block;
  width: 0.78em;
  height: 0.12em;
  left: 0.11em;
  top: 0.34em;
  background: currentColor;
}

.icon-calendar-check .p4 {
  width: 0.34em;
  height: 0.19em;
  left: 0.35em;
  top: 0.55em;
  border-width: 0.10em;
}

.icon-camera .p1 {
  display: block;
  width: 0.78em;
  height: 0.54em;
  left: 0.11em;
  top: 0.30em;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}

.icon-camera .p2 {
  display: block;
  width: 0.30em;
  height: 0.18em;
  left: 0.24em;
  top: 0.18em;
  background: currentColor;
  border-radius: 0.08em 0.08em 0 0;
}

.icon-camera .p3 {
  display: block;
  width: 0.30em;
  height: 0.30em;
  left: 0.35em;
  top: 0.42em;
  border: 0.09em solid currentColor;
  border-radius: 50%;
}
.icon-call .p1 {
  display: block;
  width: 0.62em;
  height: 0.62em;
  left: 0.19em;
  top: 0.19em;
  border-left: 0.18em solid currentColor;
  border-bottom: 0.18em solid currentColor;
  border-radius: 0.18em;
  transform: rotate(-35deg);
}

.icon-headset .p1 {
  display: block;
  width: 0.76em;
  height: 0.76em;
  left: 0.12em;
  top: 0.12em;
  border: 0.11em solid currentColor;
  border-bottom-color: transparent;
  border-radius: 50%;
}

.icon-headset .p2,
.icon-headset .p3 {
  display: block;
  width: 0.16em;
  height: 0.30em;
  top: 0.45em;
  background: currentColor;
  border-radius: 0.08em;
}

.icon-headset .p2 {
  left: 0.13em;
}

.icon-headset .p3 {
  right: 0.13em;
}

.icon-headset .p4 {
  display: block;
  width: 0.34em;
  height: 0.10em;
  right: 0.20em;
  bottom: 0.14em;
  background: currentColor;
  border-radius: 0.10em;
}

.icon-bot .p1,
.icon-screen .p1 {
  display: block;
  width: 0.74em;
  height: 0.58em;
  left: 0.13em;
  top: 0.30em;
  border: 0.11em solid currentColor;
  border-radius: 0.16em;
}

.icon-bot .p2,
.icon-bot .p3 {
  display: block;
  width: 0.12em;
  height: 0.12em;
  top: 0.54em;
  background: currentColor;
  border-radius: 50%;
}

.icon-bot .p2 {
  left: 0.34em;
}

.icon-bot .p3 {
  right: 0.34em;
}

.icon-bot .p4 {
  display: block;
  width: 0.11em;
  height: 0.24em;
  left: 0.445em;
  top: 0.10em;
  background: currentColor;
  border-radius: 0.10em;
}

.icon-lightbulb .p1 {
  display: block;
  width: 0.56em;
  height: 0.56em;
  left: 0.22em;
  top: 0.10em;
  border: 0.11em solid currentColor;
  border-radius: 50%;
}

.icon-lightbulb .p2,
.icon-lightbulb .p3 {
  display: block;
  width: 0.36em;
  height: 0.10em;
  left: 0.32em;
  background: currentColor;
  border-radius: 0.10em;
}

.icon-lightbulb .p2 {
  bottom: 0.22em;
}

.icon-lightbulb .p3 {
  bottom: 0.09em;
}

.icon-help .p1,
.icon-info .p1 {
  display: block;
  width: 0.76em;
  height: 0.76em;
  left: 0.12em;
  top: 0.12em;
  border: 0.11em solid currentColor;
  border-radius: 50%;
}

.icon-help .p2,
.icon-info .p2 {
  display: block;
  width: 0.12em;
  height: 0.36em;
  left: 0.44em;
  top: 0.32em;
  background: currentColor;
  border-radius: 0.12em;
}

.icon-help .p3,
.icon-info .p3 {
  display: block;
  width: 0.13em;
  height: 0.13em;
  left: 0.435em;
  bottom: 0.18em;
  background: currentColor;
  border-radius: 50%;
}

.icon-megaphone .p1 {
  display: block;
  width: 0.48em;
  height: 0.42em;
  left: 0.13em;
  top: 0.26em;
  border-left: 0.16em solid currentColor;
  border-top: 0.12em solid transparent;
  border-bottom: 0.12em solid transparent;
}

.icon-megaphone .p2 {
  display: block;
  width: 0.30em;
  height: 0.56em;
  right: 0.12em;
  top: 0.22em;
  border: 0.11em solid currentColor;
  border-left: 0;
  border-radius: 0 0.32em 0.32em 0;
}

.icon-megaphone .p3 {
  display: block;
  width: 0.13em;
  height: 0.30em;
  left: 0.29em;
  bottom: 0.08em;
  background: currentColor;
  border-radius: 0.08em;
  transform: rotate(-16deg);
}

.icon-gate .p1,
.icon-meeting_room .p1 {
  display: block;
  width: 0.62em;
  height: 0.78em;
  left: 0.19em;
  top: 0.11em;
  border: 0.11em solid currentColor;
  border-radius: 0.20em 0.20em 0.06em 0.06em;
}

.icon-gate .p2,
.icon-meeting_room .p2 {
  display: block;
  width: 0.12em;
  height: 0.12em;
  right: 0.30em;
  top: 0.50em;
  background: currentColor;
  border-radius: 50%;
}

.icon-handyman .p1,
.icon-settings .p1 {
  display: block;
  width: 0.70em;
  height: 0.14em;
  left: 0.15em;
  top: 0.43em;
  background: currentColor;
  border-radius: 0.14em;
  transform: rotate(-45deg);
}

.icon-handyman .p2,
.icon-settings .p2 {
  display: block;
  width: 0.28em;
  height: 0.28em;
  right: 0.10em;
  top: 0.12em;
  border: 0.11em solid currentColor;
  border-radius: 50%;
}

.icon-heart .p1,
.icon-heart .p2 {
  display: block;
  width: 0.42em;
  height: 0.42em;
  top: 0.18em;
  background: currentColor;
  border-radius: 50%;
}

.icon-heart .p1 {
  left: 0.20em;
}

.icon-heart .p2 {
  right: 0.20em;
}

.icon-heart .p3 {
  display: block;
  width: 0.44em;
  height: 0.44em;
  left: 0.28em;
  top: 0.38em;
  background: currentColor;
  transform: rotate(45deg);
  border-radius: 0.08em;
}

.icon-hourglass .p1 {
  display: block;
  width: 0.62em;
  height: 0.76em;
  left: 0.19em;
  top: 0.12em;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}

.icon-hourglass .p2,
.icon-hourglass .p3 {
  display: block;
  width: 0.44em;
  height: 0.11em;
  left: 0.28em;
  background: currentColor;
  border-radius: 0.10em;
}

.icon-hourglass .p2 {
  top: 0.24em;
  transform: rotate(35deg);
}

.icon-hourglass .p3 {
  bottom: 0.24em;
  transform: rotate(-35deg);
}

.icon-podium .p1,
.icon-badge .p1 {
  display: block;
  width: 0.54em;
  height: 0.40em;
  left: 0.23em;
  top: 0.18em;
  border: 0.11em solid currentColor;
  border-radius: 0.12em;
}

.icon-podium .p2,
.icon-badge .p2 {
  display: block;
  width: 0.78em;
  height: 0.13em;
  left: 0.11em;
  bottom: 0.28em;
  background: currentColor;
  border-radius: 0.10em;
}

.icon-podium .p3,
.icon-badge .p3 {
  display: block;
  width: 0.50em;
  height: 0.13em;
  left: 0.25em;
  bottom: 0.12em;
  background: currentColor;
  border-radius: 0.10em;
}

.icon-cloud-check .p1 {
  display: block;
  width: 0.76em;
  height: 0.42em;
  left: 0.12em;
  bottom: 0.17em;
  border: 0.11em solid currentColor;
  border-radius: 0.24em;
}

.icon-cloud-check .p2,
.icon-cloud-check .p3 {
  display: block;
  background: currentColor;
  border-radius: 50%;
}

.icon-cloud-check .p2 {
  width: 0.34em;
  height: 0.34em;
  left: 0.25em;
  top: 0.20em;
}

.icon-cloud-check .p3 {
  width: 0.28em;
  height: 0.28em;
  right: 0.24em;
  top: 0.27em;
}

.icon-cloud-check .p4 {
  width: 0.30em;
  height: 0.18em;
  left: 0.38em;
  top: 0.55em;
  border-width: 0.09em;
  color: #ffffff;
}

.icon-screen .p2 {
  display: block;
  width: 0.32em;
  height: 0.10em;
  left: 0.34em;
  bottom: 0.08em;
  background: currentColor;
  border-radius: 0.08em;
}

.icon-wifi .p1 {
  border-left-color: transparent;
  border-right-color: transparent;
  border-bottom-color: transparent;
}

.icon-wifi .p2 {
  display: block;
  width: 0.50em;
  height: 0.50em;
  left: 0.25em;
  top: 0.36em;
  border: 0.11em solid currentColor;
  border-left-color: transparent;
  border-right-color: transparent;
  border-bottom-color: transparent;
  border-radius: 50%;
}

.icon-wifi .p3 {
  display: block;
  width: 0.13em;
  height: 0.13em;
  left: 0.435em;
  bottom: 0.13em;
  background: currentColor;
  border-radius: 50%;
}

.icon-corners-out .p1 {
  left: 0.12em;
  top: 0.12em;
  transform: rotate(-90deg);
}

.icon-corners-out .p2,
.icon-corners-in .p2 {
  display: block;
  width: 0.50em;
  height: 0.50em;
  border-right: 0.13em solid currentColor;
  border-top: 0.13em solid currentColor;
}

.icon-corners-out .p2 {
  right: 0.12em;
  bottom: 0.12em;
  transform: rotate(90deg);
}

.icon-corners-in .p1 {
  right: 0.12em;
  top: 0.12em;
  transform: rotate(90deg);
}

.icon-corners-in .p2 {
  left: 0.12em;
  bottom: 0.12em;
  transform: rotate(-90deg);
}

.icon-logout .p1 {
  right: 0.10em;
  top: 0.25em;
  transform: rotate(45deg);
}

.icon-logout .p2 {
  display: block;
  width: 0.56em;
  height: 0.13em;
  right: 0.16em;
  top: 0.44em;
  background: currentColor;
  border-radius: 0.12em;
}

.icon-logout .p3 {
  display: block;
  width: 0.34em;
  height: 0.66em;
  left: 0.10em;
  top: 0.17em;
  border: 0.11em solid currentColor;
  border-right: 0;
  border-radius: 0.08em 0 0 0.08em;
}

.icon-edit .p1 {
  display: block;
  width: 0.68em;
  height: 0.14em;
  left: 0.19em;
  top: 0.44em;
  background: currentColor;
  border-radius: 0.12em;
  transform: rotate(-45deg);
}

.icon-edit .p2 {
  display: block;
  width: 0.24em;
  height: 0.24em;
  right: 0.08em;
  top: 0.14em;
  border: 0.10em solid currentColor;
  transform: rotate(-45deg);
}
</style>

