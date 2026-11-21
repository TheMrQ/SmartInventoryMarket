import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const chart = readFileSync(new URL('../src/components/DemandForecastChart.jsx', import.meta.url), 'utf8')
const operations = readFileSync(new URL('../src/pages/OperationalPages.jsx', import.meta.url), 'utf8')
const decisions = readFileSync(new URL('../src/pages/DecisionsPage.jsx', import.meta.url), 'utf8')

test('forecast chart accepts a historical uncertainty range without replacing point forecasts', () => {
  assert.match(chart, /reliability, productId/)
  assert.match(chart, /interval80/)
  assert.match(chart, /Point forecast/)
  assert.match(chart, /80% historical uncertainty interval/)
})

test('reliability panels expose evidence and leave decision formulas intact', () => {
  assert.match(operations, /ForecastReliabilityPanel/)
  assert.match(operations, /not a certainty score/)
  assert.match(decisions, /Decision evidence/)
  assert.match(decisions, /Comparable pre-TEST rolling-fold error/)
  assert.match(decisions, /decision\.reorder_point/)
  assert.match(decisions, /decision\.target_stock/)
  assert.doesNotMatch(operations, /Forecast confidence:/)
})
