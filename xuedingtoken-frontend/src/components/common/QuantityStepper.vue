<template>
  <div class="qty-stepper">
    <button @click="emit('update:modelValue', Math.max(1, modelValue - 1))">−</button>
    <span>{{ modelValue }}</span>
    <button @click="emit('update:modelValue', modelValue + 1)">+</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ modelValue: number }>()
const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.qty-stepper { display: flex; align-items: center; gap: 0; border: 1px solid #E5E7EB; border-radius: 8px; overflow: hidden; }
.qty-stepper button { width: 32px; height: 32px; background: #F9FAFB; border: none; font-size: 16px; cursor: pointer; }
.qty-stepper button:hover { background: #E5E7EB; }
.qty-stepper span { width: 40px; text-align: center; font-size: 14px; font-weight: 500; border-left: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; line-height: 32px; }
</style>
