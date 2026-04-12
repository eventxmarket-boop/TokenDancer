import { api } from '@/api/client'
import type { AdminModelRoute } from '@/api/adminModelRoutes'
import type { AdminProviderKey } from '@/api/adminProviderKeys'
import type { AdminProvider } from '@/api/adminProviders'
import type { AdminRoutePolicy } from '@/api/adminRoutePolicies'

export type AdminProxyTesterRouteMode = 'auto' | 'provider' | 'provider_key'

export interface AdminProxyTesterMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface AdminProxyTesterOptions {
  models: AdminModelRoute[]
  providers: AdminProvider[]
  provider_keys: AdminProviderKey[]
  route_policies: AdminRoutePolicy[]
}

export interface AdminProxyTesterRunPayload {
  public_model_name: string
  route_mode: AdminProxyTesterRouteMode
  provider_id?: number
  provider_key_id?: number
  temperature?: number
  max_tokens?: number
  stream?: boolean
  messages: AdminProxyTesterMessage[]
}

export interface AdminProxyTesterResult {
  success: boolean
  status_code: number
  route_mode: AdminProxyTesterRouteMode
  public_model_name: string
  assistant_message?: string | null
  error_summary?: string | null
  request_id?: string | null
  request_log_id?: number | null
  request_origin: string
  request_tag?: string | null
  request_status?: string | null
  latency_ms?: number | null
  provider_id?: number | null
  provider_name?: string | null
  provider_type?: string | null
  provider_key_id?: number | null
  provider_key_name?: string | null
  policy_name?: string | null
  policy_type?: string | null
  upstream_model_name?: string | null
  fallback_triggered?: boolean
  provider_switch_count?: number
  key_switch_count?: number
  failure_chain_summary?: string | null
  log_written: boolean
  source_key_usage_updated: boolean
  source_key_last_used_at?: string | null
  source_key_used_count_today?: number | null
  forced_provider_honored?: boolean | null
  forced_source_key_honored?: boolean | null
  usage?: {
    prompt_tokens?: number
    completion_tokens?: number
    total_tokens?: number
  } | null
}

export const adminProxyTesterApi = {
  getOptions: () => api.get<AdminProxyTesterOptions>('/admin/proxy-tester/options'),
  run: (data: AdminProxyTesterRunPayload) => api.post<AdminProxyTesterResult>('/admin/proxy-tester/run', data),
}
