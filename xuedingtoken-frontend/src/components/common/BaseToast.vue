<template>
  <Teleport to="body">
    <div class="toast-container">
      <div
        v-for="toast in feedbackStore.toasts"
        :key="toast.id"
        class="toast"
        :class="toast.type"
      >{{ toast.message }}</div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useFeedbackStore } from '@/stores/feedback'
const feedbackStore = useFeedbackStore()
</script>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  gap: 8px;
  align-items: center;
  z-index: 9999;
  pointer-events: none;
}
.toast {
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  color: #fff;
  pointer-events: auto;
  animation: slideUp .3s ease;
  white-space: nowrap;
}
.toast.success { background: #10B981; }
.toast.error { background: #EF4444; }
.toast.info { background: #4F46E5; }
.toast.warning { background: #F59E0B; }
@keyframes slideUp {
  from { opacity: 0; transform: translateX(-50%) translateY(20px); }
  to { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
