<template>
  <view class="login-page">
    <!-- 装饰光晕圆 -->
    <view class="bg-orbs">
      <view class="orb orb-1"></view>
      <view class="orb orb-2"></view>
    </view>

    <!-- 中央登录卡片 -->
    <view class="card-wrapper animate-fade-up">
      <view class="login-card">
        <!-- Logo 区域 -->
        <view class="logo-area">
          <view class="logo-icon">
            <IconGraduationCap :size="48" color="#ffffff" />
          </view>
          <text class="logo-title">医小管</text>
          <text class="logo-subtitle">教师工作台</text>
        </view>

        <!-- 表单区域 -->
        <view class="form-section">
          <!-- 用户名输入框 -->
          <view class="input-group">
            <text class="input-label">USERNAME</text>
            <view class="input-wrapper">
              <view class="input-icon">
                <IconUser :size="20" :color="primaryColor" />
              </view>
              <input
                v-model="username"
                class="input-field"
                type="text"
                placeholder="请输入教师工号"
              />
            </view>
          </view>

          <!-- 密码输入框 -->
          <view class="input-group">
            <text class="input-label">PASSWORD</text>
            <view class="input-wrapper">
              <view class="input-icon">
                <IconLock :size="20" :color="primaryColor" />
              </view>
              <input
                v-model="password"
                class="input-field"
                :type="showPassword ? 'text' : 'password'"
                placeholder="请输入登录密码"
              />
              <view class="input-action" @click="togglePasswordVisibility">
                <IconEye :size="20" :color="onSurfaceVariantColor" />
              </view>
            </view>
          </view>

          <!-- 验证码区域 -->
          <view v-if="captchaEnabled" class="input-group">
            <text class="input-label">验证码</text>
            <view class="captcha-row">
              <view class="input-wrapper captcha-input">
                <input
                  v-model="captchaCode"
                  class="input-field"
                  type="text"
                  placeholder="请输入验证码"
                />
              </view>
              <image 
                v-if="captchaImg" 
                class="captcha-image" 
                :src="captchaImg" 
                mode="aspectFit"
                @click="refreshCaptcha"
              />
              <view v-else class="captcha-image captcha-placeholder" @click="refreshCaptcha">
                <text class="captcha-placeholder-text">点击刷新</text>
              </view>
            </view>
          </view>

          <!-- 记住我和忘记密码 -->
          <view class="form-options">
            <view class="remember-me" @click="toggleRememberMe">
              <view class="checkbox" :class="{ 'checkbox--checked': rememberMe }">
                <IconCheck v-if="rememberMe" :size="12" color="#ffffff" stroke-width="3" />
              </view>
              <text class="remember-text">记住我</text>
            </view>
            <text class="forgot-link" @click="handleForgotPassword">忘记密码？</text>
          </view>

          <!-- 登录按钮 -->
          <button class="login-btn" :disabled="loading" @click="handleLogin">
            <text class="login-btn-text">{{ loading ? '登录中...' : '立即登录' }}</text>
            <IconArrowRight v-if="!loading" :size="20" color="#ffffff" />
          </button>
        </view>

        <!-- 其他登录方式（暂未对接，隐藏） -->
      </view>
    </view>

    <!-- Footer -->
    <view class="footer animate-fade-up delay-2">
      <text class="footer-text">山东第一医科大学 · 医小管智能管理系统</text>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { login as loginApi, getUserInfo } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { useWsStore } from '@/stores/websocket'
import IconGraduationCap from '../../components/icons/IconGraduationCap.vue'
import IconUser from '../../components/icons/IconUser.vue'
import IconLock from '../../components/icons/IconLock.vue'
import IconEye from '../../components/icons/IconEye.vue'
import IconCheck from '../../components/icons/IconCheck.vue'
import IconArrowRight from '../../components/icons/IconArrowRight.vue'

// 主题色（用于动态绑定）
const primaryColor = '#5b21b6'
const onSurfaceVariantColor = '#5d5b5f'

// 用户状态
const userStore = useUserStore()
const wsStore = useWsStore()

// 表单数据
const username = ref('')
const password = ref('')
const captchaEnabled = ref(false) // v2 无验证码
const loading = ref(false)
const rememberMe = ref(true)
const showPassword = ref(false)

// 切换密码可见性
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value
}

// 切换记住我
const toggleRememberMe = () => {
  rememberMe.value = !rememberMe.value
}

// 登录处理
const handleLogin = async () => {
  const staffId = username.value.trim()
  const pwd = password.value.trim()
  if (!staffId || !pwd) {
    uni.showToast({ title: '请输入工号和密码', icon: 'none' })
    return
  }
  loading.value = true
  try {
    const loginRes = await loginApi({
      staff_id: staffId,
      password: pwd
    })
    userStore.setToken(loginRes.access_token)
    
    // 获取用户信息
    const userInfo = await getUserInfo()
    // 二次校验：确认返回角色为 teacher 或 admin
    if (userInfo.role !== 'teacher' && userInfo.role !== 'admin') {
      userStore.clearAuth()
      uni.showToast({ title: '该账号不属于教师端，请使用正确的客户端登录', icon: 'none' })
      return
    }
    userStore.setUserInfo(userInfo as any)
    
    // 建立 WebSocket 连接
    wsStore.init(loginRes.access_token, loginRes.centrifugo_token)
    
    uni.switchTab({ url: '/pages/dashboard/index' })
  } catch (e: any) {
    uni.showToast({ title: e?.message || '登录失败', icon: 'none' })
  } finally {
    loading.value = false
  }
}

// 忘记密码
const handleForgotPassword = () => {
  uni.showToast({ title: '请联系管理员', icon: 'none' })
}

</script>

<style lang="scss" scoped>
.login-page {
  position: relative;
  min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, $primary-fixed-dim, $primary, $primary-dim);
  overflow: hidden;
}

// 装饰光晕圆
.bg-orbs {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
}

.orb-1 {
  top: -10%;
  left: -10%;
  width: 60%;
  height: 40%;
  background: rgba($secondary-container, 0.2);
}

.orb-2 {
  bottom: -10%;
  right: -10%;
  width: 50%;
  height: 50%;
  background: rgba($primary-container, 0.3);
}

// 卡片包装器
.card-wrapper {
  position: relative;
  width: 100%;
  max-width: 400px;
  padding: 0 24px;
}

// 登录卡片
.login-card {
  background: rgba($surface-container-lowest, 0.95);
  backdrop-filter: blur(40px);
  -webkit-backdrop-filter: blur(40px);
  border-radius: $radius-lg;                   // 2rem MD3
  padding: 40px 32px;
  box-shadow: $shadow-fab;                     // No-Shadow: 紫色折射取代中性灰
  // No-Line: 去掉 1px solid glass border
}

// Logo 区域
.logo-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32px;
}

.logo-icon {
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, $primary, $primary-container);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba($primary, 0.3);
  transform: rotate(3deg);
}

.logo-title {
  font-family: $font-headline;
  font-size: 28px;
  font-weight: 800;
  color: $on-surface;
  margin-bottom: 8px;
  letter-spacing: -0.02em;
}

.logo-subtitle {
  font-family: $font-body;
  font-size: 14px;
  font-weight: 500;
  color: $on-surface-variant;
  letter-spacing: 0.1em;
}

// 表单区域
.form-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-label {
  font-family: $font-label;
  font-size: 11px;
  font-weight: 700;
  color: $on-surface-variant;
  margin-left: 8px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.input-field {
  width: 100%;
  height: 56px;
  padding-left: 48px;
  padding-right: 16px;
  background: $surface-container-low;
  border-radius: 12px;
  border: none;
  outline: none;
  font-family: $font-body;
  font-size: 15px;
  color: $on-surface;
  
  &::placeholder {
    color: rgba($on-surface-variant, 0.5);
  }
}

// 验证码区域
.captcha-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.captcha-input {
  flex: 1;
  
  .input-field {
    padding-left: 16px;
  }
}

.captcha-image {
  width: 120px;
  height: 56px;
  border-radius: 12px;
  background: $surface-container-low;
}

.captcha-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed $outline-variant;
}

.captcha-placeholder-text {
  font-family: $font-body;
  font-size: 12px;
  color: $on-surface-variant;
}

.input-action {
  position: absolute;
  right: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
}

// 表单选项
.form-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 4px;
  margin-top: 4px;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
}

.checkbox {
  width: 20px;
  height: 20px;
  background: $surface-container;
  border: 2px solid $outline-variant;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  
  &--checked {
    background: $primary;
    border-color: $primary;
  }
}

.remember-text {
  font-family: $font-body;
  font-size: 14px;
  font-weight: 500;
  color: $on-surface-variant;
}

.forgot-link {
  font-family: $font-body;
  font-size: 14px;
  font-weight: 600;
  color: $primary;
}

// 登录按钮
.login-btn {
  width: 100%;
  height: 56px;
  margin-top: 16px;
  background: linear-gradient(to right, $primary, $primary-container);
  border-radius: 9999px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: 0 8px 20px -4px rgba($primary, 0.4);
  border: none;
  
  &:active {
    transform: scale(0.98);
  }
  
  &:disabled {
    opacity: 0.7;
  }
}

.login-btn-text {
  font-family: $font-headline;
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
}

// 其他登录方式
.alt-login {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid $surface-container-high;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.alt-login-title {
  font-family: $font-body;
  font-size: 12px;
  font-weight: 500;
  color: $on-surface-variant;
  margin-bottom: 16px;
}

.alt-login-buttons {
  display: flex;
  gap: 24px;
}

.alt-login-btn {
  width: 44px;
  height: 44px;
  background: $surface-container;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:active {
    background: $surface-container-high;
  }
}

// Footer
.footer {
  margin-top: 48px;
  text-align: center;
  padding: 0 24px;
}

.footer-text {
  font-family: $font-body;
  font-size: 12px;
  font-weight: 500;
  color: rgba($on-primary-fixed, 0.7);
  letter-spacing: 0.05em;
}

.footer-copyright {
  font-family: $font-body;
  font-size: 10px;
  font-weight: 500;
  color: rgba($on-primary-fixed, 0.4);
  margin-top: 8px;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

// 动画
.animate-fade-up {
  opacity: 0;
  animation: fadeUp 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
}

.delay-2 {
  animation-delay: 0.2s;
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
