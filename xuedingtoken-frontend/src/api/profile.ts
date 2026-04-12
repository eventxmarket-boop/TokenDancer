import { api } from '@/api/client'

export interface UserProfile {
  id?: number
  username: string
  email: string
  status: string
  balance: number
  available_balance: number
  created_at?: string
}

export const profileApi = {
  get(): Promise<UserProfile> {
    return api.get<UserProfile>('/auth/profile')
  },

  update(data: { username: string }): Promise<UserProfile> {
    return api.put<UserProfile>('/auth/profile', data)
  },

  changePassword(currentPassword: string, newPassword: string): Promise<{ message: string }> {
    return api.put<{ message: string }>('/auth/password', {
      current_password: currentPassword,
      new_password: newPassword,
    })
  },
}
