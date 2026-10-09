export const toneFor = (status) => ({
  STOCKOUT_RISK: 'danger', REORDER_NEEDED: 'warning', HEALTHY: 'success', OVERSTOCK_RISK: 'info',
  NEW: 'warning', ACCEPTED: 'success', MODIFIED: 'info', REJECTED: 'danger', EXPIRED: 'neutral',
  RECEIVED: 'success', IN_TRANSIT: 'info', ORDERED: 'info', APPROVED: 'warning', CANCELLED: 'danger', DRAFT: 'neutral',
  SALE: 'danger', RECEIPT: 'success', ADJUSTMENT_IN: 'info', ADJUSTMENT_OUT: 'warning',
}[status] || 'neutral')
