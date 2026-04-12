import { api } from '@/api/client'

export interface ProductListItem {
  id: number
  name: string
  slug: string
  category: string
  tag: string | null
  price_cny: number
  stock: number
  delivery_type: string
  is_active: boolean
  sort_order: number
}

export interface ProductDetail extends ProductListItem {
  description: string | null
  price_usd_value: number
  created_at: string
  updated_at: string | null
}

export const productsApi = {
  list: (params?: { category?: string }) =>
    api.get<ProductListItem[]>('/products', params),

  get: (id: number) =>
    api.get<ProductDetail>(`/products/${id}`),

  featured: (limit = 4) =>
    api.get<ProductListItem[]>(`/products/featured`, { limit }),
}
