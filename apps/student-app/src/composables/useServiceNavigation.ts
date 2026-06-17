/**
 * Shared service navigation helpers.
 */
import { showFeatureNotice } from './useFeatureNotice'

const SSO_LOGIN_URL = 'https://sso.sdfmu.edu.cn/login'

type ExternalOptions = {
  useSso?: boolean
}

export function openAiQuestion(question: string) {
  uni.setStorageSync('chat_init_query', question)
  uni.switchTab({ url: '/pages/chat/index' })
}

function wrapSsoUrl(target: string): string {
  const params = new URLSearchParams({
    noAutoRedirect: 'true',
    service: target,
  })
  return `${SSO_LOGIN_URL}?${params.toString()}`
}

function shouldUseSso(target: string): boolean {
  try {
    const host = new URL(target).hostname.toLowerCase()
    return host.endsWith('.sdfmu.edu.cn') && host !== 'www.sdfmu.edu.cn'
  } catch {
    return false
  }
}

function isWechatBrowser(): boolean {
  return typeof window !== 'undefined' && /MicroMessenger/i.test(window.navigator.userAgent)
}

export function openExternal(url: string, options: ExternalOptions = {}) {
  const target = url.trim()
  if (!target) return

  const finalUrl = options.useSso || shouldUseSso(target) ? wrapSsoUrl(target) : target

  // #ifdef H5
  if (isWechatBrowser()) {
    window.location.href = finalUrl
  } else {
    window.open(finalUrl, '_blank', 'noopener,noreferrer')
  }
  // #endif
  // #ifndef H5
  uni.navigateTo({ url: `/pages/services/webview?url=${encodeURIComponent(finalUrl)}` })
  // #endif
}

export function showComingSoon(featureName: string, suggestedQuestion?: string) {
  showFeatureNotice({
    title: featureName,
    suggestedQuestion,
    icon: suggestedQuestion ? 'construction' : 'hourglass_empty',
    description: suggestedQuestion
      ? '该功能正在接入中\n你可以先让医小管帮你查询办理流程、材料和入口。'
      : '该功能正在建设中，敬请期待。',
  })
}
