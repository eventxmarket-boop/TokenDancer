import { useKeyStore } from '@/stores/keys'
import { buildCommand, type DeployType } from '@/utils/commandBuilder'

export const installService = {
  getAvailableKeys() {
    return useKeyStore().keys.filter((k: any) => k.status === 'active')
  },
  buildCommand(type: DeployType, keyId: string) {
    const key = useKeyStore().keys.find((k: any) => k.id === Number(keyId))
    const apiKey = key?.key_value || 'your-api-key-here'
    return buildCommand(type, apiKey)
  },
  buildAllCommands(keyId: string) {
    const key = useKeyStore().keys.find((k: any) => k.id === Number(keyId))
    const apiKey = key?.key_value || 'your-api-key-here'
    return {
      'claude-code': buildCommand('claude-code', apiKey),
      'openclaw': buildCommand('openclaw', apiKey),
      'generic': buildCommand('generic', apiKey),
    }
  },
}
