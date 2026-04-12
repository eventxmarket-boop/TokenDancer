import { api } from '@/api/client'
import type { ProviderType } from '@/constants/providerTypes'

export interface AdminProvider {
  id: number
  name: string
  provider_type: ProviderType
  base_url?: string | null
  is_active: boolean
  priority: number
  timeout_seconds: number
  health_status?: string
  last_health_check_at?: string | null
  notes?: string | null
}

export interface AdminProviderPayload {
  name: string
  provider_type: ProviderType
  base_url?: string
  is_active?: boolean
  priority?: number
  timeout_seconds?: number
  notes?: string
}

export const adminProvidersApi = {
  list: () => api.get<AdminProvider[]>('/admin/providers'),
  get: (id: number) => api.get<AdminProvider>(`/admin/providers/${id}`),
  create: (data: AdminProviderPayload) => api.post<AdminProvider>('/admin/providers', data),
  update: (id: number, data: Partial<AdminProviderPayload>) => api.patch<AdminProvider>(`/admin/providers/${id}`, data),
}
