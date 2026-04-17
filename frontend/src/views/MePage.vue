<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { authUser, isLoggedIn, logout } from '@/stores/auth'

const router = useRouter()
const myEntries = [
  {
    key: 'my-seeds' as const,
    to: '/my-seeds',
    title: '我创建的 Seed',
    summary: '继续查看你亲手创建的人格。',
  },
  {
    key: 'reply-assistant' as const,
    to: '/reply-assistant',
    title: '我该怎么回',
    summary: '直接输入一句话，获取回复建议。',
  },
  {
    key: 'favorites' as const,
    to: '/favorites',
    title: '收藏的人格',
    summary: '回到你最常用的常驻人格。',
  },
  {
    key: 'sessions' as const,
    to: '/sessions',
    title: '最近会话',
    summary: '继续上一次还没聊完的话题。',
  },
]

const username = computed(() => authUser.value?.username || authUser.value?.email || '登录账号')

function goLogin() {
  void router.push({ path: '/login', query: { redirect: '/me' } })
}

function goRegister() {
  void router.push({ path: '/register', query: { redirect: '/me' } })
}

function handleLogout() {
  logout()
  void router.replace('/')
}
</script>

<template>
  <section class="my-page">
    <div class="my-page__inner">
      <div v-if="!isLoggedIn" class="my-page__head my-page__head--compact">
        <p class="eyebrow">个人中心</p>
        <h1>{{ username }}</h1>

        <div class="hero-actions hero-actions--center">
          <button class="primary-btn" type="button" @click="goLogin">登录</button>
          <button class="secondary-btn" type="button" @click="goRegister">注册</button>
        </div>
      </div>

      <template v-else>
        <div class="my-page__head">
          <p class="eyebrow">个人中心</p>
          <h1>{{ username }}</h1>
        </div>

        <div class="my-entry-grid">
          <RouterLink
            v-for="entry in myEntries"
            :key="entry.to"
            class="my-entry-link"
            :class="[`my-entry-link--${entry.key}`]"
            :to="entry.to"
          >
            <article class="my-entry-card">
              <span class="my-entry-card__tag">{{ entry.key === 'my-seeds' ? '01' : entry.key === 'reply-assistant' ? '02' : entry.key === 'favorites' ? '03' : '04' }}</span>
              <h3>{{ entry.title }}</h3>
              <p>{{ entry.summary }}</p>
            </article>
          </RouterLink>
        </div>

        <div class="hero-actions hero-actions--center">
          <button class="secondary-btn" type="button" @click="handleLogout">退出登录</button>
        </div>
      </template>
    </div>
  </section>
</template>
