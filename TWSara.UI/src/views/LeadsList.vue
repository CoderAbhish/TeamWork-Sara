<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import { listLeads, createLead, assignLeads, importLeadsCsv, downloadLeadsCsv } from '@/api/leads'
import { listBuilders, listProjects } from '@/api/builders'
import { listTeamMembers } from '@/api/teamMembers'
import { getLeadStatuses, getLeadCategories } from '@/api/lookups'
import { statusColor, categoryColor } from '@/lib/badges'

const { role } = useAuth()
const router = useRouter()
const isAdmin = computed(() => role.value === 'admin')

const leads = ref([])
const total = ref(0)
const loading = ref(true)

const statuses = ref([])
const categories = ref([])
const builders = ref([])
const teamMembers = ref([])

const search = ref('')
const statusId = ref('')
const categoryId = ref('')
const builderId = ref('')
const assignedToUserId = ref('')
const sortBy = ref('createdOn')
const sortDir = ref('desc')
const page = ref(1)
const pageSize = 20

const selectedIds = ref(new Set())
const bulkAssignTo = ref('')
const bulkAssigning = ref(false)

const showCreateModal = ref(false)
const createForm = ref({
  leadName: '', contactNumber: '', alternateNumber: '', leadLocation: '',
  builderId: '', projectId: '', assignedToUserId: '',
})
const createProjects = ref([])
const creating = ref(false)
const createError = ref('')

const importInput = ref(null)
const importResult = ref(null)
const importing = ref(false)

const columns = computed(() => {
  const cols = [
    ...(isAdmin.value ? [{ key: 'select', label: '' }] : []),
    { key: 'leadName', label: 'Name' },
    { key: 'contactNumber', label: 'Contact' },
    { key: 'project', label: 'Project' },
    { key: 'status', label: 'Status', sortable: true },
    { key: 'category', label: 'Category' },
    ...(isAdmin.value ? [{ key: 'assignedTo', label: 'Assigned to' }] : []),
    { key: 'createdOn', label: 'Created', sortable: true },
  ]
  return cols
})

function currentFilterParams() {
  const params = { sortBy: sortBy.value, sortDir: sortDir.value, page: page.value, pageSize }
  if (search.value) params.search = search.value
  if (statusId.value) params.status = statusId.value
  if (categoryId.value) params.category = categoryId.value
  if (builderId.value) params.builderId = builderId.value
  if (isAdmin.value && assignedToUserId.value) params.assignedToUserId = assignedToUserId.value
  return params
}

async function loadLeads() {
  loading.value = true
  const result = await listLeads(currentFilterParams())
  leads.value = result.items
  total.value = result.total
  selectedIds.value = new Set()
  loading.value = false
}

async function loadFilters() {
  const [s, c, b] = await Promise.all([getLeadStatuses(), getLeadCategories(), listBuilders()])
  statuses.value = s
  categories.value = c
  builders.value = b
  if (isAdmin.value) teamMembers.value = await listTeamMembers()
}

function onSort(key) {
  if (sortBy.value === key) {
    sortDir.value = sortDir.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortDir.value = 'asc'
  }
  loadLeads()
}

function onFilterChange() {
  page.value = 1
  loadLeads()
}

function toggleSelect(id) {
  const next = new Set(selectedIds.value)
  next.has(id) ? next.delete(id) : next.add(id)
  selectedIds.value = next
}

async function onBulkAssign() {
  if (!bulkAssignTo.value || !selectedIds.value.size) return
  bulkAssigning.value = true
  try {
    await assignLeads(Array.from(selectedIds.value), Number(bulkAssignTo.value))
    bulkAssignTo.value = ''
    await loadLeads()
  } finally {
    bulkAssigning.value = false
  }
}

watch(() => createForm.value.builderId, async (builderIdValue) => {
  createForm.value.projectId = ''
  createProjects.value = builderIdValue ? await listProjects(builderIdValue) : []
})

async function onCreateLead() {
  createError.value = ''
  const f = createForm.value
  if (!f.leadName.trim() || !f.contactNumber.trim()) {
    createError.value = 'Name and contact number are required.'
    return
  }
  creating.value = true
  try {
    await createLead({
      leadName: f.leadName.trim(),
      contactNumber: f.contactNumber.trim(),
      alternateNumber: f.alternateNumber.trim() || undefined,
      leadLocation: f.leadLocation.trim() || undefined,
      projectId: f.projectId ? Number(f.projectId) : undefined,
      assignedToUserId: f.assignedToUserId ? Number(f.assignedToUserId) : undefined,
    })
    showCreateModal.value = false
    createForm.value = { leadName: '', contactNumber: '', alternateNumber: '', leadLocation: '', builderId: '', projectId: '', assignedToUserId: '' }
    await loadLeads()
  } catch (err) {
    createError.value = err.response?.data?.error || 'Could not create lead.'
  } finally {
    creating.value = false
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
    importResult.value = await importLeadsCsv(file)
    await loadLeads()
  } finally {
    importing.value = false
    event.target.value = ''
  }
}

async function onExport() {
  await downloadLeadsCsv(currentFilterParams())
}

function fmtDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

onMounted(async () => {
  await loadFilters()
  await loadLeads()
})
</script>

<template>
  <AppShell title="Leads">
    <template #actions>
      <template v-if="isAdmin">
        <button @click="onExport" class="px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Export CSV
        </button>
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
          New Lead
        </button>
      </template>
    </template>

    <div
      v-if="importResult"
      class="mb-4 px-4 py-3 rounded-md bg-emerald-50 border border-emerald-200 text-sm text-emerald-800 flex justify-between items-start"
    >
      <div>
        <p><strong>{{ importResult.created }}</strong> created, <strong>{{ importResult.updated }}</strong> updated.</p>
        <p v-if="importResult.errors.length" class="text-rose-600 mt-1">
          {{ importResult.errors.length }} row(s) skipped:
          <span v-for="e in importResult.errors.slice(0, 3)" :key="e.row"> row {{ e.row }} ({{ e.message }});</span>
        </p>
      </div>
      <button @click="importResult = null" class="text-emerald-600 hover:text-emerald-800 text-xs font-medium">Dismiss</button>
    </div>

    <div class="bg-white rounded-lg border border-slate-200 p-4 mb-4 flex flex-wrap gap-3 items-end">
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Search</label>
        <input
          v-model="search" @keyup.enter="onFilterChange" type="text" placeholder="Name, contact, location"
          class="px-3 py-1.5 border border-slate-300 rounded-md text-sm w-48 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Status</label>
        <select v-model="statusId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="s in statuses" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Category</label>
        <select v-model="categoryId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="c in categories" :key="c.recordId" :value="c.recordId">{{ c.recordName }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Builder</label>
        <select v-model="builderId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="b in builders" :key="b.recordId" :value="b.recordId">{{ b.builderName }}</option>
        </select>
      </div>
      <div v-if="isAdmin">
        <label class="block text-xs font-medium text-slate-500 mb-1">Assigned to</label>
        <select v-model="assignedToUserId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">Anyone</option>
          <option v-for="m in teamMembers" :key="m.recordId" :value="m.recordId">{{ m.username }}</option>
        </select>
      </div>
      <button @click="onFilterChange" class="px-3 py-1.5 rounded-md bg-ink-900 hover:bg-ink-800 text-white text-sm font-medium">
        Apply
      </button>
    </div>

    <div v-if="isAdmin && selectedIds.size" class="mb-4 px-4 py-3 rounded-md bg-brand-50 border border-brand-200 flex items-center gap-3">
      <span class="text-sm text-brand-800 font-medium">{{ selectedIds.size }} selected</span>
      <select v-model="bulkAssignTo" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
        <option value="">Assign to…</option>
        <option v-for="m in teamMembers" :key="m.recordId" :value="m.recordId">{{ m.username }}</option>
      </select>
      <button
        @click="onBulkAssign"
        :disabled="!bulkAssignTo || bulkAssigning"
        class="px-3 py-1.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold"
      >
        {{ bulkAssigning ? 'Assigning…' : 'Assign' }}
      </button>
    </div>

    <DataTable
      :columns="columns"
      :rows="leads"
      :loading="loading"
      :sort-by="sortBy"
      :sort-dir="sortDir"
      empty-text="No leads found."
      @sort="onSort"
      @row-click="(row) => router.push(`/leads/${row.recordId}`)"
    >
      <template #cell-select="{ row }">
        <input
          type="checkbox"
          :checked="selectedIds.has(row.recordId)"
          @click.stop="toggleSelect(row.recordId)"
          class="rounded border-slate-300"
        />
      </template>
      <template #cell-leadName="{ row }">{{ row.customer.leadName }}</template>
      <template #cell-contactNumber="{ row }">{{ row.customer.contactNumber }}</template>
      <template #cell-project="{ row }">
        <template v-if="row.project">
          <div class="text-sm">{{ row.project.projectName }}</div>
          <div class="text-xs text-slate-400">{{ row.project.builderName }}</div>
        </template>
        <span v-else class="text-slate-300 text-xs">No project yet</span>
      </template>
      <template #cell-status="{ row }">
        <Badge v-if="row.leadStatusName" :label="row.leadStatusName" :color="statusColor(row.leadStatusName)" />
        <span v-else class="text-slate-300 text-xs">—</span>
      </template>
      <template #cell-category="{ row }">
        <Badge v-if="row.leadCategoryName" :label="row.leadCategoryName" :color="categoryColor(row.leadCategoryName)" />
        <span v-else class="text-slate-300 text-xs">—</span>
      </template>
      <template #cell-assignedTo="{ row }">{{ row.assignedToUsername || '—' }}</template>
      <template #cell-createdOn="{ row }">{{ fmtDate(row.createdOn) }}</template>
    </DataTable>

    <div v-if="total > pageSize" class="flex justify-between items-center mt-4 text-sm text-slate-500">
      <span>{{ total }} lead(s) — page {{ page }} of {{ Math.ceil(total / pageSize) }}</span>
      <div class="flex gap-2">
        <button
          :disabled="page <= 1"
          @click="page--; loadLeads()"
          class="px-3 py-1.5 rounded-md border border-slate-300 disabled:opacity-40"
        >
          Previous
        </button>
        <button
          :disabled="page >= Math.ceil(total / pageSize)"
          @click="page++; loadLeads()"
          class="px-3 py-1.5 rounded-md border border-slate-300 disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </div>

    <Modal v-if="showCreateModal" title="New Lead" width-class="max-w-xl" @close="showCreateModal = false">
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
          <label class="block text-sm font-medium text-slate-600 mb-1">Builder</label>
          <select v-model="createForm.builderId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
            <option value="">Select builder</option>
            <option v-for="b in builders" :key="b.recordId" :value="b.recordId">{{ b.builderName }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Project</label>
          <select v-model="createForm.projectId" :disabled="!createForm.builderId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-slate-50">
            <option value="">Select project</option>
            <option v-for="p in createProjects" :key="p.recordId" :value="p.recordId">{{ p.projectName }}</option>
          </select>
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium text-slate-600 mb-1">Assign to</label>
          <select v-model="createForm.assignedToUserId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
            <option value="">Unassigned</option>
            <option v-for="m in teamMembers" :key="m.recordId" :value="m.recordId">{{ m.username }}</option>
          </select>
        </div>
      </div>
      <p v-if="createError" class="text-sm text-rose-600 mt-3">{{ createError }}</p>

      <template #footer>
        <button @click="showCreateModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button
          @click="onCreateLead"
          :disabled="creating"
          class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold"
        >
          {{ creating ? 'Creating…' : 'Create' }}
        </button>
      </template>
    </Modal>
  </AppShell>
</template>
