import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, ArrowDownToLine, ArrowRight, Boxes, ClipboardCheck, PackageCheck } from 'lucide-react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Link } from 'react-router-dom'
import { api } from '../api/client'
import { Badge, Empty, Loading } from '../components/ui'
import { displayProduct, displayStatus, formatUnits } from '../utils/presentation'
import { toneFor } from '../utils/status'

const snapshotItems = [
  { key: 'products', label: 'Products tracked', detail: 'M5 CA_1 demo products', icon: Boxes },
  { key: 'onHand', label: 'Available stock', detail: 'Ready for sale', icon: PackageCheck },
  { key: 'incoming', label: 'Incoming stock', detail: 'Open purchase orders', icon: ArrowDownToLine },
  { key: 'new', label: 'Awaiting review', detail: 'Restock decisions', icon: ClipboardCheck },
]
const riskColors = { STOCKOUT_RISK: '#dc2626', REORDER_NEEDED: '#d97706', HEALTHY: '#16a34a', OVERSTOCK_RISK: '#4f46e5' }
const actionRisks = new Set(['STOCKOUT_RISK', 'REORDER_NEEDED'])

export default function DashboardPage() {
  const inventory = useQuery({ queryKey: ['inventory'], queryFn: api.inventory })
  const products = useQuery({ queryKey: ['products'], queryFn: () => api.products({ limit: 100 }) })
  const decisions = useQuery({ queryKey: ['decisions'], queryFn: api.decisions })
  const recommendations = useQuery({ queryKey: ['recommendations'], queryFn: api.recommendations })
  const orders = useQuery({ queryKey: ['orders'], queryFn: api.purchaseOrders })
  if ([inventory, products, decisions, recommendations, orders].some((query) => query.isLoading)) return <Loading />

  const inv = inventory.data || []
  const dec = decisions.data || []
  const rec = recommendations.data || []
  const productById = new Map((products.data || []).map((product) => [product.id, product]))
  const attention = dec.filter((item) => item.risk_status !== 'HEALTHY')
  const actionNeeded = dec.filter((item) => actionRisks.has(item.risk_status))
  const pendingReviews = rec.filter((item) => item.status === 'NEW')
  const values = {
    products: (products.data || []).length,
    onHand: inv.reduce((sum, item) => sum + item.on_hand, 0),
    incoming: inv.reduce((sum, item) => sum + item.incoming_quantity, 0),
    new: pendingReviews.length,
  }
  const risks = ['STOCKOUT_RISK', 'REORDER_NEEDED', 'HEALTHY', 'OVERSTOCK_RISK'].map((name) => ({ name: displayStatus(name), count: dec.filter((item) => item.risk_status === name).length, color: riskColors[name] }))
  const pulseTitle = actionNeeded.length
    ? `${actionNeeded.length} product${actionNeeded.length === 1 ? '' : 's'} need a stock decision`
    : pendingReviews.length
      ? `${pendingReviews.length} recommendation${pendingReviews.length === 1 ? '' : 's'} await review`
      : 'Inventory signals are ready to monitor'
  const pulseText = actionNeeded.length
    ? 'Review the forecast-informed risks before the next replenishment decision.'
    : 'Saved demand forecasts, supplier lead times, and stock position are brought together here.'

  return <main className="dashboard-control-room stack">
    <header className="dashboard-intro">
      <div><p>Smart Inventory Market / M5 CA_1 thesis demo</p><h1>Inventory control room</h1><span>Current stock, incoming supply, and saved demand evidence in one operational view.</span></div>
      <Link className="dashboard-intro-link" to="/decisions">Open inventory insights <ArrowRight size={16}/></Link>
    </header>

    <section className="inventory-pulse" aria-labelledby="inventory-pulse-heading">
      <div className="pulse-copy">
        <div className="pulse-label"><i><AlertTriangle size={16}/></i><span>Inventory pulse</span></div>
        <h2 id="inventory-pulse-heading">{pulseTitle}</h2>
        <p>{pulseText}</p>
      </div>
      <div className="pulse-evidence" aria-label="Current decision evidence">
        <div><span>Products at risk</span><strong>{actionNeeded.length.toLocaleString()}</strong><small>Stockout or reorder signals</small></div>
        <div><span>Awaiting review</span><strong>{pendingReviews.length.toLocaleString()}</strong><small>Human approval remains required</small></div>
      </div>
      <div className="pulse-actions">
        <Link className="button" to="/decisions">Review decisions <ArrowRight size={16}/></Link>
        <Link className="pulse-link" to="/forecasts">View demand forecasts</Link>
      </div>
    </section>

    <section className="inventory-snapshot" aria-label="Inventory snapshot">
      {snapshotItems.map(({ key, label, detail, icon: Icon }) => <article key={key} className="snapshot-item"><i><Icon size={18}/></i><div><span>{label}</span><strong>{key === 'products' || key === 'new' ? values[key].toLocaleString() : formatUnits(values[key])}</strong><small>{detail}</small></div></article>)}
    </section>

    <section className="dashboard-primary-grid">
      <article className="panel dashboard-risk-panel"><header><div><p className="eyebrow">Forecast-informed stock state</p><h2>Inventory health</h2><span>Signals combine current position, incoming supply, and saved demand evidence.</span></div></header>{dec.length ? <ResponsiveContainer width="100%" height={276}><BarChart data={risks} margin={{ top: 8, right: 6, left: -18, bottom: 0 }}><XAxis dataKey="name" tick={{ fontSize: 11 }} tickLine={false} axisLine={false}/><YAxis allowDecimals={false} tickLine={false} axisLine={false}/><Tooltip cursor={{ fill: '#eff6ff' }}/><Bar dataKey="count" radius={[6, 6, 0, 0]}>{risks.map((entry) => <Cell key={entry.name} fill={entry.color}/>)}</Bar></BarChart></ResponsiveContainer> : <Empty title="Inventory insights aren't available yet">Add a supplier and generate a forecast to calculate stock risk.</Empty>}</article>
      <article className="panel dashboard-priority-panel"><header><div><p className="eyebrow">Action queue</p><h2>Restock recommendations</h2></div><Link to="/decisions">See all</Link></header>{rec.length ? <div className="mini-list">{rec.slice(0, 5).map((item) => { const product = displayProduct(productById.get(item.product_id) || { sku: `Product ${item.product_id}` }); return <div key={item.id}><div><strong>{product.name}</strong><span>{product.sku} / Suggested {formatUnits(item.recommended_quantity)}</span></div><Badge tone={toneFor(item.status)}>{displayStatus(item.status)}</Badge></div> })}</div> : <Empty title="No restock recommendations yet">Recommendations appear when a product genuinely needs more stock.</Empty>}</article>
    </section>

    <section className="dashboard-evidence-grid">
      <article className="panel"><header><div><p className="eyebrow">Stock to review</p><h2>Inventory attention</h2></div><span className="panel-count">{attention.length.toLocaleString()} signals</span></header>{attention.length ? <div className="mini-list">{attention.slice(0, 5).map((item) => <div key={item.product_id}><div><strong>{displayProduct(item).name}</strong><span>{item.sku} / {formatUnits(item.inventory_position)} in position / {formatUnits(item.recommended_quantity)} suggested</span></div><Badge tone={toneFor(item.risk_status)}>{displayStatus(item.risk_status)}</Badge></div>)}</div> : <Empty title="Inventory looks balanced">Stock risk will appear here when a product needs attention.</Empty>}</article>
      <article className="panel"><header><div><p className="eyebrow">Procurement status</p><h2>Recent purchase orders</h2></div><Link to="/purchase-orders">Open orders</Link></header>{(orders.data || []).length ? <div className="mini-list">{orders.data.slice(0, 5).map((item) => <div key={item.id}><div><strong>{item.po_number}</strong><span>{item.items.length} line item{item.items.length === 1 ? '' : 's'}</span></div><Badge tone={toneFor(item.status)}>{displayStatus(item.status)}</Badge></div>)}</div> : <Empty title="No purchase orders yet">Create a purchase order when stock needs to be replenished.</Empty>}</article>
    </section>
  </main>
}
