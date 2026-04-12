<template>
  <button class="btn btn-sm btn-outline" @click="copy">
    {{ copied ? '✓ 已复制' : (label || '复制') }}
  </button>
</template>

<script setup lang="ts">
import { ref } from 'vue'
const props = defineProps<{ text: string; label?: string }>()
const copied = ref(false)
const copy = async () => {
  try {
    await navigator.clipboard.writeText(props.text)
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  } catch {
    copied.value = true
    setTimeout(() => copied.value = false, 2000)
  }
}
</script>
