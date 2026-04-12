<template>
  <div class="filter-bar">
    <div class="filter-left">
      <slot />
    </div>
    <div class="filter-right">
      <button v-if="showReset" class="btn btn-ghost btn-sm" @click="emit('reset')">重置</button>
      <button v-if="showRefresh" class="btn btn-outline btn-sm" @click="emit('refresh')">刷新</button>
      <button v-if="showExport" class="btn btn-outline btn-sm" @click="emit('export')">导出CSV</button>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ showReset?: boolean; showRefresh?: boolean; showExport?: boolean }>()
const emit = defineEmits(['reset', 'refresh', 'export'])
</script>

<style scoped>
.filter-bar { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; gap: 8px; flex-wrap: wrap; }
.filter-left { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.filter-right { display: flex; gap: 8px; }
</style>
