<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import {
  listSuggestions,
  createSuggestion,
  approveSuggestion,
  rejectSuggestion,
  importSuggestionsCsv,
} from '@/api/leadSuggestions'
import { listBuilders, listProjects } from '@/api/builders'

const { role } = useAuth()
const router = useRouter()
const isAdmin = computed(() => role.value === 'admin')

const suggestions = ref([])
const loading = ref(true)
const statusFilter = ref(isAdmin.value ? 'pending' : '')
const actingOn = ref(new Set())

const builders = ref([])

const showCreateModal = ref(false)
const createForm = ref({ leadName: '', contactNumber: '', alternateNumber: '', leadLocation: '', builderId: '', projectId: '' })
const createProjects = ref([])
const creating = ref(false)
const createError = ref('')

const importInput = ref(null)
const importResult = ref(null)
const importing = ref(false)

const statusColorFor = { pending: 'amber', approved: 'emerald', rejected: 'rose' }

const columns = computed(() => [
  { key: 'leadName', label: 'Name' },
  { key: 'contactNumber', label: 'Contact' },
  { key: 'project', label: 'Project' },
  ...(isAdmin.value ? [{ key: 'suggestedBy', label: 'Suggested by' }] : []),
  { key: 'status', label: 'Status' },
  { key: 'createdOn', label: 'Created' },
  ...(isAdmin.value ? [{ key: 'actions', label: '' }] : []),
])

async function load() {
  loading.value = true
  suggestions.value = await listSuggestions(statusFilter.value || undefined)
  loading.value = false
}

watch(() => createForm.value.builderId, async (builderId) => {
  createForm.value.projectId = ''
  createProjects.value = builderId ? await listProjects(builderId) : []
})

async function onCreate() {
  createError.value = ''
  const f = createForm.value
  if (!f.leadName.trim() || !f.contactNumber.trim()) {
    createError.value = 'Name and contact number are required.'
    return
  }
  creating.value = true
  try {
    await createSuggestion({
      leadName: f.leadName.trim(),
      contactNumber: f.contactNumber.trim(),
      alternateNumber: f.alternateNumber.trim() || undefined,
      leadLocation: f.leadLocation.trim() || undefined,
      builderId: f.builderId ? Number(f.builderId) : undefined,
      projectId: f.projectId ? Number(f.projectId) : undefined,
    })
    showCreateModal.value = false
    createForm.value = { leadName: '', contactNumber: '', alternateNumber: '', leadLocation: '', builderId: '', projectId: '' }
    await load()
  } catch (err) {
    createError.value = err.response?.data?.error || 'Could not submit suggestion.'
  } finally {
    creating.value = false
  }
}

async function onApprove(suggestion) {
  actingOn.value.add(suggestion.recordId)
  try {
    const result = await approveSuggestion(suggestion.recordId)
    await load()
    if (result?.lead?.recordId) router.push(`/leads/${result.lead.recordId}`)
  } finally {
    actingOn.value.delete(suggestion.recordId)
  }
}

async function onReject(suggestion) {
  actingOn.value.add(suggestion.recordId)
  try {
    await rejectSuggestion(suggestion.recordId)
    await load()
  } finally {
    actingOn.value.delete(suggestion.recordId)
  }
}

function triggerImport() {
  importInput.value?.click()
}

async function onImportFile(event) {
  const file = event.target.files?.[0]
  if (!file) return
  importing.value = true
  importResult.value = null
  try {
    importResult.value = await importSuggestionsCsv(file)
    await load()
  } finally {
    importing.value = false
    event.target.value = ''
  }
}

function fmtDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

onMounted(async () => {
  if (!isAdmin.value) builders.value = await listBuilders()
  await load()
})
</script>

<template>
  <AppShell title="Lead Suggestions">
    <template #actions>
      <template v-if="!isAdmin">
        <button
          @click="triggerImport"
          :disabled="importing"
          class="px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100 disabled:opacity-60"
        >
          {{ importing ? 'Importing…' : 'Import CSV' }}
        </button>
        <input ref="importInput" type="file" accept=".csv" class="hidden" @change="onImportFile" />
        <button
          @click="showCreateModal = true"
          class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold transition-colors"
        >
          Suggest a Lead
        </button>
      </template>
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

    <div
      v-if="importResult"
      class="mb-4 px-4 py-3 rounded-md bg-emerald-50 border border-emerald-200 text-sm text-emerald-800 flex justify-between items-start"
    >
      <div>
        <p><strong>{{ importResult.created }}</strong> suggestion(s) submitted for review.</p>
        <p v-if="importResult.errors.length" class="text-rose-600 mt-1">
          {{ importResult.errors.length }} row(s) skipped:
          <span v-for="e in importResult.errors.slice(0, 3)" :key="e.row"> row {{ e.row }} ({{ e.message }});</span>
        </p>
      </div>
      <button @click="importResult = null" class="text-emerald-600 hover:text-emerald-800 text-xs font-medium">Dismiss</button>
    </div>

    <DataTable :columns="columns" :rows="suggestions" :loading="loading" empty-text="No suggestions yet.">
      <template #cell-leadName="{ row }">{{ row.leadName }}</template>
      <template #cell-contactNumber="{ row }">{{ row.contactNumber }}</template>
      <template #cell-project="{ row }">
        <span v-if="row.projectName">{{ row.projectName }} — {{ row.builderName }}</span>
        <span v-else class="text-slate-300 text-xs">—</span>
      </template>
      <template #cell-suggestedBy="{ row }">{{ row.suggestedByUsername }}</template>
      <template #cell-status="{ row }">
        <Badge :label="row.status" :color="statusColorFor[row.status]" />
      </template>
      <template #cell-createdOn="{ row }">{{ fmtDate(row.createdOn) }}</template>
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

    <Modal v-if="showCreateModal" title="Suggest a Lead" width-class="max-w-lg" @close="showCreateModal = false">
      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="block text-sm font-medium text-slate-600 mb-1">Lead name</label>
          <input v-model="createForm.leadName" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Contact number</label>
          <input v-model="createForm.contactNumber" type="tel" maxlength="10" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Alternate number</label>
          <input v-model="createForm.alternateNumber" type="tel" maxlength="10" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium text-slate-600 mb-1">Location</label>
          <input v-model="createForm.leadLocation" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Builder (optional)</label>
          <select v-model="createForm.builderId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
            <option value="">Not sure</option>
            <option v-for="b in builders" :key="b.recordId" :value="b.recordId">{{ b.builderName }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Project (optional)</label>
          <select v-model="createForm.projectId" :disabled="!createForm.builderId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-slate-50">
            <option value="">Not sure</option>
            <option v-for="p in createProjects" :key="p.recordId" :value="p.recordId">{{ p.projectName }}</option>
          </select>
        </div>
      </div>
      <p v-if="createError" class="text-sm text-rose-600 mt-3">{{ createError }}</p>

      <template #footer>
        <button @click="showCreateModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button
          @click="onCreate"
          :disabled="creating"
          class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold"
        >
          {{ creating ? 'Submitting…' : 'Submit' }}
        </button>
      </template>
    </Modal>
  </AppShell>
</template>
