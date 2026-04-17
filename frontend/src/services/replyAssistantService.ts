import { authHeaders } from '@/services/authService'
import type { UniversalCreateWizardRawMaterials } from '@/services/createWizardService'

const API_PREFIX = '/persona-api'

export type ReplyAssistantRequestPayload = {
  message: string
  target_person_type: string
  target_person_label?: string
  scene_type: string
  current_context?: string
  target_goal?: string
  tone_hint?: string
  relationship_status?: string
  conversation_context?: string
  raw_materials?: UniversalCreateWizardRawMaterials | Record<string, unknown>
}

export type ReplyAssistantUnderstandingResult = {
  meaning_guess: string
  emotion_guess: string
  intent_guess: string
  relationship_state_guess: string
  scene_guess: string
  risk_flags: string[]
}

export type ReplyAssistantReplyCandidate = {
  label: string
  text: string
  style_tags: string[]
  reason: string
}

export type ReplyAssistantPredictedReply = {
  label: string
  text: string
  risk_level: string
}

export type ReplyAssistantToneProfile = {
  label: string
  style_tags: string[]
  guidance: string
}

export type ReplyAssistantResponse = {
  mode: 'reply_assistant'
  target_person_type: string
  target_person_label: string
  scene_type: string
  scene_label: string
  understanding_result: ReplyAssistantUnderstandingResult
  reply_candidates: ReplyAssistantReplyCandidate[]
  predicted_replies: ReplyAssistantPredictedReply[]
  risk_flags: string[]
  tone_profile: ReplyAssistantToneProfile
  recommended_reply: string
  material_summary: string
  context_summary: string
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

export async function requestReplyAssistant(
  payload: ReplyAssistantRequestPayload,
): Promise<ReplyAssistantResponse> {
  const response = await fetch(`${API_PREFIX}/reply-assistant`, {
    method: 'POST',
    headers: authHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(payload),
  })

  return readJson<ReplyAssistantResponse>(response)
}
