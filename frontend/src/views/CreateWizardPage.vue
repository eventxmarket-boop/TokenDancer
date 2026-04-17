<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import MaterialInputPanel from '@/components/shared/MaterialInputPanel.vue'
import {
  clearWizardState,
  loadWizardState,
  saveLatestDraft,
  saveWizardState,
  submitCreateDraft,
  normalizeCreateWizardInputMode,
  type CreateWizardRawMaterials,
  type UploadedImageDocument,
  type TextMaterialDocument,
} from '@/services/createWizardService'
import {
  requestSelfFillAssistant,
  type SelfFillAssistantRequestPayload,
  type SelfFillAssistantResponse,
} from '@/services/selfFillAssistantService'

type CreateType =
  | 'self_unified'
  | 'source_persona'
  | 'relationship_persona'
  | 'family_companion'
  | 'reunion_persona'
  | 'intimate_companion'
  | 'reply_assistant'

type SelfCreateMode = 'light' | 'standard' | 'deep'

type SelfInterviewQuestionOption = {
  key: string
  label: string
  question: string
  dimension: string
  reason: string
}

type SelfInterviewEntry = {
  id: string
  key: string
  question: string
  answer: string
  dimension: string
  reason: string
}

type SelfFillAssistantMessage = {
  role: 'user' | 'assistant'
  content: string
}

const router = useRouter()
const route = useRoute()

const step = ref(1)
const loading = ref(false)
const error = ref('')
const createType = ref<CreateType>('self_unified')
const createMode = ref<SelfCreateMode>('light')
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
  create_mode: 'light',
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
  self_public_sources_text: '',
  self_external_feedback_text: '',
  self_deep_dive_answers_text: '',
  self_interview_answers_text: '',
  self_interview_custom_questions_text: '',
  self_validation_samples_text: '',
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
  reunion_guided_recall_scenes: '',
  reunion_guided_how_they_addressed_you: '',
  reunion_guided_repeated_phrases: '',
  reunion_guided_most_characteristic_moment: '',
  reunion_guided_deepest_impression: '',
  reunion_guided_care_style: '',
  reunion_guided_typical_reminders: '',
  reunion_guided_most_important_shared_memory: '',
  guided_most_common_topics: '',
  guided_comfort_style: '',
  guided_most_characteristic_event: '',
  guided_repeated_phrases: '',
  guided_care_habits: '',
  guided_most_common_reminders: '',
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
  target_person_type: 'crush',
  target_person_label: '暧昧 / crush',
  target_person_name: '',
  reply_mode: 'single_message',
  relationship_status: '',
  reply_goal: '',
  tone: '',
  target_person_description: '',
  single_message_text: '',
  reply_style_samples: '',
  reply_material_notes: '',
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
    title: '关系经营',
    description: '先看清关系，再调整表达、改善相处、继续经营。',
    hint: '从关系经营开始',
  },
  {
    type: 'reply_assistant' as const,
    title: '我该怎么回',
    description: '收到一句话，不知道怎么回，就从这里开始。',
    hint: '从回复开始',
  },
]

const intimateModeCards = [
  ['relationship_management', '关系经营'],
  ['past_relation_mirror', '过去关系 / 自我镜像'],
] as const

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
    relationship_management: '关系经营',
    message_simulation: '关系经营',
    past_relation_mirror: '过去关系 / 自我镜像',
  },
  reply_assistant: {
    single_message: '单条消息',
    material_distill: '材料蒸馏',
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

const replyAssistantTargetTypeOptions = [
  ['crush', '暧昧 / crush'],
  ['partner', '伴侣'],
  ['ex', '前任'],
  ['colleague', '同事'],
  ['boss', '上司 / 领导'],
  ['client', '客户 / 对接方'],
  ['friend', '朋友'],
  ['family', '家人'],
] as const

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
  'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill': 'single_message',
  'relationship-training-skill': 'relationship_management',
  xinyi: 'relationship_management',
  'relationship-training-skill+xinyi': 'relationship_management',
  'crush-skill': 'relationship_management',
  'partner-skill': 'relationship_management',
  'npy-skill': 'relationship_management',
  'partner-skill+npy-skill': 'relationship_management',
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
  relationship_management: 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill',
  message_simulation: 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill',
  partner_maintenance: 'relationship-training-skill+xinyi+partner-skill+npy-skill',
  past_relation_mirror: 'ex-skill+first-love-skill+shuixian-skill',
  single_message: 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill',
  material_distill: 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill',
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
  'relationship-training-skill': 'intimate_companion_relationship_management',
  xinyi: 'intimate_companion_relationship_management',
  'relationship-training-skill+xinyi': 'intimate_companion_relationship_management',
  'crush-skill': 'intimate_companion_relationship_management',
  'partner-skill': 'intimate_companion_relationship_management',
  'npy-skill': 'intimate_companion_relationship_management',
  'partner-skill+npy-skill': 'intimate_companion_relationship_management',
  'ex-skill': 'intimate_companion_past_relation_mirror',
  'first-love-skill': 'intimate_companion_past_relation_mirror',
  'shuixian-skill': 'intimate_companion_past_relation_mirror',
  'ex-skill+first-love-skill+shuixian-skill': 'intimate_companion_past_relation_mirror',
  'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill': 'reply_assistant_single_message',
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
const isReplyAssistant = computed(() => createType.value === 'reply_assistant')

const stepLabels = computed(() =>
  isSelfUnified.value
    ? ['选择深度', '选择方式', '填写信息', '生成结果']
    : isFamilyCompanion.value
    ? ['选择关系类型', '填写信息', '确认结果', '生成结果']
    : isReunionPersona.value
    ? ['选择材料', '填写信息', '确认结果', '生成结果']
    : isReplyAssistant.value
    ? ['选择入口', '选择模式', '填写信息', '生成结果']
    : ['选择类型', '选择方式', '填写信息', '生成结果'],
)

const currentInputs = computed(() => {
  if (createType.value === 'intimate_companion') {
    return intimateModeCards
  }
  if (createType.value === 'reply_assistant') {
    return Object.entries(inputModeLabels.reply_assistant || {})
  }

  return Object.entries(inputModeLabels[createType.value] || {})
})

const selfModeCards = [
  {
    mode: 'light' as const,
    title: '轻量模式',
    description: '先试试看，少量材料就能跑出一版骨架。',
  },
  {
    mode: 'standard' as const,
    title: '标准模式',
    description: '在轻量基础上继续补缺口，形成更稳的主线。',
  },
  {
    mode: 'deep' as const,
    title: '深度模式',
    description: '在标准基础上再补一轮摘要与验证，拉满深度。',
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

const selfModeJourneyCopy: Record<SelfCreateMode, string> = {
  light: '先试轻量，确认骨架后再补到标准。',
  standard: '在轻量基础上补缺口，形成稳定主线。',
  deep: '在标准基础上再补摘要与验证，拉满深度。',
}

const selfModeNextStepCopy: Record<SelfCreateMode, string> = {
  light: '下一步建议：继续补到标准',
  standard: '下一步建议：补到深度',
  deep: '当前已经是最完整路径',
}

type SelfFillPageKey =
  | 'materials'
  | 'analysis'
  | 'signals'
  | 'material_details'
  | 'identity'
  | 'decision'
  | 'knowledge'
  | 'boundary'
  | 'interview'
  | 'custom'
  | 'review'

type SelfFillPageCard = {
  key: SelfFillPageKey
  title: string
  description: string
  summary: string
}

const selfFillPageCards: SelfFillPageCard[] = [
  {
    key: 'analysis',
    title: '准备与分析',
    description: '先看要准备什么，再开始逐页填写。',
    summary: '先把素材范围、填写项数量和当前档位看清楚，再进入下一页。',
  },
  {
    key: 'materials',
    title: '材料层',
    description: '先放能证明你判断方式的素材。',
    summary: '把真实聊天、长文、决策记录、项目复盘或 OCR 材料先放进来。',
  },
  {
    key: 'signals',
    title: '公开资料 / 外部反馈',
    description: '把可查资料和别人评价补上。',
    summary: '这一步会帮助系统区分稳定人格和动态事实。',
  },
  {
    key: 'material_details',
    title: '材料说明',
    description: '说明你最代表自己的材料是什么。',
    summary: '写你最能代表自己的材料总览和材料类型。',
  },
  {
    key: 'identity',
    title: '自我身份层',
    description: '写你是谁、站在哪。',
    summary: '把长期目标、价值锚点、底线和角色定位写清楚。',
  },
  {
    key: 'decision',
    title: '自我判断层',
    description: '写你怎么判断问题。',
    summary: '把风险偏好、决策原则、取舍方式和止损规则写清楚。',
  },
  {
    key: 'knowledge',
    title: '自我知识源层',
    description: '写你现在知道什么。',
    summary: '把静态材料、最近动态和可查证来源写清楚。',
  },
  {
    key: 'boundary',
    title: '边界规则 / 验证样本',
    description: '写不能越线的地方。',
    summary: '把不编造、不过度承诺、验证样本和边界规则写清楚。',
  },
  {
    key: 'interview',
    title: '追问补洞',
    description: '用更少问题补关键缺口。',
    summary: '先从下拉问题补洞，再用回答修正分析报告。',
  },
  {
    key: 'custom',
    title: '可选追问',
    description: '补 1 到 3 个你自己想问的问题。',
    summary: '把你自己最想追问的补充问题写进去。',
  },
  {
    key: 'review',
    title: '汇总摘要',
    description: '全部填完后回头看一眼，再继续修改。',
    summary: '把前面填过的内容收成一页摘要，方便你回头逐项修改。',
  },
]

const selfFillPageIndex = ref(0)
const selfFillCurrentPage = computed(() => selfFillPageCards[selfFillPageIndex.value] || selfFillPageCards[0])
const selfFillInfoPageCards = computed(() => selfFillPageCards.filter((item) => item.key !== 'analysis' && item.key !== 'review'))
const selfFillInfoPageCount = computed(() => selfFillInfoPageCards.value.length)
const selfFillPageCount = computed(() => selfFillPageCards.length)
const selfFillPageNavItems = computed(() =>
  selfFillPageCards.map((item, index) => ({
    ...item,
    index,
    active: index === selfFillPageIndex.value,
    completed: index < selfFillPageIndex.value,
    isReview: item.key === 'review',
  }))
)
const selfFillCurrentPageIsHelper = computed(() =>
  selfFillCurrentPage.value.key === 'analysis' || selfFillCurrentPage.value.key === 'review'
)
const selfFillCurrentInfoPageIndex = computed(() => {
  const index = selfFillInfoPageCards.value.findIndex((item) => item.key === selfFillCurrentPage.value.key)
  return index >= 0 ? index + 1 : 0
})
const selfFillPrepHints = computed(() => {
  const hints = [
    `这条主线一共 ${selfFillInfoPageCount.value} 个填写项，外加 1 个准备页和 1 个汇总页。`,
    '建议先准备真实聊天、长文表达、项目复盘或决策记录。',
    '如果有公开资料、外部反馈或可查来源，也可以一并放在旁边。',
  ]

  if (createMode.value === 'light') {
    hints.unshift('轻量模式适合先拿 1 到 2 个最像你的材料试跑。')
  } else if (createMode.value === 'standard') {
    hints.unshift('标准模式适合先补全主线，再逐页补缺口。')
  } else {
    hints.unshift('深度模式适合把材料、追问、知识源和边界一次补完整。')
  }

  return hints
})
const selfFillReviewRows = computed(() => [
  { key: 'name', label: '名称', value: formState.name || '未填写', pageKey: 'materials' as SelfFillPageKey },
  { key: 'mode', label: '蒸馏深度', value: selfModeLabels[createMode.value], pageKey: 'materials' as SelfFillPageKey },
  {
    key: 'sources',
    label: '公开资料 / 知识源',
    value: formState.self_public_sources_text || '未填写',
    pageKey: 'signals' as SelfFillPageKey,
  },
  {
    key: 'feedback',
    label: '他人评价 / 外部反馈',
    value: formState.self_external_feedback_text || '未填写',
    pageKey: 'signals' as SelfFillPageKey,
  },
  {
    key: 'material',
    label: '材料说明',
    value: formState.work_system_summary || '未填写',
    pageKey: 'material_details' as SelfFillPageKey,
  },
  {
    key: 'identity',
    label: '自我身份层',
    value: formState.reply_persona_summary || '未填写',
    pageKey: 'identity' as SelfFillPageKey,
  },
  {
    key: 'decision',
    label: '自我判断层',
    value: formState.thinking_dna_summary || '未填写',
    pageKey: 'decision' as SelfFillPageKey,
  },
  {
    key: 'knowledge',
    label: '自我知识源层',
    value: formState.memory_evidence_summary || '未填写',
    pageKey: 'knowledge' as SelfFillPageKey,
  },
  {
    key: 'boundary',
    label: '边界规则',
    value: formState.reflection_rules_summary || '未填写',
    pageKey: 'boundary' as SelfFillPageKey,
  },
  {
    key: 'interview',
    label: '追问补洞',
    value: `${selfInterviewEntries.value.length} 项已完成`,
    pageKey: 'interview' as SelfFillPageKey,
  },
  {
    key: 'custom',
    label: '可选追问',
    value: formState.self_interview_custom_questions_text || '未填写',
    pageKey: 'custom' as SelfFillPageKey,
  },
])

function jumpToSelfFillReviewTarget(item: { key: string; pageKey: SelfFillPageKey }) {
  if (item.key === 'mode') {
    goStep(1)
    return
  }
  goSelfFillPageByKey(item.pageKey)
}

function resetSelfFillPageIndex() {
  selfFillPageIndex.value = 0
}

function goSelfFillPage(nextIndex: number) {
  selfFillPageIndex.value = Math.min(Math.max(nextIndex, 0), selfFillPageCards.length - 1)
}

function goSelfFillPageByKey(key: SelfFillPageKey) {
  const index = selfFillPageCards.findIndex((item) => item.key === key)
  if (index >= 0) {
    goSelfFillPage(index)
  }
}

function nextSelfFillPage() {
  if (selfFillCurrentPage.value.key === 'review') {
    goStep(4)
    return
  }
  goSelfFillPage(selfFillPageIndex.value + 1)
}

function prevSelfFillPage() {
  goSelfFillPage(selfFillPageIndex.value - 1)
}

const selfInterviewQuestionOptions: SelfInterviewQuestionOption[] = [
  {
    key: 'long_term_goal',
    label: '长期目标',
    question: '如果只能保留一个长期方向，你会先保留哪一个？',
    dimension: '长期目标',
    reason: '确认你真正想长期押注的方向。',
  },
  {
    key: 'value_anchor',
    label: '价值锚点',
    question: '哪三个价值一旦被碰到，你会立刻停下来？',
    dimension: '价值锚点',
    reason: '确认你最不愿意让步的部分。',
  },
  {
    key: 'decision_rule',
    label: '判断规则',
    question: '你做重大判断时最先看的三个条件是什么？',
    dimension: '核心判断规则',
    reason: '确认你最常用的判断顺序。',
  },
  {
    key: 'expression_style',
    label: '表达风格',
    question: '哪些场景你会说得更直，哪些场景你会收一点？',
    dimension: '表达风格',
    reason: '确认你在不同场景里的表达切换。',
  },
  {
    key: 'work_style',
    label: '做事方式',
    question: '你更常用哪种做事顺序：先保底、先推进还是先验证？',
    dimension: '做事方式',
    reason: '确认你做事时最稳定的节奏。',
  },
  {
    key: 'mistake_case',
    label: '错误判断',
    question: '你做过最典型的一次错误判断是什么？',
    dimension: '阶段变化',
    reason: '从错误里看判断逻辑的修正点。',
  },
  {
    key: 'recent_change',
    label: '最近变化',
    question: '最近你新增了什么观点、偏好或做法？',
    dimension: '近期变化',
    reason: '让动态事实能被持续更新。',
  },
  {
    key: 'external_feedback',
    label: '外部反馈',
    question: '别人最常怎么评价你的判断、表达、推进方式或边界感？',
    dimension: '他人评价',
    reason: '从外部视角校准自我描述。',
  },
  {
    key: 'public_sources',
    label: '公开资料',
    question: '你愿意让系统优先查哪些可公开验证的资料源？',
    dimension: '公开资料源',
    reason: '让动态问题能先查再答。',
  },
  {
    key: 'boundary_rule',
    label: '边界规则',
    question: '哪些事情你不允许系统为了“像你”而编造？',
    dimension: '边界规则',
    reason: '避免人格越写越假。',
  },
  {
    key: 'stop_loss',
    label: '止损规则',
    question: '什么信号出现时，你会判断该止损了？',
    dimension: '止损规则',
    reason: '补上你判断中的止损阈值。',
  },
  {
    key: 'push_rule',
    label: '推进规则',
    question: '什么信号出现时，你会判断值得继续推进？',
    dimension: '推进规则',
    reason: '补上你判断中的推进阈值。',
  },
  {
    key: 'custom_question',
    label: '自定义补充',
    question: '自定义补充',
    dimension: '自定义补充',
    reason: '把你最想追问的问题自己写进来。',
  },
]

const selfInterviewEntries = ref<SelfInterviewEntry[]>([])
const selfInterviewSelectedOptionKey = ref(selfInterviewQuestionOptions[0]?.key || 'long_term_goal')
const selfInterviewDialogOpen = ref(false)
const selfInterviewDialogQuestion = ref('')
const selfInterviewDialogAnswer = ref('')
const selfInterviewDialogDimension = ref('')
const selfInterviewDialogReason = ref('')
const selfInterviewDialogKey = ref('')
const selfInterviewDialogError = ref('')
const selfFillAssistantOpen = ref(false)
const selfFillAssistantLoading = ref(false)
const selfFillAssistantError = ref('')
const selfFillAssistantInput = ref('')
const selfFillAssistantMessages = ref<SelfFillAssistantMessage[]>([])

function createSelfInterviewEntryId() {
  const fallback = `self-interview-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return fallback
}

function splitQuestionAnswerLine(value: string): [string, string] {
  const text = String(value || '').trim()
  if (!text) {
    return ['', '']
  }

  const separators = ['｜', '|', '：', ':']
  for (const separator of separators) {
    const index = text.indexOf(separator)
    if (index > 0) {
      return [text.slice(0, index).trim(), text.slice(index + 1).trim()]
    }
  }

  return [text, '']
}

function parseSelfInterviewEntriesText(value: string) {
  return String(value || '')
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      const [question, answer] = splitQuestionAnswerLine(line)
      if (!question && !answer) {
        return null
      }
      const option = selfInterviewQuestionOptions.find((item) => item.question === question || item.label === question)
      return {
        id: createSelfInterviewEntryId(),
        key: option?.key || `legacy-${index}`,
        question,
        answer,
        dimension: option?.dimension || '历史补充',
        reason: option?.reason || '从历史保存内容里恢复',
      } as SelfInterviewEntry
    })
    .filter(Boolean) as SelfInterviewEntry[]
}

function serializeSelfInterviewEntries(entries: SelfInterviewEntry[]) {
  return entries
    .map((entry) => {
      const question = String(entry.question || '').trim()
      const answer = String(entry.answer || '').trim()
      if (!question && !answer) {
        return ''
      }
      return `${question || '未命名问题'}｜${answer}`
    })
    .filter(Boolean)
    .join('\n')
}

function syncSelfInterviewTextFromEntries() {
  formState.self_interview_answers_text = serializeSelfInterviewEntries(selfInterviewEntries.value)
}

function resetSelfInterviewEntries() {
  selfInterviewEntries.value = []
  selfInterviewSelectedOptionKey.value = selfInterviewQuestionOptions[0]?.key || 'long_term_goal'
  selfInterviewDialogOpen.value = false
  selfInterviewDialogQuestion.value = ''
  selfInterviewDialogAnswer.value = ''
  selfInterviewDialogDimension.value = ''
  selfInterviewDialogReason.value = ''
  selfInterviewDialogKey.value = ''
  selfInterviewDialogError.value = ''
  syncSelfInterviewTextFromEntries()
}

function hydrateSelfInterviewEntriesFromText(value: string) {
  const entries = parseSelfInterviewEntriesText(value)
  selfInterviewEntries.value = entries
  syncSelfInterviewTextFromEntries()
}

function openSelfInterviewDialog(key = selfInterviewSelectedOptionKey.value) {
  const option = selfInterviewQuestionOptions.find((item) => item.key === key) || selfInterviewQuestionOptions[0]
  if (!option) {
    return
  }

  selfInterviewSelectedOptionKey.value = option.key
  const existing = selfInterviewEntries.value.find((entry) => entry.key === option.key)

  selfInterviewDialogOpen.value = true
  selfInterviewDialogKey.value = option.key
  selfInterviewDialogDimension.value = option.dimension
  selfInterviewDialogReason.value = option.reason
  selfInterviewDialogQuestion.value = existing?.question || option.question
  selfInterviewDialogAnswer.value = existing?.answer || ''
  selfInterviewDialogError.value = ''
}

function closeSelfInterviewDialog() {
  selfInterviewDialogOpen.value = false
  selfInterviewDialogError.value = ''
}

function removeSelfInterviewEntry(key: string) {
  selfInterviewEntries.value = selfInterviewEntries.value.filter((entry) => entry.key !== key)
  syncSelfInterviewTextFromEntries()
}

function editSelfInterviewEntry(key: string) {
  openSelfInterviewDialog(key)
}

function addSelfInterviewEntry() {
  const question = selfInterviewDialogQuestion.value.trim()
  const answer = selfInterviewDialogAnswer.value.trim()
  if (!question) {
    selfInterviewDialogError.value = '请先补一个问题。'
    return
  }
  if (!answer) {
    selfInterviewDialogError.value = '请先填写回答。'
    return
  }

  const option = selfInterviewQuestionOptions.find((item) => item.key === selfInterviewDialogKey.value)
  const nextEntry: SelfInterviewEntry = {
    id: selfInterviewEntries.value.find((entry) => entry.key === selfInterviewDialogKey.value)?.id || createSelfInterviewEntryId(),
    key: selfInterviewDialogKey.value || option?.key || `custom-${Date.now()}`,
    question,
    answer,
    dimension: option?.dimension || '自定义补充',
    reason: option?.reason || '手动补充',
  }

  const nextEntries = selfInterviewEntries.value.filter((entry) => entry.key !== nextEntry.key)
  nextEntries.push(nextEntry)
  selfInterviewEntries.value = nextEntries
  syncSelfInterviewTextFromEntries()
  closeSelfInterviewDialog()
}

const selfFillAssistantQuickPrompts = [
  {
    label: '这个字段怎么填',
    prompt: '这个字段怎么填？请结合当前页面解释它的作用和填写重点。',
  },
  {
    label: '轻量/标准/深度',
    prompt: '轻量、标准、深度这三个档位到底有什么区别？',
  },
  {
    label: '分析报告作用',
    prompt: '分析报告这一块是做什么的？',
  },
  {
    label: '追问补洞',
    prompt: '追问补洞这一块为什么要做？',
  },
] as const

function createSelfFillAssistantGreeting(): SelfFillAssistantMessage {
  return {
    role: 'assistant',
    content: `我是填写助手，只解释这页怎么填。当前是${selfModeLabels[createMode.value]}，你可以直接问字段含义、skill 逻辑、追问补洞或档位区别。`,
  }
}

function resetSelfFillAssistantConversation() {
  selfFillAssistantMessages.value = [createSelfFillAssistantGreeting()]
  selfFillAssistantInput.value = ''
  selfFillAssistantError.value = ''
}

function openSelfFillAssistantDialog(preferredPrompt = '') {
  if (!selfFillAssistantMessages.value.length) {
    resetSelfFillAssistantConversation()
  }
  selfFillAssistantOpen.value = true
  selfFillAssistantError.value = ''
  if (preferredPrompt) {
    selfFillAssistantInput.value = preferredPrompt
  }
}

function closeSelfFillAssistantDialog() {
  selfFillAssistantOpen.value = false
  selfFillAssistantError.value = ''
}

function buildSelfFillAssistantFormSnapshot() {
  return {
    name: formState.name,
    create_mode: createMode.value,
    work_system_summary: formState.work_system_summary,
    work_system_points: formState.work_system_points,
    reply_persona_summary: formState.reply_persona_summary,
    reply_persona_points: formState.reply_persona_points,
    thinking_dna_summary: formState.thinking_dna_summary,
    thinking_dna_points: formState.thinking_dna_points,
    memory_evidence_summary: formState.memory_evidence_summary,
    memory_evidence_points: formState.memory_evidence_points,
    reflection_rules_summary: formState.reflection_rules_summary,
    reflection_rules_points: formState.reflection_rules_points,
    self_public_sources_text: formState.self_public_sources_text,
    self_external_feedback_text: formState.self_external_feedback_text,
    self_validation_samples_text: formState.self_validation_samples_text,
    self_interview_answers_text: formState.self_interview_answers_text,
    self_interview_custom_questions_text: formState.self_interview_custom_questions_text,
  }
}

async function sendSelfFillAssistantMessage(messageText = selfFillAssistantInput.value) {
  const message = messageText.trim()
  if (!message || selfFillAssistantLoading.value) {
    return
  }

  selfFillAssistantError.value = ''
  const priorMessages = [...selfFillAssistantMessages.value]
  selfFillAssistantMessages.value = [...priorMessages, { role: 'user', content: message }]
  selfFillAssistantInput.value = ''
  selfFillAssistantLoading.value = true

  try {
    const currentPage = selfFillCurrentPage.value
    const payload: SelfFillAssistantRequestPayload = {
      message,
      create_mode: createMode.value,
      current_step: String(step.value),
      active_section: currentPage.title,
      active_field_key: currentPage.key,
      active_field_label: currentPage.title,
      field_context: `${selfModeJourneyCopy[createMode.value]} · ${currentPage.summary}`,
      conversation_context: priorMessages
        .slice(-8)
        .map((item) => `${item.role === 'user' ? '用户' : '助手'}：${item.content}`)
        .join('\n'),
      form_snapshot: buildSelfFillAssistantFormSnapshot(),
    }
    const result: SelfFillAssistantResponse = await requestSelfFillAssistant(payload)
    selfFillAssistantMessages.value = [...selfFillAssistantMessages.value, { role: 'assistant', content: result.reply }]
  } catch (cause) {
    const message = cause instanceof Error ? cause.message : '填写助手暂时不可用'
    selfFillAssistantError.value = message
    selfFillAssistantMessages.value = [
      ...selfFillAssistantMessages.value,
      {
        role: 'assistant',
        content: `抱歉，${message}。我只回答这页的填写和 skill 解释。`,
      },
    ]
  } finally {
    selfFillAssistantLoading.value = false
  }
}

function sendSelfFillAssistantPrompt(prompt: string) {
  selfFillAssistantInput.value = prompt
  void sendSelfFillAssistantMessage(prompt)
}

function createEmptyMaterialState(): CreateWizardRawMaterials {
  return {
    chat_history_text: '',
    memory_notes_text: '',
    text_materials_text: '',
    uploaded_text_documents: [],
    uploaded_image_documents: [],
    ocr_extracted_texts: [],
    image_notes_text: '',
    photo_notes_text: '',
    voice_notes_text: '',
    diary_text: '',
    letter_text: '',
    conflict_text: '',
    draft_message_text: '',
    recent_context_text: '',
    reply_style_samples_text: '',
    relationship_status_text: '',
    interaction_patterns_text: '',
    history_text: '',
    expression_samples_text: '',
  }
}

const familyMaterialState = ref<CreateWizardRawMaterials>(createEmptyMaterialState())
const reunionMaterialState = ref<CreateWizardRawMaterials>(createEmptyMaterialState())
const intimateMaterialState = ref<CreateWizardRawMaterials>(createEmptyMaterialState())
const replyAssistantMaterialState = ref<CreateWizardRawMaterials>(createEmptyMaterialState())
const selfMaterialState = ref<CreateWizardRawMaterials>(createEmptyMaterialState())
const sourceMaterialState = ref<CreateWizardRawMaterials>(createEmptyMaterialState())
const relationshipMaterialState = ref<CreateWizardRawMaterials>(createEmptyMaterialState())

const familyMaterialFileName = ref('')
const reunionMaterialFileName = ref('')

const familyUploadedTextDocuments = computed({
  get: () => familyMaterialState.value.uploaded_text_documents,
  set: (value: TextMaterialDocument[]) => {
    familyMaterialState.value.uploaded_text_documents = value
  },
})
const familyUploadedImageDocuments = computed({
  get: () => familyMaterialState.value.uploaded_image_documents,
  set: (value: UploadedImageDocument[]) => {
    familyMaterialState.value.uploaded_image_documents = value
  },
})
const familyChatHistoryText = computed({
  get: () => familyMaterialState.value.chat_history_text,
  set: (value: string) => {
    familyMaterialState.value.chat_history_text = value
  },
})
const familyMemoryNotesText = computed({
  get: () => familyMaterialState.value.memory_notes_text,
  set: (value: string) => {
    familyMaterialState.value.memory_notes_text = value
  },
})
const familyTextMaterialsText = computed({
  get: () => familyMaterialState.value.text_materials_text,
  set: (value: string) => {
    familyMaterialState.value.text_materials_text = value
  },
})
const reunionUploadedTextDocuments = computed({
  get: () => reunionMaterialState.value.uploaded_text_documents,
  set: (value: TextMaterialDocument[]) => {
    reunionMaterialState.value.uploaded_text_documents = value
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
    return '关系经营'
  }
  if (createType.value === 'reply_assistant') {
    return '我该怎么回'
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
    value === 'intimate_companion' ||
    value === 'reply_assistant'
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

  const group = readQueryValue('group')
  if (group === 'reply_assistant') {
    return 'reply_assistant'
  }
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
    return normalizeCreateWizardInputMode(createTypeValue, schemaKey)
  }

  if (sourceRepo && inputModeBySourceRepo[sourceRepo]) {
    return normalizeCreateWizardInputMode(createTypeValue, inputModeBySourceRepo[sourceRepo])
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
    return 'relationship_management'
  }
  if (createTypeValue === 'reply_assistant') {
    return 'single_message'
  }

  return 'colleague'
}

function resolveSchemaKey(createTypeValue: CreateType, sourceRepo: string, inputModeValue: string, displayName: string) {
  const normalizedInputMode = normalizeCreateWizardInputMode(createTypeValue, inputModeValue)
  if (createTypeValue === 'family_companion') {
    return `family_companion_${normalizedInputMode || 'mother'}`
  }
  if (createTypeValue === 'reunion_persona') {
    return `reunion_persona_${normalizedInputMode || 'chat_history'}`
  }
  if (createTypeValue === 'intimate_companion') {
    return `intimate_companion_${normalizedInputMode || 'relationship_management'}`
  }
  if (createTypeValue === 'reply_assistant') {
    return `reply_assistant_${normalizedInputMode || 'single_message'}`
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
  if (type === 'reply_assistant') {
    return 'reply_assistant'
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
    return 'relationship-training-skill+xinyi+partner-skill+npy-skill'
  }
  if (type === 'reply_assistant') {
    return 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill'
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
    return '关系经营'
  }
  if (type === 'reply_assistant') {
    return '我该怎么回'
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
  resetSelfFillPageIndex()
  resetSelfFillAssistantConversation()
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
  if (type === 'reply_assistant') {
    return 'reply_assistant'
  }

  if (mode === 'colleague' || mode === 'boss') {
    return 'relationship_workplace'
  }
  if (mode === 'supervisor' || mode === 'senpai' || mode === 'professor_a' || mode === 'professor_b') {
    return 'relationship_academia'
  }
  if (
    mode === 'relationship_management' ||
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
    if (mode === 'manual_profile') return '先写身份、判断和表达底色。'
    if (mode === 'chat_history') return '适合把真实聊天当作素材输入。'
    if (mode === 'documents') return '适合把文章、笔记和项目材料补进去。'
    if (mode === 'memory_notes') return '适合补最近变化和记忆片段。'
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

  if (type === 'reply_assistant') {
    if (mode === 'single_message') return '输入一条消息，直接给候选回法和预判。'
    if (mode === 'material_distill') return '输入聊天记录或材料，先蒸馏出对方的回复风格。'
    if (mode === 'crush') return '适合暧昧 / crush 的回复场景。'
    if (mode === 'partner') return '适合伴侣的稳定关系回复。'
    if (mode === 'ex') return '适合前任或过去关系的回复。'
    if (mode === 'colleague') return '适合同事的工作回复。'
    if (mode === 'boss') return '适合上司 / 领导的沟通回复。'
    if (mode === 'client') return '适合客户 / 对接方的回复。'
    if (mode === 'friend') return '适合朋友的日常回复。'
    if (mode === 'family') return '适合家人的回复。'
  }

  if (type === 'intimate_companion') {
    if (
      mode === 'relationship_management' ||
      mode === 'relationship_understanding' ||
      mode === 'relationship_maintenance' ||
      mode === 'partner_maintenance' ||
      mode === 'message_simulation' ||
      mode === 'crush'
    ) {
      return '适合先看清关系、调整表达、改善相处，并根据材料动态偏向理解、维护或发送前预演。'
    }
    if (mode === 'past_relation_mirror') return '适合回看过去关系和自我镜像。'
  }

  if (type === 'family_companion') {
    if (mode === 'mother') return '更偏安慰、接住情绪和熟悉照顾感。'
    if (mode === 'parents') return '更偏家庭共同记忆和稳定建议。'
    if (mode === 'other_family') return '更偏通用家庭陪伴。'
  }

  if (type === 'reunion_persona') {
    if (mode === 'chat_history') return '适合从聊天记录开始。'
    if (mode === 'documents') return '适合从文档或纪念材料开始。'
    if (mode === 'memory_notes') return '适合先整理回忆片段。'
    if (mode === 'photo_notes') return '适合先整理照片 / 截图说明。'
    if (mode === 'voice_notes') return '适合先整理口述回忆。'
  }

  if (type === 'reply_assistant') {
    if (mode === 'single_message') return '输入一条消息，直接给候选回法和预判。'
    if (mode === 'material_distill') return '输入聊天记录或材料，先蒸馏出对方的回复风格。'
    if (mode === 'crush') return '适合暧昧 / crush 的回复场景。'
    if (mode === 'partner') return '适合伴侣的稳定关系回复。'
    if (mode === 'ex') return '适合前任或过去关系的回复。'
    if (mode === 'colleague') return '适合同事的工作回复。'
    if (mode === 'boss') return '适合上司 / 领导的沟通回复。'
    if (mode === 'client') return '适合客户 / 对接方的回复。'
    if (mode === 'friend') return '适合朋友的日常回复。'
    if (mode === 'family') return '适合家人的回复。'
  }

  return '适合继续完善。'
}

function getRelationshipLabel(mode: string) {
  const intimateLegacyLabel = {
    relationship_understanding: '关系经营',
    relationship_maintenance: '关系经营',
    partner_maintenance: '关系经营',
    message_simulation: '关系经营',
    crush: '关系经营',
  } as const
  return (
    (mode === 'relationship_management' ? '关系经营' : '') ||
    inputModeLabels.reply_assistant[mode] ||
    inputModeLabels.relationship_persona[mode] ||
    inputModeLabels.intimate_companion[mode] ||
    intimateLegacyLabel[mode as keyof typeof intimateLegacyLabel] ||
    inputModeLabels.family_companion[mode] ||
    inputModeLabels.reunion_persona[mode] ||
    '关系人格'
  )
}

function getFamilySubtypeNote(mode: string) {
  if (mode === 'mother') {
    return '妈妈更偏安慰和接住情绪，语气更熟悉。'
  }
  if (mode === 'parents') {
    return '父母更偏家庭共同记忆和稳定建议。'
  }
  if (mode === 'other_family') {
    return '其他家人走更通用的家庭陪伴。'
  }
  return '先选妈妈、父母或其他家人，再统一填写下面的内容。'
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
  familyMaterialState.value = createEmptyMaterialState()
  reunionMaterialState.value = createEmptyMaterialState()
  intimateMaterialState.value = createEmptyMaterialState()
  replyAssistantMaterialState.value = createEmptyMaterialState()
  selfMaterialState.value = createEmptyMaterialState()
  sourceMaterialState.value = createEmptyMaterialState()
  relationshipMaterialState.value = createEmptyMaterialState()
  familyMaterialFileName.value = ''
  reunionMaterialFileName.value = ''
  resetSelfInterviewEntries()

  if (type === 'self_unified') {
    formState.name = displayName || '自我主线'
    formState.create_mode = mode || 'light'
    formState.work_system_summary = '先放能证明你判断方式的素材。'
    formState.work_system_points = '真实聊天\n长文表达\n项目复盘\n决策记录'
    formState.reply_persona_summary = '把最稳定的自我定位写出来。'
    formState.reply_persona_points = '我最在意什么\n我最坚持什么\n我站在什么位置说话'
    formState.thinking_dna_summary = '把判断顺序和决策原则写出来。'
    formState.thinking_dna_points = '先问条件\n再看出路\n再算代价'
    formState.memory_evidence_summary = '把静态材料和动态知识源写出来。'
    formState.memory_evidence_points = '笔记 / 文章 / 公开表达\n指定网站 / 项目 / 文档'
    formState.reflection_rules_summary = '把边界规则和验证样本写出来。'
    formState.reflection_rules_points = '不编造经历\n不假装熟悉\n不把动态事实说死'
    formState.self_public_sources_text = 'GitHub / 博客 / 作品集 / 公众号 / 视频号 / B站'
    formState.self_external_feedback_text = '他人评价、复盘记录、外部反馈'
    formState.self_deep_dive_answers_text = ''
    formState.self_interview_answers_text = ''
    formState.self_interview_custom_questions_text = ''
    formState.self_validation_samples_text = '要不要接某个 offer？\n要不要转方向？\n要不要先做 MVP？\n这件事该止损还是继续推进？'
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
    formState.relationship_type = getRelationshipLabel(mode) || displayName || '关系经营'
    formState.persona_name = displayName || getRelationshipLabel(mode) || '关系经营'
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

  if (type === 'reply_assistant') {
    formState.target_person_type = 'crush'
    formState.target_person_label = '暧昧 / crush'
    formState.target_person_name = displayName || '暧昧对象'
    formState.reply_mode = mode || 'single_message'
    formState.relationship_status = '关系状态待补充'
    formState.reply_goal = '先把话接住，再给更合适的回应。'
    formState.tone = '自然、克制、清楚。'
    formState.target_person_description = '把对方的话、关系状态和目标一起整理出来。'
    formState.single_message_text = '把对方原话贴在这里。'
    formState.reply_style_samples = '稳妥版\n自然版\n主动版\n克制版'
    formState.reply_material_notes = '把聊天记录、文件、图片或 OCR 材料补充进来。'
    formState.relation_boundaries = '不替你做最终决定，不夸大未确认的信息。'
  }
}

function buildEntryDefaults() {
  const createTypeValue = inferCreateTypeFromQuery()
  const rawDisplayName = readQueryValue('display_name') || readQueryValue('name')
  const displayName =
    createTypeValue === 'self_unified'
      ? getDefaultDisplayNameForType(createTypeValue)
      : rawDisplayName || getDefaultDisplayNameForType(createTypeValue)
  const createModeValue = (readQueryValue('create_mode') as SelfCreateMode) || 'light'
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
    familyMaterialState: familyMaterialState.value,
    reunionMaterialState: reunionMaterialState.value,
    intimateMaterialState: intimateMaterialState.value,
    replyAssistantMaterialState: replyAssistantMaterialState.value,
    selfMaterialState: selfMaterialState.value,
    sourceMaterialState: sourceMaterialState.value,
    relationshipMaterialState: relationshipMaterialState.value,
    selfFillAssistantMessages: selfFillAssistantMessages.value,
    selfFillAssistantInput: selfFillAssistantInput.value,
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
    familyMaterialState?: CreateWizardRawMaterials
    reunionMaterialState?: CreateWizardRawMaterials
    intimateMaterialState?: CreateWizardRawMaterials
    replyAssistantMaterialState?: CreateWizardRawMaterials
    selfMaterialState?: CreateWizardRawMaterials
    sourceMaterialState?: CreateWizardRawMaterials
    relationshipMaterialState?: CreateWizardRawMaterials
    selfFillAssistantMessages?: SelfFillAssistantMessage[]
    selfFillAssistantInput?: string
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
    inputMode.value = normalizeCreateWizardInputMode(createType.value, snapshot.inputMode)
  }
  if (createType.value === 'family_companion' && snapshot.familySubtype) {
    inputMode.value = normalizeCreateWizardInputMode(createType.value, snapshot.familySubtype)
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
  if (snapshot.familyMaterialState) {
    familyMaterialState.value = snapshot.familyMaterialState
  }
  if (snapshot.reunionMaterialState) {
    reunionMaterialState.value = snapshot.reunionMaterialState
  }
  if (snapshot.intimateMaterialState) {
    intimateMaterialState.value = snapshot.intimateMaterialState
  }
  if (snapshot.replyAssistantMaterialState) {
    replyAssistantMaterialState.value = snapshot.replyAssistantMaterialState
  }
  if (snapshot.selfMaterialState) {
    selfMaterialState.value = snapshot.selfMaterialState
  }
  if (snapshot.sourceMaterialState) {
    sourceMaterialState.value = snapshot.sourceMaterialState
  }
  if (snapshot.relationshipMaterialState) {
    relationshipMaterialState.value = snapshot.relationshipMaterialState
  }
  if (Array.isArray(snapshot.selfFillAssistantMessages) && snapshot.selfFillAssistantMessages.length > 0) {
    selfFillAssistantMessages.value = snapshot.selfFillAssistantMessages
  }
  if (snapshot.selfFillAssistantInput) {
    selfFillAssistantInput.value = snapshot.selfFillAssistantInput
  }

  if (createType.value === 'relationship_persona') {
    const intimateModes = new Set([
      'relationship_management',
      'relationship_understanding',
      'message_simulation',
      'crush',
      'partner_maintenance',
      'past_relation_mirror',
    ])
    const familyModes = new Set(['mother', 'parents', 'other_family'])
    const intimateSources = new Set([
      'relationship-training-skill+xinyi+partner-skill+npy-skill',
      'relationship-training-skill+xinyi',
      'relationship-training-skill',
      'xinyi',
      'partner-skill+npy-skill',
      'partner-skill',
      'npy-skill',
      'crush-skill',
      'ex-skill+first-love-skill+shuixian-skill',
    ])
    const familySources = new Set(['MamaSkill', 'parents-skills', 'MamaSkill+parents-skills+darwin-skill', 'parents-skills+MamaSkill'])
    const reunionSources = new Set(['reunion-skill'])
    const replySources = new Set([
      'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill',
      'crush-skill',
      'colleague-skill',
      'boss-skills',
      'partner-skill',
      'npy-skill',
      'ex-skill',
    ])

    if (
      selectedGroup.value === 'relationship_intimate' ||
      intimateModes.has(inputMode.value) ||
      intimateSources.has(selectedSourceRepo.value)
    ) {
      createType.value = 'intimate_companion'
      selectedGroup.value = 'relationship_intimate'
      if (inputMode.value === 'ex' || inputMode.value === 'first_love' || inputMode.value === 'self_mirror') {
        inputMode.value = 'past_relation_mirror'
      } else if (inputMode.value === 'partner' || inputMode.value === 'ideal_partner') {
        inputMode.value = 'relationship_management'
      } else if (inputMode.value === 'relationship_training' || inputMode.value === 'relationship_interpreter') {
        inputMode.value = 'relationship_management'
      } else if (
        !inputMode.value ||
        inputMode.value === 'relationship_understanding' ||
        inputMode.value === 'partner_maintenance' ||
        inputMode.value === 'relationship_maintenance' ||
        inputMode.value === 'message_simulation' ||
        inputMode.value === 'crush'
      ) {
        inputMode.value = 'relationship_management'
      }
    } else if (reunionSources.has(selectedSourceRepo.value) || inputMode.value === 'reunion' || selectedSchemaKey.value?.startsWith('reunion_persona_')) {
      createType.value = 'reunion_persona'
      selectedGroup.value = 'relationship_family'
      inputMode.value = inputMode.value || 'chat_history'
      selectedSourceRepo.value = 'reunion-skill'
      selectedName.value = selectedName.value || '重逢人格'
    } else if (
      selectedGroup.value === 'reply_assistant' ||
      replySources.has(selectedSourceRepo.value) ||
      inputMode.value === 'single_message' ||
      inputMode.value === 'material_distill' ||
      selectedSchemaKey.value?.startsWith('reply_assistant_')
    ) {
      createType.value = 'reply_assistant'
      selectedGroup.value = 'reply_assistant'
      selectedSourceRepo.value = 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill'
      if (!inputMode.value || inputMode.value === 'single_message' || inputMode.value === 'material_distill') {
        inputMode.value = normalizeCreateWizardInputMode(createType.value, inputMode.value || 'single_message')
      }
      selectedName.value = selectedName.value || '我该怎么回'
    } else if (
      selectedGroup.value === 'relationship_family' ||
      familyModes.has(inputMode.value) ||
      familySources.has(selectedSourceRepo.value)
    ) {
      createType.value = 'family_companion'
      selectedGroup.value = 'relationship_family'
    }
  }

  if (createType.value === 'reply_assistant') {
    const replySources = new Set([
      'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill',
      'crush-skill',
      'colleague-skill',
      'boss-skills',
      'partner-skill',
      'npy-skill',
      'ex-skill',
    ])
    selectedGroup.value = 'reply_assistant'
    if (!replySources.has(selectedSourceRepo.value)) {
      selectedSourceRepo.value = 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill'
    }
    inputMode.value = normalizeCreateWizardInputMode(createType.value, inputMode.value || 'single_message')
    selectedName.value = selectedName.value || '我该怎么回'
    selectedSchemaKey.value = selectedSchemaKey.value || resolveSchemaKey(createType.value, selectedSourceRepo.value, inputMode.value, selectedName.value)
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
      createMode.value = 'light'
    }
  }

  resetFormForType(createType.value, selectedName.value, inputMode.value)

  if (snapshot.formState) {
    Object.assign(formState, snapshot.formState)
  }

  if (createType.value === 'self_unified') {
    formState.name = normalizeSelfUnifiedDisplayName(formState.name)
    hydrateSelfInterviewEntriesFromText(formState.self_interview_answers_text)
    resetSelfFillPageIndex()
    if (!selfFillAssistantMessages.value.length) {
      resetSelfFillAssistantConversation()
    }
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
  inputMode.value = normalizeCreateWizardInputMode(createType.value, defaults.inputMode)
  selfInputModes.value = createType.value === 'self_unified' ? ['manual_profile'] : [defaults.inputMode || 'manual_profile']

  resetFormForType(createType.value, selectedName.value, inputMode.value)
  if (createType.value === 'self_unified') {
    resetSelfFillPageIndex()
    resetSelfFillAssistantConversation()
  }
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
  createMode.value = 'light'
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
    createMode.value = 'light'
    inputMode.value = 'manual_profile'
    selfInputModes.value = ['manual_profile']
  } else if (type === 'source_persona') {
    inputMode.value = 'documents'
  } else if (type === 'family_companion') {
    inputMode.value = 'mother'
  } else if (type === 'reunion_persona') {
    inputMode.value = 'chat_history'
  } else if (type === 'intimate_companion') {
    inputMode.value = 'relationship_management'
  } else if (type === 'reply_assistant') {
    inputMode.value = 'single_message'
  } else {
    inputMode.value = 'colleague'
  }
  selectedSchemaKey.value = resolveSchemaKey(type, selectedSourceRepo.value, inputMode.value, selectedName.value)
  resetFormForType(type, selectedName.value, inputMode.value)
  step.value = type === 'self_unified' ? 1 : 2
}

function selectInputMode(mode: string) {
  const normalizedMode = normalizeCreateWizardInputMode(createType.value, mode)
  inputMode.value = normalizedMode
  selectedGroup.value = resolveGroupForTypeAndMode(createType.value, normalizedMode)
  if (
    createType.value === 'relationship_persona' ||
    createType.value === 'family_companion' ||
    createType.value === 'reunion_persona' ||
    createType.value === 'intimate_companion' ||
    createType.value === 'reply_assistant'
  ) {
    if (createType.value === 'family_companion') {
      selectedSourceRepo.value = 'parents-skills+MamaSkill'
      selectedName.value = selectedName.value || getDefaultDisplayNameForType(createType.value)
    } else if (createType.value === 'reunion_persona') {
      selectedSourceRepo.value = 'reunion-skill'
      selectedName.value = selectedName.value || '重逢人格'
    } else if (createType.value === 'intimate_companion') {
      selectedSourceRepo.value =
        sourceRepoByInputMode[normalizedMode] || 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill'
      selectedName.value = getRelationshipLabel(normalizedMode) || selectedName.value
    } else if (createType.value === 'reply_assistant') {
      selectedSourceRepo.value =
        sourceRepoByInputMode[normalizedMode] ||
        'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill+ex-skill+colleague-skill+teammate-skill'
      selectedName.value = getDefaultDisplayNameForType(createType.value)
    } else {
      selectedSourceRepo.value = sourceRepoByInputMode[normalizedMode] || selectedSourceRepo.value
      selectedName.value = getRelationshipLabel(normalizedMode) || selectedName.value
    }
  } else if (createType.value === 'self_unified') {
    selfInputModes.value = Array.from(new Set([...(selfInputModes.value || []), mode]))
  }
  selectedSchemaKey.value = resolveSchemaKey(createType.value, selectedSourceRepo.value, normalizedMode, selectedName.value)
  resetFormForType(createType.value, selectedName.value, normalizedMode)
  step.value =
    createType.value === 'family_companion' || createType.value === 'reunion_persona' || createType.value === 'reply_assistant'
      ? 2
      : 3
}

function goStep(nextStep: number) {
  step.value = Math.min(Math.max(nextStep, 1), 4)
}

function buildFamilyRawMaterials() {
  return { ...familyMaterialState.value }
}

function buildFamilyGuidedMemoryAnswers() {
  return {
    most_common_topics: formState.guided_most_common_topics,
    comfort_style: formState.guided_comfort_style,
    most_characteristic_event: formState.guided_most_characteristic_event,
    repeated_phrases: formState.guided_repeated_phrases,
    care_habits: formState.guided_care_habits,
    most_common_reminders: formState.guided_most_common_reminders,
  }
}

function buildReunionGuidedMemoryAnswers() {
  return {
    recall_scenes: formState.reunion_guided_recall_scenes,
    how_they_addressed_you: formState.reunion_guided_how_they_addressed_you,
    repeated_phrases: formState.reunion_guided_repeated_phrases,
    most_characteristic_moment: formState.reunion_guided_most_characteristic_moment,
    deepest_impression: formState.reunion_guided_deepest_impression,
    care_style: formState.reunion_guided_care_style,
    typical_reminders: formState.reunion_guided_typical_reminders,
    most_important_shared_memory: formState.reunion_guided_most_important_shared_memory,
  }
}

function buildReunionRawMaterials() {
  return { ...reunionMaterialState.value }
}

function buildIntimateRawMaterials() {
  return { ...intimateMaterialState.value }
}

function buildReplyAssistantRawMaterials() {
  return { ...replyAssistantMaterialState.value }
}

function buildSelfRawMaterials() {
  return { ...selfMaterialState.value }
}

function buildSourceRawMaterials() {
  return { ...sourceMaterialState.value }
}

function buildRelationshipRawMaterials() {
  return { ...relationshipMaterialState.value }
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
      target_person_type: createType.value === 'reply_assistant' ? formState.target_person_type : undefined,
      reply_mode: createType.value === 'reply_assistant' ? inputMode.value : undefined,
      target_person_label: createType.value === 'reply_assistant' ? formState.target_person_label : undefined,
      target_person_name: createType.value === 'reply_assistant' ? formState.target_person_name : undefined,
      relationship_status: createType.value === 'reply_assistant' ? formState.relationship_status : undefined,
      reply_goal: createType.value === 'reply_assistant' ? formState.reply_goal : undefined,
      tone: createType.value === 'reply_assistant' ? formState.tone : undefined,
      target_person_description: createType.value === 'reply_assistant' ? formState.target_person_description : undefined,
      input_modes: createType.value === 'self_unified' ? [...selfInputModes.value] : [inputMode.value],
      schema_key: selectedSchemaKey.value || resolveSchemaKey(createType.value, selectedSourceRepo.value, inputMode.value, selectedName.value),
      raw_materials:
        createType.value === 'family_companion'
          ? buildFamilyRawMaterials()
          : createType.value === 'reunion_persona'
            ? buildReunionRawMaterials()
            : createType.value === 'intimate_companion'
              ? buildIntimateRawMaterials()
              : createType.value === 'reply_assistant'
                ? buildReplyAssistantRawMaterials()
              : createType.value === 'self_unified'
                ? buildSelfRawMaterials()
                : createType.value === 'source_persona'
                  ? buildSourceRawMaterials()
                  : createType.value === 'relationship_persona'
                    ? buildRelationshipRawMaterials()
              : undefined,
      guided_memory_answers:
        createType.value === 'family_companion' ? buildFamilyGuidedMemoryAnswers() : undefined,
      reunion_guided_memory_answers:
        createType.value === 'reunion_persona' ? buildReunionGuidedMemoryAnswers() : undefined,
      form_data:
        createType.value === 'self_unified'
          ? { ...formState, ...selfUnifiedPayload }
        : createType.value === 'family_companion'
          ? {
              ...formState,
              raw_materials: buildFamilyRawMaterials(),
              guided_memory_answers: buildFamilyGuidedMemoryAnswers(),
            }
            : createType.value === 'reunion_persona'
              ? {
                  ...formState,
                  raw_materials: buildReunionRawMaterials(),
                  reunion_guided_memory_answers: buildReunionGuidedMemoryAnswers(),
                }
              : createType.value === 'intimate_companion'
                ? {
                    ...formState,
                    raw_materials: buildIntimateRawMaterials(),
                  }
                : createType.value === 'reply_assistant'
                  ? {
                      ...formState,
                      raw_materials: buildReplyAssistantRawMaterials(),
                    }
                : createType.value === 'source_persona'
                  ? {
                      ...formState,
                      raw_materials: buildSourceRawMaterials(),
                    }
                  : createType.value === 'relationship_persona'
                    ? {
                        ...formState,
                        raw_materials: buildRelationshipRawMaterials(),
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

watch(
  selfInterviewEntries,
  () => {
    if (!isBootstrapping.value) {
      syncSelfInterviewTextFromEntries()
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
              <h3>{{ isSelfUnified ? '选择深度' : isFamilyCompanion ? (isReunionPersona ? '选择材料' : '选择家人类型') : '选择创建类型' }}</h3>
            </div>
            <p class="section-note">
              {{
                isSelfUnified
                  ? selfModeJourneyCopy[createMode]
                  : isFamilyCompanion
                    ? (isReunionPersona ? '先选聊天记录、文本材料或记忆片段。' : '先选妈妈、父母或其他家人，再统一填写下面的内容。')
                    : '先确认你要从哪里开始创建。'
              }}
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

          <div v-if="isSelfUnified" class="summary-panel summary-panel--compact self-mode-path-panel">
            <p class="eyebrow">升级路径</p>
            <h3>{{ selfModeJourneyCopy[createMode] }}</h3>
            <p class="state-copy">{{ selfModeNextStepCopy[createMode] }}</p>
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
              <h3>{{ isSelfUnified ? '选择输入方式' : isFamilyCompanion ? (isReunionPersona ? '填写重逢资料' : '选择家人类型') : '选择创建方式' }}</h3>
            </div>
            <p class="section-note">
              {{ isSelfUnified ? '可以先选一个或多个输入方式。' : isFamilyCompanion ? (isReunionPersona ? '把记忆层和安全边界先写清楚。' : '先选妈妈、父母或其他家人，再统一填写下面的内容。') : '不同类型会显示不同的方式选择。' }}
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
              <p class="section-note section-note--subtle">{{ getFamilySubtypeNote(inputMode) }}</p>
              <p class="eyebrow">人格层</p>
              <div class="form-grid">
                <label class="form-field">
                  <span>你怎么称呼这位家人</span>
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
                  <span>难过时会怎么安慰</span>
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

              <MaterialInputPanel
                v-model="familyMaterialState"
                path-type="family"
                :subtype="inputMode"
                :supports-guided-prompts="true"
              />

              <p v-if="!isReunionPersona" class="eyebrow">补充回忆（可选）</p>
              <p v-if="!isReunionPersona" class="section-note">
                没有完整材料也没关系，可以先用几个关键问题补充这段家人关系。
              </p>
              <div v-if="!isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>你们最常聊什么</span>
                  <textarea
                    v-model="formState.guided_most_common_topics"
                    class="field-input wizard-textarea"
                    rows="4"
                    placeholder="比如：吃饭、工作、考试、回家"
                  ></textarea>
                </label>
                <label class="form-field">
                  <span>他 / 她最常怎么安慰你</span>
                  <textarea
                    v-model="formState.guided_comfort_style"
                    class="field-input wizard-textarea"
                    rows="4"
                    placeholder="比如：先别急、慢慢来、我在呢"
                  ></textarea>
                </label>
              </div>

              <div v-if="!isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>最像他 / 她的一件小事是什么</span>
                  <textarea
                    v-model="formState.guided_most_characteristic_event"
                    class="field-input wizard-textarea"
                    rows="4"
                    placeholder="比如：每天都会提醒你吃饭"
                  ></textarea>
                </label>
                <label class="form-field">
                  <span>有哪些反复说过的话</span>
                  <textarea
                    v-model="formState.guided_repeated_phrases"
                    class="field-input wizard-textarea"
                    rows="4"
                    placeholder="把常说的话整理成几句"
                  ></textarea>
                </label>
              </div>

              <div v-if="!isReunionPersona" class="form-grid">
                <label class="form-field">
                  <span>最常提醒你的是什么</span>
                  <textarea
                    v-model="formState.guided_most_common_reminders"
                    class="field-input wizard-textarea"
                    rows="4"
                    placeholder="比如：注意休息、先稳住、别太累"
                  ></textarea>
                </label>
                <label class="form-field">
                  <span>他 / 她最典型的关心方式</span>
                  <textarea
                    v-model="formState.guided_care_habits"
                    class="field-input wizard-textarea"
                    rows="4"
                    placeholder="比如：每天问候近况、记得你爱吃什么"
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
              <MaterialInputPanel
                v-if="isReunionPersona"
                v-model="reunionMaterialState"
                path-type="reunion"
                :supports-guided-prompts="false"
              />

              <template v-if="isReunionPersona">
                <p class="eyebrow">补充回忆（可选）</p>
                <p class="section-note section-note--subtle">
                  没有完整材料也没关系，可以先用几个安静的问题补充这段重逢记忆。
                </p>
                <div class="form-grid">
                  <label class="form-field">
                    <span>你最容易在什么场景想起 ta</span>
                    <textarea
                      v-model="formState.reunion_guided_recall_scenes"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="例如：路过旧街道、看到某张照片、听到某首歌"
                    ></textarea>
                  </label>
                  <label class="form-field">
                    <span>ta 最常怎么称呼你</span>
                    <textarea
                      v-model="formState.reunion_guided_how_they_addressed_you"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="例如：名字的昵称、熟悉的称呼"
                    ></textarea>
                  </label>
                </div>

                <div class="form-grid">
                  <label class="form-field">
                    <span>ta 反复说过的话</span>
                    <textarea
                      v-model="formState.reunion_guided_repeated_phrases"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="把常见的话整理出来"
                    ></textarea>
                  </label>
                  <label class="form-field">
                    <span>哪件小事最像 ta</span>
                    <textarea
                      v-model="formState.reunion_guided_most_characteristic_moment"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="例如：某个动作、习惯或回应方式"
                    ></textarea>
                  </label>
                </div>

                <div class="form-grid">
                  <label class="form-field">
                    <span>ta 给你最深的印象是什么</span>
                    <textarea
                      v-model="formState.reunion_guided_deepest_impression"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="例如：安静、细心、克制、温柔"
                    ></textarea>
                  </label>
                  <label class="form-field">
                    <span>ta 最常表达关心的方式</span>
                    <textarea
                      v-model="formState.reunion_guided_care_style"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="例如：提醒你吃饭、问你近况、陪你走一段"
                    ></textarea>
                  </label>
                </div>

                <div class="form-grid">
                  <label class="form-field">
                    <span>哪些提醒最像 ta</span>
                    <textarea
                      v-model="formState.reunion_guided_typical_reminders"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="例如：注意休息、慢慢来、先稳住"
                    ></textarea>
                  </label>
                  <label class="form-field">
                    <span>你最想保留的共同记忆</span>
                    <textarea
                      v-model="formState.reunion_guided_most_important_shared_memory"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="例如：一起走过的一段路、某次见面"
                    ></textarea>
                  </label>
                </div>
              </template>
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

          <div v-if="createType === 'self_unified'" class="wizard-form wizard-form--self-fill">
            <div class="summary-panel summary-panel--compact self-fill-intro">
              <p class="eyebrow">自我主线</p>
              <h3>按页填写，而不是一次铺开</h3>
              <p class="state-copy">轻量先试，标准继续补，深度再拉满。你可以随时上一步、下一步，或者直接点右侧页签跳回去改。</p>
              <p class="state-copy state-copy--muted">{{ selfModeJourneyCopy[createMode] }} {{ selfModeNextStepCopy[createMode] }}</p>
              <ul class="summary-panel__list">
                <li><span>填写项</span><strong>{{ selfFillInfoPageCount }} 项</strong></li>
                <li><span>辅助页</span><strong>2 页</strong></li>
                <li><span>页面总数</span><strong>{{ selfFillPageCount }} 页</strong></li>
                <li><span>当前档位</span><strong>{{ selfModeLabels[createMode] }}</strong></li>
              </ul>
              <ul class="self-fill-prep-list">
                <li v-for="hint in selfFillPrepHints" :key="hint">{{ hint }}</li>
              </ul>
            </div>

            <div class="self-fill-layout">
              <aside class="self-fill-rail">
                <button
                  v-for="page in selfFillPageNavItems"
                  :key="page.key"
                  type="button"
                  class="self-fill-rail__button"
                  :class="{ active: page.active, completed: page.completed, helper: page.isReview || page.key === 'analysis' }"
                  @click="goSelfFillPage(page.index)"
                >
                  <span class="self-fill-rail__index">{{ page.isReview ? '汇总' : page.index + 1 }}</span>
                  <span class="self-fill-rail__body">
                    <strong>{{ page.title }}</strong>
                    <small>{{ page.description }}</small>
                  </span>
                </button>
              </aside>

              <section class="self-fill-page">
                <div class="section-head self-fill-page__head">
                  <div>
                    <p class="eyebrow">{{ selfFillCurrentPage.key === 'review' ? '汇总页' : selfFillCurrentPageIsHelper ? '准备页' : `第 ${selfFillCurrentInfoPageIndex} 项` }}</p>
                    <h3>{{ selfFillCurrentPage.title }}</h3>
                  </div>
                  <p class="section-note">{{ selfFillCurrentPage.description }}</p>
                </div>

                <div class="summary-panel summary-panel--compact self-fill-page__summary">
                  <h3>{{ selfFillCurrentPage.summary }}</h3>
                  <p class="state-copy">
                    {{ selfFillCurrentPageIsHelper ? '这一页先帮你看清结构，再继续往下填。' : '这一页只聚焦一个信息点，填完就可以下一步。' }}
                  </p>
                  <p class="state-copy state-copy--muted">可以随时回到任一页继续修改，不用一次填完。</p>
                </div>

                <div class="self-fill-page__toolbar">
                  <button class="ghost-button ghost-button--small" type="button" :disabled="selfFillPageIndex === 0" @click="prevSelfFillPage">
                    上一步
                  </button>
                  <button class="ghost-button ghost-button--small" type="button" @click="openSelfFillAssistantDialog()">
                    打开填写助手
                  </button>
                  <button class="primary-btn primary-btn--small" type="button" @click="nextSelfFillPage">
                    {{ selfFillCurrentPage.key === 'review' ? '去总汇总' : '下一步' }}
                  </button>
                </div>

                <div v-if="selfFillCurrentPage.key === 'analysis'" class="self-fill-page__content">
                  <div class="summary-panel summary-panel--compact">
                    <p class="eyebrow">准备资料</p>
                    <h3>先把素材放旁边，再逐页填写</h3>
                    <p class="state-copy">建议先准备真实聊天、长文表达、项目复盘、决策记录、公开资料和外部反馈。填写助手会随时解释每一页要做什么。</p>
                  </div>
                  <div class="self-fill-assistant-panel self-fill-assistant-panel--inline">
                    <div class="self-fill-assistant-panel__head">
                      <div>
                        <p class="eyebrow">填写助手</p>
                        <h3>只解释怎么填，不回答别的</h3>
                      </div>
                      <button type="button" class="ghost-button ghost-button--small" @click="openSelfFillAssistantDialog()">
                        打开填写助手
                      </button>
                    </div>
                    <p class="state-copy">它会调用大模型解释当前页的 skill 逻辑、字段含义、补洞顺序和档位区别。</p>
                    <div class="self-fill-assistant-panel__chips">
                      <button
                        v-for="item in selfFillAssistantQuickPrompts"
                        :key="item.label"
                        type="button"
                        class="ghost-button ghost-button--small"
                        @click="openSelfFillAssistantDialog(item.prompt)"
                      >
                        {{ item.label }}
                      </button>
                    </div>
                  </div>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'materials'" class="self-fill-page__content">
                  <MaterialInputPanel
                    v-model="selfMaterialState"
                    path-type="self"
                    :supports-guided-prompts="false"
                  />
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'signals'" class="self-fill-page__content">
                  <label class="form-field">
                    <span>公开资料 / 知识源</span>
                    <textarea
                      v-model="formState.self_public_sources_text"
                      class="field-input wizard-textarea"
                      rows="5"
                      placeholder="GitHub / 博客 / 作品集 / 公众号 / 视频号 / B站 / 其他可查资料"
                    ></textarea>
                  </label>
                  <details class="self-fill-more">
                    <summary>补充外部反馈</summary>
                    <label class="form-field">
                      <span>他人评价 / 外部反馈</span>
                      <textarea
                        v-model="formState.self_external_feedback_text"
                        class="field-input wizard-textarea"
                        rows="4"
                        placeholder="别人怎么评价你的判断、表达、推进方式或边界感"
                      ></textarea>
                    </label>
                  </details>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'material_details'" class="self-fill-page__content">
                  <label class="form-field">
                    <span>材料说明</span>
                    <textarea
                      v-model="formState.work_system_summary"
                      class="field-input wizard-textarea"
                      rows="6"
                      placeholder="先写最能代表你的材料是什么"
                    ></textarea>
                  </label>
                  <details class="self-fill-more">
                    <summary>补充材料类型</summary>
                    <label class="form-field">
                      <span>材料类型</span>
                      <textarea
                        v-model="formState.work_system_points"
                        class="field-input wizard-textarea"
                        rows="4"
                        placeholder="每行一条：真实聊天 / 长文表达 / 决策记录 / 项目复盘"
                      ></textarea>
                    </label>
                  </details>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'identity'" class="self-fill-page__content">
                  <label class="form-field">
                    <span>自我身份层</span>
                    <textarea
                      v-model="formState.reply_persona_summary"
                      class="field-input wizard-textarea"
                      rows="6"
                      placeholder="你是谁、站在什么位置说话"
                    ></textarea>
                  </label>
                  <details class="self-fill-more">
                    <summary>补充身份要点</summary>
                    <label class="form-field">
                      <span>自我身份要点</span>
                      <textarea
                        v-model="formState.reply_persona_points"
                        class="field-input wizard-textarea"
                        rows="4"
                        placeholder="每行一条：长期目标 / 价值锚点 / 底线 / 经验标签"
                      ></textarea>
                    </label>
                  </details>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'decision'" class="self-fill-page__content">
                  <label class="form-field">
                    <span>自我判断层</span>
                    <textarea
                      v-model="formState.thinking_dna_summary"
                      class="field-input wizard-textarea"
                      rows="6"
                      placeholder="你做判断时最看重什么"
                    ></textarea>
                  </label>
                  <details class="self-fill-more">
                    <summary>补充判断要点</summary>
                    <label class="form-field">
                      <span>自我判断要点</span>
                      <textarea
                        v-model="formState.thinking_dna_points"
                        class="field-input wizard-textarea"
                        rows="4"
                        placeholder="每行一条：风险偏好 / 决策原则 / 取舍方式 / 止损规则"
                      ></textarea>
                    </label>
                  </details>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'knowledge'" class="self-fill-page__content">
                  <label class="form-field">
                    <span>自我知识源层</span>
                    <textarea
                      v-model="formState.memory_evidence_summary"
                      class="field-input wizard-textarea"
                      rows="6"
                      placeholder="静态材料、最近动态、指定网站 / 项目 / 文档"
                    ></textarea>
                  </label>
                  <details class="self-fill-more">
                    <summary>补充知识源要点</summary>
                    <label class="form-field">
                      <span>知识源要点</span>
                      <textarea
                        v-model="formState.memory_evidence_points"
                        class="field-input wizard-textarea"
                        rows="4"
                        placeholder="每行一条：静态材料 / 动态来源 / 可查证信息源"
                      ></textarea>
                    </label>
                  </details>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'boundary'" class="self-fill-page__content">
                  <label class="form-field">
                    <span>边界规则</span>
                    <textarea
                      v-model="formState.reflection_rules_summary"
                      class="field-input wizard-textarea"
                      rows="6"
                      placeholder="不编造经历、不假装熟悉、不把动态事实说死"
                    ></textarea>
                  </label>
                  <details class="self-fill-more">
                    <summary>补充验证样本</summary>
                    <label class="form-field">
                      <span>验证样本</span>
                      <textarea
                        v-model="formState.self_validation_samples_text"
                        class="field-input wizard-textarea"
                        rows="4"
                        placeholder="每行一条：要不要接 offer / 要不要转方向 / 要不要先做 MVP"
                      ></textarea>
                    </label>
                  </details>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'interview'" class="self-fill-page__content">
                  <div class="summary-panel summary-panel--compact">
                    <p class="eyebrow">追问补洞</p>
                    <h3>把分析报告里缺的关键问题补全</h3>
                    <p class="state-copy">先从下拉框选一个问题，系统会自动弹出对话框。回答后点“添加”，会同步进分析报告的缺口补全里。</p>
                  </div>

                  <div class="self-interview-builder">
                    <label class="form-field self-interview-builder__select">
                      <span>选择问题</span>
                      <select
                        v-model="selfInterviewSelectedOptionKey"
                        class="field-input"
                        @change="openSelfInterviewDialog(selfInterviewSelectedOptionKey)"
                      >
                        <option v-for="option in selfInterviewQuestionOptions" :key="option.key" :value="option.key">
                          {{ option.label }} · {{ option.dimension }}
                        </option>
                      </select>
                    </label>

                    <div class="self-interview-builder__status">
                      <strong>已添加 {{ selfInterviewEntries.length }} / {{ selfInterviewQuestionOptions.length }} 项</strong>
                      <span>同一个问题会自动覆盖旧答案，方便你持续修正。</span>
                    </div>

                    <div v-if="selfInterviewEntries.length" class="self-interview-builder__list">
                      <article v-for="entry in selfInterviewEntries" :key="entry.id" class="self-interview-builder__item">
                        <div class="self-interview-builder__item-head">
                          <div>
                            <p class="self-interview-builder__item-dimension">{{ entry.dimension }}</p>
                            <h4>{{ entry.question }}</h4>
                          </div>
                          <div class="self-interview-builder__item-actions">
                            <button type="button" class="ghost-button ghost-button--small" @click="editSelfInterviewEntry(entry.key)">编辑</button>
                            <button type="button" class="ghost-button ghost-button--small" @click="removeSelfInterviewEntry(entry.key)">移除</button>
                          </div>
                        </div>
                        <p class="self-interview-builder__item-answer">{{ entry.answer }}</p>
                      </article>
                    </div>
                    <p v-else class="state-copy state-copy--muted">还没有添加问题，先从下拉框选一个吧。</p>
                  </div>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'custom'" class="self-fill-page__content">
                  <label class="form-field">
                    <span>可选追问（补充）</span>
                    <textarea
                      v-model="formState.self_interview_custom_questions_text"
                      class="field-input wizard-textarea"
                      rows="7"
                      placeholder="如果你想让系统继续补问，可以把你最想追问的 1 到 3 个问题写在这里。"
                    ></textarea>
                  </label>
                </div>

                <div v-else-if="selfFillCurrentPage.key === 'review'" class="self-fill-page__content">
                  <div class="summary-panel summary-panel--compact">
                    <p class="eyebrow">汇总摘要</p>
                    <h3>全部填完后，再看一眼整体</h3>
                    <p class="state-copy">你可以直接回到任意一页修改，这里只是帮你把所有内容收拢成一张总览。</p>
                  </div>
                  <div class="self-fill-review-grid">
                    <article v-for="item in selfFillReviewRows" :key="item.key" class="self-fill-review-card">
                      <div class="self-fill-review-card__head">
                      <div>
                          <p class="self-fill-review-card__label">{{ item.label }}</p>
                          <h4>{{ item.value }}</h4>
                        </div>
                        <button type="button" class="ghost-button ghost-button--small" @click="jumpToSelfFillReviewTarget(item)">
                          编辑
                        </button>
                      </div>
                      <p class="self-fill-review-card__meta">点击可回到对应页继续修改。</p>
                    </article>
                  </div>
                </div>
              </section>
            </div>

            <div v-if="selfFillAssistantOpen" class="self-fill-assistant-modal" @click.self="closeSelfFillAssistantDialog">
              <div class="self-fill-assistant-modal__panel">
                <div class="self-fill-assistant-modal__head">
                  <div>
                    <p class="eyebrow">填写助手</p>
                    <h3>只解释当前页面的填写方法</h3>
                    <p class="section-note section-note--subtle">
                      当前档位：{{ selfModeLabels[createMode] }} · 只回答 skill 解释和字段填写
                    </p>
                  </div>
                  <button type="button" class="ghost-button ghost-button--small" @click="closeSelfFillAssistantDialog">关闭</button>
                </div>

                <div class="self-fill-assistant-chat">
                  <article
                    v-for="(message, index) in selfFillAssistantMessages"
                    :key="`${message.role}-${index}`"
                    class="self-fill-assistant-chat__message"
                    :class="`self-fill-assistant-chat__message--${message.role}`"
                  >
                    <span class="self-fill-assistant-chat__role">{{ message.role === 'user' ? '我' : '填写助手' }}</span>
                    <p>{{ message.content }}</p>
                  </article>
                </div>

                <p v-if="selfFillAssistantError" class="state-copy state-copy--error">{{ selfFillAssistantError }}</p>

                <div class="self-fill-assistant-panel__chips self-fill-assistant-panel__chips--modal">
                  <button
                    v-for="item in selfFillAssistantQuickPrompts"
                    :key="`modal-${item.label}`"
                    type="button"
                    class="ghost-button ghost-button--small"
                    @click="sendSelfFillAssistantPrompt(item.prompt)"
                  >
                    {{ item.label }}
                  </button>
                </div>

                <label class="form-field">
                  <span>输入问题</span>
                  <textarea
                    v-model="selfFillAssistantInput"
                    class="field-input wizard-textarea"
                    rows="4"
                    placeholder="例如：这个字段怎么填？轻量和标准有什么区别？"
                    @keydown.enter.exact.prevent="sendSelfFillAssistantMessage()"
                  ></textarea>
                </label>

                <div class="wizard-actions wizard-actions--inline">
                  <button class="ghost-btn" type="button" @click="closeSelfFillAssistantDialog">关闭</button>
                  <button class="primary-btn" type="button" :disabled="selfFillAssistantLoading" @click="sendSelfFillAssistantMessage()">
                    {{ selfFillAssistantLoading ? '发送中...' : '发送' }}
                  </button>
                </div>
              </div>
            </div>

            <div v-if="selfInterviewDialogOpen" class="self-interview-modal" @click.self="closeSelfInterviewDialog">
              <div class="self-interview-modal__panel">
                <div class="self-interview-modal__head">
                  <div>
                    <p class="eyebrow">追问补洞</p>
                    <h3>补全这个关键问题</h3>
                    <p class="section-note section-note--subtle">
                      {{ selfInterviewDialogDimension }} · {{ selfInterviewDialogReason }}
                    </p>
                  </div>
                  <button type="button" class="ghost-button ghost-button--small" @click="closeSelfInterviewDialog">关闭</button>
                </div>

                <div class="form-grid">
                  <label class="form-field">
                    <span>问题</span>
                    <textarea
                      v-model="selfInterviewDialogQuestion"
                      class="field-input wizard-textarea"
                      rows="4"
                      :readonly="selfInterviewDialogKey !== 'custom_question'"
                    ></textarea>
                  </label>
                  <label class="form-field">
                    <span>回答</span>
                    <textarea
                      v-model="selfInterviewDialogAnswer"
                      class="field-input wizard-textarea"
                      rows="4"
                      placeholder="把你的真实回答写下来"
                    ></textarea>
                  </label>
                </div>

                <p v-if="selfInterviewDialogError" class="state-copy state-copy--error">{{ selfInterviewDialogError }}</p>

                <div class="wizard-actions wizard-actions--inline">
                  <button class="ghost-btn" type="button" @click="closeSelfInterviewDialog">取消</button>
                  <button class="primary-btn" type="button" @click="addSelfInterviewEntry">添加</button>
                </div>
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

            <MaterialInputPanel
              v-model="sourceMaterialState"
              path-type="source"
              :supports-guided-prompts="false"
            />
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
                <li><span>照片 / 相册</span><strong>{{ createType === 'reunion_persona' ? (formState.photo_notes || '未填写') : (familyUploadedImageDocuments.length ? `${familyUploadedImageDocuments.length} 张：${familyUploadedImageDocuments.map((item) => item.filename).join(' / ')}` : '未上传') }}</strong></li>
              </ul>
            </div>
          </div>

          <div v-else-if="createType === 'intimate_companion'" class="wizard-form">
            <div class="form-grid">
              <label class="form-field">
                <span>关系类型</span>
                <input v-model="formState.relationship_type" class="field-input" type="text" placeholder="关系经营 / 消息模拟 / 过去关系 / 自我镜像" />
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

            <MaterialInputPanel
              v-model="intimateMaterialState"
              path-type="intimate"
              :supports-guided-prompts="false"
            />

            <label class="form-field">
              <span>边界或禁忌话题</span>
              <textarea v-model="formState.relation_boundaries" class="field-input wizard-textarea" rows="4"></textarea>
            </label>
          </div>

          <div v-else-if="createType === 'reply_assistant'" class="wizard-form">
            <div class="form-grid">
              <label class="form-field">
                <span>人物类型</span>
                <select v-model="formState.target_person_type" class="field-input">
                  <option v-for="[value, label] in replyAssistantTargetTypeOptions" :key="value" :value="value">
                    {{ label }}
                  </option>
                </select>
              </label>
              <label class="form-field">
                <span>对方称呼</span>
                <input v-model="formState.target_person_name" class="field-input" type="text" placeholder="例如：小林 / 甲方 / 妈妈" />
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>当前关系状态</span>
                <textarea
                  v-model="formState.relationship_status"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="例如：暧昧期 / 合作中 / 冷战中 / 日常沟通"
                ></textarea>
              </label>
              <label class="form-field">
                <span>你想达到的目标</span>
                <textarea
                  v-model="formState.reply_goal"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="例如：接住情绪、稳住局面、推进一步、先不激化"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>语气要求</span>
                <textarea
                  v-model="formState.tone"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="例如：自然、克制、清楚、不油腻"
                ></textarea>
              </label>
              <label class="form-field">
                <span>一句话原文</span>
                <textarea
                  v-model="formState.single_message_text"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="把对方原话直接贴进来"
                ></textarea>
              </label>
            </div>

            <div class="form-grid">
              <label class="form-field">
                <span>候选回复风格</span>
                <textarea
                  v-model="formState.reply_style_samples"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="稳妥版 / 自然版 / 主动版 / 克制版"
                ></textarea>
              </label>
              <label class="form-field">
                <span>补充说明</span>
                <textarea
                  v-model="formState.reply_material_notes"
                  class="field-input wizard-textarea"
                  rows="4"
                  placeholder="可以补充聊天记录、文件、图片或 OCR 材料"
                ></textarea>
              </label>
            </div>

            <MaterialInputPanel
              v-model="replyAssistantMaterialState"
              path-type="relationship"
              :supports-guided-prompts="false"
            />

            <label class="form-field">
              <span>人物描述 / 场景补充</span>
              <textarea
                v-model="formState.target_person_description"
                class="field-input wizard-textarea"
                rows="4"
                placeholder="补充对方说话风格、场景、关系变化或雷区"
              ></textarea>
            </label>
          </div>

          <div v-else-if="createType === 'relationship_persona'" class="wizard-form">
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

            <MaterialInputPanel
              v-model="relationshipMaterialState"
              path-type="relationship"
              :supports-guided-prompts="false"
            />
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
              <template v-else-if="createType === 'reply_assistant'">
                <h3>{{ formState.target_person_name || '未填写对方称呼' }}</h3>
                <p class="state-copy">
                  {{ formState.reply_goal || '还没有说明你想达到的目标。' }}
                </p>
                <ul class="summary-panel__list">
                  <li><span>人物类型</span><strong>{{ replyAssistantTargetTypeOptions.find(([value]) => value === formState.target_person_type)?.[1] || formState.target_person_type }}</strong></li>
                  <li><span>关系状态</span><strong>{{ formState.relationship_status || '未填写' }}</strong></li>
                  <li><span>语气要求</span><strong>{{ formState.tone || '未填写' }}</strong></li>
                </ul>
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
  font-size: 0.8rem;
  line-height: 1.45;
}

.inline-actions {
  display: inline-flex;
  justify-content: flex-end;
  align-items: center;
}

.ghost-button {
  border: 1px solid var(--line);
  background: rgba(255, 255, 255, 0.72);
  color: var(--text);
  border-radius: 999px;
  padding: 0.62rem 1rem;
  min-height: 42px;
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
  min-height: 36px;
}

.self-interview-builder {
  display: grid;
  gap: 0.9rem;
  margin-top: 0.85rem;
}

.wizard-form--self-fill {
  gap: 1rem;
}

.self-fill-intro {
  display: grid;
  gap: 0.8rem;
}

.self-fill-prep-list {
  margin: 0.2rem 0 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.35rem;
  color: var(--muted);
}

.self-fill-layout {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
  gap: 1rem;
  align-items: start;
}

.self-fill-rail {
  display: grid;
  gap: 0.6rem;
  position: sticky;
  top: 1rem;
}

.self-fill-rail__button {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 0.7rem;
  align-items: start;
  width: 100%;
  text-align: left;
  padding: 0.9rem 1rem;
  border-radius: 1rem;
  border: 1px solid rgba(255, 159, 138, 0.12);
  background: rgba(255, 255, 255, 0.72);
  cursor: pointer;
  transition:
    transform 0.18s ease,
    border-color 0.18s ease,
    box-shadow 0.18s ease,
    background 0.18s ease;
}

.self-fill-rail__button:hover {
  transform: translateY(-1px);
  border-color: rgba(255, 159, 138, 0.32);
  box-shadow: 0 16px 32px rgba(255, 159, 138, 0.08);
}

.self-fill-rail__button.active {
  border-color: rgba(255, 159, 138, 0.55);
  background: rgba(255, 247, 244, 0.96);
}

.self-fill-rail__button.completed {
  border-color: rgba(120, 194, 173, 0.22);
}

.self-fill-rail__button.helper {
  background: rgba(245, 248, 255, 0.9);
}

.self-fill-rail__index {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 2.4rem;
  min-height: 2.4rem;
  border-radius: 999px;
  background: rgba(255, 159, 138, 0.12);
  color: var(--accent);
  font-size: 0.82rem;
  font-weight: 700;
}

.self-fill-rail__body {
  display: grid;
  gap: 0.18rem;
}

.self-fill-rail__body strong {
  font-size: 0.95rem;
}

.self-fill-rail__body small {
  color: var(--muted);
  line-height: 1.45;
}

.self-fill-page {
  display: grid;
  gap: 1rem;
}

.self-fill-page__head {
  margin-bottom: -0.1rem;
}

.self-fill-page__summary {
  display: grid;
  gap: 0.45rem;
}

.self-fill-page__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  align-items: center;
}

.primary-btn--small {
  min-height: 40px;
  padding: 0.64rem 1rem;
}

.self-fill-page__content {
  display: grid;
  gap: 0.9rem;
}

.self-fill-more {
  border: 1px dashed rgba(255, 159, 138, 0.18);
  border-radius: 1rem;
  padding: 0.85rem 0.95rem;
  background: rgba(255, 255, 255, 0.54);
}

.self-fill-more > summary {
  cursor: pointer;
  color: var(--accent);
  font-weight: 700;
  margin-bottom: 0.8rem;
}

.self-fill-review-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.self-fill-review-card {
  display: grid;
  gap: 0.55rem;
  padding: 1rem;
  border: 1px solid rgba(255, 159, 138, 0.12);
  border-radius: 1.15rem;
  background: rgba(255, 255, 255, 0.76);
}

.self-fill-review-card__head {
  display: flex;
  justify-content: space-between;
  gap: 0.9rem;
  align-items: start;
}

.self-fill-review-card__label {
  margin: 0 0 0.35rem;
  font-size: 0.8rem;
  color: var(--muted);
}

.self-fill-review-card h4 {
  margin: 0;
  font-size: 1rem;
  line-height: 1.55;
}

.self-fill-review-card__meta {
  margin: 0;
  color: var(--muted);
  font-size: 0.88rem;
}

.self-fill-assistant-panel--inline {
  margin-top: 0.25rem;
}

.self-interview-builder__select {
  width: 100%;
}

.self-interview-builder__status {
  display: grid;
  gap: 0.25rem;
  padding: 0.85rem 0.95rem;
  border: 1px solid rgba(255, 159, 138, 0.18);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.72);
  color: var(--muted);
  line-height: 1.55;
}

.self-interview-builder__status strong {
  color: var(--text);
}

.self-interview-builder__list {
  display: grid;
  gap: 0.75rem;
}

.self-interview-builder__item {
  display: grid;
  gap: 0.65rem;
  padding: 0.95rem 1rem;
  border: 1px solid var(--line);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.8);
}

.self-interview-builder__item-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.self-interview-builder__item-dimension {
  margin: 0 0 0.22rem;
  color: var(--accent);
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.self-interview-builder__item-head h4 {
  margin: 0;
  font-size: 1rem;
  line-height: 1.4;
}

.self-interview-builder__item-actions {
  display: inline-flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.self-interview-builder__item-answer {
  margin: 0;
  color: var(--text);
  line-height: 1.65;
  white-space: pre-wrap;
}

.self-fill-assistant-panel {
  gap: 0.9rem;
}

.self-fill-assistant-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.self-fill-assistant-panel__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.self-fill-assistant-panel__chips--modal {
  margin-top: -0.1rem;
}

.self-fill-assistant-modal {
  position: fixed;
  inset: 0;
  z-index: 60;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.2rem;
  background: rgba(18, 24, 31, 0.54);
  backdrop-filter: blur(10px);
}

.self-fill-assistant-modal__panel {
  width: min(920px, 100%);
  max-height: min(90vh, 920px);
  overflow: auto;
  display: grid;
  gap: 0.95rem;
  padding: 1.25rem;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98), rgba(255, 248, 244, 0.99));
  box-shadow: 0 30px 90px rgba(37, 28, 22, 0.28);
}

.self-fill-assistant-modal__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.self-fill-assistant-chat {
  display: grid;
  gap: 0.75rem;
  max-height: 42vh;
  overflow: auto;
  padding-right: 0.15rem;
}

.self-fill-assistant-chat__message {
  display: grid;
  gap: 0.38rem;
  max-width: 88%;
  padding: 0.9rem 1rem;
  border-radius: 18px;
  line-height: 1.65;
  white-space: pre-wrap;
  border: 1px solid var(--line);
}

.self-fill-assistant-chat__message p {
  margin: 0;
}

.self-fill-assistant-chat__message--assistant {
  justify-self: start;
  background: rgba(255, 255, 255, 0.9);
}

.self-fill-assistant-chat__message--user {
  justify-self: end;
  background: rgba(255, 159, 138, 0.12);
  border-color: rgba(255, 159, 138, 0.2);
}

.self-fill-assistant-chat__role {
  color: var(--accent);
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.self-interview-modal {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.2rem;
  background: rgba(18, 24, 31, 0.54);
  backdrop-filter: blur(10px);
}

.self-interview-modal__panel {
  width: min(880px, 100%);
  max-height: min(88vh, 900px);
  overflow: auto;
  display: grid;
  gap: 1rem;
  padding: 1.25rem;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(255, 248, 244, 0.98));
  box-shadow: 0 30px 90px rgba(37, 28, 22, 0.26);
}

.self-interview-modal__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
}

.wizard-actions--inline {
  justify-content: flex-end;
}

.state-copy--error {
  color: #c45849;
}

.state-copy--muted {
  color: var(--muted);
}

@media (max-width: 640px) {
  .inline-meta {
    margin-top: 0.1rem;
    display: inline-block;
  }

  .inline-actions {
    width: 100%;
    justify-content: flex-start;
  }

  .ghost-button {
    width: 100%;
  }

  .ghost-button--small {
    width: auto;
  }

  .self-interview-builder__item-head,
  .self-interview-modal__head {
    flex-direction: column;
  }

  .self-fill-assistant-panel__head,
  .self-fill-assistant-modal__head {
    flex-direction: column;
  }

  .self-interview-builder__item-actions,
  .wizard-actions--inline {
    width: 100%;
    justify-content: flex-start;
  }

  .self-fill-assistant-panel__chips {
    width: 100%;
  }

  .self-fill-assistant-chat__message {
    max-width: 100%;
  }

  .self-interview-modal {
    padding: 0.65rem;
  }

  .self-interview-modal__panel {
    max-height: 94vh;
    padding: 1rem;
    border-radius: 22px;
  }

  .self-fill-assistant-modal {
    padding: 0.65rem;
  }

  .self-fill-assistant-modal__panel {
    max-height: 94vh;
    padding: 1rem;
    border-radius: 22px;
  }
}

@media (max-width: 1120px) {
  .self-fill-layout {
    grid-template-columns: 1fr;
  }

  .self-fill-rail {
    position: static;
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .self-fill-rail {
    grid-template-columns: 1fr;
  }

  .self-fill-review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
