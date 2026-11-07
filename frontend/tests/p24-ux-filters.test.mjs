import assert from 'node:assert/strict'
import test from 'node:test'

import { filterInventoryRows, filterPurchaseOrders, filterSupplierMappings, filterSuppliers } from '../src/utils/dataFilters.js'

const products = new Map([[21, { id: 21, sku: 'FOODS_2_005', name: 'Food Item 2-005' }], [23, { id: 23, sku: 'FOODS_2_007', name: 'Food Item 2-007' }]])
const suppliers = new Map([[2, { id: 2, code: 'SIM_M5_CA1_FOODS_V1_SUP_02', name: 'Synthetic Supplier 2', email: 'supply@example.test' }]])

test('inventory filtering matches trimmed case-insensitive SKU and product names', () => {
  const rows = [{ product_id: 21, sku: 'FOODS_2_005', product_name: 'Food Item 2-005', on_hand: 6, incoming_quantity: 8, inventory_position: 14 }, { product_id: 23, sku: 'FOODS_2_007', product_name: 'Food Item 2-007' }]
  assert.deepEqual(filterInventoryRows(rows, products, ' foods_2_005 ').map((row) => row.product_id), [21])
  assert.deepEqual(filterInventoryRows(rows, products, 'item 2-007').map((row) => row.product_id), [23])
  assert.equal(filterInventoryRows(rows, products, 'missing').length, 0)
  assert.equal(filterInventoryRows(rows, products, '').length, 2)
})

test('supplier and mapping filters match supplier code, name and product context', () => {
  const rows = [...suppliers.values()]
  assert.equal(filterSuppliers(rows, 'synthetic supplier 2').length, 1)
  assert.equal(filterSuppliers(rows, 'SUP_02').length, 1)
  assert.equal(filterSuppliers(rows, 'none').length, 0)
  assert.equal(filterSupplierMappings([{ id: 1, supplier_id: 2, product_id: 21 }], products, suppliers, 'FOODS_2_005').length, 1)
})

test('purchase-order search combines PO/supplier search with a supported status filter', () => {
  const rows = [{ id: 4, po_number: 'SIM_M5_CA1_FOODS_V1-INCOMING', supplier_id: 2, status: 'IN_TRANSIT' }, { id: 7, po_number: 'SIM_M5_CA1_FOODS_V1-LINKED-DRAFT', supplier_id: 2, status: 'DRAFT' }]
  assert.deepEqual(filterPurchaseOrders(rows, suppliers, 'PARTIAL', '').map((row) => row.id), [])
  assert.deepEqual(filterPurchaseOrders(rows, suppliers, 'INCOMING', 'IN_TRANSIT').map((row) => row.id), [4])
  assert.deepEqual(filterPurchaseOrders(rows, suppliers, 'synthetic supplier 2', 'DRAFT').map((row) => row.id), [7])
  assert.equal(filterPurchaseOrders(rows, suppliers, 'incoming', 'RECEIVED').length, 0)
})
