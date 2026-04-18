<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { authUser, isLoggedIn, logout } from '@/stores/auth'

const router = useRouter()
const myEntries = [
  {
    key: 'my-seeds' as const,
    to: '/my-seeds',
    title: '我创建的seed',
    summary: '继续查看你亲手创建的人格。',
  },
  {
    key: 'favorites' as const,
    to: '/favorites',
    title: '收藏的seed',
    summary: '回答你最常用的seed。',
  },
  {
    key: 'reply-assistant' as const,
    to: '/reply-assistant',
    title: '我该怎么回',
    summary: '直接输入一句话，获取回复建议。',
  },
  {
    key: 'how-to-do' as const,
    to: '/how-to-do',
    title: '我该怎么做',
    summary: '继续查看你保存的卦象和判断。',
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
        <p class="hero-text">登录后可以同步 Seed、收藏和 Mind 入口。</p>

        <div class="hero-actions hero-actions--center">
          <button class="primary-btn" type="button" @click="goLogin">登录</button>
          <button class="secondary-btn" type="button" @click="goRegister">注册</button>
        </div>
      </div>

      <template v-else>
        <div class="my-page__head">
          <p class="eyebrow">个人中心</p>
          <h1>{{ username }}</h1>
          <p class="hero-text">查看你创建过的 Seed、收藏和常用入口。</p>
        </div>

        <div class="my-entry-grid my-entry-grid--clover">
          <RouterLink
            v-for="entry in myEntries"
            :key="entry.to"
            class="my-entry-link"
            :class="[`my-entry-link--${entry.key}`]"
            :to="entry.to"
          >
            <article class="my-entry-card">
              <span class="my-entry-card__tag">
                {{
                  entry.key === 'my-seeds'
                    ? '01'
                    : entry.key === 'favorites'
                      ? '02'
                      : entry.key === 'reply-assistant'
                        ? '03'
                        : '04'
                }}
              </span>
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

<style scoped>
.my-entry-grid--clover {
  width: min(720px, 100%);
  grid-template-columns: repeat(2, minmax(0, 1fr));
  justify-items: center;
  align-items: center;
  gap: 1.1rem;
}

.my-entry-link {
  width: 100%;
  display: flex;
}

.my-entry-link :deep(.my-entry-card),
.my-entry-card {
  width: 100%;
  aspect-ratio: 1 / 1;
  min-height: unset;
  border-radius: 32px;
  padding: 1.35rem;
  justify-items: center;
  align-content: center;
}

.my-entry-link--my-seeds {
  transform: translate(0.35rem, 0.25rem);
}

.my-entry-link--favorites {
  transform: translate(-0.35rem, 0.25rem);
}

.my-entry-link--reply-assistant {
  transform: translate(0.35rem, -0.25rem);
}

.my-entry-link--how-to-do {
  transform: translate(-0.35rem, -0.25rem);
}

.my-entry-card h3 {
  font-size: 1.34rem;
  line-height: 1.2;
}

.my-entry-card p {
  max-width: 12ch;
}

@media (max-width: 700px) {
  .my-entry-grid--clover {
    gap: 0.9rem;
  }

  .my-entry-link--my-seeds,
  .my-entry-link--favorites,
  .my-entry-link--reply-assistant,
  .my-entry-link--how-to-do {
    transform: none;
  }

  .my-entry-link :deep(.my-entry-card),
  .my-entry-card {
    border-radius: 28px;
    padding: 1.1rem;
  }
}
</style>
