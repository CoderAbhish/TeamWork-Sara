<script setup>
import { ref } from 'vue'
import { useAuth } from '@/stores/auth'

const username = ref('')
const emailId = ref('')
const password = ref('')
const contactNumber = ref('')
const error = ref('')
const submitting = ref(false)
const submitted = ref(false)

const { register } = useAuth()

async function onSubmit() {
  error.value = ''
  submitting.value = true
  try {
    await register({
      username: username.value,
      emailId: emailId.value,
      password: password.value,
      contactNumber: contactNumber.value,
    })
    submitted.value = true
  } catch (err) {
    error.value = err.response?.data?.error || 'Registration failed. Please try again.'
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-ink-900 px-4">
    <div v-if="submitted" class="w-full max-w-sm bg-white rounded-lg shadow-xl p-8 text-center">
      <p class="text-2xl font-semibold tracking-tight text-ink-900 mb-4">
        Sara<span class="text-brand-500">Hive</span>
      </p>
      <div class="w-12 h-12 rounded-full bg-amber-100 text-amber-600 flex items-center justify-center mx-auto mb-4">
        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      </div>
      <p class="text-slate-700 font-medium">Registration submitted</p>
      <p class="text-sm text-slate-500 mt-2">
        An admin will review your account before you can sign in. Please check back soon.
      </p>
      <router-link to="/login" class="block text-center text-sm text-brand-600 hover:text-brand-700 mt-6 font-medium">
        Back to sign in
      </router-link>
    </div>

    <form v-else class="w-full max-w-sm bg-white rounded-lg shadow-xl p-8" @submit.prevent="onSubmit">
      <div class="mb-6 text-center">
        <p class="text-2xl font-semibold tracking-tight text-ink-900">
          Sara<span class="text-brand-500">Hive</span>
        </p>
        <p class="text-sm text-slate-500 mt-1">Team member sign up</p>
      </div>

      <label for="username" class="block text-sm font-medium text-slate-600 mt-4 mb-1">Username</label>
      <input
        id="username" v-model="username" type="text" autocomplete="username" required
        class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
      />

      <label for="emailId" class="block text-sm font-medium text-slate-600 mt-4 mb-1">Email</label>
      <input
        id="emailId" v-model="emailId" type="email" autocomplete="email" required
        class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
      />

      <label for="contactNumber" class="block text-sm font-medium text-slate-600 mt-4 mb-1">Contact number</label>
      <input
        id="contactNumber" v-model="contactNumber" type="tel" maxlength="10"
        class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
      />

      <label for="password" class="block text-sm font-medium text-slate-600 mt-4 mb-1">Password</label>
      <input
        id="password" v-model="password" type="password" autocomplete="new-password" minlength="8" required
        class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
      />

      <p v-if="error" class="text-sm text-rose-600 mt-3">{{ error }}</p>

      <button
        type="submit"
        :disabled="submitting"
        class="w-full mt-6 py-2.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold transition-colors"
      >
        {{ submitting ? 'Submitting…' : 'Create account' }}
      </button>

      <router-link to="/login" class="block text-center text-sm text-brand-600 hover:text-brand-700 mt-4">
        Already have an account? Sign in
      </router-link>
    </form>
  </div>
</template>
