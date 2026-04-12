<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <div class="empty-title">{{ title }}</div>
    <div v-if="description" class="empty-desc">{{ description }}</div>
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  icon?: string
  title: string
  description?: string
}>()
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 64px 24px;
  text-align: center;
}
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }
.empty-title { font-size: 15px; font-weight: 600; color: #333; margin-bottom: 6px; }
.empty-desc { font-size: 13px; color: #999; max-width: 360px; }
</style>
