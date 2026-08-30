<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '@/stores/auth'
import NotificationBell from './NotificationBell.vue'

defineProps({
  title: { type: String, required: true },
})

const router = useRouter()
const { user, role, logout } = useAuth()

// Stroke-based 24x24 icon paths, matching the style already used for the
// Modal close icon and the notification bell (stroke="currentColor",
// round caps/joins) — kept hand-rolled rather than pulling in an icon
// library, consistent with this app's existing "no UI-kit dependency" bar
// (charts and the one other icon are hand-rolled SVG too).
const ICONS = {
  dashboard: 'M3 12l9-9 9 9M5 10v10a1 1 0 001 1h4v-6h4v6h4a1 1 0 001-1V10',
  leads: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM4 21a8 8 0 0116 0',
  suggestions: 'M9 18h6M10 21h4M12 3a6 6 0 00-4 10.5c.5.6 1 1.3 1 2.5h6c0-1.2.5-1.9 1-2.5A6 6 0 0012 3z',
  transfers: 'M7 7h13m0 0l-4-4m4 4l-4 4M17 17H4m0 0l4 4m-4-4l4-4',
  builders: 'M4 21V7l8-4 8 4v14M9 21v-6h6v6M4 21h16',
  'project-search': 'M21 21l-4.35-4.35M11 19a8 8 0 100-16 8 8 0 000 16z',
  team: 'M17 20h4v-1a4 4 0 00-3-3.87M8 20H3v-1a4 4 0 013-3.87M13.5 8.5a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0zM19.5 9.5a2 2 0 11-4 0 2 2 0 014 0zM8.5 9.5a2 2 0 11-4 0 2 2 0 014 0z',
}

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard', adminOnly: false },
  { to: '/leads', label: 'Leads', icon: 'leads', adminOnly: false },
  { to: '/transfers', label: 'Transfers', icon: 'transfers', adminOnly: false },
  { to: '/project-search', label: 'Find Projects', icon: 'project-search', adminOnly: false },
  { to: '/suggestions', label: 'Suggestions', icon: 'suggestions', adminOnly: false },
  { to: '/builders', label: 'Builders', icon: 'builders', adminOnly: false },
  { to: '/team-members', label: 'Team', icon: 'team', adminOnly: true },
]

const visibleItems = computed(() => navItems.filter((item) => !item.adminOnly || role.value === 'admin'))
// Bottom tab bar caps at 5 slots: 4 primary destinations + a "More" button
// that opens a sheet with the rest, rather than cramming every item in.
const primaryItems = computed(() => visibleItems.value.slice(0, 4))
const moreItems = computed(() => visibleItems.value.slice(4))

const showMoreSheet = ref(false)

function onLogout() {
  logout()
  router.replace('/login')
}
</script>

<template>
  <div class="min-h-dvh grid grid-cols-1 sm:grid-cols-[4.5rem_1fr] lg:grid-cols-[15rem_1fr] bg-slate-50">
    <!-- Sidebar (>=lg) / icon rail (sm-lg) — hidden on phone in favor of the bottom tab bar. -->
    <aside class="hidden sm:flex flex-col bg-ink-900 text-ink-50 sticky top-0 h-dvh">
      <div class="h-16 shrink-0 flex items-center justify-center lg:justify-start px-0 lg:px-6 border-b border-white/10">
        <span class="text-lg font-semibold tracking-tight text-white">
          <span class="lg:hidden">SH</span>
          <span class="hidden lg:inline">Sara<span class="text-brand-300">Hive</span></span>
        </span>
      </div>

      <nav class="flex-1 px-2 lg:px-3 py-4 space-y-1 overflow-y-auto">
        <router-link
          v-for="item in visibleItems" :key="item.to"
          :to="item.to"
          :title="item.label"
          class="tap-target flex items-center gap-3 px-2.5 lg:px-3 py-2 rounded-md text-sm font-medium text-ink-100 hover:bg-white/10 hover:text-white transition-colors justify-center lg:justify-start"
          active-class="bg-brand-600 text-white hover:bg-brand-600"
        >
          <svg class="w-5 h-5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="ICONS[item.icon]" />
          </svg>
          <span class="hidden lg:inline">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="px-3 py-4 border-t border-white/10 text-xs text-ink-100 hidden lg:block">
        <p class="font-medium text-white">{{ user?.username }}</p>
        <p class="capitalize opacity-70">{{ role === 'admin' ? 'Admin' : 'Team member' }}</p>
      </div>
    </aside>

    <div class="flex flex-col min-w-0">
      <header class="shrink-0 bg-white border-b border-slate-200 flex flex-wrap items-center justify-between gap-y-2 sm:h-16 px-4 sm:px-6 py-2.5 sm:py-0 sticky top-0 z-30">
        <h1 class="text-page-title font-semibold text-slate-800 truncate">{{ title }}</h1>
        <div class="flex items-center flex-wrap justify-end gap-1 sm:gap-3 ml-auto">
          <slot name="actions" />
          <NotificationBell />
          <button
            @click="onLogout"
            class="tap-target text-sm font-medium text-slate-500 hover:text-brand-600 px-3 py-1.5 rounded-md hover:bg-slate-100 transition-colors"
          >
            Log out
          </button>
        </div>
      </header>

      <main class="flex-1 min-w-0 p-4 sm:p-6 pb-24 sm:pb-6 overflow-auto">
        <slot />
      </main>
    </div>

    <!-- Bottom tab bar (<sm / <600px only). -->
    <nav
      class="sm:hidden fixed bottom-0 inset-x-0 z-30 bg-ink-900 border-t border-white/10 flex items-stretch"
      style="padding-bottom: env(safe-area-inset-bottom)"
    >
      <router-link
        v-for="item in primaryItems" :key="item.to"
        :to="item.to"
        class="tap-target flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-medium text-ink-100"
        active-class="text-white"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="ICONS[item.icon]" />
        </svg>
        {{ item.label }}
      </router-link>
      <button
        v-if="moreItems.length"
        @click="showMoreSheet = true"
        class="tap-target flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[11px] font-medium text-ink-100"
      >
        <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <circle cx="5" cy="12" r="1.75" />
          <circle cx="12" cy="12" r="1.75" />
          <circle cx="19" cy="12" r="1.75" />
        </svg>
        More
      </button>
    </nav>

    <!-- "More" bottom sheet — the rest of the nav items that don't fit in the 5-slot bottom bar. -->
    <div v-if="showMoreSheet" class="sm:hidden fixed inset-0 z-40" @click="showMoreSheet = false">
      <div class="absolute inset-0 bg-ink-900/50"></div>
      <div
        class="absolute bottom-0 inset-x-0 bg-white rounded-t-2xl shadow-xl p-4"
        style="padding-bottom: calc(1rem + env(safe-area-inset-bottom))"
        @click.stop
      >
        <div class="w-10 h-1 rounded-full bg-slate-200 mx-auto mb-4"></div>
        <router-link
          v-for="item in moreItems" :key="item.to"
          :to="item.to"
          @click="showMoreSheet = false"
          class="tap-target flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          <svg class="w-5 h-5 shrink-0 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" :d="ICONS[item.icon]" />
          </svg>
          {{ item.label }}
        </router-link>
      </div>
    </div>
  </div>
</template>
