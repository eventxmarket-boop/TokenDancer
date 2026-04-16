const AUTH_STATE_KEY = 'persona-auth-state'
const API_PREFIX = '/persona-api'

export type AuthUser = {
  id: number
  username: string
  email: string
  status: string
  role: string
  balance: number
  available_balance: number
  created_at: string | null
}

export type AuthTokenResponse = {
  access_token: string
  token_type: string
  user: AuthUser
}

export type RegisterPayload = {
  username: string
  email: string
  password: string
}

export type LoginPayload = {
  username_or_email: string
  password: string
}

export type StoredAuthState = {
  token: string
  user: AuthUser | null
}

function readErrorMessage(response: Response): Promise<string> {
  return response.text().then((text) => {
    try {
      const payload = JSON.parse(text) as Record<string, unknown>
      const message = payload.detail ?? payload.message
      if (typeof message === 'string' && message.trim()) {
        return message.trim()
      }
    } catch {
      // fall through to raw text below
    }
    return text.trim()
  })
}

async function readJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await readErrorMessage(response)
    throw new Error(detail || `Request failed with status ${response.status}`)
  }

  return (await response.json()) as T
}

export function readStoredAuthState(): StoredAuthState {
  if (typeof localStorage === 'undefined') {
    return { token: '', user: null }
  }

  try {
    const raw = localStorage.getItem(AUTH_STATE_KEY)
    if (!raw) {
      return { token: '', user: null }
    }
    const parsed = JSON.parse(raw) as Partial<StoredAuthState>
    return {
      token: typeof parsed.token === 'string' ? parsed.token.trim() : '',
      user: parsed.user && typeof parsed.user === 'object' ? (parsed.user as AuthUser) : null,
    }
  } catch {
    return { token: '', user: null }
  }
}

export function getAuthToken(): string {
  return readStoredAuthState().token
}

export function getAuthUser(): AuthUser | null {
  return readStoredAuthState().user
}

export function setStoredAuthState(state: StoredAuthState) {
  if (typeof localStorage === 'undefined') {
    return
  }
  localStorage.setItem(
    AUTH_STATE_KEY,
    JSON.stringify({
      token: state.token,
      user: state.user,
    }),
  )
}

export function clearStoredAuthState() {
  if (typeof localStorage === 'undefined') {
    return
  }
  localStorage.removeItem(AUTH_STATE_KEY)
}

export function authHeaders(extraHeaders: HeadersInit = {}): HeadersInit {
  const token = getAuthToken()
  const headers = new Headers(extraHeaders)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  return headers
}

export async function register(payload: RegisterPayload): Promise<AuthTokenResponse> {
  const response = await fetch(`${API_PREFIX}/auth/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  return readJson<AuthTokenResponse>(response)
}

export async function login(payload: LoginPayload): Promise<AuthTokenResponse> {
  const response = await fetch(`${API_PREFIX}/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })
  return readJson<AuthTokenResponse>(response)
}

export async function me(): Promise<AuthUser> {
  const response = await fetch(`${API_PREFIX}/auth/me`, {
    headers: authHeaders(),
  })
  return readJson<AuthUser>(response)
}
