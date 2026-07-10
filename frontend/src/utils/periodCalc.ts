export type PeriodUnit = 'trading_day' | 'natural_week' | 'natural_month'

export function inferUnitFromLabel(label: string): PeriodUnit {
  if (label.includes('周')) return 'natural_week'
  if (label.includes('月')) return 'natural_month'
  return 'trading_day'
}

export function suggestLabel(unit: PeriodUnit, value: number): string {
  if (unit === 'natural_week') return `${value}周`
  if (unit === 'natural_month') return `${value}月`
  return `${value}交易日`
}

export function periodValueHint(unit: PeriodUnit): string {
  if (unit === 'natural_week') return '自然周数'
  if (unit === 'natural_month') return '自然月数'
  return '交易日数'
}

export function periodUnitText(unit: PeriodUnit, value: number): string {
  if (unit === 'natural_week') return `${value}自然周`
  if (unit === 'natural_month') return `${value}自然月`
  return `${value}交易日`
}

function pad(n: number) {
  return String(n).padStart(2, '0')
}

function toIso(d: Date) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function addTradingDays(start: string, n: number): string {
  const d = new Date(`${start}T12:00:00`)
  let counted = 0
  while (counted < n) {
    d.setDate(d.getDate() + 1)
    const wd = d.getDay()
    if (wd !== 0 && wd !== 6) counted += 1
  }
  return toIso(d)
}

export function addNaturalWeeks(start: string, weeks: number): string {
  const d = new Date(`${start}T12:00:00`)
  d.setDate(d.getDate() + 7 * weeks)
  return toIso(d)
}

export function addNaturalMonths(start: string, months: number): string {
  const d = new Date(`${start}T12:00:00`)
  const day = d.getDate()
  d.setMonth(d.getMonth() + months)
  const last = new Date(d.getFullYear(), d.getMonth() + 1, 0).getDate()
  d.setDate(Math.min(day, last))
  return toIso(d)
}

export function dueDateForPeriod(start: string, unit: PeriodUnit, value: number): string {
  if (unit === 'natural_week') return addNaturalWeeks(start, value)
  if (unit === 'natural_month') return addNaturalMonths(start, value)
  return addTradingDays(start, value)
}
