const FAVORITE_KEY_PREFIX = 'persona-favorites'

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

export function getFavoriteSlugs(scope: FavoriteScope = 'guest'): string[] {
  return readFavoriteSlugs(scope)
}

export function isFavoriteSlug(slug: string, scope: FavoriteScope = 'guest'): boolean {
  return readFavoriteSlugs(scope).includes(slug)
}

export function toggleFavoriteSlug(slug: string, scope: FavoriteScope = 'guest'): boolean {
  const current = new Set(readFavoriteSlugs(scope))
  if (current.has(slug)) {
    current.delete(slug)
  } else {
    current.add(slug)
  }

  writeFavoriteSlugs(Array.from(current), scope)
  return current.has(slug)
}

export function setFavoriteSlugs(values: string[], scope: FavoriteScope = 'guest') {
  writeFavoriteSlugs(values, scope)
}

export function clearFavoriteSlugs(scope: FavoriteScope = 'guest') {
  writeFavoriteSlugs([], scope)
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
  writeFavoriteSlugs(Array.from(current), toKey)
  clearFavoriteSlugs(fromKey)
}
