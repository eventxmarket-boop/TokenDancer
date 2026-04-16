const API_PREFIX = '/persona-api'

const WIZARD_STATE_KEY = 'persona-create-wizard-state'
const DRAFT_KEY = 'persona-create-latest-draft'
const SAVED_DRAFTS_KEY = 'persona-create-saved-drafts'

export type CreateWizardPayload = {
  create_type: string
  group: string
  source_repo: string
  display_name: string
  create_mode: string
  input_mode: string
  input_modes: string[]
  schema_key: string
  form_data: Record<string, unknown>
}

export type CreateWizardDraftMeta = {
  id: string
  slug: string
  name: string
  category: string
  version: string
  status: string
  create_type: string
  create_mode: string
  input_mode: string
  input_modes: string[]
  group: string
  display_name: string
  schema_key: string
  source_repo: string
  repo_url: string
  source_repos: string[]
  source_hint: string
  stage: string
  persona_kind: string
  generated_at: string
}

export type FamilyCompanionPersonaProfile = {
  relationship_type: string
  name: string
  tone: string
  catchphrases: string[]
  comfort_style: string
  celebration_style: string
  boundaries: string
}

export type FamilyCompanionMemoryBase = {
  shared_events: string[]
  important_advice: string[]
  daily_habits: string[]
  emotional_triggers: string[]
  chat_history_summary: string
  memory_fragments: string[]
  text_materials: string[]
  image_notes: string[]
  voice_notes: string[]
}

export type FamilyCompanionEmotionRules = {
  summary: string
  emotion_state_priority: string[]
  response_sequence: string[]
  response_temperature_map: Record<string, string>
  memory_priority_rules: string[]
  boundary_rules: string[]
}

export type TextMaterialDocument = {
  filename: string
  content: string
}

export type FamilyCompanionRawMaterials = {
  chat_history_text: string
  memory_notes_text: string
  text_materials_text: string
  uploaded_text_documents: TextMaterialDocument[]
  image_notes_text: string
  photo_notes_text: string
  voice_notes_text: string
}

export type ReunionPersonaProfile = {
  relationship_type: string
  name: string
  tone: string
  remembrance_style: string
  comfort_style: string
  boundaries: string
}

export type ReunionPersonaMemoryBase = {
  chat_history_summary: string
  diary_notes: string[]
  letter_notes: string[]
  photo_notes: string[]
  voice_notes: string[]
  memory_fragments: string[]
  shared_memories: string[]
}

export type ReunionPersonaRawMaterials = {
  chat_history_text: string
  diary_text: string
  letter_text: string
  memory_notes_text: string
  uploaded_text_documents: TextMaterialDocument[]
  photo_notes_text: string
  voice_notes_text: string
}

export type IntimateCompanionRawMaterials = {
  chat_history_text: string
  memory_notes_text: string
  text_materials_text: string
  uploaded_text_documents: TextMaterialDocument[]
  image_notes_text: string
  voice_notes_text: string
  conflict_text: string
  draft_message_text: string
  recent_context_text: string
  reply_style_samples_text: string
  relationship_status_text: string
  interaction_patterns_text: string
  history_text: string
  expression_samples_text: string
}

export type ReunionPersonaRetrievalPolicy = {
  mode: string
  progressive_recall: boolean
  priority_rules: string[]
  fallback_rules: string[]
}

export type ReunionPersonaSafetyGuardrails = {
  boundaries: string[]
  emotional_protection: string[]
  avoid_triggers: string[]
}

export type SelfPersonaUnifiedLayer = {
  summary: string
  points: string[]
}

export type SelfPersonaUnifiedDraft = {
  create_mode: string
  input_modes: string[]
  work_system: SelfPersonaUnifiedLayer
  reply_persona: SelfPersonaUnifiedLayer
  thinking_dna: SelfPersonaUnifiedLayer
  memory_evidence: SelfPersonaUnifiedLayer
  reflection_rules: SelfPersonaUnifiedLayer
}

export type IntimateCompanionRelationshipProfile = {
  relationship_type: string
  name: string
  relationship_stage: string
  tone: string
  response_temperature: string
  catchphrases: string[]
  boundaries: string
}

export type IntimateCompanionMemoryBase = {
  conversation_samples: string[]
  interaction_rules: string[]
  relationship_goals: string[]
  key_memories: string[]
  relationship_context: string
  misunderstanding_points: string[]
  rewrite_targets: string[]
  target_persona_profile: Record<string, unknown>
  conversation_context: Record<string, unknown>
  reply_style_samples: string[]
  simulation_preferences: Record<string, unknown>
  interaction_patterns: string[]
  maintenance_goals: string[]
  relationship_memory: string[]
  expression_samples: string[]
  response_temperature: string
  boundaries: string[]
}

export type CreateWizardDraft = {
  meta: CreateWizardDraftMeta
  profile: string
  mindset: string
  heuristics: string
  expression: string
  guardrails: string
  relationship_type?: string
  raw_materials?: FamilyCompanionRawMaterials | ReunionPersonaRawMaterials | Record<string, unknown> | null
  emotion_rules?: FamilyCompanionEmotionRules | Record<string, unknown> | null
  self_persona_unified?: SelfPersonaUnifiedDraft | null
  persona_profile?: FamilyCompanionPersonaProfile | null
  memory_base?: FamilyCompanionMemoryBase | null
  reunion_persona_profile?: ReunionPersonaProfile | null
  reunion_memory_base?: ReunionPersonaMemoryBase | null
  reunion_memory_retrieval_policy?: ReunionPersonaRetrievalPolicy | null
  reunion_safety_guardrails?: ReunionPersonaSafetyGuardrails | null
  relationship_profile?: IntimateCompanionRelationshipProfile | null
  intimate_memory_base?: IntimateCompanionMemoryBase | null
  intimate_understanding?: Record<string, unknown> | null
  intimate_message_simulation?: Record<string, unknown> | null
  intimate_relationship_maintenance?: Record<string, unknown> | null
  intimate_past_relationship?: Record<string, unknown> | null
}

export type CreateWizardDraftResponse = {
  draft: CreateWizardDraft
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

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await readErrorMessage(response)
    throw new Error(detail || `Request failed with status ${response.status}`)
  }

  return (await response.json()) as T
}

export async function submitCreateDraft(payload: CreateWizardPayload): Promise<CreateWizardDraft> {
  const response = await fetch(`${API_PREFIX}/create-wizard/draft`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  const result = await readJson<CreateWizardDraftResponse>(response)
  return result.draft
}

export function saveWizardState(state: unknown) {
  window.sessionStorage.setItem(WIZARD_STATE_KEY, JSON.stringify(state))
}

export function loadWizardState<T = unknown>(): T | null {
  const raw = window.sessionStorage.getItem(WIZARD_STATE_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

export function clearWizardState() {
  window.sessionStorage.removeItem(WIZARD_STATE_KEY)
}

export function saveLatestDraft(draft: CreateWizardDraft) {
  window.sessionStorage.setItem(DRAFT_KEY, JSON.stringify(draft))
}

export function loadLatestDraft(): CreateWizardDraft | null {
  const raw = window.sessionStorage.getItem(DRAFT_KEY)
  if (!raw) {
    return null
  }

  try {
    return JSON.parse(raw) as CreateWizardDraft
  } catch {
    return null
  }
}

export function saveDraftLocally(draft: CreateWizardDraft) {
  const drafts = loadSavedDrafts()
  drafts.unshift(draft)
  window.localStorage.setItem(SAVED_DRAFTS_KEY, JSON.stringify(drafts.slice(0, 12)))
}

export function loadSavedDrafts(): CreateWizardDraft[] {
  const raw = window.localStorage.getItem(SAVED_DRAFTS_KEY)
  if (!raw) {
    return []
  }

  try {
    const parsed = JSON.parse(raw) as unknown
    return Array.isArray(parsed) ? (parsed as CreateWizardDraft[]) : []
  } catch {
    return []
  }
}
