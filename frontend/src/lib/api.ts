import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60_000,
})

api.interceptors.response.use(
  res => res,
  err => {
    const msg = err.response?.data?.detail ?? err.message ?? 'Request failed'
    return Promise.reject(new Error(msg))
  }
)

// ── Jobs ──────────────────────────────────────────────────────────────────────
export const jobsApi = {
  list: (params?: Record<string, string | number>) => api.get('/jobs', { params }).then(r => r.data),
  get: (id: string) => api.get(`/jobs/${id}`).then(r => r.data),
  stats: () => api.get('/jobs/stats').then(r => r.data),
  discover: (body: { keywords: string; location?: string; platforms?: string[]; limit?: number }) =>
    api.post('/jobs/discover', body).then(r => r.data),
  analyse: (id: string) => api.post(`/jobs/${id}/analyse`).then(r => r.data),
  tailor: (id: string) => api.post(`/jobs/${id}/tailor`).then(r => r.data),
  apply: (id: string, resumeId?: string) =>
    api.post(`/jobs/${id}/apply`, null, { params: resumeId ? { resume_id: resumeId } : {} }).then(r => r.data),
  resolveFields: (id: string, answers: Record<string, string>) =>
    api.post(`/jobs/${id}/resolve-fields`, { answers }).then(r => r.data),
  updateStatus: (id: string, status: string) =>
    api.patch(`/jobs/${id}/status`, null, { params: { status } }).then(r => r.data),
  pendingFields: (id: string) => api.get(`/jobs/${id}/pending-fields`).then(r => r.data),
}

// ── Resumes ───────────────────────────────────────────────────────────────────
export const resumesApi = {
  list: () => api.get('/resumes').then(r => r.data),
  get: (id: string) => api.get(`/resumes/${id}`).then(r => r.data),
  text: (id: string) => api.get(`/resumes/${id}/text`).then(r => r.data),
  upload: (file: File, isBase = true) => {
    const fd = new FormData()
    fd.append('file', file)
    return api.post(`/resumes/upload?is_base=${isBase}`, fd).then(r => r.data)
  },
}

// ── Answers ───────────────────────────────────────────────────────────────────
export const answersApi = {
  list: () => api.get('/answers').then(r => r.data),
  save: (body: { field_key: string; answer: string; field_label?: string; is_sensitive?: boolean }) =>
    api.post('/answers', body).then(r => r.data),
  delete: (fieldKey: string) => api.delete(`/answers/${fieldKey}`).then(r => r.data),
}

// ── History ───────────────────────────────────────────────────────────────────
export const historyApi = {
  applications: (limit = 100) => api.get('/history/applications', { params: { limit } }).then(r => r.data),
  logs: (limit = 200) => api.get('/history/logs', { params: { limit } }).then(r => r.data),
}

// ── Settings ──────────────────────────────────────────────────────────────────
export const settingsApi = {
  get: () => api.get('/settings').then(r => r.data),
  update: (body: Record<string, unknown>) => api.patch('/settings', body).then(r => r.data),
}

export default api
