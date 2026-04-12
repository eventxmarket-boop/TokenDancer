import { api } from '@/api/client'

// ── 用户管理 ─────────────────────────────────────────────
export const adminUsersApi = {
  list: (params?: { search?: string; role?: string; status?: string }) =>
    api.get<any[]>('/admin/users', params),
  get: (id: number) => api.get<any>('/admin/users/' + id),
  update: (id: number, data: { status?: string; role?: string; balance?: number }) =>
    api.patch<any>('/admin/users/' + id, data),
}

// ── 订单管理 ─────────────────────────────────────────────
export const adminOrdersApi = {
  list: (params?: { order_no?: string; status?: string; limit?: number; offset?: number }) =>
    api.get<any[]>('/admin/orders', params),
  get: (id: number) => api.get<any>('/admin/orders/' + id),
  updateStatus: (id: number, status: string) =>
    api.patch<any>('/admin/orders/' + id, { status }),
}

// ── 兑换码管理 ───────────────────────────────────────────
export const adminRedeemCodesApi = {
  list: (params?: { is_used?: boolean; is_expired?: boolean }) =>
    api.get<any[]>('/admin/redeem-codes', params),
  create: (data: {
    code?: string
    reward_type: string
    reward_amount: number
    expires_at?: string
  }) => api.post<any>('/admin/redeem-codes', data),
  update: (id: number, data: { expires_at?: string }) =>
    api.patch<any>('/admin/redeem-codes/' + id, data),
  delete: (id: number) => api.delete('/admin/redeem-codes/' + id),
}

// ── 商品管理 ─────────────────────────────────────────────
export const adminProductsApi = {
  list: (params?: { search?: string; category?: string; is_active?: boolean }) =>
    api.get<any[]>('/admin/products', params),
  get: (id: number) => api.get<any>('/admin/products/' + id),
  create: (data: {
    name: string; slug: string; category: string; description?: string
    tag?: string; price_cny: number; price_usd_value: number
    stock: number; delivery_type: string; is_active: boolean; sort_order?: number
  }) => api.post<any>('/admin/products', data),
  update: (id: number, data: Partial<{
    name: string; slug: string; category: string; description: string
    tag: string; price_cny: number; price_usd_value: number
    stock: number; delivery_type: string; is_active: boolean; sort_order: number
  }>) => api.patch<any>('/admin/products/' + id, data),
}

// ── 渠道管理 ─────────────────────────────────────────────
export const adminProvidersApi = {
  list: () => api.get<any[]>('/admin/providers'),
  create: (data: any) => api.post<any>('/admin/providers', data),
  update: (id: number, data: any) => api.patch<any>('/admin/providers/' + id, data),
}

// ── 源 Key 池 ────────────────────────────────────────────
export const adminProviderKeysApi = {
  list: (params?: { provider_id?: number }) =>
    api.get<any[]>('/admin/provider-keys', params),
  create: (data: any) => api.post<any>('/admin/provider-keys', data),
  update: (id: number, data: any) => api.patch<any>('/admin/provider-keys/' + id, data),
}

// ── 模型映射 ─────────────────────────────────────────────
export const adminModelRoutesApi = {
  list: () => api.get<any[]>('/admin/model-routes'),
  create: (data: any) => api.post<any>('/admin/model-routes', data),
  update: (id: number, data: any) => api.patch<any>('/admin/model-routes/' + id, data),
}

// ── 路由策略 ─────────────────────────────────────────────
export const adminRoutePoliciesApi = {
  list: () => api.get<any[]>('/admin/route-policies'),
  create: (data: any) => api.post<any>('/admin/route-policies', data),
  update: (id: number, data: any) => api.patch<any>('/admin/route-policies/' + id, data),
}

// ── 请求日志 ─────────────────────────────────────────────
export const adminProxyLogsApi = {
  list: (params?: {
    provider_id?: number; public_model_name?: string
    request_status?: string; date_from?: string; date_to?: string
    limit?: number; offset?: number
  }) => api.get<any[]>('/admin/proxy-logs', params),
}
