import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Check, ClipboardList, HelpCircle, Pencil, X } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
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
    <header className="page-heading"><div><p className="eyebrow">Decision support</p><h2>Inventory Insights</h2><p>Turn forecast demand, supplier delivery time, and stock levels into clear restocking guidance.</p></div></header>
    <div className="tabs"><button className={tab === 'decisions' ? 'active' : ''} onClick={() => setTab('decisions')}><ClipboardList size={16}/>Inventory Insights</button><button className={tab === 'recommendations' ? 'active' : ''} onClick={() => setTab('recommendations')}>Restock Recommendations <span>{recommendations.data?.filter((item) => item.status === 'NEW').length || 0}</span></button></div>
    {tab === 'decisions' ? <><div className="toolbar"><label>Stock status<select value={risk} onChange={(event) => setRisk(event.target.value)}><option value="">All statuses</option><RiskOption value="STOCKOUT_RISK"/><RiskOption value="REORDER_NEEDED"/><RiskOption value="HEALTHY"/><RiskOption value="OVERSTOCK_RISK"/></select></label><label>Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="SKU or product"/></label></div><article className="panel table-wrap"><table><thead><tr><th>Product</th><th>Available / incoming</th><th>Supplier</th><th><Tooltip label="Estimated supplier delivery time"><span>Lead time <HelpCircle size={13}/></span></Tooltip></th><th>Forecast demand</th><th><Tooltip label="Extra stock kept to reduce shortage risk."><span>Safety stock <HelpCircle size={13}/></span></Tooltip></th><th><Tooltip label="Inventory level at which restocking should be considered."><span>Reorder point <HelpCircle size={13}/></span></Tooltip></th><th>Stock status</th><th>Suggested order</th><th /></tr></thead><tbody>{decisions.data?.map((item) => <tr key={item.product_id}><td><strong>{displayProduct(item).name}</strong><small>{item.sku}</small></td><td>{formatUnits(item.on_hand)}<small>{formatUnits(item.incoming_quantity)} incoming · <Tooltip label="Available stock + incoming stock"><span>{formatUnits(item.inventory_position)} position</span></Tooltip></small></td><td>{item.supplier_name}<small>Selected supplier</small></td><td>{item.lead_time_days} days</td><td>{formatForecast(item.expected_lead_time_demand)}</td><td>{formatUnits(item.safety_stock)}</td><td>{formatUnits(item.reorder_point)}</td><td><Badge tone={toneFor(item.risk_status)}>{displayStatus(item.risk_status)}</Badge></td><td><strong className="recommended-quantity">{formatUnits(item.recommended_quantity)}</strong></td><td>{item.recommended_quantity > 0 && <Button className="compact" loading={generate.isPending} onClick={() => generate.mutate(item.product_id)}>Create restock recommendation</Button>}</td></tr>)}</tbody></table>{!decisions.data?.length && <Empty title="Inventory insights aren't available yet">Add a supplier and generate a forecast to calculate stock risk.</Empty>}</article></> : <Recommendations rows={recommendations.data || []} productById={productById} onReview={setReview}/>}
    <p className="callout">Reviewing a recommendation does not change inventory or automatically place a purchase order.</p>
    {review && <ReviewModal recommendation={review} product={productById.get(review.product_id)} onClose={() => setReview(null)} client={client}/>}
  </div>
}

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
