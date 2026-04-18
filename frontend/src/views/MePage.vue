<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { authUser, isLoggedIn, logout } from '@/stores/auth'
import { listHowToDoHistoryRecords, type HowToDoHistoryRecord } from '@/services/howToDoHistoryService'

const router = useRouter()
const historyRecords = ref<HowToDoHistoryRecord[]>([])
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

onMounted(() => {
  historyRecords.value = listHowToDoHistoryRecords().slice(0, 5)
})

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

        <section class="summary-panel summary-panel--featured my-history-panel">
          <div class="seed-group__head">
            <h3>卦象历史</h3>
            <RouterLink class="text-link" to="/how-to-do">去查看</RouterLink>
          </div>
          <div v-if="historyRecords.length" class="liuyao-history-list">
            <article v-for="item in historyRecords" :key="item.id" class="liuyao-history-item">
              <div class="liuyao-history-item__title">
                <strong>{{ item.title || '未命名卦象' }}</strong>
                <span v-if="item.favorite" class="status-pill">收藏</span>
              </div>
              <p>{{ item.category }} · {{ item.castMode }}</p>
              <p>{{ new Date(item.updatedAt).toLocaleString('zh-CN') }}</p>
            </article>
          </div>
          <p v-else class="empty-panel__copy">你还没有保存过卦象历史。</p>
        </section>

        <div class="hero-actions hero-actions--center">
          <button class="secondary-btn" type="button" @click="handleLogout">退出登录</button>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.my-history-panel {
  display: grid;
  gap: 0.85rem;
}

.liuyao-history-list {
  display: grid;
  gap: 0.7rem;
}

.liuyao-history-item {
  display: grid;
  gap: 0.22rem;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  border: 1px solid rgba(148, 163, 184, 0.16);
  background: color-mix(in srgb, var(--card-bg) 95%, transparent);
}

.liuyao-history-item__title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.liuyao-history-item p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 0.9rem;
}
</style>
