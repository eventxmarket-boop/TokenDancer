const escapeMap: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
}

function escapeHtml(text: string): string {
  return text.replace(/[&<>"']/g, (char) => escapeMap[char] ?? char)
}

function renderInlineMarkdown(text: string): string {
  const escaped = escapeHtml(text)
  return escaped.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
}

function flushParagraph(buffer: string[], output: string[]) {
  if (!buffer.length) {
    return
  }
  const html = buffer.map((line) => renderInlineMarkdown(line)).join('<br>')
  output.push(`<p>${html}</p>`)
  buffer.length = 0
}

function flushList(
  items: { type: 'ul' | 'ol'; content: string[] } | null,
  output: string[],
) {
  if (!items || !items.content.length) {
    return
  }

  const tag = items.type
  const renderedItems = items.content
    .map((item) => `<li>${renderInlineMarkdown(item)}</li>`)
    .join('')
  output.push(`<${tag}>${renderedItems}</${tag}>`)
}

export function renderMarkdown(text: string): string {
  if (!text) return ''

  const lines = text.replace(/\r\n/g, '\n').trim().split('\n')
  const output: string[] = []
  const paragraph: string[] = []
  let list: { type: 'ul' | 'ol'; content: string[] } | null = null

  for (const rawLine of lines) {
    const line = rawLine.trim()

    if (!line) {
      flushParagraph(paragraph, output)
      flushList(list, output)
      list = null
      continue
    }

    const unorderedMatch = line.match(/^[-*+]\s+(.*)$/)
    const orderedMatch = line.match(/^\d+[.)]\s+(.*)$/)

    if (unorderedMatch || orderedMatch) {
      flushParagraph(paragraph, output)
      const type: 'ul' | 'ol' = unorderedMatch ? 'ul' : 'ol'
      const content = (unorderedMatch?.[1] ?? orderedMatch?.[1] ?? '').trim()

      if (!list || list.type !== type) {
        flushList(list, output)
        list = { type, content: [] }
      }

      list.content.push(content)
      continue
    }

    flushList(list, output)
    list = null
    paragraph.push(line)
  }

  flushParagraph(paragraph, output)
  flushList(list, output)

  return output.join('\n')
}
