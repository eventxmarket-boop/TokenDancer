const API_PREFIX = '/persona-api'

const WIZARD_STATE_KEY = 'persona-create-wizard-state'
const DRAFT_KEY = 'persona-create-latest-draft'
const SAVED_DRAFTS_KEY = 'persona-create-saved-drafts'

export type CreateWizardPayload = {
  create_type: string
  group: string
  source_repo: string
  display_name: string
  input_mode: string
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
  input_mode: string
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

export type CreateWizardDraft = {
  meta: CreateWizardDraftMeta
  profile: string
  mindset: string
  heuristics: string
  expression: string
  guardrails: string
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
