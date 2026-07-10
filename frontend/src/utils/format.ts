export function fmtPrice(n: number) {
  return Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function fmtDateShort(d: string) {
  return d.length >= 10 ? d.slice(5) : d
}

/** 到期日是否已到（含当天），未到期不展示收益。 */
export function isDueDateReached(dueDate: string) {
  const today = new Date()
  const y = today.getFullYear()
  const m = String(today.getMonth() + 1).padStart(2, '0')
  const d = String(today.getDate()).padStart(2, '0')
  return dueDate.slice(0, 10) <= `${y}-${m}-${d}`
}

/** 时间线按到期日先后排列（短周期在前）。 */
export function sortNodesByDueDate<T extends { due_date: string; sort_order?: number }>(nodes: T[]): T[] {
  return [...nodes].sort((a, b) => {
    const cmp = a.due_date.slice(0, 10).localeCompare(b.due_date.slice(0, 10))
    if (cmp !== 0) return cmp
    return (a.sort_order ?? 0) - (b.sort_order ?? 0)
  })
}

export function fmtPctVal(v: number | null | undefined, signed = true) {
  if (v == null) return '—'
  const prefix = signed && v > 0 ? '+' : ''
  return `${prefix}${v.toFixed(1)}%`
}
