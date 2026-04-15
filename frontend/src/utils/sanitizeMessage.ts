export function stripThinkBlocks(text: string): string {
  if (!text) return text

  return text
    .replace(/<think>[\s\S]*?<\/think>/gi, '')
    .replace(/<reasoning>[\s\S]*?<\/reasoning>/gi, '')
    .replace(/<analysis>[\s\S]*?<\/analysis>/gi, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
