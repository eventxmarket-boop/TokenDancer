<template>
  <div class="pagination">
    <button :disabled="current <= 1" @click="emit('update:current', current - 1)">‹</button>
    <span>第 {{ current }} / {{ total }} 页</span>
    <button :disabled="current >= total" @click="emit('update:current', current + 1)">›</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ current: number; total: number }>()
const emit = defineEmits(['update:current'])
</script>

<style scoped>
.pagination { display: flex; align-items: center; gap: 12px; justify-content: center; padding: 24px 0; }
.pagination button { width: 32px; height: 32px; border: 1px solid #E5E7EB; border-radius: 6px; background: #fff; cursor: pointer; font-size: 16px; }
.pagination button:disabled { opacity: .4; cursor: not-allowed; }
.pagination button:hover:not(:disabled) { border-color: #4F46E5; color: #4F46E5; }
.pagination span { font-size: 14px; color: #6B7280; }
</style>
