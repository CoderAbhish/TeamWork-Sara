const STATUS_COLORS = {
  New: 'sky',
  Contacted: 'amber',
  'Site Visit Scheduled': 'violet',
  Negotiation: 'orange',
  Converted: 'emerald',
  Lost: 'rose',
  'On Hold': 'slate',
}

const CATEGORY_COLORS = { 'New/Fresh': 'sky', Hot: 'rose', Warm: 'amber', Cold: 'violet', Dead: 'slate' }

const PROJECT_STATUS_COLORS = {
  Planning: 'slate',
  'Under Construction': 'amber',
  'Nearing Completion': 'sky',
  Completed: 'emerald',
  'On Hold': 'rose',
}

const TRANSFER_STATUS_COLORS = { pending: 'amber', approved: 'emerald', rejected: 'rose' }

export function statusColor(name) {
  return STATUS_COLORS[name] || 'slate'
}

export function categoryColor(name) {
  return CATEGORY_COLORS[name] || 'slate'
}

export function projectStatusColor(name) {
  return PROJECT_STATUS_COLORS[name] || 'slate'
}

export function transferStatusColor(status) {
  return TRANSFER_STATUS_COLORS[status] || 'slate'
}

// isRegistered/expiryDate -> { label, color } for the lead-registration badge.
export function registrationStatus(isRegistered, expiryDate) {
  if (!isRegistered) return { label: 'Not registered', color: 'slate' }
  if (!expiryDate) return { label: 'Registered', color: 'emerald' }
  const daysLeft = (new Date(expiryDate) - new Date()) / (1000 * 60 * 60 * 24)
  if (daysLeft < 0) return { label: 'Registration expired', color: 'rose' }
  if (daysLeft <= 7) return { label: 'Expiring soon', color: 'amber' }
  return { label: 'Registered', color: 'emerald' }
}

// Hex equivalents for SVG chart fills (Tailwind class names don't work as
// `fill` attributes). Validated with the dataviz skill's palette validator
// (`validate_palette.js "#F43F5E,#F59E0B,#0EA5E9" --mode light` — all PASS).
const CATEGORY_HEX = {
  'New/Fresh': '#0EA5E9',
  Hot: '#F43F5E',
  Warm: '#F59E0B',
  Cold: '#8B5CF6',
  Dead: '#94A3B8',
  Uncategorized: '#94A3B8',
}

export function categoryHex(name) {
  return CATEGORY_HEX[name] || '#94A3B8'
}
