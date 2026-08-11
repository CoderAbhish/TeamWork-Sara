import api from '@/lib/api'

export const getConvertedOverTime = (period) =>
  api.get('/analytics/converted-over-time', { params: { period } }).then((r) => r.data.buckets)

export const getLeadsByCategory = () =>
  api.get('/analytics/leads-by-category').then((r) => r.data.items)

export const getHotLeads = () => api.get('/analytics/hot-leads').then((r) => r.data.items)

export const getPublicStats = () => api.get('/public/stats').then((r) => r.data)
