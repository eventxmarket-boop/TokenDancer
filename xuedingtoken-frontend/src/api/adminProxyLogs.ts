import { api } from '@/api/client'

export interface AdminProxyLog {
  id: number
  request_id?: string | null
  user_id?: number | null
  user_api_key_id?: number | null
  public_model_name: string
  provider_id?: number | null
  provider_name?: string | null
  provider_type?: string | null
  provider_key_id?: number | null
  provider_key_name?: string | null
  provider_model_name: string
  request_status: string
  input_tokens: number
  output_tokens: number
  total_tokens: number
  cost: number
  latency_ms: number
  error_message?: string | null
  requested_at: string
  upstream_provider_id?: number | null
  upstream_key_id?: number | null
  policy_type?: string
  fallback_triggered?: boolean
  retry_attempt?: number
  provider_switch_count?: number
  key_switch_count?: number
  failure_chain_summary?: string | null
}

export const adminProxyLogsApi = {
  list: (params?: {
    provider_id?: number | string
    public_model_name?: string
    request_status?: string
    date_from?: string
    date_to?: string
    limit?: number
    offset?: number
  }) => api.get<AdminProxyLog[]>('/admin/proxy-logs', params),
}
