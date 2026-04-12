import { api } from '@/api/client'

export const adminAuditApi = {
  list: (params?: {
    admin_user_id?: number
    action?: string
    target_type?: string
    limit?: number
    offset?: number
  }) => api.get<{ total: number; records: any[] }>('/admin/audit-logs/', params),
}
