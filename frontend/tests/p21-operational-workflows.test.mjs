import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import { canGenerateForecast, createSaleIdempotencyKey, receiptLinesForSubmission } from '../src/utils/operationalWorkflows.js'
import { hasBlockingQueryError } from '../src/utils/queryState.js'

test('secure sale key generation uses the default browser-style Crypto receiver', () => {
  const key = createSaleIdempotencyKey()
  assert.match(key, /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i)
})

test('secure sale key generation retains an injected Crypto receiver', () => {
  const cryptoProvider = {
    calls: 0,
    randomUUID() {
      assert.equal(this, cryptoProvider)
      this.calls += 1
      return `sale-${this.calls}`
    },
  }
  assert.equal(createSaleIdempotencyKey(cryptoProvider), 'sale-1')
  assert.equal(cryptoProvider.calls, 1)
})

test('a sale modal keeps one generated key in its useState initializer for retries', () => {
  const source = readFileSync(new URL('../src/pages/OperationalPages.jsx', import.meta.url), 'utf8')
  assert.match(source, /const \[idempotencyKey\] = useState\(\(\) => createSaleIdempotencyKey\(\)\)/)
  assert.match(source, /api\.recordSale\(data\)/)
  assert.match(source, /idempotency_key: idempotencyKey/)
  assert.match(source, /<Button type="button" className="secondary" onClick=\{onClose\}>Cancel<\/Button>/)
})

test('a sale key fails safely when secure UUID generation is unavailable', () => {
  assert.throws(() => createSaleIdempotencyKey({}), /Secure idempotency-key generation is unavailable/)
})

test('all primary data rows share the inspection marker while action semantics remain explicit', () => {
  const catalog = readFileSync(new URL('../src/pages/CatalogPages.jsx', import.meta.url), 'utf8')
  const operational = readFileSync(new URL('../src/pages/OperationalPages.jsx', import.meta.url), 'utf8')
  const decisions = readFileSync(new URL('../src/pages/DecisionsPage.jsx', import.meta.url), 'utf8')
  const styles = readFileSync(new URL('../src/premium.css', import.meta.url), 'utf8')
  assert.match(catalog, /interaction-row interaction-row-actionable/)
  assert.match(catalog, /interaction-row interaction-row-scan/)
  assert.match(operational, /interaction-row interaction-row-actionable/)
  assert.match(operational, /interaction-row interaction-row-scan/)
  assert.match(decisions, /decision-row interaction-row interaction-row-actionable/)
  assert.match(styles, /\.interaction-row:hover \{ background: #f5f9ff; box-shadow: inset 3px 0 0 var\(--blue-500\); \}/)
  assert.match(styles, /\.interaction-row-actionable \{ cursor: pointer; \}/)
})

test('purchase-order actions keep Manage first and label the stable actions column', () => {
  const source = readFileSync(new URL('../src/pages/OperationalPages.jsx', import.meta.url), 'utf8')
  assert.match(source, /<th className="row-actions">Actions<\/th>/)
  assert.match(source, /row-action-group"><button className="link-button row-action-manage"[\s\S]*?>Manage<\/button>\{next && <button className="link-button row-action-workflow"/)
  assert.match(source, /DRAFT: \['APPROVED', 'Approve order'\]/)
})

test('dashboard retains semantic KPI classes and the workspace has a recovery boundary', () => {
  const dashboard = readFileSync(new URL('../src/pages/DashboardPage.jsx', import.meta.url), 'utf8')
  const app = readFileSync(new URL('../src/App.jsx', import.meta.url), 'utf8')
  assert.match(dashboard, /snapshot-\$\{key\}/)
  assert.match(app, /<WorkspaceErrorBoundary><Shell/)
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
