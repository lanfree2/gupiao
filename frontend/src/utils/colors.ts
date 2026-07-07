export const COLORS: Record<string, string> = {
  blue: '#3b6fd4',
  green: '#0d9b6c',
  orange: '#d98218',
  purple: '#8b5cf6',
  gray: '#8b92a3',
}

export function tagColor(color: string) {
  return COLORS[color] || COLORS.gray
}
