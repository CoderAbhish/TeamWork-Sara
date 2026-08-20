import api from '@/lib/api'

export const listSiteVisits = (leadId) =>
  api.get(`/leads/${leadId}/site-visits`).then((r) => r.data.items)

export const createSiteVisit = (leadId, payload) =>
  api.post(`/leads/${leadId}/site-visits`, payload).then((r) => r.data.siteVisit)

export const updateSiteVisit = (visitId, patch) =>
  api.patch(`/site-visits/${visitId}`, patch).then((r) => r.data.siteVisit)

export const deleteSiteVisit = (visitId) => api.delete(`/site-visits/${visitId}`)
