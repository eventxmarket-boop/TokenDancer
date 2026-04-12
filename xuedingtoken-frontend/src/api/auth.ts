import { api } from '@/api/client'

export const authApi = {
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.put('/auth/password', data),

  forgotPassword: (email: string) =>
    api.post('/auth/forgot-password', { email }),
}
