import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import { formatApplicationDateTime, parseApplicationUtcDateTime } from '../src/utils/presentation.js'

test('timezone-naive application datetimes are interpreted as UTC instants', () => {
  assert.equal(parseApplicationUtcDateTime('2026-11-07T15:02:23').toISOString(), '2026-11-07T15:02:23.000Z')
  assert.match(formatApplicationDateTime('2026-11-07T15:02:23', { locale: 'en-US', timeZone: 'Asia/Ho_Chi_Minh', hour12: false }), /Nov 7, 2026.*22:02/)
})

test('explicit UTC and offset application datetimes are not double-converted', () => {
  assert.equal(parseApplicationUtcDateTime('2026-11-07T15:02:23Z').toISOString(), '2026-11-07T15:02:23.000Z')
  assert.equal(parseApplicationUtcDateTime('2026-11-07T22:02:23+07:00').toISOString(), '2026-11-07T15:02:23.000Z')
})

test('date-only, invalid, and missing values do not become UTC instants', () => {
  assert.equal(parseApplicationUtcDateTime('2026-11-07'), null)
  assert.equal(parseApplicationUtcDateTime('not-a-date'), null)
  assert.equal(parseApplicationUtcDateTime(null), null)
  assert.equal(formatApplicationDateTime('2026-11-07'), '—')
})

test('operational UI uses the shared confirmation and UTC presentation helpers', () => {
  const operational = readFileSync(new URL('../src/pages/OperationalPages.jsx', import.meta.url), 'utf8')
  const catalog = readFileSync(new URL('../src/pages/CatalogPages.jsx', import.meta.url), 'utf8')
  const decisions = readFileSync(new URL('../src/pages/DecisionsPage.jsx', import.meta.url), 'utf8')
  const ui = readFileSync(new URL('../src/components/ui.jsx', import.meta.url), 'utf8')
  assert.doesNotMatch(operational, /window\.(confirm|alert)/)
  assert.match(operational, /<ConfirmationDialog/)
  assert.match(operational, /requestReceiptConfirmation/)
  assert.match(operational, /formatApplicationDateTime\(order\.received_at\)/)
  assert.match(catalog, /formatApplicationDateTime\(row\.occurred_at\)/)
  assert.match(catalog, /formatApplicationDate\(row\.updated_at\)/)
  assert.match(decisions, /formatApplicationDateTime\(row\.expires_at\)/)
  assert.match(ui, /export function ConfirmationDialog/)
  assert.match(ui, /pending = false/)
})
