<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import {
  loadCreateCatalog,
  type CreateCatalogGroup,
  type CreateCatalogItem,
  type CreateCatalogResponse,
} from '@/services/createCatalogService'

const loading = ref(true)
const error = ref('')
const catalog = ref<CreateCatalogResponse | null>(null)
const selectedSlug = ref('')

const groupOrder = [
  'self',
  'source',
  'relationship_workplace',
  'relationship_academia',
  'relationship_intimate',
  'relationship_family',
  'digital_twin',
  'protection',
]

const inputModeLabels: Record<string, string> = {
  manual_profile: '手动资料',
  chat_history: '聊天记录',
  documents: '文档',
  video: '视频',
  pdf: 'PDF',
  audio: '音频',
  digital_traces: '数字痕迹',
  personal_data: '个人数据',
  multi_platform_data: '多平台资料',
  memory_notes: '记忆笔记',
  skill_file: '技能文件',
}

const sectionAnchors: Record<string, string> = {
  self: 'create-self',
  source: 'create-source',
  relationship_workplace: 'create-relationship',
  relationship_academia: 'create-relationship-academia',
  relationship_intimate: 'create-relationship-intimate',
  relationship_family: 'create-relationship-family',
  digital_twin: 'create-digital-twin',
  protection: 'create-protection',
}

const groupLabels: Record<string, string> = {
  self: '自我人格',
  source: '资料投喂创建',
  relationship_workplace: '职场关系',
  relationship_academia: '学术关系',
  relationship_intimate: '亲密关系',
  relationship_family: '家庭关系',
  digital_twin: '数字分身',
  protection: '隐私与防护',
}

const groupDescriptions: Record<string, string> = {
  self: '从自己开始，把做事方式、回复方式和判断顺序整理成可用人格。',
  source: '从聊天记录、PDF、音频、视频和文本里提炼更像的回应方式。',
  relationship_workplace: '把同事和老板的工作关系整理成可以继续问的视角。',
  relationship_academia: '把导师、师兄和老师的视角整理成可对话模板。',
  relationship_intimate: '把亲密关系中的角色和互动模式整理成更细腻的模板。',
  relationship_family: '把父母、妈妈和重逢场景整理成更细腻的关系人格。',
  digital_twin: '做更高保真的长期数字分身或多平台蒸馏框架。',
  protection: '资料脱敏、防蒸馏与边界保留，不让创建流程越界。',
}

const groups = computed(() => {
  const items = catalog.value?.groups ?? []
  return [...items].sort((left, right) => {
    const leftOrder = groupOrder.indexOf(left.group)
    const rightOrder = groupOrder.indexOf(right.group)
    return (leftOrder === -1 ? 99 : leftOrder) - (rightOrder === -1 ? 99 : rightOrder)
  })
})

const allItems = computed(() => groups.value.flatMap((group) => group.items))

const selectedItem = computed(() => {
  if (!allItems.value.length) {
    return null
  }

  return allItems.value.find((item) => item.slug === selectedSlug.value) ?? allItems.value[0]
})

const totalItemCount = computed(() => allItems.value.length)
const totalRepoCount = computed(() => new Set(allItems.value.map((item) => item.source_repo)).size)

const topZones = computed(() => [
  {
    key: 'self',
    title: '自我人格',
    description: '从你自己开始，先做做事方式，再做表达方式。',
    target: sectionAnchors.self,
    count: countItems(['self']),
  },
  {
    key: 'source',
    title: '资料投喂创建',
    description: '聊天记录、文档、音频、视频都可以进入同一条创建路径。',
    target: sectionAnchors.source,
    count: countItems(['source']),
  },
  {
    key: 'relationship',
    title: '关系人格',
    description: '同事、老板、导师、伴侣、父母等关系都能按分组拆开。',
    target: sectionAnchors.relationship_workplace,
    count: countItems([
      'relationship_workplace',
      'relationship_academia',
      'relationship_intimate',
      'relationship_family',
    ]),
  },
  {
    key: 'digital_twin',
    title: '数字分身',
    description: '高保真、长期、多平台的蒸馏入口留在这里。',
    target: sectionAnchors.digital_twin,
    count: countItems(['digital_twin']),
  },
  {
    key: 'protection',
    title: '隐私与防护',
    description: '资料脱敏、防蒸馏和边界保留都归在这一区。',
    target: sectionAnchors.protection,
    count: countItems(['protection']),
  },
])

const selectedInputModes = computed(() =>
  (selectedItem.value?.input_modes ?? []).map((mode) => inputModeLabels[mode] || mode.replace(/_/g, ' ')),
)

function countItems(groupsToCount: string[]) {
  return groups.value
    .filter((group) => groupsToCount.includes(group.group))
    .reduce((total, group) => total + group.items.length, 0)
}

function sectionId(group: CreateCatalogGroup) {
  return sectionAnchors[group.group] || `create-${group.group}`
}

function getGroupLabel(group: string) {
  return groupLabels[group] || group
}

function getGroupDescription(group: string) {
  return groupDescriptions[group] || ''
}

function formatStage(stage: string) {
  if (stage === 'entry_only') {
    return '入口型'
  }
  return stage
}

async function scrollToTarget(targetId: string) {
  await nextTick()
  document.getElementById(targetId)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function focusItem(item: CreateCatalogItem) {
  selectedSlug.value = item.slug
  await nextTick()
  document.getElementById('create-rail')?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function startSelectedCreation() {
  if (!selectedItem.value) {
    return
  }

  void focusItem(selectedItem.value)
}

const loadCatalog = async () => {
  loading.value = true
  error.value = ''

  try {
    catalog.value = await loadCreateCatalog()
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载 Create 目录失败'
    error.value = message
    catalog.value = null
  } finally {
    loading.value = false
  }
}

watch(
  allItems,
  (items) => {
    if (!items.length) {
      return
    }

    if (!selectedSlug.value || !items.some((item) => item.slug === selectedSlug.value)) {
      selectedSlug.value = items[0].slug
    }
  },
  { immediate: true },
)

onMounted(() => {
  void loadCatalog()
})
</script>

<template>
  <section class="page-hero">
    <div class="hero-copy">
      <p class="eyebrow">Create</p>
      <h1>创造一个人格，先从方法开始。</h1>
      <p class="hero-text">
        这里不是人格成品列表，而是你真正开始创建人格的能力目录。你可以从自己开始，也可以从资料、关系、数字分身和边界保护开始。
      </p>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>{{ totalItemCount }}</strong><span>能力项</span></span>
        <span class="metric-chip"><strong>{{ groups.length }}</strong><span>能力分组</span></span>
        <span class="metric-chip"><strong>{{ totalRepoCount }}</strong><span>来源仓库</span></span>
      </div>

      <div class="hero-actions">
        <button class="primary-btn" type="button" @click="scrollToTarget(sectionAnchors.self)">创建自我人格</button>
        <button class="secondary-btn" type="button" @click="scrollToTarget(sectionAnchors.source)">上传资料生成</button>
      </div>

      <div class="inline-links">
        <RouterLink class="text-link" to="/seed">去 Seed 选择现成人格</RouterLink>
        <RouterLink class="text-link" to="/favorites">打开收藏人格</RouterLink>
        <RouterLink class="text-link" to="/sessions">查看最近会话</RouterLink>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">创建主线</p>
        <h3 class="hero-band__title">自我人格、资料投喂、关系人格</h3>
        <p class="hero-band__copy">先把能力目录分清，再把真正的蒸馏流程接进来。</p>
      </article>

      <article class="hero-band__card" id="create-rail">
        <p class="eyebrow">当前选中</p>
        <template v-if="selectedItem">
          <h3 class="hero-band__title">{{ selectedItem.name }}</h3>
          <p class="hero-band__copy">{{ selectedItem.description }}</p>
          <div class="tag-row">
            <span v-for="mode in selectedInputModes" :key="mode" class="tag-chip">{{ mode }}</span>
          </div>
        </template>
        <template v-else>
          <h3 class="hero-band__title">还没有可用的创建模板</h3>
          <p class="hero-band__copy">当后端目录加载完成后，这里会显示当前选中的创建能力。</p>
        </template>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">Create 路线</p>
        <h3>先看五条主创建路径，再进入细分模板。</h3>
      </div>
      <p class="section-note">点击任意卡片，直接跳到对应能力分区。</p>
    </div>

    <div class="create-mode-grid">
      <button
        v-for="zone in topZones"
        :key="zone.key"
        class="create-mode-card"
        type="button"
        @click="scrollToTarget(zone.target)"
      >
        <p class="feature-card__label">{{ zone.key }}</p>
        <h4>{{ zone.title }}</h4>
        <p>{{ zone.description }}</p>
        <div class="create-mode-card__meta">
          <span class="status-pill">{{ zone.count }} 个模板</span>
          <span class="text-link">查看分区</span>
        </div>
      </button>
    </div>
  </section>

  <section class="section-card">
    <div class="section-head">
      <div>
        <p class="eyebrow">能力目录</p>
        <h3>按功能分区展开，每一组都有自己的创建模板。</h3>
      </div>
      <p class="section-note">这些条目全部归在 Create，不会混进 Seed。</p>
    </div>

    <div v-if="loading" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取 Create 能力目录…</h3>
    </div>

    <div v-else-if="error" class="state-panel">
      <p class="eyebrow">加载失败</p>
      <h3>Create 目录暂时不可用</h3>
      <p class="state-copy">{{ error }}</p>
      <button class="primary-btn" type="button" @click="loadCatalog">重试</button>
    </div>

    <div v-else class="create-layout">
      <div class="create-main">
        <article
          v-for="group in groups"
          :key="group.group"
          class="create-group"
          :id="sectionId(group)"
        >
          <div class="create-group__head">
            <div>
              <p class="eyebrow">{{ group.source_hint }}</p>
              <h3>{{ group.label }}</h3>
              <p class="section-note">{{ getGroupDescription(group.group) }}</p>
            </div>
            <span class="status-pill">{{ group.items.length }} 个模式</span>
          </div>

          <div class="create-card-grid">
            <article
              v-for="item in group.items"
              :key="item.slug"
              class="create-card"
              :class="{ 'create-card--active': selectedItem?.slug === item.slug }"
            >
              <div class="create-card__head">
                <div>
                  <p class="persona-category">{{ item.source_repo }}</p>
                  <h4>{{ item.name }}</h4>
                </div>
                <span class="status-pill">{{ formatStage(item.stage) }}</span>
              </div>

              <p class="create-card__copy">{{ item.description }}</p>

              <div class="tag-row">
                <span v-for="mode in item.input_modes" :key="mode" class="tag-chip">
                  {{ inputModeLabels[mode] || mode.replace(/_/g, ' ') }}
                </span>
              </div>

              <div class="create-card__actions">
                <button class="primary-btn" type="button" @click="focusItem(item)">开始创建</button>
                <button class="ghost-btn" type="button" @click="scrollToTarget(sectionId(group))">
                  继续浏览
                </button>
              </div>
            </article>
          </div>
        </article>
      </div>

      <aside class="create-rail">
        <div class="summary-panel">
          <p class="eyebrow">创建说明</p>
          <h3>先选模式，再选材料，最后接入蒸馏流程。</h3>
          <p class="state-copy">
            当前版本先把能力目录、模板来源和分组路径整理清楚。真正的上传、生成与调优流程，后面会继续接进来。
          </p>

          <ul class="summary-panel__list">
            <li><span>主线 1</span><strong>自我人格</strong></li>
            <li><span>主线 2</span><strong>资料 / 关系 / 数字分身</strong></li>
            <li><span>保护层</span><strong>防蒸馏与边界</strong></li>
          </ul>
        </div>

        <div class="summary-panel">
          <p class="eyebrow">当前模式</p>
          <template v-if="selectedItem">
            <h3>{{ selectedItem.name }}</h3>
            <p class="state-copy">{{ selectedItem.description }}</p>
            <ul class="summary-panel__list">
              <li><span>分组</span><strong>{{ getGroupLabel(selectedItem.group) }}</strong></li>
              <li><span>来源</span><strong>{{ selectedItem.source_repo }}</strong></li>
              <li><span>输入方式</span><strong>{{ selectedInputModes.join(' · ') }}</strong></li>
            </ul>
            <div class="hero-actions">
              <button class="primary-btn" type="button" @click="startSelectedCreation">开始创建</button>
              <RouterLink class="secondary-btn" to="/seed">切到 Seed</RouterLink>
            </div>
          </template>
          <template v-else>
            <h3>等待目录加载</h3>
            <p class="state-copy">加载完成后，这里会显示当前选中的创建模式。</p>
          </template>
        </div>

        <div class="summary-panel">
          <p class="eyebrow">后续能力</p>
          <h3>这一轮先做入口，后续再接生成执行器。</h3>
          <ul class="summary-panel__list">
            <li><span>自我蒸馏</span><strong>Work System</strong></li>
            <li><span>回复方式</span><strong>Reply Persona</strong></li>
            <li><span>资料输入</span><strong>文档 / 语音 / 视频</strong></li>
            <li><span>隐私保护</span><strong>脱敏 / 边界</strong></li>
          </ul>
        </div>
      </aside>
    </div>
  </section>
</template>
