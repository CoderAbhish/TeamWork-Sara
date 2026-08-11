<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import Badge from '@/components/ui/Badge.vue'
import KpiTile from '@/components/ui/KpiTile.vue'
import LineChart from '@/components/charts/LineChart.vue'
import BarChart from '@/components/charts/BarChart.vue'
import { useAuth } from '@/stores/auth'
import { listLeads } from '@/api/leads'
import { listBuilders } from '@/api/builders'
import { listTeamMembers } from '@/api/teamMembers'
import { getConvertedOverTime, getLeadsByCategory, getHotLeads } from '@/api/analytics'
import { statusColor, categoryColor, categoryHex } from '@/lib/badges'

const { role } = useAuth()
const router = useRouter()

const totalLeads = ref(0)
const builderCount = ref(0)
const teamMemberCount = ref(0)
const loading = ref(true)

const period = ref('month')
const periods = [
  { key: 'week', label: 'Week' },
  { key: 'month', label: 'Month' },
  { key: 'quarter', label: 'Quarter' },
  { key: 'year', label: 'Year' },
]
const convertedPoints = ref([])
const chartLoading = ref(false)

const categoryBreakdown = ref([])
const hotLeads = ref([])

async function loadPeriodChart() {
  chartLoading.value = true
  const buckets = await getConvertedOverTime(period.value)
  convertedPoints.value = buckets.map((b) => ({ label: b.label, count: b.count }))
  chartLoading.value = false
}

async function load() {
  loading.value = true
  const [leadsResult, category, hot] = await Promise.all([
    listLeads({ pageSize: 1 }),
    getLeadsByCategory(),
    getHotLeads(),
  ])
  totalLeads.value = leadsResult.total
  categoryBreakdown.value = category.map((c) => ({ ...c, color: categoryHex(c.name) }))
  hotLeads.value = hot

  if (role.value === 'admin') {
    const [builders, members] = await Promise.all([listBuilders(true), listTeamMembers()])
    builderCount.value = builders.length
    teamMemberCount.value = members.length
  }

  await loadPeriodChart()
  loading.value = false
}

function fmtDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

onMounted(load)
</script>

<template>
  <AppShell title="Dashboard">
    <div v-if="loading" class="text-slate-400 text-sm">Loading…</div>
    <div v-else class="space-y-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <KpiTile :label="role === 'admin' ? 'Total leads' : 'My leads'" :value="totalLeads" />
        <template v-if="role === 'admin'">
          <KpiTile label="Builders" :value="builderCount" />
          <KpiTile label="Team members" :value="teamMemberCount" />
        </template>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div class="lg:col-span-2 bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm font-semibold text-slate-700">
              {{ role === 'admin' ? 'Leads converted' : 'My leads converted' }}
            </p>
            <div class="flex bg-slate-100 rounded-md p-0.5">
              <button
                v-for="p in periods"
                :key="p.key"
                @click="period = p.key; loadPeriodChart()"
                class="px-3 py-1 rounded text-xs font-medium transition-colors"
                :class="period === p.key ? 'bg-white text-ink-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'"
              >
                {{ p.label }}
              </button>
            </div>
          </div>
          <p v-if="chartLoading" class="text-sm text-slate-400">Loading…</p>
          <LineChart v-else :points="convertedPoints" />
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <p class="text-sm font-semibold text-slate-700 mb-4">
            {{ role === 'admin' ? 'Leads by category' : 'My leads by category' }}
          </p>
          <p v-if="!categoryBreakdown.length" class="text-sm text-slate-400">No leads yet.</p>
          <BarChart v-else :items="categoryBreakdown" :height="200" />
        </div>
      </div>

      <div class="bg-white rounded-lg border border-slate-200 p-5">
        <p class="text-sm font-semibold text-slate-700 mb-1">Hot leads to focus on first</p>
        <p class="text-xs text-slate-400 mb-4">Oldest unresolved hot leads, longest-waiting first.</p>
        <p v-if="!hotLeads.length" class="text-sm text-slate-400">No hot leads waiting — nice work.</p>
        <ul v-else class="divide-y divide-slate-100">
          <li
            v-for="lead in hotLeads"
            :key="lead.recordId"
            @click="router.push(`/leads/${lead.recordId}`)"
            class="flex items-center justify-between py-3 cursor-pointer hover:bg-slate-50 px-2 -mx-2 rounded-md"
          >
            <div>
              <p class="text-sm font-medium text-slate-800">{{ lead.customer.leadName }}</p>
              <p class="text-xs text-slate-400">
                {{ lead.project ? `${lead.project.projectName} — ${lead.project.builderName}` : 'No project yet' }}
                · created {{ fmtDate(lead.createdOn) }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <Badge v-if="lead.leadStatusName" :label="lead.leadStatusName" :color="statusColor(lead.leadStatusName)" />
              <Badge label="Hot" :color="categoryColor('Hot')" />
            </div>
          </li>
        </ul>
      </div>
    </div>
  </AppShell>
</template>
