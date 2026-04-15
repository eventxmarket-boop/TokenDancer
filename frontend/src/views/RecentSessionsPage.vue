<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { loadRecentSessions, type RecentSessionSummary } from '@/services/chatService'

const loading = ref(true)
const error = ref('')
const sessions = ref<RecentSessionSummary[]>([])

const load = async () => {
  loading.value = true
  error.value = ''

  try {
    sessions.value = await loadRecentSessions(20)
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载最近会话失败'
    error.value = message
    sessions.value = []
  } finally {
    loading.value = false
  }
}

const sessionLink = (session: RecentSessionSummary) => ({
  path: `/chat/${session.persona_slug}`,
  query: { session_id: session.id },
})

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page-hero">
    <div class="hero-copy">
      <p class="eyebrow">Recent Sessions</p>
      <h1>从上次聊到的位置继续。</h1>
      <p class="hero-text">
        最近会话页把你聊过的内容重新整理成可继续的卡片，方便从某个人格里直接回到上次的问题。
      </p>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/seed">去 Seed 选择人格</RouterLink>
        <RouterLink class="secondary-btn" to="/favorites">打开收藏人格</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">继续对话</p>
        <h3 class="hero-band__title">不用重新找入口</h3>
        <p class="hero-band__copy">每张卡片都能直接回到对应人格和 session，适合快速回聊。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">时间线</p>
        <h3 class="hero-band__title">最近更新排前面</h3>
        <p class="hero-band__copy">自动按更新时间排序，先看到最常继续聊的那些会话。</p>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">最近会话</p>
        <h3>继续上一次聊到的位置。</h3>
      </div>
      <RouterLink class="text-link" to="/">返回首页</RouterLink>
    </div>

    <div v-if="loading" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取最近会话…</h3>
    </div>

    <div v-else-if="error" class="state-panel">
      <p class="eyebrow">加载失败</p>
      <h3>最近会话暂时不可用</h3>
      <p class="state-copy">{{ error }}</p>
      <button class="primary-btn" type="button" @click="load">重试</button>
    </div>

    <div v-else-if="!sessions.length" class="empty-panel">
      <div class="empty-panel__icon">↩</div>
      <h3>还没有可继续的聊天记录。</h3>
      <p class="empty-panel__copy">开始一次聊天后，这里就会出现可回访的会话卡片。</p>
    </div>

    <div v-else class="session-stack">
      <RouterLink
        v-for="session in sessions"
        :key="session.id"
        class="session-card"
        :to="sessionLink(session)"
      >
        <div class="session-card__top">
          <div>
            <p class="persona-category">{{ session.persona_name }}</p>
            <h4 class="session-card__title">{{ session.title }}</h4>
          </div>
          <span class="status-pill">{{ session.persona_slug }}</span>
        </div>
        <div class="session-card__actions">
          <span class="session-card__meta">{{ new Date(session.updated_at).toLocaleString() }}</span>
          <span class="text-link">继续对话</span>
        </div>
      </RouterLink>
    </div>
  </section>
</template>
