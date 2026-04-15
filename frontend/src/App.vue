<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

const navItems = [
  { to: '/', label: '首页' },
  { to: '/seed', label: 'Seed' },
  { to: '/favorites', label: '收藏' },
  { to: '/create', label: '创建' },
  { to: '/me', label: '我的' },
]

const themeKey = 'persona-theme-mode'
const theme = ref<'day' | 'night'>('day')

const themeLabel = computed(() => (theme.value === 'night' ? '日间' : '夜间'))

function applyTheme(mode: 'day' | 'night') {
  if (typeof document === 'undefined') {
    return
  }
  document.documentElement.dataset.theme = mode === 'night' ? 'night' : 'day'
  document.documentElement.dataset.themeMode = mode
}

function toggleTheme() {
  theme.value = theme.value === 'night' ? 'day' : 'night'
}

onMounted(() => {
  const stored = window.localStorage.getItem(themeKey)
  if (stored === 'day' || stored === 'night') {
    theme.value = stored
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    theme.value = 'night'
  }

  applyTheme(theme.value)
})

watch(
  theme,
  (value) => {
    applyTheme(value)
    window.localStorage.setItem(themeKey, value)
  },
)
</script>

<template>
  <div class="app-shell">
    <div class="ambient ambient-one"></div>
    <div class="ambient ambient-two"></div>
    <header class="topbar">
      <div class="brand-lockup">
        <div class="brand-mark">T</div>
        <div>
          <p class="eyebrow">Tokendancer</p>
          <h1>人格小屋</h1>
        </div>
      </div>

      <div class="topbar__actions">
        <nav class="desktop-nav" aria-label="主导航">
          <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-link">
            {{ item.label }}
          </RouterLink>
        </nav>
        <button class="theme-toggle" type="button" @click="toggleTheme">
          {{ themeLabel }}模式
        </button>
      </div>
    </header>

    <main class="page-shell">
      <RouterView />
    </main>

    <nav class="mobile-nav" aria-label="底部导航">
      <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="mobile-nav__item">
        {{ item.label }}
      </RouterLink>
    </nav>
  </div>
</template>
