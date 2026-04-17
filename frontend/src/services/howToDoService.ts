const API_PREFIX = '/persona-api'

export type HowToDoMode = 'zhouyi' | 'liuyao' | 'bazi'

export type HowToDoRequestPayload = {
  mode: HowToDoMode
  question?: string
  cast_seed?: string
  liuyao_cast_mode?: 'time' | 'manual'
  liuyao_lines?: number[]
  birth_year?: number
  birth_month?: number
  birth_day?: number
  birth_hour?: number
  gender?: 'male' | 'female' | string
  use_ai?: boolean
}

export type HowToDoCard = {
  label: string
  value: string
}

export type HowToDoResponse = {
  mode: HowToDoMode
  method_label: string
  question: string
  summary: string
  cards: HowToDoCard[]
  ai_interpretation: string
  suggestions: string[]
  raw_result: Record<string, unknown>
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
