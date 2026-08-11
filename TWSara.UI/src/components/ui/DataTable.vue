<script setup>
defineProps({
  columns: { type: Array, required: true }, // [{ key, label, sortable }]
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
</script>

<template>
  <div class="border border-slate-200 rounded-lg overflow-hidden bg-white">
    <div class="overflow-x-auto">
      <table class="min-w-full divide-y divide-slate-200 text-sm">
        <thead class="bg-slate-50">
          <tr>
            <th
              v-for="col in columns"
              :key="col.key"
              @click="onHeaderClick(col)"
              class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide"
              :class="col.sortable ? 'cursor-pointer select-none hover:text-brand-600' : ''"
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
            <td :colspan="columns.length" class="px-4 py-8 text-center text-slate-400">Loading…</td>
          </tr>
          <tr v-else-if="!rows.length">
            <td :colspan="columns.length" class="px-4 py-8 text-center text-slate-400">{{ emptyText }}</td>
          </tr>
          <template v-else>
            <tr
              v-for="row in rows"
              :key="row[rowKey]"
              class="hover:bg-slate-50 cursor-pointer"
              @click="emit('row-click', row)"
            >
              <td v-for="col in columns" :key="col.key" class="px-4 py-3 text-slate-700 align-middle">
                <slot :name="`cell-${col.key}`" :row="row">{{ row[col.key] }}</slot>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
