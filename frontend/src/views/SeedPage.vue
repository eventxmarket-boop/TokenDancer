<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { loadSeedPersonas, type Persona } from '@/services/personaService'
import { getFavoriteSlugs, toggleFavoriteSlug } from '@/services/favoriteService'

const loading = ref(true)
const error = ref('')
const seedPersonas = ref<Persona[]>([])
const favoriteSlugs = ref<string[]>(getFavoriteSlugs())

const refreshFavorites = () => {
  favoriteSlugs.value = getFavoriteSlugs()
}

const loadSeeds = async () => {
  loading.value = true
  error.value = ''

  try {
    seedPersonas.value = await loadSeedPersonas()
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载 Seed 人格失败'
    error.value = message
    seedPersonas.value = []
  } finally {
    loading.value = false
  }
}

const groups = computed(() => {
  const map = new Map<string, Persona[]>()

  for (const persona of seedPersonas.value) {
    const key = persona.seedGroup?.trim() || persona.category || '未分组'
    const bucket = map.get(key) || []
    bucket.push(persona)
    map.set(key, bucket)
  }

  return Array.from(map.entries()).map(([group, personas]) => ({ group, personas }))
})

const favoriteSet = computed(() => new Set(favoriteSlugs.value))
const featuredPersonas = computed(() => seedPersonas.value.filter((persona) => persona.isFeatured))

const isFavorite = (slug: string) => favoriteSet.value.has(slug)

const toggleFavorite = (slug: string) => {
  toggleFavoriteSlug(slug)
  refreshFavorites()
}

const groupNames = computed(() => groups.value.map((group) => group.group).slice(0, 6))

onMounted(() => {
  void loadSeeds()
})
</script>

<template>
  <section class="page-hero">
    <div class="hero-copy">
      <p class="eyebrow">Seed</p>
      <h1>选择现成人格，直接开始聊天。</h1>
      <p class="hero-text">
        这里是已经整理成产品卡片的人格馆。你可以先看简介，再决定是直接聊、查看详情，还是收藏到 Favorites。
      </p>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>{{ seedPersonas.length }}</strong><span>种子人格</span></span>
        <span class="metric-chip"><strong>{{ featuredPersonas.length }}</strong><span>精选推荐</span></span>
        <span class="metric-chip"><strong>{{ groups.length }}</strong><span>分类分组</span></span>
      </div>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/create">去创建自我人格</RouterLink>
        <RouterLink class="secondary-btn" to="/favorites">打开收藏人格</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">现成可聊</p>
        <h3 class="hero-band__title">张雪峰 / 孙宇晨 / 框架型人格</h3>
        <p class="hero-band__copy">产品化的人格已经整理成可直接聊天的 seed 卡片，不需要额外投喂。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">收藏动作</p>
        <h3 class="hero-band__title">先收藏常用人格</h3>
        <p class="hero-band__copy">把高频使用的人格收进 Favorites，后面回聊会更顺手。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">分类地图</p>
        <h3 class="hero-band__title">现实 / 商业 / 职场 / 框架</h3>
        <p class="hero-band__copy">后续还可以继续扩展导师、师兄、家庭关系等视角。</p>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">分类地图</p>
        <h3>按视角分组浏览，不是一整串平铺。</h3>
      </div>
      <p class="section-note">这里的每一组都可以继续扩充更多产品化人格。</p>
    </div>

    <div class="seed-layout">
      <div class="seed-main">
        <div v-if="loading" class="state-panel">
          <p class="eyebrow">加载中</p>
          <h3>正在读取 Seed 人格…</h3>
        </div>

        <div v-else-if="error" class="state-panel">
          <p class="eyebrow">加载失败</p>
          <h3>Seed 人格暂时不可用</h3>
          <p class="state-copy">{{ error }}</p>
          <button class="primary-btn" type="button" @click="loadSeeds">重试</button>
        </div>

        <div v-else-if="!seedPersonas.length" class="empty-panel">
          <div class="empty-panel__icon">♪</div>
          <h3>还没有可展示的 Seed 人格。</h3>
          <p class="empty-panel__copy">请先补充 backend/personas 下的种子人格目录。</p>
        </div>

        <div v-else class="group-stack group-stack--dense">
          <article v-for="group in groups" :key="group.group" class="seed-group">
            <div class="seed-group__head">
              <div>
                <p class="eyebrow">Seed Group</p>
                <h3>{{ group.group }}</h3>
              </div>
              <span class="status-pill">{{ group.personas.length }} 个</span>
            </div>

            <div class="persona-grid">
              <article v-for="persona in group.personas" :key="persona.slug" class="persona-card persona-card--featured">
                <div class="persona-card__top">
                  <div class="persona-avatar">{{ persona.avatar || persona.name.slice(0, 2) }}</div>
                  <div class="persona-card__meta">
                    <p class="persona-category">{{ persona.seedSource || persona.category }}</p>
                    <h4>{{ persona.name }}</h4>
                    <p class="persona-intro">{{ persona.intro }}</p>
                  </div>
                </div>

                <div class="tag-row">
                  <span v-if="persona.isFeatured" class="tag-chip">精选</span>
                  <span v-for="tag in persona.tags" :key="tag" class="tag-chip">{{ tag }}</span>
                </div>

                <div class="persona-card__foot">
                  <div class="tag-row">
                    <span v-for="topic in persona.topics" :key="topic" class="tag-chip">{{ topic }}</span>
                  </div>
                  <div class="persona-actions persona-actions--stack">
                    <RouterLink class="text-link" :to="`/character/${persona.slug}`">查看详情</RouterLink>
                    <RouterLink class="text-link" :to="`/chat/${persona.slug}`">开始聊天</RouterLink>
                    <button
                      v-if="persona.isFavoritable !== false"
                      class="chip-btn"
                      :class="{ 'chip-btn--active': isFavorite(persona.slug) }"
                      type="button"
                      @click="toggleFavorite(persona.slug)"
                    >
                      {{ isFavorite(persona.slug) ? '已收藏' : '收藏' }}
                    </button>
                  </div>
                </div>
              </article>
            </div>
          </article>
        </div>
      </div>

      <aside class="seed-side">
        <article class="summary-panel">
          <p class="eyebrow">使用说明</p>
          <h3>先挑视角，再决定要不要收藏。</h3>
          <p class="state-copy">Seed 页面专门放现成可聊人格，适合快速进入对话。</p>
          <div class="tag-row">
            <span v-for="name in groupNames" :key="name" class="tag-chip">{{ name }}</span>
          </div>
        </article>

        <article class="summary-panel">
          <p class="eyebrow">精选推荐</p>
          <h3>优先看这些人格。</h3>
          <div class="summary-panel__list">
            <div
              v-for="persona in featuredPersonas.slice(0, 4)"
              :key="persona.slug"
              class="session-card session-card--compact"
            >
              <div class="session-card__top">
                <div>
                  <p class="persona-category">{{ persona.seedGroup || persona.category }}</p>
                  <h4 class="session-card__title">{{ persona.name }}</h4>
                </div>
                <span class="status-pill">{{ persona.slug }}</span>
              </div>
              <div class="session-card__actions">
                <RouterLink class="text-link" :to="`/chat/${persona.slug}`">直接聊</RouterLink>
                <button
                  v-if="persona.isFavoritable !== false"
                  class="chip-btn"
                  :class="{ 'chip-btn--active': isFavorite(persona.slug) }"
                  type="button"
                  @click="toggleFavorite(persona.slug)"
                >
                  {{ isFavorite(persona.slug) ? '已收藏' : '收藏' }}
                </button>
              </div>
            </div>
          </div>
        </article>
      </aside>
    </div>
  </section>
</template>
