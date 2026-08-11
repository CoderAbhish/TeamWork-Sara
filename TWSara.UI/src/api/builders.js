import api from '@/lib/api'

export const listBuilders = (includeInactive = false) =>
  api.get('/builders', { params: { includeInactive } }).then((r) => r.data.items)

export const createBuilder = (builderName) =>
  api.post('/builders', { builderName }).then((r) => r.data.builder)

export const updateBuilder = (builderId, patch) =>
  api.patch(`/builders/${builderId}`, patch).then((r) => r.data.builder)

export const getBuilder = (builderId) =>
  api.get(`/builders/${builderId}`).then((r) => r.data.builder)

export const listProjects = (builderId) =>
  api.get(`/builders/${builderId}/projects`).then((r) => r.data.items)

export const createProject = (builderId, payload) =>
  api.post(`/builders/${builderId}/projects`, payload).then((r) => r.data.project)

export const updateProject = (projectId, patch) =>
  api.patch(`/projects/${projectId}`, patch).then((r) => r.data.project)
