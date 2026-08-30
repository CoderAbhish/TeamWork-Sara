<script setup>
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import {
  listTransferRequests,
  approveTransferRequest,
  rejectTransferRequest,
} from '@/api/leadTransfers'
import { transferStatusColor } from '@/lib/badges'

const { role } = useAuth()
const isAdmin = computed(() => role.value === 'admin')

const requests = ref([])
const loading = ref(true)
const statusFilter = ref(isAdmin.value ? 'pending' : '')
const actingOn = ref(new Set())

const columns = computed(() => [
  { key: 'leadName', label: 'Lead', priority: 'high' },
  { key: 'fromUsername', label: 'From', priority: 'high' },
  { key: 'toUsername', label: 'To', priority: 'high' },
  { key: 'comment', label: 'Comment', priority: 'medium' },
  { key: 'status', label: 'Status', priority: 'high' },
  { key: 'requestedOn', label: 'Requested', priority: 'low' },
  ...(isAdmin.value ? [{ key: 'actions', label: '' }] : []),
])

async function load() {
  loading.value = true
  requests.value = await listTransferRequests(statusFilter.value || undefined)
  loading.value = false
}

async function onApprove(row) {
  actingOn.value.add(row.recordId)
  try {
    await approveTransferRequest(row.recordId)
    await load()
  } finally {
    actingOn.value.delete(row.recordId)
  }
}

async function onReject(row) {
  actingOn.value.add(row.recordId)
  try {
    await rejectTransferRequest(row.recordId)
    await load()
  } finally {
    actingOn.value.delete(row.recordId)
  }
}

function fmtDateTime(value) {
  return value ? new Date(value).toLocaleString() : '—'
}

onMounted(load)
</script>

<template>
  <AppShell title="Lead Transfers">
    <template #actions>
      <select
        v-if="isAdmin"
        v-model="statusFilter"
        @change="load"
        class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
      >
        <option value="pending">Pending</option>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
        <option value="">All</option>
      </select>
    </template>

    <p v-if="!isAdmin" class="text-sm text-slate-500 mb-4">
      Requests you've made to hand a lead to another team member. Start a transfer from the lead's detail page.
    </p>

    <DataTable :columns="columns" :rows="requests" :loading="loading" empty-text="No transfer requests.">
      <template #cell-comment="{ row }">
        <span class="text-slate-600">{{ row.comment }}</span>
      </template>
      <template #cell-status="{ row }">
        <Badge :label="row.status" :color="transferStatusColor(row.status)" />
        <p v-if="row.status === 'rejected' && row.reviewComment" class="text-xs text-slate-400 mt-1">
          {{ row.reviewComment }}
        </p>
      </template>
      <template #cell-requestedOn="{ row }">{{ fmtDateTime(row.requestedOn) }}</template>
      <template #cell-actions="{ row }">
        <div v-if="row.status === 'pending'" class="flex gap-2">
          <button
            @click.stop="onApprove(row)"
            :disabled="actingOn.has(row.recordId)"
            class="px-2.5 py-1 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-xs font-semibold"
          >
            Approve
          </button>
          <button
            @click.stop="onReject(row)"
            :disabled="actingOn.has(row.recordId)"
            class="px-2.5 py-1 rounded-md text-rose-600 hover:bg-rose-50 text-xs font-semibold"
          >
            Reject
          </button>
        </div>
      </template>
    </DataTable>
  </AppShell>
</template>
