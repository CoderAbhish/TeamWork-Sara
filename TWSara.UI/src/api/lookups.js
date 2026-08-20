import api from '@/lib/api'

export const getProjectStatuses = () => api.get('/lookups/project-statuses').then((r) => r.data.items)
export const getLeadStatuses = () => api.get('/lookups/lead-statuses').then((r) => r.data.items)
export const getLeadCategories = () => api.get('/lookups/lead-categories').then((r) => r.data.items)
export const getPropertyTypes = () => api.get('/lookups/property-types').then((r) => r.data.items)
export const getSaleTypes = () => api.get('/lookups/sale-types').then((r) => r.data.items)
export const getListingTypes = () => api.get('/lookups/listing-types').then((r) => r.data.items)
export const getLeadSources = () => api.get('/lookups/lead-sources').then((r) => r.data.items)
