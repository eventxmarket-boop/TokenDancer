import { api } from '@/api/client'

export interface AdminProviderKey {
  id: number
  provider_id: number
  name: string
  key_masked: string
  supported_models?: string | null
  status: string
  weight: number
  rpm_limit?: number | null
  daily_limit?: number | null
  used_count_today?: number
  last_used_at?: string | null
  last_error?: string | null
  notes?: string | null
}

export interface AdminProviderKeyPayload {
  provider_id: number
  name: string
  api_key?: string
  supported_models?: string | null
  status?: string
  weight?: number
  rpm_limit?: number
  daily_limit?: number
  notes?: string | null
}

export const adminProviderKeysApi = {
  list: (params?: { provider_id?: number | string; status?: string }) => api.get<AdminProviderKey[]>('/admin/provider-keys', params),
  get: (id: number) => api.get<AdminProviderKey>(`/admin/provider-keys/${id}`),
  create: (data: AdminProviderKeyPayload) => api.post<AdminProviderKey>('/admin/provider-keys', data),
  update: (id: number, data: Partial<AdminProviderKeyPayload>) => api.patch<AdminProviderKey>(`/admin/provider-keys/${id}`, data),
}
