<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { listPersonas, type Persona } from '@/services/personaService'
import { getFavoriteScopeKey } from '@/services/favoriteService'
import {
  clearFavoriteSlugs,
  getFavoriteSlugs,
  toggleFavoriteSlug,
} from '@/services/favoriteService'
import { authUser } from '@/stores/auth'
import {
  clearFavoriteHowToDoHistoryRecords,
  listFavoriteHowToDoHistoryRecords,
  type HowToDoHistoryRecord,
} from '@/services/howToDoHistoryService'

const loading = ref(true)
const error = ref('')
const personas = ref<Persona[]>([])
const favoriteHexagrams = ref<HowToDoHistoryRecord[]>([])
const favoriteScopeKey = computed(() => getFavoriteScopeKey(authUser.value?.id ?? null))
const favoriteSlugs = ref<string[]>(getFavoriteSlugs(favoriteScopeKey.value))

const refreshFavorites = () => {
  favoriteSlugs.value = getFavoriteSlugs(favoriteScopeKey.value)
  favoriteHexagrams.value = listFavoriteHowToDoHistoryRecords()
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
  toggleFavoriteSlug(slug, favoriteScopeKey.value)
  refreshFavorites()
}

const clearFavorites = () => {
  clearFavoriteSlugs(favoriteScopeKey.value)
  clearFavoriteHowToDoHistoryRecords()
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

const hasAnyFavorites = computed(() => favoritePersonas.value.length > 0 || favoriteHexagrams.value.length > 0)

onMounted(() => {
  void load()
})

watch(favoriteScopeKey, () => {
  refreshFavorites()
})
</script>

<template>
  <section class="favorites-page">
    <div class="favorites-page__inner">
      <div class="favorites-page__head">
        <h1>收藏列表</h1>
        <p class="hero-text">按分组查看你常用的视角。</p>

        <div class="favorites-actions">
          <RouterLink class="secondary-btn" to="/seed">继续收藏</RouterLink>
          <button class="ghost-btn" type="button" @click="clearFavorites">清空收藏</button>
        </div>
      </div>

      <div class="favorites-page__body">
        <div v-if="loading" class="state-panel state-panel--center">
          <p class="eyebrow">加载中</p>
          <h3>正在读取收藏人格…</h3>
        </div>

        <div v-else-if="error" class="state-panel state-panel--center">
          <p class="eyebrow">加载失败</p>
          <h3>收藏人格暂时不可用</h3>
          <p class="state-copy">{{ error }}</p>
          <button class="primary-btn" type="button" @click="load">重试</button>
        </div>

        <div v-else-if="!hasAnyFavorites" class="empty-panel empty-panel--compact">
          <h3>你还没有收藏过人格。</h3>
          <p class="empty-panel__copy">去 Seed 或 Mind 里收藏常用对象，这里都会收进来。</p>
          <RouterLink class="primary-btn" to="/seed">去 Seed 选择人格</RouterLink>
        </div>

        <div v-else class="group-stack group-stack--favorites">
          <article v-if="favoriteHexagrams.length" class="seed-group">
            <div class="seed-group__head">
              <h3>收藏卦象</h3>
              <span class="status-pill">{{ favoriteHexagrams.length }} 条</span>
            </div>

            <div class="persona-grid">
              <article v-for="item in favoriteHexagrams" :key="item.id" class="persona-card persona-card--featured">
                <div class="persona-card__meta">
                  <h4>{{ item.title || '未命名卦象' }}</h4>
                  <p class="persona-intro">{{ item.category }} · {{ item.castMode }}</p>
                </div>

                <div class="tag-row">
                  <span class="tag-chip">{{ new Date(item.updatedAt).toLocaleString('zh-CN') }}</span>
                  <span class="tag-chip">{{ item.chatTurns.length }} 段对话</span>
                </div>

                <div class="persona-actions persona-actions--stack">
                  <RouterLink class="text-link" to="/how-to-do">去查看卦象</RouterLink>
                </div>
              </article>
            </div>
          </article>

          <article v-for="group in groups" :key="group.group" class="seed-group">
            <div class="seed-group__head">
              <h3>{{ group.group }}</h3>
              <span class="status-pill">{{ group.items.length }} 个</span>
            </div>

            <div class="persona-grid">
              <article
                v-for="persona in group.items"
                :key="persona.slug"
                class="persona-card persona-card--featured"
              >
                <div class="persona-card__top">
                  <div class="persona-avatar">{{ persona.avatar || persona.name.slice(0, 2) }}</div>
                  <div class="persona-card__meta">
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
      </div>
    </div>
  </section>
</template>
