import api from '@/lib/api'

export const getProjectStatuses = () => api.get('/lookups/project-statuses').then((r) => r.data.items)
export const getLeadStatuses = () => api.get('/lookups/lead-statuses').then((r) => r.data.items)
export const getLeadCategories = () => api.get('/lookups/lead-categories').then((r) => r.data.items)
