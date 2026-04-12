export type DeployType = 'claude-code' | 'openclaw' | 'generic'

export const buildCommand = (type: DeployType, apiKey: string, baseUrl: string = '/api'): string => {
  switch (type) {
    case 'claude-code':
      return `export ANTHROPIC_API_KEY="${apiKey}"
export ANTHROPIC_BASE_URL="${baseUrl}"
claude`
    case 'openclaw':
      return `export OPENCLAW_API_KEY="${apiKey}"
export OPENCLAW_BASE_URL="${baseUrl}"
openclaw`
    case 'generic':
      return `export API_KEY="${apiKey}"
export BASE_URL="${baseUrl}"
# Run your client
`
    default:
      return ''
  }
}
