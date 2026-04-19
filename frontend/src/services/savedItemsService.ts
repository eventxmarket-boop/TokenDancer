import { authHeaders, getAuthToken } from '@/services/authService'

const API_PREFIX = '/persona-api'

export type SavedItemPayload = Record<string, unknown>

export type SavedItemRecord<TPayload extends SavedItemPayload = SavedItemPayload> = {
  item_key: string
  title: string
  pinned: boolean
  payload: TPayload
  created_at: string
  updated_at: string
}

export type SavedItemUpsert<TPayload extends SavedItemPayload = SavedItemPayload> = {
  item_key: string
  title?: string
  pinned?: boolean
  payload?: TPayload
}

async function readErrorMessage(response: Response): Promise<string> {
  const text = await response.text()
  try {
    const payload = JSON.parse(text) as Record<string, unknown>
    const message = payload.detail ?? payload.message
    if (typeof message === 'string' && message.trim()) {
      return message.trim()
    }
  } catch {
    // fallback to plain text
  }
  return text.trim()
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await readErrorMessage(response)
    throw new Error(detail || `Request failed with status ${response.status}`)
  }
  return (await response.json()) as T
}

function hasRemoteAuth() {
  return Boolean(getAuthToken())
}

export async function loadSavedItems<TPayload extends SavedItemPayload = SavedItemPayload>(
  kind: string,
): Promise<SavedItemRecord<TPayload>[]> {
  if (!hasRemoteAuth()) {
    return []
  }

  const response = await fetch(`${API_PREFIX}/saved-items/${encodeURIComponent(kind)}`, {
    headers: authHeaders(),
  })
  return readJson<SavedItemRecord<TPayload>[]>(response)
}

export async function replaceSavedItems<TPayload extends SavedItemPayload = SavedItemPayload>(
  kind: string,
  items: SavedItemUpsert<TPayload>[],
): Promise<SavedItemRecord<TPayload>[]> {
  if (!hasRemoteAuth()) {
    return []
  }

  const response = await fetch(`${API_PREFIX}/saved-items/${encodeURIComponent(kind)}`, {
    method: 'PUT',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify({ items }),
  })
  return readJson<SavedItemRecord<TPayload>[]>(response)
}

export async function clearSavedItems(kind: string): Promise<void> {
  if (!hasRemoteAuth()) {
    return
  }

  const response = await fetch(`${API_PREFIX}/saved-items/${encodeURIComponent(kind)}`, {
    method: 'DELETE',
    headers: authHeaders(),
  })
  await readJson<{ ok: boolean }>(response)
}
