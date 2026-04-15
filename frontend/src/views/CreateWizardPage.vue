<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  clearWizardState,
  loadWizardState,
  saveLatestDraft,
  saveWizardState,
  submitCreateDraft,
} from '@/services/createWizardService'

type CreateType = 'self_persona' | 'source_persona' | 'relationship_persona'

const router = useRouter()
const route = useRoute()

const step = ref(1)
const loading = ref(false)
const error = ref('')
const createType = ref<CreateType>('self_persona')
const inputMode = ref('')
const selectedGroup = ref('')
const selectedName = ref('')

const formState = reactive({
  name: '',
  intro: '',
  values: '',
  decision_priority: '',
  expression_style: '',
  boundaries: '',
  target_name: '',
  material_type: '',
  material_description: '',
  focus_points: '',
  excluded_content: '',
  relationship_type: '',
  persona_name: '',
  speech_style: '',
  decision_logic: '',
  purpose: '',
  relation_boundaries: '',
})

const typeCards = [
  {
    type: 'self_persona' as const,
    title: '自我人格',
    description: '先把你自己的做事方式、回复方式和边界感整理出来。',
    hint: '从自己开始',
  },
  {
    type: 'source_persona' as const,
    title: '从资料创建',
    description: '把聊天记录、文档、音频或视频里的风格整理成一版结果。',
    hint: '从资料开始',
  },
  {
    type: 'relationship_persona' as const,
    title: '关系人格',
    description: '从同事、导师、父母或伴侣这类关系开始创建。',
    hint: '从关系开始',
  },
]

const inputModeLabels: Record<CreateType, Record<string, string>> = {
  self_persona: {
    manual_profile: '手动填写',
    chat_history: '聊天记录',
    documents: '文档资料',
  },
  source_persona: {
    documents: 'PDF / 文档',
    chat_history: '聊天记录',
    audio_video: '音频 / 视频',
    multi_source: '多源资料',
  },
  relationship_persona: {
    colleague: '同事',
    supervisor: '导师',
    parents: '父母',
    partner: '伴侣',
  },
}

const stepLabels = ['选择类型', '选择方式', '填写信息', '生成结果']

const currentInputs = computed(() => Object.entries(inputModeLabels[createType.value]))

const currentTypeLabel = computed(() => {
  if (createType.value === 'self_persona') {
    return '自我人格'
  }
  if (createType.value === 'source_persona') {
    return '从资料创建'
  }
  return '关系人格'
})

const selectedInputLabel = computed(() => {
  return inputModeLabels[createType.value][inputMode.value] || inputMode.value || '未选择'
})

function getInputModeNote(type: CreateType, mode: string) {
  if (type === 'self_persona') {
    if (mode === 'manual_profile') return '适合先从你自己的想法开始。'
    if (mode === 'chat_history') return '适合把对话里的表达方式整理出来。'
    if (mode === 'documents') return '适合把已有材料补充进去。'
  }

  if (type === 'source_persona') {
    if (mode === 'documents') return '适合先从文档或 PDF 开始。'
    if (mode === 'chat_history') return '适合先从聊天记录开始。'
    if (mode === 'audio_video') return '适合从音频或视频开始。'
    if (mode === 'multi_source') return '适合把多个来源放在一起。'
  }

  if (type === 'relationship_persona') {
    if (mode === 'colleague') return '适合同事视角。'
    if (mode === 'supervisor') return '适合导师视角。'
    if (mode === 'parents') return '适合父母视角。'
    if (mode === 'partner') return '适合伴侣视角。'
  }

  return '适合继续完善。'
}

function resetFormForType(type: CreateType) {
  if (type === 'self_persona') {
    formState.name = '我的自我人格'
    formState.intro = '把我自己的做事方式整理成可以继续聊天的人格。'
    formState.values = '更看重结果、边界和可执行性。'
    formState.decision_priority = '先看目标，再看路径。'
    formState.expression_style = '直接、清楚、略带解释。'
    formState.boundaries = '保留私密内容，不越过边界。'
  }

  if (type === 'source_persona') {
    formState.target_name = '资料人格'
    formState.material_type = '文档 / 聊天记录'
    formState.material_description = '基于已有资料提炼一个可对话人格。'
    formState.focus_points = '判断顺序\n表达习惯'
    formState.excluded_content = '隐私内容\n无关噪声'
  }

  if (type === 'relationship_persona') {
    formState.relationship_type = '同事'
    formState.persona_name = '关系人格'
    formState.speech_style = '说话直白、场景化。'
    formState.decision_logic = '先看现实条件，再给建议。'
    formState.purpose = '帮助理解这段关系。'
    formState.relation_boundaries = '不越界，不伪造确定事实。'
  }
}

function normalizeType(value: unknown): CreateType {
  const normalized = String(value || '').trim()
  if (normalized === 'source_persona') {
    return 'source_persona'
  }
  if (normalized === 'relationship_persona') {
    return 'relationship_persona'
  }
  return 'self_persona'
}

function saveStateSnapshot() {
  saveWizardState({
    step: step.value,
    createType: createType.value,
    inputMode: inputMode.value,
    selectedGroup: selectedGroup.value,
    selectedName: selectedName.value,
    formState: { ...formState },
  })
}

function loadStateSnapshot() {
  const snapshot = loadWizardState<{
    step?: number
    createType?: CreateType
    inputMode?: string
    selectedGroup?: string
    selectedName?: string
    formState?: Record<string, string>
  }>()

  if (!snapshot) {
    return false
  }

  if (snapshot.step) {
    step.value = Math.min(Math.max(snapshot.step, 1), 4)
  }

  if (snapshot.createType) {
    createType.value = snapshot.createType
  }

  if (snapshot.inputMode) {
    inputMode.value = snapshot.inputMode
  }

  selectedGroup.value = snapshot.selectedGroup || selectedGroup.value
  selectedName.value = snapshot.selectedName || selectedName.value

  if (snapshot.formState) {
    Object.assign(formState, snapshot.formState)
  }

  return true
}

function applyQueryDefaults() {
  const queryType = normalizeType(route.query.type)
  const queryGroup = String(route.query.group || '').trim()
  const queryName = String(route.query.name || '').trim()
  const reset = String(route.query.reset || '') === '1'

  if (reset) {
    clearWizardState()
  }

  createType.value = queryType
  selectedGroup.value = queryGroup
  selectedName.value = queryName

  if (createType.value === 'self_persona') {
    inputMode.value = inputMode.value || 'manual_profile'
  } else if (createType.value === 'source_persona') {
    inputMode.value = inputMode.value || 'documents'
  } else {
    inputMode.value = inputMode.value || 'colleague'
  }

  resetFormForType(createType.value)
}

function selectType(type: CreateType) {
  createType.value = type
  inputMode.value =
    type === 'self_persona' ? 'manual_profile' : type === 'source_persona' ? 'documents' : 'colleague'
  resetFormForType(type)
  step.value = 2
}

function selectInputMode(mode: string) {
  inputMode.value = mode
  step.value = 3
}

function goStep(nextStep: number) {
  step.value = Math.min(Math.max(nextStep, 1), 4)
}

async function generateDraft() {
  loading.value = true
  error.value = ''

  try {
    const draft = await submitCreateDraft({
      create_type: createType.value,
      input_mode: inputMode.value,
      form_data: { ...formState },
    })

    saveLatestDraft(draft)
    saveStateSnapshot()
    void router.push('/create/result')
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '生成结果失败'
    error.value = message
  } finally {
    loading.value = false
  }
}

function isCurrentType(type: CreateType) {
  return createType.value === type
}

watch([createType, inputMode, selectedGroup, selectedName], saveStateSnapshot)

watch(formState, saveStateSnapshot, { deep: true })

onMounted(() => {
  const restored = loadStateSnapshot()
  if (!restored) {
    applyQueryDefaults()
  } else if (String(route.query.reset || '') === '1') {
    applyQueryDefaults()
  }
  saveStateSnapshot()
})
</script>

<template>
  <section class="page-hero wizard-hero">
    <div class="hero-copy">
      <p class="eyebrow">创建向导</p>
      <h1>开始创建</h1>
      <p class="hero-text">按步骤填写信息，先生成一版人格雏形，再继续补充成更贴近你的样子。</p>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>{{ step }}/4</strong><span>当前步骤</span></span>
        <span class="metric-chip"><strong>{{ currentTypeLabel }}</strong><span>创建类型</span></span>
        <span class="metric-chip"><strong>{{ selectedInputLabel }}</strong><span>输入方式</span></span>
      </div>
    </div>

    <div class="hero-band">
      <article class="hero-band__card">
        <p class="eyebrow">创建方式</p>
        <h3 class="hero-band__title">{{ currentTypeLabel }}</h3>
        <p class="hero-band__copy">先把路径选好，再开始填写信息。</p>
      </article>

      <article class="hero-band__card">
        <p class="eyebrow">说明</p>
        <h3 class="hero-band__title">先生成一版可继续完善的结果</h3>
        <p class="hero-band__copy">你可以从自己、资料或关系开始。</p>
      </article>
    </div>
  </section>

  <section class="section-card">
    <div class="wizard-stepper">
      <button
        v-for="(label, index) in stepLabels"
        :key="label"
        type="button"
        class="wizard-stepper__item"
        :class="{ active: step === index + 1 }"
        @click="goStep(index + 1)"
      >
        <span>{{ index + 1 }}</span>
        <strong>{{ label }}</strong>
      </button>
    </div>

    <div class="wizard-layout">
      <div class="wizard-main">
        <article v-if="step === 1" class="wizard-stage">
          <div class="section-head">
            <div>
              <p class="eyebrow">第 1 步</p>
              <h3>选择创建类型</h3>
            </div>
            <p class="section-note">先确认你要从哪里开始创建。</p>
          </div>

          <div class="wizard-card-grid wizard-card-grid--three">
            <button
              v-for="card in typeCards"
              :key="card.type"
              class="create-mode-card wizard-choice-card"
              type="button"
              :class="{ 'create-card--active': isCurrentType(card.type) }"
              @click="selectType(card.type)"
            >
              <p class="feature-card__label">{{ card.hint }}</p>
              <h4>{{ card.title }}</h4>
              <p>{{ card.description }}</p>
            </button>
          </div>
        </article>

        <article v-else-if="step === 2" class="wizard-stage">
          <div class="section-head">
            <div>
              <p class="eyebrow">第 2 步</p>
              <h3>选择创建方式</h3>
            </div>
            <p class="section-note">不同类型会显示不同的方式选择。</p>
          </div>

          <div class="wizard-card-grid">
            <button
              v-for="[mode, label] in currentInputs"
              :key="mode"
              type="button"
              class="wizard-option-card"
              :class="{ active: inputMode === mode }"
              @click="selectInputMode(mode)"
            >
              <h4>{{ label }}</h4>
              <p>{{ getInputModeNote(createType, mode) }}</p>
            </button>
          </div>
        </article>

        <article v-else-if="step === 3" class="wizard-stage">
          <div class="section-head">
            <div>
              <p class="eyebrow">第 3 步</p>
              <h3>填写信息</h3>
            </div>
            <p class="section-note">先把关键变量写清楚，后面才更容易继续完善。</p>
          </div>

          <div v-if="createType === 'self_persona'" class="wizard-form">
            <div class="form-grid">
              <label class="form-field">
                <span>名称</span>
                <input v-model="formState.name" class="field-input" type="text" placeholder="例如：更理性的我" />
              </label>
              <label class="form-field">
                <span>一句话介绍</span>
                <input v-model="formState.intro" class="field-input" type="text" placeholder="一句话描述这个自我人格" />
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>你最看重什么</span>
                <textarea v-model="formState.values" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>做决定时优先看什么</span>
                <textarea v-model="formState.decision_priority" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>表达风格</span>
                <textarea v-model="formState.expression_style" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>希望保留的边界</span>
                <textarea v-model="formState.boundaries" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>
          </div>

          <div v-else-if="createType === 'source_persona'" class="wizard-form">
            <div class="form-grid">
              <label class="form-field">
                <span>目标人格名称</span>
                <input v-model="formState.target_name" class="field-input" type="text" placeholder="例如：工作助手视角" />
              </label>
              <label class="form-field">
                <span>材料类型</span>
                <input v-model="formState.material_type" class="field-input" type="text" placeholder="PDF / 聊天记录 / 音视频" />
              </label>
            </div>

            <label class="form-field">
              <span>材料说明</span>
              <textarea v-model="formState.material_description" class="field-input wizard-textarea" rows="4"></textarea>
            </label>

            <div class="form-grid">
              <label class="form-field">
                <span>希望提炼的重点</span>
                <textarea v-model="formState.focus_points" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>不希望被抽出的内容</span>
                <textarea v-model="formState.excluded_content" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>
          </div>

          <div v-else class="wizard-form">
            <div class="form-grid">
              <label class="form-field">
                <span>关系类型</span>
                <input v-model="formState.relationship_type" class="field-input" type="text" placeholder="同事 / 导师 / 父母 / 伴侣" />
              </label>
              <label class="form-field">
                <span>对方名称 / 称呼</span>
                <input v-model="formState.persona_name" class="field-input" type="text" placeholder="例如：李老师" />
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>对方典型说话方式</span>
                <textarea v-model="formState.speech_style" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>对方常见判断逻辑</span>
                <textarea v-model="formState.decision_logic" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>你希望这个人格帮你做什么</span>
                <textarea v-model="formState.purpose" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>你不希望它越过哪些边界</span>
                <textarea v-model="formState.relation_boundaries" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>
          </div>
        </article>

        <article v-else class="wizard-stage">
          <div class="section-head">
            <div>
              <p class="eyebrow">第 4 步</p>
              <h3>确认并生成结果</h3>
            </div>
            <p class="section-note">先看一眼，再生成第一版结果。</p>
          </div>

          <div class="wizard-review">
            <div class="summary-panel">
              <p class="eyebrow">确认信息</p>
              <h3>{{ currentTypeLabel }}</h3>
              <ul class="summary-panel__list">
                <li><span>输入方式</span><strong>{{ selectedInputLabel }}</strong></li>
                <li><span>创建类型</span><strong>{{ currentTypeLabel }}</strong></li>
                <li><span>组别</span><strong>{{ selectedGroup || '默认分组' }}</strong></li>
              </ul>
            </div>

            <div class="summary-panel">
              <p class="eyebrow">表单预览</p>
              <template v-if="createType === 'self_persona'">
                <h3>{{ formState.name || '未填写名称' }}</h3>
                <p class="state-copy">{{ formState.intro || '还没有写简介。' }}</p>
              </template>
              <template v-else-if="createType === 'source_persona'">
                <h3>{{ formState.target_name || '未填写目标名称' }}</h3>
                <p class="state-copy">{{ formState.material_description || '还没有描述材料。' }}</p>
              </template>
              <template v-else>
                <h3>{{ formState.persona_name || '未填写对象名称' }}</h3>
                <p class="state-copy">{{ formState.purpose || '还没有说明用途。' }}</p>
              </template>
            </div>
          </div>
        </article>

        <div v-if="error" class="state-panel">
          <p class="eyebrow">生成失败</p>
          <h3>结果生成暂时失败</h3>
          <p class="state-copy">{{ error }}</p>
        </div>

        <div class="wizard-actions">
          <button class="ghost-btn" type="button" :disabled="step === 1" @click="goStep(step - 1)">上一步</button>
          <button class="secondary-btn" type="button" :disabled="step === 4" @click="goStep(step + 1)">下一步</button>
          <button
            v-if="step === 4"
            class="primary-btn"
            type="button"
            :disabled="loading"
            @click="generateDraft"
          >
            {{ loading ? '生成中…' : '生成结果' }}
          </button>
        </div>
      </div>

      <aside class="wizard-rail">
        <div class="summary-panel">
          <p class="eyebrow">当前状态</p>
          <h3>按步骤填完就能看到第一版结果。</h3>
          <p class="state-copy">这版向导先帮你把信息整理成清晰的人格雏形，方便你先看轮廓。</p>
          <ul class="summary-panel__list">
            <li><span>类型</span><strong>{{ currentTypeLabel }}</strong></li>
            <li><span>输入方式</span><strong>{{ selectedInputLabel }}</strong></li>
            <li><span>状态</span><strong>可继续完善</strong></li>
          </ul>
        </div>

        <div class="summary-panel">
          <p class="eyebrow">当前支持</p>
          <h3>从自己、资料或关系开始。</h3>
          <ul class="summary-panel__list">
            <li><span>1</span><strong>从自己开始</strong></li>
            <li><span>2</span><strong>从资料开始</strong></li>
            <li><span>3</span><strong>从关系开始</strong></li>
          </ul>
        </div>
      </aside>
    </div>
  </section>
</template>
