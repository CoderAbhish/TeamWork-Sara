import api from '@/lib/api'

export const listLeads = (params = {}) => api.get('/leads', { params }).then((r) => r.data)

export const getLead = (leadId) => api.get(`/leads/${leadId}`).then((r) => r.data.lead)

// Returns the full response ({ lead, customerReused }) — customerReused lets
// the caller flag when a new lead was added under an existing contact.
export const createLead = (payload) => api.post('/leads', payload).then((r) => r.data)

export const updateLead = (leadId, patch) =>
  api.patch(`/leads/${leadId}`, patch).then((r) => r.data.lead)

export const deleteLead = (leadId) => api.delete(`/leads/${leadId}`)

export const assignLeads = (leadIds, userId) =>
  api.post('/leads/assign', { leadIds, userId }).then((r) => r.data)

export const listComments = (leadId) =>
  api.get(`/leads/${leadId}/comments`).then((r) => r.data.items)

export const addComment = (leadId, commentText) =>
  api.post(`/leads/${leadId}/comments`, { commentText }).then((r) => r.data.comment)

export const importLeadsCsv = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api
    .post('/leads/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then((r) => r.data)
}

// A plain <a href> can't carry the Authorization header, so the export is
// fetched as a blob and downloaded client-side instead.
export const downloadLeadsCsv = async (params = {}) => {
  const response = await api.get('/leads/export', { params, responseType: 'blob' })
  const url = window.URL.createObjectURL(new Blob([response.data]))
  const link = document.createElement('a')
  link.href = url
  link.download = 'leads_export.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
  window.URL.revokeObjectURL(url)
}
