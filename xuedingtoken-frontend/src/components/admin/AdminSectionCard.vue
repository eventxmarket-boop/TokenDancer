<template>
  <div class="section-card">
    <div v-if="title || $slots.header" class="section-header">
      <slot name="header">
        <span class="section-title">{{ title }}</span>
        <slot name="actions" />
      </slot>
    </div>
    <div class="section-body">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title?: string }>()
</script>

<style scoped>
.section-card {
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  min-height: 56px;
}
.section-title { font-size: 14px; font-weight: 700; color: #1a1a2e; }
.section-body { padding: 0; }
</style>
