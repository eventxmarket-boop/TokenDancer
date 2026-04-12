<template>
  <div class="skeleton-wrap">
    <div v-for="i in (count || 3)" :key="i" class="skeleton-line" :style="{ width: width || '100%', height: height || '20px' }"></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ count?: number; width?: string; height?: string }>()
</script>

<style scoped>
.skeleton-line {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 6px;
  margin-bottom: 12px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
