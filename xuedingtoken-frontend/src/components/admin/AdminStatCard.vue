<template>
  <div class="stat-card">
    <div class="stat-icon">{{ icon }}</div>
    <div class="stat-body">
      <div class="stat-value">{{ value ?? '—' }}</div>
      <div class="stat-label">{{ label }}</div>
    </div>
    <div v-if="trend" class="stat-trend" :class="trendClass">{{ trend }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
const props = defineProps<{
  label: string
  value?: string | number
  icon?: string
  trend?: string
  trendType?: 'up' | 'down' | 'neutral'
}>()
const trendClass = computed(() => ({
  'trend-up': props.trendType === 'up',
  'trend-down': props.trendType === 'down',
}))
</script>

<style scoped>
.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid #f0f0f0;
  min-width: 0;
}
.stat-icon { font-size: 28px; flex-shrink: 0; }
.stat-body { flex: 1; min-width: 0; }
.stat-value { font-size: 26px; font-weight: 700; color: #1a1a2e; line-height: 1.2; }
.stat-label { font-size: 12px; color: #888; margin-top: 4px; }
.stat-trend { font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 10px; flex-shrink: 0; }
.trend-up { background: #f6ffed; color: #52c41a; }
.trend-down { background: #fff1f0; color: #ff4d4f; }
</style>
