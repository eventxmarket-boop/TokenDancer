<script setup lang="ts">
const navItems = [
  { to: '/', label: '首页' },
  { to: '/sessions', label: '最近会话' },
  { to: '/me', label: '我的' },
]
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

      <nav class="desktop-nav" aria-label="主导航">
        <RouterLink v-for="item in navItems" :key="item.to" :to="item.to" class="nav-link">
          {{ item.label }}
        </RouterLink>
      </nav>
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
