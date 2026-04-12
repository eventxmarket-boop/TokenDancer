import { defineStore } from 'pinia'
import { ref } from 'vue'
import { api } from '@/api/client'

export interface User {
  id: number
  username: string
  email: string
  status: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(api.getToken())

  const isLoggedIn = () => !!token.value

  async function login(email: string, password: string) {
    const res = await api.post<{ access_token: string; user: User }>('/auth/login', { email, password })
    token.value = res.access_token
    user.value = res.user
    api.setToken(res.access_token)
  }

  async function register(username: string, email: string, password: string) {
    const res = await api.post<User>('/auth/register', { username, email, password })
    return res
  }

  async function fetchMe(): Promise<boolean> {
    if (!token.value) return false
    try {
      const u = await api.get<User>('/auth/me')
      user.value = u
      return true
    } catch {
      token.value = null
      user.value = null
      api.setToken(null)
      return false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    api.setToken(null)
  }

  return { user, token, isLoggedIn, login, register, fetchMe, logout }
})
