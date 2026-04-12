import { api } from '@/api/client'

export const adminProxyLogsApi = {
  list: (params?: {
    provider_id?: number | string
    public_model_name?: string
    request_status?: string
    date_from?: string
    date_to?: string
    limit?: number
    offset?: number
  }) => {
    // 过滤掉空值，避免传空字符串导致后端 422
    const clean: Record<string, string | number> = {}
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') {
          clean[k] = v as number | string
        }
      })
    }
    return api.get<any[]>('/admin/proxy-logs', Object.keys(clean).length ? clean : undefined)
  },
}
