import { api } from '@/api/client'

export interface AdminModelRoute {
  id: number
  public_model_name: string
  provider_id: number
  provider_name?: string | null
  provider_type?: string | null
  provider_model_name: string
  fallback_provider_id?: number | null
  fallback_provider_name?: string | null
  fallback_provider_type?: string | null
  fallback_model_name?: string | null
  is_active: boolean
  priority: number
  cost_multiplier: number
  max_context?: number | null
  notes?: string | null
  created_at: string
  policy_name?: string | null
  policy_type: string
  retry_count: number
  cooldown_seconds: number
  timeout_seconds: number
  request_count_24h: number
  success_rate_24h: number
  avg_latency_ms_24h: number
  failure_count_24h: number
  last_request_at?: string | null
  last_error?: string | null
}

export interface AdminModelRoutePayload {
  public_model_name: string
  provider_id: number
  provider_model_name: string
  fallback_provider_id?: number | null
  fallback_model_name?: string | null
  is_active?: boolean
  priority?: number
  cost_multiplier?: number
  max_context?: number | null
  notes?: string | null
}

export const adminModelRoutesApi = {
  list: () => api.get<AdminModelRoute[]>('/admin/model-routes'),
  create: (data: AdminModelRoutePayload) => api.post<AdminModelRoute>('/admin/model-routes', data),
  update: (id: number, data: Partial<AdminModelRoutePayload>) => api.patch<AdminModelRoute>(`/admin/model-routes/${id}`, data),
}
