import api from '@/lib/api'

export const listSuggestions = (status) =>
  api.get('/lead-suggestions', { params: status ? { status } : {} }).then((r) => r.data.items)

export const createSuggestion = (payload) =>
  api.post('/lead-suggestions', payload).then((r) => r.data.suggestion)

export const approveSuggestion = (id, projectId) =>
  api.post(`/lead-suggestions/${id}/approve`, projectId ? { projectId } : {}).then((r) => r.data)

export const rejectSuggestion = (id) =>
  api.post(`/lead-suggestions/${id}/reject`).then((r) => r.data.suggestion)

export const importSuggestionsCsv = (file) => {
  const formData = new FormData()
  formData.append('file', file)
  return api
    .post('/lead-suggestions/import', formData, { headers: { 'Content-Type': 'multipart/form-data' } })
    .then((r) => r.data)
}
