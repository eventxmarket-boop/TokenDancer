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
      <h1>最近会话</h1>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/seed">Seed</RouterLink>
        <RouterLink class="secondary-btn" to="/favorites">收藏</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">继续</p>
        <h3 class="hero-band__title">会话</h3>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">排序</p>
        <h3 class="hero-band__title">最新在前</h3>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">会话</p>
        <h3>列表</h3>
      </div>
      <RouterLink class="text-link" to="/">返回</RouterLink>
    </div>

        <div v-if="loading" class="state-panel">
          <p class="eyebrow">加载中</p>
          <h3>读取中…</h3>
    </div>

        <div v-else-if="error" class="state-panel">
          <p class="eyebrow">加载失败</p>
          <h3>暂时不可用</h3>
      <p class="state-copy">{{ error }}</p>
      <button class="primary-btn" type="button" @click="load">重试</button>
    </div>

        <div v-else-if="!sessions.length" class="empty-panel">
          <div class="empty-panel__icon">↩</div>
          <h3>暂无会话。</h3>
          <p class="empty-panel__copy">开始聊天后会出现。</p>
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
        </div>
          <div class="session-card__actions">
            <span class="session-card__meta">{{ new Date(session.updated_at).toLocaleString() }}</span>
          <span class="text-link">继续</span>
          </div>
      </RouterLink>
    </div>
  </section>
</template>
