<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import { getLead, updateLead, deleteLead, listComments, addComment } from '@/api/leads'
import { listBuilders, listProjects } from '@/api/builders'
import { listTeamMembers, listTeamMemberOptions } from '@/api/teamMembers'
import { getLeadStatuses, getLeadCategories, getLeadSources } from '@/api/lookups'
import { listSiteVisits, createSiteVisit } from '@/api/siteVisits'
import { listTransferRequests, createTransferRequest } from '@/api/leadTransfers'
import { statusColor, categoryColor, registrationStatus, transferStatusColor } from '@/lib/badges'

const props = defineProps({ id: { type: String, required: true } })
const { role, user } = useAuth()
const router = useRouter()
const isAdmin = computed(() => role.value === 'admin')

const lead = ref(null)
const comments = ref([])
const statuses = ref([])
const categories = ref([])
const leadSources = ref([])
const teamMembers = ref([])
const siteVisits = ref([])
const myPendingTransfer = ref(null)
const loading = ref(true)

const editingDetails = ref(false)
const detailsForm = ref({ leadName: '', contactNumber: '', alternateNumber: '', leadLocation: '' })
const savingDetails = ref(false)
const detailsError = ref('')

const builders = ref([])
const projectOptions = ref([])
const projectForm = ref({ builderId: '', projectId: '' })

async function onProjectBuilderChange() {
  projectForm.value.projectId = ''
  projectOptions.value = projectForm.value.builderId ? await listProjects(projectForm.value.builderId) : []
}

const newComment = ref('')
const postingComment = ref(false)

const editingRegistration = ref(false)
const registrationForm = ref({ isCustLeadRegistered: false, registrationExpiryDate: '' })
const savingRegistration = ref(false)
const regStatus = computed(() => registrationStatus(lead.value?.isCustLeadRegistered, lead.value?.registrationExpiryDate))

const editingFollowUp = ref(false)
const followUpForm = ref({ leadSourceId: '', leadSourceDetail: '', nextFollowUpOn: '' })
const savingFollowUp = ref(false)
const followUpOverdue = computed(
  () => lead.value?.nextFollowUpOn && new Date(lead.value.nextFollowUpOn) < new Date()
)

const newVisit = ref({ scheduledOn: '', notes: '' })
const addingVisit = ref(false)

const showTransferModal = ref(false)
const transferForm = ref({ toUserId: '', comment: '' })
const transferSaving = ref(false)
const transferError = ref('')

async function load() {
  loading.value = true
  const [l, c, s, cat, src] = await Promise.all([
    getLead(props.id),
    listComments(props.id),
    getLeadStatuses(),
    getLeadCategories(),
    getLeadSources(),
  ])
  lead.value = l
  comments.value = c
  statuses.value = s
  categories.value = cat
  leadSources.value = src
  siteVisits.value = await listSiteVisits(props.id)
  if (isAdmin.value) {
    teamMembers.value = await listTeamMembers()
    builders.value = await listBuilders()
  } else {
    teamMembers.value = await listTeamMemberOptions()
    const requests = await listTransferRequests()
    myPendingTransfer.value =
      requests.find((r) => r.custProjectId === Number(props.id) && r.status === 'pending') || null
  }
  loading.value = false
}

async function startEditDetails() {
  detailsForm.value = { ...lead.value.customer }
  detailsError.value = ''
  if (lead.value.project) {
    projectForm.value = { builderId: lead.value.project.builderRecordId, projectId: lead.value.project.recordId }
    projectOptions.value = await listProjects(lead.value.project.builderRecordId)
  } else {
    projectForm.value = { builderId: '', projectId: '' }
    projectOptions.value = []
  }
  editingDetails.value = true
}

async function saveDetails() {
  savingDetails.value = true
  detailsError.value = ''
  try {
    lead.value = await updateLead(props.id, {
      customer: detailsForm.value,
      projectId: projectForm.value.projectId ? Number(projectForm.value.projectId) : null,
    })
    editingDetails.value = false
  } catch (err) {
    detailsError.value = err.response?.data?.error || 'Could not save changes.'
  } finally {
    savingDetails.value = false
  }
}

async function onStatusChange(event) {
  const value = event.target.value
  lead.value = await updateLead(props.id, { leadStatusId: value ? Number(value) : null })
}

async function onCategoryChange(event) {
  const value = event.target.value
  lead.value = await updateLead(props.id, { leadCategoryId: value ? Number(value) : null })
}

async function onAssigneeChange(event) {
  const value = event.target.value
  lead.value = await updateLead(props.id, { assignedToUserId: value ? Number(value) : null })
}

function startEditRegistration() {
  registrationForm.value = {
    isCustLeadRegistered: lead.value.isCustLeadRegistered,
    registrationExpiryDate: (lead.value.registrationExpiryDate || '').slice(0, 10),
  }
  editingRegistration.value = true
}

async function saveRegistration() {
  savingRegistration.value = true
  try {
    lead.value = await updateLead(props.id, {
      isCustLeadRegistered: registrationForm.value.isCustLeadRegistered,
      registrationExpiryDate: registrationForm.value.registrationExpiryDate || null,
    })
    editingRegistration.value = false
  } finally {
    savingRegistration.value = false
  }
}

function startEditFollowUp() {
  followUpForm.value = {
    leadSourceId: lead.value.leadSourceId || '',
    leadSourceDetail: lead.value.leadSourceDetail || '',
    nextFollowUpOn: lead.value.nextFollowUpOn ? lead.value.nextFollowUpOn.slice(0, 16) : '',
  }
  editingFollowUp.value = true
}

async function saveFollowUp() {
  savingFollowUp.value = true
  try {
    const f = followUpForm.value
    lead.value = await updateLead(props.id, {
      leadSourceId: f.leadSourceId ? Number(f.leadSourceId) : null,
      leadSourceDetail: f.leadSourceDetail.trim() || null,
      nextFollowUpOn: f.nextFollowUpOn || null,
    })
    editingFollowUp.value = false
  } finally {
    savingFollowUp.value = false
  }
}

async function onAddVisit() {
  if (!newVisit.value.scheduledOn) return
  addingVisit.value = true
  try {
    await createSiteVisit(props.id, newVisit.value)
    newVisit.value = { scheduledOn: '', notes: '' }
    siteVisits.value = await listSiteVisits(props.id)
  } finally {
    addingVisit.value = false
  }
}

function openTransferModal() {
  transferError.value = ''
  transferForm.value = { toUserId: '', comment: '' }
  showTransferModal.value = true
}

async function onRequestTransfer() {
  transferError.value = ''
  if (!transferForm.value.toUserId || !transferForm.value.comment.trim()) {
    transferError.value = 'Choose a team member and add a comment.'
    return
  }
  transferSaving.value = true
  try {
    myPendingTransfer.value = await createTransferRequest(
      Number(props.id),
      Number(transferForm.value.toUserId),
      transferForm.value.comment.trim()
    )
    showTransferModal.value = false
  } catch (err) {
    transferError.value = err.response?.data?.error || 'Could not submit transfer request.'
  } finally {
    transferSaving.value = false
  }
}

async function onAddComment() {
  const text = newComment.value.trim()
  if (!text) return
  postingComment.value = true
  try {
    await addComment(props.id, text)
    newComment.value = ''
    comments.value = await listComments(props.id)
  } finally {
    postingComment.value = false
  }
}

async function onDelete() {
  if (!confirm('Delete this lead? This cannot be undone.')) return
  await deleteLead(props.id)
  router.push('/leads')
}

function fmtDateTime(value) {
  return value ? new Date(value).toLocaleString() : '—'
}

function fmtDate(value) {
  return value ? new Date(value).toLocaleDateString() : '—'
}

onMounted(load)
</script>

<template>
  <AppShell :title="lead ? lead.customer.leadName : 'Lead'">
    <template #actions>
      <button
        v-if="isAdmin"
        @click="onDelete"
        class="px-3 py-2 rounded-md text-sm font-medium text-rose-600 hover:bg-rose-50"
      >
        Delete lead
      </button>
    </template>

    <div v-if="loading" class="text-slate-400 text-sm">Loading…</div>
    <div v-else class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div class="lg:col-span-2 space-y-6">
        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm font-semibold text-slate-700">Lead details</p>
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
              <p class="text-xs text-slate-400 uppercase tracking-wide">Name</p>
              <p class="text-slate-800 mt-0.5">{{ lead.customer.leadName }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Contact</p>
              <p class="text-slate-800 mt-0.5">{{ lead.customer.contactNumber }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Alternate number</p>
              <p class="text-slate-800 mt-0.5">{{ lead.customer.alternateNumber || '—' }}</p>
            </div>
            <div>
              <p class="text-xs text-slate-400 uppercase tracking-wide">Location</p>
              <p class="text-slate-800 mt-0.5">{{ lead.customer.leadLocation || '—' }}</p>
            </div>
            <div class="col-span-2">
              <p class="text-xs text-slate-400 uppercase tracking-wide">Project</p>
              <p v-if="lead.project" class="text-slate-800 mt-0.5">{{ lead.project.projectName }} — {{ lead.project.builderName }}</p>
              <p v-else class="text-slate-400 mt-0.5 italic">No project selected yet</p>
            </div>
          </div>

          <div v-else class="grid grid-cols-2 gap-4">
            <div class="col-span-2">
              <label class="block text-xs font-medium text-slate-500 mb-1">Name</label>
              <input v-model="detailsForm.leadName" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Contact</label>
              <input v-model="detailsForm.contactNumber" type="tel" maxlength="10" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Alternate number</label>
              <input v-model="detailsForm.alternateNumber" type="tel" maxlength="10" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div class="col-span-2">
              <label class="block text-xs font-medium text-slate-500 mb-1">Location</label>
              <input v-model="detailsForm.leadLocation" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Builder</label>
              <select v-model="projectForm.builderId" @change="onProjectBuilderChange" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                <option value="">No builder</option>
                <option v-for="b in builders" :key="b.recordId" :value="b.recordId">{{ b.builderName }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Project</label>
              <select v-model="projectForm.projectId" :disabled="!projectForm.builderId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:bg-slate-50">
                <option value="">No project</option>
                <option v-for="p in projectOptions" :key="p.recordId" :value="p.recordId">{{ p.projectName }}</option>
              </select>
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

        <div v-if="lead.relatedLeads.length" class="bg-white rounded-lg border border-slate-200 p-5">
          <p class="text-sm font-semibold text-slate-700 mb-3">
            Related leads <span class="text-xs font-normal text-slate-400">(same contact, other projects)</span>
          </p>
          <ul class="space-y-2">
            <li
              v-for="r in lead.relatedLeads" :key="r.recordId"
              @click="router.push(`/leads/${r.recordId}`)"
              class="flex items-center justify-between text-sm px-3 py-2 rounded-md hover:bg-slate-50 cursor-pointer"
            >
              <span class="text-slate-700">{{ r.projectName || 'No project yet' }}<span v-if="r.builderName"> — {{ r.builderName }}</span></span>
              <span class="text-xs text-slate-400">{{ r.statusName || '—' }} · {{ r.assignedToUsername || 'Unassigned' }}</span>
            </li>
          </ul>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-4">
            <p class="text-sm font-semibold text-slate-700">Site visits</p>
          </div>
          <ul v-if="siteVisits.length" class="space-y-2 mb-4">
            <li v-for="v in siteVisits" :key="v.recordId" class="text-sm border-l-2 border-brand-200 pl-3">
              <span class="text-slate-800">{{ fmtDateTime(v.scheduledOn) }}</span>
              <span class="text-xs text-slate-400 ml-2">{{ v.status }}</span>
              <p v-if="v.notes" class="text-xs text-slate-400 mt-0.5">{{ v.notes }}</p>
            </li>
          </ul>
          <p v-else class="text-sm text-slate-400 mb-4">No site visits scheduled yet.</p>
          <div class="flex flex-wrap gap-2 items-end">
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Schedule a visit</label>
              <input v-model="newVisit.scheduledOn" type="datetime-local" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <input v-model="newVisit.notes" type="text" placeholder="Notes (optional)" class="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 flex-1 min-w-[10rem]" />
            <button @click="onAddVisit" :disabled="addingVisit || !newVisit.scheduledOn" class="px-3 py-1.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
              {{ addingVisit ? 'Adding…' : 'Add' }}
            </button>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <p class="text-sm font-semibold text-slate-700 mb-4">
            Comments
            <span v-if="!isAdmin" class="text-xs font-normal text-slate-400">(newest first)</span>
            <span v-else class="text-xs font-normal text-slate-400">(view only)</span>
          </p>

          <div v-if="!isAdmin" class="mb-4">
            <textarea
              v-model="newComment"
              rows="2"
              placeholder="Add a remark about this lead…"
              class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
            ></textarea>
            <button
              @click="onAddComment"
              :disabled="postingComment || !newComment.trim()"
              class="mt-2 px-4 py-1.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold"
            >
              {{ postingComment ? 'Posting…' : 'Post comment' }}
            </button>
          </div>

          <p v-if="!comments.length" class="text-sm text-slate-400">No comments yet.</p>
          <ul v-else class="space-y-3">
            <li v-for="c in comments" :key="c.recordId" class="border-l-2 border-brand-200 pl-3">
              <p class="text-sm text-slate-700">{{ c.commentText }}</p>
              <p class="text-xs text-slate-400 mt-0.5">{{ c.authorUsername }} · {{ fmtDateTime(c.createdOn) }}</p>
            </li>
          </ul>
        </div>
      </div>

      <div class="space-y-6">
        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <p class="text-sm font-semibold text-slate-700 mb-3">Status</p>
          <select :value="lead.leadStatusId || ''" @change="onStatusChange" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 mb-3">
            <option value="">No status</option>
            <option v-for="s in statuses" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
          </select>
          <Badge v-if="lead.leadStatusName" :label="lead.leadStatusName" :color="statusColor(lead.leadStatusName)" />

          <p class="text-sm font-semibold text-slate-700 mb-3 mt-5">Category</p>
          <select :value="lead.leadCategoryId || ''" @change="onCategoryChange" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 mb-3">
            <option value="">No category</option>
            <option v-for="c in categories" :key="c.recordId" :value="c.recordId">{{ c.recordName }}</option>
          </select>
          <Badge v-if="lead.leadCategoryName" :label="lead.leadCategoryName" :color="categoryColor(lead.leadCategoryName)" />
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-slate-700">Registration</p>
            <button v-if="!editingRegistration" @click="startEditRegistration" class="text-sm text-brand-600 hover:text-brand-700 font-medium">
              Edit
            </button>
          </div>
          <div v-if="!editingRegistration">
            <Badge :label="regStatus.label" :color="regStatus.color" />
            <p v-if="lead.isCustLeadRegistered && lead.registrationExpiryDate" class="text-xs text-slate-400 mt-2">
              Expires {{ fmtDate(lead.registrationExpiryDate) }}
            </p>
          </div>
          <div v-else class="space-y-3">
            <label class="flex items-center gap-2 text-sm text-slate-700">
              <input type="checkbox" v-model="registrationForm.isCustLeadRegistered" class="rounded border-slate-300" />
              Registered with builder
            </label>
            <div v-if="registrationForm.isCustLeadRegistered">
              <label class="block text-xs font-medium text-slate-500 mb-1">Expiry date</label>
              <input v-model="registrationForm.registrationExpiryDate" type="date" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div class="flex gap-3">
              <button @click="saveRegistration" :disabled="savingRegistration" class="px-3 py-1.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
                {{ savingRegistration ? 'Saving…' : 'Save' }}
              </button>
              <button @click="editingRegistration = false" class="px-3 py-1.5 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
                Cancel
              </button>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-slate-700">Source &amp; follow-up</p>
            <button v-if="!editingFollowUp" @click="startEditFollowUp" class="text-sm text-brand-600 hover:text-brand-700 font-medium">
              Edit
            </button>
          </div>
          <div v-if="!editingFollowUp" class="space-y-2 text-sm">
            <p><span class="text-xs text-slate-400 uppercase tracking-wide block">Source</span>
              {{ lead.leadSourceName || '—' }}<span v-if="lead.leadSourceDetail"> — {{ lead.leadSourceDetail }}</span>
            </p>
            <p>
              <span class="text-xs text-slate-400 uppercase tracking-wide block">Next follow-up</span>
              <span :class="followUpOverdue ? 'text-rose-600 font-medium' : 'text-slate-800'">{{ fmtDateTime(lead.nextFollowUpOn) }}</span>
            </p>
          </div>
          <div v-else class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Lead source</label>
              <select v-model="followUpForm.leadSourceId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                <option value="">Not set</option>
                <option v-for="s in leadSources" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Source detail (e.g. syndicate name)</label>
              <input v-model="followUpForm.leadSourceDetail" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Next follow-up</label>
              <input v-model="followUpForm.nextFollowUpOn" type="datetime-local" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div class="flex gap-3">
              <button @click="saveFollowUp" :disabled="savingFollowUp" class="px-3 py-1.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
                {{ savingFollowUp ? 'Saving…' : 'Save' }}
              </button>
              <button @click="editingFollowUp = false" class="px-3 py-1.5 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
                Cancel
              </button>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <p class="text-sm font-semibold text-slate-700 mb-3">Assignment</p>
          <select v-if="isAdmin" :value="lead.assignedToUserId || ''" @change="onAssigneeChange" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
            <option value="">Unassigned</option>
            <option v-for="m in teamMembers" :key="m.recordId" :value="m.recordId">{{ m.username }}</option>
          </select>
          <p v-else class="text-sm text-slate-700">{{ lead.assignedToUsername || 'Unassigned' }}</p>

          <template v-if="!isAdmin">
            <div v-if="myPendingTransfer" class="mt-3">
              <Badge label="Transfer pending" :color="transferStatusColor('pending')" />
              <p class="text-xs text-slate-400 mt-1">Requested to {{ myPendingTransfer.toUsername }}</p>
            </div>
            <button v-else @click="openTransferModal" class="mt-3 text-sm text-brand-600 hover:text-brand-700 font-medium">
              Request transfer
            </button>
          </template>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5 text-xs text-slate-400">
          Created {{ fmtDateTime(lead.createdOn) }}
        </div>
      </div>
    </div>

    <Modal v-if="showTransferModal" title="Request Lead Transfer" @close="showTransferModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Transfer to</label>
          <select v-model="transferForm.toUserId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
            <option value="">Select team member</option>
            <option v-for="m in teamMembers.filter((tm) => tm.recordId !== user?.recordId)" :key="m.recordId" :value="m.recordId">
              {{ m.username }}
            </option>
          </select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Comment</label>
          <textarea v-model="transferForm.comment" rows="3" placeholder="Why should this lead move?" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"></textarea>
        </div>
      </div>
      <p v-if="transferError" class="text-sm text-rose-600 mt-3">{{ transferError }}</p>

      <template #footer>
        <button @click="showTransferModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button @click="onRequestTransfer" :disabled="transferSaving" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
          {{ transferSaving ? 'Submitting…' : 'Submit' }}
        </button>
      </template>
    </Modal>
  </AppShell>
</template>
