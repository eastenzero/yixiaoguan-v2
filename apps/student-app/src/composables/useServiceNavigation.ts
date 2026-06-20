/**
 * Shared service navigation helpers.
 */
import { showFeatureNotice } from './useFeatureNotice'

const SSO_LOGIN_URL = 'https://sso.sdfmu.edu.cn/login'

export function openAiQuestion(question: string) {
  uni.setStorageSync('chat_init_query', question)
  uni.switchTab({ url: '/pages/chat/index' })
}

function wrapSsoUrl(service: string, noAutoRedirect = 'true'): string {
  const params = new URLSearchParams()
  params.set('noAutoRedirect', noAutoRedirect)
  params.set('service', service)
  return `${SSO_LOGIN_URL}?${params.toString()}`
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

function getWechatSafeUrl(target: string): string {
  try {
    const { hostname } = new URL(target)
    const host = hostname.toLowerCase()

    if (host === 'ehall.sdfmu.edu.cn') {
      return wrapSsoUrl(getEhallSsoService(target))
    }
    if (host === 'portal.sdfmu.edu.cn') {
      return wrapSsoUrl(getPortalSsoService())
    }
    if (host === 'app.sdfmu.edu.cn') {
      return wrapSsoUrl(getAppSsoService(target), '1')
    }
    if (host === 'academic.sdfmu.edu.cn') {
      return wrapSsoUrl(getAcademicSsoService(), '1')
    }
    if (host === 'vpnportal.sdfmu.edu.cn' || host === 'fpc.sdfmu.edu.cn' || host === 'ppu.sdfmu.edu.cn') {
      return wrapSsoUrl(target)
    }
  } catch {
    return target
  }

  return target
}

function isWechatBrowser(): boolean {
  return typeof window !== 'undefined' && /MicroMessenger/i.test(window.navigator.userAgent)
}

export function openExternal(url: string) {
  const target = url.trim()
  if (!target) return

  // #ifdef H5
  const finalUrl = isWechatBrowser() ? getWechatSafeUrl(target) : target
  if (isWechatBrowser()) {
    window.location.href = finalUrl
  } else {
    window.open(finalUrl, '_blank', 'noopener,noreferrer')
  }
  // #endif
  // #ifndef H5
  const embeddedUrl = getWechatSafeUrl(target)
  uni.navigateTo({ url: `/pages/services/webview?url=${encodeURIComponent(embeddedUrl)}` })
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
