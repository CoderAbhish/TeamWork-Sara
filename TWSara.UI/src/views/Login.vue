<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'
import { dashboardRouteForRole } from '@/router'

const username = ref('')
const password = ref('')
const error = ref('')
const pendingMessage = ref('')
const submitting = ref(false)

const router = useRouter()
const { login } = useAuth()

async function onSubmit() {
  error.value = ''
  pendingMessage.value = ''
  submitting.value = true
  try {
    await login(username.value, password.value)
    router.replace(dashboardRouteForRole())
  } catch (err) {
    if (err.response?.data?.error === 'pending_approval') {
      pendingMessage.value = err.response.data.message
    } else {
      error.value = err.response?.data?.error || 'Login failed. Please try again.'
    }
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-ink-900 px-4">
    <form class="w-full max-w-sm bg-white rounded-lg shadow-xl p-8" @submit.prevent="onSubmit">
      <div class="mb-6 text-center">
        <p class="text-2xl font-semibold tracking-tight text-ink-900">
          Sara<span class="text-brand-500">Hive</span>
        </p>
        <p class="text-sm text-slate-500 mt-1">Sign in to your workspace</p>
      </div>

      <label for="username" class="block text-sm font-medium text-slate-600 mt-4 mb-1">
        Username or email
      </label>
      <input
        id="username"
        v-model="username"
        type="text"
        autocomplete="username"
        required
        class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
      />

      <label for="password" class="block text-sm font-medium text-slate-600 mt-4 mb-1">
        Password
      </label>
      <input
        id="password"
        v-model="password"
        type="password"
        autocomplete="current-password"
        required
        class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
      />

      <p v-if="error" class="text-sm text-rose-600 mt-3">{{ error }}</p>
      <p v-if="pendingMessage" class="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2 mt-3">
        {{ pendingMessage }}
      </p>

      <button
        type="submit"
        :disabled="submitting"
        class="w-full mt-6 py-2.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold transition-colors"
      >
        {{ submitting ? 'Signing in…' : 'Sign in' }}
      </button>

      <router-link to="/register" class="block text-center text-sm text-brand-600 hover:text-brand-700 mt-4">
        New team member? Create an account
      </router-link>
    </form>
  </div>
</template>
