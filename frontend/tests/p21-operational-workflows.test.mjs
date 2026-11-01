import assert from 'node:assert/strict'
import test from 'node:test'

import { canGenerateForecast, createSaleIdempotencyKey, receiptLinesForSubmission } from '../src/utils/operationalWorkflows.js'
import { hasBlockingQueryError } from '../src/utils/queryState.js'

test('a sale modal can retain one caller-supplied idempotency key for retries', () => {
  let calls = 0
  const key = createSaleIdempotencyKey(() => `sale-${++calls}`)
  assert.equal(key, 'sale-1')
  assert.equal(key, 'sale-1')
  assert.equal(calls, 1)
})

test('forecast generation is enabled only for the selected eligible product', () => {
  assert.equal(canGenerateForecast(7, { eligible: true }), true)
  assert.equal(canGenerateForecast(7, { eligible: false }), false)
  assert.equal(canGenerateForecast('', { eligible: true }), false)
})

test('receipt submission retains only valid positive quantities within remaining stock', () => {
  const items = [{ id: 1, ordered_quantity: 5, received_quantity: 2 }, { id: 2, ordered_quantity: 3, received_quantity: 0 }]
  assert.deepEqual(receiptLinesForSubmission(items, { 1: '3', 2: '0' }), [{ purchase_order_item_id: 1, quantity: 3 }])
  assert.throws(() => receiptLinesForSubmission(items, { 1: '4' }), /remaining quantity/)
  assert.throws(() => receiptLinesForSubmission(items, { 1: '0', 2: '0' }), /at least one/)
})

test('a background refetch error keeps cached operational data and open input mounted', () => {
  assert.equal(hasBlockingQueryError([{ isError: true, data: [{ id: 1 }] }]), false)
  assert.equal(hasBlockingQueryError([{ isError: true, data: undefined }]), true)
})
