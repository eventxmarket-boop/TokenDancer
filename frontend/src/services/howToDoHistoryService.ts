import type { HowToDoResponse } from '@/services/howToDoService'
import { loadSavedItems, replaceSavedItems } from '@/services/savedItemsService'

export type HowToDoStoredTurn = {
  id: string
  role: 'user' | 'assistant'
  content: string
}

export type HowToDoHistoryRecord = {
  id: string
  title: string
  question: string
  category: string
  castMode: string
  createdAt: string
  updatedAt: string
  favorite: boolean
  result: HowToDoResponse
  chatTurns: HowToDoStoredTurn[]
}

const HISTORY_KEY = 'persona-how-to-do-histories'
const HISTORY_KIND = 'howtodo_history'

function canUseStorage() {
  return typeof window !== 'undefined' && typeof window.localStorage !== 'undefined'
}

function parseHistoryRecords(raw: string | null): HowToDoHistoryRecord[] {
  if (!raw) return []
  try {
    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) return []
    return parsed.filter((item): item is HowToDoHistoryRecord => {
      return Boolean(item && typeof item === 'object' && 'id' in item && 'result' in item)
    })
  } catch {
    return []
  }
}

function saveHistoryRecords(records: HowToDoHistoryRecord[]) {
  if (!canUseStorage()) return
  window.localStorage.setItem(HISTORY_KEY, JSON.stringify(records.slice(0, 40)))
}

function normalizeRecords(records: HowToDoHistoryRecord[]) {
  return records
    .filter((item) => item && typeof item === 'object' && typeof item.id === 'string')
    .map((item) => ({
      ...item,
      favorite: Boolean(item.favorite),
      updatedAt: item.updatedAt || new Date().toISOString(),
      createdAt: item.createdAt || item.updatedAt || new Date().toISOString(),
    }))
    .sort((left, right) => new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime())
}

async function syncHistoryRecordsToRemote(records: HowToDoHistoryRecord[]) {
  const payload = records.slice(0, 40).map((record) => ({
    item_key: record.id,
    title: record.title || record.question || '未命名卦象',
    pinned: Boolean(record.favorite),
    payload: record as Record<string, unknown>,
  }))
  await replaceSavedItems(HISTORY_KIND, payload)
}

export async function loadHowToDoHistoryRecords(): Promise<HowToDoHistoryRecord[]> {
  const localRecords = listHowToDoHistoryRecords()
  try {
    const remoteRecords = await loadSavedItems<HowToDoHistoryRecord>(HISTORY_KIND)
    const mergedMap = new Map<string, HowToDoHistoryRecord>()
    for (const record of [...localRecords, ...remoteRecords.map((item) => item.payload)]) {
      if (!record || typeof record !== 'object' || typeof record.id !== 'string') {
        continue
      }
      mergedMap.set(record.id, {
        ...record,
        favorite: Boolean(record.favorite),
        updatedAt: record.updatedAt || new Date().toISOString(),
        createdAt: record.createdAt || record.updatedAt || new Date().toISOString(),
      })
    }
    const merged = normalizeRecords(Array.from(mergedMap.values()))
    saveHistoryRecords(merged)
    if (merged.length || remoteRecords.length) {
      await syncHistoryRecordsToRemote(merged)
    }
    return merged
  } catch {
    return localRecords
  }
}

export function listHowToDoHistoryRecords() {
  if (!canUseStorage()) return [] as HowToDoHistoryRecord[]
  const records = parseHistoryRecords(window.localStorage.getItem(HISTORY_KEY))
  return normalizeRecords(records)
}

export async function syncHowToDoHistoryRecordsFromLocal() {
  const localRecords = listHowToDoHistoryRecords()
  try {
    const remoteRecords = await loadSavedItems<HowToDoHistoryRecord>(HISTORY_KIND)
    const mergedMap = new Map<string, HowToDoHistoryRecord>()
    for (const record of [...localRecords, ...remoteRecords.map((item) => item.payload)]) {
      if (!record || typeof record !== 'object' || typeof record.id !== 'string') {
        continue
      }
      mergedMap.set(record.id, {
        ...record,
        favorite: Boolean(record.favorite),
        updatedAt: record.updatedAt || new Date().toISOString(),
        createdAt: record.createdAt || record.updatedAt || new Date().toISOString(),
      })
    }
    const merged = normalizeRecords(Array.from(mergedMap.values()))
    saveHistoryRecords(merged)
    if (merged.length || remoteRecords.length) {
      await syncHistoryRecordsToRemote(merged)
    }
    return merged
  } catch {
    return localRecords
  }
}

export function listFavoriteHowToDoHistoryRecords() {
  return listHowToDoHistoryRecords().filter((item) => item.favorite)
}

export function upsertHowToDoHistoryRecord(record: HowToDoHistoryRecord) {
  const records = listHowToDoHistoryRecords()
  const next = [record, ...records.filter((item) => item.id !== record.id)]
  saveHistoryRecords(next)
  void syncHistoryRecordsToRemote(next)
}

export function toggleFavoriteHowToDoHistoryRecord(id: string) {
  const records = listHowToDoHistoryRecords()
  const next = records.map((item) => {
    if (item.id !== id) return item
    return {
      ...item,
      favorite: !item.favorite,
      updatedAt: new Date().toISOString(),
    }
  })
  saveHistoryRecords(next)
  void syncHistoryRecordsToRemote(next)
  return next.find((item) => item.id === id) ?? null
}

export async function clearFavoriteHowToDoHistoryRecords() {
  const records = listHowToDoHistoryRecords()
  const next = records.map((item) => ({ ...item, favorite: false }))
  saveHistoryRecords(next)
  await syncHistoryRecordsToRemote(next)
}
