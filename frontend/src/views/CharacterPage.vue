<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { loadPersona, type Persona } from '@/services/personaService'
import { getFavoriteSlugs, toggleFavoriteSlug } from '@/services/favoriteService'

const route = useRoute()
const persona = ref<Persona | null>(null)
const loading = ref(true)
const error = ref('')
const notFound = ref(false)
const favoriteSlugs = ref<string[]>(getFavoriteSlugs())

const slug = computed(() => String(route.params.id || ''))
const isFavorite = computed(() => {
  const current = persona.value?.slug
  return current ? favoriteSlugs.value.includes(current) : false
})

const load = async () => {
  const target = slug.value.trim()
  if (!target) {
    persona.value = null
    notFound.value = true
    loading.value = false
    return
  }

  loading.value = true
  error.value = ''
  notFound.value = false

  try {
    const result = await loadPersona(target)
    persona.value = result
    notFound.value = result === null
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载人格详情失败'
    error.value = message
    persona.value = null
  } finally {
    loading.value = false
  }
}

const refreshFavorites = () => {
  favoriteSlugs.value = getFavoriteSlugs()
}

const toggleFavorite = () => {
  if (!persona.value || persona.value.isFavoritable === false) {
    return
  }
  toggleFavoriteSlug(persona.value.slug)
  refreshFavorites()
}

onMounted(() => {
  void load()
})

watch(slug, () => {
  void load()
})
</script>

<template>
  <section v-if="loading" class="empty-state">
    <div class="section-card">
      <p class="eyebrow">加载中</p>
      <h2>正在读取人格详情…</h2>
    </div>
  </section>

  <section v-else-if="error" class="empty-state">
    <div class="section-card">
      <p class="eyebrow">加载失败</p>
      <h2>人格详情暂时不可用</h2>
      <p class="state-copy">{{ error }}</p>
      <RouterLink class="primary-btn" to="/">返回首页</RouterLink>
    </div>
  </section>

  <section v-else-if="notFound || !persona" class="empty-state">
    <div class="section-card">
      <p class="eyebrow">未找到</p>
      <h2>没有找到这个人格。</h2>
      <p class="state-copy">请确认链接是否存在。</p>
      <RouterLink class="primary-btn" to="/">返回首页</RouterLink>
    </div>
  </section>

  <section v-else class="detail-layout">
    <article class="detail-card">
      <div class="detail-header">
        <div class="detail-avatar">{{ persona.avatar || persona.name.slice(0, 2) }}</div>
        <div>
          <h2>{{ persona.name }}</h2>
          <p class="hero-text">{{ persona.intro }}</p>
        </div>
      </div>

      <div class="detail-block">
        <h3>标签</h3>
        <div class="tag-row">
          <span v-for="tag in persona.tags" :key="tag" class="tag-chip">{{ tag }}</span>
        </div>
      </div>

      <div class="detail-block">
        <h3>适用话题</h3>
        <div class="tag-row">
          <span v-for="topic in persona.topics" :key="topic" class="tag-chip">{{ topic }}</span>
        </div>
      </div>

      <div class="detail-block">
        <h3>人物定位</h3>
        <p class="persona-profile">{{ persona.profile }}</p>
      </div>

      <div class="detail-actions">
        <RouterLink class="primary-btn" :to="`/chat/${persona.slug}`">开始聊天</RouterLink>
        <button
          v-if="persona.isFavoritable !== false"
          class="secondary-btn"
          type="button"
          @click="toggleFavorite"
        >
          {{ isFavorite ? '取消收藏' : '收藏人格' }}
        </button>
        <RouterLink class="secondary-btn" to="/">回到首页</RouterLink>
      </div>
    </article>

    <aside class="detail-side">
      <div class="mini-panel">
        <p class="eyebrow">推荐提问</p>
        <ul class="question-list">
          <li v-for="question in persona.recommendedQuestions" :key="question">{{ question }}</li>
        </ul>
      </div>
    </aside>
  </section>
</template>
