<template>
  <view class="login-page">
    <view class="bg-decor">
      <view class="orb orb-1" />
      <view class="orb orb-2" />
      <view class="orb orb-3" />
    </view>

    <view class="main-container">
      <view class="login-card animate-fade-up">
        <view class="header">
          <view class="logo-box">
            <text class="material-symbols-outlined logo-icon">school</text>
          </view>
          <text class="app-title">医小管</text>
          <text class="app-subtitle">智慧校园服务平台</text>
        </view>

        <view class="form">
          <view class="form-group">
            <text class="label">学号 / STUDENT ID</text>
            <view class="input-wrapper">
              <text class="material-symbols-outlined input-icon">person</text>
              <input
                class="input"
                type="text"
                v-model="form.staffId"
                placeholder="请输入您的学号"
                placeholder-class="ph-color"
              />
            </view>
          </view>

          <view class="form-group">
            <text class="label">密码 / PASSWORD</text>
            <view class="input-wrapper">
              <text class="material-symbols-outlined input-icon">lock</text>
              <input
                class="input"
                :type="showPwd ? 'text' : 'password'"
                v-model="form.password"
                placeholder="请输入密码"
                placeholder-class="ph-color"
                @confirm="handleLogin"
              />
              <view class="right-action" @click="showPwd = !showPwd">
                <text class="material-symbols-outlined right-icon">{{ showPwd ? 'visibility' : 'visibility_off' }}</text>
              </view>
            </view>
          </view>

          <button class="submit-btn" :disabled="loading" @click="handleLogin">
            <text class="btn-text">{{ loading ? '登录中...' : '立即登录' }}</text>
            <text v-if="!loading" class="material-symbols-outlined btn-icon">arrow_forward</text>
          </button>
        </view>

        <view class="forgot-box">
          <text class="forgot-text">忘记密码？</text>
        </view>
      </view>

      <view class="footer-box animate-fade-up delay-2">
        <text class="footer-hint">初始密码与学号相同</text>
        <view class="footer-links">
          <text class="link-text">隐私政策</text>
          <view class="link-dot" />
          <text class="link-text">服务协议</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { login, getMe } from '@/api/auth'
import { wsManager } from '@/utils/websocket'

const userStore = useUserStore()

const form = reactive({ staffId: '', password: '' })
const showPwd = ref(false)
const loading = ref(false)

async function handleLogin() {
  if (!form.staffId.trim()) {
    uni.showToast({ title: '请输入学号', icon: 'none' }); return
  }
  if (!form.password) {
    uni.showToast({ title: '请输入密码', icon: 'none' }); return
  }

  loading.value = true
  try {
    const res = await login(form.staffId.trim(), form.password)
    userStore.setToken(res.access_token)

    const me = await getMe()
    userStore.setUserInfo(me)

    wsManager.connect(res.access_token)

    uni.showToast({ title: '登录成功', icon: 'success', duration: 1000 })
    setTimeout(() => {
      uni.switchTab({ url: '/pages/home/index' })
    }, 1000)
  } catch (e: any) {
    uni.showToast({ title: e?.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
@import '@/styles/tokens.scss';
@import '@/styles/theme.scss';

.login-page {
  position: relative;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: $space-6;
  box-sizing: border-box;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 50%, $primary-10 100%);
  overflow: hidden;
}

// ── Decorative orbs ──────────────────────────────────
.bg-decor {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.orb {
  position: absolute;
  border-radius: $radius-full;
  filter: blur(60px);
}

.orb-1 {
  top: -10%;
  left: -10%;
  width: 60%;
  aspect-ratio: 1;
  background: rgba($bg-card, 0.18);
}

.orb-2 {
  bottom: -15%;
  right: -10%;
  width: 65%;
  aspect-ratio: 1;
  background: rgba($primary-60, 0.30); // violet-400 alpha
}

.orb-3 {
  top: 35%;
  left: 50%;
  transform: translateX(-50%);
  width: 90%;
  aspect-ratio: 1;
  background: rgba($primary-70, 0.10); // violet-300 alpha
  filter: blur(80px);
}

// ── Container ────────────────────────────────────────
.main-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

// ── Glass card ───────────────────────────────────────
.login-card {
  background: rgba($bg-card, 0.96);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border-radius: $radius-xl;
  padding: $space-10 $space-6 $space-8;
  box-shadow: 0 32px 64px -12px rgba($text-primary, 0.20),
              0 0 0 1px rgba($bg-card, 0.40) inset;
}

.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: $space-8;
}

.logo-box {
  width: 88px;
  height: 88px;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  border-radius: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: $space-5;
  box-shadow: 0 16px 32px -8px rgba($primary, 0.50),
              0 4px 12px -2px rgba($primary, 0.30);
  transform: rotate(3deg);
}

.logo-icon {
  font-size: 44px;
  color: $text-inverse;
  font-variation-settings: 'FILL' 1, 'wght' 500, 'GRAD' 0, 'opsz' 24;
  transform: rotate(-3deg);
}

.app-title {
  font-size: 30px;
  font-weight: 800;
  color: $text-primary;
  letter-spacing: -0.02em;
  margin-bottom: $space-2;
}

.app-subtitle {
  font-size: $font-size-xs;
  font-weight: $font-weight-semibold;
  color: $text-secondary;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

// ── Form ─────────────────────────────────────────────
.form {
  display: flex;
  flex-direction: column;
  gap: $space-5;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.label {
  font-size: 11px;
  font-weight: $font-weight-bold;
  color: $text-secondary;
  letter-spacing: 0.10em;
  margin-left: $space-2;
  text-transform: uppercase;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  background: $surface-container-low;
  border-radius: $radius-md;
  padding: 0 $space-4;
  height: 56px;
  border: 1px solid transparent;
  transition: border-color 0.18s ease-out, background 0.18s ease-out, box-shadow 0.18s ease-out;
}

.input-wrapper:focus-within {
  background: $bg-card;
  border-color: rgba($primary, 0.35);
  box-shadow: 0 0 0 4px rgba($primary, 0.10);
}

.input {
  flex: 1;
  height: 100%;
  background: transparent;
  border: none;
  outline: none;
  padding-left: 32px;
  font-size: $font-size-base;
  font-family: $font-family-sans;
  font-weight: $font-weight-medium;
  color: $text-primary;
}

.ph-color {
  color: $text-muted;
}

.input-icon {
  font-size: 20px;
  color: $text-muted;
  position: absolute;
  left: $space-4;
}

.right-action {
  position: absolute;
  right: $space-2;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $radius-full;
  transition: background 0.18s ease-out;
}

.right-action:active {
  background: rgba($primary, 0.10);
}

.right-icon {
  font-size: 20px;
  color: $text-muted;
}

// ── Submit ───────────────────────────────────────────
.submit-btn {
  width: 100%;
  height: 56px;
  margin-top: $space-3;
  background: linear-gradient(135deg, $primary 0%, $primary-hover 100%);
  border-radius: $radius-full;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;
  border: none;
  box-shadow: 0 12px 24px -8px rgba($primary, 0.50),
              0 4px 8px -2px rgba($primary, 0.25);
  transition: transform 0.18s ease-out, box-shadow 0.18s ease-out, opacity 0.18s ease-out;
}

.submit-btn:active {
  transform: scale(0.98);
  box-shadow: 0 8px 16px -6px rgba($primary, 0.45);
}

.submit-btn[disabled] {
  opacity: 0.65;
  box-shadow: 0 4px 12px -4px rgba($primary, 0.20);
}

.submit-btn::after {
  border: none;
}

.btn-text {
  color: $text-inverse;
  font-size: $font-size-base;
  font-weight: $font-weight-bold;
  letter-spacing: 0.02em;
}

.btn-icon {
  font-size: 20px;
  color: $text-inverse;
}

// ── Forgot link ──────────────────────────────────────
.forgot-box {
  margin-top: $space-5;
  display: flex;
  justify-content: center;
}

.forgot-text {
  font-size: $font-size-xs;
  color: $primary;
  font-weight: $font-weight-bold;
  letter-spacing: 0.02em;
}

// ── Footer ───────────────────────────────────────────
.footer-box {
  margin-top: $space-8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
}

.footer-hint {
  font-size: $font-size-sm;
  font-weight: $font-weight-medium;
  color: rgba($bg-card, 0.75);
  letter-spacing: 0.05em;
}

.footer-links {
  display: flex;
  align-items: center;
  gap: $space-4;
}

.link-text {
  font-size: 11px;
  color: rgba($bg-card, 0.55);
  letter-spacing: 0.10em;
  text-transform: uppercase;
  font-weight: $font-weight-semibold;
}

.link-dot {
  width: 4px;
  height: 4px;
  background: rgba($bg-card, 0.30);
  border-radius: $radius-full;
}
</style>
