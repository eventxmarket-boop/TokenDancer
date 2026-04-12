export type ProviderType = 'openai' | 'anthropic' | 'minimax' | 'gemini' | 'proxy' | 'custom'

export interface ProviderTypeOption {
  value: ProviderType
  label: string
  hint: string
  defaultBaseUrl?: string
}

export const PROVIDER_TYPE_OPTIONS: ProviderTypeOption[] = [
  {
    value: 'openai',
    label: 'openai',
    hint: 'OpenAI 兼容接口，适合 OpenAI / OpenRouter / 兼容网关',
    defaultBaseUrl: 'https://api.openai.com/v1',
  },
  {
    value: 'anthropic',
    label: 'anthropic',
    hint: 'Anthropic 渠道标识，建议确认你的接入端是否提供兼容入口',
    defaultBaseUrl: 'https://api.anthropic.com',
  },
  {
    value: 'minimax',
    label: 'minimax',
    hint: 'Minimax 官方接口，走专用适配器',
    defaultBaseUrl: 'https://api.minimax.chat',
  },
  {
    value: 'gemini',
    label: 'gemini',
    hint: 'Gemini OpenAI 兼容入口',
    defaultBaseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai',
  },
  {
    value: 'proxy',
    label: 'proxy',
    hint: '自建 OpenAI 兼容代理',
  },
  {
    value: 'custom',
    label: 'custom',
    hint: '自定义 OpenAI 兼容上游',
  },
]

export const PROVIDER_TYPE_MAP = Object.fromEntries(
  PROVIDER_TYPE_OPTIONS.map((item) => [item.value, item])
) as Record<ProviderType, ProviderTypeOption>
