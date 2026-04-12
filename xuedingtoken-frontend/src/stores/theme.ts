import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useThemeStore = defineStore('theme', () => {
  // Read from localStorage or system preference
  const saved = localStorage.getItem('theme')
  const isDark = ref(saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches))

  function applyTheme() {
    document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  function toggle() {
    isDark.value = !isDark.value
  }

  watch(isDark, applyTheme, { immediate: true })

  return { isDark, toggle }
})
