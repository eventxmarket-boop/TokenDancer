import { api } from '@/api/client'

export const adminModelRoutesApi = {
  list: () => api.get<any[]>('/admin/model-routes'),
  create: (data: any) => api.post<any>('/admin/model-routes', data),
  update: (id: number, data: any) => api.patch<any>(`/admin/model-routes/${id}`, data),
}
