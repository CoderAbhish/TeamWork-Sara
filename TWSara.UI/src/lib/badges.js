const STATUS_COLORS = {
  New: 'sky',
  Contacted: 'amber',
  'Site Visit Scheduled': 'violet',
  Negotiation: 'orange',
  Converted: 'emerald',
  Lost: 'rose',
  'On Hold': 'slate',
}

const CATEGORY_COLORS = { Hot: 'rose', Warm: 'amber', Cold: 'sky' }

const PROJECT_STATUS_COLORS = {
  Planning: 'slate',
  'Under Construction': 'amber',
  'Nearing Completion': 'sky',
  Completed: 'emerald',
  'On Hold': 'rose',
}

export function statusColor(name) {
  return STATUS_COLORS[name] || 'slate'
}

export function categoryColor(name) {
  return CATEGORY_COLORS[name] || 'slate'
}

export function projectStatusColor(name) {
  return PROJECT_STATUS_COLORS[name] || 'slate'
}

// Hex equivalents for SVG chart fills (Tailwind class names don't work as
// `fill` attributes). Validated with the dataviz skill's palette validator
// (`validate_palette.js "#F43F5E,#F59E0B,#0EA5E9" --mode light` — all PASS).
const CATEGORY_HEX = { Hot: '#F43F5E', Warm: '#F59E0B', Cold: '#0EA5E9', Uncategorized: '#94A3B8' }

export function categoryHex(name) {
  return CATEGORY_HEX[name] || '#94A3B8'
}
