<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authUser, isLoggedIn, logout } from '@/stores/auth'

type EntryKey = 'my-seeds' | 'favorites' | 'sessions'

const router = useRouter()
const myEntries = [
  {
    key: 'my-seeds' as const,
    to: '/my-seeds',
    title: '我创建的 Seed',
    summary: '继续查看你亲手创建的人格。',
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
const selectedEntry = ref<EntryKey>('my-seeds')

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

function activateEntry(entryKey: EntryKey) {
  selectedEntry.value = entryKey
}

function enterEntry(entryKey: EntryKey) {
  selectedEntry.value = entryKey
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

        <div class="my-entry-stack">
          <RouterLink
            v-for="entry in myEntries"
            :key="entry.to"
            class="my-entry-link"
            :class="[
              `my-entry-link--${entry.key}`,
              { 'my-entry-link--active': selectedEntry === entry.key },
            ]"
            :to="entry.to"
            @pointerenter="enterEntry(entry.key)"
            @focus="activateEntry(entry.key)"
            @pointerdown="activateEntry(entry.key)"
            @click="activateEntry(entry.key)"
          >
            <article
              class="my-entry-card"
              :class="{
                'my-entry-card--active': selectedEntry === entry.key,
                'my-entry-card--inactive': selectedEntry !== entry.key,
              }"
            >
              <span class="my-entry-card__tag">{{ entry.key === 'my-seeds' ? '01' : entry.key === 'favorites' ? '02' : '03' }}</span>
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
