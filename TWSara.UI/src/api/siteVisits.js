import api from '@/lib/api'

export const listSiteVisits = (leadId) =>
  api.get(`/leads/${leadId}/site-visits`).then((r) => r.data.items)

export const createSiteVisit = (leadId, payload) =>
  api.post(`/leads/${leadId}/site-visits`, payload).then((r) => r.data.siteVisit)

export const updateSiteVisit = (visitId, patch) =>
  api.patch(`/site-visits/${visitId}`, patch).then((r) => r.data.siteVisit)

export const deleteSiteVisit = (visitId) => api.delete(`/site-visits/${visitId}`)

// Rescheduling is its own action, not a plain PATCH: a note is mandatory
// and the lead's status is pushed back to Site Visit Scheduled. Returns
// { siteVisit, lead } so callers can refresh both in one round trip.
export const rescheduleSiteVisit = (visitId, scheduledOn, notes) =>
  api.post(`/site-visits/${visitId}/reschedule`, { scheduledOn, notes }).then((r) => r.data)
