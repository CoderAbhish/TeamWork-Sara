<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import { getLead, updateLead, deleteLead, listComments, addComment } from '@/api/leads'
import { listBuilders, listProjects } from '@/api/builders'
import { listTeamMembers } from '@/api/teamMembers'
import { getLeadStatuses, getLeadCategories } from '@/api/lookups'
import { statusColor, categoryColor } from '@/lib/badges'

const props = defineProps({ id: { type: String, required: true } })
const { role } = useAuth()
const router = useRouter()
const isAdmin = computed(() => role.value === 'admin')

const lead = ref(null)
const comments = ref([])
const statuses = ref([])
const categories = ref([])
const teamMembers = ref([])
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

async function load() {
  loading.value = true
  const [l, c, s, cat] = await Promise.all([
    getLead(props.id),
    listComments(props.id),
    getLeadStatuses(),
    getLeadCategories(),
  ])
  lead.value = l
  comments.value = c
  statuses.value = s
  categories.value = cat
  if (isAdmin.value) {
    teamMembers.value = await listTeamMembers()
    builders.value = await listBuilders()
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
          <p class="text-sm font-semibold text-slate-700 mb-3">Assignment</p>
          <select v-if="isAdmin" :value="lead.assignedToUserId || ''" @change="onAssigneeChange" class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
            <option value="">Unassigned</option>
            <option v-for="m in teamMembers" :key="m.recordId" :value="m.recordId">{{ m.username }}</option>
          </select>
          <p v-else class="text-sm text-slate-700">{{ lead.assignedToUsername || 'Unassigned' }}</p>
        </div>

        <div class="bg-white rounded-lg border border-slate-200 p-5 text-xs text-slate-400">
          Created {{ fmtDateTime(lead.createdOn) }}
        </div>
      </div>
    </div>
  </AppShell>
</template>
