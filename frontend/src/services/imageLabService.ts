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
