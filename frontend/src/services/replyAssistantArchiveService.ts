import { loadSavedItems, replaceSavedItems } from '@/services/savedItemsService'

export type ReplyAssistantTargetType =
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

export type ReplyAssistantSceneType =
  | 'daily'
  | 'conflict'
  | 'push_forward'
  | 'work_report'
  | 'follow_up'
  | 'formal_notice'
  | 'rejection'
  | 'repair'

export type RewriteMode = 'alt' | 'soft' | 'boundary' | 'formal' | 'short'

export type ReplyAssistantTurn = {
  id: string
  role: 'user' | 'assistant'
  prompt?: string
  result?: Record<string, unknown> | null
  content: string
  mode?: RewriteMode | 'default'
}

export type ReplyAssistantHistoryRecord = {
  id: string
  title: string
  pinned: boolean
  createdAt: string
  updatedAt: string
  turns: ReplyAssistantTurn[]
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
  rawMaterials: Record<string, unknown>
}

const HISTORY_KIND = 'reply_history'
const HISTORY_KEY = 'persona-reply-assistant-histories'
const CURRENT_HISTORY_KEY = 'persona-reply-assistant-current-history'

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function normalizeText(value: unknown) {
  return String(value || '').trim()
}

function createFallbackRecord(): ReplyAssistantHistoryRecord {
  const now = new Date().toISOString()
  return {
    id: `reply-history-${Date.now().toString(36)}`,
    title: '新对话',
    pinned: false,
    createdAt: now,
    updatedAt: now,
    turns: [
      {
        id: `turn-${Date.now().toString(36)}`,
        role: 'assistant',
        content: '输入一句话，我直接给你可发的回复。',
      },
    ],
    draft: '',
    form: {
      message: '',
      target_person_type: 'crush',
      scene_type: 'daily',
      target_goal: '更稳妥',
    },
    contextFields: {
      before_chat: '',
      recent_state: '',
      before_after: '',
    },
    rawMaterials: {},
  }
}

function normalizeRecord(record: ReplyAssistantHistoryRecord): ReplyAssistantHistoryRecord {
  const fallback = createFallbackRecord()
  return {
    ...fallback,
    ...record,
    title: normalizeText(record.title) || '未命名会话',
    turns: Array.isArray(record.turns) && record.turns.length
      ? record.turns.map((turn) => ({
          id: normalizeText(turn.id) || `turn-${Date.now().toString(36)}`,
          role: turn.role === 'user' ? 'user' : 'assistant',
          prompt: normalizeText(turn.prompt) || undefined,
          result: turn.result || null,
          content: normalizeText(turn.content),
          mode: turn.mode,
        }))
      : fallback.turns,
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
    rawMaterials: record.rawMaterials || {},
  }
}

function parseStoredRecords(raw: string | null): ReplyAssistantHistoryRecord[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed
      .filter((item): item is ReplyAssistantHistoryRecord => Boolean(item && typeof item === 'object' && 'id' in item))
      .map((item) => normalizeRecord(item))
      .sort((left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime())
  } catch {
    return []
  }
}

function readLocalRecords(): ReplyAssistantHistoryRecord[] {
  if (!canUseStorage()) return []
  return parseStoredRecords(window.localStorage.getItem(HISTORY_KEY))
}

function writeLocalRecords(records: ReplyAssistantHistoryRecord[]) {
  if (!canUseStorage()) return
  window.localStorage.setItem(HISTORY_KEY, JSON.stringify(records.slice(0, 20)))
}

function readCurrentHistoryId() {
  if (!canUseStorage()) return ''
  return window.localStorage.getItem(CURRENT_HISTORY_KEY) || ''
}

function writeCurrentHistoryId(value: string) {
  if (!canUseStorage()) return
  if (value) {
    window.localStorage.setItem(CURRENT_HISTORY_KEY, value)
    return
  }
  window.localStorage.removeItem(CURRENT_HISTORY_KEY)
}

async function syncRemote(records: ReplyAssistantHistoryRecord[]) {
  await replaceSavedItems(HISTORY_KIND, records.slice(0, 20).map((record) => ({
    item_key: record.id,
    title: record.title || '未命名会话',
    pinned: Boolean(record.pinned),
    payload: record as Record<string, unknown>,
  })))
}

export async function loadReplyAssistantHistoryRecords(): Promise<ReplyAssistantHistoryRecord[]> {
  const localRecords = readLocalRecords()
  try {
    const remoteRecords = await loadSavedItems<ReplyAssistantHistoryRecord>(HISTORY_KIND)
    const merged = new Map<string, ReplyAssistantHistoryRecord>()
    for (const record of [...localRecords, ...remoteRecords.map((item) => item.payload)]) {
      if (!record || typeof record !== 'object' || typeof record.id !== 'string') {
        continue
      }
      merged.set(record.id, normalizeRecord(record))
    }
    const next = Array.from(merged.values()).sort(
      (left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime(),
    )
    writeLocalRecords(next)
    if (next.length || remoteRecords.length) {
      await syncRemote(next)
    }
    return next
  } catch {
    return localRecords
  }
}

export function listReplyAssistantHistoryRecords() {
  return readLocalRecords()
}

export function upsertReplyAssistantHistoryRecord(record: ReplyAssistantHistoryRecord) {
  const records = readLocalRecords()
  const next = [normalizeRecord(record), ...records.filter((item) => item.id !== record.id)]
  writeLocalRecords(next)
  void syncRemote(next)
}

export function toggleReplyAssistantPinnedRecord(id: string) {
  const records = readLocalRecords()
  const next = records.map((item) => {
    if (item.id !== id) return item
    return {
      ...item,
      pinned: !item.pinned,
      updatedAt: new Date().toISOString(),
    }
  })
  writeLocalRecords(next)
  void syncRemote(next)
  return next.find((item) => item.id === id) ?? null
}

export function saveReplyAssistantCurrentHistoryId(value: string) {
  writeCurrentHistoryId(value)
}

export function loadReplyAssistantCurrentHistoryId() {
  return readCurrentHistoryId()
}
