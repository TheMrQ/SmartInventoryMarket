import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const chart = readFileSync(new URL('../src/components/DemandForecastChart.jsx', import.meta.url), 'utf8')
const evidence = readFileSync(new URL('../src/components/ReliabilityEvidence.jsx', import.meta.url), 'utf8')
const operations = readFileSync(new URL('../src/pages/OperationalPages.jsx', import.meta.url), 'utf8')
const decisions = readFileSync(new URL('../src/pages/DecisionsPage.jsx', import.meta.url), 'utf8')

test('forecast chart uses manager-friendly range and estimate labels without replacing point forecasts', () => {
  assert.match(chart, /interval80/)
  assert.match(chart, /Forecast estimate/)
  assert.match(chart, /Typical range — 80% historical interval/)
})

test('manager view leads with plain-language reliability evidence and keeps technical traceability collapsed', () => {
  assert.match(evidence, /Recommendation reliability/)
  assert.match(evidence, /Typical forecast error/)
  assert.match(evidence, /Demand pattern/)
  assert.match(evidence, /Forecast model/)
  assert.match(evidence, /Based on historical data through/)
  assert.match(evidence, /View technical details/)
  assert.match(evidence, /Run #\{evidence\.forecast_run_id\}/)
  assert.ok(evidence.indexOf('Run #{evidence.forecast_run_id}') > evidence.indexOf('<details'))
  assert.doesNotMatch(evidence, /Historical backtest MAE/)
  assert.doesNotMatch(evidence, /Forecast confidence:/)
})

test('forecasts and inventory insights use the same evidence component while formula fields remain intact', () => {
  assert.match(operations, /ReliabilityEvidence evidence=\{evidence\} context="forecast"/)
  assert.match(decisions, /ReliabilityEvidence evidence=\{reliability\.data\} context="recommendation"/)
  assert.match(decisions, /decision\.reorder_point/)
  assert.match(decisions, /decision\.target_stock/)
  assert.match(decisions, /decision\.recommended_quantity/)
})
