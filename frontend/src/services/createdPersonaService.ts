import type { CreateWizardDraft } from '@/services/createWizardService'

const API_PREFIX = '/persona-api'

export type CreatedPersonaSummary = {
  id: number
  slug: string
  name: string
  persona_type: string
  summary: string
  status: string
  source_type: string
  created_at: string
  updated_at: string
}

export type CreatedPersonaRecord = CreatedPersonaSummary & {
  draft_payload: CreateWizardDraft
}

export type CreatedPersonaSavePayload = {
  draft: CreateWizardDraft
  source_type?: string
  status?: string
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
    // fall through to raw text
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

export async function loadMySeeds(): Promise<CreatedPersonaSummary[]> {
  const response = await fetch(`${API_PREFIX}/my-seeds`)
  return readJson<CreatedPersonaSummary[]>(response)
}

export async function loadMySeed(seedId: number): Promise<CreatedPersonaRecord | null> {
  const response = await fetch(`${API_PREFIX}/my-seeds/${encodeURIComponent(String(seedId))}`)
  if (response.status === 404) {
    return null
  }
  return readJson<CreatedPersonaRecord>(response)
}

export async function saveMySeed(
  payload: CreatedPersonaSavePayload,
  seedId?: number | null,
): Promise<CreatedPersonaRecord> {
  const response = await fetch(
    seedId
      ? `${API_PREFIX}/my-seeds/${encodeURIComponent(String(seedId))}`
      : `${API_PREFIX}/my-seeds`,
    {
      method: seedId ? 'PUT' : 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        draft: payload.draft,
        source_type: payload.source_type || 'create_wizard',
        status: payload.status || 'saved',
      }),
    },
  )

  return readJson<CreatedPersonaRecord>(response)
}
