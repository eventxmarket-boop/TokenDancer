<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { loadRecentSessions, type RecentSessionSummary } from '@/services/chatService'

const recentSessions = ref<RecentSessionSummary[]>([])
const loadingRecent = ref(true)
const error = ref('')

const loadRecent = async () => {
  loadingRecent.value = true
  error.value = ''

  try {
    recentSessions.value = await loadRecentSessions(3)
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载最近会话失败'
    error.value = message
    recentSessions.value = []
  } finally {
    loadingRecent.value = false
  }
}

const recentLink = (session: RecentSessionSummary) => ({
  path: `/chat/${session.persona_slug}`,
  query: { session_id: session.id },
})

onMounted(() => {
  void loadRecent()
})
</script>

<template>
  <section class="hero-card home-hero">
    <div class="hero-copy">
      <p class="eyebrow">两条主线</p>
      <h2>先创造一个自我人格，再和不同人格继续聊。</h2>
      <p class="hero-text">
        这一版把入口收束成两个方向：一边是自己的 Work System 与 Reply Persona，另一边是从 Seed 里挑一个视角直接开聊。
      </p>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/create">创造一个自我人格</RouterLink>
        <RouterLink class="secondary-btn" to="/seed">去 Seed 选择人格</RouterLink>
      </div>

      <div class="inline-links">
        <RouterLink class="text-link" to="/favorites">打开收藏人格</RouterLink>
        <RouterLink class="text-link" to="/sessions">继续最近会话</RouterLink>
      </div>
    </div>

    <div class="hero-visual home-visual">
      <div class="floating-orb"></div>
      <div class="spotlight-card">
        <p class="spotlight-card__label">功能 A</p>
        <h3>创造自我人格</h3>
        <p>先定义做事方式，再定义回复方式，后面再慢慢补成完整蒸馏入口。</p>
      </div>
      <div class="spotlight-card spotlight-card--alt">
        <p class="spotlight-card__label">功能 B</p>
        <h3>Seed 选人格聊天</h3>
        <p>从精选人格里直接进入对话，收藏常用人格后还能快速回聊。</p>
      </div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">快捷入口</p>
        <h3>先做最短路径，再做细节扩展。</h3>
      </div>
      <p class="section-note">这些入口是产品主线，不是辅助菜单。</p>
    </div>

    <div class="feature-grid">
      <RouterLink class="feature-card" to="/create">
        <p class="feature-card__label">Create</p>
        <h4>创造一个自我人格</h4>
        <p>围绕 Work System 和 Reply Persona，先把你自己说清楚。</p>
      </RouterLink>

      <RouterLink class="feature-card" to="/seed">
        <p class="feature-card__label">Seed</p>
        <h4>选择一个人格</h4>
        <p>在精选种子里挑一个当前最想聊的视角，直接开始对话。</p>
      </RouterLink>

      <RouterLink class="feature-card" to="/favorites">
        <p class="feature-card__label">Favorites</p>
        <h4>收藏常用人格</h4>
        <p>把经常用的人格放进收藏夹，后面继续聊更顺手。</p>
      </RouterLink>

      <RouterLink class="feature-card" to="/sessions">
        <p class="feature-card__label">Recent</p>
        <h4>继续最近会话</h4>
        <p>从上次聊到的位置接着聊，不需要每次重新找入口。</p>
      </RouterLink>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">最近会话</p>
        <h3>继续上一次聊到的位置。</h3>
      </div>
      <RouterLink class="text-link" to="/sessions">查看全部</RouterLink>
    </div>

    <div v-if="loadingRecent" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取最近会话…</h3>
    </div>

    <div v-else-if="error" class="state-panel">
      <p class="eyebrow">加载失败</p>
      <h3>最近会话暂时不可用</h3>
      <p class="state-copy">{{ error }}</p>
      <button class="primary-btn" type="button" @click="loadRecent">重试</button>
    </div>

    <div v-else-if="recentSessions.length" class="recent-session-grid">
      <RouterLink
        v-for="session in recentSessions"
        :key="session.id"
        class="recent-session-card"
        :to="recentLink(session)"
      >
        <div class="recent-session-card__head">
          <p class="persona-category">{{ session.persona_name }}</p>
          <span class="recent-session-card__time">{{ new Date(session.updated_at).toLocaleString() }}</span>
        </div>
        <h4>{{ session.title }}</h4>
        <p class="state-copy">{{ session.persona_slug }}</p>
      </RouterLink>
    </div>

    <div v-else class="state-panel">
      <p class="eyebrow">暂无最近会话</p>
      <h3>开始一次聊天后，这里会出现继续入口。</h3>
    </div>
  </section>
</template>
