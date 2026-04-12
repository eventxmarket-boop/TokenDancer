<template>
  <Teleport to="body">
    <div v-if="modelValue" class="drawer-overlay" @click.self="handleClose">
      <div class="drawer-panel" :class="{ 'drawer-open': modelValue }">
        <!-- Header -->
        <div class="drawer-header">
          <h3 class="drawer-title">{{ title }}</h3>
          <button class="drawer-close" @click="handleClose">✕</button>
        </div>

        <!-- Body -->
        <div class="drawer-body">
          <slot />
        </div>

        <!-- Footer -->
        <div v-if="$slots.footer" class="drawer-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
const props = defineProps<{
  modelValue: boolean
  title: string
}>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const handleClose = () => emit('update:modelValue', false)
</script>

<style scoped>
.drawer-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.4);
  z-index: 900; display: flex; justify-content: flex-end;
  animation: fadeIn 0.15s ease;
}
.drawer-panel {
  width: 520px; max-width: 95vw; background: #fff;
  display: flex; flex-direction: column;
  box-shadow: -4px 0 24px rgba(0,0,0,0.12);
  animation: slideIn 0.2s ease;
}
.drawer-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 20px 24px; border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.drawer-title { font-size: 16px; font-weight: 700; color: #1a1a2e; margin: 0; }
.drawer-close {
  background: none; border: none; font-size: 18px; color: #999;
  cursor: pointer; padding: 4px; line-height: 1;
}
.drawer-close:hover { color: #333; }
.drawer-body { flex: 1; overflow-y: auto; padding: 24px; }
.drawer-footer {
  padding: 16px 24px; border-top: 1px solid #f0f0f0;
  display: flex; justify-content: flex-end; gap: 12px; flex-shrink: 0;
}

@keyframes fadeIn { from { opacity: 0 } to { opacity: 1 } }
@keyframes slideIn { from { transform: translateX(100%) } to { transform: translateX(0) } }
</style>
