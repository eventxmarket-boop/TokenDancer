<template>
  <div class="tabs">
    <button v-for="tab in tabs" :key="tab.value" :class="{ active: modelValue === tab.value }" @click="emit('update:modelValue', tab.value)">{{ tab.label }}</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ tabs: { label: string; value: string }[]; modelValue: string }>()
const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.tabs { display: flex; gap: 0; border-bottom: 2px solid #E5E7EB; }
.tabs button { padding: 10px 20px; font-size: 14px; font-weight: 500; color: #6B7280; border-bottom: 2px solid transparent; margin-bottom: -2px; cursor: pointer; transition: all .2s; }
.tabs button:hover { color: #4F46E5; }
.tabs button.active { color: #4F46E5; border-bottom-color: #4F46E5; }
</style>
