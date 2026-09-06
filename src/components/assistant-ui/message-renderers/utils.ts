export function parseJsonBlock(text: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(text)
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : null
  } catch {
    return null
  }
}

function isMarkdownTableLine(line: string) {
  const trimmed = line.trim()
  if (!trimmed.startsWith('|') || !trimmed.endsWith('|')) return false
  return trimmed.split('|').length >= 4
}

function isMarkdownTableSeparator(line: string) {
  return /^\s*\|?[\s:-]+\|[\s|:-]*$/.test(line.trim())
}

export function normalizeMarkdownTables(text: string): string {
  const lines = String(text ?? '').replace(/\r\n/g, '\n').split('\n')
  const output: string[] = []
  let index = 0

  while (index < lines.length) {
    const line = lines[index]
    const nextLine = lines[index + 1] ?? ''
    const isTableStart = isMarkdownTableLine(line) && isMarkdownTableSeparator(nextLine)

    if (!isTableStart) {
      output.push(line)
      index += 1
      continue
    }

    if (output.length && output[output.length - 1].trim() !== '') {
      output.push('')
    }

    while (index < lines.length && lines[index].trim() !== '') {
      output.push(lines[index].replace(/\s+$/g, '').trimEnd())
      index += 1
    }

    if (index < lines.length && output[output.length - 1].trim() !== '') {
      output.push('')
    }
  }

  return output.join('\n').replace(/\n{3,}/g, '\n\n')
}
