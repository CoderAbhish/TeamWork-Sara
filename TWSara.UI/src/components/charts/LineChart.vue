<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  points: { type: Array, required: true }, // [{ label, count }]
  height: { type: Number, default: 220 },
  color: { type: String, default: '#B5672A' }, // brand-500
})

const width = 640
const padding = { top: 20, right: 20, bottom: 28, left: 16 }

const maxCount = computed(() => Math.max(1, ...props.points.map((p) => p.count)))
const chartHeight = computed(() => props.height - padding.top - padding.bottom)
const chartWidth = computed(() => width - padding.left - padding.right)
const stepX = computed(() => chartWidth.value / Math.max(props.points.length - 1, 1))

const coords = computed(() =>
  props.points.map((p, i) => ({
    ...p,
    x: padding.left + i * stepX.value,
    y: padding.top + chartHeight.value - (p.count / maxCount.value) * chartHeight.value,
  }))
)

const linePath = computed(() => coords.value.map((c, i) => `${i === 0 ? 'M' : 'L'}${c.x},${c.y}`).join(' '))
const areaPath = computed(() => {
  if (!coords.value.length) return ''
  const baseline = padding.top + chartHeight.value
  const first = coords.value[0]
  const last = coords.value[coords.value.length - 1]
  return `M${first.x},${baseline} ${coords.value.map((c) => `L${c.x},${c.y}`).join(' ')} L${last.x},${baseline} Z`
})

const hoveredIndex = ref(null)
const hovered = computed(() => (hoveredIndex.value === null ? null : coords.value[hoveredIndex.value]))

function onMove(event) {
  const svg = event.currentTarget
  const rect = svg.getBoundingClientRect()
  const scaleX = width / rect.width
  const pointerX = (event.clientX - rect.left) * scaleX
  let nearest = 0
  let nearestDist = Infinity
  coords.value.forEach((c, i) => {
    const dist = Math.abs(c.x - pointerX)
    if (dist < nearestDist) {
      nearestDist = dist
      nearest = i
    }
  })
  hoveredIndex.value = nearest
}
</script>

<template>
  <div class="chart-container relative">
    <svg
      :viewBox="`0 0 ${width} ${height}`"
      class="w-full"
      :style="{ height: `${height}px` }"
      @mousemove="onMove"
      @mouseleave="hoveredIndex = null"
    >
      <line
        :x1="padding.left" :x2="width - padding.right"
        :y1="padding.top + chartHeight" :y2="padding.top + chartHeight"
        stroke="#E2E8F0" stroke-width="1"
      />

      <path :d="areaPath" :fill="color" opacity="0.1" />
      <path :d="linePath" fill="none" :stroke="color" stroke-width="2" stroke-linejoin="round" stroke-linecap="round" />

      <line
        v-if="hovered"
        :x1="hovered.x" :x2="hovered.x"
        :y1="padding.top" :y2="padding.top + chartHeight"
        stroke="#94A3B8" stroke-width="1" stroke-dasharray="3,3"
      />

      <circle
        v-for="(c, i) in coords" :key="c.label"
        :cx="c.x" :cy="c.y" :r="hoveredIndex === i ? 6 : 4"
        :fill="color" stroke="white" stroke-width="2"
      />

      <text
        v-for="(c, i) in coords" :key="`label-${c.label}`"
        v-show="i === 0 || i === coords.length - 1 || i === hoveredIndex"
        :x="c.x" :y="padding.top + chartHeight + 18"
        :text-anchor="i === 0 ? 'start' : i === coords.length - 1 ? 'end' : 'middle'"
        class="fill-slate-500 text-[11px]"
      >
        {{ c.label }}
      </text>
    </svg>

    <div
      v-if="hovered"
      class="absolute pointer-events-none bg-ink-900 text-white text-xs rounded-md px-2.5 py-1.5 -translate-x-1/2 -translate-y-full shadow-lg"
      :style="{ left: `${(hovered.x / width) * 100}%`, top: `${(hovered.y / height) * 100}%`, marginTop: '-10px' }"
    >
      <span class="font-semibold">{{ hovered.count }}</span> converted · {{ hovered.label }}
    </div>
  </div>
</template>
