import assert from 'node:assert/strict'
import test from 'node:test'
import {
  demandPatternFor,
  displayForecastModel,
  recommendationReliabilityFor,
  zeroSalesExplanation,
} from '../src/utils/reliabilityPresentation.js'

test('demand-pattern labels explain the existing sparsity bands in manager language', () => {
  assert.equal(demandPatternFor({ sparsity_band: '0-25% zero' }).label, 'Stable')
  assert.equal(demandPatternFor({ sparsity_band: '25-50% zero' }).label, 'Variable')
  assert.equal(demandPatternFor({ sparsity_band: '50-75% zero' }).label, 'Irregular')
  assert.equal(demandPatternFor({ sparsity_band: '75-100% zero' }).label, 'Highly intermittent')
  assert.match(zeroSalesExplanation({ zero_rate_56: .625 }), /63%/)
})

test('reliability explanation is derived from existing evidence level and demand pattern', () => {
  const moderate = recommendationReliabilityFor({ evidence_level: 'MODERATE', sparsity_band: '50-75% zero' })
  const limited = recommendationReliabilityFor({ evidence_level: 'LIMITED', sparsity_band: '75-100% zero' })
  assert.equal(moderate.level, 'Moderate')
  assert.match(moderate.explanation, /irregular sales/)
  assert.equal(limited.level, 'Limited')
  assert.match(limited.explanation, /highly intermittent/)
  assert.equal(displayForecastModel('XGBOOST_V1'), 'XGBoost V1')
})
