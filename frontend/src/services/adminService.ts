import { authHeaders } from '@/services/authService'

const API_PREFIX = '/persona-api'

export type LlmConfig = {
  id: number
  provider: string
  base_url: string
  api_key_masked: string
  model_name: string
  temperature: number
  max_tokens: number
  is_default: boolean
  is_enabled: boolean
  created_at: string
  updated_at: string
}

export type LlmConfigDashboard = {
  current: LlmConfig | null
  items: LlmConfig[]
}

export type LlmConfigPayload = {
  id?: number | null
  provider: string
  base_url: string
  api_key: string
  model_name: string
  temperature: number
  max_tokens: number
  is_default: boolean
  is_enabled: boolean
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
    // fall back to raw text
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

export async function getLlmConfig(): Promise<LlmConfigDashboard> {
  const response = await fetch(`${API_PREFIX}/admin/llm-config`, {
    headers: authHeaders(),
  })
  return readJson<LlmConfigDashboard>(response)
}

export async function saveLlmConfig(payload: LlmConfigPayload): Promise<LlmConfig> {
  const response = await fetch(`${API_PREFIX}/admin/llm-config`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  return readJson<LlmConfig>(response)
}

export async function updateLlmConfig(id: number, payload: LlmConfigPayload): Promise<LlmConfig> {
  const response = await fetch(`${API_PREFIX}/admin/llm-config/${encodeURIComponent(String(id))}`, {
    method: 'PUT',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  return readJson<LlmConfig>(response)
}

export async function activateLlmConfig(id: number): Promise<LlmConfig> {
  const response = await fetch(`${API_PREFIX}/admin/llm-config/${encodeURIComponent(String(id))}/activate`, {
    method: 'POST',
    headers: authHeaders(),
  })

  return readJson<LlmConfig>(response)
}
