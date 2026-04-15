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

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="hero-card">
    <div class="hero-copy">
      <p class="eyebrow">Favorites</p>
      <h2>收藏常用人格，后面继续聊更顺手。</h2>
      <p class="hero-text">
        这里保存的是你在本地浏览器里收藏的人格。常用的视角可以先收进来，之后从这里直接进入详情或聊天。
      </p>
      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/seed">去 Seed 选人格</RouterLink>
        <RouterLink class="secondary-btn" to="/create">创造自我人格</RouterLink>
      </div>
    </div>

    <div class="hero-visual favorites-visual">
      <div class="floating-orb"></div>
      <div class="spotlight-card">
        <p class="spotlight-card__label">本地收藏</p>
        <h3>{{ favoritePersonas.length }} 个人格</h3>
        <p>收藏状态不需要登录，先把产品闭环跑顺。</p>
      </div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">收藏列表</p>
        <h3>只保留你常用的视角。</h3>
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

    <div v-else-if="!favoritePersonas.length" class="state-panel">
      <p class="eyebrow">暂无收藏</p>
      <h3>你还没有收藏过人格。</h3>
      <p class="state-copy">去 Seed 页面点一下收藏，常用人格就会出现在这里。</p>
    </div>

    <div v-else class="persona-grid">
      <article v-for="persona in favoritePersonas" :key="persona.slug" class="persona-card">
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

        <div class="persona-card__foot">
          <div class="persona-actions persona-actions--stack">
            <RouterLink class="text-link" :to="`/character/${persona.slug}`">查看详情</RouterLink>
            <RouterLink class="text-link" :to="`/chat/${persona.slug}`">直接聊天</RouterLink>
            <button class="chip-btn chip-btn--active" type="button" @click="toggleFavorite(persona.slug)">
              取消收藏
            </button>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>
