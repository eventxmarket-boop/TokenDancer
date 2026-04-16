<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  clearWizardState,
  loadWizardState,
  saveLatestDraft,
  saveWizardState,
  submitCreateDraft,
  type TextMaterialDocument,
} from '@/services/createWizardService'

type CreateType =
  | 'self_unified'
  | 'source_persona'
  | 'relationship_persona'
  | 'family_companion'
  | 'reunion_persona'
  | 'intimate_companion'

type SelfCreateMode = 'light' | 'standard' | 'deep'

const router = useRouter()
const route = useRoute()

const step = ref(1)
const loading = ref(false)
const error = ref('')
const createType = ref<CreateType>('self_unified')
const createMode = ref<SelfCreateMode>('standard')
const selfInputModes = ref<string[]>(['manual_profile'])
const inputMode = ref('')
const selectedGroup = ref('')
const selectedName = ref('')
const selectedSourceRepo = ref('')
const selectedSchemaKey = ref('')
const isBootstrapping = ref(false)

function normalizeSelfUnifiedDisplayName(value: unknown) {
  const text = String(value || '').trim()
  if (!text || text === '我的人格') {
    return '自我主线'
  }
  return text
}

const formState = reactive({
  name: '',
  create_mode: 'standard',
  work_system_summary: '',
  work_system_points: '',
  reply_persona_summary: '',
  reply_persona_points: '',
  thinking_dna_summary: '',
  thinking_dna_points: '',
  memory_evidence_summary: '',
  memory_evidence_points: '',
  reflection_rules_summary: '',
  reflection_rules_points: '',
  target_name: '',
  material_type: '',
  material_description: '',
  focus_points: '',
  excluded_content: '',
  relationship_type: '',
  persona_name: '',
  relationship_stage: '',
  speech_style: '',
  response_temperature: '',
  decision_logic: '',
  purpose: '',
  relation_boundaries: '',
  catchphrases: '',
  comfort_style: '',
  celebration_style: '',
  shared_events: '',
  important_advice: '',
  daily_habits: '',
  emotional_triggers: '',
  chat_history_summary: '',
  memory_fragments: '',
  text_materials: '',
  image_notes: '',
  voice_notes: '',
  remembrance_style: '',
  retrieval_mode: '',
  priority_rules: '',
  fallback_rules: '',
  safety_boundaries: '',
  emotional_protection: '',
  avoid_triggers: '',
  diary_notes: '',
  letter_notes: '',
  photo_notes: '',
  conversation_samples: '',
  interaction_rules: '',
  relationship_goals: '',
  key_memories: '',
  shared_memories: '',
})

const typeCards = [
  {
    type: 'self_unified' as const,
    title: '自我主线',
    description: '先把做事方式、回复方式、思考路径和生活痕迹整理出来。',
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
  {
    type: 'intimate_companion' as const,
    title: '亲密关系',
    description: '从关系理解、消息模拟、关系维护或过去关系开始创建。',
    hint: '从亲密关系开始',
  },
]

const inputModeLabels: Record<CreateType, Record<string, string>> = {
  self_unified: {
    manual_profile: '手动填写',
    chat_history: '聊天记录',
    documents: '文档资料',
    memory_notes: '记忆片段',
  },
  source_persona: {
    documents: 'PDF / 文档',
    chat_history: '聊天记录',
    audio_video: '音频 / 视频',
    multi_source: '多源资料',
  },
  relationship_persona: {
    colleague: '同事',
    boss: '老板',
    supervisor: '导师',
    senpai: '师兄',
    professor_a: '大学老师',
    professor_b: '大学老师（模板 B）',
  },
  intimate_companion: {
    relationship_understanding: '关系理解',
    message_simulation: '消息模拟',
    partner_maintenance: '关系维护',
    past_relation_mirror: '过去关系 / 自我镜像',
  },
  family_companion: {
    mother: '妈妈',
    parents: '父母',
    other_family: '其他家人',
  },
  reunion_persona: {
    chat_history: '聊天记录',
    documents: '文档资料',
    memory_notes: '记忆片段',
    photo_notes: '照片 / 截图',
    voice_notes: '语音 / 口述',
  },
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
  'parents-skills': 'parents',
  'reunion-skill': 'reunion',
  MamaSkill: 'mama',
  'MamaSkill+parents-skills+darwin-skill': 'mother',
  'parents-skills+MamaSkill': 'mother',
  'digital-twin-skill': 'multi_source',
  'immortal-skill': 'multi_source',
  'anti-distill': 'documents',
  'relationship-training-skill': 'relationship_understanding',
  xinyi: 'relationship_understanding',
  'relationship-training-skill+xinyi': 'relationship_understanding',
  'crush-skill': 'message_simulation',
  'partner-skill': 'partner_maintenance',
  'npy-skill': 'partner_maintenance',
  'partner-skill+npy-skill': 'partner_maintenance',
  'ex-skill': 'past_relation_mirror',
  'first-love-skill': 'past_relation_mirror',
  'shuixian-skill': 'past_relation_mirror',
  'ex-skill+first-love-skill+shuixian-skill': 'past_relation_mirror',
}

const sourceRepoByInputMode: Record<string, string> = {
  manual_profile: 'self-skill',
  chat_history: 'self-skill',
  documents: 'anyone-to-skill',
  audio_video: 'anyone-to-skill',
  multi_source: 'anyone-to-skill',
  colleague: 'colleague-skill',
  boss: 'boss-skills',
  supervisor: 'supervisor',
  senpai: 'senpai-skill',
  professor_a: 'professor-skill',
  professor_b: 'Professor_skill',
  ex: 'ex-skill',
  relationship_training: 'relationship-training-skill',
  ideal_partner: 'npy-skill',
  crush: 'crush-skill',
  partner: 'partner-skill',
  first_love: 'first-love-skill',
  self_mirror: 'shuixian-skill',
  relationship_interpreter: 'xinyi',
  parents: 'parents-skills',
  reunion: 'reunion-skill',
  mama: 'MamaSkill',
  mother: 'MamaSkill+parents-skills+darwin-skill',
  other_family: 'MamaSkill+parents-skills+darwin-skill',
  relationship_understanding: 'relationship-training-skill+xinyi',
  message_simulation: 'crush-skill',
  partner_maintenance: 'partner-skill+npy-skill',
  past_relation_mirror: 'ex-skill+first-love-skill+shuixian-skill',
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
  'relationship-training-skill': 'intimate_companion_relationship_understanding',
  xinyi: 'intimate_companion_relationship_understanding',
  'relationship-training-skill+xinyi': 'intimate_companion_relationship_understanding',
  'crush-skill': 'intimate_companion_message_simulation',
  'partner-skill': 'intimate_companion_partner_maintenance',
  'npy-skill': 'intimate_companion_partner_maintenance',
  'partner-skill+npy-skill': 'intimate_companion_partner_maintenance',
  'ex-skill': 'intimate_companion_past_relation_mirror',
  'first-love-skill': 'intimate_companion_past_relation_mirror',
  'shuixian-skill': 'intimate_companion_past_relation_mirror',
  'ex-skill+first-love-skill+shuixian-skill': 'intimate_companion_past_relation_mirror',
  'parents-skills': 'relationship_family_parents',
  'reunion-skill': 'relationship_family_reunion',
  MamaSkill: 'relationship_family_mama',
  'MamaSkill+parents-skills+darwin-skill': 'family_companion_mother',
  'parents-skills+MamaSkill': 'family_companion_mother',
  'digital-twin-skill': 'digital_twin_high_fidelity',
  'immortal-skill': 'digital_twin_immortal',
  'anti-distill': 'protection_anti_distill',
}

const isFamilyCompanion = computed(() => createType.value === 'family_companion' || createType.value === 'reunion_persona')
const isReunionPersona = computed(() => createType.value === 'reunion_persona')
const isSelfUnified = computed(() => createType.value === 'self_unified')

const stepLabels = computed(() =>
  isSelfUnified.value
    ? ['选择深度', '选择方式', '填写信息', '生成结果']
    : isFamilyCompanion.value
    ? ['选择关系类型', '填写信息', '确认结果', '生成结果']
    : isReunionPersona.value
    ? ['选择材料', '填写信息', '确认结果', '生成结果']
    : ['选择类型', '选择方式', '填写信息', '生成结果'],
)

const currentInputs = computed(() => Object.entries(inputModeLabels[createType.value] || {}))

const selfModeCards = [
  {
    mode: 'light' as const,
    title: '轻量模式',
    description: '先用表单快速生成一版人格骨架。',
  },
  {
    mode: 'standard' as const,
    title: '标准模式',
    description: '表单加少量材料，生成更稳的一版结果。',
  },
  {
    mode: 'deep' as const,
    title: '深度模式',
    description: '表单加材料再加反思层，做更完整的自己。',
  },
]

const selfInputModeOptions = [
  { key: 'manual_profile', label: '手动填写' },
  { key: 'chat_history', label: '聊天记录' },
  { key: 'documents', label: '文档资料' },
  { key: 'memory_notes', label: '记忆片段' },
]

const selfModeLabels: Record<SelfCreateMode, string> = {
  light: '轻量模式',
  standard: '标准模式',
  deep: '深度模式',
}

const memoryEvidenceFileName = ref('')
const familyMaterialFileName = ref('')
const reunionMaterialFileName = ref('')
const intimateMaterialFileName = ref('')
const familyUploadedTextDocuments = ref<TextMaterialDocument[]>([])
const reunionUploadedTextDocuments = ref<TextMaterialDocument[]>([])
const intimateUploadedTextDocuments = ref<TextMaterialDocument[]>([])
const familyChatHistoryText = computed({
  get: () => formState.chat_history_summary,
  set: (value: string) => {
    formState.chat_history_summary = value
  },
})
const familyMemoryNotesText = computed({
  get: () => formState.memory_fragments,
  set: (value: string) => {
    formState.memory_fragments = value
  },
})
const familyTextMaterialsText = computed({
  get: () => formState.text_materials,
  set: (value: string) => {
    formState.text_materials = value
  },
})
const familyImageNotesText = computed({
  get: () => formState.image_notes,
  set: (value: string) => {
    formState.image_notes = value
  },
})
const familyVoiceNotesText = computed({
  get: () => formState.voice_notes,
  set: (value: string) => {
    formState.voice_notes = value
  },
})

const currentTypeLabel = computed(() => {
  if (createType.value === 'self_unified') {
    return '自我主线'
  }
  if (createType.value === 'source_persona') {
    return '从资料创建'
  }
  if (createType.value === 'reunion_persona') {
    return '重逢人格'
  }
  if (createType.value === 'intimate_companion') {
    return '亲密关系'
  }
  if (createType.value === 'family_companion') {
    return '家人陪伴'
  }
  return '关系人格'
})

const selectedInputLabel = computed(() => {
  if (isSelfUnified.value) {
    const modes = selfInputModes.value.length
      ? selfInputModes.value.map((mode) => inputModeLabels.self_unified[mode] || mode).join(' / ')
      : '未选择'
    return `${selfModeLabels[createMode.value]} · ${modes}`
  }
  return inputModeLabels[createType.value]?.[inputMode.value] || inputMode.value || '未选择'
})

function readQueryValue(key: string) {
  const value = route.query[key]
  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }
  return String(value || '').trim()
}

function normalizeCreateType(value: string): CreateType {
  if (
    value === 'self_persona' ||
    value === 'self_mindset_distill' ||
    value === 'self_deep_self_persona' ||
    value === 'self_digital_trace_persona'
  ) {
    return 'self_unified'
  }
  if (
    value === 'self_unified' ||
    value === 'source_persona' ||
    value === 'relationship_persona' ||
    value === 'family_companion' ||
    value === 'reunion_persona' ||
    value === 'intimate_companion'
  ) {
    return value
  }
  return 'self_unified'
}

function inferCreateTypeFromQuery() {
  const explicit = readQueryValue('create_type') || readQueryValue('type')
  if (explicit) {
    return normalizeCreateType(explicit)
  }

  if (explicit === 'relationship_persona') {
    const relationGroup = readQueryValue('group')
    if (relationGroup === 'relationship_family') {
      return readQueryValue('source_repo') === 'reunion-skill' ? 'reunion_persona' : 'family_companion'
    }
    if (relationGroup === 'relationship_intimate') {
      return 'intimate_companion'
    }
    return 'relationship_persona'
  }

  const group = readQueryValue('group')
  if (group === 'source') {
    return 'source_persona'
  }
  if (group === 'relationship_family') {
    return readQueryValue('source_repo') === 'reunion-skill' ? 'reunion_persona' : 'family_companion'
  }
  if (group === 'relationship_intimate') {
    return 'intimate_companion'
  }
  if (
    group === 'relationship_workplace' ||
    group === 'relationship_academia' ||
    group === 'relationship'
  ) {
    return 'relationship_persona'
  }

  return 'self_unified'
}

function resolveInputMode(createTypeValue: CreateType, sourceRepo: string, schemaKey: string) {
  if (schemaKey && schemaKey in inputModeLabels[createTypeValue]) {
    return schemaKey
  }

  if (sourceRepo && inputModeBySourceRepo[sourceRepo]) {
    return inputModeBySourceRepo[sourceRepo]
  }

  if (createTypeValue === 'self_unified') {
    return 'manual_profile'
  }

  if (createTypeValue === 'source_persona') {
    return 'documents'
  }
  if (createTypeValue === 'family_companion') {
    return 'mother'
  }
  if (createTypeValue === 'reunion_persona') {
    return 'chat_history'
  }
  if (createTypeValue === 'intimate_companion') {
    return 'relationship_understanding'
  }

  return 'colleague'
}

function resolveSchemaKey(createTypeValue: CreateType, sourceRepo: string, inputModeValue: string, displayName: string) {
  if (createTypeValue === 'family_companion') {
    return `family_companion_${inputModeValue || 'mother'}`
  }
  if (createTypeValue === 'reunion_persona') {
    return `reunion_persona_${inputModeValue || 'chat_history'}`
  }
  if (createTypeValue === 'intimate_companion') {
    return `intimate_companion_${inputModeValue || 'relationship_understanding'}`
  }
  if (sourceRepo && schemaKeyBySourceRepo[sourceRepo]) {
    return schemaKeyBySourceRepo[sourceRepo]
  }

  const fallbackKey = `${createTypeValue}_${inputModeValue || 'default'}`
  return displayName ? `${fallbackKey}_${displayName}` : fallbackKey
}

function getDefaultGroupForType(type: CreateType) {
  if (type === 'self_unified') {
    return 'self'
  }
  if (type === 'source_persona') {
    return 'source'
  }
  if (type === 'family_companion') {
    return 'relationship_family'
  }
  if (type === 'reunion_persona') {
    return 'relationship_family'
  }
  if (type === 'intimate_companion') {
    return 'relationship_intimate'
  }
  return 'relationship_workplace'
}

function getDefaultSourceRepoForType(type: CreateType) {
  if (type === 'self_unified') {
    return 'self-skill+nuwa-skill+forge-skill+digital-life'
  }
  if (type === 'source_persona') {
    return 'anyone-to-skill'
  }
  if (type === 'family_companion') {
    return 'parents-skills+MamaSkill'
  }
  if (type === 'reunion_persona') {
    return 'reunion-skill'
  }
  if (type === 'intimate_companion') {
    return 'relationship-training-skill+xinyi'
  }
  return 'colleague-skill'
}

function getDefaultDisplayNameForType(type: CreateType) {
  if (type === 'self_unified') {
    return '自我主线'
  }
  if (type === 'source_persona') {
    return '资料人格'
  }
  if (type === 'family_companion') {
    return '家人陪伴'
  }
  if (type === 'reunion_persona') {
    return '重逢人格'
  }
  if (type === 'intimate_companion') {
    return '亲密关系'
  }
  return '关系人格'
}

function selectSelfMode(mode: SelfCreateMode) {
  createMode.value = mode
  selectedGroup.value = getDefaultGroupForType(createType.value)
  selectedSourceRepo.value = getDefaultSourceRepoForType(createType.value)
  selectedName.value = getDefaultDisplayNameForType(createType.value)
  selectedSchemaKey.value = 'self_unified'
  inputMode.value = 'manual_profile'
  selfInputModes.value = ['manual_profile']
  resetFormForType(createType.value, selectedName.value, inputMode.value)
  step.value = 2
}

function toggleSelfInputMode(mode: string) {
  const allowedModes = new Set(['manual_profile', 'chat_history', 'documents', 'memory_notes'])
  if (!allowedModes.has(mode)) {
    return
  }

  const existing = new Set(selfInputModes.value)
  if (existing.has(mode)) {
    existing.delete(mode)
  } else {
    existing.add(mode)
  }

  selfInputModes.value = Array.from(existing)
  if (!selfInputModes.value.length) {
    selfInputModes.value = ['manual_profile']
  }
  inputMode.value = mode
  selectedGroup.value = getDefaultGroupForType(createType.value)
  selectedSourceRepo.value = getDefaultSourceRepoForType(createType.value)
  selectedName.value = getDefaultDisplayNameForType(createType.value)
  selectedSchemaKey.value = 'self_unified'
}

function handleSelfMemoryFileChange(event: Event) {
  const target = event.target as HTMLInputElement | null
  const file = target?.files?.[0]
  if (!file) {
    return
  }

  memoryEvidenceFileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    const content = String(reader.result || '').trim()
    if (!content) {
      return
    }
    if (!selfInputModes.value.includes('documents')) {
      selfInputModes.value = Array.from(new Set([...selfInputModes.value, 'documents']))
    }
    const appended = [formState.memory_evidence_points, content].filter(Boolean).join('\n')
    formState.memory_evidence_points = appended
  }
  reader.readAsText(file)
  target.value = ''
}

function appendTextToFormField(field: keyof typeof formState, content: string) {
  const current = String(formState[field] || '').trim()
  const appended = [current, content.trim()].filter(Boolean).join('\n')
  formState[field] = appended
}

function handleFamilyMaterialFileChange(event: Event) {
  const target = event.target as HTMLInputElement | null
  const file = target?.files?.[0]
  if (!file) {
    return
  }

  familyMaterialFileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    const content = String(reader.result || '').trim()
    if (!content) {
      return
    }
    familyUploadedTextDocuments.value = [
      ...familyUploadedTextDocuments.value,
      { filename: file.name, content },
    ]
    appendTextToFormField('text_materials', content)
    appendTextToFormField('memory_fragments', content)
    saveStateSnapshot()
  }
  reader.readAsText(file)
  target.value = ''
}

function removeFamilyUploadedTextDocument(index: number) {
  if (index < 0 || index >= familyUploadedTextDocuments.value.length) {
    return
  }
  familyUploadedTextDocuments.value = familyUploadedTextDocuments.value.filter((_, itemIndex) => itemIndex !== index)
  saveStateSnapshot()
}

function handleReunionMaterialFileChange(event: Event) {
  const target = event.target as HTMLInputElement | null
  const file = target?.files?.[0]
  if (!file) {
    return
  }

  reunionMaterialFileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    const content = String(reader.result || '').trim()
    if (!content) {
      return
    }
    reunionUploadedTextDocuments.value = [
      ...reunionUploadedTextDocuments.value,
      { filename: file.name, content },
    ]
    appendTextToFormField('diary_notes', content)
    appendTextToFormField('memory_fragments', content)
    saveStateSnapshot()
  }
  reader.readAsText(file)
  target.value = ''
}

function handleIntimateMaterialFileChange(event: Event) {
  const target = event.target as HTMLInputElement | null
  const file = target?.files?.[0]
  if (!file) {
    return
  }

  intimateMaterialFileName.value = file.name
  const reader = new FileReader()
  reader.onload = () => {
    const content = String(reader.result || '').trim()
    if (!content) {
      return
    }
    intimateUploadedTextDocuments.value = [
      ...intimateUploadedTextDocuments.value,
      { filename: file.name, content },
    ]
    appendTextToFormField('text_materials', content)
    appendTextToFormField('memory_fragments', content)
    if (createType.value === 'intimate_companion') {
      if (inputMode.value === 'relationship_understanding' || inputMode.value === 'message_simulation') {
        appendTextToFormField('chat_history_summary', content)
      }
      if (inputMode.value === 'partner_maintenance') {
        appendTextToFormField('interaction_rules', content)
      }
      if (inputMode.value === 'past_relation_mirror') {
        appendTextToFormField('key_memories', content)
      }
    }
    saveStateSnapshot()
  }
  reader.readAsText(file)
  target.value = ''
}

function resolveGroupForTypeAndMode(type: CreateType, mode: string) {
  if (type === 'self_unified') {
    return 'self'
  }
  if (type === 'source_persona') {
    return 'source'
  }
  if (type === 'family_companion') {
    return 'relationship_family'
  }
  if (type === 'reunion_persona') {
    return 'relationship_family'
  }
  if (type === 'intimate_companion') {
    return 'relationship_intimate'
  }

  if (mode === 'colleague' || mode === 'boss') {
    return 'relationship_workplace'
  }
  if (mode === 'supervisor' || mode === 'senpai' || mode === 'professor_a' || mode === 'professor_b') {
    return 'relationship_academia'
  }
  if (
    mode === 'relationship_understanding' ||
    mode === 'message_simulation' ||
    mode === 'partner_maintenance' ||
    mode === 'past_relation_mirror'
  ) {
    return 'relationship_intimate'
  }
  if (mode === 'parents' || mode === 'reunion' || mode === 'mama' || mode === 'mother' || mode === 'other_family') {
    return 'relationship_family'
  }

  return 'relationship_workplace'
}

function getInputModeNote(type: CreateType, mode: string) {
  if (type === 'self_unified') {
    if (mode === 'manual_profile') return '适合先从你自己的想法开始。'
    if (mode === 'chat_history') return '适合把对话里的表达方式整理出来。'
    if (mode === 'documents') return '适合把已有材料补充进去。'
    if (mode === 'memory_notes') return '适合把记忆片段补进去。'
  }

  if (type === 'source_persona') {
    if (mode === 'documents') return '适合先从文档或 PDF 开始。'
    if (mode === 'chat_history') return '适合先从聊天记录开始。'
    if (mode === 'audio_video') return '适合从音频或视频开始。'
    if (mode === 'multi_source') return '适合把多个来源放在一起。'
  }

  if (type === 'relationship_persona') {
    if (mode === 'colleague') return '适合同事视角。'
    if (mode === 'boss') return '适合老板视角。'
    if (mode === 'supervisor') return '适合导师视角。'
    if (mode === 'senpai') return '适合师兄视角。'
    if (mode === 'professor_a' || mode === 'professor_b') return '适合老师视角。'
    if (mode === 'ex') return '适合前任视角。'
    if (mode === 'relationship_training') return '适合关系训练视角。'
    if (mode === 'ideal_partner') return '适合理想伴侣视角。'
    if (mode === 'crush') return '适合暧昧对象视角。'
    if (mode === 'parents') return '适合父母视角。'
    if (mode === 'partner') return '适合伴侣视角。'
    if (mode === 'first_love') return '适合初恋视角。'
    if (mode === 'self_mirror') return '适合自我镜像伴侣视角。'
    if (mode === 'relationship_interpreter') return '适合关系理解辅助视角。'
    if (mode === 'reunion') return '适合重逢人格视角。'
    if (mode === 'mama') return '适合妈妈视角。'
  }

  if (type === 'intimate_companion') {
    if (mode === 'relationship_understanding') return '适合先理解对方表达和关系状态。'
    if (mode === 'message_simulation') return '适合先预测对方回复，再看怎么发。'
    if (mode === 'partner_maintenance') return '适合伴侣关系维护与磨合。'
    if (mode === 'past_relation_mirror') return '适合回看过去关系和自我镜像。'
  }

  if (type === 'family_companion') {
    if (mode === 'mother') return '适合妈妈视角。'
    if (mode === 'parents') return '适合父母视角。'
    if (mode === 'other_family') return '适合其他家人视角。'
  }

  if (type === 'reunion_persona') {
    if (mode === 'chat_history') return '适合从聊天记录开始。'
    if (mode === 'documents') return '适合从文档或纪念材料开始。'
    if (mode === 'memory_notes') return '适合先整理回忆片段。'
    if (mode === 'photo_notes') return '适合先整理照片 / 截图说明。'
    if (mode === 'voice_notes') return '适合先整理口述回忆。'
  }

  return '适合继续完善。'
}

function getRelationshipLabel(mode: string) {
  return (
    inputModeLabels.relationship_persona[mode] ||
    inputModeLabels.intimate_companion[mode] ||
    inputModeLabels.family_companion[mode] ||
    inputModeLabels.reunion_persona[mode] ||
    '关系人格'
  )
}

function getFamilySubtypePreset(mode: string) {
  if (mode === 'parents') {
    return {
      relationshipType: '父母',
      personaName: '父母',
      speechStyle: '更稳、更完整，带家庭整体视角。',
      catchphrases: '先稳住\n我们一起想办法\n慢慢来',
      comfortStyle: '先稳住情绪，再给更完整的家庭建议。',
      celebrationStyle: '先一起高兴，再顺着把家里的安排和共识说完整。',
      sharedEvents: '家庭一起经历的重要时刻\n成长过程里的大事',
      importantAdvice: '先看现实条件\n先把家庭安排稳住',
      dailyHabits: '会提醒你注意整体安排\n会关心你的成长进度',
      emotionalTriggers: '家庭压力\n成长选择\n重要决定',
      relationBoundaries: '更偏家庭整体关心，不替你做决定。',
      chatHistorySummary: '把父母整体关心、提醒和建议先整理出来。',
      memoryFragments: '家庭共同记忆\n成长过程里的关键片段',
      textMaterials: '家庭说明\n家书材料',
      imageNotes: '家庭照片 / 截图说明',
      voiceNotes: '家庭语音提醒',
    }
  }

  if (mode === 'other_family') {
    return {
      relationshipType: '其他家人',
      personaName: '其他家人',
      speechStyle: '温和、自然、通用家庭陪伴感。',
      catchphrases: '慢慢说\n我在呢\n先别急',
      comfortStyle: '先接住情绪，再给自然的陪伴和提醒。',
      celebrationStyle: '先替你高兴，再顺着把好消息说完整。',
      sharedEvents: '一起经历过的小事\n家里常见的互动',
      importantAdvice: '保持联系\n照顾好自己',
      dailyHabits: '会问候你近况\n会留意你的状态',
      emotionalTriggers: '日常压力\n家庭琐事\n需要陪伴',
      relationBoundaries: '保持亲近感，也保留合适边界。',
      chatHistorySummary: '把其他家人的关心方式和日常互动先整理出来。',
      memoryFragments: '小事里的关心\n常见互动片段',
      textMaterials: '家庭便条\n补充说明',
      imageNotes: '图片 / 截图说明',
      voiceNotes: '语音说明',
    }
  }

  return {
    relationshipType: '妈妈',
    personaName: '妈妈',
    speechStyle: '温和、熟悉、会先接住情绪。',
    catchphrases: '先别急\n慢慢来\n我在呢',
    comfortStyle: '先接住情绪，再慢慢安慰，语气更熟悉。',
    celebrationStyle: '先替你高兴，再顺着把好消息说完整。',
    sharedEvents: '小时候一起吃饭\n你难过时被安慰',
    importantAdvice: '先照顾好自己\n遇事先稳住',
    dailyHabits: '会问你吃饭没\n会提醒你休息',
    emotionalTriggers: '考试压力\n工作烦心\n好消息分享',
    relationBoundaries: '不越界，不替你做决定，不伪造没发生过的事。',
    chatHistorySummary: '把你和家人之间的重要聊天、提醒和记忆先整理出来。',
    memoryFragments: '聊天记录片段\n共同回忆\n日常关心',
    textMaterials: '文本材料\n手记内容',
    imageNotes: '照片 / 截图说明',
    voiceNotes: '语音片段说明',
  }
}

function clearFormState() {
  for (const key of Object.keys(formState) as Array<keyof typeof formState>) {
    formState[key] = ''
  }
}

function resetFormForType(type: CreateType, displayName = '', mode = '') {
  clearFormState()
  familyMaterialFileName.value = ''
  reunionMaterialFileName.value = ''
  intimateMaterialFileName.value = ''
  familyUploadedTextDocuments.value = []
  reunionUploadedTextDocuments.value = []
  intimateUploadedTextDocuments.value = []

  if (type === 'self_unified') {
    formState.name = displayName || '自我主线'
    formState.work_system_summary = '把做事方式整理成可以继续使用的人格骨架。'
    formState.work_system_points = '先看目标\n再看路径\n再看边界'
    formState.reply_persona_summary = '把回复方式整理成更像自己的表达。'
    formState.reply_persona_points = '直接一点\n清楚一点\n保留边界'
    formState.thinking_dna_summary = '把判断路径和取舍逻辑整理出来。'
    formState.thinking_dna_points = '先问条件\n再看出路\n再算代价'
    formState.memory_evidence_summary = '把聊天片段、文字材料和生活痕迹整理进去。'
    formState.memory_evidence_points = '聊天记录\n文字片段\n文件材料'
    formState.reflection_rules_summary = '把容易失真和需要保留的边界先写清楚。'
    formState.reflection_rules_points = '不夸张\n不越界\n不替自己下定论'
  }

  if (type === 'source_persona') {
    formState.target_name = displayName || '资料人格'
    formState.material_type = '文档 / 聊天记录'
    formState.material_description = '基于已有资料提炼一个可对话人格。'
    formState.focus_points = '判断顺序\n表达习惯'
    formState.excluded_content = '隐私内容\n无关噪声'
  }

  if (type === 'relationship_persona') {
    formState.relationship_type = getRelationshipLabel(mode) || displayName || '关系人格'
    formState.persona_name = displayName || getRelationshipLabel(mode) || '关系人格'
    formState.speech_style = '说话直白、场景化。'
    formState.decision_logic = '先看现实条件，再给建议。'
    formState.purpose = '帮助理解这段关系。'
    formState.relation_boundaries = '不越界，不伪造确定事实。'
  }

  if (type === 'family_companion') {
    const preset = getFamilySubtypePreset(mode)
    formState.relationship_type = preset.relationshipType || getRelationshipLabel(mode) || displayName || '家人陪伴'
    formState.persona_name = displayName || preset.personaName || getRelationshipLabel(mode) || '家人陪伴'
    formState.speech_style = preset.speechStyle
    formState.catchphrases = preset.catchphrases
    formState.comfort_style = preset.comfortStyle
    formState.celebration_style = preset.celebrationStyle
    formState.shared_events = preset.sharedEvents
    formState.important_advice = preset.importantAdvice
    formState.daily_habits = preset.dailyHabits
    formState.emotional_triggers = preset.emotionalTriggers
    formState.relation_boundaries = preset.relationBoundaries
    formState.chat_history_summary = preset.chatHistorySummary
    formState.memory_fragments = preset.memoryFragments
    formState.text_materials = preset.textMaterials
    formState.image_notes = preset.imageNotes
    formState.voice_notes = preset.voiceNotes
  }

  if (type === 'reunion_persona') {
    formState.relationship_type = getRelationshipLabel(mode) || displayName || '重逢人格'
    formState.persona_name = displayName || getRelationshipLabel(mode) || '重逢人格'
    formState.speech_style = '克制、温和、保留记忆感。'
    formState.remembrance_style = '先慢慢回忆，再一点点靠近。'
    formState.comfort_style = '先稳住情绪，再带着记忆慢慢说。'
    formState.relation_boundaries = '不激进刺激，不越界替代现实。'
    formState.chat_history_summary = '把聊天记录、日记、信件和口述材料先整理一下。'
    formState.memory_fragments = '关键回忆片段\n重要往事\n共同经历'
    formState.diary_notes = '日记内容\n信件摘录'
    formState.letter_notes = '书信文本'
    formState.photo_notes = '照片说明 / 截图说明'
    formState.voice_notes = '口述回忆 / 语音说明'
    formState.shared_memories = '你们共同经历过的时刻\n反复出现的记忆'
    formState.retrieval_mode = '渐进式回忆'
    formState.priority_rules = '优先最近对话\n优先当前情绪相关记忆'
    formState.fallback_rules = '记忆不足时先稳住情绪\n不编造细节'
    formState.safety_boundaries = '不激进刺激\n不替现实关系下结论'
    formState.emotional_protection = '先接住情绪\n避免高压追问'
    formState.avoid_triggers = '不要把空白补成确定事实\n不要一次抛出过多强刺激回忆'
  }

  if (type === 'intimate_companion') {
    formState.relationship_type = getRelationshipLabel(mode) || displayName || '亲密关系'
    formState.persona_name = displayName || getRelationshipLabel(mode) || '亲密关系'
    formState.relationship_stage = getRelationshipLabel(mode) || '关系阶段待补充'
    formState.speech_style = '自然、贴近、带一点熟悉感。'
    formState.response_temperature = '先接住情绪，再顺着回应。'
    formState.catchphrases = '最近怎么样\n我在听'
    formState.decision_logic = '先看关系状态，再决定回应节奏。'
    formState.purpose = '帮助理解关系、模拟回应或整理复盘。'
    formState.relation_boundaries = '不越界，不替对方下结论。'
    formState.conversation_samples = '你今天过得怎么样？\n最近在忙什么？'
    formState.interaction_rules = '先回应情绪，再进入内容本身\n不要一下子逼问对方'
    formState.relationship_goals = '让沟通更顺畅\n让关系更稳定'
    formState.key_memories = '常聊的话题\n一起经历过的重要时刻'
  }
}

function buildEntryDefaults() {
  const createTypeValue = inferCreateTypeFromQuery()
  const rawDisplayName = readQueryValue('display_name') || readQueryValue('name')
  const displayName =
    createTypeValue === 'self_unified'
      ? getDefaultDisplayNameForType(createTypeValue)
      : rawDisplayName || getDefaultDisplayNameForType(createTypeValue)
  const createModeValue = readQueryValue('create_mode') as SelfCreateMode || 'standard'
  const schemaKeyFromQuery = readQueryValue('schema_key')
  const inputModeFromQuery = readQueryValue('input_mode')
  const sourceRepo = readQueryValue('source_repo') || getDefaultSourceRepoForType(createTypeValue)
  const inputModeValue = inputModeFromQuery || resolveInputMode(createTypeValue, sourceRepo, schemaKeyFromQuery)
  const group = readQueryValue('group') || resolveGroupForTypeAndMode(createTypeValue, inputModeValue)
  const schemaKeyValue =
    schemaKeyFromQuery || resolveSchemaKey(createTypeValue, sourceRepo, inputModeValue, displayName)

  return {
    createType: createTypeValue,
    group,
    sourceRepo,
    displayName,
    createMode: createModeValue,
    inputMode: inputModeValue,
    schemaKey: schemaKeyValue,
  }
}

function saveStateSnapshot() {
  saveWizardState({
    step: step.value,
    createType: createType.value,
    createMode: createMode.value,
    inputMode: inputMode.value,
    familySubtype: createType.value === 'family_companion' ? inputMode.value : '',
    selfInputModes: selfInputModes.value,
    selectedGroup: selectedGroup.value,
    selectedName: selectedName.value,
    selectedSourceRepo: selectedSourceRepo.value,
    selectedSchemaKey: selectedSchemaKey.value,
    familyUploadedTextDocuments: familyUploadedTextDocuments.value,
    reunionUploadedTextDocuments: reunionUploadedTextDocuments.value,
    intimateUploadedTextDocuments: intimateUploadedTextDocuments.value,
    formState: { ...formState },
  })
}

function loadStateSnapshot() {
  const snapshot = loadWizardState<{
    step?: number
    createType?: string
    createMode?: SelfCreateMode
    inputMode?: string
    familySubtype?: string
    selfInputModes?: string[]
    selectedGroup?: string
    selectedName?: string
    selectedSourceRepo?: string
    selectedSchemaKey?: string
    familyUploadedTextDocuments?: TextMaterialDocument[]
    reunionUploadedTextDocuments?: TextMaterialDocument[]
    intimateUploadedTextDocuments?: TextMaterialDocument[]
    formState?: Record<string, string>
  }>()

  if (!snapshot) {
    return false
  }

  if (snapshot.step) {
    step.value = Math.min(Math.max(snapshot.step, 1), 4)
  }

  if (snapshot.createType) {
    createType.value = normalizeCreateType(snapshot.createType)
  }

  if (snapshot.createMode) {
    createMode.value = snapshot.createMode
  }

  if (snapshot.inputMode) {
    inputMode.value = snapshot.inputMode
  }
  if (createType.value === 'family_companion' && snapshot.familySubtype) {
    inputMode.value = snapshot.familySubtype
  }

  if (Array.isArray(snapshot.selfInputModes) && snapshot.selfInputModes.length > 0) {
    selfInputModes.value = snapshot.selfInputModes
  }

  selectedGroup.value = snapshot.selectedGroup || selectedGroup.value
  selectedName.value =
    createType.value === 'self_unified'
      ? normalizeSelfUnifiedDisplayName(snapshot.selectedName || selectedName.value)
      : snapshot.selectedName || selectedName.value
  selectedSourceRepo.value = snapshot.selectedSourceRepo || selectedSourceRepo.value
  selectedSchemaKey.value = snapshot.selectedSchemaKey || selectedSchemaKey.value
  if (Array.isArray(snapshot.familyUploadedTextDocuments)) {
    familyUploadedTextDocuments.value = snapshot.familyUploadedTextDocuments
  }
  if (Array.isArray(snapshot.reunionUploadedTextDocuments)) {
    reunionUploadedTextDocuments.value = snapshot.reunionUploadedTextDocuments
  }
  if (Array.isArray(snapshot.intimateUploadedTextDocuments)) {
    intimateUploadedTextDocuments.value = snapshot.intimateUploadedTextDocuments
  }

  if (createType.value === 'relationship_persona') {
    const intimateModes = new Set(['relationship_understanding', 'message_simulation', 'partner_maintenance', 'past_relation_mirror'])
    const familyModes = new Set(['mother', 'parents', 'other_family'])
    const intimateSources = new Set(['relationship-training-skill+xinyi', 'crush-skill', 'partner-skill+npy-skill', 'ex-skill+first-love-skill+shuixian-skill'])
    const familySources = new Set(['MamaSkill', 'parents-skills', 'MamaSkill+parents-skills+darwin-skill', 'parents-skills+MamaSkill'])
    const reunionSources = new Set(['reunion-skill'])

    if (
      selectedGroup.value === 'relationship_intimate' ||
      intimateModes.has(inputMode.value) ||
      intimateSources.has(selectedSourceRepo.value)
    ) {
      createType.value = 'intimate_companion'
      selectedGroup.value = 'relationship_intimate'
      if (inputMode.value === 'ex' || inputMode.value === 'first_love' || inputMode.value === 'self_mirror') {
        inputMode.value = 'past_relation_mirror'
      } else if (inputMode.value === 'crush') {
        inputMode.value = 'message_simulation'
      } else if (inputMode.value === 'partner' || inputMode.value === 'ideal_partner') {
        inputMode.value = 'partner_maintenance'
      } else if (inputMode.value === 'relationship_training' || inputMode.value === 'relationship_interpreter') {
        inputMode.value = 'relationship_understanding'
      }
    } else if (reunionSources.has(selectedSourceRepo.value) || inputMode.value === 'reunion' || selectedSchemaKey.value?.startsWith('reunion_persona_')) {
      createType.value = 'reunion_persona'
      selectedGroup.value = 'relationship_family'
      inputMode.value = inputMode.value || 'chat_history'
      selectedSourceRepo.value = 'reunion-skill'
      selectedName.value = selectedName.value || '重逢人格'
    } else if (
      selectedGroup.value === 'relationship_family' ||
      familyModes.has(inputMode.value) ||
      familySources.has(selectedSourceRepo.value)
    ) {
      createType.value = 'family_companion'
      selectedGroup.value = 'relationship_family'
    }
  }

  if (createType.value === 'self_unified') {
    const allowedModes = new Set(['manual_profile', 'chat_history', 'documents', 'memory_notes'])
    if (!selfInputModes.value.length) {
      selfInputModes.value = ['manual_profile']
    }
    selfInputModes.value = selfInputModes.value.filter((mode) => allowedModes.has(mode))
    if (!selfInputModes.value.length) {
      selfInputModes.value = ['manual_profile']
    }
    if (!createMode.value) {
      createMode.value = 'standard'
    }
  }

  resetFormForType(createType.value, selectedName.value, inputMode.value)

  if (snapshot.formState) {
    Object.assign(formState, snapshot.formState)
  }

  if (createType.value === 'self_unified') {
    formState.name = normalizeSelfUnifiedDisplayName(formState.name)
  }

  return true
}

function applyQueryDefaults() {
  const defaults = buildEntryDefaults()

  createType.value = defaults.createType
  createMode.value = defaults.createMode
  selectedGroup.value = defaults.group
  selectedName.value = defaults.displayName
  selectedSourceRepo.value = defaults.sourceRepo
  selectedSchemaKey.value = defaults.schemaKey
  inputMode.value = defaults.inputMode
  selfInputModes.value = createType.value === 'self_unified' ? ['manual_profile'] : [defaults.inputMode || 'manual_profile']

  resetFormForType(createType.value, selectedName.value, inputMode.value)
}

function hasEntryQuery() {
  return Boolean(
    readQueryValue('create_type') ||
      readQueryValue('type') ||
      readQueryValue('group') ||
      readQueryValue('source_repo') ||
      readQueryValue('display_name') ||
      readQueryValue('name') ||
      readQueryValue('input_mode') ||
      readQueryValue('schema_key'),
  )
}

function initializeWizardState() {
  const reset = readQueryValue('reset') === '1'
  const hasEntry = hasEntryQuery()
  isBootstrapping.value = true

  if (reset) {
    clearWizardState()
  }

  if (reset || hasEntry) {
    step.value = 1
    applyQueryDefaults()
    saveStateSnapshot()
    isBootstrapping.value = false
    return
  }

  const restored = loadStateSnapshot()
  if (restored) {
    isBootstrapping.value = false
    return
  }

  step.value = 1
  createType.value = 'self_unified'
  createMode.value = 'standard'
  inputMode.value = 'manual_profile'
  selfInputModes.value = ['manual_profile']
  selectedGroup.value = getDefaultGroupForType(createType.value)
  selectedName.value = getDefaultDisplayNameForType(createType.value)
  selectedSourceRepo.value = getDefaultSourceRepoForType(createType.value)
  selectedSchemaKey.value = resolveSchemaKey(createType.value, selectedSourceRepo.value, inputMode.value, selectedName.value)
  resetFormForType(createType.value, selectedName.value, inputMode.value)
  saveStateSnapshot()
  isBootstrapping.value = false
}

function selectType(type: CreateType) {
  createType.value = type
  selectedGroup.value = getDefaultGroupForType(type)
  selectedSourceRepo.value = getDefaultSourceRepoForType(type)
  selectedName.value = getDefaultDisplayNameForType(type)
  if (type === 'self_unified') {
    createMode.value = 'standard'
    inputMode.value = 'manual_profile'
    selfInputModes.value = ['manual_profile']
  } else if (type === 'source_persona') {
    inputMode.value = 'documents'
  } else if (type === 'family_companion') {
    inputMode.value = 'mother'
  } else if (type === 'reunion_persona') {
    inputMode.value = 'chat_history'
  } else if (type === 'intimate_companion') {
    inputMode.value = 'relationship_understanding'
  } else {
    inputMode.value = 'colleague'
  }
  selectedSchemaKey.value = resolveSchemaKey(type, selectedSourceRepo.value, inputMode.value, selectedName.value)
  resetFormForType(type, selectedName.value, inputMode.value)
  step.value = type === 'self_unified' ? 1 : 2
}

function selectInputMode(mode: string) {
  inputMode.value = mode
  selectedGroup.value = resolveGroupForTypeAndMode(createType.value, mode)
  if (
    createType.value === 'relationship_persona' ||
    createType.value === 'family_companion' ||
    createType.value === 'reunion_persona' ||
    createType.value === 'intimate_companion'
  ) {
    if (createType.value === 'family_companion') {
      selectedSourceRepo.value = 'parents-skills+MamaSkill'
      selectedName.value = selectedName.value || getDefaultDisplayNameForType(createType.value)
    } else if (createType.value === 'reunion_persona') {
      selectedSourceRepo.value = 'reunion-skill'
      selectedName.value = selectedName.value || '重逢人格'
    } else {
      selectedSourceRepo.value = sourceRepoByInputMode[mode] || selectedSourceRepo.value
      selectedName.value = getRelationshipLabel(mode) || selectedName.value
    }
  } else if (createType.value === 'self_unified') {
    selfInputModes.value = Array.from(new Set([...(selfInputModes.value || []), mode]))
  }
  selectedSchemaKey.value = resolveSchemaKey(createType.value, selectedSourceRepo.value, mode, selectedName.value)
  resetFormForType(createType.value, selectedName.value, mode)
  step.value = createType.value === 'family_companion' || createType.value === 'reunion_persona' ? 2 : 3
}

function goStep(nextStep: number) {
  step.value = Math.min(Math.max(nextStep, 1), 4)
}

function buildFamilyRawMaterials() {
  return {
    chat_history_text: familyChatHistoryText.value,
    memory_notes_text: familyMemoryNotesText.value,
    text_materials_text: familyTextMaterialsText.value,
    uploaded_text_documents: familyUploadedTextDocuments.value,
    image_notes_text: familyImageNotesText.value,
    photo_notes_text: familyImageNotesText.value,
    voice_notes_text: familyVoiceNotesText.value,
  }
}

function buildReunionRawMaterials() {
  return {
    chat_history_text: formState.chat_history_summary,
    diary_text: formState.diary_notes,
    letter_text: formState.letter_notes,
    memory_notes_text: formState.memory_fragments,
    uploaded_text_documents: reunionUploadedTextDocuments.value,
    photo_notes_text: formState.photo_notes,
    voice_notes_text: formState.voice_notes,
  }
}

function buildIntimateRawMaterials() {
  return {
    chat_history_text: formState.chat_history_summary,
    memory_notes_text: formState.memory_fragments,
    text_materials_text: formState.text_materials,
    uploaded_text_documents: intimateUploadedTextDocuments.value,
    image_notes_text: formState.image_notes,
    voice_notes_text: formState.voice_notes,
    conflict_text: formState.memory_fragments,
    draft_message_text: formState.conversation_samples,
    recent_context_text: formState.chat_history_summary,
    reply_style_samples_text: formState.conversation_samples,
    relationship_status_text: formState.relationship_stage,
    interaction_patterns_text: formState.interaction_rules,
    history_text: formState.key_memories,
    expression_samples_text: formState.catchphrases,
  }
}

async function generateDraft() {
  loading.value = true
  error.value = ''

  try {
    const selfUnifiedPayload =
      createType.value === 'self_unified'
        ? {
            create_mode: createMode.value,
            input_modes: selfInputModes.value,
            self_persona_unified: {
              create_mode: createMode.value,
              input_modes: selfInputModes.value,
              work_system: {
                summary: formState.work_system_summary,
                points: formState.work_system_points.split(/\n+/).map((item) => item.trim()).filter(Boolean),
              },
              reply_persona: {
                summary: formState.reply_persona_summary,
                points: formState.reply_persona_points.split(/\n+/).map((item) => item.trim()).filter(Boolean),
              },
              thinking_dna: {
                summary: formState.thinking_dna_summary,
                points: formState.thinking_dna_points.split(/\n+/).map((item) => item.trim()).filter(Boolean),
              },
              memory_evidence: {
                summary: formState.memory_evidence_summary,
                points: formState.memory_evidence_points.split(/\n+/).map((item) => item.trim()).filter(Boolean),
              },
              reflection_rules: {
                summary: formState.reflection_rules_summary,
                points: formState.reflection_rules_points.split(/\n+/).map((item) => item.trim()).filter(Boolean),
              },
            },
          }
        : null

    const draft = await submitCreateDraft({
      create_type: createType.value,
      group: selectedGroup.value,
      source_repo: selectedSourceRepo.value,
      display_name: selectedName.value,
      create_mode: createType.value === 'self_unified' ? createMode.value : '',
      input_mode: inputMode.value,
      family_subtype: createType.value === 'family_companion' ? inputMode.value : '',
      input_modes: createType.value === 'self_unified' ? [...selfInputModes.value] : [inputMode.value],
      schema_key: selectedSchemaKey.value || resolveSchemaKey(createType.value, selectedSourceRepo.value, inputMode.value, selectedName.value),
      form_data:
        createType.value === 'self_unified'
          ? { ...formState, ...selfUnifiedPayload }
          : createType.value === 'family_companion'
            ? {
                ...formState,
                raw_materials: buildFamilyRawMaterials(),
              }
            : createType.value === 'reunion_persona'
              ? {
                  ...formState,
                  raw_materials: buildReunionRawMaterials(),
                }
              : createType.value === 'intimate_companion'
                ? {
                    ...formState,
                    raw_materials: buildIntimateRawMaterials(),
                  }
              : { ...formState },
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

watch([createType, inputMode, selectedGroup, selectedName, selectedSourceRepo, selectedSchemaKey], () => {
  if (!isBootstrapping.value) {
    saveStateSnapshot()
  }
})

watch(
  formState,
  () => {
    if (!isBootstrapping.value) {
      saveStateSnapshot()
    }
  },
  { deep: true },
)

onMounted(() => {
  initializeWizardState()
})

watch(
  () => route.query,
  () => {
    initializeWizardState()
  },
  { deep: true },
)
</script>

<template>
  <section class="page-hero page-hero--single wizard-hero">
    <div class="hero-copy">
      <p class="eyebrow">创建向导</p>
      <h1>开始创建</h1>
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
              <h3>{{ isSelfUnified ? '选择深度' : isFamilyCompanion ? (isReunionPersona ? '选择材料' : '选择子类型') : '选择创建类型' }}</h3>
            </div>
            <p class="section-note">
              {{ isSelfUnified ? '先选轻量、标准或深度模式。' : isFamilyCompanion ? (isReunionPersona ? '先选聊天记录、文本材料或记忆片段。' : '先选妈妈、父母或其他家人。') : '先确认你要从哪里开始创建。' }}
            </p>
          </div>

          <div v-if="isSelfUnified" class="wizard-card-grid wizard-card-grid--three">
            <button
              v-for="card in selfModeCards"
              :key="card.mode"
              type="button"
              class="wizard-option-card"
              :class="{ active: createMode === card.mode }"
              @click="selectSelfMode(card.mode)"
            >
              <h4>{{ card.title }}</h4>
              <p>{{ card.description }}</p>
            </button>
          </div>

          <div v-else-if="isFamilyCompanion" class="wizard-card-grid wizard-card-grid--three">
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

          <div v-else class="wizard-card-grid wizard-card-grid--three">
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
              <h3>{{ isSelfUnified ? '选择输入方式' : isFamilyCompanion ? (isReunionPersona ? '填写重逢资料' : '填写人物资料') : '选择创建方式' }}</h3>
            </div>
            <p class="section-note">
              {{ isSelfUnified ? '可以先选一个或多个输入方式。' : isFamilyCompanion ? (isReunionPersona ? '把记忆层和安全边界先写清楚。' : '把人物层和记忆层先写清楚。') : '不同类型会显示不同的方式选择。' }}
            </p>
          </div>

          <template v-if="isSelfUnified">
            <div class="wizard-card-grid wizard-card-grid--three">
              <button
                v-for="option in selfInputModeOptions"
                :key="option.key"
                type="button"
                class="wizard-option-card"
                :class="{ active: selfInputModes.includes(option.key) }"
                @click="toggleSelfInputMode(option.key)"
              >
                <h4>{{ option.label }}</h4>
                <p>{{ getInputModeNote(createType, option.key) }}</p>
              </button>
            </div>
          </template>

          <template v-else-if="isFamilyCompanion">
            <div class="wizard-form">
              <p class="eyebrow">人格层</p>
              <div class="form-grid">
                <label class="form-field">
                  <span>你怎么称呼他 / 她</span>
                  <input v-model="formState.persona_name" class="field-input" type="text" placeholder="例如：妈妈 / 父母 / 其他家人" />
                </label>
                <label class="form-field">
                  <span>说话风格</span>
                  <input v-model="formState.speech_style" class="field-input" type="text" placeholder="温和、直接、唠叨一点..." />
                </label>
              </div>

              <div class="form-grid">
                <label class="form-field">
                  <span>常见口头禅</span>
                  <textarea v-model="formState.catchphrases" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
                <label class="form-field">
                  <span>难过时会怎么说</span>
                  <textarea v-model="formState.comfort_style" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
              </div>

              <div class="form-grid">
                <label class="form-field">
                  <span>好消息时会怎么回应</span>
                  <textarea v-model="formState.celebration_style" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
                <label class="form-field">
                  <span>有哪些边界或禁忌话题</span>
                  <textarea v-model="formState.relation_boundaries" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
              </div>

              <p class="eyebrow">记忆层</p>
              <div class="form-grid">
                <label class="form-field">
                  <span>关键共同经历</span>
                  <textarea v-model="formState.shared_events" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
                <label class="form-field">
                  <span>最常提起的往事</span>
                  <textarea v-model="formState.daily_habits" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
              </div>

              <div class="form-grid">
                <label class="form-field">
                  <span>反复说过的话</span>
                  <textarea v-model="formState.important_advice" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
                <label class="form-field">
                  <span>她 / 他们最在意你的什么</span>
                  <textarea v-model="formState.emotional_triggers" class="field-input wizard-textarea" rows="4"></textarea>
                </label>
              </div>

              <p class="eyebrow">材料输入层</p>
              <div v-if="!isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>聊天记录粘贴框</span>
                  <textarea
                    v-model="familyChatHistoryText"
                    class="field-input wizard-textarea"
                    rows="5"
                    placeholder="把关键聊天记录、称呼方式、关心语气直接贴进来"
                  ></textarea>
                </label>
                <label class="form-field">
                  <span>回忆片段 / 记忆笔记</span>
                  <textarea
                    v-model="familyMemoryNotesText"
                    class="field-input wizard-textarea"
                    rows="5"
                    placeholder="把最像家人的片段、提醒、安慰话整理进来"
                  ></textarea>
                </label>
              </div>

              <div v-if="!isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>文本材料补充</span>
                  <textarea
                    v-model="familyTextMaterialsText"
                    class="field-input wizard-textarea"
                    rows="5"
                    placeholder="可直接粘贴文字材料、家书、聊天摘录或家庭说明"
                  ></textarea>
                </label>
                <label class="form-field">
                  <span>上传 txt / md / csv</span>
                  <input
                    class="field-input"
                    type="file"
                    accept=".txt,.md,.csv,text/plain,text/markdown,text/csv"
                    @change="handleFamilyMaterialFileChange"
                  />
                  <small class="field-hint">
                    {{
                      familyUploadedTextDocuments.length
                        ? `${familyUploadedTextDocuments.length} 个文件：${familyUploadedTextDocuments.map((item) => item.filename).join(' / ')}`
                        : (familyMaterialFileName || '上传后会自动读取文本内容并补进记忆库')
                    }}
                  </small>
                </label>
              </div>

              <div v-if="!isReunionPersona && familyUploadedTextDocuments.length" class="summary-panel summary-panel--compact">
                <p class="eyebrow">已上传文件</p>
                <h3>文件会被一起提炼进记忆库</h3>
                <ul class="summary-panel__list">
                  <li v-for="(item, index) in familyUploadedTextDocuments" :key="`${item.filename}-${index}`">
                    <span>
                      {{ item.filename }}
                      <small class="inline-meta">{{ Math.max(item.content.length, 1) }} 字</small>
                    </span>
                    <strong class="inline-actions">
                      <button class="ghost-button ghost-button--small" type="button" @click="removeFamilyUploadedTextDocument(index)">
                        删除
                      </button>
                    </strong>
                  </li>
                </ul>
              </div>

              <div v-if="!isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>图片说明</span>
                  <textarea
                    v-model="familyImageNotesText"
                    class="field-input wizard-textarea"
                    rows="5"
                    placeholder="先用文字记录图片或截图里的关键信息"
                  ></textarea>
                </label>
                <label class="form-field">
                  <span>语音说明</span>
                  <textarea
                    v-model="familyVoiceNotesText"
                    class="field-input wizard-textarea"
                    rows="5"
                    placeholder="先用文字记录语音里的关键信息"
                  ></textarea>
                </label>
              </div>

              <div v-if="isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>回忆方式</span>
                  <textarea v-model="formState.remembrance_style" class="field-input wizard-textarea" rows="4" placeholder="先慢慢回忆，再一点点靠近"></textarea>
                </label>
                <label class="form-field">
                  <span>聊天记录摘要</span>
                  <textarea v-model="formState.chat_history_summary" class="field-input wizard-textarea" rows="4" placeholder="把关键聊天记录、信件或日记先整理一下"></textarea>
                </label>
              </div>

              <p v-if="isReunionPersona" class="eyebrow">回忆层</p>
              <div v-if="isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>日记 / 信件</span>
                  <textarea v-model="formState.diary_notes" class="field-input wizard-textarea" rows="4" placeholder="可以直接粘贴日记或信件摘录"></textarea>
                </label>
                <label class="form-field">
                  <span>书信文本</span>
                  <textarea v-model="formState.letter_notes" class="field-input wizard-textarea" rows="4" placeholder="可以直接粘贴信件摘录"></textarea>
                </label>
              </div>

              <p v-if="isReunionPersona" class="eyebrow">材料输入层</p>
              <div v-if="isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>上传 txt / md / csv</span>
                  <input class="field-input" type="file" accept=".txt,.md,.csv,text/plain,text/markdown,text/csv" @change="handleReunionMaterialFileChange" />
                  <small class="field-hint">
                    {{
                      reunionUploadedTextDocuments.length
                        ? reunionUploadedTextDocuments.map((item) => item.filename).join(' / ')
                        : (reunionMaterialFileName || '可把文本材料追加到日记 / 信件里')
                    }}
                  </small>
                </label>
                <label class="form-field">
                  <span>书信文本</span>
                  <textarea v-model="formState.letter_notes" class="field-input wizard-textarea" rows="4" placeholder="可以直接粘贴信件摘录"></textarea>
                </label>
              </div>

              <div v-if="isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>记忆片段</span>
                  <textarea v-model="formState.memory_fragments" class="field-input wizard-textarea" rows="4" placeholder="一句一句整理出最有回忆感的片段"></textarea>
                </label>
                <label class="form-field">
                  <span>语音备注</span>
                  <textarea v-model="formState.voice_notes" class="field-input wizard-textarea" rows="4" placeholder="先用文字记录语音里的关键信息"></textarea>
                </label>
              </div>

              <div v-if="isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>照片 / 截图备注</span>
                  <textarea v-model="formState.photo_notes" class="field-input wizard-textarea" rows="4" placeholder="照片说明、截图说明、口述回忆"></textarea>
                </label>
                <label class="form-field">
                  <span>安全边界</span>
                  <textarea v-model="formState.safety_boundaries" class="field-input wizard-textarea" rows="4" placeholder="不激进刺激，不替现实关系下结论"></textarea>
                </label>
              </div>
            </div>
          </template>

          <div v-else class="wizard-card-grid">
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
              <h3>{{ isFamilyCompanion ? (isReunionPersona ? '确认重逢人格与记忆层' : '确认人物层与记忆层') : '填写信息' }}</h3>
            </div>
            <p class="section-note">{{ isFamilyCompanion ? (isReunionPersona ? '先看一眼记忆与护栏，再继续生成。' : '先看一眼，再继续生成。') : '先把关键变量写清楚，后面才更容易继续完善。' }}</p>
          </div>

          <div v-if="createType === 'self_unified'" class="wizard-form">
            <div class="form-grid">
              <label class="form-field">
                <span>名称</span>
                <input v-model="formState.name" class="field-input" type="text" placeholder="例如：更完整的我" />
              </label>
              <label class="form-field">
                <span>创建深度</span>
                <input :value="selfModeLabels[createMode]" class="field-input" type="text" readonly />
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>做事方式摘要</span>
                <textarea
                  v-model="formState.work_system_summary"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="先写你做事时最稳定的样子"
                ></textarea>
              </label>
              <label class="form-field">
                <span>做事方式要点</span>
                <textarea
                  v-model="formState.work_system_points"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="每行一条：先看目标 / 再看路径 / 再看边界"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>回复方式</span>
                <textarea
                  v-model="formState.reply_persona_summary"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="你希望这个人格怎么开口说话"
                ></textarea>
              </label>
              <label class="form-field">
                <span>回复方式要点</span>
                <textarea
                  v-model="formState.reply_persona_points"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="每行一条：直接一点 / 清楚一点 / 保留边界"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>思考方式</span>
                <textarea
                  v-model="formState.thinking_dna_summary"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="你做判断时最看重什么"
                ></textarea>
              </label>
              <label class="form-field">
                <span>思考方式要点</span>
                <textarea
                  v-model="formState.thinking_dna_points"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="每行一条：先问条件 / 再看出路 / 再算代价"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>生活痕迹</span>
                <textarea
                  v-model="formState.memory_evidence_summary"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="可写聊天记录、文本片段或数字痕迹"
                ></textarea>
              </label>
              <label class="form-field">
                <span>生活痕迹要点</span>
                <textarea
                  v-model="formState.memory_evidence_points"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="每行一条：聊天片段 / 文字材料 / 文件内容"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>上传 txt / md / csv</span>
                <input class="field-input" type="file" accept=".txt,.md,.csv,text/plain,text/markdown,text/csv" @change="handleSelfMemoryFileChange" />
                <small class="field-hint">{{ memoryEvidenceFileName || '可把文件内容追加到生活痕迹里' }}</small>
              </label>
              <label class="form-field">
                <span>反思规则</span>
                <textarea
                  v-model="formState.reflection_rules_summary"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="你希望这个人格保留什么边界"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>反思规则要点</span>
                <textarea
                  v-model="formState.reflection_rules_points"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="每行一条：不夸张 / 不越界 / 不替自己下定论"
                ></textarea>
              </label>
              <div class="summary-panel summary-panel--compact">
                <p class="eyebrow">输入方式</p>
                <h3>可多选</h3>
                <p class="state-copy">你可以同时保留手动填写、聊天记录、文本材料和记忆片段。</p>
                <ul class="summary-panel__list">
                  <li v-for="option in selfInputModeOptions" :key="option.key">
                    <span>{{ option.label }}</span>
                    <strong>{{ selfInputModes.includes(option.key) ? '已选择' : '未选择' }}</strong>
                  </li>
                </ul>
              </div>
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

          <div v-else-if="createType === 'family_companion' || createType === 'reunion_persona'" class="wizard-review wizard-review--family">
            <div class="summary-panel">
              <p class="eyebrow">{{ createType === 'reunion_persona' ? '重逢人格层' : '人物层' }}</p>
              <h3>{{ formState.persona_name || '未填写称呼' }}</h3>
              <ul class="summary-panel__list">
                <li><span>关系类型</span><strong>{{ getRelationshipLabel(inputMode) }}</strong></li>
                <li><span>说话风格</span><strong>{{ formState.speech_style || '未填写' }}</strong></li>
                <li><span>{{ createType === 'reunion_persona' ? '回忆方式' : '口头禅' }}</span><strong>{{ createType === 'reunion_persona' ? (formState.remembrance_style || '未填写') : (formState.catchphrases || '未填写') }}</strong></li>
              </ul>
            </div>

            <div class="summary-panel">
              <p class="eyebrow">记忆层</p>
              <h3>{{ createType === 'reunion_persona' ? '重逢记忆' : '共同记忆' }}</h3>
              <ul class="summary-panel__list">
                <li><span>{{ createType === 'reunion_persona' ? '聊天摘要' : '关键经历' }}</span><strong>{{ createType === 'reunion_persona' ? (formState.chat_history_summary || '未填写') : (formState.shared_events || '未填写') }}</strong></li>
                <li><span>{{ createType === 'reunion_persona' ? '检索策略' : '常见安慰' }}</span><strong>{{ createType === 'reunion_persona' ? (formState.priority_rules || '未填写') : (formState.comfort_style || '未填写') }}</strong></li>
                <li><span>{{ createType === 'reunion_persona' ? '安全护栏' : '重要建议' }}</span><strong>{{ createType === 'reunion_persona' ? (formState.safety_boundaries || '未填写') : (formState.important_advice || '未填写') }}</strong></li>
              </ul>
            </div>

            <div class="summary-panel">
              <p class="eyebrow">材料输入层</p>
              <h3>{{ createType === 'reunion_persona' ? '重逢材料' : '家人材料' }}</h3>
              <ul class="summary-panel__list">
                <li><span>聊天记录</span><strong>{{ createType === 'reunion_persona' ? (formState.chat_history_summary || '未填写') : (familyChatHistoryText || '未填写') }}</strong></li>
                <li><span>{{ createType === 'reunion_persona' ? '日记 / 信件' : '记忆片段' }}</span><strong>{{ createType === 'reunion_persona' ? (formState.diary_notes || formState.letter_notes || '未填写') : (familyMemoryNotesText || '未填写') }}</strong></li>
                <li><span>{{ createType === 'reunion_persona' ? '口述回忆' : '文本材料' }}</span><strong>{{ createType === 'reunion_persona' ? (formState.voice_notes || '未填写') : (familyTextMaterialsText || '未填写') }}</strong></li>
                <li><span>上传文件</span><strong>{{ createType === 'reunion_persona' ? (reunionUploadedTextDocuments.length ? reunionUploadedTextDocuments.map((item) => item.filename).join(' / ') : (reunionMaterialFileName || '未上传')) : (familyUploadedTextDocuments.length ? familyUploadedTextDocuments.map((item) => item.filename).join(' / ') : (familyMaterialFileName || '未上传')) }}</strong></li>
              </ul>
            </div>
          </div>

          <div v-else-if="createType === 'intimate_companion'" class="wizard-form">
            <div class="form-grid">
              <label class="form-field">
                <span>关系类型</span>
                <input v-model="formState.relationship_type" class="field-input" type="text" placeholder="关系理解 / 消息模拟 / 关系维护 / 过去关系" />
              </label>
              <label class="form-field">
                <span>对方名称 / 称呼</span>
                <input v-model="formState.persona_name" class="field-input" type="text" placeholder="例如：小林 / 阿泽 / 你喜欢的人" />
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>关系阶段</span>
                <input v-model="formState.relationship_stage" class="field-input" type="text" placeholder="例如：暧昧期 / 关系中 / 磨合中" />
              </label>
              <label class="form-field">
                <span>说话风格</span>
                <textarea v-model="formState.speech_style" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>回复温度</span>
                <textarea v-model="formState.response_temperature" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>常见口头禅</span>
                <textarea v-model="formState.catchphrases" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>对话样本</span>
                <textarea v-model="formState.conversation_samples" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>互动规则</span>
                <textarea v-model="formState.interaction_rules" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>关系目标</span>
                <textarea v-model="formState.relationship_goals" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
              <label class="form-field">
                <span>关键记忆</span>
                <textarea v-model="formState.key_memories" class="field-input wizard-textarea" rows="4"></textarea>
              </label>
            </div>

            <p class="eyebrow">材料输入层</p>
            <div class="form-grid">
              <label class="form-field">
                <span>聊天记录</span>
                <textarea
                  v-model="formState.chat_history_summary"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="粘贴最近聊天记录、冲突片段或对方样本"
                ></textarea>
              </label>
              <label class="form-field">
                <span>消息样本 / 回忆片段</span>
                <textarea
                  v-model="formState.memory_fragments"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="粘贴你准备发的话、对方回复样本或关系记忆"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>文本材料</span>
                <textarea
                  v-model="formState.text_materials"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="可直接粘贴日记、信件摘录、关系说明"
                ></textarea>
              </label>
              <label class="form-field">
                <span>上传 txt / md / csv</span>
                <input
                  class="field-input"
                  type="file"
                  accept=".txt,.md,.csv,text/plain,text/markdown,text/csv"
                  @change="handleIntimateMaterialFileChange"
                />
                <small class="field-hint">
                  {{
                    intimateUploadedTextDocuments.length
                      ? intimateUploadedTextDocuments.map((item) => item.filename).join(' / ')
                      : (intimateMaterialFileName || '可把文本材料追加到聊天记录和记忆片段里')
                  }}
                </small>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>图片 / 截图备注</span>
                <textarea
                  v-model="formState.image_notes"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="先用文字记录图片或截图里的关键信息"
                ></textarea>
              </label>
              <label class="form-field">
                <span>语音备注</span>
                <textarea
                  v-model="formState.voice_notes"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="先用文字记录语音里的关键信息"
                ></textarea>
              </label>
            </div>

            <div class="summary-panel summary-panel--compact">
              <p class="eyebrow">材料输入摘要</p>
              <h3>已支持文本材料输入</h3>
              <ul class="summary-panel__list">
                <li>
                  <span>聊天记录</span>
                  <strong>{{ formState.chat_history_summary || '未填写' }}</strong>
                </li>
                <li>
                  <span>消息样本 / 回忆片段</span>
                  <strong>{{ formState.memory_fragments || '未填写' }}</strong>
                </li>
                <li>
                  <span>文本材料</span>
                  <strong>{{ formState.text_materials || '未填写' }}</strong>
                </li>
                <li>
                  <span>上传文件</span>
                  <strong>
                    {{
                      intimateUploadedTextDocuments.length
                        ? intimateUploadedTextDocuments.map((item) => item.filename).join(' / ')
                        : (intimateMaterialFileName || '未上传')
                    }}
                  </strong>
                </li>
              </ul>
            </div>

            <label class="form-field">
              <span>边界或禁忌话题</span>
              <textarea v-model="formState.relation_boundaries" class="field-input wizard-textarea" rows="4"></textarea>
            </label>
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
              <h3>{{ isSelfUnified ? '生成结果' : isFamilyCompanion ? '生成结果' : '确认并生成结果' }}</h3>
            </div>
            <p class="section-note">{{ isSelfUnified ? '先看结果，再保存。' : isFamilyCompanion ? '先看结果，再保存。' : '先看结果，再生成。' }}</p>
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
              <p class="eyebrow">表单内容</p>
              <template v-if="createType === 'self_unified'">
                <h3>{{ formState.name || '未填写名称' }}</h3>
                <ul class="summary-panel__list">
                  <li><span>做事方式</span><strong>{{ formState.work_system_summary || '未填写' }}</strong></li>
                  <li><span>回复方式</span><strong>{{ formState.reply_persona_summary || '未填写' }}</strong></li>
                  <li><span>思考方式</span><strong>{{ formState.thinking_dna_summary || '未填写' }}</strong></li>
                  <li><span>生活痕迹</span><strong>{{ formState.memory_evidence_summary || '未填写' }}</strong></li>
                  <li><span>反思规则</span><strong>{{ formState.reflection_rules_summary || '未填写' }}</strong></li>
                </ul>
              </template>
              <template v-else-if="createType === 'source_persona'">
                <h3>{{ formState.target_name || '未填写目标名称' }}</h3>
                <p class="state-copy">{{ formState.material_description || '还没有描述材料。' }}</p>
              </template>
              <template v-else-if="createType === 'family_companion'">
                <h3>{{ formState.persona_name || '未填写称呼' }}</h3>
                <p class="state-copy">{{ formState.comfort_style || '还没有填写安慰方式。' }}</p>
              </template>
              <template v-else-if="createType === 'reunion_persona'">
                <h3>{{ formState.persona_name || '未填写称呼' }}</h3>
                <p class="state-copy">{{ formState.remembrance_style || '还没有填写回忆方式。' }}</p>
              </template>
              <template v-else-if="createType === 'intimate_companion'">
                <h3>{{ formState.persona_name || '未填写对象名称' }}</h3>
                <p class="state-copy">{{ formState.relationship_stage || '还没有填写关系阶段。' }}</p>
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

    </div>
  </section>
</template>

<style scoped>
.inline-meta {
  display: block;
  margin-top: 0.18rem;
  color: var(--muted);
  font-size: 0.74rem;
}

.inline-actions {
  display: inline-flex;
  justify-content: flex-end;
}

.ghost-button {
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  border-radius: 999px;
  padding: 0.62rem 1rem;
  cursor: pointer;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    background 0.18s ease;
}

.ghost-button:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(255, 159, 138, 0.4);
  background: rgba(255, 255, 255, 0.92);
}

.ghost-button--small {
  padding: 0.42rem 0.78rem;
  font-size: 0.84rem;
}
</style>
