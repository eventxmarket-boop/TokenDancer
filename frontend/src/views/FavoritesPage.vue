<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { listPersonas, type Persona } from '@/services/personaService'
import {
  clearFavoriteSlugs,
  getFavoriteSlugs,
  toggleFavoriteSlug,
} from '@/services/favoriteService'

const loading = ref(true)
const error = ref('')
const personas = ref<Persona[]>([])
const favoriteSlugs = ref<string[]>(getFavoriteSlugs())

const refreshFavorites = () => {
  favoriteSlugs.value = getFavoriteSlugs()
}

const load = async () => {
  loading.value = true
  error.value = ''

  try {
    personas.value = await listPersonas()
    refreshFavorites()
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载收藏人格失败'
    error.value = message
    personas.value = []
  } finally {
    loading.value = false
  }
}

const favoriteSet = computed(() => new Set(favoriteSlugs.value))

const favoritePersonas = computed(() =>
  personas.value.filter((persona) => favoriteSet.value.has(persona.slug)),
)

const toggleFavorite = (slug: string) => {
  toggleFavoriteSlug(slug)
  refreshFavorites()
}

const clearFavorites = () => {
  clearFavoriteSlugs()
  refreshFavorites()
}

const groups = computed(() => {
  const map = new Map<string, Persona[]>()

  for (const persona of favoritePersonas.value) {
    const key = persona.seedGroup?.trim() || persona.category || '收藏'
    const bucket = map.get(key) || []
    bucket.push(persona)
    map.set(key, bucket)
  }

  return Array.from(map.entries()).map(([group, items]) => ({ group, items }))
})

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="page-hero">
    <div class="hero-copy">
      <p class="eyebrow">Favorites</p>
      <h1>把常用人格收藏起来，后面继续聊更顺手。</h1>
      <p class="hero-text">
        收藏页保存的是你在本地浏览器里最常用的视角。常聊的人格不需要每次重新找，点一下就能回到详情或聊天。
      </p>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>{{ favoritePersonas.length }}</strong><span>已收藏</span></span>
        <span class="metric-chip"><strong>{{ groups.length }}</strong><span>收藏分组</span></span>
      </div>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/seed">去 Seed 继续收藏</RouterLink>
        <RouterLink class="secondary-btn" to="/create">创造自我人格</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">本地存储</p>
        <h3 class="hero-band__title">不需要登录也能记住收藏</h3>
        <p class="hero-band__copy">收藏状态先存浏览器本地，产品闭环更轻，也更适合当前阶段。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">快捷动作</p>
        <h3 class="hero-band__title">直接进详情 / 直接开聊</h3>
        <p class="hero-band__copy">收藏页不是终点，而是一个复用入口，帮助你更快回到常聊人格。</p>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">收藏列表</p>
        <h3>按分组查看你常用的视角。</h3>
      </div>
      <div class="hero-actions">
        <RouterLink class="text-link" to="/seed">继续收藏</RouterLink>
        <button class="ghost-btn" type="button" @click="clearFavorites">清空收藏</button>
      </div>
    </div>

    <div v-if="loading" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取收藏人格…</h3>
    </div>

    <div v-else-if="error" class="state-panel">
      <p class="eyebrow">加载失败</p>
      <h3>收藏人格暂时不可用</h3>
      <p class="state-copy">{{ error }}</p>
      <button class="primary-btn" type="button" @click="load">重试</button>
    </div>

    <div v-else-if="!favoritePersonas.length" class="empty-panel">
      <div class="empty-panel__icon">♡</div>
      <h3>你还没有收藏过人格。</h3>
      <p class="empty-panel__copy">去 Seed 页面点一下收藏，常用人格就会出现在这里。</p>
      <RouterLink class="primary-btn" to="/seed">去 Seed 选择人格</RouterLink>
    </div>

    <div v-else class="group-stack">
      <article v-for="group in groups" :key="group.group" class="seed-group">
        <div class="seed-group__head">
          <div>
            <p class="eyebrow">收藏分组</p>
            <h3>{{ group.group }}</h3>
          </div>
          <span class="status-pill">{{ group.items.length }} 个</span>
        </div>

        <div class="persona-grid">
          <article v-for="persona in group.items" :key="persona.slug" class="persona-card persona-card--featured">
            <div class="persona-card__top">
              <div class="persona-avatar">{{ persona.avatar || persona.name.slice(0, 2) }}</div>
              <div class="persona-card__meta">
                <p class="persona-category">{{ persona.seedSource || persona.category }}</p>
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
              <button class="chip-btn chip-btn--active" type="button" @click="toggleFavorite(persona.slug)">
                取消收藏
              </button>
            </div>
          </article>
        </div>
      </article>
    </div>
  </section>
</template>
