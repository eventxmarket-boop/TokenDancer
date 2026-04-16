<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { authUser, isLoggedIn, logout } from '@/stores/auth'

const router = useRouter()
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
        <p class="hero-text">登录后可以同步 Seed、收藏和最近会话。</p>

        <div class="hero-actions hero-actions--center">
          <button class="primary-btn" type="button" @click="goLogin">登录</button>
          <button class="secondary-btn" type="button" @click="goRegister">注册</button>
        </div>
      </div>

      <template v-else>
        <div class="my-page__head">
          <p class="eyebrow">个人中心</p>
          <h1>{{ username }}</h1>
          <p class="hero-text">查看你创建过的人格、收藏和最近会话。</p>
        </div>

        <div class="my-entry-grid">
          <RouterLink v-for="entry in myEntries" :key="entry.to" class="my-entry-card" :to="entry.to">
            <h3>{{ entry.title }}</h3>
          </RouterLink>
        </div>

        <div class="hero-actions hero-actions--center">
          <button class="secondary-btn" type="button" @click="handleLogout">退出登录</button>
        </div>
      </template>
    </div>
  </section>
</template>
