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
  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">最近会话</p>
        <h2>继续上一次聊到的位置。</h2>
      </div>
      <RouterLink class="secondary-btn" to="/">返回首页</RouterLink>
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

    <div v-else-if="!sessions.length" class="state-panel">
      <p class="eyebrow">暂无会话</p>
      <h3>还没有可继续的聊天记录。</h3>
      <p class="state-copy">先去首页选一个人格开始聊吧。</p>
    </div>

    <div v-else class="recent-session-grid">
      <RouterLink
        v-for="session in sessions"
        :key="session.id"
        class="recent-session-card"
        :to="sessionLink(session)"
      >
        <div class="recent-session-card__head">
          <p class="persona-category">{{ session.persona_name }}</p>
          <span class="recent-session-card__time">{{ new Date(session.updated_at).toLocaleString() }}</span>
        </div>
        <h4>{{ session.title }}</h4>
        <p class="state-copy">{{ session.persona_slug }}</p>
      </RouterLink>
    </div>
  </section>
</template>
