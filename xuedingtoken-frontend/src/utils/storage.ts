// localStorage 封装，统一数据持久化
// 提供 get / set / remove，带 JSON 自动序列化
// 支持设置默认值

const PREFIX = 'xd_'

export const storage = {
  get<T>(key: string, fallback: T): T {
    try {
      const raw = localStorage.getItem(PREFIX + key)
      return raw ? JSON.parse(raw) : fallback
    } catch {
      return fallback
    }
  },
  set<T>(key: string, value: T): void {
    try {
      localStorage.setItem(PREFIX + key, JSON.stringify(value))
    } catch {}
  },
  remove(key: string): void {
    localStorage.removeItem(PREFIX + key)
  },
  clear(): void {
    Object.keys(localStorage)
      .filter(k => k.startsWith(PREFIX))
      .forEach(k => localStorage.removeItem(k))
  },
}
