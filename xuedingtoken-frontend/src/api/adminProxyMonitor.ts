import { api } from '@/api/client'

export const adminProxyMonitorApi = {
  overview: () => api.get<any>('/admin/proxy-monitor/overview'),
  providers: () => api.get<any[]>('/admin/proxy-monitor/providers'),
  models: () => api.get<any[]>('/admin/proxy-monitor/models'),
  failures: (params?: { limit?: number }) => api.get<any[]>('/admin/proxy-monitor/failures', params),
  probeProvider: (providerId: number) => api.post<any>(`/admin/proxy-monitor/providers/${providerId}/probe`),
  switchModel: (routeId: number, mode: 'swap' = 'swap') => api.post<any>(`/admin/proxy-monitor/models/${routeId}/switch`, { mode }),
}
