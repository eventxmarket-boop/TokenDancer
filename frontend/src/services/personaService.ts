import { authHeaders } from '@/services/authService'

export type Persona = {
  id: string
  slug: string
  name: string
  category: string
  avatar: string | null
  intro: string
  profile: string
  tags: string[]
  topics: string[]
  recommendedQuestions: string[]
  version: string
  status: string
  isSeed?: boolean
  seedSource?: string
  seedGroup?: string
  isFeatured?: boolean
  isFavoritable?: boolean
  personaKind?: string
  sortOrder?: number
}

const API_PREFIX = '/persona-api'

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await readErrorMessage(response)
    throw new Error(detail || `Request failed with status ${response.status}`)
  }

  return (await response.json()) as T
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
    // fall back to raw text below
  }

  return text.trim()
}

export async function listPersonas(): Promise<Persona[]> {
  const response = await fetch(`${API_PREFIX}/personas`, {
    headers: authHeaders(),
  })
  return readJson<Persona[]>(response)
}

export async function loadPersona(id: string): Promise<Persona | null> {
  const response = await fetch(`${API_PREFIX}/personas/${encodeURIComponent(id)}`, {
    headers: authHeaders(),
  })
  if (response.status === 404) {
    return null
  }
  return readJson<Persona>(response)
}

export async function loadSeedPersonas(): Promise<Persona[]> {
  const response = await fetch(`${API_PREFIX}/seed-personas`, {
    headers: authHeaders(),
  })
  return readJson<Persona[]>(response)
}
