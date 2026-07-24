/**
 * Shared service navigation helpers.
 */
import { showFeatureNotice } from './useFeatureNotice'

const SSO_LOGIN_URL = 'https://sso.sdfmu.edu.cn/login'

type ExternalOptions = {
  useSso?: boolean
  ssoNoAutoRedirect?: boolean
}

export function openAiQuestion(question: string) {
  uni.setStorageSync('chat_init_query', question)
  uni.switchTab({ url: '/pages/chat/index' })
}

function wrapSsoUrl(service: string, noAutoRedirect?: string): string {
  const params = new URLSearchParams()
  if (noAutoRedirect) {
    params.set('noAutoRedirect', noAutoRedirect)
  }
  params.set('service', service)
  return `${SSO_LOGIN_URL}?${params.toString()}`
}

export function buildSsoServiceUrl(url: string): string {
  return wrapSsoUrl(url, 'true')
}

function getEhallSsoService(target: string): string {
  return `https://ehall.sdfmu.edu.cn/site/login/cas-login?redirect_url=${encodeURIComponent(target)}`
}

function getPortalSsoService(): string {
  return 'https://portal.sdfmu.edu.cn/frontend/login/index?redirect=https://portal.sdfmu.edu.cn/'
}

function getAppSsoService(target: string): string {
  return `https://app.sdfmu.edu.cn/a_sdfmu/api/sso/index?redirect=${encodeURIComponent(target)}&from=wap`
}

function getAcademicSsoService(): string {
  const oauthUrl = `https://app.sdfmu.edu.cn/uc/api/oauth/index?redirect=${encodeURIComponent('http://academic.sdfmu.edu.cn/mrFjNnfHQI.php/index/asycn_user?redirect=apply%2Fshowlist')}&appid=200230220105459274&state=STATE&qrcode=1`
  return `https://app.sdfmu.edu.cn/a_sdfmu/api/sso/index?redirect=${encodeURIComponent(oauthUrl)}&from=wap`
}

function getSsoUrl(target: string, options: ExternalOptions): string {
  try {
    const { hostname } = new URL(target)
    const host = hostname.toLowerCase()

    if (host === 'app.sdfmu.edu.cn') {
      return wrapSsoUrl(getAppSsoService(target), '1')
    }
    if (host === 'academic.sdfmu.edu.cn') {
      return wrapSsoUrl(getAcademicSsoService(), '1')
    }
  } catch {
    // Fall through to the standard CAS service wrapper below.
  }

  return wrapSsoUrl(target, options.ssoNoAutoRedirect ? 'true' : undefined)
}

function getWechatSafeUrl(target: string): string {
  try {
    const { hostname } = new URL(target)
    const host = hostname.toLowerCase()

    if (host === 'ehall.sdfmu.edu.cn') {
      return wrapSsoUrl(getEhallSsoService(target), 'true')
    }
    if (host === 'portal.sdfmu.edu.cn') {
      return wrapSsoUrl(getPortalSsoService(), 'true')
    }
    if (host === 'app.sdfmu.edu.cn') {
      return wrapSsoUrl(getAppSsoService(target), '1')
    }
    if (host === 'academic.sdfmu.edu.cn') {
      return wrapSsoUrl(getAcademicSsoService(), '1')
    }
  } catch {
    return target
  }

  return target
}

function isWechatBrowser(): boolean {
  return typeof window !== 'undefined' && /MicroMessenger/i.test(window.navigator.userAgent)
}

export function openExternal(url: string, options: ExternalOptions = {}) {
  const target = url.trim()
  if (!target) return

  const ssoUrl = options.useSso ? getSsoUrl(target, options) : target

  // #ifdef H5
  const finalUrl = options.useSso ? ssoUrl : isWechatBrowser() ? getWechatSafeUrl(target) : target
  if (isWechatBrowser()) {
    window.location.href = finalUrl
  } else {
    window.open(finalUrl, '_blank', 'noopener,noreferrer')
  }
  // #endif
  // #ifndef H5
  const embeddedUrl = options.useSso ? ssoUrl : getWechatSafeUrl(target)
  uni.navigateTo({ url: `/pages/services/webview?url=${encodeURIComponent(embeddedUrl)}` })
  // #endif
}

export function openSsoExternal(url: string) {
  openExternal(url, { useSso: true, ssoNoAutoRedirect: true })
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
