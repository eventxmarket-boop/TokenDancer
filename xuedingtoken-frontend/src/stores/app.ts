import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const sidebarCollapsed = ref(false)
  const currentLang = ref('zh')

  const toggleSidebar = () => { sidebarCollapsed.value = !sidebarCollapsed.value }
  const setLang = (lang: string) => { currentLang.value = lang }

  return { sidebarCollapsed, currentLang, toggleSidebar, setLang }
})
