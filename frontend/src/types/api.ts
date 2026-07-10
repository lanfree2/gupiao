export interface NodeOut {
  id: number
  label: string
  days: number
  sort_order?: number
  due_date: string
  status: string
  close_price: number | null
  pct_change: number | null
}

export interface RecommendationOut {
  id: number
  stock_code: string
  stock_name: string
  channel_id: number
  channel_name: string
  channel_color: string
  recommend_date: string
  recommend_price: number
  reason: string
  created_at: string
  nodes: NodeOut[]
}

export interface ChannelStatsOut {
  id: number
  name: string
  color: string
  description: string
  is_active: boolean
  record_count: number
  win_rate: number | null
  avg_return: number | null
}

export interface PeriodOut {
  id: number
  label: string
  days: number
  unit: 'trading_day' | 'natural_week' | 'natural_month'
  sort_order: number
}

export interface DashboardOut {
  tracking_count: number
  win_rate: number | null
  avg_return: number | null
  pending_nodes: number
  channel_win_rates: { name: string; color: string; win_rate: number | null }[]
  channel_avg_returns: { name: string; color: string; avg_return: number | null }[]
  period_stats: { label: string; days: number; sample: number; win_rate: number | null; avg_return: number | null }[]
  channel_period_stats: {
    name: string
    color: string
    record_count: number
    win_rate: number | null
    avg_return: number | null
    periods: { label: string; days: number; sample: number; win_rate: number | null; avg_return: number | null }[]
  }[]
  recent: RecommendationOut[]
}
