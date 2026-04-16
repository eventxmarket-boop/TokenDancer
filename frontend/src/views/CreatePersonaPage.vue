<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  loadCreateCatalog,
  type CreateCatalogGroup,
  type CreateCatalogItem,
  type CreateCatalogResponse,
} from '@/services/createCatalogService'

type MainPathKey = 'self' | 'source' | 'work' | 'intimate' | 'family'

type MainPathSection = {
  key: MainPathKey
  title: string
  description: string
  groupKeys: string[]
}

const router = useRouter()
const loading = ref(true)
const error = ref('')
const catalog = ref<CreateCatalogResponse | null>(null)
const expandedSection = ref<MainPathKey | null>('self')

const mainPathSections: MainPathSection[] = [
  {
    key: 'self',
    title: '我的人格',
    description: '从你的做事方式、表达习惯、思考路径和生活痕迹出发。',
    groupKeys: ['self'],
  },
  {
    key: 'source',
    title: '从资料创建',
    description: '从聊天记录、文档或其他资料中整理出一个人格雏形。',
    groupKeys: ['source', 'digital_twin', 'protection'],
  },
  {
    key: 'work',
    title: '职场关系',
    description: '把同事、老板、导师或老师的风格整理出来。',
    groupKeys: ['relationship_workplace', 'relationship_academia'],
  },
  {
    key: 'intimate',
    title: '亲密关系',
    description: '从亲密关系里的表达方式、互动习惯和情绪逻辑出发。',
    groupKeys: ['relationship_intimate'],
  },
  {
    key: 'family',
    title: '家人陪伴',
    description: '从熟悉的关心方式、说话方式和记忆片段中开始，也可进入重逢人格。',
    groupKeys: ['relationship_family'],
  },
]

const displayLabelMap: Record<string, string> = {
  'self-skill': '我的人格',
  'nuwa-skill': '我的人格',
  'forge-skill': '我的人格',
  'digital-life': '我的人格',
  'self-skill+nuwa-skill+forge-skill+digital-life': '我的人格',
  'colleague-skill': '同事',
  'boss-skills': '老板',
  supervisor: '导师',
  'senpai-skill': '师兄',
  'professor-skill': '大学老师',
  Professor_skill: '大学老师',
  'ex-skill': '前任',
  'relationship-training-skill': '关系训练',
  relationship_understanding: '关系理解',
  message_simulation: '消息模拟',
  partner_maintenance: '关系维护',
  past_relation_mirror: '过去关系 / 自我镜像',
  'npy-skill': '理想伴侣',
  'crush-skill': '暧昧消息',
  'partner-skill': '伴侣维护',
  'first-love-skill': '初恋',
  'shuixian-skill': '自我镜像',
  xinyi: '关系理解',
  colleague: '同事',
  boss: '老板',
  senpai: '师兄',
  professor_a: '大学老师',
  professor_b: '大学老师',
  'parents-skills': '父母',
  'reunion-skill': '重逢人格',
  MamaSkill: '妈妈',
  'MamaSkill+parents-skills+darwin-skill': '妈妈',
  'parents-skills+MamaSkill': '妈妈',
  mother: '妈妈',
  parents: '父母',
  other_family: '其他家人',
  mama: '妈妈',
  reunion: '重逢人格',
  'digital-twin-skill': '数字分身',
  'immortal-skill': '数字分身',
  'anti-distill': '防护',
  manual_profile: '手动填写',
  chat_history: '聊天记录',
  documents: '文档',
  video: '视频',
  pdf: 'PDF',
  audio: '音频',
  digital_traces: '数字痕迹',
  personal_data: '个人资料',
  multi_platform_data: '多平台资料',
  memory_notes: '记忆笔记',
  skill_file: '资料内容',
  image_notes: '图片说明',
  voice_notes: '语音说明',
  text_materials: '文本材料',
  diary_notes: '日记',
  letter_notes: '信件',
  photo_notes: '照片说明',
  conflict_text: '冲突片段',
  draft_message_text: '待发送消息',
  recent_context_text: '最近上下文',
  reply_style_samples_text: '回复样本',
  relationship_status_text: '关系状态',
  interaction_patterns_text: '互动样本',
  history_text: '历史材料',
  expression_samples_text: '表达样本',
}

const schemaKeyBySourceRepo: Record<string, string> = {
  'self-skill': 'self_unified',
  'nuwa-skill': 'self_unified',
  'forge-skill': 'self_unified',
  'digital-life': 'self_unified',
  'self-skill+nuwa-skill+forge-skill+digital-life': 'self_unified',
  'anyone-to-skill': 'source_anyone_from_sources',
  'colleague-skill': 'relationship_workplace_colleague',
  'boss-skills': 'relationship_workplace_boss',
  supervisor: 'relationship_academia_supervisor',
  'senpai-skill': 'relationship_academia_senpai',
  'professor-skill': 'relationship_academia_professor_a',
  Professor_skill: 'relationship_academia_professor_b',
  'ex-skill': 'relationship_intimate_ex',
  'relationship-training-skill': 'relationship_intimate_relationship_training',
  'npy-skill': 'relationship_intimate_ideal_partner',
  'crush-skill': 'relationship_intimate_crush',
  'partner-skill': 'relationship_intimate_partner',
  'first-love-skill': 'relationship_intimate_first_love',
  'shuixian-skill': 'relationship_intimate_self_mirror',
  xinyi: 'relationship_intimate_relationship_interpreter',
  'parents-skills': 'relationship_family_parents',
  'reunion-skill': 'relationship_family_reunion',
  MamaSkill: 'relationship_family_mama',
  'MamaSkill+parents-skills+darwin-skill': 'family_companion_mother',
  'digital-twin-skill': 'digital_twin_high_fidelity',
  'immortal-skill': 'digital_twin_immortal',
  'anti-distill': 'protection_anti_distill',
}

const inputModeBySourceRepo: Record<string, string> = {
  'self-skill': 'manual_profile',
  'nuwa-skill': 'documents',
  'forge-skill': 'chat_history',
  'digital-life': 'documents',
  'self-skill+nuwa-skill+forge-skill+digital-life': 'manual_profile',
  'anyone-to-skill': 'documents',
  'colleague-skill': 'colleague',
  'boss-skills': 'boss',
  supervisor: 'supervisor',
  'senpai-skill': 'senpai',
  'professor-skill': 'professor_a',
  Professor_skill: 'professor_b',
  'ex-skill': 'ex',
  'relationship-training-skill': 'relationship_training',
  'npy-skill': 'ideal_partner',
  'crush-skill': 'crush',
  'partner-skill': 'partner',
  'first-love-skill': 'first_love',
  'shuixian-skill': 'self_mirror',
  xinyi: 'relationship_interpreter',
  'parents-skills': 'parents',
  'reunion-skill': 'reunion',
  MamaSkill: 'mama',
  'MamaSkill+parents-skills+darwin-skill': 'mother',
  'digital-twin-skill': 'multi_source',
  'immortal-skill': 'multi_source',
  'anti-distill': 'documents',
}

function getDefaultInputMode(item: CreateCatalogItem) {
  return inputModeBySourceRepo[item.source_repo] || item.input_modes[0] || 'manual_profile'
}

function getSchemaKeyForItem(item: CreateCatalogItem) {
  if (item.create_type === 'self_unified' || item.group === 'self') {
    return 'self_unified'
  }
  if (item.create_type === 'family_companion') {
    return `family_companion_${getDefaultInputMode(item)}`
  }
  if (item.create_type === 'reunion_persona') {
    return `reunion_persona_${getDefaultInputMode(item)}`
  }
  return schemaKeyBySourceRepo[item.source_repo] || `${item.group}_${item.slug}`
}

function getWizardCreateTypeForItem(item: CreateCatalogItem) {
  return item.create_type || getWizardTypeForGroup(item.group)
}

const groups = computed(() => {
  const items = catalog.value?.groups ?? []
  return [...items].sort((left, right) => {
    const order: Record<string, number> = {
      self: 0,
      source: 1,
      relationship_workplace: 2,
      relationship_academia: 3,
      relationship_intimate: 4,
      relationship_family: 5,
      digital_twin: 6,
      protection: 7,
    }
    return (order[left.group] ?? 99) - (order[right.group] ?? 99)
  })
})

const sectionViews = computed(() => {
  const map = new Map(groups.value.map((group) => [group.group, group] as const))

  return mainPathSections.map((section) => {
    const matchedGroups = section.groupKeys
      .map((groupKey) => map.get(groupKey))
      .filter((group): group is CreateCatalogGroup => Boolean(group))

    const items = matchedGroups
      .flatMap((group) => group.items)
      .filter((item) => {
        if (section.key !== 'family') {
          return true
        }
        return (
          item.create_type === 'family_companion' ||
          item.create_type === 'reunion_persona' ||
          item.slug === 'family_companion' ||
          item.slug === 'reunion_persona'
        )
      })

    return {
      ...section,
      groups: matchedGroups,
      items,
      itemCount: items.length,
    }
  })
})

function getWizardTypeForGroup(group: string) {
  if (group === 'self') {
    return 'self_unified'
  }
  if (group === 'source') {
    return 'source_persona'
  }
  if (group === 'relationship_family') {
    return 'family_companion'
  }
  if (group === 'relationship_intimate') {
    return 'intimate_companion'
  }
  if (group === 'relationship_workplace' || group === 'relationship_academia') {
    return 'relationship_persona'
  }
  return ''
}

function buildWizardQuery(item: CreateCatalogItem) {
  const createType = getWizardCreateTypeForItem(item)
  return {
    create_type: createType,
    group: item.group,
    source_repo: item.source_repo,
    display_name: item.name,
    create_mode: createType === 'self_unified' ? 'standard' : '',
    input_mode: getDefaultInputMode(item),
    schema_key: getSchemaKeyForItem(item),
    reset: '1',
  }
}

function canOpenWizard(item: CreateCatalogItem) {
  return Boolean(getWizardCreateTypeForItem(item))
}

function toggleSection(sectionKey: MainPathKey) {
  expandedSection.value = expandedSection.value === sectionKey ? null : sectionKey
}

function collapseSection(sectionKey: MainPathKey) {
  if (expandedSection.value === sectionKey) {
    expandedSection.value = null
  }
}

function getDisplayLabel(value: string) {
  return displayLabelMap[value] || value.replace(/[_-]+/g, ' ')
}

function startCreation(item: CreateCatalogItem) {
  const type = getWizardCreateTypeForItem(item)
  if (!type) {
    return
  }

  void router.push({
    path: '/create/wizard',
    query: buildWizardQuery(item),
  })
}

const loadCatalog = async () => {
  loading.value = true
  error.value = ''

  try {
    catalog.value = await loadCreateCatalog()
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '加载 Create 内容失败'
    error.value = message
    catalog.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  void loadCatalog()
})
</script>

<template>
  <section class="page-hero create-hero">
    <div class="hero-copy">
      <p class="eyebrow">Create</p>
      <h1>创造一个人格</h1>
      <p class="hero-text">从自己、资料，或某种关系开始，创建一个人格。</p>
    </div>
  </section>

  <section class="section-card create-accordion-shell">
    <div class="section-head">
      <div>
        <p class="eyebrow">创建路径</p>
        <h3>先选一条主路径，再展开里面的内容。</h3>
      </div>
      <p class="section-note">点击任意卡片，开始创建。</p>
    </div>

    <div v-if="loading" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取创建路径…</h3>
    </div>

    <div v-else-if="error" class="state-panel">
      <p class="eyebrow">加载失败</p>
      <h3>Create 页面暂时不可用</h3>
      <p class="state-copy">{{ error }}</p>
      <button class="primary-btn" type="button" @click="loadCatalog">重试</button>
    </div>

    <div v-else class="create-accordion">
      <article
        v-for="section in sectionViews"
        :key="section.key"
        class="create-accordion__section"
        :class="{ active: expandedSection === section.key }"
      >
        <button class="create-accordion__trigger" type="button" @click="toggleSection(section.key)">
          <div>
            <p class="eyebrow">主路径</p>
            <h3>{{ section.title }}</h3>
            <p class="section-note">{{ section.description }}</p>
          </div>
          <span class="status-pill">{{ section.itemCount }} 个入口</span>
        </button>

        <transition name="accordion-slide">
          <div v-if="expandedSection === section.key" class="create-accordion__panel">
            <div class="create-accordion__panel-head">
              <button class="secondary-btn" type="button" @click="collapseSection(section.key)">收起</button>
            </div>
            <div v-for="group in section.groups" :key="group.group" class="create-subgroup">
              <div class="create-subgroup__head">
                <div>
                  <p class="eyebrow">{{ group.label }}</p>
                  <h4>{{ group.label }}</h4>
                </div>
                <span class="status-pill">{{ group.items.length }} 个入口</span>
              </div>

              <p class="section-note">{{ group.description }}</p>

              <div class="create-card-grid">
                <article
                  v-for="item in group.items"
                  :key="item.slug"
                  class="create-card create-card--compact"
                >
                  <div class="create-card__head">
                    <div>
                      <p class="persona-category">{{ group.label }}</p>
                      <h4>{{ item.name }}</h4>
                    </div>
                  </div>

                  <p class="create-card__copy">{{ item.description }}</p>

                  <div class="tag-row">
                    <span v-for="mode in item.input_modes" :key="mode" class="tag-chip">
                      {{ getDisplayLabel(mode) }}
                    </span>
                  </div>

                  <div class="create-card__actions">
                    <button
                      v-if="canOpenWizard(item)"
                      class="primary-btn"
                      type="button"
                      @click="startCreation(item)"
                    >
                      开始创建
                    </button>
                    <span v-else class="status-pill">更多方式</span>
                  </div>
                </article>
              </div>
            </div>
          </div>
        </transition>
      </article>
    </div>
  </section>
</template>
