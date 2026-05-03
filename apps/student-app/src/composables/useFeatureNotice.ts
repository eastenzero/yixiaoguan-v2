/**
 * 全局 FeatureNotice 弹层状态管理
 * 组件 FeatureNoticeSheet.vue 消费此状态
 */
import { reactive } from 'vue'
import { openAiQuestion } from './useServiceNavigation'

export interface FeatureNoticeOptions {
  title: string
  description?: string
  icon?: string
  primaryText?: string
  secondaryText?: string
  suggestedQuestion?: string
}

export interface FeatureNoticeState {
  visible: boolean
  title: string
  description: string
  icon: string
  primaryText: string
  secondaryText: string
  suggestedQuestion: string | undefined
}

const state = reactive<FeatureNoticeState>({
  visible: false,
  title: '',
  description: '',
  icon: 'construction',
  primaryText: '问问医小管',
  secondaryText: '我知道了',
  suggestedQuestion: undefined,
})

export function showFeatureNotice(options: FeatureNoticeOptions) {
  state.title = options.title
  state.description = options.description || '该功能正在建设中，敬请期待。\n你可以先让医小管帮你查询相关流程和入口。'
  state.icon = options.icon || 'construction'
  state.primaryText = options.primaryText || '问问医小管'
  state.secondaryText = options.secondaryText || '我知道了'
  state.suggestedQuestion = options.suggestedQuestion
  state.visible = true
}

export function hideFeatureNotice() {
  state.visible = false
}

export function onFeatureNoticePrimary() {
  if (state.suggestedQuestion) {
    openAiQuestion(state.suggestedQuestion)
  }
  state.visible = false
}

export function useFeatureNotice() {
  return { state, show: showFeatureNotice, hide: hideFeatureNotice, onPrimary: onFeatureNoticePrimary }
}
