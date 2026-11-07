import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import { fulfillmentForPurchaseOrder, inventoryContextForProduct } from '../src/utils/purchaseOrderWorkspace.js'

test('purchase-order fulfillment aggregates actual line quantities', () => {
  assert.deepEqual(
    fulfillmentForPurchaseOrder([
      { ordered_quantity: 8, received_quantity: 6 },
      { ordered_quantity: 4, received_quantity: 1 },
    ]),
    { ordered: 12, received: 7, remaining: 5, lineCount: 2, percentReceived: 58 },
  )
})

test('inventory context keeps the backend-reported inventory position', () => {
  const rows = new Map([[22, { product_id: 22, on_hand: 9, incoming_quantity: 2, inventory_position: 11 }]])
  assert.deepEqual(inventoryContextForProduct(rows, 22), { onHand: 9, incoming: 2, inventoryPosition: 11 })
  assert.equal(inventoryContextForProduct(rows, 999), null)
})

test('purchase-order workspace uses product identity, linked recommendation, and status-specific controls', () => {
  const source = readFileSync(new URL('../src/pages/OperationalPages.jsx', import.meta.url), 'utf8')
  assert.match(source, /displayProduct\(\s*productsById\.get\(item\.product_id\),?\s*\)/)
  assert.doesNotMatch(source, /Product #\{item\.product_id\}/)
  assert.match(source, /order\.reorder_recommendation_id/)
  assert.match(source, /Linked/)
  assert.match(source, /order\.status === "IN_TRANSIT" && remaining > 0/)
  assert.match(source, /Confirm receipt/)
  assert.match(source, /order\.status === "RECEIVED"/)
  assert.match(source, /order\.status === "DRAFT"/)
  assert.match(source, /InventoryContext/)
})

test('shared result count remains a compact summary surface rather than a pill', () => {
  const styles = readFileSync(new URL('../src/premium.css', import.meta.url), 'utf8')
  assert.match(styles, /\.result-count \{ border:1px solid #bfdbfe; border-radius:11px; background:#eff6ff/)
  assert.doesNotMatch(styles, /\.result-count \{[^}]*border-radius:999px/)
})
