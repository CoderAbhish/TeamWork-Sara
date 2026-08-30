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

export const getProject = (projectId) =>
  api.get(`/projects/${projectId}`).then((r) => r.data.project)

// Cross-builder project search — filters: search, location, builderId,
// propertyTypeId, saleTypeId, listingTypeId, lookupProjectStatusRecordId,
// minPrice, maxPrice, page, pageSize.
export const searchProjects = (params = {}) =>
  api.get('/projects/search', { params }).then((r) => r.data)

export const updateProject = (projectId, patch) =>
  api.patch(`/projects/${projectId}`, patch).then((r) => r.data.project)

export const listManagers = (projectId) =>
  api.get(`/projects/${projectId}/managers`).then((r) => r.data.items)

export const createManager = (projectId, payload) =>
  api.post(`/projects/${projectId}/managers`, payload).then((r) => r.data.manager)

export const updateManager = (managerId, patch) =>
  api.patch(`/project-managers/${managerId}`, patch).then((r) => r.data.manager)

export const deleteManager = (managerId) => api.delete(`/project-managers/${managerId}`)

export const listConfigurations = (projectId) =>
  api.get(`/projects/${projectId}/configurations`).then((r) => r.data.items)

export const createConfiguration = (projectId, payload) =>
  api.post(`/projects/${projectId}/configurations`, payload).then((r) => r.data.configuration)

export const updateConfiguration = (configId, patch) =>
  api.patch(`/project-configurations/${configId}`, patch).then((r) => r.data.configuration)

export const deleteConfiguration = (configId) => api.delete(`/project-configurations/${configId}`)
