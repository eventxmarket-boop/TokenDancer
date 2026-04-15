const API_PREFIX = '/persona-api'

export type ChatUsage = {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
}

export type ChatResponse = {
  session_id: string
  persona_slug: string
  reply: string
  model: string
  usage: ChatUsage
  latency_ms: number
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

export async function sendChatMessage(payload: {
  personaSlug: string
  sessionId?: string | null
  message: string
}): Promise<ChatResponse> {
  const response = await fetch(`${API_PREFIX}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      persona_slug: payload.personaSlug,
      session_id: payload.sessionId || null,
      message: payload.message,
    }),
  })

  return readJson<ChatResponse>(response)
}

export async function clearChatSession(sessionId: string): Promise<{ session_id: string; status: string }> {
  const response = await fetch(`${API_PREFIX}/sessions/${encodeURIComponent(sessionId)}/clear`, {
    method: 'POST',
  })

  return readJson<{ session_id: string; status: string }>(response)
}
