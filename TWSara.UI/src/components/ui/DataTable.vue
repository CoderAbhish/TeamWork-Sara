<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  // [{ key, label, sortable, priority }] — priority: 'high' (default,
  // always shown) | 'medium' (hidden below md/905px) | 'low' (hidden
  // below lg/1240px). Dropped columns reappear via the expand-row toggle
  // (item 23) below lg, and via the stacked card below sm (item 24).
  columns: { type: Array, required: true },
  rows: { type: Array, required: true },
  sortBy: { type: String, default: '' },
  sortDir: { type: String, default: 'desc' },
  loading: { type: Boolean, default: false },
  emptyText: { type: String, default: 'No records found.' },
  rowKey: { type: String, default: 'recordId' },
})
const emit = defineEmits(['sort', 'row-click'])

function onHeaderClick(col) {
  if (!col.sortable) return
  emit('sort', col.key)
}

function priorityClass(col) {
  if (col.priority === 'low') return 'hidden lg:table-cell'
  if (col.priority === 'medium') return 'hidden md:table-cell'
  return ''
}

const droppableColumns = computed(() => props.columns.filter((c) => c.priority === 'low' || c.priority === 'medium'))
const expandedRows = ref(new Set())
function toggleExpanded(id) {
  const next = new Set(expandedRows.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expandedRows.value = next
}

// Card mode (below sm/600px): the first "real" column becomes the card
// title, select/actions columns (empty label, structural) go in the card's
// header row, and everything else stacks as label: value.
const structuralKeys = ['select', 'actions']
const primaryColumn = computed(() => props.columns.find((c) => !structuralKeys.includes(c.key)))
const cardBodyColumns = computed(() =>
  props.columns.filter((c) => !structuralKeys.includes(c.key) && c.key !== primaryColumn.value?.key && c.label)
)
const hasSelect = computed(() => props.columns.some((c) => c.key === 'select'))
const hasActions = computed(() => props.columns.some((c) => c.key === 'actions'))
</script>

<template>
  <div class="border border-slate-200 rounded-lg overflow-hidden bg-white">
    <!-- Table (sm/600px and up). -->
    <div class="hidden sm:block overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th v-if="droppableColumns.length" class="lg:hidden w-8"></th>
            <th
              v-for="col in columns"
              :key="col.key"
              @click="onHeaderClick(col)"
              class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide"
              :class="[col.sortable ? 'cursor-pointer select-none hover:text-brand-600' : '', priorityClass(col)]"
            >
              <span class="inline-flex items-center gap-1">
                {{ col.label }}
                <span v-if="col.sortable && sortBy === col.key">{{ sortDir === 'asc' ? '▲' : '▼' }}</span>
              </span>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-if="loading">
            <td :colspan="columns.length + 1" class="px-4 py-8 text-center text-slate-400">Loading…</td>
          </tr>
          <tr v-else-if="!rows.length">
            <td :colspan="columns.length + 1" class="px-4 py-8 text-center text-slate-400">{{ emptyText }}</td>
          </tr>
          <template v-else>
            <template v-for="row in rows" :key="row[rowKey]">
              <tr class="hover:bg-slate-50 cursor-pointer" @click="emit('row-click', row)">
                <td v-if="droppableColumns.length" class="lg:hidden px-2 text-center" @click.stop="toggleExpanded(row[rowKey])">
                  <button type="button" class="tap-target inline-flex items-center justify-center text-slate-400 hover:text-slate-600">
                    <svg
                      class="w-4 h-4 transition-transform"
                      :class="expandedRows.has(row[rowKey]) ? 'rotate-90' : ''"
                      fill="none" stroke="currentColor" viewBox="0 0 24 24"
                    >
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                    </svg>
                  </button>
                </td>
                <td v-for="col in columns" :key="col.key" class="px-4 py-3 text-slate-700 align-middle" :class="priorityClass(col)">
                  <slot :name="`cell-${col.key}`" :row="row">{{ row[col.key] }}</slot>
                </td>
              </tr>
              <tr v-if="droppableColumns.length && expandedRows.has(row[rowKey])" class="lg:hidden bg-slate-50">
                <td :colspan="columns.length + 1" class="px-4 py-3">
                  <dl class="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                    <div v-for="col in droppableColumns" :key="col.key" :class="col.priority === 'medium' ? 'md:hidden' : ''">
                      <dt class="text-xs text-slate-400 uppercase tracking-wide">{{ col.label }}</dt>
                      <dd class="text-slate-700 mt-0.5">
                        <slot :name="`cell-${col.key}`" :row="row">{{ row[col.key] }}</slot>
                      </dd>
                    </div>
                  </dl>
                </td>
              </tr>
            </template>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Stacked cards (below sm/600px). -->
    <div class="sm:hidden">
      <div v-if="loading" class="px-4 py-8 text-center text-slate-400 text-sm">Loading…</div>
      <div v-else-if="!rows.length" class="px-4 py-8 text-center text-slate-400 text-sm">{{ emptyText }}</div>
      <ul v-else class="divide-y divide-slate-100">
        <li
          v-for="row in rows" :key="row[rowKey]"
          class="p-4 active:bg-slate-50"
          @click="emit('row-click', row)"
        >
          <div class="flex items-start justify-between gap-2">
            <div class="flex items-center gap-2 min-w-0">
              <span v-if="hasSelect" @click.stop>
                <slot name="cell-select" :row="row" />
              </span>
              <div class="min-w-0 font-medium text-slate-800 text-sm">
                <slot v-if="primaryColumn" :name="`cell-${primaryColumn.key}`" :row="row">{{ row[primaryColumn?.key] }}</slot>
              </div>
            </div>
            <span v-if="hasActions" @click.stop class="shrink-0">
              <slot name="cell-actions" :row="row" />
            </span>
          </div>
          <dl class="mt-2 space-y-1.5">
            <div v-for="col in cardBodyColumns" :key="col.key" class="flex items-baseline justify-between gap-3 text-sm">
              <dt class="text-xs text-slate-400 uppercase tracking-wide shrink-0">{{ col.label }}</dt>
              <dd class="text-slate-700 text-right min-w-0">
                <slot :name="`cell-${col.key}`" :row="row">{{ row[col.key] }}</slot>
              </dd>
            </div>
          </dl>
        </li>
      </ul>
    </div>
  </div>
</template>
