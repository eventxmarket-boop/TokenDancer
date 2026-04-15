const API_PREFIX = '/persona-api'

export type CreateCatalogItem = {
  slug: string
  name: string
  group: string
  create_type: string
  source_repo: string
  repo_url: string
  source_repos?: string[]
  source_urls?: string[]
  description: string
  input_modes: string[]
  stage: string
  entry_type: string
  ui_mode: string
  status: string
  sort_order: number
}

export type CreateCatalogGroup = {
  group: string
  label: string
  description: string
  source_hint: string
  sort_order: number
  items: CreateCatalogItem[]
}

export type CreateCatalogResponse = {
  version: string
  updated_at: string
  groups: CreateCatalogGroup[]
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

export async function loadCreateCatalog(): Promise<CreateCatalogResponse> {
  const response = await fetch(`${API_PREFIX}/create-catalog`)
  return readJson<CreateCatalogResponse>(response)
}
