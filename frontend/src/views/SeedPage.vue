<script setup lang="ts">
import { computed, nextTick, onMounted, ref } from 'vue'
import { loadSeedPersonas, type Persona } from '@/services/personaService'
import { getFavoriteSlugs, toggleFavoriteSlug } from '@/services/favoriteService'

const loading = ref(true)
const error = ref('')
const seedPersonas = ref<Persona[]>([])
const favoriteSlugs = ref<string[]>(getFavoriteSlugs())
const listSectionRef = ref<HTMLElement | null>(null)
const featuredSectionRef = ref<HTMLElement | null>(null)
const groupSectionRef = ref<HTMLElement | null>(null)
const featuredExpanded = ref(false)

const displayLabelMap: Record<string, string> = {
  self: '我的人格',
  source: '从资料创建',
  work: '职场关系',
  intimate: '亲密关系',
  family: '家人陪伴',
  digital_twin: '数字分身',
  protection: '防护',
  relationship_workplace: '职场关系',
  relationship_academia: '校园关系',
  relationship_intimate: '亲密关系',
  relationship_family: '家人陪伴',
}

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

const formatLabel = (value: string | undefined | null) => {
  const raw = String(value || '').trim()
  if (!raw) {
    return '未分组'
  }
  if (/[\u4e00-\u9fff]/.test(raw)) {
    return raw
  }
  return displayLabelMap[raw] || '未分组'
}

const scrollToSection = async (target: 'list' | 'featured' | 'groups') => {
  const el =
    target === 'featured'
      ? featuredSectionRef.value
      : target === 'groups'
        ? groupSectionRef.value
        : listSectionRef.value
  if (target === 'featured' && !featuredExpanded.value) {
    featuredExpanded.value = true
    await nextTick()
  }
  el?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

const toggleFeaturedPreview = async () => {
  featuredExpanded.value = !featuredExpanded.value
  if (featuredExpanded.value) {
    await nextTick()
    featuredSectionRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }
}

const toggleFavorite = (slug: string) => {
  toggleFavoriteSlug(slug)
  refreshFavorites()
}

onMounted(() => {
  void loadSeeds()
})
</script>

<template>
  <section class="page-hero page-hero--single">
    <div class="hero-copy">
      <p class="eyebrow">Seed</p>
      <h1>选择现成人格</h1>

      <div class="hero-metrics">
        <button class="metric-chip metric-chip--button" type="button" @click="scrollToSection('list')">
          <strong>{{ seedPersonas.length }}</strong><span>种子人格</span>
        </button>
        <button class="metric-chip metric-chip--button" type="button" @click="scrollToSection('featured')">
          <strong>{{ featuredPersonas.length }}</strong><span>精选推荐</span>
        </button>
        <button class="metric-chip metric-chip--button" type="button" @click="scrollToSection('groups')">
          <strong>{{ groups.length }}</strong><span>分类分组</span>
        </button>
      </div>

      <div class="hero-actions">
        <RouterLink class="primary-btn" to="/create">去创建</RouterLink>
        <RouterLink class="secondary-btn" to="/favorites">打开收藏</RouterLink>
        <button class="secondary-btn" type="button" @click="toggleFeaturedPreview">
          {{ featuredExpanded ? '收起' : '精选推荐' }}
        </button>
      </div>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">Seed 列表</p>
        <h3>人格卡片总列表</h3>
      </div>
    </div>

    <div class="seed-layout seed-layout--stack">
      <div ref="listSectionRef" class="seed-main">
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

        <div v-else ref="groupSectionRef" class="group-stack group-stack--dense">
          <article v-for="group in groups" :key="group.group" class="seed-group">
            <div class="seed-group__head">
              <div>
                <p class="eyebrow">分组</p>
                <h3>{{ formatLabel(group.group) }}</h3>
              </div>
            </div>

            <div class="persona-grid">
              <article v-for="persona in group.personas" :key="persona.slug" class="persona-card persona-card--featured persona-card--seed">
                <div class="persona-card__top">
                  <div class="persona-avatar">{{ persona.avatar || persona.name.slice(0, 2) }}</div>
                  <div class="persona-card__meta">
                    <h4>{{ persona.name }}</h4>
                    <p class="persona-intro">{{ persona.intro }}</p>
                  </div>
                </div>

                <div class="persona-card__foot">
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
    </div>

    <article v-if="featuredExpanded" ref="featuredSectionRef" class="summary-panel summary-panel--featured summary-panel--featured-inline">
      <div class="seed-featured__head">
        <div>
          <p class="eyebrow">精选推荐</p>
          <h3>推荐人格</h3>
        </div>
        <button class="secondary-btn" type="button" @click="toggleFeaturedPreview">收起</button>
      </div>

      <div class="summary-panel__list">
        <div
          v-for="persona in featuredPersonas.slice(0, 4)"
          :key="persona.slug"
          class="session-card session-card--compact"
        >
          <div class="session-card__top">
            <div>
              <h4 class="session-card__title">{{ persona.name }}</h4>
            </div>
          </div>
          <p class="persona-intro">{{ persona.intro }}</p>
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

      <div class="seed-featured__foot">
        <button class="secondary-btn" type="button" @click="toggleFeaturedPreview">收起</button>
      </div>
    </article>
  </section>
</template>
