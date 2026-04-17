import { authHeaders } from '@/services/authService'

const API_PREFIX = '/persona-api'

export type SelfFillAssistantRequestPayload = {
  message: string
  create_mode?: string
  current_step?: string
  active_section?: string
  active_field_key?: string
  active_field_label?: string
  field_context?: string
  conversation_context?: string
  form_snapshot?: Record<string, unknown>
}

export type SelfFillAssistantResponse = {
  mode: 'self_fill_assistant'
  reply: string
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

export async function requestSelfFillAssistant(
  payload: SelfFillAssistantRequestPayload,
): Promise<SelfFillAssistantResponse> {
  const response = await fetch(`${API_PREFIX}/self-fill-assistant`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  return readJson<SelfFillAssistantResponse>(response)
}
