import { computed, ref } from 'vue'

import {
  authHeaders,
  clearStoredAuthState,
  getAuthToken,
  getAuthUser,
  login as loginRequest,
  me as loadCurrentUser,
  register as registerRequest,
  readStoredAuthState,
  setStoredAuthState,
  type AuthTokenResponse,
  type AuthUser,
  type LoginPayload,
  type RegisterPayload,
} from '@/services/authService'
import { migrateFavoriteSlugs } from '@/services/favoriteService'

const authToken = ref(getAuthToken())
const currentUser = ref<AuthUser | null>(getAuthUser())
const authReady = ref(false)
const authLoading = ref(false)

let bootstrapPromise: Promise<void> | null = null

function applyAuthSession(response: AuthTokenResponse) {
  authToken.value = response.access_token
  currentUser.value = response.user
  setStoredAuthState({
    token: response.access_token,
    user: response.user,
  })
  void migrateFavoriteSlugs('guest', `user:${response.user.id}`)
}

export const isLoggedIn = computed(() => Boolean(authToken.value && currentUser.value))
export const authUser = computed(() => currentUser.value)

export async function ensureAuthReady(force = false) {
  if (bootstrapPromise && !force) {
    return bootstrapPromise
  }

  bootstrapPromise = (async () => {
    authLoading.value = true
    try {
      const stored = readStoredAuthState()
      if (!stored.token) {
        authToken.value = ''
        currentUser.value = null
        clearStoredAuthState()
        authReady.value = true
        return
      }

      authToken.value = stored.token
      currentUser.value = stored.user

      const user = await loadCurrentUser()
      currentUser.value = user
      setStoredAuthState({ token: stored.token, user })
      void migrateFavoriteSlugs('guest', `user:${user.id}`)
    } catch {
      authToken.value = ''
      currentUser.value = null
      clearStoredAuthState()
    } finally {
      authLoading.value = false
      authReady.value = true
      bootstrapPromise = null
    }
  })()

  return bootstrapPromise
}

export async function loginWithAuth(payload: LoginPayload) {
  const response = await loginRequest(payload)
  applyAuthSession(response)
  return response
}

export async function registerWithAuth(payload: RegisterPayload) {
  const response = await registerRequest(payload)
  applyAuthSession(response)
  return response
}

export function logout() {
  authToken.value = ''
  currentUser.value = null
  authReady.value = true
  clearStoredAuthState()
}

export function getAuthHeaders(extraHeaders: HeadersInit = {}) {
  return authHeaders(extraHeaders)
}

export function getCurrentUserId(): number | null {
  return currentUser.value?.id || null
}
