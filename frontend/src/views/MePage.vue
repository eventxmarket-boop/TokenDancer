<script setup lang="ts">
const myEntries = [
  {
    to: '/my-seeds',
    title: '我创建的 Seed',
    description: '查看你创建过的人格，并继续使用。',
  },
  {
    to: '/favorites',
    title: '收藏的人格',
    description: '回到你常用的人格。',
  },
  {
    to: '/sessions',
    title: '最近会话',
    description: '继续上一次的聊天。',
  },
]
</script>

<template>
  <section class="my-page">
    <div class="my-page__inner">
      <div class="my-page__head">
        <h1>我的</h1>
      </div>

      <div class="my-entry-grid">
        <RouterLink v-for="entry in myEntries" :key="entry.to" class="my-entry-card" :to="entry.to">
          <h3>{{ entry.title }}</h3>
          <p>{{ entry.description }}</p>
        </RouterLink>
      </div>
    </div>
  </section>
</template>
