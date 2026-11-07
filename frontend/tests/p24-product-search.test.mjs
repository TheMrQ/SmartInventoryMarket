import assert from 'node:assert/strict'
import test from 'node:test'

import { normalizedProductSearch, PRODUCT_SEARCH_DEBOUNCE_MS, productSearchParams, productSearchPresentation } from '../src/utils/productSearch.js'

test('product search debounces a normalized SKU/name request for 300ms', () => {
  assert.equal(PRODUCT_SEARCH_DEBOUNCE_MS, 300)
  assert.equal(normalizedProductSearch('  FOODS_1  '), 'FOODS_1')
  assert.deepEqual(productSearchParams('FOODS_1'), { limit: 100, search: 'FOODS_1' })
  assert.deepEqual(productSearchParams(''), { limit: 100 })
})

test('product search preserves the mounted table while a newer query fetches', () => {
  assert.deepEqual(productSearchPresentation({ hasProducts: true, isFetching: true, isError: false }), { keepTableMounted: true, showUpdating: true, showNoResults: false })
  assert.deepEqual(productSearchPresentation({ hasProducts: true, isFetching: false, isError: false }), { keepTableMounted: true, showUpdating: false, showNoResults: true })
})
