import { loadSavedItems, replaceSavedItems } from '@/services/savedItemsService'

const FAVORITE_KEY_PREFIX = 'persona-favorites'
const FAVORITE_KIND = 'seed_favorites'

export type FavoriteScope = string | number | null | undefined

export function getFavoriteScopeKey(scope: FavoriteScope = 'guest'): string {
  if (typeof scope === 'number' && Number.isFinite(scope) && scope > 0) {
    return `user:${Math.trunc(scope)}`
  }
  const text = String(scope || '').trim()
  if (!text || text === 'guest') {
    return 'guest'
  }
  return text
}

function getFavoriteStorageKey(scope: FavoriteScope = 'guest') {
  return `${FAVORITE_KEY_PREFIX}:${getFavoriteScopeKey(scope)}`
}

function readFavoriteSlugs(scope: FavoriteScope = 'guest'): string[] {
  try {
    const raw = localStorage.getItem(getFavoriteStorageKey(scope))
    if (!raw) {
      return []
    }

    const parsed = JSON.parse(raw) as unknown
    if (!Array.isArray(parsed)) {
      return []
    }

    return parsed
      .map((value) => (typeof value === 'string' ? value.trim() : ''))
      .filter((value) => value.length > 0)
  } catch {
    return []
  }
}

function writeFavoriteSlugs(values: string[], scope: FavoriteScope = 'guest') {
  localStorage.setItem(getFavoriteStorageKey(scope), JSON.stringify(Array.from(new Set(values))))
}

function normalizeSlugs(values: string[]) {
  return Array.from(new Set(values.map((value) => value.trim()).filter((value) => value.length > 0)))
}

async function syncFavoriteSlugsToRemote(values: string[], scope: FavoriteScope = 'guest') {
  const key = getFavoriteScopeKey(scope)
  if (key === 'guest') {
    return
  }

  await replaceSavedItems(FAVORITE_KIND, values.map((slug) => ({
    item_key: slug,
    title: slug,
    pinned: true,
    payload: { slug },
  })))
}

export function getFavoriteSlugs(scope: FavoriteScope = 'guest'): string[] {
  return readFavoriteSlugs(scope)
}

export async function loadFavoriteSlugs(scope: FavoriteScope = 'guest'): Promise<string[]> {
  const localValues = normalizeSlugs(readFavoriteSlugs(scope))
  const key = getFavoriteScopeKey(scope)
  if (key === 'guest') {
    return localValues
  }

  try {
    const remote = await loadSavedItems<{ slug?: string }>(FAVORITE_KIND)
    const remoteValues = remote
      .map((item) => item.payload?.slug || item.item_key)
      .filter((value): value is string => typeof value === 'string' && value.trim().length > 0)
    const merged = normalizeSlugs([...localValues, ...remoteValues])
    writeFavoriteSlugs(merged, scope)
    if (merged.length || remote.length) {
      await syncFavoriteSlugsToRemote(merged, scope)
    }
    return merged
  } catch {
    return localValues
  }
}

export function isFavoriteSlug(slug: string, scope: FavoriteScope = 'guest'): boolean {
  return readFavoriteSlugs(scope).includes(slug)
}

export async function toggleFavoriteSlug(slug: string, scope: FavoriteScope = 'guest'): Promise<boolean> {
  const current = new Set(readFavoriteSlugs(scope))
  if (current.has(slug)) {
    current.delete(slug)
  } else {
    current.add(slug)
  }

  const values = Array.from(current)
  writeFavoriteSlugs(values, scope)
  await syncFavoriteSlugsToRemote(values, scope)
  return current.has(slug)
}

export async function setFavoriteSlugs(values: string[], scope: FavoriteScope = 'guest') {
  const next = normalizeSlugs(values)
  writeFavoriteSlugs(next, scope)
  await syncFavoriteSlugsToRemote(next, scope)
}

export async function clearFavoriteSlugs(scope: FavoriteScope = 'guest') {
  writeFavoriteSlugs([], scope)
  await syncFavoriteSlugsToRemote([], scope)
}

export function migrateFavoriteSlugs(fromScope: FavoriteScope, toScope: FavoriteScope) {
  const fromKey = getFavoriteScopeKey(fromScope)
  const toKey = getFavoriteScopeKey(toScope)
  if (!fromKey || !toKey || fromKey === toKey) {
    return
  }
  const current = new Set([
    ...readFavoriteSlugs(fromKey),
    ...readFavoriteSlugs(toKey),
  ])
  const merged = Array.from(current)
  writeFavoriteSlugs(merged, toKey)
  void syncFavoriteSlugsToRemote(merged, toScope)
  void clearFavoriteSlugs(fromKey)
}
