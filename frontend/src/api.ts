const BASE = '/api'

function getToken(): string | null {
  return localStorage.getItem('token')
}

function authHeaders(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(options.headers || {}),
    },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const api = {
  // Auth
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),

  createUser: (email: string, password: string, role: string) =>
    request('/auth/users', {
      method: 'POST',
      body: JSON.stringify({ email, password, role }),
    }),

  // Jobs
  listJobs: (params: Record<string, string | number | undefined> = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params)
        .filter(([, v]) => v !== undefined && v !== '')
        .map(([k, v]) => [k, String(v)])
    ).toString()
    return request<any[]>(`/jobs${qs ? `?${qs}` : ''}`)
  },

  getJob: (id: number) => request<any>(`/jobs/${id}`),

  claimJob: (id: number) =>
    request<{ assignment_id: number; claimed_at: string }>(`/jobs/${id}/claim`, { method: 'POST' }),

  releaseJob: (id: number) =>
    request<{ status: string }>(`/jobs/${id}/claim`, { method: 'DELETE' }),

  submitJob: (id: number, outcome: string, notes: string) =>
    request<any>(`/jobs/${id}/submission`, {
      method: 'POST',
      body: JSON.stringify({ outcome, notes: notes || null }),
    }),

  downloadResume: async (id: number): Promise<void> => {
    const res = await fetch(`${BASE}/jobs/${id}/resume`, {
      headers: authHeaders() as Record<string, string>,
    })
    if (!res.ok) throw new Error('Resume not available')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `resume_job_${id}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  },

  // Admin
  getDashboard: () => request<any>('/admin/dashboard'),

  triggerIngestion: (body: object) =>
    request<any>('/admin/ingest', { method: 'POST', body: JSON.stringify(body) }),

  markStale: () => request<any>('/admin/stale/mark', { method: 'POST' }),

  exportCsv: async (): Promise<void> => {
    const res = await fetch(`${BASE}/admin/export/csv`, {
      headers: authHeaders() as Record<string, string>,
    })
    if (!res.ok) throw new Error('Export failed')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'submissions.csv'
    a.click()
    URL.revokeObjectURL(url)
  },

  getDedupReview: () => request<any[]>('/admin/dedup/review'),
}
