<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

const mobileNavItems = [
  { to: '/', label: 'Seed' },
  { to: '/reply-assistant', label: '我该怎么回' },
  { to: '/favorites', label: '收藏' },
  { to: '/me', label: '个人' },
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

const isReplyMenuActive = computed(
  () => route.path === '/reply-assistant' || route.path === '/reply-assistant/workbench' || route.path === '/how-to-do',
)

const isSeedMenuActive = computed(
  () => route.path.startsWith('/create') || route.path === '/',
)

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
      <RouterLink class="brand-lockup brand-lockup--link" to="/" aria-label="返回首页">
        <div class="brand-mark">T</div>
        <div>
          <p class="eyebrow">Tokendancer</p>
        </div>
      </RouterLink>

      <div class="topbar__actions">
        <nav class="desktop-nav" aria-label="主导航">
          <div class="nav-group" :class="{ 'nav-group--active': isSeedMenuActive }">
            <RouterLink to="/" class="nav-dropdown__trigger">Seed</RouterLink>
            <div class="nav-dropdown" aria-label="Seed 下拉菜单">
              <RouterLink to="/create" class="nav-dropdown__item">创建</RouterLink>
              <RouterLink to="/" class="nav-dropdown__item">Seed</RouterLink>
            </div>
          </div>

          <div class="nav-group" :class="{ 'nav-group--active': isReplyMenuActive }">
            <RouterLink to="/reply-assistant" class="nav-dropdown__trigger">我该怎么回</RouterLink>
            <div class="nav-dropdown" aria-label="我该怎么回 下拉菜单">
              <RouterLink to="/reply-assistant/workbench" class="nav-dropdown__item">我该怎么回</RouterLink>
              <RouterLink to="/how-to-do" class="nav-dropdown__item">我该怎么做</RouterLink>
            </div>
          </div>

          <RouterLink to="/favorites" class="nav-link">收藏</RouterLink>
          <RouterLink to="/me" class="nav-link">个人</RouterLink>
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
      <RouterLink v-for="item in mobileNavItems" :key="item.to" :to="item.to" class="mobile-nav__item">
        {{ item.label }}
      </RouterLink>
    </nav>
  </div>
</template>
