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

const INTIMATE_CANONICAL_SLUG = 'relationship_management'
const INTIMATE_CANONICAL_NAME = '关系经营'
const INTIMATE_CANONICAL_SOURCE_REPOS = new Set([
  'relationship-training-skill',
  'xinyi',
  'partner-skill',
  'npy-skill',
  'crush-skill',
])
const INTIMATE_CANONICAL_SOURCE_URLS = new Set([
  'https://github.com/TammyTan516/relationship-training-skill',
  'https://github.com/kroxchan/xinyi',
  'https://github.com/NatalieCao323/partner-skill',
  'https://github.com/wwwttlll/npy-skill',
  'https://github.com/yyyyyyylll/crush-skill',
])

function normalizeIntimateCatalogSlug(value: string) {
  if (
    value === 'relationship_understanding' ||
    value === 'relationship_maintenance' ||
    value === 'partner_maintenance' ||
    value === 'message_simulation' ||
    value === 'crush'
  ) {
    return INTIMATE_CANONICAL_SLUG
  }
  return value
}

function normalizeIntimateCatalogItem(item: CreateCatalogItem): CreateCatalogItem {
  if (item.create_type !== 'intimate_companion') {
    return item
  }

  const normalizedSlug = normalizeIntimateCatalogSlug(item.slug)
  const normalizedSourceRepos = Array.from(
    new Set(
      [item.source_repo, ...(item.source_repos || [])]
        .filter((value): value is string => Boolean(value && value.trim()))
        .map((value) => String(value).trim()),
    ),
  )
  const normalizedSourceUrls = Array.from(
    new Set(
      [item.repo_url, ...(item.source_urls || [])]
        .filter((value): value is string => Boolean(value && value.trim()))
        .map((value) => String(value).trim()),
    ),
  )

  const canonicalSourceRepo = normalizedSourceRepos.find((repo) => INTIMATE_CANONICAL_SOURCE_REPOS.has(repo))
    || item.source_repo
    || normalizedSourceRepos[0]
    || 'relationship-training-skill+xinyi+partner-skill+npy-skill+crush-skill'

  const canonicalRepoUrl = normalizedSourceUrls.find((url) => INTIMATE_CANONICAL_SOURCE_URLS.has(url))
    || item.repo_url
    || normalizedSourceUrls[0]
    || 'https://github.com/TammyTan516/relationship-training-skill'

  return {
    ...item,
    slug: normalizedSlug,
    name: normalizedSlug === INTIMATE_CANONICAL_SLUG ? INTIMATE_CANONICAL_NAME : item.name,
    source_repo: canonicalSourceRepo,
    repo_url: canonicalRepoUrl,
    source_repos: normalizedSourceRepos.length ? normalizedSourceRepos : item.source_repos,
    source_urls: normalizedSourceUrls.length ? normalizedSourceUrls : item.source_urls,
  }
}

function normalizeCreateCatalogGroup(group: CreateCatalogGroup): CreateCatalogGroup {
  if (group.group !== 'relationship_intimate') {
    return group
  }

  const orderedItems = group.items
    .map(normalizeIntimateCatalogItem)
    .sort((left, right) => left.sort_order - right.sort_order)

  const deduped = new Map<string, CreateCatalogItem>()
  for (const item of orderedItems) {
    const canonicalSlug = normalizeIntimateCatalogSlug(item.slug)
    const existing = deduped.get(canonicalSlug)
    if (!existing) {
      deduped.set(canonicalSlug, { ...item, slug: canonicalSlug, name: canonicalSlug === INTIMATE_CANONICAL_SLUG ? INTIMATE_CANONICAL_NAME : item.name })
      continue
    }

    const mergedSourceRepos = Array.from(
      new Set([...(existing.source_repos || []), ...(item.source_repos || []), existing.source_repo, item.source_repo].filter((value): value is string => Boolean(value && value.trim()))),
    )
    const mergedSourceUrls = Array.from(
      new Set([...(existing.source_urls || []), ...(item.source_urls || []), existing.repo_url, item.repo_url].filter((value): value is string => Boolean(value && value.trim()))),
    )
    deduped.set(canonicalSlug, {
      ...existing,
      ...item,
      slug: canonicalSlug,
      name: canonicalSlug === INTIMATE_CANONICAL_SLUG ? INTIMATE_CANONICAL_NAME : existing.name,
      source_repo: mergedSourceRepos[0] || existing.source_repo || item.source_repo,
      repo_url: mergedSourceUrls[0] || existing.repo_url || item.repo_url,
      source_repos: mergedSourceRepos,
      source_urls: mergedSourceUrls,
      description: existing.description || item.description,
    })
  }

  return {
    ...group,
    items: Array.from(deduped.values()).sort((left, right) => left.sort_order - right.sort_order),
  }
}

function normalizeCreateCatalogResponse(response: CreateCatalogResponse): CreateCatalogResponse {
  return {
    ...response,
    groups: response.groups.map(normalizeCreateCatalogGroup),
  }
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
  const catalog = await readJson<CreateCatalogResponse>(response)
  return normalizeCreateCatalogResponse(catalog)
}
