<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  items: { type: Array, required: true }, // [{ name, count, color }]
  height: { type: Number, default: 220 },
})

const width = 480
const padding = { top: 28, right: 16, bottom: 28, left: 16 }
const barWidth = 24
const radius = 4

const containerRef = ref(null)
const containerWidth = ref(480)
let resizeObserver = null

onMounted(() => {
  if (!containerRef.value) return
  resizeObserver = new ResizeObserver((entries) => {
    containerWidth.value = entries[0].contentRect.width
  })
  resizeObserver.observe(containerRef.value)
})
onUnmounted(() => resizeObserver?.disconnect())

// Below this rendered width there isn't room for a value label over every
// bar plus a full category name without them colliding — thin both out.
const compact = computed(() => containerWidth.value < 380)
function labelFor(name) {
  return compact.value && name.length > 4 ? `${name.slice(0, 3)}…` : name
}

const maxCount = computed(() => Math.max(1, ...props.items.map((i) => i.count)))
const chartHeight = computed(() => props.height - padding.top - padding.bottom)
const slotWidth = computed(() => (width - padding.left - padding.right) / Math.max(props.items.length, 1))

const bars = computed(() =>
  props.items.map((item, i) => {
    const barHeight = maxCount.value ? (item.count / maxCount.value) * chartHeight.value : 0
    const slotX = padding.left + i * slotWidth.value
    const x = slotX + (slotWidth.value - barWidth) / 2
    const y = padding.top + (chartHeight.value - barHeight)
    return { ...item, x, y, barHeight, cx: slotX + slotWidth.value / 2 }
  })
)

function roundedTopRectPath(x, y, w, h) {
  if (h <= 0) return ''
  const r = Math.min(radius, h, w / 2)
  return `M${x},${y + h} L${x},${y + r} Q${x},${y} ${x + r},${y} L${x + w - r},${y} Q${x + w},${y} ${x + w},${y + r} L${x + w},${y + h} Z`
}

const hovered = ref(null)
const tooltipStyle = ref({})

function onHover(bar, event) {
  hovered.value = bar
  const rect = event.currentTarget.closest('.chart-container').getBoundingClientRect()
  tooltipStyle.value = {
    left: `${event.clientX - rect.left}px`,
    top: `${event.clientY - rect.top}px`,
  }
}
</script>

<template>
  <div ref="containerRef" class="chart-container relative">
    <svg :viewBox="`0 0 ${width} ${height}`" class="w-full" :style="{ height: `${height}px` }">
      <line
        :x1="padding.left" :x2="width - padding.right"
        :y1="padding.top + chartHeight" :y2="padding.top + chartHeight"
        stroke="#E2E8F0" stroke-width="1"
      />
      <g v-for="bar in bars" :key="bar.name">
        <path
          :d="roundedTopRectPath(bar.x, bar.y, barWidth, bar.barHeight)"
          :fill="bar.color"
          class="cursor-pointer transition-opacity"
          :class="hovered && hovered.name !== bar.name ? 'opacity-60' : ''"
          @mousemove="onHover(bar, $event)"
          @mouseleave="hovered = null"
        />
        <text
          v-if="bar.count > 0 && (!compact || hovered?.name === bar.name)"
          :x="bar.cx" :y="bar.y - 8"
          text-anchor="middle"
          class="fill-slate-700 text-[13px] font-semibold"
        >
          {{ bar.count }}
        </text>
        <text
          :x="bar.cx" :y="padding.top + chartHeight + 18"
          text-anchor="middle"
          class="fill-slate-500 text-[11px]"
        >
          {{ labelFor(bar.name) }}
        </text>
      </g>
    </svg>

    <div
      v-if="hovered"
      class="absolute pointer-events-none bg-ink-900 text-white text-xs rounded-md px-2.5 py-1.5 -translate-x-1/2 -translate-y-full shadow-lg"
      :style="{ left: tooltipStyle.left, top: `calc(${tooltipStyle.top} - 8px)` }"
    >
      <span class="font-semibold">{{ hovered.count }}</span> {{ hovered.name }}
    </div>
  </div>
</template>
