<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @click.self="$emit('update:modelValue', false)">
      <div class="modal-box">
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <button @click="$emit('update:modelValue', false)">✕</button>
        </div>
        <div class="modal-body">
          <slot />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
defineProps<{ modelValue: boolean; title: string }>()
defineEmits(['update:modelValue'])
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,.5);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.modal-box {
  background: #fff;
  border-radius: 12px;
  width: 480px;
  max-width: 90vw;
  max-height: 80vh;
  overflow: auto;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #E5E7EB;
}
.modal-header h3 { font-size: 18px; font-weight: 600; }
.modal-header button { background: none; border: none; font-size: 20px; cursor: pointer; color: #6B7280; }
.modal-body { padding: 24px; }

@media (max-width: 720px) {
  .modal-overlay {
    align-items: flex-end;
    padding: 12px;
  }
  .modal-box {
    width: 100%;
    max-width: none;
    max-height: 88vh;
    border-radius: 18px 18px 0 0;
  }
  .modal-header {
    padding: 16px 18px;
  }
  .modal-header h3 {
    font-size: 16px;
  }
  .modal-header button {
    width: 36px;
    height: 36px;
  }
  .modal-body {
    padding: 18px;
  }
}
</style>
