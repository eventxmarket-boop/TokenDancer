<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { loadRecentSessions, type RecentSessionSummary } from '@/services/chatService'
import { getFavoriteSlugs } from '@/services/favoriteService'
import { loadSeedPersonas, type Persona } from '@/services/personaService'

const recentSessions = ref<RecentSessionSummary[]>([])
const seedPersonas = ref<Persona[]>([])
const loadingRecent = ref(true)
const loadingSeed = ref(true)
const error = ref('')

const favoriteCount = computed(() => getFavoriteSlugs().length)
const featuredPersonas = computed(() =>
  seedPersonas.value.filter((persona) => persona.isFeatured).slice(0, 4),
)

const metrics = computed(() => [
  { label: 'Seed 人格', value: seedPersonas.value.length },
  { label: '精选人格', value: featuredPersonas.value.length },
  { label: '收藏数量', value: favoriteCount.value },
])

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

const loadSeeds = async () => {
  loadingSeed.value = true

  try {
    seedPersonas.value = await loadSeedPersonas()
  } catch {
    seedPersonas.value = []
  } finally {
    loadingSeed.value = false
  }
}

const recentLink = (session: RecentSessionSummary) => ({
  path: `/chat/${session.persona_slug}`,
  query: { session_id: session.id },
})

onMounted(() => {
  void loadRecent()
  void loadSeeds()
})
</script>

<template>
  <section class="page-hero">
    <div class="hero-copy">
      <p class="eyebrow">Persona Station</p>
      <h1>创造一个自我人格，也可以去不同人格里继续聊。</h1>
      <p class="hero-text">
        这是一个把自我蒸馏和人格对话放在同一空间里的产品。你可以先创造自己，也可以先挑一个已经整理好的视角，直接开始聊天。
      </p>

      <div class="hero-metrics">
        <span v-for="metric in metrics" :key="metric.label" class="metric-chip">
          <strong>{{ metric.value }}</strong>
          <span>{{ metric.label }}</span>
        </span>
      </div>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/create">创造一个自我人格</RouterLink>
        <RouterLink class="secondary-btn" to="/seed">去 Seed 选择人格聊天</RouterLink>
      </div>

      <div class="inline-links">
        <RouterLink class="text-link" to="/favorites">打开收藏人格</RouterLink>
        <RouterLink class="text-link" to="/sessions">继续最近会话</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">Create</p>
        <h3 class="hero-band__title">先把你自己说清楚</h3>
        <p class="hero-band__copy">Work System 负责做事方式，Reply Persona 负责表达方式，后面再慢慢补成完整生成流程。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">Seed</p>
        <h3 class="hero-band__title">从现成人格开始聊</h3>
        <p class="hero-band__copy">张雪峰、孙宇晨以及更多种子人格都已经整理成能直接对话的产品卡片。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">Favorites</p>
        <h3 class="hero-band__title">常用人格放一边</h3>
        <p class="hero-band__copy">常用视角收藏起来，下次不用重新找，直接继续聊就行。</p>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">主功能入口</p>
        <h3>先给两个主入口，再给收藏和最近会话。</h3>
      </div>
      <p class="section-note">主入口更像产品，辅助入口更像效率工具。</p>
    </div>

    <div class="feature-grid feature-grid--three">
      <RouterLink class="feature-card feature-card--large" to="/create">
        <p class="feature-card__label">Create</p>
        <h4>创造一个自我人格</h4>
        <p>围绕你的做事方式、回复方式和表达边界，先做一个更像你的入口。</p>
      </RouterLink>

      <RouterLink class="feature-card feature-card--large" to="/seed">
        <p class="feature-card__label">Seed</p>
        <h4>选择现成人格聊天</h4>
        <p>从精选种子人格里直接挑一个视角，进入更具体的对话场景。</p>
      </RouterLink>

      <RouterLink class="feature-card" to="/favorites">
        <p class="feature-card__label">Favorites</p>
        <h4>收藏常用人格</h4>
        <p>把你最常聊的视角存起来，之后可以更快进入对话。</p>
      </RouterLink>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">精选 Seed</p>
        <h3>先推荐几个最适合直接开聊的人格。</h3>
      </div>
      <RouterLink class="text-link" to="/seed">查看全部</RouterLink>
    </div>

    <div v-if="loadingSeed" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取精选人格…</h3>
    </div>

    <div v-else-if="featuredPersonas.length" class="persona-grid">
      <article v-for="persona in featuredPersonas" :key="persona.slug" class="persona-card persona-card--featured">
        <div class="persona-card__top">
          <div class="persona-avatar">{{ persona.avatar || persona.name.slice(0, 2) }}</div>
          <div class="persona-card__meta">
            <p class="persona-category">{{ persona.seedGroup || persona.category }}</p>
            <h4>{{ persona.name }}</h4>
            <p class="persona-intro">{{ persona.intro }}</p>
          </div>
        </div>

        <div class="tag-row">
          <span v-for="tag in persona.tags" :key="tag" class="tag-chip">{{ tag }}</span>
        </div>

        <div class="persona-actions persona-actions--stack">
          <RouterLink class="text-link" :to="`/character/${persona.slug}`">查看详情</RouterLink>
          <RouterLink class="text-link" :to="`/chat/${persona.slug}`">直接聊天</RouterLink>
        </div>
      </article>
    </div>

    <div v-else class="empty-panel">
      <div class="empty-panel__icon">♪</div>
      <h3>暂时还没有精选人格。</h3>
      <p class="empty-panel__copy">等后端 seed 数据准备好后，这里会自动变成精选人格卡片区。</p>
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

    <div class="session-layout">
      <div class="session-stack">
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

        <template v-else-if="recentSessions.length">
          <RouterLink
            v-for="session in recentSessions"
            :key="session.id"
            class="session-card"
            :to="recentLink(session)"
          >
            <div class="session-card__top">
              <div>
                <p class="persona-category">{{ session.persona_name }}</p>
                <h4 class="session-card__title">{{ session.title }}</h4>
              </div>
              <span class="status-pill">{{ session.persona_slug }}</span>
            </div>
            <div class="session-card__actions">
              <div class="session-card__meta">
                <span>{{ new Date(session.updated_at).toLocaleString() }}</span>
              </div>
              <span class="text-link">继续对话</span>
            </div>
          </RouterLink>
        </template>

        <div v-else class="empty-panel">
          <div class="empty-panel__icon">↩</div>
          <h3>开始一次聊天后，这里会出现继续入口。</h3>
          <p class="empty-panel__copy">上次聊到哪，下次就从哪接着聊，不需要重新找人格。</p>
        </div>
      </div>

      <aside class="summary-panel">
        <p class="eyebrow">快捷入口</p>
        <h3>把常用动作放在旁边。</h3>
        <p class="state-copy">这里先保留最常用的几条路径，帮助用户更快回到核心功能。</p>
        <div class="hero-actions">
          <RouterLink class="primary-btn" to="/create">创造自我人格</RouterLink>
          <RouterLink class="secondary-btn" to="/seed">去 Seed</RouterLink>
          <RouterLink class="secondary-btn" to="/favorites">收藏人格</RouterLink>
        </div>
        <ul class="summary-panel__list">
          <li><span>主页</span><strong>Landing</strong></li>
          <li><span>人格</span><strong>Seed / Create</strong></li>
          <li><span>复用</span><strong>Favorites / Recent</strong></li>
        </ul>
      </aside>
    </div>
  </section>
</template>
