import api from '@/lib/api'

export const listFollowUps = (leadId) =>
  api.get(`/leads/${leadId}/follow-ups`).then((r) => r.data.items)

// A follow-up entry always needs a comment — the history is append-only.
export const logFollowUp = (leadId, followUpOn, comment) =>
  api.post(`/leads/${leadId}/follow-ups`, { followUpOn, comment }).then((r) => r.data)
