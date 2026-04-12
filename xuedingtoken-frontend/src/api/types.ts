export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  message?: string
}

export interface ApiListResponse<T> extends ApiResponse<T[]> {
  total?: number
  page?: number
  pageSize?: number
}
