import { api } from '@/api/client'

export const adminRoutePoliciesApi = {
  list: () => api.get<any[]>('/admin/route-policies'),
  create: (data: any) => api.post<any>('/admin/route-policies', data),
  update: (id: number, data: any) => api.patch<any>(`/admin/route-policies/${id}`, data),
}
