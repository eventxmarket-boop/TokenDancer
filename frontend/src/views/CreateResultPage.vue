<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  loadLatestDraft,
  saveDraftLocally,
  saveLatestDraft,
  type CreateWizardDraft,
} from '@/services/createWizardService'

const router = useRouter()
const loading = ref(true)
const notice = ref('')
const draft = ref<CreateWizardDraft | null>(null)

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
}

const editableDraft = reactive<CreateWizardDraft>({
  meta: {
    id: '',
    slug: '',
    name: '',
    category: '',
    version: '',
    status: '',
    create_type: '',
    input_mode: '',
    group: '',
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
  return '关系人格'
})

const inputModeLabel = computed(() => {
  if (!draft.value) {
    return '未选择'
  }

  const mode = draft.value.meta.input_mode
  return inputModeLabels[mode] || mode || '未选择'
})

function applyDraft(nextDraft: CreateWizardDraft) {
  draft.value = nextDraft
  editableDraft.meta = { ...nextDraft.meta }
  editableDraft.profile = nextDraft.profile
  editableDraft.mindset = nextDraft.mindset
  editableDraft.heuristics = nextDraft.heuristics
  editableDraft.expression = nextDraft.expression
  editableDraft.guardrails = nextDraft.guardrails
}

function cloneDraft(source: CreateWizardDraft): CreateWizardDraft {
  return {
    meta: {
      ...source.meta,
      source_repos: [...source.meta.source_repos],
    },
    profile: source.profile,
    mindset: source.mindset,
    heuristics: source.heuristics,
    expression: source.expression,
    guardrails: source.guardrails,
  }
}

function persistEditedDraft() {
  const snapshot = cloneDraft(editableDraft)
  saveLatestDraft(snapshot)
  notice.value = '这版结果已同步保存。'
}

function saveDraft() {
  const snapshot = cloneDraft(editableDraft)
  saveLatestDraft(snapshot)
  saveDraftLocally(snapshot)
  notice.value = '这版结果已保存到本地。'
}

function backToWizard() {
  persistEditedDraft()
  void router.push('/create/wizard')
}

onMounted(() => {
  const storedDraft = loadLatestDraft()
  if (!storedDraft) {
    void router.replace('/create/wizard')
    return
  }

  applyDraft(storedDraft)
  loading.value = false
})

watch(
  editableDraft,
  (next) => {
    saveLatestDraft(cloneDraft(next))
  },
  { deep: true },
)
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
        <span class="metric-chip"><strong>可继续完善</strong><span>状态</span></span>
      </div>

      <div class="hero-actions">
        <button class="primary-btn" type="button" @click="saveDraft">保存这版结果</button>
        <button class="secondary-btn" type="button" @click="backToWizard">返回修改</button>
      </div>

      <p v-if="notice" class="persona-hero-note">{{ notice }}</p>
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

  <section class="section-card">
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

        <article class="draft-card">
          <p class="eyebrow">Profile</p>
          <pre class="draft-preview">{{ editableDraft.profile }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">Mindset</p>
          <pre class="draft-preview">{{ editableDraft.mindset }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">Heuristics</p>
          <pre class="draft-preview">{{ editableDraft.heuristics }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">Expression</p>
          <pre class="draft-preview">{{ editableDraft.expression }}</pre>
        </article>

        <article class="draft-card">
          <p class="eyebrow">Guardrails</p>
          <pre class="draft-preview">{{ editableDraft.guardrails }}</pre>
        </article>
      </div>

      <aside class="draft-rail">
        <div class="summary-panel">
          <p class="eyebrow">继续完善</p>
          <h3>现在可以直接继续改。</h3>
          <p class="state-copy">编辑区会实时同步当前结果，保存后会写入本地结果列表。</p>
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
            <button class="primary-btn" type="button" @click="saveDraft">保存这版结果</button>
            <button class="secondary-btn" type="button" @click="backToWizard">返回修改</button>
          </div>
          <button class="ghost-btn" type="button" disabled>后续继续完善</button>
        </div>
      </aside>
    </div>
  </section>
</template>
