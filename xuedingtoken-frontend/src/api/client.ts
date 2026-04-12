const CONFIGURED_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim() || ''
const ABSOLUTE_URL_RE = /^https?:\/\//i

export const API_BASE_URL = ABSOLUTE_URL_RE.test(CONFIGURED_BASE_URL)
  ? CONFIGURED_BASE_URL.replace(/\/$/, '')
  : '/api'

export interface ApiError {
  detail: string
  message?: string
}

type QueryParamValue = string | number | boolean | undefined

function normalizePath(path: string): string {
  return path.startsWith('/') ? path : `/${path}`
}

export function resolveUrl(path: string, params?: Record<string, QueryParamValue>): string {
  const searchParams = new URLSearchParams()
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.set(key, String(value))
    })
  }

  const base = `${API_BASE_URL}${normalizePath(path)}`
  const query = searchParams.toString()
  return query ? `${base}?${query}` : base
}

class ApiClient {
  private token: string | null = null

  setToken(token: string | null) {
    this.token = token
    if (token) {
      localStorage.setItem('token', token)
    } else {
      localStorage.removeItem('token')
    }
  }

  getToken(): string | null {
    if (!this.token) {
      this.token = localStorage.getItem('token')
    }
    return this.token
  }

  private async request<T>(
    method: string,
    path: string,
    body?: any,
    params?: Record<string, QueryParamValue>
  ): Promise<T> {
    const url = resolveUrl(path, params)

    const headers: Record<string, string> = { 'Content-Type': 'application/json' }
    const token = this.getToken()
    if (token) {
      headers.Authorization = `Bearer ${token}`
    }

    let res: Response
    try {
      res = await fetch(url, {
        method,
        headers,
        body: body !== undefined ? JSON.stringify(body) : undefined,
      })
    } catch (err: any) {
      const msg = err?.message || ''
      if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('Network request failed')) {
        throw new Error(`无法连接后端服务（${API_BASE_URL}），请确认后端已在运行`)
      }
      if (msg.includes('timeout') || msg.includes('Timeout')) {
        throw new Error('请求超时，请检查网络连接')
      }
      console.error(`[Network Error] ${method} ${path}`, err)
      throw new Error('网络异常，请检查网络连接后重试')
    }

    if (res.status === 401) {
      this.setToken(null)
      window.location.href = '/auth/login'
      throw new Error('未登录或登录已过期，请重新登录')
    }

    if (res.status === 403) {
      const err = await res.json().catch(() => ({ detail: '权限不足或账户状态异常' }))
      throw new Error(err.detail || '权限不足，账户可能已被禁用')
    }

    if (res.status === 404) {
      throw new Error(`接口不存在（${res.status}），请更新前端版本`)
    }

    if (res.status === 422) {
      const err = await res.json().catch(() => ({ detail: '数据验证失败' }))
      const msgs = Array.isArray(err.detail)
        ? err.detail.map((e: any) => e.msg || e.loc?.join('.') || '字段错误').join('；')
        : (err.detail || '数据验证失败')
      throw new Error(msgs)
    }

    if (res.status === 429) {
      throw new Error('请求过于频繁，请稍后再试')
    }

    if (res.status >= 500) {
      throw new Error('服务异常，请稍后重试')
    }

    if (!res.ok) {
      let detail = `HTTP ${res.status}`
      try {
        const err = await res.json()
        detail = err.detail || err.message || `HTTP ${res.status}`
      } catch {
        detail = `HTTP ${res.status} ${res.statusText}`
      }
      console.error(`[API Error] ${method} ${path} → ${res.status}`, {
        url,
        status: res.status,
        statusText: res.statusText,
        detail,
      })
      throw new Error(detail)
    }

    if (res.status === 204) return undefined as T
    return res.json()
  }

  get<T>(path: string, params?: Record<string, QueryParamValue>) {
    return this.request<T>('GET', path, undefined, params)
  }

  post<T>(path: string, body?: any) {
    return this.request<T>('POST', path, body)
  }

  patch<T>(path: string, body?: any) {
    return this.request<T>('PATCH', path, body)
  }

  put<T>(path: string, body?: any) {
    return this.request<T>('PUT', path, body)
  }

  delete<T>(path: string) {
    return this.request<T>('DELETE', path)
  }
}

export const api = new ApiClient()
