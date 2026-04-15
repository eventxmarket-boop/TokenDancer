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

type CreateType = 'self_persona' | 'source_persona' | 'relationship_persona' | 'family_companion' | 'intimate_companion'

const router = useRouter()
const route = useRoute()

const step = ref(1)
const loading = ref(false)
const error = ref('')
const createType = ref<CreateType>('self_persona')
const inputMode = ref('')
const selectedGroup = ref('')
const selectedName = ref('')
const selectedSourceRepo = ref('')
const selectedSchemaKey = ref('')
const isBootstrapping = ref(false)

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
  conversation_samples: '',
  interaction_rules: '',
  relationship_goals: '',
  key_memories: '',
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
  {
    type: 'intimate_companion' as const,
    title: '亲密关系',
    description: '从关系理解、消息模拟、关系维护或过去关系开始创建。',
    hint: '从亲密关系开始',
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
}

const inputModeBySourceRepo: Record<string, string> = {
  'self-skill': 'manual_profile',
  'nuwa-skill': 'documents',
  'forge-skill': 'chat_history',
  'digital-life': 'documents',
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
  'self-skill': 'self_persona',
  'nuwa-skill': 'self_mindset_distill',
  'forge-skill': 'self_deep_self_persona',
  'digital-life': 'self_digital_trace_persona',
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
  'digital-twin-skill': 'digital_twin_high_fidelity',
  'immortal-skill': 'digital_twin_immortal',
  'anti-distill': 'protection_anti_distill',
}

const isFamilyCompanion = computed(() => createType.value === 'family_companion')

const stepLabels = computed(() =>
  isFamilyCompanion.value
    ? ['选择关系类型', '填写信息', '确认结果', '生成结果']
    : ['选择类型', '选择方式', '填写信息', '生成结果'],
)

const currentInputs = computed(() => Object.entries(inputModeLabels[createType.value] || {}))

const currentTypeLabel = computed(() => {
  if (createType.value === 'self_persona') {
    return '自我人格'
  }
  if (createType.value === 'source_persona') {
    return '从资料创建'
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
  return inputModeLabels[createType.value]?.[inputMode.value] || inputMode.value || '未选择'
})

function readQueryValue(key: string) {
  const value = route.query[key]
  if (Array.isArray(value)) {
    return String(value[0] || '').trim()
  }
  return String(value || '').trim()
}

function inferCreateTypeFromQuery() {
  const explicit = readQueryValue('create_type') || readQueryValue('type')
  if (
    explicit === 'self_persona' ||
    explicit === 'source_persona' ||
    explicit === 'family_companion' ||
    explicit === 'intimate_companion'
  ) {
    return explicit as CreateType
  }

  if (explicit === 'relationship_persona') {
    const relationGroup = readQueryValue('group')
    if (relationGroup === 'relationship_family') {
      return 'family_companion'
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
    return 'family_companion'
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

  return 'self_persona'
}

function resolveInputMode(createTypeValue: CreateType, sourceRepo: string, schemaKey: string) {
  if (schemaKey && schemaKey in inputModeLabels[createTypeValue]) {
    return schemaKey
  }

  if (sourceRepo && inputModeBySourceRepo[sourceRepo]) {
    return inputModeBySourceRepo[sourceRepo]
  }

  if (createTypeValue === 'self_persona') {
    return 'manual_profile'
  }

  if (createTypeValue === 'source_persona') {
    return 'documents'
  }
  if (createTypeValue === 'family_companion') {
    return 'mother'
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
  if (type === 'self_persona') {
    return 'self'
  }
  if (type === 'source_persona') {
    return 'source'
  }
  if (type === 'family_companion') {
    return 'relationship_family'
  }
  if (type === 'intimate_companion') {
    return 'relationship_intimate'
  }
  return 'relationship_workplace'
}

function getDefaultSourceRepoForType(type: CreateType) {
  if (type === 'self_persona') {
    return 'self-skill'
  }
  if (type === 'source_persona') {
    return 'anyone-to-skill'
  }
  if (type === 'family_companion') {
    return 'MamaSkill+parents-skills+darwin-skill'
  }
  if (type === 'intimate_companion') {
    return 'relationship-training-skill+xinyi'
  }
  return 'colleague-skill'
}

function getDefaultDisplayNameForType(type: CreateType) {
  if (type === 'self_persona') {
    return '我的自我人格'
  }
  if (type === 'source_persona') {
    return '资料人格'
  }
  if (type === 'family_companion') {
    return '家人陪伴'
  }
  if (type === 'intimate_companion') {
    return '亲密关系'
  }
  return '关系人格'
}

function resolveGroupForTypeAndMode(type: CreateType, mode: string) {
  if (type === 'self_persona') {
    return 'self'
  }
  if (type === 'source_persona') {
    return 'source'
  }
  if (type === 'family_companion') {
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

  return '适合继续完善。'
}

function getRelationshipLabel(mode: string) {
  return (
    inputModeLabels.relationship_persona[mode] ||
    inputModeLabels.intimate_companion[mode] ||
    inputModeLabels.family_companion[mode] ||
    '关系人格'
  )
}

function clearFormState() {
  for (const key of Object.keys(formState) as Array<keyof typeof formState>) {
    formState[key] = ''
  }
}

function resetFormForType(type: CreateType, displayName = '', mode = '') {
  clearFormState()

  if (type === 'self_persona') {
    formState.name = displayName || '我的自我人格'
    formState.intro = '把我自己的做事方式整理成可以继续聊天的人格。'
    formState.values = '更看重结果、边界和可执行性。'
    formState.decision_priority = '先看目标，再看路径。'
    formState.expression_style = '直接、清楚、略带解释。'
    formState.boundaries = '保留私密内容，不越过边界。'
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
    formState.relationship_type = getRelationshipLabel(mode) || displayName || '家人陪伴'
    formState.persona_name = displayName || getRelationshipLabel(mode) || '家人陪伴'
    formState.speech_style = '温和、熟悉、带一点家里的感觉。'
    formState.catchphrases = '先别急\n慢慢来\n我在呢'
    formState.comfort_style = '先接住情绪，再慢慢安慰。'
    formState.celebration_style = '先替你高兴，再顺着把好消息讲完。'
    formState.shared_events = '小时候一起吃饭\n你难过时被安慰'
    formState.important_advice = '先照顾好自己\n遇事先稳住'
    formState.daily_habits = '会问你吃饭没\n会提醒你休息'
    formState.emotional_triggers = '考试压力\n工作烦心\n好消息分享'
    formState.relation_boundaries = '不越界，不替你做决定，不伪造没发生过的事。'
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
  const displayName = readQueryValue('display_name') || readQueryValue('name') || getDefaultDisplayNameForType(createTypeValue)
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
    inputMode: inputModeValue,
    schemaKey: schemaKeyValue,
  }
}

function saveStateSnapshot() {
  saveWizardState({
    step: step.value,
    createType: createType.value,
    inputMode: inputMode.value,
    selectedGroup: selectedGroup.value,
    selectedName: selectedName.value,
    selectedSourceRepo: selectedSourceRepo.value,
    selectedSchemaKey: selectedSchemaKey.value,
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
    selectedSourceRepo?: string
    selectedSchemaKey?: string
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
  selectedSourceRepo.value = snapshot.selectedSourceRepo || selectedSourceRepo.value
  selectedSchemaKey.value = snapshot.selectedSchemaKey || selectedSchemaKey.value

  if (createType.value === 'relationship_persona') {
    const intimateModes = new Set(['relationship_understanding', 'message_simulation', 'partner_maintenance', 'past_relation_mirror'])
    const familyModes = new Set(['mother', 'parents', 'other_family'])
    const intimateSources = new Set(['relationship-training-skill+xinyi', 'crush-skill', 'partner-skill+npy-skill', 'ex-skill+first-love-skill+shuixian-skill'])
    const familySources = new Set(['MamaSkill', 'parents-skills', 'MamaSkill+parents-skills+darwin-skill', 'reunion-skill'])

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
    } else if (
      selectedGroup.value === 'relationship_family' ||
      familyModes.has(inputMode.value) ||
      familySources.has(selectedSourceRepo.value)
    ) {
      createType.value = 'family_companion'
      selectedGroup.value = 'relationship_family'
    }
  }

  resetFormForType(createType.value, selectedName.value, inputMode.value)

  if (snapshot.formState) {
    Object.assign(formState, snapshot.formState)
  }

  return true
}

function applyQueryDefaults() {
  const defaults = buildEntryDefaults()

  createType.value = defaults.createType
  selectedGroup.value = defaults.group
  selectedName.value = defaults.displayName
  selectedSourceRepo.value = defaults.sourceRepo
  selectedSchemaKey.value = defaults.schemaKey
  inputMode.value = defaults.inputMode

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
  createType.value = 'self_persona'
  inputMode.value = 'manual_profile'
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
  if (type === 'self_persona') {
    inputMode.value = 'manual_profile'
  } else if (type === 'source_persona') {
    inputMode.value = 'documents'
  } else if (type === 'family_companion') {
    inputMode.value = 'mother'
  } else if (type === 'intimate_companion') {
    inputMode.value = 'relationship_understanding'
  } else {
    inputMode.value = 'colleague'
  }
  selectedSchemaKey.value = resolveSchemaKey(type, selectedSourceRepo.value, inputMode.value, selectedName.value)
  resetFormForType(type, selectedName.value, inputMode.value)
  step.value = 2
}

function selectInputMode(mode: string) {
  inputMode.value = mode
  selectedGroup.value = resolveGroupForTypeAndMode(createType.value, mode)
  if (createType.value === 'relationship_persona' || createType.value === 'family_companion' || createType.value === 'intimate_companion') {
    selectedSourceRepo.value = sourceRepoByInputMode[mode] || selectedSourceRepo.value
    selectedName.value = getRelationshipLabel(mode) || selectedName.value
  }
  selectedSchemaKey.value = resolveSchemaKey(createType.value, selectedSourceRepo.value, mode, selectedName.value)
  resetFormForType(createType.value, selectedName.value, mode)
  step.value = createType.value === 'family_companion' ? 2 : 3
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
      group: selectedGroup.value,
      source_repo: selectedSourceRepo.value,
      display_name: selectedName.value,
      input_mode: inputMode.value,
      schema_key: selectedSchemaKey.value || resolveSchemaKey(createType.value, selectedSourceRepo.value, inputMode.value, selectedName.value),
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
              <h3>{{ isFamilyCompanion ? '选择关系类型' : '选择创建类型' }}</h3>
            </div>
            <p class="section-note">{{ isFamilyCompanion ? '先选妈妈、父母或其他家人。' : '先确认你要从哪里开始创建。' }}</p>
          </div>

          <div v-if="isFamilyCompanion" class="wizard-card-grid wizard-card-grid--three">
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
              <h3>{{ isFamilyCompanion ? '填写人物资料' : '选择创建方式' }}</h3>
            </div>
            <p class="section-note">{{ isFamilyCompanion ? '把人物层和记忆层先写清楚。' : '不同类型会显示不同的方式选择。' }}</p>
          </div>

          <template v-if="isFamilyCompanion">
            <div class="wizard-form">
              <div class="form-grid">
                <label class="form-field">
                  <span>你怎么称呼他 / 她</span>
                  <input v-model="formState.persona_name" class="field-input" type="text" placeholder="例如：妈妈 / 爸爸" />
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
              <h3>{{ isFamilyCompanion ? '确认人物层与记忆层' : '填写信息' }}</h3>
            </div>
            <p class="section-note">{{ isFamilyCompanion ? '先看一眼，再继续生成。' : '先把关键变量写清楚，后面才更容易继续完善。' }}</p>
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

          <div v-else-if="createType === 'family_companion'" class="wizard-review wizard-review--family">
            <div class="summary-panel">
              <p class="eyebrow">人物层</p>
              <h3>{{ formState.persona_name || '未填写称呼' }}</h3>
              <ul class="summary-panel__list">
                <li><span>关系类型</span><strong>{{ getRelationshipLabel(inputMode) }}</strong></li>
                <li><span>说话风格</span><strong>{{ formState.speech_style || '未填写' }}</strong></li>
                <li><span>口头禅</span><strong>{{ formState.catchphrases || '未填写' }}</strong></li>
              </ul>
            </div>

            <div class="summary-panel">
              <p class="eyebrow">记忆层</p>
              <h3>共同记忆</h3>
              <ul class="summary-panel__list">
                <li><span>关键经历</span><strong>{{ formState.shared_events || '未填写' }}</strong></li>
                <li><span>常见安慰</span><strong>{{ formState.comfort_style || '未填写' }}</strong></li>
                <li><span>重要建议</span><strong>{{ formState.important_advice || '未填写' }}</strong></li>
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
              <h3>{{ isFamilyCompanion ? '生成结果' : '确认并生成结果' }}</h3>
            </div>
            <p class="section-note">{{ isFamilyCompanion ? '把这一版保存成可继续完善的结果。' : '先看一眼，再生成第一版结果。' }}</p>
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
              <template v-else-if="createType === 'family_companion'">
                <h3>{{ formState.persona_name || '未填写称呼' }}</h3>
                <p class="state-copy">{{ formState.comfort_style || '还没有填写安慰方式。' }}</p>
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
