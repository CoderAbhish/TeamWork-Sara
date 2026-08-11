import { computed, reactive } from 'vue'
import api from '@/lib/api'

const state = reactive({
  token: localStorage.getItem('accessToken') || null,
  user: JSON.parse(localStorage.getItem('authUser') || 'null'),
})

function _applySession(data) {
  state.token = data.access_token
  state.user = data.user
  localStorage.setItem('accessToken', data.access_token)
  localStorage.setItem('authUser', JSON.stringify(data.user))
  return data.user
}

async function login(username, password) {
  const { data } = await api.post('/auth/login', { username, password })
  return _applySession(data)
}

async function register({ username, emailId, password, contactNumber, alternateNumber }) {
  const { data } = await api.post('/auth/register', {
    username,
    emailId,
    password,
    contactNumber,
    alternateNumber,
  })
  // No session is issued here — the account is pending admin approval.
  return data
}

function logout() {
  state.token = null
  state.user = null
  localStorage.removeItem('accessToken')
  localStorage.removeItem('authUser')
}

export function useAuth() {
  return {
    user: computed(() => state.user),
    role: computed(() => state.user?.role ?? null),
    isAuthenticated: computed(() => !!state.token),
    login,
    register,
    logout,
  }
}
