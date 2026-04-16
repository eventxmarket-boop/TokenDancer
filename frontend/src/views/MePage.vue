<script setup lang="ts">
const myEntries = [
  {
    to: '/my-seeds',
    title: '我创建的 Seed',
  },
  {
    to: '/favorites',
    title: '收藏的人格',
  },
  {
    to: '/sessions',
    title: '最近会话',
  },
]
</script>

<template>
  <section class="my-page">
    <div class="my-page__inner">
      <div class="my-entry-grid">
        <RouterLink v-for="entry in myEntries" :key="entry.to" class="my-entry-card" :to="entry.to">
          <h3>{{ entry.title }}</h3>
        </RouterLink>
      </div>
    </div>
  </section>
</template>
