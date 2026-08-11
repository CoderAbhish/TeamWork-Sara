<script setup>
import { onMounted, ref } from 'vue'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import { getBuilder, listProjects, createProject, updateProject } from '@/api/builders'
import { getProjectStatuses } from '@/api/lookups'
import { projectStatusColor } from '@/lib/badges'

const props = defineProps({ id: { type: String, required: true } })
const { role } = useAuth()

const builder = ref(null)
const projects = ref([])
const statuses = ref([])
const loading = ref(true)

const showCreateModal = ref(false)
const form = ref({ projectName: '', lookupProjectStatusRecordId: '', startDate: '', plannedCompletionDate: '' })
const saving = ref(false)
const error = ref('')

const columns = [
  { key: 'projectName', label: 'Project' },
  { key: 'statusName', label: 'Status' },
  { key: 'startDate', label: 'Start date' },
  { key: 'plannedCompletionDate', label: 'Planned completion' },
]

async function load() {
  loading.value = true
  const [b, p, s] = await Promise.all([getBuilder(props.id), listProjects(props.id), getProjectStatuses()])
  builder.value = b
  projects.value = p
  statuses.value = s
  loading.value = false
}

async function onCreateProject() {
  error.value = ''
  if (!form.value.projectName.trim() || !form.value.lookupProjectStatusRecordId) {
    error.value = 'Project name and status are required.'
    return
  }
  saving.value = true
  try {
    await createProject(props.id, form.value)
    showCreateModal.value = false
    form.value = { projectName: '', lookupProjectStatusRecordId: '', startDate: '', plannedCompletionDate: '' }
    await load()
  } catch (err) {
    error.value = err.response?.data?.error || 'Could not create project.'
  } finally {
    saving.value = false
  }
}

async function onStatusChange(project, statusId) {
  await updateProject(project.recordId, { lookupProjectStatusRecordId: Number(statusId) })
  await load()
}

function fmtDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

onMounted(load)
</script>

<template>
  <AppShell :title="builder ? builder.builderName : 'Builder'">
    <template #actions>
      <button
        v-if="role === 'admin'"
        @click="showCreateModal = true"
        class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold transition-colors"
      >
        New Project
      </button>
    </template>

    <div v-if="loading" class="text-slate-400 text-sm">Loading…</div>
    <template v-else>
      <div class="mb-4 flex items-center gap-2">
        <Badge :label="builder.isActive ? 'Active' : 'Inactive'" :color="builder.isActive ? 'emerald' : 'slate'" />
        <span class="text-sm text-slate-500">{{ builder.projectCount }} project(s)</span>
      </div>

      <DataTable :columns="columns" :rows="projects" empty-text="No projects for this builder yet.">
        <template #cell-statusName="{ row }">
          <select
            v-if="role === 'admin'"
            :value="row.lookupProjectStatusRecordId"
            @click.stop
            @change="onStatusChange(row, $event.target.value)"
            class="text-xs border border-slate-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand-400"
          >
            <option v-for="s in statuses" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
          </select>
          <Badge v-else :label="row.statusName" :color="projectStatusColor(row.statusName)" />
        </template>
        <template #cell-startDate="{ row }">{{ fmtDate(row.startDate) }}</template>
        <template #cell-plannedCompletionDate="{ row }">{{ fmtDate(row.plannedCompletionDate) }}</template>
      </DataTable>
    </template>

    <Modal v-if="showCreateModal" title="New Project" @close="showCreateModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Project name</label>
          <input
            v-model="form.projectName"
            type="text"
            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Status</label>
          <select
            v-model="form.lookupProjectStatusRecordId"
            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
          >
            <option value="" disabled>Select a status</option>
            <option v-for="s in statuses" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Start date</label>
          <input
            v-model="form.startDate"
            type="date"
            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Planned completion</label>
          <input
            v-model="form.plannedCompletionDate"
            type="date"
            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
          />
        </div>
      </div>
      <p v-if="error" class="text-sm text-rose-600 mt-3">{{ error }}</p>

      <template #footer>
        <button @click="showCreateModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button
          @click="onCreateProject"
          :disabled="saving"
          class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold"
        >
          {{ saving ? 'Creating…' : 'Create' }}
        </button>
      </template>
    </Modal>
  </AppShell>
</template>
