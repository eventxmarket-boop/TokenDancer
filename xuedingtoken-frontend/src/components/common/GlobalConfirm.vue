<template>
  <Teleport to="body">
    <div v-if="visible" class="confirm-overlay" @click.self="cancel">
      <div class="confirm-box" :class="{ danger: opts?.danger }">
        <div class="confirm-header">
          <h3>{{ opts?.title || '确认' }}</h3>
        </div>
        <div class="confirm-body">
          <p>{{ opts?.message || '' }}</p>
        </div>
        <div class="confirm-footer">
          <button class="btn btn-outline" @click="cancel">{{ opts?.cancelText || '取消' }}</button>
          <button class="btn" :class="opts?.danger ? 'btn-danger' : 'btn-primary'" @click="confirm">{{ opts?.confirmText || '确认' }}</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { ConfirmOpts } from './GlobalConfirm.types'

const visible = ref(false)
let resolveFn: ((val: boolean) => void) | null = null
const opts = ref<ConfirmOpts | null>(null)

const open = (o: ConfirmOpts = {}): Promise<boolean> => {
  opts.value = o
  visible.value = true
  return new Promise(res => { resolveFn = res })
}

const confirm = () => {
  visible.value = false
  resolveFn?.(true)
}

const cancel = () => {
  visible.value = false
  resolveFn?.(false)
}

defineExpose({ open })
</script>

<style scoped>
.confirm-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.5); z-index: 3000; display: flex; align-items: center; justify-content: center; }
.confirm-box { background: #fff; border-radius: 12px; width: 400px; max-width: 90vw; overflow: hidden; }
.confirm-box.danger { border-top: 3px solid #EF4444; }
.confirm-header { padding: 20px 24px 16px; border-bottom: 1px solid #E5E7EB; }
.confirm-header h3 { font-size: 16px; font-weight: 600; }
.confirm-body { padding: 20px 24px; }
.confirm-body p { font-size: 14px; color: #6B7280; line-height: 1.6; }
.confirm-footer { padding: 16px 24px; display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid #E5E7EB; }
.btn-danger { background: #EF4444; color: #fff; }
</style>
