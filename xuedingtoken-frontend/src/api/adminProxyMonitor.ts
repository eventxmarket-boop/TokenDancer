import { api } from '@/api/client'
import type { AdminModelRoute } from '@/api/adminModelRoutes'
import type { AdminProvider } from '@/api/adminProviders'

export interface AdminProxyOverview {
  total_requests_24h: number
  success_rate_24h: number
  failed_requests_24h: number
  avg_latency_ms_24h: number
  healthy_provider_count: number
  active_provider_count: number
  active_model_count: number
  active_provider_key_count: number
}

export interface AdminProxyFailureLog {
  id: number
  requested_at?: string | null
  public_model_name: string
  provider_id?: number | null
  provider_name?: string | null
  provider_type?: string | null
  provider_key_id?: number | null
  provider_key_name?: string | null
  request_status: string
  latency_ms?: number | null
  error_message?: string | null
  failure_chain_summary?: string | null
  fallback_triggered?: boolean
  policy_type?: string
}

export const adminProxyMonitorApi = {
  overview: () => api.get<AdminProxyOverview>('/admin/proxy-monitor/overview'),
  providers: () => api.get<AdminProvider[]>('/admin/proxy-monitor/providers'),
  models: () => api.get<AdminModelRoute[]>('/admin/proxy-monitor/models'),
  failures: (params?: { limit?: number }) => api.get<AdminProxyFailureLog[]>('/admin/proxy-monitor/failures', params),
  probeProvider: (providerId: number) => api.post<any>(`/admin/proxy-monitor/providers/${providerId}/probe`),
  switchModel: (routeId: number, mode: 'swap' = 'swap') => api.post<any>(`/admin/proxy-monitor/models/${routeId}/switch`, { mode }),
}
