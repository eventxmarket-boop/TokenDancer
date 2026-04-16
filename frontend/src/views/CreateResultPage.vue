<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  loadLatestDraft,
  saveDraftLocally,
  saveLatestDraft,
  type CreateWizardDraft,
  type FamilyCompanionMemoryBase,
  type FamilyCompanionGuidedMemoryAnswers,
  type FamilyCompanionEmotionRules,
  type FamilyCompanionPersonaProfile,
  type IntimateCompanionMemoryBase,
  type IntimateCompanionRelationshipProfile,
  type ReunionPersonaMemoryBase,
  type ReunionPersonaProfile,
  type ReunionPersonaRetrievalPolicy,
  type ReunionPersonaSafetyGuardrails,
  type SelfPersonaUnifiedDraft,
} from '@/services/createWizardService'
import {
  loadMySeed,
  saveMySeed,
  type CreatedPersonaRecord,
} from '@/services/createdPersonaService'
import { isLoggedIn } from '@/stores/auth'

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

const familySubtypeLabels: Record<string, string> = {
  mother: '妈妈',
  parents: '父母',
  other_family: '其他家人',
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
    create_mode: '',
    input_mode: '',
    family_subtype: '',
    input_modes: [],
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
  raw_materials: null,
  emotion_rules: null,
  guided_memory_answers: null,
  self_persona_unified: {
    create_mode: 'standard',
    input_modes: [],
    work_system: { summary: '', points: [] },
    reply_persona: { summary: '', points: [] },
    thinking_dna: { summary: '', points: [] },
    memory_evidence: { summary: '', points: [] },
    reflection_rules: { summary: '', points: [] },
  },
  persona_profile: null,
  memory_base: null,
  reunion_persona_profile: null,
  reunion_memory_base: null,
  reunion_memory_retrieval_policy: null,
  reunion_safety_guardrails: null,
  relationship_profile: null,
  intimate_memory_base: null,
})

const typeLabel = computed(() => {
  if (!draft.value) {
    return '人格雏形'
  }

  const type = draft.value.meta.create_type
  if (type === 'self_unified') {
    return '自我主线'
  }
  if (type === 'source_persona') {
    return '从资料创建'
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
})

const displayDraftName = computed(() => {
  const name = normalizeText(editableDraft.meta.name)
  if (draft.value?.meta.create_type === 'self_unified' && (!name || name === '我的人格')) {
    return '自我主线'
  }
  return name
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
  const payload = editableDraft.persona_profile || draft.value?.persona_profile
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const familySubtypeLabel = computed(() => {
  const subtype = normalizeText(
    (draft.value as Record<string, unknown> | null)?.family_subtype ||
      (draft.value?.meta as Record<string, unknown> | undefined)?.family_subtype ||
      (editableDraft as Record<string, unknown>)?.family_subtype,
  )
  if (subtype) {
    return familySubtypeLabels[subtype] || subtype
  }
  const relationshipType = normalizeText(familyPersonaProfile.value?.relationship_type)
  if (relationshipType) {
    if (relationshipType.includes('妈')) {
      return '妈妈'
    }
    if (relationshipType.includes('父')) {
      return '父母'
    }
    if (relationshipType.includes('家')) {
      return '其他家人'
    }
  }
  return ''
})

function normalizeText(value: unknown) {
  return String(value || '').replace(/\s+/g, ' ').trim()
}

function excerptText(value: unknown, limit = 48) {
  const text = normalizeText(value)
  return text ? text.slice(0, limit) : ''
}

function normalizeDocuments(value: unknown) {
  if (!Array.isArray(value)) {
    return []
  }
  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null
      }
      const record = item as Record<string, unknown>
      const filename = normalizeText(record.filename || record.name)
      const content = normalizeText(record.content || record.text || record.body)
      return filename || content ? { filename, content } : null
    })
    .filter(Boolean) as Array<{ filename: string; content: string }>
}

function normalizeImageDocuments(value: unknown) {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null
      }
      const record = item as Record<string, unknown>
      const filename = normalizeText(record.filename || record.name)
      const mimeType = normalizeText(record.mime_type || record.type)
      const size = Number(record.size || 0)
      const ocrStatus = normalizeText(record.ocr_status || record.status)
      const ocrText = normalizeText(record.ocr_text || record.text || record.content)
      return filename || mimeType || size || ocrStatus || ocrText
        ? { filename, mimeType, size, ocrStatus, ocrText }
        : null
    })
    .filter(Boolean) as Array<{ filename: string; mimeType: string; size: number; ocrStatus: string; ocrText: string }>
}

function normalizeOcrResults(value: unknown) {
  if (!Array.isArray(value)) {
    return []
  }

  return value
    .map((item) => {
      if (!item || typeof item !== 'object') {
        return null
      }
      const record = item as Record<string, unknown>
      const filename = normalizeText(record.filename || record.name)
      const mimeType = normalizeText(record.mime_type || record.type)
      const size = Number(record.size || 0)
      const ocrStatus = normalizeText(record.ocr_status || record.status) || 'failed'
      const ocrText = normalizeText(record.ocr_text || record.text || record.content)
      return filename || mimeType || size || ocrStatus || ocrText
        ? { filename, mimeType, size, ocrStatus, ocrText }
        : null
    })
    .filter(Boolean) as Array<{ filename: string; mimeType: string; size: number; ocrStatus: string; ocrText: string }>
}

function normalizeStringList(value: unknown) {
  if (Array.isArray(value)) {
    return value.map((item) => normalizeText(item)).filter(Boolean)
  }
  if (typeof value === 'string') {
    return value
      .split(/\n+/)
      .map((item) => item.trim())
      .filter(Boolean)
  }
  return []
}

function normalizeStringMap(value: unknown) {
  if (!value || typeof value !== 'object') {
    return []
  }
  return Object.entries(value as Record<string, unknown>)
    .map(([key, item]) => {
      const normalized = normalizeText(item)
      return normalized ? `${key}：${normalized}` : ''
    })
    .filter(Boolean)
}

function buildMaterialLines(rawMaterials: unknown, mode: 'family' | 'reunion' | 'intimate') {
  if (!rawMaterials || typeof rawMaterials !== 'object') {
    return []
  }

  const record = rawMaterials as Record<string, unknown>
  if (mode === 'family') {
    const documents = normalizeDocuments(record.uploaded_text_documents)
    return [
      { label: '聊天记录摘要', value: excerptText(record.chat_history_text) || '未填写' },
      { label: '回忆笔记摘要', value: excerptText(record.memory_notes_text) || '未填写' },
      { label: '文本材料摘要', value: excerptText(record.text_materials_text) || '未填写' },
      {
        label: '已上传材料文件数',
        value: documents.length ? `${documents.length} 个` : '0 个',
      },
      { label: '图片说明摘要', value: excerptText(record.image_notes_text) || '未填写' },
      { label: '语音说明摘要', value: excerptText(record.voice_notes_text) || '未填写' },
    ]
  }

  if (mode === 'intimate') {
    const documents = normalizeDocuments(record.uploaded_text_documents)
    return [
      { label: '聊天记录', value: excerptText(record.chat_history_text) || '未填写' },
      { label: '消息样本', value: excerptText(record.draft_message_text) || '未填写' },
      { label: '关系片段', value: excerptText(record.memory_notes_text) || '未填写' },
      { label: '文本材料', value: excerptText(record.text_materials_text) || '未填写' },
      {
        label: '上传文件',
        value: documents.length ? documents.map((item) => item.filename).join(' / ') : '未上传',
      },
      { label: '图片备注', value: excerptText(record.image_notes_text) || '未填写' },
      { label: '语音备注', value: excerptText(record.voice_notes_text) || '未填写' },
    ]
  }

  const documents = normalizeDocuments(record.uploaded_text_documents)
  return [
    { label: '聊天记录', value: excerptText(record.chat_history_text) || '未填写' },
    { label: '日记 / 信件', value: excerptText(record.diary_text) || '未填写' },
    { label: '书信文本', value: excerptText(record.letter_text) || '未填写' },
    {
      label: '上传文件',
      value: documents.length ? documents.map((item) => item.filename).join(' / ') : '未上传',
    },
    { label: '照片备注', value: excerptText(record.photo_notes_text) || '未填写' },
    { label: '语音备注', value: excerptText(record.voice_notes_text) || '未填写' },
  ]
}

const familyRawMaterials = computed(() => {
  const payload = editableDraft.raw_materials || draft.value?.raw_materials
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const familyGuidedAnswers = computed<FamilyCompanionGuidedMemoryAnswers | null>(() => {
  const payload = editableDraft.guided_memory_answers || draft.value?.guided_memory_answers
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const familyMaterialSummaryLines = computed(() => {
  const profile = familyPersonaProfile.value
  const memory = familyMemoryBase.value
  const rawMaterials = familyRawMaterials.value
  const guidedAnswers = familyGuidedAnswers.value
  const documents = normalizeDocuments((rawMaterials as Record<string, unknown> | null)?.uploaded_text_documents)
  const imageDocuments = normalizeImageDocuments((rawMaterials as Record<string, unknown> | null)?.uploaded_image_documents)
  const ocrResults = normalizeOcrResults((rawMaterials as Record<string, unknown> | null)?.ocr_extracted_texts)
  const ocrSuccessCount = ocrResults.filter((item) => ['success', 'partial'].includes(item.ocrStatus) && item.ocrText).length
  const ocrFailedCount = ocrResults.filter((item) => !['success', 'partial'].includes(item.ocrStatus) || !item.ocrText).length
  const ocrSnippet = ocrResults.find((item) => ['success', 'partial'].includes(item.ocrStatus) && item.ocrText)?.ocrText || ''
  return [
    {
      label: '子类型侧重',
      value:
        familySubtypeLabel.value ||
        (normalizeText((draft.value as Record<string, unknown> | null)?.family_subtype) || '妈妈'),
    },
    {
      label: '聊天记录摘要',
      value:
        memory?.chat_history_summary ||
        excerptText((rawMaterials as Record<string, unknown> | null)?.chat_history_text) ||
        '未填写',
    },
    {
      label: '共同经历摘要',
      value:
        memory?.episodic_memories?.join(' / ') ||
        memory?.shared_events?.join(' / ') ||
        '未填写',
    },
    {
      label: '稳定认知摘要',
      value:
        memory?.semantic_memories?.join(' / ') ||
        memory?.important_advice?.join(' / ') ||
        '未填写',
    },
    {
      label: '说话 / 安慰习惯',
      value:
        memory?.procedural_memories?.join(' / ') ||
        profile?.comfort_style ||
        '未填写',
    },
    {
      label: '常说的话摘要',
      value: profile?.catchphrases?.join(' / ') || memory?.important_advice?.join(' / ') || '未填写',
    },
    {
      label: '引导补充',
      value:
        guidedAnswers
          ? (() => {
              const items = [
                guidedAnswers.most_common_topics,
                guidedAnswers.comfort_style,
                guidedAnswers.most_characteristic_event,
                guidedAnswers.repeated_phrases,
                guidedAnswers.care_habits,
                guidedAnswers.most_common_reminders,
              ]
                .map((item) => normalizeText(item))
                .filter(Boolean)
              return items.length ? `${items.length} 项 / ${items[0]}` : '已参与'
            })()
          : '未填写',
    },
    {
      label: '已上传材料文件数',
      value: documents.length ? `${documents.length} 个` : '0 个',
    },
    {
      label: '已上传图片数',
      value: imageDocuments.length ? `${imageDocuments.length} 张` : '0 张',
    },
    {
      label: '已识别图片数',
      value: ocrSuccessCount ? `${ocrSuccessCount} 张${ocrFailedCount ? ` / ${ocrFailedCount} 张未识别` : ''}` : '0 张',
    },
    {
      label: 'OCR 提取摘要',
      value: ocrSnippet ? ocrSnippet.slice(0, 60) : '未提取到可用文本',
    },
    {
      label: '图片说明',
      value:
        excerptText((rawMaterials as Record<string, unknown> | null)?.image_notes_text) ||
        excerptText((rawMaterials as Record<string, unknown> | null)?.photo_notes_text) ||
        '未填写',
    },
  ]
})

const reunionRawMaterials = computed(() => {
  const payload = editableDraft.raw_materials || draft.value?.raw_materials
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const reunionMaterialLines = computed(() => buildMaterialLines(reunionRawMaterials.value, 'reunion'))

const intimateRawMaterials = computed(() => {
  const payload = editableDraft.raw_materials || draft.value?.raw_materials
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const intimateMaterialLines = computed(() => buildMaterialLines(intimateRawMaterials.value, 'intimate'))

const familyMemoryBase = computed<FamilyCompanionMemoryBase | null>(() => {
  const payload = editableDraft.memory_base || draft.value?.memory_base
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const familyEmotionRules = computed<FamilyCompanionEmotionRules | null>(() => {
  const payload = editableDraft.emotion_rules || draft.value?.emotion_rules
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload as FamilyCompanionEmotionRules
})

const intimateRelationshipProfile = computed<IntimateCompanionRelationshipProfile | null>(() => {
  const payload = editableDraft.relationship_profile || draft.value?.relationship_profile
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const intimateMemoryBase = computed<IntimateCompanionMemoryBase | null>(() => {
  const payload = editableDraft.intimate_memory_base || draft.value?.intimate_memory_base
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
    { label: '共同经历（episodic）', value: memory.episodic_memories?.join(' / ') || memory.shared_events?.join(' / ') || '未填写' },
    { label: '稳定认知（semantic）', value: memory.semantic_memories?.join(' / ') || memory.important_advice?.join(' / ') || '未填写' },
    { label: '说话 / 安慰习惯（procedural）', value: memory.procedural_memories?.join(' / ') || memory.daily_habits?.join(' / ') || '未填写' },
    { label: '旧版摘要', value: memory.legacy_summary?.join(' / ') || memory.chat_history_summary || '未填写' },
  ]
})

const familyEmotionLines = computed(() => {
  const rules = familyEmotionRules.value
  if (!rules) {
    return []
  }

  return [
    { label: '规则摘要', value: rules.summary || '未填写' },
    { label: '情绪优先级', value: normalizeStringList(rules.emotion_state_priority).join(' / ') || '未填写' },
    { label: '回复顺序', value: normalizeStringList(rules.response_sequence).join(' / ') || '未填写' },
    { label: '记忆优先级', value: normalizeStringList(rules.memory_priority_rules).join(' / ') || '未填写' },
    { label: '边界规则', value: normalizeStringList(rules.boundary_rules).join(' / ') || '未填写' },
    { label: '温度映射', value: normalizeStringMap(rules.response_temperature_map).join(' / ') || '未填写' },
  ]
})

const reunionPersonaProfile = computed<ReunionPersonaProfile | null>(() => {
  const payload = editableDraft.reunion_persona_profile || draft.value?.reunion_persona_profile
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const reunionMemoryBase = computed<ReunionPersonaMemoryBase | null>(() => {
  const payload = editableDraft.reunion_memory_base || draft.value?.reunion_memory_base
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const reunionRetrievalPolicy = computed<ReunionPersonaRetrievalPolicy | null>(() => {
  const payload = editableDraft.reunion_memory_retrieval_policy || draft.value?.reunion_memory_retrieval_policy
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const reunionSafetyGuardrails = computed<ReunionPersonaSafetyGuardrails | null>(() => {
  const payload = editableDraft.reunion_safety_guardrails || draft.value?.reunion_safety_guardrails
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const reunionProfileLines = computed(() => {
  const profile = reunionPersonaProfile.value
  if (!profile) {
    return []
  }

  return [
    { label: '关系类型', value: profile.relationship_type || '未填写' },
    { label: '称呼', value: profile.name || '未填写' },
    { label: '说话风格', value: profile.tone || '未填写' },
    { label: '回忆方式', value: profile.remembrance_style || '未填写' },
    { label: '安抚方式', value: profile.comfort_style || '未填写' },
    { label: '边界', value: profile.boundaries || '未填写' },
  ]
})

const reunionMemoryLines = computed(() => {
  const memory = reunionMemoryBase.value
  if (!memory) {
    return []
  }

  const policy = reunionRetrievalPolicy.value
  const safety = reunionSafetyGuardrails.value

  return [
    { label: '聊天摘要', value: memory.chat_history_summary || '未填写' },
    { label: '日记 / 信件', value: memory.diary_notes?.join(' / ') || '未填写' },
    { label: '书信文本', value: memory.letter_notes?.join(' / ') || '未填写' },
    { label: '照片备注', value: memory.photo_notes?.join(' / ') || '未填写' },
    { label: '语音备注', value: memory.voice_notes?.join(' / ') || '未填写' },
    { label: '记忆片段', value: memory.memory_fragments?.join(' / ') || '未填写' },
    { label: '共同记忆', value: memory.shared_memories?.join(' / ') || '未填写' },
    { label: '检索模式', value: policy?.mode || '未填写' },
    { label: '优先规则', value: policy?.priority_rules?.join(' / ') || '未填写' },
    { label: '安全护栏', value: safety?.emotional_protection?.join(' / ') || '未填写' },
  ]
})

const selfUnifiedDraft = computed<SelfPersonaUnifiedDraft | null>(() => {
  const payload = editableDraft.self_persona_unified || draft.value?.self_persona_unified
  if (!payload || typeof payload !== 'object') {
    return null
  }
  return payload
})

const selfUnifiedLayers = computed(() => {
  const unified = selfUnifiedDraft.value
  if (!unified) {
    return []
  }

  return [
    {
      title: '做事方式',
      summary: unified.work_system?.summary || '',
      points: unified.work_system?.points || [],
    },
    {
      title: '回复方式',
      summary: unified.reply_persona?.summary || '',
      points: unified.reply_persona?.points || [],
    },
    {
      title: '思考方式',
      summary: unified.thinking_dna?.summary || '',
      points: unified.thinking_dna?.points || [],
    },
    {
      title: '生活痕迹',
      summary: unified.memory_evidence?.summary || '',
      points: unified.memory_evidence?.points || [],
    },
    {
      title: '反思规则',
      summary: unified.reflection_rules?.summary || '',
      points: unified.reflection_rules?.points || [],
    },
  ]
})

type SelfUnifiedLayerKey = 'work_system' | 'reply_persona' | 'thinking_dna' | 'memory_evidence' | 'reflection_rules'

function ensureSelfUnifiedDraft() {
  if (!editableDraft.self_persona_unified) {
    editableDraft.self_persona_unified = {
      create_mode: 'standard',
      input_modes: [],
      work_system: { summary: '', points: [] },
      reply_persona: { summary: '', points: [] },
      thinking_dna: { summary: '', points: [] },
      memory_evidence: { summary: '', points: [] },
      reflection_rules: { summary: '', points: [] },
    }
  }
  return editableDraft.self_persona_unified
}

function getUnifiedLayerSummary(layer: SelfUnifiedLayerKey) {
  return ensureSelfUnifiedDraft()[layer].summary || ''
}

function getUnifiedLayerPointsText(layer: SelfUnifiedLayerKey) {
  return ensureSelfUnifiedDraft()[layer].points.join('\n')
}

function updateUnifiedLayerSummary(layer: SelfUnifiedLayerKey, value: string) {
  ensureSelfUnifiedDraft()[layer].summary = value
}

function updateUnifiedLayerPoints(layer: SelfUnifiedLayerKey, value: string) {
  ensureSelfUnifiedDraft()[layer].points = value
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean)
}

function handleUnifiedLayerSummaryInput(layer: SelfUnifiedLayerKey, event: Event) {
  const target = event.target as HTMLTextAreaElement | null
  updateUnifiedLayerSummary(layer, target?.value || '')
}

function handleUnifiedLayerPointsInput(layer: SelfUnifiedLayerKey, event: Event) {
  const target = event.target as HTMLTextAreaElement | null
  updateUnifiedLayerPoints(layer, target?.value || '')
}

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
  if (
    snapshot.meta.create_type === 'self_unified' &&
    (!String(snapshot.meta.name || '').trim() || String(snapshot.meta.name || '').trim() === '我的人格')
  ) {
    snapshot.meta.name = '自我主线'
    snapshot.meta.display_name = '自我主线'
  }
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
  if (!isLoggedIn.value) {
    persistEditedDraft()
    notice.value = '请先登录后再保存到“我创建的 Seed”'
    await router.push({ path: '/login', query: { redirect: route.fullPath } })
    return
  }

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

function isAuthRequiredError(message: string) {
  const normalized = message.toLowerCase()
  return (
    normalized.includes('认证') ||
    normalized.includes('token') ||
    normalized.includes('登录') ||
    normalized.includes('authorization')
  )
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
    try {
      const restored = await loadFromSeed(querySeedId)
      if (restored) {
        loading.value = false
        return
      }
    } catch (cause) {
      const message = cause instanceof Error ? cause.message : ''
      if (isAuthRequiredError(message)) {
        await router.push({ path: '/login', query: { redirect: route.fullPath } })
        return
      }
      notice.value = message || '加载保存结果失败'
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
  <section class="page-hero page-hero--single wizard-hero">
    <div class="hero-copy">
      <p class="eyebrow">创建结果</p>
      <h1>你的人格雏形已经生成。</h1>

      <div class="hero-metrics">
        <span class="metric-chip"><strong>{{ typeLabel }}</strong><span>人格类型</span></span>
        <span v-if="draft?.meta.create_type === 'family_companion' && familySubtypeLabel" class="metric-chip">
          <strong>{{ familySubtypeLabel }}</strong><span>家人子类型</span>
        </span>
        <span class="metric-chip"><strong>{{ displayDraftName || '未命名' }}</strong><span>结果名称</span></span>
        <span class="metric-chip"><strong>{{ savedSeedLabel }}</strong><span>保存状态</span></span>
      </div>

      <div class="hero-actions">
        <button class="primary-btn" type="button" :disabled="saving" @click="saveDraft">
          {{ saving ? '保存中…' : createdSeedId ? '保存更新' : '保存到我的 Seed' }}
        </button>
        <button class="secondary-btn" type="button" @click="backToWizard">返回修改</button>
      </div>

      <p v-if="notice" class="persona-hero-note">{{ notice }}</p>
      <p v-if="draft?.raw_materials" class="persona-hero-note">已基于输入材料生成记忆库。</p>

      <div v-if="createdSeedId || createdSeed" class="hero-actions hero-actions--wrap">
        <button class="secondary-btn" type="button" @click="goToMySeeds">去我的 Seed</button>
        <button class="secondary-btn" type="button" @click="startChat">开始对话</button>
        <button class="secondary-btn" type="button" @click="continueEditing">继续编辑</button>
      </div>
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
              <h3>{{ displayDraftName }}</h3>
            </div>
            <span class="status-pill">{{ typeLabel }}</span>
          </div>
          <p class="state-copy">{{ inputModeLabel }} · {{ editableDraft.meta.generated_at }}</p>
        </article>

        <article v-if="draft?.meta.create_type === 'self_unified'" class="draft-card">
          <p class="eyebrow">五层结构</p>
          <div class="self-unified-grid">
            <div v-for="layer in selfUnifiedLayers" :key="layer.title" class="self-unified-grid__item">
              <span>{{ layer.title }}</span>
              <strong>{{ layer.summary || '未填写' }}</strong>
              <p v-if="layer.points.length" class="self-unified-grid__copy">
                {{ layer.points.join(' / ') }}
              </p>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'family_companion'" class="draft-card">
          <p class="eyebrow">人格层 · {{ familySubtypeLabel || '妈妈' }}</p>
          <div class="family-grid">
            <div v-for="line in familyProfileLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'family_companion'" class="draft-card">
          <p class="eyebrow">记忆层 · {{ familySubtypeLabel || '妈妈' }}</p>
          <div class="family-grid">
            <div v-for="line in familyMemoryLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'family_companion'" class="draft-card">
          <p class="eyebrow">情绪规则 · {{ familySubtypeLabel || '妈妈' }}</p>
          <div class="family-grid">
            <div v-for="line in familyEmotionLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'family_companion'" class="draft-card">
          <p class="eyebrow">材料提炼摘要 · {{ familySubtypeLabel || '妈妈' }}</p>
          <h3>已基于输入材料生成记忆库</h3>
          <p class="state-copy">系统已经把聊天记录、回忆笔记、文本材料和上传文件提炼成可继续聊天的记忆层。</p>
          <div class="family-grid">
            <div v-for="line in familyMaterialSummaryLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'reunion_persona'" class="draft-card">
          <p class="eyebrow">人格层</p>
          <div class="family-grid">
            <div v-for="line in reunionProfileLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'reunion_persona'" class="draft-card">
          <p class="eyebrow">记忆层</p>
          <div class="family-grid">
            <div v-for="line in reunionMemoryLines" :key="line.label" class="family-grid__item">
              <span>{{ line.label }}</span>
              <strong>{{ line.value }}</strong>
            </div>
          </div>
        </article>

        <article v-if="draft?.meta.create_type === 'reunion_persona'" class="draft-card">
          <p class="eyebrow">材料输入层</p>
          <h3>已基于输入材料生成记忆库</h3>
          <div class="family-grid">
            <div v-for="line in reunionMaterialLines" :key="line.label" class="family-grid__item">
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

        <article v-if="draft?.meta.create_type === 'intimate_companion'" class="draft-card">
          <p class="eyebrow">材料输入层</p>
          <h3>已基于输入材料生成结构化结果</h3>
          <div class="family-grid">
            <div v-for="line in intimateMaterialLines" :key="line.label" class="family-grid__item">
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
          <template v-if="draft?.meta.create_type === 'self_unified'">
            <label class="form-field">
              <span>做事方式</span>
              <textarea
                :value="getUnifiedLayerSummary('work_system')"
                class="field-input wizard-textarea"
                rows="4"
                @input="handleUnifiedLayerSummaryInput('work_system', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>做事方式要点</span>
              <textarea
                :value="getUnifiedLayerPointsText('work_system')"
                class="field-input wizard-textarea"
                rows="4"
                placeholder="每行一条"
                @input="handleUnifiedLayerPointsInput('work_system', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>回复方式</span>
              <textarea
                :value="getUnifiedLayerSummary('reply_persona')"
                class="field-input wizard-textarea"
                rows="4"
                @input="handleUnifiedLayerSummaryInput('reply_persona', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>回复方式要点</span>
              <textarea
                :value="getUnifiedLayerPointsText('reply_persona')"
                class="field-input wizard-textarea"
                rows="4"
                placeholder="每行一条"
                @input="handleUnifiedLayerPointsInput('reply_persona', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>思考方式</span>
              <textarea
                :value="getUnifiedLayerSummary('thinking_dna')"
                class="field-input wizard-textarea"
                rows="4"
                @input="handleUnifiedLayerSummaryInput('thinking_dna', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>思考方式要点</span>
              <textarea
                :value="getUnifiedLayerPointsText('thinking_dna')"
                class="field-input wizard-textarea"
                rows="4"
                placeholder="每行一条"
                @input="handleUnifiedLayerPointsInput('thinking_dna', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>生活痕迹</span>
              <textarea
                :value="getUnifiedLayerSummary('memory_evidence')"
                class="field-input wizard-textarea"
                rows="4"
                @input="handleUnifiedLayerSummaryInput('memory_evidence', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>生活痕迹要点</span>
              <textarea
                :value="getUnifiedLayerPointsText('memory_evidence')"
                class="field-input wizard-textarea"
                rows="4"
                placeholder="每行一条"
                @input="handleUnifiedLayerPointsInput('memory_evidence', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>反思规则</span>
              <textarea
                :value="getUnifiedLayerSummary('reflection_rules')"
                class="field-input wizard-textarea"
                rows="4"
                @input="handleUnifiedLayerSummaryInput('reflection_rules', $event)"
              ></textarea>
            </label>
            <label class="form-field">
              <span>反思规则要点</span>
              <textarea
                :value="getUnifiedLayerPointsText('reflection_rules')"
                class="field-input wizard-textarea"
                rows="4"
                placeholder="每行一条"
                @input="handleUnifiedLayerPointsInput('reflection_rules', $event)"
              ></textarea>
            </label>
          </template>
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
