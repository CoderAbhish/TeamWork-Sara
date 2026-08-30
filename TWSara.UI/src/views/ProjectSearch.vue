<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Badge from '@/components/ui/Badge.vue'
import { listBuilders, searchProjects } from '@/api/builders'
import { getProjectStatuses, getPropertyTypes, getSaleTypes, getListingTypes } from '@/api/lookups'
import { projectStatusColor } from '@/lib/badges'

const router = useRouter()

const projects = ref([])
const total = ref(0)
const loading = ref(true)

const builders = ref([])
const statuses = ref([])
const propertyTypes = ref([])
const saleTypes = ref([])
const listingTypes = ref([])

const search = ref('')
const location = ref('')
const builderId = ref('')
const propertyTypeId = ref('')
const saleTypeId = ref('')
const listingTypeId = ref('')
const statusId = ref('')
const minPrice = ref('')
const maxPrice = ref('')
const page = ref(1)
const pageSize = 20

const columns = [
  { key: 'projectName', label: 'Project', priority: 'high' },
  { key: 'builderName', label: 'Builder', priority: 'high' },
  { key: 'location', label: 'Location', priority: 'high' },
  { key: 'propertyTypeName', label: 'Property type', priority: 'medium' },
  { key: 'listingTypeName', label: 'Listing', priority: 'medium' },
  { key: 'statusName', label: 'Status', priority: 'low' },
  { key: 'priceRange', label: 'Starting price', priority: 'high' },
]

function currentFilterParams() {
  const params = { page: page.value, pageSize }
  if (search.value) params.search = search.value
  if (location.value) params.location = location.value
  if (builderId.value) params.builderId = builderId.value
  if (propertyTypeId.value) params.propertyTypeId = propertyTypeId.value
  if (saleTypeId.value) params.saleTypeId = saleTypeId.value
  if (listingTypeId.value) params.listingTypeId = listingTypeId.value
  if (statusId.value) params.lookupProjectStatusRecordId = statusId.value
  if (minPrice.value) params.minPrice = minPrice.value
  if (maxPrice.value) params.maxPrice = maxPrice.value
  return params
}

async function load() {
  loading.value = true
  const result = await searchProjects(currentFilterParams())
  projects.value = result.items
  total.value = result.total
  loading.value = false
}

function onFilterChange() {
  page.value = 1
  load()
}

function fmtMoney(value) {
  return value === null || value === undefined ? null : `₹${Number(value).toLocaleString('en-IN')}`
}

function fmtPriceRange(row) {
  const min = fmtMoney(row.minStartingPrice)
  const max = fmtMoney(row.maxStartingPrice)
  if (!min && !max) return '—'
  if (min === max) return min
  return `${min} – ${max}`
}

async function loadFilters() {
  const [b, s, pt, st, lt] = await Promise.all([
    listBuilders(), getProjectStatuses(), getPropertyTypes(), getSaleTypes(), getListingTypes(),
  ])
  builders.value = b
  statuses.value = s
  propertyTypes.value = pt
  saleTypes.value = st
  listingTypes.value = lt
}

onMounted(async () => {
  await loadFilters()
  await load()
})
</script>

<template>
  <AppShell title="Find Projects">
    <div class="bg-white rounded-lg border border-slate-200 p-4 mb-4 flex flex-wrap gap-3 items-end">
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Search</label>
        <input
          v-model="search" @keyup.enter="onFilterChange" type="text" placeholder="Project or builder name"
          class="px-3 py-1.5 border border-slate-300 rounded-md text-sm w-48 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Location</label>
        <input
          v-model="location" @keyup.enter="onFilterChange" type="text" placeholder="e.g. Koramangala"
          class="px-3 py-1.5 border border-slate-300 rounded-md text-sm w-40 focus:outline-none focus:ring-2 focus:ring-brand-400"
        />
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Builder</label>
        <select v-model="builderId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="b in builders" :key="b.recordId" :value="b.recordId">{{ b.builderName }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Property type</label>
        <select v-model="propertyTypeId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="t in propertyTypes" :key="t.recordId" :value="t.recordId">{{ t.recordName }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Sale type</label>
        <select v-model="saleTypeId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="t in saleTypes" :key="t.recordId" :value="t.recordId">{{ t.recordName }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Listing type</label>
        <select v-model="listingTypeId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="t in listingTypes" :key="t.recordId" :value="t.recordId">{{ t.recordName }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Status</label>
        <select v-model="statusId" @change="onFilterChange" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
          <option value="">All</option>
          <option v-for="s in statuses" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
        </select>
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Min price</label>
        <input v-model="minPrice" @keyup.enter="onFilterChange" type="number" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm w-28 focus:outline-none focus:ring-2 focus:ring-brand-400" />
      </div>
      <div>
        <label class="block text-xs font-medium text-slate-500 mb-1">Max price</label>
        <input v-model="maxPrice" @keyup.enter="onFilterChange" type="number" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm w-28 focus:outline-none focus:ring-2 focus:ring-brand-400" />
      </div>
      <button @click="onFilterChange" class="px-3 py-1.5 rounded-md bg-ink-900 hover:bg-ink-800 text-white text-sm font-medium">
        Apply
      </button>
    </div>

    <DataTable
      :columns="columns"
      :rows="projects"
      :loading="loading"
      empty-text="No projects match these filters."
      @row-click="(row) => router.push(`/projects/${row.recordId}`)"
    >
      <template #cell-propertyTypeName="{ row }">{{ row.propertyTypeName || '—' }}</template>
      <template #cell-listingTypeName="{ row }">{{ row.listingTypeName || '—' }}</template>
      <template #cell-statusName="{ row }">
        <Badge v-if="row.statusName" :label="row.statusName" :color="projectStatusColor(row.statusName)" />
        <span v-else class="text-slate-300 text-xs">—</span>
      </template>
      <template #cell-priceRange="{ row }">{{ fmtPriceRange(row) }}</template>
    </DataTable>

    <div v-if="total > pageSize" class="flex justify-between items-center mt-4 text-sm text-slate-500">
      <span>{{ total }} project(s) — page {{ page }} of {{ Math.ceil(total / pageSize) }}</span>
      <div class="flex gap-2">
        <button :disabled="page <= 1" @click="page--; load()" class="px-3 py-1.5 rounded-md border border-slate-300 disabled:opacity-40">
          Previous
        </button>
        <button :disabled="page >= Math.ceil(total / pageSize)" @click="page++; load()" class="px-3 py-1.5 rounded-md border border-slate-300 disabled:opacity-40">
          Next
        </button>
      </div>
    </div>
  </AppShell>
</template>
