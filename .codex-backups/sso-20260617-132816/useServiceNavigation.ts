/**
 * 共享服务导航工具函数
 * - openAiQuestion: 跳转智能问答并自动发送预设问题
 * - openExternal: 打开外部链接（H5 新标签页 / App webview）
 * - showComingSoon: 建设中弹层 + 可选"问问医小管"引导（使用自定义 FeatureNoticeSheet）
 */
import { showFeatureNotice } from './useFeatureNotice'

export function openAiQuestion(question: string) {
  uni.setStorageSync('chat_init_query', question)
  uni.switchTab({ url: '/pages/chat/index' })
}

export function openExternal(url: string) {
  // #ifdef H5
  window.open(url, '_blank')
  // #endif
  // #ifndef H5
  uni.navigateTo({ url: `/pages/services/webview?url=${encodeURIComponent(url)}` })
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
