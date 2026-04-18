<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { requestReplyAssistant, type ReplyAssistantResponse } from '@/services/replyAssistantService'
import type {
  TextMaterialDocument,
  UniversalCreateWizardRawMaterials,
} from '@/services/createWizardService'

type ReplyAssistantTargetType =
  | 'crush'
  | 'partner'
  | 'ex'
  | 'colleague'
  | 'boss'
  | 'client'
  | 'public_sector'
  | 'mentor'
  | 'friend'
  | 'family'

type ReplyAssistantSceneType =
  | 'daily'
  | 'conflict'
  | 'push_forward'
  | 'work_report'
  | 'follow_up'
  | 'formal_notice'
  | 'rejection'
  | 'repair'

type RewriteMode = 'alt' | 'soft' | 'boundary' | 'formal' | 'short'

type ThreadTurn = {
  id: string
  role: 'user' | 'assistant'
  prompt?: string
  result?: ReplyAssistantResponse | null
  content: string
  mode?: RewriteMode | 'default'
}

type ReplyAssistantHistoryRecord = {
  id: string
  title: string
  pinned: boolean
  createdAt: string
  updatedAt: string
  turns: ThreadTurn[]
  draft: string
  form: {
    message: string
    target_person_type: ReplyAssistantTargetType
    scene_type: ReplyAssistantSceneType
    target_goal: string
  }
  contextFields: {
    before_chat: string
    recent_state: string
    before_after: string
  }
  rawMaterials: UniversalCreateWizardRawMaterials
}

const targetPersonOptions: Array<[ReplyAssistantTargetType, string]> = [
  ['crush', '暧昧对象'],
  ['partner', '伴侣'],
  ['ex', '前任'],
  ['colleague', '同事'],
  ['boss', '上司 / 领导'],
  ['client', '客户 / 对接方'],
  ['public_sector', '体制内 / 公务沟通'],
  ['mentor', '导师 / 前辈'],
  ['friend', '朋友'],
  ['family', '家人'],
]

const sceneOptions: Array<[ReplyAssistantSceneType, string, string]> = [
  ['daily', '日常聊天', '普通消息、寒暄、接话。'],
  ['conflict', '冷战 / 冲突', '有情绪、有摩擦、需要缓和。'],
  ['push_forward', '推进关系', '想往前一步，但要控制节奏。'],
  ['work_report', '工作汇报', '汇报进度、同步结果、说明情况。'],
  ['follow_up', '跟进未回复', '催进度或提醒对方查看。'],
  ['formal_notice', '正式通知', '正式告知、邮件、公告、流程性回复。'],
  ['rejection', '拒绝 / 婉拒', '想拒绝但保持体面。'],
  ['repair', '解释误会 / 修复', '澄清误会、修复关系、缓和气氛。'],
]

const rewriteButtons: Array<{ label: string; mode: RewriteMode }> = [
  { label: '换一个版本', mode: 'alt' },
  { label: '更软一点', mode: 'soft' },
  { label: '更有边界一点', mode: 'boundary' },
  { label: '更正式一点', mode: 'formal' },
  { label: '更简短一点', mode: 'short' },
]

const route = useRoute()
const router = useRouter()

function createEmptyMaterialState(): UniversalCreateWizardRawMaterials {
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

function createId(prefix: string) {
  const fallback = `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${prefix}-${crypto.randomUUID()}`
  }
  return fallback
}

const form = reactive({
  message: '',
  target_person_type: 'crush' as ReplyAssistantTargetType,
  scene_type: 'daily' as ReplyAssistantSceneType,
  target_goal: '更稳妥',
})

const contextFields = reactive({
  before_chat: '',
  recent_state: '',
  before_after: '',
})

const rawMaterials = ref<UniversalCreateWizardRawMaterials>(createEmptyMaterialState())
const loading = ref(false)
const error = ref('')
const result = ref<ReplyAssistantResponse | null>(null)
const lastPrompt = ref('')
const turns = ref<ThreadTurn[]>([
  {
    id: createId('turn'),
    role: 'assistant',
    content: '输入一句话，我直接给你可发的回复。',
  },
])
const menuOpen = ref(false)
const histories = ref<ReplyAssistantHistoryRecord[]>([])
const activeHistoryId = ref('')
const contextOpen = ref(false)
const advancedOpen = ref(false)
const fileInputRef = ref<HTMLInputElement | null>(null)
const imageInputRef = ref<HTMLInputElement | null>(null)

const targetPersonLabel = computed(
  () => targetPersonOptions.find(([value]) => value === form.target_person_type)?.[1] || '',
)
const sceneLabel = computed(() => sceneOptions.find(([value]) => value === form.scene_type)?.[1] || '')

const attachmentSummary = computed(() => {
  const fileCount = rawMaterials.value.uploaded_text_documents.length
  const imageCount = rawMaterials.value.uploaded_image_documents.length
  if (!fileCount && !imageCount) return ''
  const parts = []
  if (fileCount) parts.push(`${fileCount} 文件`)
  if (imageCount) parts.push(`${imageCount} 图片`)
  return parts.join(' · ')
})

const historyStorageKey = 'persona-reply-assistant-histories'
const currentHistoryStorageKey = 'persona-reply-assistant-current-history'

const currentHistoryRecord = computed(
  () => histories.value.find((item) => item.id === activeHistoryId.value) ?? null,
)
const currentHistoryIsFavorite = computed(() => Boolean(currentHistoryRecord.value?.pinned))

const conversationLocked = computed(() => turns.value.some((turn) => turn.role === 'user'))

function createEmptyHistoryForm() {
  return {
    message: '',
    target_person_type: 'crush' as ReplyAssistantTargetType,
    scene_type: 'daily' as ReplyAssistantSceneType,
    target_goal: '更稳妥',
  }
}

function createEmptyContextFields() {
  return {
    before_chat: '',
    recent_state: '',
    before_after: '',
  }
}

function cloneRawMaterials(source: UniversalCreateWizardRawMaterials): UniversalCreateWizardRawMaterials {
  return {
    ...source,
    uploaded_text_documents: source.uploaded_text_documents.map((item) => ({ ...item })),
    uploaded_image_documents: source.uploaded_image_documents.map((item) => ({
      filename: item.filename,
      mime_type: item.mime_type,
      size: item.size,
      ocr_status: item.ocr_status,
      ocr_text: item.ocr_text,
    })),
    ocr_extracted_texts: source.ocr_extracted_texts.map((item) => ({ ...item })),
  }
}

function createEmptyHistoryRecord(): ReplyAssistantHistoryRecord {
  const now = new Date().toISOString()
  return {
    id: createId('reply-history'),
    title: '新对话',
    pinned: false,
    createdAt: now,
    updatedAt: now,
    turns: [
      {
        id: createId('turn'),
        role: 'assistant',
        content: '输入一句话，我直接给你可发的回复。',
      },
    ],
    draft: '',
    form: createEmptyHistoryForm(),
    contextFields: createEmptyContextFields(),
    rawMaterials: createEmptyMaterialState(),
  }
}

function normalizeHistoryRecord(record: ReplyAssistantHistoryRecord): ReplyAssistantHistoryRecord {
  return {
    ...record,
    title: normalizeText(record.title) || '未命名会话',
    turns: Array.isArray(record.turns) && record.turns.length
      ? record.turns.map((turn) => ({
          id: normalizeText(turn.id) || createId('turn'),
          role: turn.role === 'user' ? 'user' : 'assistant',
          prompt: normalizeText(turn.prompt) || undefined,
          result: turn.result || null,
          content: normalizeText(turn.content),
          mode: turn.mode,
        }))
      : createEmptyHistoryRecord().turns,
    draft: normalizeText(record.draft),
    form: {
      message: normalizeText(record.form?.message),
      target_person_type: record.form?.target_person_type || 'crush',
      scene_type: record.form?.scene_type || 'daily',
      target_goal: normalizeText(record.form?.target_goal) || '更稳妥',
    },
    contextFields: {
      before_chat: normalizeText(record.contextFields?.before_chat),
      recent_state: normalizeText(record.contextFields?.recent_state),
      before_after: normalizeText(record.contextFields?.before_after),
    },
    rawMaterials: {
      ...createEmptyMaterialState(),
      ...record.rawMaterials,
      uploaded_text_documents: Array.isArray(record.rawMaterials?.uploaded_text_documents)
        ? record.rawMaterials.uploaded_text_documents.map((item) => ({
            filename: normalizeText(item.filename),
            content: normalizeText(item.content),
          })).filter((item) => item.filename || item.content)
        : [],
      uploaded_image_documents: Array.isArray(record.rawMaterials?.uploaded_image_documents)
        ? record.rawMaterials.uploaded_image_documents.map((item) => ({
            filename: normalizeText(item.filename),
            mime_type: normalizeText(item.mime_type) || 'image/*',
            size: Number(item.size) || 0,
            ocr_status: normalizeText(item.ocr_status) || '待识别',
            ocr_text: normalizeText(item.ocr_text),
          }))
        : [],
      ocr_extracted_texts: Array.isArray(record.rawMaterials?.ocr_extracted_texts)
        ? record.rawMaterials.ocr_extracted_texts.map((item) => ({
            filename: normalizeText(item.filename),
            mime_type: normalizeText(item.mime_type) || 'image/*',
            size: Number(item.size) || 0,
            ocr_status: normalizeText(item.ocr_status) || '待识别',
            ocr_text: normalizeText(item.ocr_text),
          }))
        : [],
    },
  }
}

function loadHistories() {
  if (typeof window === 'undefined') {
    return
  }

  try {
    const raw = window.localStorage.getItem(historyStorageKey)
    if (!raw) {
      histories.value = []
      return
    }
    const parsed = JSON.parse(raw) as ReplyAssistantHistoryRecord[]
    histories.value = Array.isArray(parsed) ? parsed.map(normalizeHistoryRecord) : []
  } catch {
    histories.value = []
  }
}

function saveHistories() {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(historyStorageKey, JSON.stringify(histories.value.slice(0, 20)))
}

function saveCurrentHistoryId(value: string) {
  if (typeof window === 'undefined') {
    return
  }
  if (value) {
    window.localStorage.setItem(currentHistoryStorageKey, value)
  } else {
    window.localStorage.removeItem(currentHistoryStorageKey)
  }
}

function loadCurrentHistoryId() {
  if (typeof window === 'undefined') {
    return ''
  }
  return window.localStorage.getItem(currentHistoryStorageKey) || ''
}

function syncCurrentHistory(record: ReplyAssistantHistoryRecord) {
  const index = histories.value.findIndex((item) => item.id === record.id)
  if (index >= 0) {
    histories.value.splice(index, 1, record)
  } else {
    histories.value.unshift(record)
  }
  saveHistories()
  activeHistoryId.value = record.id
  saveCurrentHistoryId(record.id)
}

function updateHistoryById(
  id: string,
  updater: (record: ReplyAssistantHistoryRecord) => ReplyAssistantHistoryRecord,
) {
  const index = histories.value.findIndex((item) => item.id === id)
  if (index < 0) {
    return null
  }
  const next = updater(normalizeHistoryRecord(histories.value[index]))
  histories.value.splice(index, 1, next)
  saveHistories()
  return next
}

function snapshotCurrentHistory() {
  const record = histories.value.find((item) => item.id === activeHistoryId.value) || createEmptyHistoryRecord()
  return normalizeHistoryRecord({
    ...record,
    id: activeHistoryId.value || record.id,
    title: record.title || '新对话',
    updatedAt: new Date().toISOString(),
    turns: turns.value.map((turn) => ({
      id: turn.id,
      role: turn.role,
      prompt: turn.prompt,
      result: turn.result || null,
      content: turn.content,
      mode: turn.mode,
    })),
    draft: form.message,
    form: {
      message: form.message,
      target_person_type: form.target_person_type,
      scene_type: form.scene_type,
      target_goal: form.target_goal,
    },
    contextFields: {
      before_chat: contextFields.before_chat,
      recent_state: contextFields.recent_state,
      before_after: contextFields.before_after,
    },
    rawMaterials: cloneRawMaterials(rawMaterials.value),
  })
}

function persistConversation() {
  const current = snapshotCurrentHistory()
  syncCurrentHistory({
    ...current,
    title: normalizeText(current.title) || makeHistoryTitle(),
    updatedAt: new Date().toISOString(),
  })
}

function makeHistoryTitle() {
  const prompt = normalizeText(lastPrompt.value || form.message || turns.value.find((item) => item.role === 'user')?.content || '')
  if (!prompt) {
    return '新对话'
  }
  return prompt.length > 16 ? `${prompt.slice(0, 16)}…` : prompt
}

function startNewConversation() {
  activeHistoryId.value = ''
  saveCurrentHistoryId('')
  menuOpen.value = false
  result.value = null
  error.value = ''
  loading.value = false
  form.message = ''
  form.target_person_type = 'crush'
  form.scene_type = 'daily'
  form.target_goal = '更稳妥'
  contextFields.before_chat = ''
  contextFields.recent_state = ''
  contextFields.before_after = ''
  rawMaterials.value = createEmptyMaterialState()
  turns.value = [
    {
      id: createId('turn'),
      role: 'assistant',
      content: '输入一句话，我直接给你可发的回复。',
    },
  ]
}

function hydrateConversation(record: ReplyAssistantHistoryRecord) {
  activeHistoryId.value = record.id
  saveCurrentHistoryId(record.id)
  form.message = record.form.message
  form.target_person_type = record.form.target_person_type
  form.scene_type = record.form.scene_type
  form.target_goal = record.form.target_goal
  contextFields.before_chat = record.contextFields.before_chat
  contextFields.recent_state = record.contextFields.recent_state
  contextFields.before_after = record.contextFields.before_after
  rawMaterials.value = cloneRawMaterials(record.rawMaterials)
  turns.value = record.turns.length
    ? record.turns.map((turn) => ({
        id: turn.id,
        role: turn.role,
        prompt: turn.prompt,
        result: turn.result || null,
        content: turn.content,
        mode: turn.mode,
      }))
    : [
        {
          id: createId('turn'),
          role: 'assistant',
          content: '输入一句话，我直接给你可发的回复。',
        },
      ]
}

function togglePin(record: ReplyAssistantHistoryRecord) {
  updateHistoryById(record.id, (current) => ({
    ...current,
    pinned: !current.pinned,
    updatedAt: new Date().toISOString(),
  }))
}

function toggleCurrentConversationFavorite() {
  if (!activeHistoryId.value) {
    persistConversation()
  }
  const record = histories.value.find((item) => item.id === activeHistoryId.value)
  if (!record) {
    return
  }
  togglePin(record)
}

function goToArchive(tab: 'history' | 'favorites') {
  menuOpen.value = false
  void router.push({
    path: '/archive/reply',
    query: {
      tab,
    },
  })
}

function loadConversationById(id: string) {
  const record = histories.value.find((item) => item.id === id)
  if (!record) {
    return false
  }
  hydrateConversation(record)
  return true
}

function buildCurrentContext() {
  return [contextFields.before_chat, contextFields.recent_state, contextFields.before_after].filter(Boolean).join('\n')
}

function buildConversationContext() {
  const advancedText = [rawMaterials.value.chat_history_text, rawMaterials.value.memory_notes_text, rawMaterials.value.text_materials_text]
    .filter(Boolean)
    .join('\n')
  const extras = [rawMaterials.value.image_notes_text, rawMaterials.value.voice_notes_text, rawMaterials.value.recent_context_text]
    .filter(Boolean)
    .join('\n')
  const recentTurns = turns.value
    .filter((turn) => turn.role === 'user' || turn.role === 'assistant')
    .slice(-6)
    .map((turn) => `${turn.role === 'user' ? '用户' : '助手'}：${normalizeText(turn.content)}`)
    .filter(Boolean)
    .join('\n')
  return [recentTurns, advancedText, extras].filter(Boolean).join('\n')
}

function buildThreadContext() {
  return [
    `对方：${targetPersonLabel.value}`,
    `场景：${sceneLabel.value}`,
    `目标：${form.target_goal.trim()}`,
    buildCurrentContext(),
  ]
    .filter(Boolean)
    .join('\n')
}

function pushUserTurn(prompt: string) {
  turns.value.push({
    id: createId('user'),
    role: 'user',
    prompt,
    content: prompt,
  })
}

function pushAssistantTurn(prompt: string, response: ReplyAssistantResponse, mode: ThreadTurn['mode']) {
  const parts = [
    response.judgment,
    response.recommended_reply,
    response.risk_note,
    response.likely_consequence,
  ].filter(Boolean)
  turns.value.push({
    id: createId('assistant'),
    role: 'assistant',
    prompt,
    result: response,
    mode,
    content: parts.join('\n'),
  })
}

function normalizeText(value: unknown) {
  return String(value || '').trim()
}

function isTextFile(file: File) {
  if (file.type && (file.type === 'text/plain' || file.type === 'text/markdown' || file.type === 'text/csv')) {
    return true
  }
  return /\.(txt|md|csv)$/i.test(file.name)
}

function isImageFile(file: File) {
  if (file.type && file.type.startsWith('image/')) {
    return true
  }
  return /\.(jpg|jpeg|png|webp)$/i.test(file.name)
}

function guessImageMimeType(file: File) {
  if (file.type && file.type.startsWith('image/')) {
    return file.type
  }
  if (/\.jpe?g$/i.test(file.name)) {
    return 'image/jpeg'
  }
  if (/\.png$/i.test(file.name)) {
    return 'image/png'
  }
  if (/\.webp$/i.test(file.name)) {
    return 'image/webp'
  }
  return 'image/*'
}

async function readFileAsText(file: File) {
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error(`读取文件失败：${file.name}`))
    reader.readAsText(file)
  })
}

async function readFileAsDataUrl(file: File) {
  return await new Promise<string>((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(new Error(`读取图片失败：${file.name}`))
    reader.readAsDataURL(file)
  })
}

async function handleTextFiles(event: Event) {
  const target = event.target as HTMLInputElement | null
  const files = Array.from(target?.files || []).filter(isTextFile)
  if (!files.length) {
    if (target) target.value = ''
    return
  }

  const documents = await Promise.all(
    files.map(async (file) => {
      const content = normalizeText(await readFileAsText(file))
      return content ? { filename: file.name, content } : null
    }),
  )

  const validDocuments = documents.filter(Boolean) as TextMaterialDocument[]
  rawMaterials.value.uploaded_text_documents = [...rawMaterials.value.uploaded_text_documents, ...validDocuments]
  const appended = validDocuments.map((item) => item.content).filter(Boolean).join('\n')
  if (appended) {
    rawMaterials.value.text_materials_text = [rawMaterials.value.text_materials_text, appended].filter(Boolean).join('\n')
  }
  if (target) target.value = ''
}

async function handleImageFiles(event: Event) {
  const target = event.target as HTMLInputElement | null
  const files = Array.from(target?.files || []).filter(isImageFile)
  if (!files.length) {
    if (target) target.value = ''
    return
  }

  const documents = await Promise.all(
    files.map(async (file) => ({
      filename: file.name,
      mime_type: guessImageMimeType(file),
      size: file.size,
      data_url: await readFileAsDataUrl(file),
      ocr_status: '待识别',
      ocr_text: '',
    })),
  )

  rawMaterials.value.uploaded_image_documents = [...rawMaterials.value.uploaded_image_documents, ...documents]
  if (target) target.value = ''
}

function triggerTextUpload() {
  fileInputRef.value?.click()
}

function triggerImageUpload() {
  imageInputRef.value?.click()
}

function removeTextDocument(index: number) {
  rawMaterials.value.uploaded_text_documents = rawMaterials.value.uploaded_text_documents.filter((_, itemIndex) => itemIndex !== index)
}

function removeImageDocument(index: number) {
  rawMaterials.value.uploaded_image_documents = rawMaterials.value.uploaded_image_documents.filter((_, itemIndex) => itemIndex !== index)
}

function onTargetPersonTypeChange(event: Event) {
  const nextValue = (event.target as HTMLSelectElement | null)?.value || form.target_person_type
  if (conversationLocked.value && nextValue !== form.target_person_type) {
    error.value = '这段对话已经开始，切换对象可能导致回答偏差。建议新开一个对话。'
    return
  }
  error.value = ''
  form.target_person_type = nextValue as ReplyAssistantTargetType
}

function onSceneTypeChange(event: Event) {
  const nextValue = (event.target as HTMLSelectElement | null)?.value || form.scene_type
  if (conversationLocked.value && nextValue !== form.scene_type) {
    error.value = '这段对话已经开始，切换场景可能导致回答偏差。建议新开一个对话。'
    return
  }
  error.value = ''
  form.scene_type = nextValue as ReplyAssistantSceneType
}

async function generateReply(rewriteMode: RewriteMode | 'default' = 'default') {
  const prompt = rewriteMode === 'default' ? form.message.trim() : (lastPrompt.value || form.message.trim())
  if (!prompt) {
    return
  }

  loading.value = true
  error.value = ''

  try {
    if (rewriteMode === 'default') {
      pushUserTurn(prompt)
      lastPrompt.value = prompt
    }
    const nextResult = await requestReplyAssistant({
      message: prompt,
      target_person_type: form.target_person_type,
      target_person_label: targetPersonLabel.value,
      scene_type: form.scene_type,
      current_context: buildThreadContext(),
      target_goal: form.target_goal,
      conversation_context: buildConversationContext(),
      conversation_turns: turns.value
        .filter((turn) => turn.role === 'user' || turn.role === 'assistant')
        .slice(-10)
        .map((turn) => ({
          role: turn.role,
          content: turn.content,
        })),
      rewrite_mode: rewriteMode,
      raw_materials: rawMaterials.value,
    })
    result.value = nextResult
    pushAssistantTurn(prompt, nextResult, rewriteMode)
    if (rewriteMode === 'default') {
      form.message = ''
    }
    persistConversation()
    result.value = nextResult
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : '生成回复建议失败'
    result.value = null
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHistories()
  const historyId = String(route.query.history || '').trim()
  if (historyId && loadConversationById(historyId)) {
    return
  }

  activeHistoryId.value = loadCurrentHistoryId()
  if (activeHistoryId.value) {
    const current = histories.value.find((item) => item.id === activeHistoryId.value)
    if (current) {
      hydrateConversation(current)
    }
  }
})
</script>

<template>
  <section class="section-card reply-shell">
    <button class="reply-history-toggle" type="button" aria-label="查看菜单" @click="menuOpen = !menuOpen">
      <span></span>
      <span></span>
      <span></span>
    </button>

    <transition name="fade">
      <aside v-if="menuOpen" class="reply-history-panel">
        <div class="reply-history-panel__head">
          <button class="ghost-button ghost-button--small" type="button" @click="startNewConversation">新对话</button>
          <button
            class="ghost-button ghost-button--small"
            type="button"
            :disabled="loading"
            @click="toggleCurrentConversationFavorite"
          >
            {{ currentHistoryIsFavorite ? '取消收藏' : '收藏对话' }}
          </button>
        </div>
        <div class="reply-history-panel__links">
          <button type="button" class="reply-history-link" @click="goToArchive('history')">历史</button>
          <button type="button" class="reply-history-link" @click="goToArchive('favorites')">收藏</button>
        </div>
      </aside>
    </transition>

    <div class="reply-thread">
      <article v-for="turn in turns" :key="turn.id" class="reply-turn" :class="`reply-turn--${turn.role}`">
        <div v-if="turn.role === 'assistant'" class="reply-turn__meta">
          <span v-if="turn.mode && turn.mode !== 'default'" class="reply-turn__mode">
            {{ rewriteButtons.find((item) => item.mode === turn.mode)?.label || '重写' }}
          </span>
        </div>

        <template v-if="turn.role === 'user'">
          <p class="reply-turn__text">{{ turn.content }}</p>
        </template>

        <template v-else>
          <div v-if="turn.result" class="reply-answer-grid">
            <article class="reply-answer-card">
              <p class="reply-answer-card__label">基础判断</p>
              <h3>{{ turn.result.judgment || '先输入内容。' }}</h3>
            </article>
            <article class="reply-answer-card reply-answer-card--main">
              <p class="reply-answer-card__label">推荐回复</p>
              <h3>{{ turn.result.recommended_reply || '这里显示可发送回复。' }}</h3>
              <div class="rewrite-actions">
                <button
                  v-for="item in rewriteButtons"
                  :key="item.mode"
                  class="chip-btn"
                  type="button"
                  :disabled="loading || !(form.message.trim() || lastPrompt)"
                  @click="generateReply(item.mode)"
                >
                  {{ item.label }}
                </button>
              </div>
            </article>
            <article class="reply-answer-card">
              <p class="reply-answer-card__label">小提示</p>
              <p>{{ turn.result.risk_note || '这里显示风险。' }}</p>
            </article>
            <article class="reply-answer-card">
              <p class="reply-answer-card__label">回复推测</p>
              <p>{{ turn.result.likely_consequence || '这里显示走向。' }}</p>
            </article>
          </div>
          <p v-else class="reply-turn__text">{{ turn.content }}</p>
        </template>
      </article>

      <article v-if="loading" class="reply-turn reply-turn--assistant">
        <p class="reply-turn__text">生成中…</p>
      </article>
    </div>

    <div class="reply-composer">
      <div class="reply-composer__row">
        <label class="reply-select">
          <span>对方</span>
          <select
            :value="form.target_person_type"
            class="field-input field-input--compact"
            :disabled="conversationLocked"
            @change="onTargetPersonTypeChange"
          >
            <option v-for="[value, label] in targetPersonOptions" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
        </label>
        <label class="reply-select">
          <span>场景</span>
          <select
            :value="form.scene_type"
            class="field-input field-input--compact"
            :disabled="conversationLocked"
            @change="onSceneTypeChange"
          >
            <option v-for="[value, label] in sceneOptions" :key="value" :value="value">
              {{ label }}
            </option>
          </select>
        </label>
      </div>

      <p v-if="conversationLocked" class="reply-lock-tip">
        当前对话已开始，不能切换对象或场景。要换的话，建议新开一个对话。
      </p>

      <label class="reply-input">
        <textarea
          v-model="form.message"
          class="field-input reply-input__textarea"
          rows="4"
          placeholder="把对方的话贴在这里，直接生成回复"
          @keydown.meta.enter.exact.prevent="generateReply()"
          @keydown.ctrl.enter.exact.prevent="generateReply()"
        ></textarea>
      </label>

      <div class="reply-composer__attachments-row">
        <div class="reply-composer__attachment-actions">
          <button class="reply-chip" type="button" @click="contextOpen = !contextOpen">+</button>
          <button class="reply-chip" type="button" @click="advancedOpen = !advancedOpen">高级</button>
          <button class="reply-chip" type="button" @click="triggerTextUpload">📄 文件</button>
          <button class="reply-chip" type="button" @click="triggerImageUpload">🖼 图片</button>
        </div>
        <span v-if="attachmentSummary" class="reply-chip reply-chip--ghost">{{ attachmentSummary }}</span>
      </div>

      <div class="reply-composer__footer">
        <div class="reply-composer__attach">
          <input ref="fileInputRef" class="reply-hidden-input" type="file" accept=".txt,.md,.csv,text/plain,text/markdown,text/csv" multiple @change="handleTextFiles" />
          <input ref="imageInputRef" class="reply-hidden-input" type="file" accept="image/*,.jpg,.jpeg,.png,.webp" multiple @change="handleImageFiles" />
        </div>
        <button class="primary-btn" type="button" :disabled="loading || !form.message.trim()" @click="generateReply()">
          {{ loading ? '生成中…' : '发送' }}
        </button>
      </div>

      <transition name="fade">
        <div v-if="contextOpen" class="reply-drawer">
          <div class="reply-drawer__grid">
            <label class="form-field">
              <span>前面在聊什么</span>
              <textarea v-model="contextFields.before_chat" class="field-input reply-drawer__textarea" rows="3"></textarea>
            </label>
            <label class="form-field">
              <span>最近什么状态</span>
              <textarea v-model="contextFields.recent_state" class="field-input reply-drawer__textarea" rows="3"></textarea>
            </label>
            <label class="form-field">
              <span>这句话前后发生了什么</span>
              <textarea v-model="contextFields.before_after" class="field-input reply-drawer__textarea" rows="3"></textarea>
            </label>
            <label class="form-field reply-drawer__span-2">
              <span>你的目标</span>
              <textarea
                v-model="form.target_goal"
                class="field-input reply-drawer__textarea"
                rows="3"
                placeholder="更自然 / 更正式 / 更有边界 / 更推进 / 更克制"
              ></textarea>
            </label>
          </div>
        </div>
      </transition>

      <transition name="fade">
        <div v-if="advancedOpen" class="reply-drawer reply-drawer--advanced">
          <div class="reply-drawer__grid">
            <label class="form-field">
              <span>多轮聊天 / 额外上下文</span>
              <textarea
                v-model="rawMaterials.recent_context_text"
                class="field-input reply-drawer__textarea"
                rows="4"
                placeholder="把前后聊天一起贴进来"
              ></textarea>
            </label>
            <label class="form-field">
              <span>聊天记录粘贴</span>
              <textarea
                v-model="rawMaterials.chat_history_text"
                class="field-input reply-drawer__textarea"
                rows="4"
                placeholder="粘贴聊天记录、对话片段或材料摘要"
              ></textarea>
            </label>
            <label class="form-field">
              <span>记忆笔记 / 回忆片段</span>
              <textarea
                v-model="rawMaterials.memory_notes_text"
                class="field-input reply-drawer__textarea"
                rows="4"
                placeholder="把反复出现的记忆、提醒、关心方式整理进来"
              ></textarea>
            </label>
            <label class="form-field">
              <span>文本材料补充</span>
              <textarea
                v-model="rawMaterials.text_materials_text"
                class="field-input reply-drawer__textarea"
                rows="4"
                placeholder="可粘贴家书、日记、便条、文字说明"
              ></textarea>
            </label>
            <label class="form-field">
              <span>图片说明</span>
              <textarea
                v-model="rawMaterials.image_notes_text"
                class="field-input reply-drawer__textarea"
                rows="3"
                placeholder="如果 OCR 不完整，可以补一句这张图想表达什么"
              ></textarea>
            </label>
            <label class="form-field">
              <span>语音说明</span>
              <textarea
                v-model="rawMaterials.voice_notes_text"
                class="field-input reply-drawer__textarea"
                rows="3"
                placeholder="如果有语音材料，可以先用文字补充"
              ></textarea>
            </label>
          </div>
          <div v-if="rawMaterials.uploaded_text_documents.length || rawMaterials.uploaded_image_documents.length" class="reply-attachments">
            <article v-for="(item, index) in rawMaterials.uploaded_text_documents" :key="`text-${item.filename}-${index}`" class="reply-attachment">
              <span>📄 {{ item.filename }}</span>
              <button type="button" class="ghost-button ghost-button--small" @click="removeTextDocument(index)">移除</button>
            </article>
            <article v-for="(item, index) in rawMaterials.uploaded_image_documents" :key="`image-${item.filename}-${index}`" class="reply-attachment">
              <span>🖼 {{ item.filename }}</span>
              <button type="button" class="ghost-button ghost-button--small" @click="removeImageDocument(index)">移除</button>
            </article>
          </div>
        </div>
      </transition>

      <div v-if="error" class="reply-error">
        <p>{{ error }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.reply-shell {
  position: relative;
  display: grid;
  gap: 1rem;
  padding-bottom: 1.2rem;
  padding-top: 3rem;
  font-size: 0.96rem;
}

.reply-history-toggle {
  position: absolute;
  top: 0.9rem;
  left: 0.9rem;
  z-index: 6;
  display: inline-flex;
  flex-direction: column;
  justify-content: center;
  gap: 0.23rem;
  width: 42px;
  height: 42px;
  border: 1px solid rgba(127, 140, 172, 0.2);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px rgba(32, 40, 60, 0.08);
}

.reply-history-toggle span {
  display: block;
  width: 18px;
  height: 2px;
  margin: 0 auto;
  border-radius: 999px;
  background: var(--text);
}

.reply-history-panel {
  position: absolute;
  top: 3.8rem;
  left: 0.9rem;
  z-index: 5;
  width: min(340px, calc(100vw - 1.8rem));
  padding: 0.9rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: 0 24px 50px rgba(24, 32, 57, 0.16);
  backdrop-filter: blur(18px);
}

.reply-history-panel__head {
  display: flex;
  justify-content: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.reply-history-panel__links {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.reply-history-link {
  flex: 1 1 0;
  min-width: 0;
  min-height: 42px;
  padding: 0.55rem 0.8rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 16px;
  background: rgba(248, 250, 252, 0.94);
  color: var(--text);
  font-weight: 700;
}

.reply-history-link:hover,
.reply-history-link:focus-visible {
  border-color: rgba(96, 110, 220, 0.32);
  background: rgba(242, 245, 255, 0.98);
}

.reply-thread {
  display: grid;
  gap: 0.9rem;
  min-height: 36vh;
}

.reply-turn {
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.64);
  box-shadow: 0 12px 28px rgba(40, 45, 60, 0.05);
}

.reply-turn--user {
  margin-left: auto;
  max-width: min(720px, 92%);
  background: rgba(243, 247, 255, 0.96);
}

.reply-turn--assistant {
  max-width: min(920px, 100%);
}

.reply-turn__meta {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.7rem;
}

.reply-turn__mode {
  display: inline-flex;
  align-items: center;
  border-radius: 999px;
  padding: 0.18rem 0.6rem;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.01em;
  background: rgba(63, 81, 181, 0.08);
  color: var(--text);
}

.reply-turn__mode {
  background: rgba(86, 104, 180, 0.12);
}

.reply-turn__text {
  white-space: pre-wrap;
  line-height: 1.7;
  margin: 0;
  color: var(--text);
}

.reply-answer-grid {
  display: grid;
  gap: 0.8rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.reply-answer-card {
  border-radius: 18px;
  padding: 0.9rem 1rem;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(127, 140, 172, 0.16);
}

.reply-answer-card--main {
  grid-column: span 2;
}

.reply-answer-card__label {
  margin: 0 0 0.45rem;
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--muted);
}

.reply-answer-card h3,
.reply-answer-card p {
  margin: 0;
  line-height: 1.6;
}

.reply-composer {
  position: sticky;
  bottom: 0;
  display: grid;
  gap: 0.8rem;
  padding: 0.95rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 24px;
  background: rgba(252, 253, 255, 0.96);
  box-shadow: 0 18px 40px rgba(24, 32, 57, 0.08);
  backdrop-filter: blur(18px);
}

.reply-composer__row,
.reply-composer__attachments-row,
.reply-composer__footer {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  align-items: center;
}

.reply-composer__attachments-row {
  justify-content: space-between;
}

.reply-composer__attachment-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.reply-chip {
  border: 1px solid rgba(127, 140, 172, 0.18);
  border-radius: 999px;
  padding: 0.45rem 0.78rem;
  background: #fff;
  font-weight: 700;
  color: var(--text);
}

.reply-chip--ghost {
  background: rgba(244, 246, 250, 0.8);
}

.reply-select {
  display: grid;
  gap: 0.35rem;
  min-width: 160px;
  flex: 1 1 160px;
}

.reply-select span,
.reply-input span {
  font-size: 0.72rem;
  font-weight: 700;
  color: var(--muted);
}

.reply-lock-tip {
  margin: 0;
  padding: 0.65rem 0.8rem;
  border-radius: 16px;
  background: rgba(255, 159, 138, 0.12);
  border: 1px solid rgba(255, 159, 138, 0.18);
  color: var(--text);
  font-size: 0.85rem;
  line-height: 1.55;
}

.field-input--compact {
  min-height: 42px;
  font-size: 0.92rem;
}

.reply-input {
  display: grid;
  gap: 0.45rem;
}

.reply-input__textarea {
  min-height: 112px;
  resize: vertical;
  font-size: 0.96rem;
  line-height: 1.65;
}

.reply-composer__footer {
  justify-content: space-between;
}

.reply-composer__attach {
  display: none;
}

.reply-drawer {
  display: grid;
  gap: 0.8rem;
  padding: 0.85rem;
  border-radius: 20px;
  background: rgba(244, 246, 250, 0.94);
  border: 1px solid rgba(127, 140, 172, 0.14);
}

.reply-drawer__grid {
  display: grid;
  gap: 0.8rem;
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.reply-drawer__textarea {
  min-height: 76px;
  font-size: 0.94rem;
}

.reply-drawer--advanced .reply-drawer__grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.reply-attachments {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
}

.reply-attachment {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  border: 1px solid rgba(127, 140, 172, 0.16);
  border-radius: 999px;
  padding: 0.35rem 0.65rem;
  background: #fff;
}

.reply-error {
  padding: 0.6rem 0.8rem;
  color: var(--danger, #b42318);
}

.reply-error p {
  margin: 0;
}

.rewrite-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.55rem;
  margin-top: 0.85rem;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

@media (max-width: 980px) {
  .reply-shell {
    padding-top: 3.6rem;
  }

  .reply-history-panel {
    width: calc(100vw - 1.8rem);
  }

  .reply-answer-grid,
  .reply-drawer__grid {
    grid-template-columns: 1fr;
  }

  .reply-answer-card--main {
    grid-column: span 1;
  }

  .reply-shell {
    padding-bottom: 0.8rem;
    font-size: 0.94rem;
  }

  .reply-composer {
    position: static;
  }

  .reply-composer__attachments-row {
    align-items: flex-start;
  }

  .reply-composer__attachment-actions {
    gap: 0.45rem;
  }
}
</style>
