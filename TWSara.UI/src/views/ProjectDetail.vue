<script setup>
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import {
  getProject,
  updateProject,
  listManagers,
  createManager,
  updateManager,
  deleteManager,
  listConfigurations,
  createConfiguration,
  updateConfiguration,
  deleteConfiguration,
} from '@/api/builders'
import { listLeads } from '@/api/leads'
import { getProjectStatuses, getPropertyTypes, getSaleTypes, getListingTypes } from '@/api/lookups'
import { projectStatusColor } from '@/lib/badges'

const props = defineProps({ id: { type: String, required: true } })
const { role } = useAuth()
const isAdmin = computed(() => role.value === 'admin')

const project = ref(null)
const managers = ref([])
const configurations = ref([])
const statuses = ref([])
const propertyTypes = ref([])
const saleTypes = ref([])
const listingTypes = ref([])
const loading = ref(true)
const canEditManagers = ref(false)

const editingDetails = ref(false)
const detailsForm = ref({})
const savingDetails = ref(false)
const detailsError = ref('')

const showManagerModal = ref(false)
const managerForm = ref({ managerName: '', contactNumber: '', emailId: '', notes: '' })
const savingManager = ref(false)
const managerError = ref('')

const showConfigModal = ref(false)
const configForm = ref({
  configurationLabel: '', sizeSqFt: '', plotDimensionSqFt: '', startingPriceAmount: '', baseRatePerSqFt: '', notes: '',
})
const savingConfig = ref(false)
const configError = ref('')

const configColumns = [
  { key: 'configurationLabel', label: 'Configuration' },
  { key: 'sizeSqFt', label: 'Size (sq.ft)' },
  { key: 'plotDimensionSqFt', label: 'Plot dimension (sq.ft)' },
  { key: 'startingPriceAmount', label: 'Starting price' },
  { key: 'baseRatePerSqFt', label: 'Base rate/sq.ft' },
  ...(isAdmin.value ? [{ key: 'actions', label: '' }] : []),
]

async function load() {
  loading.value = true
  const [p, m, c, s, pt, st, lt] = await Promise.all([
    getProject(props.id),
    listManagers(props.id),
    listConfigurations(props.id),
    getProjectStatuses(),
    getPropertyTypes(),
    getSaleTypes(),
    getListingTypes(),
  ])
  project.value = p
  managers.value = m
  configurations.value = c
  statuses.value = s
  propertyTypes.value = pt
  saleTypes.value = st
  listingTypes.value = lt

  if (isAdmin.value) {
    canEditManagers.value = true
  } else {
    const mine = await listLeads({ projectId: props.id, pageSize: 1 })
    canEditManagers.value = mine.total > 0
  }
  loading.value = false
}

function startEditDetails() {
  detailsError.value = ''
  detailsForm.value = {
    lookupProjectStatusRecordId: project.value.lookupProjectStatusRecordId,
    location: project.value.location || '',
    propertyTypeId: project.value.propertyTypeId || '',
    saleTypeId: project.value.saleTypeId || '',
    listingTypeId: project.value.listingTypeId || '',
    areaExtent: project.value.areaExtent || '',
    structureDescription: project.value.structureDescription || '',
    numberOfTowers: project.value.numberOfTowers ?? '',
    totalUnits: project.value.totalUnits ?? '',
    reraNumber: project.value.reraNumber || '',
    approvalAuthority: project.value.approvalAuthority || '',
    startDate: (project.value.startDate || '').slice(0, 10),
    plannedCompletionDate: (project.value.plannedCompletionDate || '').slice(0, 10),
    possessionDate: (project.value.possessionDate || '').slice(0, 10),
  }
  editingDetails.value = true
}

async function saveDetails() {
  savingDetails.value = true
  detailsError.value = ''
  try {
    const f = detailsForm.value
    project.value = await updateProject(props.id, {
      lookupProjectStatusRecordId: Number(f.lookupProjectStatusRecordId),
      location: f.location.trim(),
      propertyTypeId: f.propertyTypeId ? Number(f.propertyTypeId) : null,
      saleTypeId: f.saleTypeId ? Number(f.saleTypeId) : null,
      listingTypeId: f.listingTypeId ? Number(f.listingTypeId) : null,
      areaExtent: f.areaExtent.trim() || null,
      structureDescription: f.structureDescription.trim() || null,
      numberOfTowers: f.numberOfTowers !== '' ? Number(f.numberOfTowers) : null,
      totalUnits: f.totalUnits !== '' ? Number(f.totalUnits) : null,
      reraNumber: f.reraNumber.trim() || null,
      approvalAuthority: f.approvalAuthority.trim() || null,
      startDate: f.startDate || null,
      plannedCompletionDate: f.plannedCompletionDate || null,
      possessionDate: f.possessionDate || null,
    })
    editingDetails.value = false
  } catch (err) {
    detailsError.value = err.response?.data?.error || 'Could not save changes.'
  } finally {
    savingDetails.value = false
  }
}

function openManagerModal() {
  managerError.value = ''
  managerForm.value = { managerName: '', contactNumber: '', emailId: '', notes: '' }
  showManagerModal.value = true
}

async function onCreateManager() {
  managerError.value = ''
  const f = managerForm.value
  if (!f.managerName.trim() || !f.contactNumber.trim()) {
    managerError.value = 'Name and contact number are required.'
    return
  }
  savingManager.value = true
  try {
    await createManager(props.id, {
      managerName: f.managerName.trim(),
      contactNumber: f.contactNumber.trim(),
      emailId: f.emailId.trim() || undefined,
      notes: f.notes.trim() || undefined,
    })
    showManagerModal.value = false
    managers.value = await listManagers(props.id)
  } catch (err) {
    managerError.value = err.response?.data?.error || 'Could not add manager.'
  } finally {
    savingManager.value = false
  }
}

async function onDeactivateManager(manager) {
  await updateManager(manager.recordId, { isActive: false })
  managers.value = await listManagers(props.id)
}

async function onDeleteManager(manager) {
  if (!confirm(`Remove ${manager.managerName} as a POC for this project?`)) return
  await deleteManager(manager.recordId)
  managers.value = await listManagers(props.id)
}

function openConfigModal() {
  configError.value = ''
  configForm.value = {
    configurationLabel: '', sizeSqFt: '', plotDimensionSqFt: '', startingPriceAmount: '', baseRatePerSqFt: '', notes: '',
  }
  showConfigModal.value = true
}

async function onCreateConfig() {
  configError.value = ''
  const f = configForm.value
  if (!f.configurationLabel.trim()) {
    configError.value = 'Configuration label is required.'
    return
  }
  savingConfig.value = true
  try {
    await createConfiguration(props.id, {
      configurationLabel: f.configurationLabel.trim(),
      sizeSqFt: f.sizeSqFt || undefined,
      plotDimensionSqFt: f.plotDimensionSqFt || undefined,
      startingPriceAmount: f.startingPriceAmount || undefined,
      baseRatePerSqFt: f.baseRatePerSqFt || undefined,
      notes: f.notes.trim() || undefined,
    })
    showConfigModal.value = false
    configurations.value = await listConfigurations(props.id)
  } catch (err) {
    configError.value = err.response?.data?.error || 'Could not add configuration.'
  } finally {
    savingConfig.value = false
  }
}

async function onDeleteConfig(config) {
  if (!confirm(`Remove configuration "${config.configurationLabel}"?`)) return
  await deleteConfiguration(config.recordId)
  configurations.value = await listConfigurations(props.id)
}

function fmtDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

function fmtMoney(value) {
  return value === null || value === undefined ? '—' : `₹${Number(value).toLocaleString('en-IN')}`
}

onMounted(load)
</script>

<template>
  <AppShell :title="project ? project.projectName : 'Project'">
    <div v-if="loading" class="text-slate-400 text-sm">Loading…</div>
    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm font-semibold text-slate-700">Project details</p>
            <button
              v-if="isAdmin && !editingDetails"
              @click="startEditDetails"
              class="text-sm text-brand-600 hover:text-brand-700 font-medium"
            >
              Edit
            </button>
          </div>

          <div v-if="!editingDetails" class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Status</p>
              <Badge v-if="project.statusName" :label="project.statusName" :color="projectStatusColor(project.statusName)" class="mt-0.5" />
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Location</p>
              <p class="text-slate-800 mt-0.5">{{ project.location || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Property type</p>
              <p class="text-slate-800 mt-0.5">{{ project.propertyTypeName || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Sale type</p>
              <p class="text-slate-800 mt-0.5">{{ project.saleTypeName || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Listing type</p>
              <p class="text-slate-800 mt-0.5">{{ project.listingTypeName || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Area extent</p>
              <p class="text-slate-800 mt-0.5">{{ project.areaExtent || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Structure</p>
              <p class="text-slate-800 mt-0.5">{{ project.structureDescription || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Towers / Units</p>
              <p class="text-slate-800 mt-0.5">{{ project.numberOfTowers ?? '—' }} / {{ project.totalUnits ?? '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">RERA number</p>
              <p class="text-slate-800 mt-0.5">{{ project.reraNumber || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Approval authority</p>
              <p class="text-slate-800 mt-0.5">{{ project.approvalAuthority || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Start date</p>
              <p class="text-slate-800 mt-0.5">{{ fmtDate(project.startDate) }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Possession date</p>
              <p class="text-slate-800 mt-0.5">{{ fmtDate(project.possessionDate) }}</p>
            </div>
          </div>

          <div v-else class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Status</label>
              <select v-model="detailsForm.lookupProjectStatusRecordId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                <option v-for="s in statuses" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Location *</label>
              <input v-model="detailsForm.location" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Property type</label>
              <select v-model="detailsForm.propertyTypeId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                <option value="">Not set</option>
                <option v-for="t in propertyTypes" :key="t.recordId" :value="t.recordId">{{ t.recordName }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Sale type</label>
              <select v-model="detailsForm.saleTypeId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                <option value="">Not set</option>
                <option v-for="t in saleTypes" :key="t.recordId" :value="t.recordId">{{ t.recordName }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Listing type</label>
              <select v-model="detailsForm.listingTypeId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                <option value="">Not set</option>
                <option v-for="t in listingTypes" :key="t.recordId" :value="t.recordId">{{ t.recordName }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Area extent</label>
              <input v-model="detailsForm.areaExtent" type="text" placeholder="e.g. 4 Acres" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Structure</label>
              <input v-model="detailsForm.structureDescription" type="text" placeholder="e.g. B+G+17 Floors" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Number of towers</label>
              <input v-model="detailsForm.numberOfTowers" type="number" min="0" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Total units</label>
              <input v-model="detailsForm.totalUnits" type="number" min="0" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">RERA number</label>
              <input v-model="detailsForm.reraNumber" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Approval authority</label>
              <input v-model="detailsForm.approvalAuthority" type="text" placeholder="e.g. BDA, BMRDA" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Start date</label>
              <input v-model="detailsForm.startDate" type="date" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Possession date</label>
              <input v-model="detailsForm.possessionDate" type="date" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <p v-if="detailsError" class="col-span-2 text-sm text-rose-600">{{ detailsError }}</p>
            <div class="col-span-2 flex gap-3">
              <button @click="saveDetails" :disabled="savingDetails" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
                {{ savingDetails ? 'Saving…' : 'Save' }}
              </button>
              <button @click="editingDetails = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
                Cancel
              </button>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm font-semibold text-slate-700">Configurations</p>
            <button v-if="isAdmin" @click="openConfigModal" class="text-sm text-brand-600 hover:text-brand-700 font-medium">
              Add configuration
            </button>
          </div>
          <DataTable :columns="configColumns" :rows="configurations" empty-text="No configurations added yet.">
            <template #cell-sizeSqFt="{ row }">{{ row.sizeSqFt ?? '—' }}</template>
            <template #cell-plotDimensionSqFt="{ row }">{{ row.plotDimensionSqFt ?? '—' }}</template>
            <template #cell-startingPriceAmount="{ row }">{{ fmtMoney(row.startingPriceAmount) }}</template>
            <template #cell-baseRatePerSqFt="{ row }">{{ fmtMoney(row.baseRatePerSqFt) }}</template>
            <template #cell-actions="{ row }">
              <button @click.stop="onDeleteConfig(row)" class="text-xs font-semibold text-rose-600 hover:bg-rose-50 px-2 py-1 rounded-md">
                Remove
              </button>
            </template>
          </DataTable>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-slate-700">Managers (POC)</p>
            <button v-if="canEditManagers" @click="openManagerModal" class="text-sm text-brand-600 hover:text-brand-700 font-medium">
              Add
            </button>
          </div>
          <p v-if="!managers.length" class="text-sm text-slate-400">No manager mapped yet.</p>
          <ul v-else class="space-y-3">
            <li v-for="m in managers" :key="m.recordId" class="border-l-2 border-brand-200 pl-3">
              <p class="text-sm text-slate-800 font-medium">{{ m.managerName }}</p>
              <p class="text-xs text-slate-500">{{ m.contactNumber }}<span v-if="m.emailId"> · {{ m.emailId }}</span></p>
              <p v-if="m.notes" class="text-xs text-slate-400 mt-0.5">{{ m.notes }}</p>
              <div v-if="canEditManagers" class="flex gap-3 mt-1">
                <button @click="onDeactivateManager(m)" class="text-xs text-slate-500 hover:text-slate-700">Deactivate</button>
                <button @click="onDeleteManager(m)" class="text-xs text-rose-600 hover:text-rose-700">Remove</button>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <Modal v-if="showManagerModal" title="Add Manager (POC)" @close="showManagerModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Name</label>
          <input v-model="managerForm.managerName" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Contact number</label>
          <input v-model="managerForm.contactNumber" type="tel" maxlength="10" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Email (optional)</label>
          <input v-model="managerForm.emailId" type="email" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Notes (optional)</label>
          <textarea v-model="managerForm.notes" rows="2" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"></textarea>
        </div>
      </div>
      <p v-if="managerError" class="text-sm text-rose-600 mt-3">{{ managerError }}</p>

      <template #footer>
        <button @click="showManagerModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button @click="onCreateManager" :disabled="savingManager" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
          {{ savingManager ? 'Adding…' : 'Add' }}
        </button>
      </template>
    </Modal>

    <Modal v-if="showConfigModal" title="Add Configuration" @close="showConfigModal = false">
      <div class="grid grid-cols-2 gap-4">
        <div class="col-span-2">
          <label class="block text-sm font-medium text-slate-600 mb-1">Configuration label</label>
          <input v-model="configForm.configurationLabel" type="text" placeholder="e.g. 3 BHK" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Size (sq.ft)</label>
          <input v-model="configForm.sizeSqFt" type="number" step="0.01" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Plot dimension (sq.ft)</label>
          <input v-model="configForm.plotDimensionSqFt" type="number" step="0.01" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Starting price</label>
          <input v-model="configForm.startingPriceAmount" type="number" step="0.01" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Base rate / sq.ft</label>
          <input v-model="configForm.baseRatePerSqFt" type="number" step="0.01" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div class="col-span-2">
          <label class="block text-sm font-medium text-slate-600 mb-1">Notes (optional)</label>
          <textarea v-model="configForm.notes" rows="2" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"></textarea>
        </div>
      </div>
      <p v-if="configError" class="text-sm text-rose-600 mt-3">{{ configError }}</p>

      <template #footer>
        <button @click="showConfigModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button @click="onCreateConfig" :disabled="savingConfig" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
          {{ savingConfig ? 'Adding…' : 'Add' }}
        </button>
      </template>
    </Modal>
  </AppShell>
</template>
