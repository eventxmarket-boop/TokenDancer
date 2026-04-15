const FAVORITE_KEY = 'persona-favorites'

function readFavoriteSlugs(): string[] {
  try {
    const raw = localStorage.getItem(FAVORITE_KEY)
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

function writeFavoriteSlugs(values: string[]) {
  localStorage.setItem(FAVORITE_KEY, JSON.stringify(Array.from(new Set(values))))
}

export function getFavoriteSlugs(): string[] {
  return readFavoriteSlugs()
}

export function isFavoriteSlug(slug: string): boolean {
  return readFavoriteSlugs().includes(slug)
}

export function toggleFavoriteSlug(slug: string): boolean {
  const current = new Set(readFavoriteSlugs())
  if (current.has(slug)) {
    current.delete(slug)
  } else {
    current.add(slug)
  }

  writeFavoriteSlugs(Array.from(current))
  return current.has(slug)
}

export function setFavoriteSlugs(values: string[]) {
  writeFavoriteSlugs(values)
}

export function clearFavoriteSlugs() {
  writeFavoriteSlugs([])
}
