<template>
  <view class="login-page">
    <view class="bg-decor">
      <view class="decor-circle decor-1" />
      <view class="decor-circle decor-2" />
    </view>
    <view class="main-container">
      <view class="login-card">
        <view class="header">
          <view class="logo-box">
            <text class="material-symbols-outlined logo-icon" style="font-variation-settings: 'FILL' 1">school</text>
          </view>
          <text class="app-title">医小管</text>
          <text class="app-subtitle">智慧校园服务平台</text>
        </view>

        <view class="form">
          <view class="form-group">
            <text class="label">学号</text>
            <view class="input-wrapper">
              <text class="material-symbols-outlined input-icon">person</text>
              <input class="input" type="text" v-model="form.staffId" placeholder="请输入您的学号" placeholder-class="ph-color" />
            </view>
          </view>

          <view class="form-group">
            <text class="label">密码</text>
            <view class="input-wrapper">
              <text class="material-symbols-outlined input-icon">lock</text>
              <input class="input" :type="showPwd ? 'text' : 'password'" v-model="form.password" placeholder="请输入密码" placeholder-class="ph-color" @confirm="handleLogin" />
              <text class="material-symbols-outlined right-icon" @click="showPwd = !showPwd">{{ showPwd ? 'visibility' : 'visibility_off' }}</text>
            </view>
          </view>

          <button class="submit-btn" :disabled="loading" @click="handleLogin">
            <text class="btn-text">{{ loading ? '登录中...' : '登录' }}</text>
            <text class="material-symbols-outlined btn-icon">arrow_forward</text>
          </button>
        </view>

        <view class="forgot-box">
          <text class="forgot-text">忘记密码？</text>
        </view>
      </view>

      <view class="footer-box">
        <text class="footer-hint">初始密码与学号相同</text>
        <view class="footer-links">
          <text class="link-text">隐私政策</text>
          <view class="dot" />
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
import { centrifugeManager } from '@/utils/centrifuge'

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
    // 二次校验：确认返回角色为 student
    if (me.role !== 'student') {
      userStore.logout()
      uni.showToast({ title: '该账号不属于学生端，请使用正确的客户端登录', icon: 'none' })
      return
    }
    userStore.setUserInfo(me)

    wsManager.connect(res.access_token)
    if (res.centrifugo_token) {
      centrifugeManager.connect(res.centrifugo_token)
    }

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

.login-page {
  min-height: 100vh;
  background: linear-gradient(135deg, $primary, $secondary);
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  box-sizing: border-box;
}
.bg-decor { position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 0; }
.decor-circle { position: absolute; border-radius: 50%; }
.decor-1 { top: -10%; left: -10%; width: 40%; height: 40%; background: rgba(255,255,255,0.05); filter: blur(50px); }
.decor-2 { top: 60%; right: -5%; width: 30%; height: 30%; background: rgba(178,140,255,0.20); filter: blur(40px); }

.main-container { width: 100%; max-width: 25rem; z-index: 1; }
.login-card { background: $surface-container-lowest; border-radius: $radius-lg; padding: 2.5rem 1.75rem; box-shadow: $shadow-fab; }
.header { display: flex; flex-direction: column; align-items: center; margin-bottom: 2rem; }
.logo-box { width: 4rem; height: 4rem; background: rgba($primary-container, 0.30); border-radius: $radius-md; display: flex; align-items: center; justify-content: center; margin-bottom: 0.75rem; }
.logo-icon { font-size: 2.25rem; color: $secondary; }
.app-title { font-size: 1.875rem; font-weight: 800; color: $text-primary; margin-bottom: 0.25rem; }
.app-subtitle { font-size: 0.875rem; font-weight: 500; color: $text-secondary; letter-spacing: 0.125rem; opacity: 0.7; }

.form .form-group { margin-bottom: 1.25rem; }
.label { font-size: 0.75rem; font-weight: 700; color: $text-secondary; margin-bottom: 0.5rem; margin-left: 0.25rem; display: block; }
.input-wrapper { position: relative; display: flex; align-items: center; background: $surface-container-high; border-radius: $radius-md; padding: 0 1rem; height: 3.25rem; }
.input { flex: 1; height: 100%; background: transparent; border: none; padding-left: 1.75rem; font-size: 0.875rem; color: $text-primary; font-weight: 500; }
.ph-color { color: $text-muted; }
.input-icon { font-size: 1.25rem; color: $text-muted; position: absolute; left: 1rem; }
.right-icon { font-size: 1.25rem; color: $text-muted; position: absolute; right: 1rem; }

.submit-btn { width: 100%; height: 3.5rem; background: linear-gradient(135deg, $primary, $primary-container); border-radius: $radius-full; display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin-top: 1.75rem; box-shadow: $shadow-fab; }
.submit-btn:active { transform: scale(0.95); }
.submit-btn[disabled] { opacity: 0.7; }
.btn-text { color: $text-inverse; font-size: 1rem; font-weight: 700; }
.btn-icon { font-size: 1.125rem; color: $text-inverse; }

.forgot-box { margin-top: 1.5rem; display: flex; justify-content: center; }
.forgot-text { font-size: 0.75rem; color: $primary; font-weight: 600; text-decoration: underline; }

.footer-box { margin-top: 2rem; display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.footer-hint { font-size: 0.875rem; color: rgba(255,255,255,0.6); font-weight: 500; }
.footer-links { display: flex; align-items: center; gap: 1.5rem; }
.link-text { font-size: 0.75rem; color: rgba(255,255,255,0.4); }
.dot { width: 0.25rem; height: 0.25rem; background: rgba(255,255,255,0.2); border-radius: 50%; }
</style>
