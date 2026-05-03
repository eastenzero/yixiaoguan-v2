/**
 * 全局自定义 Dialog 状态管理
 * 组件 AppDialog.vue 消费此状态
 * 用法:
 *   const dialog = useDialog()
 *   await dialog.confirm({ title: '提示', content: '确定吗？' })
 *   dialog.alert({ title: '关于', content: '版本信息' })
 */
import { reactive } from 'vue'

export interface DialogOptions {
  title: string
  content: string
  icon?: string
  iconFill?: boolean
  confirmText?: string
  cancelText?: string
  confirmDanger?: boolean
}

export interface DialogState {
  visible: boolean
  title: string
  content: string
  icon: string
  iconFill: boolean
  confirmText: string
  cancelText: string
  confirmDanger: boolean
  mode: 'alert' | 'confirm'
  resolve: ((value: boolean) => void) | null
}

const state = reactive<DialogState>({
  visible: false,
  title: '',
  content: '',
  icon: '',
  iconFill: false,
  confirmText: '确定',
  cancelText: '取消',
  confirmDanger: false,
  mode: 'alert',
  resolve: null,
})

function open(mode: 'alert' | 'confirm', options: DialogOptions): Promise<boolean> {
  return new Promise((resolve) => {
    state.title = options.title
    state.content = options.content
    state.icon = options.icon || ''
    state.iconFill = options.iconFill ?? false
    state.confirmText = options.confirmText || '确定'
    state.cancelText = options.cancelText || '取消'
    state.confirmDanger = options.confirmDanger ?? false
    state.mode = mode
    state.resolve = resolve
    state.visible = true
  })
}

function close(result: boolean) {
  state.visible = false
  if (state.resolve) {
    state.resolve(result)
    state.resolve = null
  }
}

export function dialogAlert(options: DialogOptions): Promise<boolean> {
  return open('alert', { confirmText: '知道了', ...options })
}

export function dialogConfirm(options: DialogOptions): Promise<boolean> {
  return open('confirm', options)
}

export function dialogClose(result: boolean) {
  close(result)
}

export function useDialog() {
  return { state, alert: dialogAlert, confirm: dialogConfirm, close: dialogClose }
}
