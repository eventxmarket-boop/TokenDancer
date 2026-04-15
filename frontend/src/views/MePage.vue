<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { loadRecentSessions, type RecentSessionSummary } from '@/services/chatService'
import { getFavoriteSlugs } from '@/services/favoriteService'
import { listPersonas, type Persona } from '@/services/personaService'

const recent = ref<RecentSessionSummary[]>([])
const favoritePersonas = ref<Persona[]>([])
const recentLoading = ref(true)
const favoritesLoading = ref(true)

const loadRecent = async () => {
  recentLoading.value = true
  try {
    recent.value = await loadRecentSessions(5)
  } catch {
    recent.value = []
  } finally {
    recentLoading.value = false
  }
}

const loadFavorites = async () => {
  favoritesLoading.value = true
  try {
    const personas = await listPersonas()
    const slugs = new Set(getFavoriteSlugs())
    favoritePersonas.value = personas.filter((persona) => slugs.has(persona.slug))
  } catch {
    favoritePersonas.value = []
  } finally {
    favoritesLoading.value = false
  }
}

const sessionLink = (session: RecentSessionSummary) => ({
  path: `/chat/${session.persona_slug}`,
  query: { session_id: session.id },
})

const favoriteCount = computed(() => favoritePersonas.value.length)

onMounted(() => {
  void loadRecent()
  void loadFavorites()
})
</script>

<template>
  <section class="page-hero">
    <div class="hero-copy">
      <p class="eyebrow">My Space</p>
      <h1>最近会话、收藏人格和快捷入口。</h1>
      <p class="hero-text">
        这里是你的个人中枢：可以继续最近会话，查看已收藏的人格，也可以快速回到 Seed 或 Create。
      </p>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>{{ favoriteCount }}</strong><span>收藏人格</span></span>
        <span class="metric-chip"><strong>{{ recent.length }}</strong><span>最近会话</span></span>
      </div>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/seed">去 Seed</RouterLink>
        <RouterLink class="secondary-btn" to="/create">创造自我人格</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">最近聊天</p>
        <h3 class="hero-band__title">保留回聊入口</h3>
        <p class="hero-band__copy">你可以从这里快速回到上一次聊到的位置。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">收藏人格</p>
        <h3 class="hero-band__title">把常用人格放在旁边</h3>
        <p class="hero-band__copy">收藏页中的人格会在这里同步展示，方便后续继续使用。</p>
      </article>
    </div>
  </section>

  <section class="profile-grid">
    <article class="summary-panel">
      <p class="eyebrow">最近聊天</p>
      <h3>继续上次聊到的位置。</h3>
      <div v-if="recentLoading" class="state-copy">正在读取最近会话…</div>
      <div v-else-if="recent.length" class="session-stack">
        <RouterLink
          v-for="item in recent"
          :key="item.id"
          class="session-card"
          :to="sessionLink(item)"
        >
          <div class="session-card__top">
            <div>
              <p class="persona-category">{{ item.persona_name }}</p>
              <h4 class="session-card__title">{{ item.title }}</h4>
            </div>
            <span class="status-pill">{{ item.persona_slug }}</span>
          </div>
          <div class="session-card__actions">
            <span class="session-card__meta">{{ new Date(item.updated_at).toLocaleString() }}</span>
            <span class="text-link">继续</span>
          </div>
        </RouterLink>
      </div>
      <div v-else class="empty-panel">
        <div class="empty-panel__icon">↩</div>
        <p class="empty-panel__copy">还没有最近会话，先从 Seed 选一个人格开始聊吧。</p>
      </div>
    </article>

    <article class="summary-panel">
      <p class="eyebrow">收藏人格</p>
      <h3>把最常用的视角放在这里。</h3>
      <div v-if="favoritesLoading" class="state-copy">正在读取收藏…</div>
      <div v-else-if="favoritePersonas.length" class="tag-row">
        <span v-for="persona in favoritePersonas" :key="persona.slug" class="tag-chip">
          {{ persona.name }}
        </span>
      </div>
      <div v-else class="empty-panel">
        <div class="empty-panel__icon">♡</div>
        <p class="empty-panel__copy">还没有收藏人格，去 Seed 页面把常用的人格先收进来。</p>
      </div>
    </article>

    <article class="summary-panel">
      <p class="eyebrow">快捷入口</p>
      <h3>把最常用动作固定下来。</h3>
      <p class="state-copy">主页、Seed、Create、收藏和最近会话，都可以从这里一键回到。</p>
      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/seed">去 Seed</RouterLink>
        <RouterLink class="secondary-btn" to="/favorites">收藏人格</RouterLink>
        <RouterLink class="secondary-btn" to="/sessions">最近会话</RouterLink>
      </div>
    </article>
  </section>
</template>
