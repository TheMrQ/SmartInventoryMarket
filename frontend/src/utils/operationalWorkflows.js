export function createSaleIdempotencyKey(cryptoProvider = globalThis.crypto) {
  if (typeof cryptoProvider === 'function') return cryptoProvider()
  if (typeof cryptoProvider?.randomUUID !== 'function') throw new Error('Secure idempotency-key generation is unavailable.')
  return cryptoProvider.randomUUID()
}

export function canGenerateForecast(productId, eligibility) {
  return Boolean(productId && eligibility?.eligible)
}

export function receiptLinesForSubmission(items, receiptValues) {
  const lines = items.map((item) => ({
    purchase_order_item_id: item.id,
    quantity: Number(receiptValues[item.id]) || 0,
  })).filter((line) => line.quantity > 0)
  if (!lines.length) throw new Error('Enter at least one receipt quantity.')
  for (const line of lines) {
    const item = items.find((candidate) => candidate.id === line.purchase_order_item_id)
    if (!Number.isInteger(line.quantity) || line.quantity < 1 || line.quantity > item.ordered_quantity - item.received_quantity) {
      throw new Error('Receipt cannot exceed the remaining quantity.')
    }
  }
  return lines
}
