import { api } from './client'

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant' | 'tool'
  content: string
}

export interface ChatCompletionsPayload {
  model: string
  messages: Array<{ role: string; content: string }>
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

export interface ChatCompletionsResponse {
  id: string
  object: string
  created: number
  model: string
  choices: Array<{
    index: number
    message: {
      role: string
      content: string
    }
    finish_reason: string
  }>
  usage?: {
    prompt_tokens: number
    completion_tokens: number
    total_tokens: number
  }
  debug?: {
    public_model?: string
    provider_name?: string
    provider_type?: string
    provider_id?: number
    provider_key_id?: number
    policy_type?: string
    fallback_used?: boolean
    fallback_triggered?: boolean
    provider_switch_count?: number
    key_switch_count?: number
    latency_ms?: number
    cost?: number
    total_tokens?: number
    upstream_model_name?: string
    failure_chain_summary?: string
  }
}

/**
 * 调用 /proxy/chat/completions，复用 client.ts 的统一错误处理
 */
export async function chatCompletions(
  payload: ChatCompletionsPayload
): Promise<ChatCompletionsResponse> {
  return api.post<ChatCompletionsResponse>('/proxy/chat/completions', payload)
}

export async function listProxyModels(): Promise<{ object: string; data: any[] }> {
  return api.get<{ object: string; data: any[] }>('/v1/models')
}
