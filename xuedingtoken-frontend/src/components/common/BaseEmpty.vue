<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon || '📭' }}</div>
    <h3>{{ title }}</h3>
    <p>{{ desc }}</p>
    <button v-if="action" class="btn btn-primary mt-4" @click="$emit('action')">{{ action }}</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ icon?: string; title: string; desc?: string; action?: string }>()
defineEmits(['action'])
</script>

<style scoped>
.empty-state { text-align: center; padding: 48px 24px; }
.empty-icon { font-size: 40px; opacity: .4; margin-bottom: 14px; }
.empty-state h3 { font-size: 16px; font-weight: 600; margin-bottom: 8px; }
.empty-state p { font-size: 13px; color: #6B7280; }
</style>
