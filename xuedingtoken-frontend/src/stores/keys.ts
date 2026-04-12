import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { api } from '@/api/client'

export interface APIKey {
  id: number
  name: string
  key_value: string
  group_name: string
  status: string
  allowed_models?: string | null
  expires_at?: string | null
  last_used_at: string | null
  last_used_model?: string | null
  created_at: string
}

export interface APIKeyPayload {
  name?: string
  group_name?: string
  status?: string
  allowed_models?: string | null
  expires_at?: string | null
}

export const useKeyStore = defineStore('keys', () => {
  const keys = ref<APIKey[]>([])
  const search = ref('')
  const filterGroup = ref('全部')
  const filterStatus = ref('全部')

  async function fetchKeys() {
    keys.value = await api.get<APIKey[]>('/keys')
  }

  async function createKey(payload: { name: string; group_name?: string; allowed_models?: string | null; expires_at?: string | null }) {
    const key = await api.post<APIKey>('/keys', payload)
    await fetchKeys()
    return key
  }

  async function updateKey(id: number, data: APIKeyPayload) {
    const key = await api.patch<APIKey>(`/keys/${id}`, data)
    const idx = keys.value.findIndex((item: APIKey) => item.id === id)
    if (idx !== -1) keys.value[idx] = key
    return key
  }

  async function deleteKey(id: number) {
    await api.delete(`/keys/${id}`)
    keys.value = keys.value.filter((item: APIKey) => item.id !== id)
  }

  const filtered = computed(() => {
    const keyword = search.value.trim().toLowerCase()
    return keys.value.filter((item: APIKey) => {
      const matchName = !keyword
        || item.name.toLowerCase().includes(keyword)
        || item.key_value.toLowerCase().includes(keyword)
        || (item.last_used_model || '').toLowerCase().includes(keyword)
        || (item.allowed_models || '').toLowerCase().includes(keyword)
      const matchGroup = filterGroup.value === '全部' || item.group_name === filterGroup.value
      const matchStatus = filterStatus.value === '全部' || item.status === filterStatus.value
      return matchName && matchGroup && matchStatus
    })
  })

  return { keys, filtered, search, filterGroup, filterStatus, fetchKeys, createKey, updateKey, deleteKey }
})
