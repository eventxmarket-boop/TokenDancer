import { api } from '@/api/client'

export const contentApi = {
  announcements: () => api.get<any[]>('/content/announcements'),
  privacy: () => api.get<any>('/content/privacy'),
  terms: () => api.get<any>('/content/terms'),
  qrs: () => api.get<any[]>('/content/qrs/latest'),
}

export const adminContentApi = {
  listAnnouncements: () => api.get<any[]>('/admin/announcements'),
  createAnnouncement: (data: any) => api.post<any>('/admin/announcements', data),
  updateAnnouncement: (id: number, data: any) => api.patch<any>(`/admin/announcements/${id}`, data),
  deleteAnnouncement: (id: number) => api.delete<any>(`/admin/announcements/${id}`),
  getPrivacy: () => api.get<any>('/admin/content/privacy'),
  updatePrivacy: (data: any) => api.put<any>('/admin/content/privacy', data),
  getTerms: () => api.get<any>('/admin/content/terms'),
  updateTerms: (data: any) => api.put<any>('/admin/content/terms', data),
  listQrs: () => api.get<any[]>('/admin/qrs'),
  createQr: (data: any) => api.post<any>('/admin/qrs', data),
  updateQr: (id: number, data: any) => api.patch<any>(`/admin/qrs/${id}`, data),
  deleteQr: (id: number) => api.delete<any>(`/admin/qrs/${id}`),
  listPages: () => api.get<any[]>('/admin/content/pages'),
  getPage: (slug: string) => api.get<any>(`/admin/content/pages/${slug}`),
  updatePage: (slug: string, data: any) => api.put<any>(`/admin/content/pages/${slug}`, data),
}
