import api from '@/lib/api'

export const listTeamMembers = () => api.get('/team-members').then((r) => r.data.items)

// A minimal peer list any authenticated team member can call (unlike
// listTeamMembers, which is admin-only) — used to pick a transfer target.
export const listTeamMemberOptions = () => api.get('/team-members/options').then((r) => r.data.items)

export const getTeamMember = (userId) =>
  api.get(`/team-members/${userId}`).then((r) => r.data.teamMember)

export const setTeamMemberActive = (userId, isActive) =>
  api.patch(`/team-members/${userId}`, { isActive }).then((r) => r.data.teamMember)

export const setTeamMemberApproved = (userId, isApproved) =>
  api.patch(`/team-members/${userId}`, { isApproved }).then((r) => r.data.teamMember)

export const getTeamMemberLeads = (userId) =>
  api.get(`/team-members/${userId}/leads`).then((r) => r.data.items)
