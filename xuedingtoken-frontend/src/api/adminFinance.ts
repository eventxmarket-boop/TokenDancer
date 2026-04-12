import { api } from '@/api/client'

// ── 管理员财务与用量 ─────────────────────────────────────
export const adminFinanceApi = {
  overview: () => api.get<any>('/admin/finance/overview'),

  ledger: (params?: {
    user_id?: number
    entry_type?: string
    limit?: number
    offset?: number
  }) => api.get<{ total: number; records: any[] }>('/admin/finance/ledger', params),

  usage: (params?: {
    user_id?: number
    model?: string
    limit?: number
    offset?: number
  }) => api.get<{ total: number; records: any[] }>('/admin/finance/usage', params),
}
