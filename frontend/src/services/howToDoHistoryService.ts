import type { HowToDoResponse } from '@/services/howToDoService'

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

export function listHowToDoHistoryRecords() {
  if (!canUseStorage()) return [] as HowToDoHistoryRecord[]
  const records = parseHistoryRecords(window.localStorage.getItem(HISTORY_KEY))
  return [...records].sort((left, right) => {
    return new Date(right.updatedAt).getTime() - new Date(left.updatedAt).getTime()
  })
}

export function listFavoriteHowToDoHistoryRecords() {
  return listHowToDoHistoryRecords().filter((item) => item.favorite)
}

export function upsertHowToDoHistoryRecord(record: HowToDoHistoryRecord) {
  const records = listHowToDoHistoryRecords()
  const next = [record, ...records.filter((item) => item.id !== record.id)]
  saveHistoryRecords(next)
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
  return next.find((item) => item.id === id) ?? null
}

export function clearFavoriteHowToDoHistoryRecords() {
  const records = listHowToDoHistoryRecords()
  const next = records.map((item) => ({ ...item, favorite: false }))
  saveHistoryRecords(next)
}
