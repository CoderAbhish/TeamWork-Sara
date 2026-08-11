<script setup>
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import { listTeamMembers, setTeamMemberActive, setTeamMemberApproved, getTeamMemberLeads } from '@/api/teamMembers'
import { listComments } from '@/api/leads'
import { statusColor, categoryColor } from '@/lib/badges'

const members = ref([])
const loading = ref(true)
const approving = ref(new Set())

const pendingMembers = computed(() => members.value.filter((m) => !m.isApproved))
const activeMembers = computed(() => members.value.filter((m) => m.isApproved))

const columns = [
  { key: 'username', label: 'Username' },
  { key: 'emailId', label: 'Email' },
  { key: 'contactNumber', label: 'Contact' },
  { key: 'assignedLeadCount', label: 'Assigned leads' },
  { key: 'isActive', label: 'Status' },
]

const selectedMember = ref(null)
const memberLeads = ref([])
const memberLeadsLoading = ref(false)
const expandedLeadId = ref(null)
const expandedComments = ref([])
const expandedLoading = ref(false)

async function load() {
  loading.value = true
  members.value = await listTeamMembers()
  loading.value = false
}

async function toggleActive(member) {
  await setTeamMemberActive(member.recordId, !member.isActive)
  await load()
}

async function approveMember(member) {
  approving.value.add(member.recordId)
  try {
    await setTeamMemberApproved(member.recordId, true)
    await load()
  } finally {
    approving.value.delete(member.recordId)
  }
}

async function openMember(member) {
  selectedMember.value = member
  memberLeadsLoading.value = true
  expandedLeadId.value = null
  memberLeads.value = await getTeamMemberLeads(member.recordId)
  memberLeadsLoading.value = false
}

async function toggleLeadComments(lead) {
  if (expandedLeadId.value === lead.recordId) {
    expandedLeadId.value = null
    return
  }
  expandedLeadId.value = lead.recordId
  expandedLoading.value = true
  expandedComments.value = await listComments(lead.recordId)
  expandedLoading.value = false
}

onMounted(load)
</script>

<template>
  <AppShell title="Team members">
    <div v-if="!loading && pendingMembers.length" class="mb-6 bg-amber-50 border border-amber-200 rounded-lg p-5">
      <p class="text-sm font-semibold text-amber-800 mb-3">Pending approval ({{ pendingMembers.length }})</p>
      <ul class="space-y-2">
        <li
          v-for="m in pendingMembers"
          :key="m.recordId"
          class="flex items-center justify-between bg-white rounded-md border border-amber-100 px-4 py-2.5"
        >
          <div>
            <p class="text-sm font-medium text-slate-800">{{ m.username }}</p>
            <p class="text-xs text-slate-400">{{ m.emailId }} · {{ m.contactNumber || 'no contact number' }}</p>
          </div>
          <button
            @click="approveMember(m)"
            :disabled="approving.has(m.recordId)"
            class="px-3 py-1.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold"
          >
            {{ approving.has(m.recordId) ? 'Approving…' : 'Approve' }}
          </button>
        </li>
      </ul>
    </div>

    <DataTable :columns="columns" :rows="activeMembers" :loading="loading" empty-text="No approved team members yet." @row-click="openMember">
      <template #cell-isActive="{ row }">
        <button @click.stop="toggleActive(row)" type="button">
          <Badge :label="row.isActive ? 'Active' : 'Deactivated'" :color="row.isActive ? 'emerald' : 'slate'" />
        </button>
      </template>
    </DataTable>

    <Modal
      v-if="selectedMember"
      :title="`${selectedMember.username}'s leads`"
      width-class="max-w-2xl"
      @close="selectedMember = null"
    >
      <div v-if="memberLeadsLoading" class="text-sm text-slate-400">Loading…</div>
      <p v-else-if="!memberLeads.length" class="text-sm text-slate-400">No leads assigned yet.</p>
      <ul v-else class="space-y-3">
        <li v-for="lead in memberLeads" :key="lead.recordId" class="border border-slate-200 rounded-md">
          <button
            @click="toggleLeadComments(lead)"
            type="button"
            class="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-slate-50"
          >
            <div>
              <p class="text-sm font-medium text-slate-800">{{ lead.customer.leadName }}</p>
              <p class="text-xs text-slate-400">
                {{ lead.project ? `${lead.project.projectName} — ${lead.project.builderName}` : 'No project yet' }}
              </p>
            </div>
            <div class="flex items-center gap-2">
              <Badge v-if="lead.leadStatusName" :label="lead.leadStatusName" :color="statusColor(lead.leadStatusName)" />
              <Badge v-if="lead.leadCategoryName" :label="lead.leadCategoryName" :color="categoryColor(lead.leadCategoryName)" />
            </div>
          </button>

          <div v-if="expandedLeadId === lead.recordId" class="px-4 pb-3 border-t border-slate-100 pt-3">
            <p class="text-xs font-medium text-slate-500 mb-2">Remarks (view only, newest first)</p>
            <div v-if="expandedLoading" class="text-xs text-slate-400">Loading…</div>
            <p v-else-if="!expandedComments.length" class="text-xs text-slate-400">No remarks yet.</p>
            <ul v-else class="space-y-2">
              <li v-for="c in expandedComments" :key="c.recordId" class="border-l-2 border-brand-200 pl-2">
                <p class="text-sm text-slate-700">{{ c.commentText }}</p>
                <p class="text-xs text-slate-400">{{ new Date(c.createdOn).toLocaleString() }}</p>
              </li>
            </ul>
          </div>
        </li>
      </ul>
    </Modal>
  </AppShell>
</template>
