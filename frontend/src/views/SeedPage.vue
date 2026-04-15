<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { loadSeedPersonas, type Persona } from '@/services/personaService'
import {
  getFavoriteSlugs,
  toggleFavoriteSlug,
} from '@/services/favoriteService'

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

const isFavorite = (slug: string) => favoriteSet.value.has(slug)

const toggleFavorite = (slug: string) => {
  toggleFavoriteSlug(slug)
  refreshFavorites()
}

const countText = computed(() => `${seedPersonas.value.length} 个精选人格`)

onMounted(() => {
  void loadSeeds()
})
</script>

<template>
  <section class="hero-card">
    <div class="hero-copy">
      <p class="eyebrow">Seed 选择人格</p>
      <h2>先挑一个视角，再开始对话。</h2>
      <p class="hero-text">
        这里放的是已经整理过的种子人格。你可以直接聊天、查看详情，或者先收藏常用人格，后面继续用会更顺手。
      </p>
      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/create">创造一个自我人格</RouterLink>
        <RouterLink class="secondary-btn" to="/favorites">打开收藏人格</RouterLink>
      </div>
      <p class="section-note">{{ countText }}</p>
    </div>

    <div class="hero-visual seed-visual">
      <div class="floating-orb"></div>
      <div class="spotlight-card">
        <p class="spotlight-card__label">收藏提示</p>
        <h3>把常用人格放进收藏夹</h3>
        <p>收藏状态保存在本地浏览器，后面再进来还会保留。</p>
      </div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">精选人格</p>
        <h3>按视角分组浏览。</h3>
      </div>
      <p class="section-note">当前推荐来源已经用 seed 形式整理过了。</p>
    </div>

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

    <div v-else-if="!seedPersonas.length" class="state-panel">
      <p class="eyebrow">暂无人格</p>
      <h3>还没有可展示的 Seed 人格。</h3>
      <p class="state-copy">请先补充 backend/personas 下的种子人格目录。</p>
    </div>

    <div v-else class="group-stack">
      <article v-for="group in groups" :key="group.group" class="seed-group">
        <div class="seed-group__head">
          <div>
            <p class="eyebrow">Seed Group</p>
            <h3>{{ group.group }}</h3>
          </div>
          <span class="status-pill">{{ group.personas.length }} 个</span>
        </div>

        <div class="persona-grid">
          <article v-for="persona in group.personas" :key="persona.slug" class="persona-card">
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
                <RouterLink class="text-link" :to="`/chat/${persona.slug}`">直接聊天</RouterLink>
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
  </section>
</template>
