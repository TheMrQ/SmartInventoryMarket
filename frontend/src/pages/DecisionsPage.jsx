import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, ClipboardList, HelpCircle, Pencil, X } from 'lucide-react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'
import { api } from '../api/client'
import { DemandForecastChart } from '../components/DemandForecastChart'
import { Badge, Button, Empty, Loading, Modal, Tooltip } from '../components/ui'
import { displayProduct, displayStatus, formatForecast, formatUnits } from '../utils/presentation'
import { toneFor } from '../utils/status'

const invalidate = (client) => ['decisions', 'recommendations', 'inventory'].forEach((key) => client.invalidateQueries({ queryKey: [key] }))
const fail = (error) => toast.error(error.message || 'Operation failed')
const RiskOption = ({ value }) => <option value={value}>{displayStatus(value)}</option>

export default function DecisionsPage() {
  const client = useQueryClient()
  const [tab, setTab] = useState('decisions')
  const [risk, setRisk] = useState('')
  const [search, setSearch] = useState('')
  const [review, setReview] = useState(null)
  const [selectedDecision, setSelectedDecision] = useState(null)
  const decisions = useQuery({ queryKey: ['decisions', risk, search], queryFn: () => api.decisions({ ...(risk && { risk_status: risk }), ...(search && { search }) }) })
  const recommendations = useQuery({ queryKey: ['recommendations'], queryFn: api.recommendations })
  const products = useQuery({ queryKey: ['products'], queryFn: () => api.products({ limit: 100 }) })
  const generate = useMutation({
    mutationFn: api.generateRecommendation,
    onSuccess: (data) => { invalidate(client); toast.success(data.recommendation ? 'Restock recommendation created' : 'No restock is needed for this snapshot') },
    onError: fail,
  })
  if ([decisions, recommendations, products].some((query) => query.isLoading)) return <Loading />
  const productById = new Map((products.data || []).map((product) => [product.id, product]))
  return <div className="stack">
    <header className="page-heading"><div><p className="eyebrow">Decision support</p><h2>Inventory Insights</h2><p>Use saved demand forecasts, supplier delivery time, and current stock together to make a restocking decision.</p></div></header>
    <div className="tabs"><button className={tab === 'decisions' ? 'active' : ''} onClick={() => setTab('decisions')}><ClipboardList size={16}/>Inventory Insights</button><button className={tab === 'recommendations' ? 'active' : ''} onClick={() => setTab('recommendations')}>Restock Recommendations <span>{recommendations.data?.filter((item) => item.status === 'NEW').length || 0}</span></button></div>
    {tab === 'decisions' ? <>
      <div className="toolbar"><label>Stock status<select value={risk} onChange={(event) => setRisk(event.target.value)}><option value="">All statuses</option><RiskOption value="STOCKOUT_RISK"/><RiskOption value="REORDER_NEEDED"/><RiskOption value="HEALTHY"/><RiskOption value="OVERSTOCK_RISK"/></select></label><label>Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="SKU or product"/></label></div>
      <article className="panel table-wrap"><table><thead><tr><th>Product</th><th>Available / incoming</th><th>Supplier</th><th><Tooltip label="Estimated supplier delivery time"><span>Lead time <HelpCircle size={13}/></span></Tooltip></th><th>Forecast demand</th><th><Tooltip label="Extra inventory kept as a buffer against forecast error and demand variation."><span>Safety stock <HelpCircle size={13}/></span></Tooltip></th><th>Stock status</th><th>Recommended order</th><th /></tr></thead><tbody>{decisions.data?.map((item) => <tr key={item.product_id} className="decision-row" onClick={() => setSelectedDecision(item)}><td><strong>{displayProduct(item).name}</strong><small>{item.sku}</small></td><td>{formatUnits(item.on_hand)}<small>{formatUnits(item.incoming_quantity)} incoming · {formatUnits(item.inventory_position)} position</small></td><td>{item.supplier_name}<small>Selected supplier</small></td><td>{item.lead_time_days} days</td><td>{formatForecast(item.expected_lead_time_demand)}</td><td>{formatUnits(item.safety_stock)}</td><td><Badge tone={toneFor(item.risk_status)}>{displayStatus(item.risk_status)}</Badge></td><td><strong className="recommended-quantity">{formatUnits(item.recommended_quantity)}</strong></td><td><button className="link-button" onClick={(event) => { event.stopPropagation(); setSelectedDecision(item) }}>View insight</button></td></tr>)}</tbody></table>{!decisions.data?.length && <Empty title="Inventory insights aren't available yet">Add a supplier and <Link to="/forecasts">generate a forecast first</Link> to calculate stock risk.</Empty>}</article>
    </> : <Recommendations rows={recommendations.data || []} productById={productById} onReview={setReview}/>}
    <p className="callout">A restock recommendation is always human-reviewed. Accepting, adjusting, or rejecting it does not change inventory or automatically create a purchase order.</p>
    {selectedDecision && <DecisionDetail decision={selectedDecision} product={productById.get(selectedDecision.product_id)} onClose={() => setSelectedDecision(null)} onGenerate={() => generate.mutate(selectedDecision.product_id)} generating={generate.isPending}/>}
    {review && <ReviewModal recommendation={review} product={productById.get(review.product_id)} onClose={() => setReview(null)} client={client}/>}
  </div>
}

function DecisionDetail({ decision, product, onClose, onGenerate, generating }) {
  const forecast = useQuery({ queryKey: ['latestForecast', String(decision.product_id)], queryFn: () => api.latestForecast(decision.product_id), retry: false })
  const display = displayProduct(product || decision)
  const target = Math.max(Number(decision.target_stock) || 0, 1)
  const position = Math.max(Number(decision.inventory_position) || 0, 0)
  const recommended = Math.max(Number(decision.recommended_quantity) || 0, 0)
  const positionPercent = Math.min(100, (position / target) * 100)
  const gapPercent = Math.min(100 - positionPercent, (recommended / target) * 100)
  return <Modal title="Inventory insight" className="decision-detail" onClose={onClose}>
    <div className="decision-detail-heading"><div><p className="eyebrow">Selected product</p><h3>{display.name}</h3><p>{display.sku}</p></div><Badge tone={toneFor(decision.risk_status)}>{displayStatus(decision.risk_status)}</Badge></div>
    <section className="decision-recommendation"><span>Recommended order</span><strong>{formatUnits(recommended)}</strong><p>Target stock already includes the safety-stock buffer.</p></section>
    <div className="decision-sections">
      <section><p className="eyebrow">Current stock</p><DecisionValue label="Available stock" value={formatUnits(decision.on_hand)}/><DecisionValue label="Incoming stock" value={formatUnits(decision.incoming_quantity)}/><DecisionValue label="Inventory position" value={formatUnits(decision.inventory_position)} emphasis/></section>
      <section><p className="eyebrow">Demand</p><DecisionValue label="Forecast demand during supplier lead time" value={formatForecast(decision.expected_lead_time_demand)}/><DecisionValue label="Supplier lead time" value={`${decision.lead_time_days} days`}/><DecisionValue label="Safety stock" value={formatUnits(decision.safety_stock)} helper="Extra inventory kept as a buffer against forecast error and demand variation."/></section>
      <section><p className="eyebrow">Decision</p><DecisionValue label="Reorder point" value={formatUnits(decision.reorder_point)}/><DecisionValue label="Target stock" value={formatUnits(decision.target_stock)}/><DecisionValue label="Recommended order" value={formatUnits(recommended)} emphasis/></section>
    </div>
    <section className="stock-coverage"><header><div><p className="eyebrow">Stock coverage</p><h3>Target stock versus current position</h3></div></header><div className="coverage-track" aria-label={`Target stock ${formatUnits(decision.target_stock)}; current position ${formatUnits(decision.inventory_position)}; recommended order gap ${formatUnits(recommended)}`}><span className="coverage-position" style={{ width: `${positionPercent}%` }}/><span className="coverage-gap" style={{ left: `${positionPercent}%`, width: `${gapPercent}%` }}/></div><div className="coverage-labels"><span><b>Target</b>{formatUnits(decision.target_stock)}</span><span><b>Current position</b>{formatUnits(decision.inventory_position)}</span><span><b>Gap / recommended order</b>{formatUnits(recommended)}</span></div></section>
    <details className="calculation-details"><summary>How was this calculated?</summary><div><p><strong>Inventory position</strong> = Available stock + Incoming stock</p><p><strong>Reorder point</strong> = Lead-time forecast + Safety stock</p><p><strong>Recommended order</strong> = Target stock − Inventory position (minimum 0)</p></div></details>
    {forecast.isLoading ? <Loading /> : forecast.data ? <article className="panel decision-chart"><DemandForecastChart forecast={forecast.data} productId={decision.product_id} horizon={forecast.data.horizon_days} productName={display.name} compact/></article> : <section className="callout decision-no-forecast"><strong>Generate forecast first</strong><span>A saved forecast is needed to show demand context for this decision.</span><Link className="button compact" to={`/forecasts?product=${decision.product_id}&horizon=28`} onClick={onClose}>Open Forecasts</Link></section>}
    {recommended > 0 && <footer><Button loading={generating} onClick={onGenerate}>Create restock recommendation</Button></footer>}
  </Modal>
}

function DecisionValue({ label, value, emphasis, helper }) { return <div className={emphasis ? 'decision-value emphasis' : 'decision-value'}><span>{label}{helper && <Tooltip label={helper}><HelpCircle size={13}/></Tooltip>}</span><strong>{value}</strong></div> }

function Recommendations({ rows, productById, onReview }) {
  return <article className="panel table-wrap"><table><thead><tr><th>Product</th><th>Status</th><th>Suggested order</th><th>Approved quantity</th><th>Supplier</th><th>Expires</th><th /></tr></thead><tbody>{rows.map((row) => { const product = displayProduct(productById.get(row.product_id) || { sku: `Product ${row.product_id}` }); return <tr key={row.id}><td><strong>{product.name}</strong><small>{product.sku}</small></td><td><Badge tone={toneFor(row.status)}>{displayStatus(row.status)}</Badge></td><td><strong className="recommended-quantity">{formatUnits(row.recommended_quantity)}</strong></td><td>{row.approved_quantity == null ? '—' : formatUnits(row.approved_quantity)}</td><td>{row.supplier_name || 'Supplier unavailable'}</td><td>{row.expires_at ? new Date(row.expires_at).toLocaleString() : '—'}</td><td>{row.status === 'NEW' && <Button className="compact" onClick={() => onReview(row)}>Review</Button>}</td></tr> })}</tbody></table>{!rows.length && <Empty title="No restock recommendations yet">Recommendations appear here when a product genuinely needs more stock.</Empty>}</article>
}

function ReviewModal({ recommendation, product, onClose, client }) {
  const [action, setAction] = useState('ACCEPT')
  const [approved, setApproved] = useState(recommendation.recommended_quantity)
  const [notes, setNotes] = useState('')
  const review = useMutation({ mutationFn: (data) => api.reviewRecommendation(recommendation.id, data), onSuccess: () => { invalidate(client); toast.success('Recommendation reviewed'); onClose() }, onError: fail })
  const submit = (event) => { event.preventDefault(); review.mutate({ action, approved_quantity: action === 'MODIFY' ? Number(approved) : undefined, notes }) }
  return <Modal title="Review restock recommendation" onClose={onClose}><form className="form-grid" onSubmit={submit}><p className="callout">{displayProduct(product || { sku: `Product ${recommendation.product_id}` }).name}: suggested order <strong>{formatUnits(recommendation.recommended_quantity)}</strong>. This review does not create a purchase order.</p><div className="review-actions"><button type="button" className={action === 'ACCEPT' ? 'selected' : ''} onClick={() => setAction('ACCEPT')}><Check size={17}/>Accept recommendation</button><button type="button" className={action === 'MODIFY' ? 'selected' : ''} onClick={() => setAction('MODIFY')}><Pencil size={17}/>Adjust quantity</button><button type="button" className={action === 'REJECT' ? 'selected' : ''} onClick={() => setAction('REJECT')}><X size={17}/>Reject recommendation</button></div>{action === 'MODIFY' && <label>Approved quantity<input required type="number" min="0" value={approved} onChange={(event) => setApproved(event.target.value)}/></label>}<label>Notes<textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Optional review notes"/></label><footer><Button type="button" className="secondary" onClick={onClose}>Cancel</Button><Button loading={review.isPending}>Confirm review</Button></footer></form></Modal>
}
