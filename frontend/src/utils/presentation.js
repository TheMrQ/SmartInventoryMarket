const statusLabels = {
  STOCKOUT_RISK: 'Stockout risk',
  REORDER_NEEDED: 'Reorder needed',
  HEALTHY: 'Healthy stock',
  OVERSTOCK_RISK: 'Overstock risk',
  NEW: 'Awaiting review',
  ACCEPTED: 'Accepted',
  MODIFIED: 'Modified',
  REJECTED: 'Rejected',
  EXPIRED: 'Expired',
  DRAFT: 'Draft',
  APPROVED: 'Approved',
  ORDERED: 'Ordered',
  IN_TRANSIT: 'In transit',
  RECEIVED: 'Received',
  CANCELLED: 'Cancelled',
  SALE: 'Sale',
  RECEIPT: 'Goods received',
  ADJUSTMENT_IN: 'Stock added',
  ADJUSTMENT_OUT: 'Stock removed',
  ACTIVE: 'Active',
  INACTIVE: 'Inactive',
}

const m5Sku = /^FOODS_(\d+)_(\d+)$/

export function displayStatus(value) {
  return statusLabels[value] || String(value || '').replaceAll('_', ' ')
}

export function displayProduct(productOrSku) {
  const product = typeof productOrSku === 'string' ? { sku: productOrSku } : productOrSku
  const sku = product?.sku || ''
  const match = sku.match(m5Sku)
  const generatedDemoName = product?.name === `Demo Product — ${sku}`
  const name = match && (!product?.name || generatedDemoName)
    ? `Food Item ${match[1]}-${match[2]}`
    : product?.name || sku || 'Product unavailable'
  return { name, sku }
}

export function formatUnits(value, maximumFractionDigits = 0) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return `${number.toLocaleString(undefined, { maximumFractionDigits })} unit${number === 1 ? '' : 's'}`
}

export function formatForecast(value) {
  const number = Number(value)
  if (!Number.isFinite(number)) return '—'
  return `${number.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })} units`
}

export function formatShortDate(value) {
  if (!value) return '—'
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(`${value}T00:00:00`))
}

// Application datetimes are stored and returned as UTC, including legacy values
// without an offset. Date-only business fields intentionally do not use this parser.
export function parseApplicationUtcDateTime(value) {
  if (typeof value !== 'string' || !value.trim() || /^\d{4}-\d{2}-\d{2}$/.test(value.trim())) return null
  const normalized = value.trim().replace(' ', 'T')
  const hasExplicitOffset = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized)
  const parsed = new Date(hasExplicitOffset ? normalized : `${normalized}Z`)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function formatApplicationDateTime(value, options = {}) {
  const parsed = parseApplicationUtcDateTime(value)
  if (!parsed) return '—'
  const { locale, ...formatOptions } = options
  return new Intl.DateTimeFormat(locale, {
    dateStyle: 'medium',
    timeStyle: 'short',
    ...formatOptions,
  }).format(parsed)
}

export function formatApplicationDate(value, options = {}) {
  const parsed = parseApplicationUtcDateTime(value)
  if (!parsed) return '—'
  const { locale, ...formatOptions } = options
  return new Intl.DateTimeFormat(locale, { dateStyle: 'medium', ...formatOptions }).format(parsed)
}
