<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  loadLatestDraft,
  saveDraftLocally,
  saveLatestDraft,
  type CreateWizardDraft,
  type FamilyCompanionMemoryBase,
  type FamilyCompanionPersonaProfile,
  type IntimateCompanionMemoryBase,
  type IntimateCompanionRelationshipProfile,
} from '@/services/createWizardService'
import {
  loadMySeed,
  saveMySeed,
  type CreatedPersonaRecord,
} from '@/services/createdPersonaService'

const router = useRouter()
const route = useRoute()
const loading = ref(true)
const notice = ref('')
const draft = ref<CreateWizardDraft | null>(null)
const createdSeedId = ref<number | null>(null)
const createdSeed = ref<CreatedPersonaRecord | null>(null)
const saving = ref(false)
const editorAnchor = ref<HTMLElement | null>(null)

const inputModeLabels: Record<string, string> = {
  manual_profile: '手动填写',
  chat_history: '聊天记录',
  documents: '文档资料',
  audio_video: '音频 / 视频',
  multi_source: '多源资料',
  colleague: '同事',
  supervisor: '导师',
  parents: '父母',
  partner: '伴侣',
  mother: '妈妈',
  other_family: '其他家人',
  relationship_understanding: '关系理解',
  message_simulation: '消息模拟',
  partner_maintenance: '关系维护',
  past_relation_mirror: '过去关系 / 自我镜像',
}

const editableDraft = reactive<CreateWizardDraft>({
  meta: {
    id: '',
    slug: '',
    name: '',
    category: '',
    display_name: '',
    version: '',
    status: '',
    create_type: '',
    input_mode: '',
    group: '',
    schema_key: '',
    source_repo: '',
    repo_url: '',
    source_repos: [],
    source_hint: '',
    stage: '',
    persona_kind: '',
    generated_at: '',
  },
  profile: '',
  mindset: '',
  heuristics: '',
  expression: '',
  guardrails: '',
  relationship_type: '',
  persona_profile: null,
  memory_base: null,
  relationship_profile: null,
  intimate_memory_base: null,
})

const typeLabel = computed(() => {
  if (!draft.value) {
    return '人格雏形'
  }

  const type = draft.value.meta.create_type
  if (type === 'self_persona') {
    return '自我人格'
  }
  if (type === 'source_persona') {
    return '从资料创建'
  }
  if (type === 'family_companion') {
    return '家人陪伴'
  }
  if (type === 'intimate_companion') {
    return '亲密关系'
  }
  return '关系人格'
})

const inputModeLabel = computed(() => {
  if (!draft.value) {
    return '未选择'
  }

  const mode = draft.value.meta.input_mode
  return inputModeLabels[mode] || mode || '未选择'
})

const savedSeedLabel = computed(() => {
  if (createdSeed.value) {
    return '已保存到“我创建的 Seed”'
  }
  return '先保存到“我创建的 Seed”'
})

const familyPersonaProfile = computed<FamilyCompanionPersonaProfile | null>(() => {
  const payload = draft.value?.persona_profile || editableDraft.persona_profile
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const familyMemoryBase = computed<FamilyCompanionMemoryBase | null>(() => {
  const payload = draft.value?.memory_base || editableDraft.memory_base
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const intimateRelationshipProfile = computed<IntimateCompanionRelationshipProfile | null>(() => {
  const payload = draft.value?.relationship_profile || editableDraft.relationship_profile
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const intimateMemoryBase = computed<IntimateCompanionMemoryBase | null>(() => {
  const payload = draft.value?.intimate_memory_base || editableDraft.intimate_memory_base
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const familyProfileLines = computed(() => {
  const profile = familyPersonaProfile.value
  if (!profile) {
    return []
  }

  return [
    { label: '关系类型', value: profile.relationship_type || '未填写' },
    { label: '称呼', value: profile.name || '未填写' },
    { label: '说话风格', value: profile.tone || '未填写' },
    { label: '常见口头禅', value: profile.catchphrases?.join(' / ') || '未填写' },
    { label: '难过时', value: profile.comfort_style || '未填写' },
    { label: '好消息时', value: profile.celebration_style || '未填写' },
    { label: '边界', value: profile.boundaries || '未填写' },
  ]
})

const familyMemoryLines = computed(() => {
  const memory = familyMemoryBase.value
  if (!memory) {
    return []
  }

  return [
    { label: '关键共同经历', value: memory.shared_events?.join(' / ') || '未填写' },
    { label: '最常提起的往事', value: memory.daily_habits?.join(' / ') || '未填写' },
    { label: '反复说过的话', value: memory.important_advice?.join(' / ') || '未填写' },
    { label: '在意的事', value: memory.emotional_triggers?.join(' / ') || '未填写' },
  ]
})

const intimateProfileLines = computed(() => {
  const profile = intimateRelationshipProfile.value
  if (!profile) {
    return []
  }

  return [
    { label: '关系类型', value: profile.relationship_type || '未填写' },
    { label: '对象称呼', value: profile.name || '未填写' },
    { label: '关系阶段', value: profile.relationship_stage || '未填写' },
    { label: '说话风格', value: profile.tone || '未填写' },
    { label: '回复温度', value: profile.response_temperature || '未填写' },
    { label: '边界', value: profile.boundaries || '未填写' },
    { label: '口头禅', value: profile.catchphrases?.join(' / ') || '未填写' },
  ]
})

const intimateMemoryLines = computed(() => {
  const memory = intimateMemoryBase.value
  if (!memory) {
    return []
  }

  return [
    { label: '对话样本', value: memory.conversation_samples?.join(' / ') || '未填写' },
    { label: '互动规则', value: memory.interaction_rules?.join(' / ') || '未填写' },
    { label: '关系目标', value: memory.relationship_goals?.join(' / ') || '未填写' },
    { label: '关键记忆', value: memory.key_memories?.join(' / ') || '未填写' },
  ]
})

function applyDraft(nextDraft: CreateWizardDraft) {
  const snapshot = cloneDraft(nextDraft)
  draft.value = snapshot
  Object.assign(editableDraft, snapshot)
}

function cloneDraft(source: CreateWizardDraft): CreateWizardDraft {
  return JSON.parse(JSON.stringify(source)) as CreateWizardDraft
}

async function ensureSeedSaved() {
  if (createdSeedId.value) {
    return true
  }

  await saveDraft()
  return Boolean(createdSeedId.value)
}

async function goToMySeeds() {
  const saved = await ensureSeedSaved()
  if (!saved) {
    return
  }
  void router.push('/my-seeds')
}

async function startChat() {
  const saved = await ensureSeedSaved()
  if (!saved) {
    return
  }
  const slug = createdSeed.value?.slug?.trim() || editableDraft.meta.slug.trim()
  if (!slug) {
    return
  }
  void router.push(`/chat/${slug}`)
}

function continueEditing() {
  editorAnchor.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

async function persistToBackend() {
  const snapshot = cloneDraft(editableDraft)
  const response = await saveMySeed(
    {
      draft: snapshot,
      source_type: 'create_wizard',
      status: 'saved',
    },
    createdSeedId.value,
  )

  createdSeedId.value = response.id
  createdSeed.value = response
  applyDraft(response.draft_payload)
  editableDraft.meta.slug = response.slug
  saveLatestDraft(response.draft_payload)
  saveDraftLocally(response.draft_payload)
  notice.value = '已保存到“我创建的 Seed”'
  await router.replace({ query: { ...route.query, seed_id: String(response.id) } })
}

async function saveDraft() {
  saving.value = true
  notice.value = ''

  try {
    await persistToBackend()
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '保存失败'
    notice.value = message
  } finally {
    saving.value = false
  }
}

function backToWizard() {
  persistEditedDraft()
  void router.push('/create/wizard')
}

function persistEditedDraft() {
  const snapshot = cloneDraft(editableDraft)
  saveLatestDraft(snapshot)
}

async function loadFromSeed(seedId: number) {
  const record = await loadMySeed(seedId)
  if (!record) {
    return false
  }

  createdSeedId.value = record.id
  createdSeed.value = record
  applyDraft(record.draft_payload)
  editableDraft.meta.slug = record.slug
  saveLatestDraft(record.draft_payload)
  return true
}

async function loadInitialDraft() {
  const querySeedId = Number(route.query.seed_id || 0)
  if (querySeedId > 0) {
    const restored = await loadFromSeed(querySeedId)
    if (restored) {
      loading.value = false
      return
    }
  }

  const storedDraft = loadLatestDraft()
  if (!storedDraft) {
    await router.replace('/create/wizard')
    return
  }

  applyDraft(storedDraft)
  loading.value = false
}

watch(
  editableDraft,
  (next) => {
    saveLatestDraft(cloneDraft(next))
  },
  { deep: true },
)

onMounted(() => {
  void loadInitialDraft()
})
</script>

<template>
  <section class="page-hero wizard-hero">
    <div class="hero-copy">
      <p class="eyebrow">创建结果</p>
      <h1>你的人格雏形已经生成。</h1>
      <p class="hero-text">这是第一版结果。你可以继续补充内容，让它更完整、更贴近真实使用场景。</p>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>{{ typeLabel }}</strong><span>人格类型</span></span>
        <span class="metric-chip"><strong>{{ editableDraft.meta.name || '未命名' }}</strong><span>结果名称</span></span>
        <span class="metric-chip"><strong>{{ savedSeedLabel }}</strong><span>保存状态</span></span>
      </div>

      <div class="hero-actions">
        <button class="primary-btn" type="button" :disabled="saving" @click="saveDraft">
          {{ saving ? '保存中…' : createdSeedId ? '保存更新' : '保存到我的 Seed' }}
        </button>
        <button class="secondary-btn" type="button" @click="backToWizard">返回修改</button>
      </div>

      <p v-if="notice" class="persona-hero-note">{{ notice }}</p>

      <div v-if="createdSeedId || createdSeed" class="hero-actions hero-actions--wrap">
        <button class="secondary-btn" type="button" @click="goToMySeeds">去我的 Seed</button>
        <button class="secondary-btn" type="button" @click="startChat">开始对话</button>
        <button class="secondary-btn" type="button" @click="continueEditing">继续编辑</button>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">后续动作</p>
        <h3 class="hero-band__title">后面可以继续完善成正式人格</h3>
        <p class="hero-band__copy">这一版结果先收好，后面还可以继续补充信息。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">保存状态</p>
        <h3 class="hero-band__title">这版结果已可复用</h3>
        <p class="hero-band__copy">保存后可以继续回到向导修改，也能留作后续完善的起点。</p>
      </article>
    </div>
  </section>

  <section class="section-card" ref="editorAnchor">
    <div v-if="loading" class="state-panel">
      <p class="eyebrow">加载中</p>
      <h3>正在读取最新结果…</h3>
    </div>

      <div v-else class="draft-layout">
      <div class="draft-main">
        <article class="draft-card draft-card--header">
          <div class="draft-card__head">
            <div>
              <p class="eyebrow">结果身份</p>
              <h3>{{ editableDraft.meta.name }}</h3>
            </div>
            <span class="status-pill">{{ typeLabel }}</span>
          </div>
          <p class="state-copy">{{ inputModeLabel }} · {{ editableDraft.meta.generated_at }}</p>
        </article>

        <article v-if="draft?.meta.create_type === 'family_companion'" class="draft-card">
          <p class="eyebrow">人格层</p>
          <div class="family-grid">
            <div v-for="line in familyProfileLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'family_companion'" class="draft-card">
          <p class="eyebrow">记忆层</p>
          <div class="family-grid">
            <div v-for="line in familyMemoryLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'intimate_companion'" class="draft-card">
          <p class="eyebrow">关系层</p>
          <div class="family-grid">
            <div v-for="line in intimateProfileLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'intimate_companion'" class="draft-card">
          <p class="eyebrow">记忆层</p>
          <div class="family-grid">
            <div v-for="line in intimateMemoryLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article class="draft-card">
          <p class="eyebrow">定位</p>
          <pre class="draft-preview">{{ editableDraft.profile }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">思考方式</p>
          <pre class="draft-preview">{{ editableDraft.mindset }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">判断规则</p>
          <pre class="draft-preview">{{ editableDraft.heuristics }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">表达风格</p>
          <pre class="draft-preview">{{ editableDraft.expression }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">边界</p>
          <pre class="draft-preview">{{ editableDraft.guardrails }}</pre>
        </article>
      </div>

      <aside class="draft-rail">
        <div class="summary-panel">
          <p class="eyebrow">继续完善</p>
          <h3>现在可以直接继续改。</h3>
          <p class="state-copy">编辑区会实时同步当前结果，保存后会写入我的 Seed。</p>
        </div>

        <div class="summary-panel">
          <label class="form-field">
            <span>名称</span>
            <input v-model="editableDraft.meta.name" class="field-input" type="text" />
          </label>
          <label class="form-field">
            <span>Profile</span>
            <textarea v-model="editableDraft.profile" class="field-input wizard-textarea" rows="6"></textarea>
          </label>
          <label class="form-field">
            <span>Mindset</span>
            <textarea v-model="editableDraft.mindset" class="field-input wizard-textarea" rows="6"></textarea>
          </label>
          <label class="form-field">
            <span>Heuristics</span>
            <textarea v-model="editableDraft.heuristics" class="field-input wizard-textarea" rows="6"></textarea>
          </label>
          <label class="form-field">
            <span>Expression</span>
            <textarea v-model="editableDraft.expression" class="field-input wizard-textarea" rows="6"></textarea>
          </label>
          <label class="form-field">
            <span>Guardrails</span>
            <textarea v-model="editableDraft.guardrails" class="field-input wizard-textarea" rows="6"></textarea>
          </label>

          <div class="hero-actions">
            <button class="primary-btn" type="button" :disabled="saving" @click="saveDraft">
              {{ saving ? '保存中…' : createdSeedId ? '保存更新' : '保存到我的 Seed' }}
            </button>
            <button class="secondary-btn" type="button" @click="backToWizard">返回修改</button>
          </div>
          <button class="ghost-btn" type="button" disabled>后续继续完善</button>
        </div>
      </aside>
    </div>
  </section>
</template>
