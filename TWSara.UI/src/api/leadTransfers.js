import api from '@/lib/api'

export const listTransferRequests = (status) =>
  api.get('/lead-transfer-requests', { params: status ? { status } : {} }).then((r) => r.data.items)

export const createTransferRequest = (custProjectId, toUserId, comment) =>
  api
    .post('/lead-transfer-requests', { custProjectId, toUserId, comment })
    .then((r) => r.data.transferRequest)

export const approveTransferRequest = (transferId) =>
  api.post(`/lead-transfer-requests/${transferId}/approve`).then((r) => r.data.transferRequest)

export const rejectTransferRequest = (transferId, reviewComment) =>
  api
    .post(`/lead-transfer-requests/${transferId}/reject`, { reviewComment })
    .then((r) => r.data.transferRequest)
