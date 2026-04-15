<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { loadMySeeds, type CreatedPersonaSummary } from '@/services/createdPersonaService'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const seeds = ref<CreatedPersonaSummary[]>([])

const typeLabels: Record<string, string> = {
  self_persona: '自我',
  source_persona: '资料',
  relationship_persona: '关系',
  family_companion: '家人陪伴',
}

const groupedSeeds = computed(() => {
  const map = new Map<string, CreatedPersonaSummary[]>()
  for (const seed of seeds.value) {
    const bucket = map.get(seed.persona_type) || []
    bucket.push(seed)
    map.set(seed.persona_type, bucket)
  }

  const order = ['self_persona', 'source_persona', 'relationship_persona', 'family_companion']
  return order
    .map((type) => ({
      type,
      label: typeLabels[type] || type,
      items: map.get(type) || [],
    }))
    .filter((group) => group.items.length > 0)
})

const load = async () => {
  loading.value = true
  error.value = ''

  try {
    seeds.value = await loadMySeeds()
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载我创建的 Seed 失败'
    error.value = message
    seeds.value = []
  } finally {
    loading.value = false
  }
}

function openSeed(seedId: number) {
  void router.push({ path: '/create/result', query: { seed_id: String(seedId) } })
}

function chatSeed(slug: string) {
  void router.push({ path: `/chat/${slug}` })
}

onMounted(() => {
  void load()
})
</script>

<template>
  <section class="my-seeds-page">
    <div class="my-seeds-page__inner">
      <div class="my-seeds-page__head">
        <p class="eyebrow">我创建的 Seed</p>
        <h1>我创建的 Seed</h1>
        <p class="hero-text">查看你创建过的人格，并继续使用。</p>
      </div>

      <div v-if="loading" class="state-panel state-panel--center">
        <p class="eyebrow">加载中</p>
        <h3>正在读取我创建的 Seed…</h3>
      </div>

      <div v-else-if="error" class="state-panel state-panel--center">
        <p class="eyebrow">加载失败</p>
        <h3>我创建的 Seed 暂时不可用</h3>
        <p class="state-copy">{{ error }}</p>
        <button class="primary-btn" type="button" @click="load">重试</button>
      </div>

      <div v-else-if="!seeds.length" class="empty-panel empty-panel--compact">
        <h3>你还没有创建过 Seed。</h3>
        <p class="empty-panel__copy">先去 Create 创建一版结果，保存后就会出现在这里。</p>
        <RouterLink class="primary-btn" to="/create">去创建</RouterLink>
      </div>

      <div v-else class="my-seeds-group-stack">
        <article v-for="group in groupedSeeds" :key="group.type" class="seed-group">
          <div class="seed-group__head">
            <h3>{{ group.label }}</h3>
            <span class="status-pill">{{ group.items.length }} 个</span>
          </div>

          <div class="persona-grid">
            <article v-for="seed in group.items" :key="seed.id" class="persona-card persona-card--featured">
              <div class="persona-card__top">
                <div class="persona-avatar">{{ seed.name.slice(0, 2) }}</div>
                <div class="persona-card__meta">
                  <p class="persona-category">{{ group.label }}</p>
                  <h4>{{ seed.name }}</h4>
                  <p class="persona-intro">{{ seed.summary || '这是一版可以继续完善的人格。' }}</p>
                </div>
              </div>

              <div class="tag-row">
                <span class="tag-chip">{{ typeLabels[seed.persona_type] || seed.persona_type }}</span>
                <span class="tag-chip">{{ new Date(seed.created_at).toLocaleDateString() }}</span>
              </div>

              <div class="persona-actions persona-actions--stack">
                <button class="chip-btn chip-btn--active" type="button" @click="openSeed(seed.id)">
                  查看
                </button>
                <button class="chip-btn" type="button" @click="chatSeed(seed.slug)">
                  对话
                </button>
                <button class="chip-btn" type="button" @click="openSeed(seed.id)">
                  编辑
                </button>
              </div>
            </article>
          </div>
        </article>
      </div>
    </div>
  </section>
</template>
