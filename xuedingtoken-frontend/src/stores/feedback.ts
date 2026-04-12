import { defineStore } from 'pinia'
import { ref, inject, type Ref, type InjectionKey } from 'vue'
import type { GlobalConfirmInstance } from '@/components/common/GlobalConfirm.types'

export interface Toast {
  id: number
  message: string
  type: 'success' | 'error' | 'info' | 'warning'
}

const CONFIRM_KEY: InjectionKey<Ref<GlobalConfirmInstance | null>> = Symbol('GlobalConfirm')

export { CONFIRM_KEY }

export const useFeedbackStore = defineStore('feedback', () => {
  const toasts = ref<Toast[]>([])

  const push = (message: string, type: Toast['type'] = 'info') => {
    const id = Date.now()
    toasts.value.push({ id, message, type })
    setTimeout(() => {
      toasts.value = toasts.value.filter((t: Toast) => t.id !== id)
    }, 3000)
  }

  const success = (msg: string) => push(msg, 'success')
  const error = (msg: string) => push(msg, 'error')
  const info = (msg: string) => push(msg, 'info')
  const warning = (msg: string) => push(msg, 'warning')

  // inject at call-time (not store creation time) so confirmRef is resolved after App.vue mounts
  const confirm = async (opts: {
    title?: string
    message?: string
    confirmText?: string
    cancelText?: string
    danger?: boolean
  }): Promise<boolean> => {
    const confirmRef = inject(CONFIRM_KEY)
    if (confirmRef?.value) {
      return confirmRef.value.open(opts)
    }
    return Promise.resolve(false)
  }

  return { toasts, push, success, error, info, warning, confirm }
})
