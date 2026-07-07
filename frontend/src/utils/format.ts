export function fmtPrice(n: number) {
  return Number(n).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

export function fmtDateShort(d: string) {
  return d.length >= 10 ? d.slice(5) : d
}

export function fmtPctVal(v: number | null | undefined, signed = true) {
  if (v == null) return '—'
  const prefix = signed && v > 0 ? '+' : ''
  return `${prefix}${v.toFixed(1)}%`
}
