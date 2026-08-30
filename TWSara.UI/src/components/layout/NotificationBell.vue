<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { listNotifications, dismissNotification } from '@/api/notifications'

const router = useRouter()
const items = ref([])
const open = ref(false)
let pollTimer = null

const SEVERITY_DOT = { urgent: 'bg-rose-500', warning: 'bg-amber-500', info: 'bg-sky-500' }
// unassignedLeads is a live count, not a discrete event — dismissing it
// wouldn't make sense since it isn't "read", it just changes.
const DISMISSIBLE_TYPES = new Set(['followUpReminder', 'registrationExpired'])

async function load() {
  try {
    items.value = await listNotifications()
  } catch {
    // Polling failure shouldn't be disruptive — just try again next tick.
  }
}

async function onDismiss(item, event) {
  event.stopPropagation()
  items.value = items.value.filter((i) => i.key !== item.key)
  await dismissNotification(item.key)
}

function onItemClick(item) {
  open.value = false
  if (item.type === 'transferRequest') {
    router.push('/transfers')
  } else if (item.leadId) {
    router.push(`/leads/${item.leadId}`)
  } else if (item.type === 'unassignedLeads') {
    router.push('/leads')
  }
}

onMounted(() => {
  load()
  pollTimer = setInterval(load, 60000)
})
onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <div class="relative">
    <button
      @click="open = !open"
      type="button"
      class="relative p-2 rounded-md text-slate-500 hover:text-brand-600 hover:bg-slate-100 transition-colors"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 17h5l-1.4-1.4A2 2 0 0118 14.2V11a6 6 0 10-12 0v3.2a2 2 0 01-.6 1.4L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
      </svg>
      <span
        v-if="items.length"
        class="absolute top-0.5 right-0.5 min-w-[1.1rem] h-[1.1rem] px-1 rounded-full bg-rose-500 text-white text-[10px] font-semibold flex items-center justify-center leading-none"
      >
        {{ items.length > 9 ? '9+' : items.length }}
      </span>
    </button>

    <div v-if="open" class="fixed inset-0 z-40" @click="open = false"></div>
    <div v-if="open" class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-xl border border-slate-200 z-50 max-h-96 overflow-y-auto">
      <div class="px-4 py-3 border-b border-slate-100">
        <p class="text-sm font-semibold text-slate-700">Notifications</p>
      </div>
      <p v-if="!items.length" class="px-4 py-6 text-sm text-slate-400 text-center">You're all caught up.</p>
      <ul v-else class="divide-y divide-slate-100">
        <li
          v-for="item in items" :key="item.key"
          @click="onItemClick(item)"
          class="px-4 py-3 hover:bg-slate-50 cursor-pointer flex items-start gap-2"
        >
          <span class="w-2 h-2 rounded-full mt-1.5 shrink-0" :class="SEVERITY_DOT[item.severity] || 'bg-slate-400'"></span>
          <div class="flex-1 min-w-0">
            <p class="text-sm text-slate-800 font-medium">{{ item.title }}</p>
            <p class="text-xs text-slate-500 mt-0.5">{{ item.message }}</p>
          </div>
          <button
            v-if="DISMISSIBLE_TYPES.has(item.type)"
            @click="onDismiss(item, $event)"
            type="button"
            class="text-slate-300 hover:text-slate-500 shrink-0 text-sm leading-none px-1"
          >
            ✕
          </button>
        </li>
      </ul>
    </div>
  </div>
</template>
