const API_PREFIX = '/persona-api'

export type HowToDoSection = 'cast' | 'reference' | 'catalog' | 'calendar' | 'clock' | 'records' | 'songs'
export type HowToDoCastMode = 'character' | 'number' | 'coin' | 'taiji'

export type HowToDoRequestPayload = {
  section: HowToDoSection
  cast_mode?: HowToDoCastMode
  question?: string
  cast_seed?: string
  character_text?: string
  number_text?: string
  use_ai?: boolean
  selected_hexagram?: string
}

export type HowToDoCard = {
  label: string
  value: string
}

export type HowToDoCatalogCard = {
  number: number
  name: string
  meaning: string
  binary: string
}

export type HowToDoResponse = {
  section: HowToDoSection
  method_label: string
  question: string
  summary: string
  cards: HowToDoCard[]
  ai_interpretation: string
  suggestions: string[]
  raw_result: Record<string, unknown>
  catalog: HowToDoCatalogCard[]
  model_used: string
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

export async function requestHowToDo(payload: HowToDoRequestPayload): Promise<HowToDoResponse> {
  const response = await fetch(`${API_PREFIX}/how-to-do`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  return readJson<HowToDoResponse>(response)
}
