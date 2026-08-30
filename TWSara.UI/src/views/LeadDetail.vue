<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import { useAuth } from '@/stores/auth'
import { getLead, updateLead, changeLeadStatus, deleteLead, listComments, addComment } from '@/api/leads'
import { listBuilders, listProjects } from '@/api/builders'
import { listTeamMembers, listTeamMemberOptions } from '@/api/teamMembers'
import { getLeadStatuses, getLeadCategories, getLeadSources } from '@/api/lookups'
import { listSiteVisits, createSiteVisit, updateSiteVisit, rescheduleSiteVisit } from '@/api/siteVisits'
import { listFollowUps, logFollowUp } from '@/api/leadFollowUps'
import { listTransferRequests, createTransferRequest } from '@/api/leadTransfers'
import { statusColor, categoryColor, registrationStatus, transferStatusColor } from '@/lib/badges'

// Mirrors the backend's MANUAL_STATUS_TRANSITIONS (lead_controller.py) —
// status can only move along this path; Site Visit Scheduled and
// Negotiation are set automatically by the API, never by hand here.
const MANUAL_STATUS_TRANSITIONS = {
  New: ['Contacted'],
  Contacted: ['Lost', 'On Hold'],
  'Site Visit Scheduled': ['Lost', 'On Hold'],
  Negotiation: ['Converted', 'On Hold', 'Lost'],
}

const VISIT_STATUS_OPTIONS = ['Scheduled', 'Completed', 'Postponed', 'Preponed', 'No-show']

// A small in-app replacement for window.confirm()/alert() — used for the
// site-visit-scheduling confirmation and the registration-blocked notice,
// so both render as a styled dialog with Confirm/Cancel instead of the
// browser's native popup. resolve(true) on Confirm, resolve(false) on
// Cancel; callers that just need to show a message (nothing to decide)
// can ignore the resolved value.
const pendingDialog = ref(null)
function askConfirm(message, options = {}) {
  return new Promise((resolve) => {
    pendingDialog.value = { message, resolve, ...options }
  })
}
function resolvePendingDialog(value) {
  pendingDialog.value?.resolve(value)
  pendingDialog.value = null
}

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
const followUps = ref([])
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

const OFF_TRACK_STATUSES = ['Lost', 'On Hold']
const funnelStatuses = computed(() => statuses.value.filter((s) => !OFF_TRACK_STATUSES.includes(s.recordName)))
const currentFunnelIndex = computed(() =>
  funnelStatuses.value.findIndex((s) => s.recordId === lead.value?.leadStatusId)
)
const offTrackStatus = computed(() =>
  OFF_TRACK_STATUSES.includes(lead.value?.leadStatusName) ? lead.value.leadStatusName : null
)

const registeringLead = ref(false)
const regStatus = computed(() => registrationStatus(lead.value?.isCustLeadRegistered, lead.value?.registrationExpiryDate))

const editingSource = ref(false)
const sourceForm = ref({ leadSourceId: '', leadSourceDetail: '' })
const savingSource = ref(false)

const followUpOverdue = computed(
  () => lead.value?.nextFollowUpOn && new Date(lead.value.nextFollowUpOn) < new Date()
)
const showFollowUpModal = ref(false)
const followUpLogForm = ref({ followUpOn: '', comment: '' })
const followUpSaving = ref(false)
const followUpError = ref('')

const availableStatusTargets = computed(() => {
  const allowedNames = MANUAL_STATUS_TRANSITIONS[lead.value?.leadStatusName] || []
  return statuses.value.filter((s) => allowedNames.includes(s.recordName))
})
const showStatusModal = ref(false)
const statusForm = ref({ toStatusId: '', toStatusName: '', comment: '' })
const statusSaving = ref(false)
const statusError = ref('')

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
  followUps.value = await listFollowUps(props.id)
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

function openStatusModal(target) {
  statusError.value = ''
  statusForm.value = { toStatusId: target.recordId, toStatusName: target.recordName, comment: '' }
  showStatusModal.value = true
}

async function onChangeStatus() {
  statusError.value = ''
  if (!statusForm.value.comment.trim()) {
    statusError.value = 'A comment is required.'
    return
  }
  statusSaving.value = true
  try {
    lead.value = await changeLeadStatus(props.id, statusForm.value.toStatusId, statusForm.value.comment.trim())
    showStatusModal.value = false
    comments.value = await listComments(props.id)
  } catch (err) {
    statusError.value = err.response?.data?.error || 'Could not change status.'
  } finally {
    statusSaving.value = false
  }
}

async function onCategoryChange(event) {
  const value = event.target.value
  lead.value = await updateLead(props.id, { leadCategoryId: value ? Number(value) : null })
}

async function onAssigneeChange(event) {
  const value = event.target.value
  lead.value = await updateLead(props.id, { assignedToUserId: value ? Number(value) : null })
}

async function toggleRegistration() {
  registeringLead.value = true
  try {
    lead.value = await updateLead(props.id, { isCustLeadRegistered: !lead.value.isCustLeadRegistered })
  } catch (err) {
    // The expiry date is always derived from the builder's configured
    // validity window, never entered by hand — if it's missing, the API
    // rejects the request and we surface that as a blocking dialog.
    await askConfirm(err.response?.data?.error || 'Could not update registration.', { title: 'Registration' })
  } finally {
    registeringLead.value = false
  }
}

function startEditSource() {
  sourceForm.value = {
    leadSourceId: lead.value.leadSourceId || '',
    leadSourceDetail: lead.value.leadSourceDetail || '',
  }
  editingSource.value = true
}

async function saveSource() {
  savingSource.value = true
  try {
    const f = sourceForm.value
    lead.value = await updateLead(props.id, {
      leadSourceId: f.leadSourceId ? Number(f.leadSourceId) : null,
      leadSourceDetail: f.leadSourceDetail.trim() || null,
    })
    editingSource.value = false
  } finally {
    savingSource.value = false
  }
}

function openFollowUpModal() {
  followUpError.value = ''
  followUpLogForm.value = { followUpOn: '', comment: '' }
  showFollowUpModal.value = true
}

async function onLogFollowUp() {
  followUpError.value = ''
  if (!followUpLogForm.value.followUpOn || !followUpLogForm.value.comment.trim()) {
    followUpError.value = 'Next follow-up date and a comment are both required.'
    return
  }
  followUpSaving.value = true
  try {
    const result = await logFollowUp(
      props.id, followUpLogForm.value.followUpOn, followUpLogForm.value.comment.trim()
    )
    lead.value = result.lead
    followUps.value = await listFollowUps(props.id)
    showFollowUpModal.value = false
  } catch (err) {
    followUpError.value = err.response?.data?.error || 'Could not log follow-up.'
  } finally {
    followUpSaving.value = false
  }
}

async function onAddVisit() {
  if (!newVisit.value.scheduledOn) return
  const confirmed = await askConfirm(
    `Schedule a site visit for ${fmtDateTime(newVisit.value.scheduledOn)}?`, { title: 'Schedule Site Visit' }
  )
  if (!confirmed) return
  addingVisit.value = true
  try {
    await createSiteVisit(props.id, newVisit.value)
    newVisit.value = { scheduledOn: '', notes: '' }
    // Scheduling a visit can auto-advance the lead status (New/Contacted ->
    // Site Visit Scheduled) — refetch the lead too, not just the visit list,
    // so the flow bar updates without a page refresh.
    const [visits, freshLead] = await Promise.all([listSiteVisits(props.id), getLead(props.id)])
    siteVisits.value = visits
    lead.value = freshLead
  } finally {
    addingVisit.value = false
  }
}

// "Completed" can only be reached on or after the visit's own date — mirrors
// the same rule enforced server-side.
function canMarkCompleted(visit) {
  const visitDate = new Date(visit.scheduledOn)
  visitDate.setHours(0, 0, 0, 0)
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  return today >= visitDate
}

const updatingVisitStatus = ref(new Set())
const visitStatusError = ref('')

async function onVisitStatusChange(visit, newStatus) {
  visitStatusError.value = ''
  updatingVisitStatus.value.add(visit.recordId)
  try {
    await updateSiteVisit(visit.recordId, { status: newStatus })
    // Marking a visit Completed can auto-advance Site Visit Scheduled -> Negotiation.
    const [visits, freshLead] = await Promise.all([listSiteVisits(props.id), getLead(props.id)])
    siteVisits.value = visits
    lead.value = freshLead
  } catch (err) {
    visitStatusError.value = err.response?.data?.error || 'Could not update the visit status.'
  } finally {
    updatingVisitStatus.value.delete(visit.recordId)
  }
}

const showRescheduleModal = ref(false)
const rescheduleTarget = ref(null)
const rescheduleForm = ref({ scheduledOn: '', notes: '' })
const rescheduleSaving = ref(false)
const rescheduleError = ref('')

function openRescheduleModal(visit) {
  rescheduleError.value = ''
  rescheduleTarget.value = visit
  rescheduleForm.value = { scheduledOn: visit.scheduledOn ? visit.scheduledOn.slice(0, 16) : '', notes: '' }
  showRescheduleModal.value = true
}

async function onReschedule() {
  rescheduleError.value = ''
  if (!rescheduleForm.value.scheduledOn || !rescheduleForm.value.notes.trim()) {
    rescheduleError.value = 'A new date/time and a note are both required.'
    return
  }
  rescheduleSaving.value = true
  try {
    const result = await rescheduleSiteVisit(
      rescheduleTarget.value.recordId, rescheduleForm.value.scheduledOn, rescheduleForm.value.notes.trim()
    )
    lead.value = result.lead
    siteVisits.value = await listSiteVisits(props.id)
    showRescheduleModal.value = false
  } catch (err) {
    rescheduleError.value = err.response?.data?.error || 'Could not reschedule the visit.'
  } finally {
    rescheduleSaving.value = false
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
    <template v-else>
      <div class="bg-white rounded-lg border border-slate-200 p-5 mb-6">
        <div class="flex items-center justify-between mb-4">
          <p class="text-sm font-semibold text-slate-700">Lead flow</p>
          <Badge v-if="offTrackStatus" :label="offTrackStatus" :color="statusColor(offTrackStatus)" />
        </div>
        <div class="flex items-center">
          <template v-for="(s, i) in funnelStatuses" :key="s.recordId">
            <div class="flex flex-col items-center" :class="i === 0 ? '' : 'flex-1'">
              <div class="flex items-center w-full">
                <div v-if="i > 0" class="flex-1 h-0.5" :class="i <= currentFunnelIndex ? 'bg-brand-400' : 'bg-slate-200'"></div>
                <div
                  class="w-7 h-7 shrink-0 rounded-full flex items-center justify-center text-xs font-semibold"
                  :class="[
                    offTrackStatus ? 'bg-slate-200 text-slate-400' :
                    i < currentFunnelIndex ? 'bg-brand-500 text-white' :
                    i === currentFunnelIndex ? 'bg-brand-600 text-white ring-4 ring-brand-100' :
                    'bg-slate-100 text-slate-400',
                  ]"
                >
                  <span v-if="!offTrackStatus && i < currentFunnelIndex">✓</span>
                  <span v-else>{{ i + 1 }}</span>
                </div>
              </div>
              <p
                class="text-xs mt-2 text-center px-1"
                :class="!offTrackStatus && i === currentFunnelIndex ? 'text-brand-700 font-semibold' : 'text-slate-500'"
              >
                {{ s.recordName }}
              </p>
            </div>
          </template>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
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
          <p v-if="visitStatusError" class="text-sm text-rose-600 mb-2">{{ visitStatusError }}</p>
          <ul v-if="siteVisits.length" class="space-y-2 mb-4">
            <li v-for="v in siteVisits" :key="v.recordId" class="text-sm border-l-2 border-brand-200 pl-3 flex items-start justify-between gap-3">
              <div>
                <span class="text-slate-800">{{ fmtDateTime(v.scheduledOn) }}</span>
                <p v-if="v.notes" class="text-xs text-slate-400 mt-0.5">{{ v.notes }}</p>
              </div>
              <div class="shrink-0 flex flex-col items-end gap-1">
                <select
                  :value="v.status"
                  :disabled="updatingVisitStatus.has(v.recordId)"
                  @change="onVisitStatusChange(v, $event.target.value)"
                  class="text-xs border border-slate-300 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-brand-400 disabled:opacity-60"
                >
                  <option
                    v-for="opt in VISIT_STATUS_OPTIONS" :key="opt" :value="opt"
                    :disabled="opt === 'Scheduled' || (opt === 'Completed' && !canMarkCompleted(v))"
                  >
                    {{ opt }}
                  </option>
                </select>
                <button
                  @click="openRescheduleModal(v)"
                  :disabled="v.status === 'Scheduled'"
                  class="text-xs font-medium text-slate-500 hover:text-slate-700 disabled:opacity-40 disabled:hover:text-slate-500"
                  :title="v.status === 'Scheduled' ? 'Update the status first — reschedule becomes available once something has been recorded about this visit' : ''"
                >
                  Reschedule
                </button>
              </div>
            </li>
          </ul>
          <p v-else class="text-sm text-slate-400 mb-4">No site visits scheduled yet.</p>
          <p v-if="!lead.isCustLeadRegistered" class="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-md px-3 py-2">
            This lead must be registered with the builder before a visit can be scheduled.
          </p>
          <div v-else class="flex flex-wrap gap-2 items-end">
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
          <Badge v-if="lead.leadStatusName" :label="lead.leadStatusName" :color="statusColor(lead.leadStatusName)" />
          <p v-if="lead.leadStatusName === 'Site Visit Scheduled'" class="text-xs text-slate-400 mt-3">
            Moves to Negotiation automatically once a site visit is marked completed.
          </p>
          <div v-if="availableStatusTargets.length" class="flex flex-wrap gap-2 mt-3">
            <button
              v-for="target in availableStatusTargets" :key="target.recordId"
              @click="openStatusModal(target)"
              class="px-3 py-1.5 rounded-md border border-slate-300 hover:border-brand-400 hover:text-brand-700 text-xs font-medium text-slate-600"
            >
              Mark as {{ target.recordName }}
            </button>
          </div>
          <p v-else-if="lead.leadStatusName !== 'Site Visit Scheduled'" class="text-xs text-slate-400 mt-3">
            No further status change available.
          </p>

          <p class="text-sm font-semibold text-slate-700 mb-3 mt-5">Category</p>
          <select :value="lead.leadCategoryId || ''" @change="onCategoryChange" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 mb-3">
            <option value="">No category</option>
            <option v-for="c in categories" :key="c.recordId" :value="c.recordId">{{ c.recordName }}</option>
          </select>
          <Badge v-if="lead.leadCategoryName" :label="lead.leadCategoryName" :color="categoryColor(lead.leadCategoryName)" />
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <p class="text-sm font-semibold text-slate-700 mb-3">Registration</p>
          <Badge :label="regStatus.label" :color="regStatus.color" />
          <p v-if="lead.isCustLeadRegistered && lead.registrationExpiryDate" class="text-xs text-slate-400 mt-2">
            Expires {{ fmtDate(lead.registrationExpiryDate) }} <span class="text-slate-300">(set from the builder's validity window)</span>
          </p>
          <div>
            <button
              @click="toggleRegistration"
              :disabled="registeringLead"
              class="mt-3 px-3 py-1.5 rounded-md border border-slate-300 hover:border-brand-400 hover:text-brand-700 text-xs font-medium text-slate-600 disabled:opacity-60"
            >
              {{ registeringLead ? 'Saving…' : lead.isCustLeadRegistered ? 'Mark as not registered' : 'Register lead' }}
            </button>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-slate-700">Lead source</p>
            <button v-if="!editingSource" @click="startEditSource" class="text-sm text-brand-600 hover:text-brand-700 font-medium">
              Edit
            </button>
          </div>
          <p v-if="!editingSource" class="text-sm text-slate-800">
            {{ lead.leadSourceName || '—' }}<span v-if="lead.leadSourceDetail"> — {{ lead.leadSourceDetail }}</span>
          </p>
          <div v-else class="space-y-3">
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Source</label>
              <select v-model="sourceForm.leadSourceId" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                <option value="">Not set</option>
                <option v-for="s in leadSources" :key="s.recordId" :value="s.recordId">{{ s.recordName }}</option>
              </select>
            </div>
            <div>
              <label class="block text-xs font-medium text-slate-500 mb-1">Detail (e.g. syndicate name)</label>
              <input v-model="sourceForm.leadSourceDetail" type="text" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div class="flex gap-3">
              <button @click="saveSource" :disabled="savingSource" class="px-3 py-1.5 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
                {{ savingSource ? 'Saving…' : 'Save' }}
              </button>
              <button @click="editingSource = false" class="px-3 py-1.5 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
                Cancel
              </button>
            </div>
          </div>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5">
          <div class="flex items-center justify-between mb-3">
            <p class="text-sm font-semibold text-slate-700">Follow-up</p>
            <button @click="openFollowUpModal" class="text-sm text-brand-600 hover:text-brand-700 font-medium">
              Log follow-up
            </button>
          </div>
          <p class="text-xs text-slate-400 uppercase tracking-wide">Next follow-up</p>
          <p :class="followUpOverdue ? 'text-rose-600 font-medium' : 'text-slate-800'" class="text-sm mb-3">
            {{ fmtDateTime(lead.nextFollowUpOn) }}
          </p>
          <p v-if="!followUps.length" class="text-sm text-slate-400">No follow-ups logged yet.</p>
          <ul v-else class="space-y-2 max-h-48 overflow-y-auto">
            <li v-for="f in followUps" :key="f.recordId" class="text-sm border-l-2 border-brand-200 pl-3">
              <p class="text-slate-800">Next: {{ fmtDateTime(f.followUpOn) }}</p>
              <p class="text-slate-600">{{ f.comment }}</p>
              <p class="text-xs text-slate-400 mt-0.5">{{ f.authorUsername }} · {{ fmtDateTime(f.createdOn) }}</p>
            </li>
          </ul>
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
    </template>

    <Modal v-if="showStatusModal" :title="`Mark as ${statusForm.toStatusName}`" @close="showStatusModal = false">
      <div>
        <label class="block text-sm font-medium text-slate-600 mb-1">Comment (required)</label>
        <textarea
          v-model="statusForm.comment" rows="3" placeholder="Why is the status changing?"
          class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
        ></textarea>
      </div>
      <p v-if="statusError" class="text-sm text-rose-600 mt-3">{{ statusError }}</p>

      <template #footer>
        <button @click="showStatusModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button @click="onChangeStatus" :disabled="statusSaving" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
          {{ statusSaving ? 'Saving…' : 'Confirm' }}
        </button>
      </template>
    </Modal>

    <Modal v-if="showFollowUpModal" title="Log Follow-up" @close="showFollowUpModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Next follow-up date &amp; time</label>
          <input v-model="followUpLogForm.followUpOn" type="datetime-local" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Comment (required)</label>
          <textarea
            v-model="followUpLogForm.comment" rows="3" placeholder="What happened on this touchpoint?"
            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          ></textarea>
        </div>
      </div>
      <p v-if="followUpError" class="text-sm text-rose-600 mt-3">{{ followUpError }}</p>

      <template #footer>
        <button @click="showFollowUpModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button @click="onLogFollowUp" :disabled="followUpSaving" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
          {{ followUpSaving ? 'Saving…' : 'Log' }}
        </button>
      </template>
    </Modal>

    <Modal v-if="showRescheduleModal" title="Reschedule Site Visit" @close="showRescheduleModal = false">
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">New date &amp; time</label>
          <input v-model="rescheduleForm.scheduledOn" type="datetime-local" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-600 mb-1">Comment (required)</label>
          <textarea
            v-model="rescheduleForm.notes" rows="3" placeholder="Why is the visit being rescheduled?"
            class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400"
          ></textarea>
        </div>
        <p class="text-xs text-slate-400">This moves the lead's status back to Site Visit Scheduled.</p>
      </div>
      <p v-if="rescheduleError" class="text-sm text-rose-600 mt-3">{{ rescheduleError }}</p>

      <template #footer>
        <button @click="showRescheduleModal = false" class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100">
          Cancel
        </button>
        <button @click="onReschedule" :disabled="rescheduleSaving" class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold">
          {{ rescheduleSaving ? 'Saving…' : 'Reschedule' }}
        </button>
      </template>
    </Modal>

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

    <ConfirmDialog
      v-if="pendingDialog"
      :title="pendingDialog.title || 'Confirm'"
      :message="pendingDialog.message"
      @confirm="resolvePendingDialog(true)"
      @cancel="resolvePendingDialog(false)"
    />
  </AppShell>
</template>
