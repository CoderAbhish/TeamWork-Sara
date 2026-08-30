<script setup>
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'
import NotificationBell from './NotificationBell.vue'

defineProps({
  title: { type: String, required: true },
})

const router = useRouter()
const { user, role, logout } = useAuth()

const navItems = [
  { to: '/dashboard', label: 'Dashboard', adminOnly: false },
  { to: '/leads', label: 'Leads', adminOnly: false },
  { to: '/suggestions', label: 'Suggestions', adminOnly: false },
  { to: '/transfers', label: 'Transfers', adminOnly: false },
  { to: '/builders', label: 'Builders', adminOnly: false },
  { to: '/project-search', label: 'Find Projects', adminOnly: false },
  { to: '/team-members', label: 'Team', adminOnly: true },
]

function onLogout() {
  logout()
  router.replace('/login')
}
</script>

<template>
  <div class="min-h-screen flex bg-slate-50">
    <aside class="w-60 shrink-0 bg-ink-900 text-ink-50 flex flex-col">
      <div class="h-16 flex items-center px-6 border-b border-white/10">
        <span class="text-lg font-semibold tracking-tight text-white">Sara<span class="text-brand-300">Hive</span></span>
      </div>

      <nav class="flex-1 px-3 py-4 space-y-1">
        <template v-for="item in navItems" :key="item.to">
          <router-link
            v-if="!item.adminOnly || role === 'admin'"
            :to="item.to"
            class="block px-3 py-2 rounded-md text-sm font-medium text-ink-100 hover:bg-white/10 hover:text-white transition-colors"
            active-class="bg-brand-600 text-white hover:bg-brand-600"
          >
            {{ item.label }}
          </router-link>
        </template>
      </nav>

      <div class="px-3 py-4 border-t border-white/10 text-xs text-ink-100">
        <p class="font-medium text-white">{{ user?.username }}</p>
        <p class="capitalize opacity-70">{{ role === 'admin' ? 'Admin' : 'Team member' }}</p>
      </div>
    </aside>

    <div class="flex-1 flex flex-col min-w-0">
      <header class="h-16 shrink-0 bg-white border-b border-slate-200 flex items-center justify-between px-6">
        <h1 class="text-lg font-semibold text-slate-800">{{ title }}</h1>
        <div class="flex items-center gap-3">
          <slot name="actions" />
          <NotificationBell />
          <button
            @click="onLogout"
            class="text-sm font-medium text-slate-500 hover:text-brand-600 px-3 py-1.5 rounded-md hover:bg-slate-100 transition-colors"
          >
            Log out
          </button>
        </div>
      </header>

      <main class="flex-1 min-w-0 p-6 overflow-auto">
        <slot />
      </main>
    </div>
  </div>
</template>
