import { api } from '@/api/client'

export type RoutePolicyType = 'fixed' | 'fallback' | 'weighted' | 'cost_first'

export interface AdminRoutePolicy {
  id: number
  name: string
  public_model_name: string
  primary_provider_id: number
  primary_provider_name?: string | null
  secondary_provider_id?: number | null
  secondary_provider_name?: string | null
  policy_type: RoutePolicyType
  retry_count: number
  cooldown_seconds: number
  timeout_seconds: number
  is_active: boolean
  notes?: string | null
  created_at: string
  linked_route_id?: number | null
  route_ready: boolean
  route_provider_pair_valid: boolean
}

export interface AdminRoutePolicyPayload {
  name: string
  public_model_name: string
  primary_provider_id: number
  secondary_provider_id?: number | null
  policy_type: RoutePolicyType
  retry_count?: number
  cooldown_seconds?: number
  timeout_seconds?: number
  is_active?: boolean
  notes?: string | null
}

export const adminRoutePoliciesApi = {
  list: () => api.get<AdminRoutePolicy[]>('/admin/route-policies'),
  create: (data: AdminRoutePolicyPayload) => api.post<AdminRoutePolicy>('/admin/route-policies', data),
  update: (id: number, data: Partial<AdminRoutePolicyPayload>) => api.patch<AdminRoutePolicy>(`/admin/route-policies/${id}`, data),
}
