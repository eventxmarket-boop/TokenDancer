import { useProfileStore } from '@/stores/profile'

export const profileService = {
  updateProfile(data: Parameters<ReturnType<typeof useProfileStore>['updateProfile']>[0]) {
    useProfileStore().updateProfile(data)
  },
  async changePassword(_current: string, next: string): Promise<{ ok: boolean; msg: string }> {
    if (next.length < 8) return { ok: false, msg: '新密码至少8个字符' }
    await useProfileStore().changePassword()
    return { ok: true, msg: '密码修改成功' }
  },
}
