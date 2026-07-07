const API = import.meta.env.VITE_API_BASE_URL || '/api'

export type User = { id: number; phone: string; nickname: string; role: string }

function headers() {
  const token = localStorage.getItem('token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  }
}

async function request<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API}${path}`, { ...opts, headers: { ...headers(), ...(opts.headers || {}) } })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data.detail
    const msg = Array.isArray(detail)
      ? detail.map((d: { msg?: string }) => d.msg).join('; ')
      : detail || data.message || res.statusText || `HTTP ${res.status}`
    throw new Error(msg)
  }
  return data as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),

  smsConfig: () => api.get<{ enabled: boolean; mock_mode: boolean; mock_hint?: string }>('/auth/sms/config'),
  sendSms: (phone: string, purpose: string) => api.post('/auth/sms/send', { phone, purpose }),
  register: (body: object) => api.post<{ access_token: string; user: User }>('/auth/register', body),
  login: (body: object) => api.post<{ access_token: string; user: User }>('/auth/login', body),
  changePassword: (body: object) => api.post('/auth/password/change', body),
  resetPasswordSms: (body: object) => api.post('/auth/password/reset/sms', body),
  me: () => api.get<User>('/auth/me'),

  dashboard: () => api.get('/dashboard'),
  channels: () => api.get('/channels'),
  createChannel: (body: object) => api.post('/channels', body),
  updateChannel: (id: number, body: object) => api.put(`/channels/${id}`, body),
  deleteChannel: (id: number) => api.post(`/channels/${id}/delete`),
  channelDetail: (id: number) => api.get(`/recommendations/channels/${id}/detail`),
  recommendations: (params?: string) => api.get(`/recommendations${params || ''}`),
  search: (q: string, scope: string) => api.get(`/recommendations/search?q=${encodeURIComponent(q)}&scope=${scope}`),
  getRec: (id: number) => api.get(`/recommendations/${id}`),
  createRec: (body: object) => api.post('/recommendations', body),
  updateRec: (id: number, body: object) => api.put(`/recommendations/${id}`, body),
  deleteRec: (id: number) => api.post(`/recommendations/${id}/delete`),
  refetchRec: (id: number) => api.post(`/recommendations/${id}/refetch`),
  periods: () => api.get('/periods'),
  savePeriods: (body: object[]) => api.put('/periods', body),
  stockLookup: (code: string) => api.get(`/stocks/lookup?code=${code}`),
  stockClose: (code: string, tradeDate: string) =>
    api.get(`/stocks/close?code=${encodeURIComponent(code)}&trade_date=${tradeDate}`),

  adminDashboard: () => api.get('/admin/dashboard'),
  adminStocks: (q?: string) => api.get(`/admin/stocks${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  adminStock: (code: string) => api.get(`/admin/stocks/${code}`),
  adminChannels: (q?: string, userId?: number) => {
    const p = new URLSearchParams()
    if (q) p.set('q', q)
    if (userId) p.set('user_id', String(userId))
    const qs = p.toString()
    return api.get(`/admin/channels${qs ? `?${qs}` : ''}`)
  },
  adminChannel: (id: number) => api.get(`/admin/channels/${id}`),
  adminRecords: (q?: string, scope?: string) => {
    const p = new URLSearchParams()
    if (q) p.set('q', q)
    if (scope) p.set('scope', scope)
    const qs = p.toString()
    return api.get(`/admin/records${qs ? `?${qs}` : ''}`)
  },
  runWorker: () => api.post('/admin/worker/run'),
  adminDeleteRec: (id: number) => api.post(`/admin/recommendations/${id}/delete`),
}

export function fmtPct(v: number | null | undefined) {
  if (v == null) return '—'
  return `${v > 0 ? '+' : ''}${v.toFixed(1)}%`
}

export function chipClass(v: number | null | undefined) {
  if (v == null) return 'flat'
  if (v > 0) return 'up'
  if (v < 0) return 'down'
  return 'flat'
}
