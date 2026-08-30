import api from '@/lib/api'

export const listNotifications = () => api.get('/notifications').then((r) => r.data.items)

export const dismissNotification = (key) => api.post('/notifications/dismiss', { key })
