import { authHeaders } from '@/services/authService'

const API_PREFIX = '/persona-api'

export type ImageLabGeneratePayload = {
  prompt: string
  size: '1024x1024' | '1024x1536' | '1536x1024' | 'auto'
  quality: 'low' | 'medium' | 'high' | 'auto'
  output_format: 'png' | 'webp' | 'jpeg'
}

export type ImageLabGenerateResponse = {
  image_base64: string
  mime_type: string
  model: string
  size: string
  quality: string
  output_format: string
}

export type PlusBridgeEvent = {
  accepted: boolean
  received_at: string
  stage: string
  message: string
  mode: string
  transport: string
  prompt_length: number
  size: string
  quality: string
  output_format: string
  success?: boolean | null
  error?: string | null
  user_id?: string | null
}

export type PlusBridgeStatus = {
  updated_at?: string | null
  mode: string
  transport: string
  stage: string
  message: string
  prompt: string
  prompt_length: number
  size: string
  quality: string
  output_format: string
  model: string
  page_url: string
  image_base64: string
  mime_type: string
  success?: boolean | null
  error?: string | null
  user_id?: string | null
  events: Array<Record<string, unknown>>
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
    // fallback to raw text
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

export async function generateImageLabImage(
  payload: ImageLabGeneratePayload,
): Promise<ImageLabGenerateResponse> {
  const response = await fetch(`${API_PREFIX}/image-lab/generate`, {
    method: 'POST',
    headers: authHeaders({
      'Content-Type': 'application/json',
      'X-Internal-User': 'internal-test-user',
    }),
    body: JSON.stringify(payload),
  })

  return readJson<ImageLabGenerateResponse>(response)
}

export async function getPlusBridgeStatus(): Promise<PlusBridgeStatus | null> {
  const response = await fetch(`${API_PREFIX}/image-lab/bridge/status`, {
    headers: authHeaders(),
  })
  return readJson<PlusBridgeStatus | null>(response)
}

export async function getLatestPlusBridgeResult(): Promise<PlusBridgeStatus | null> {
  const response = await fetch(`${API_PREFIX}/image-lab/bridge/latest`, {
    headers: authHeaders(),
  })
  return readJson<PlusBridgeStatus | null>(response)
}
