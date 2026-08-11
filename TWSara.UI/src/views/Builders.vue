<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/layout/AppShell.vue'
import DataTable from '@/components/ui/DataTable.vue'
import Modal from '@/components/ui/Modal.vue'
import Badge from '@/components/ui/Badge.vue'
import { useAuth } from '@/stores/auth'
import { listBuilders, createBuilder, updateBuilder } from '@/api/builders'

const { role } = useAuth()
const router = useRouter()

const builders = ref([])
const loading = ref(true)
const showInactive = ref(false)
const showCreateModal = ref(false)
const newBuilderName = ref('')
const creating = ref(false)
const error = ref('')

const columns = [
  { key: 'builderName', label: 'Builder' },
  { key: 'projectCount', label: 'Projects' },
  { key: 'isActive', label: 'Status' },
]

async function load() {
  loading.value = true
  builders.value = await listBuilders(showInactive.value)
  loading.value = false
}

async function onCreate() {
  error.value = ''
  const name = newBuilderName.value.trim()
  if (!name) return
  creating.value = true
  try {
    await createBuilder(name)
    showCreateModal.value = false
    newBuilderName.value = ''
    await load()
  } catch (err) {
    error.value = err.response?.data?.error || 'Could not create builder.'
  } finally {
    creating.value = false
  }
}

async function toggleActive(builder) {
  await updateBuilder(builder.recordId, { isActive: !builder.isActive })
  await load()
}

onMounted(load)
</script>

<template>
  <AppShell title="Builders">
    <template #actions>
      <label v-if="role === 'admin'" class="flex items-center gap-2 text-sm text-slate-500 mr-2">
        <input type="checkbox" v-model="showInactive" @change="load" class="rounded border-slate-300" />
        Show inactive
      </label>
      <button
        v-if="role === 'admin'"
        @click="showCreateModal = true"
        class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 text-white text-sm font-semibold transition-colors"
      >
        New Builder
      </button>
    </template>

    <DataTable
      :columns="columns"
      :rows="builders"
      :loading="loading"
      empty-text="No builders yet."
      @row-click="(row) => router.push(`/builders/${row.recordId}`)"
    >
      <template #cell-isActive="{ row }">
        <button
          v-if="role === 'admin'"
          @click.stop="toggleActive(row)"
          type="button"
        >
          <Badge :label="row.isActive ? 'Active' : 'Inactive'" :color="row.isActive ? 'emerald' : 'slate'" />
        </button>
        <Badge v-else :label="row.isActive ? 'Active' : 'Inactive'" :color="row.isActive ? 'emerald' : 'slate'" />
      </template>
    </DataTable>

    <Modal v-if="showCreateModal" title="New Builder" @close="showCreateModal = false">
      <label class="block text-sm font-medium text-slate-600 mb-1">Builder name</label>
      <input
        v-model="newBuilderName"
        type="text"
        class="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-brand-400"
        @keyup.enter="onCreate"
      />
      <p v-if="error" class="text-sm text-rose-600 mt-2">{{ error }}</p>

      <template #footer>
        <button
          @click="showCreateModal = false"
          class="px-4 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100"
        >
          Cancel
        </button>
        <button
          @click="onCreate"
          :disabled="creating"
          class="px-4 py-2 rounded-md bg-brand-500 hover:bg-brand-600 disabled:opacity-60 text-white text-sm font-semibold"
        >
          {{ creating ? 'Creating…' : 'Create' }}
        </button>
      </template>
    </Modal>
  </AppShell>
</template>
