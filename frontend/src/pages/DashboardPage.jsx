import { useQuery } from '@tanstack/react-query'
import { AlertTriangle, ArrowDownToLine, Boxes, ClipboardCheck, PackageCheck } from 'lucide-react'
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api/client'
import { Badge, Empty, Loading } from '../components/ui'
import { displayProduct, displayStatus, formatUnits } from '../utils/presentation'
import { toneFor } from '../utils/status'

const cards = [
  { key: 'products', label: 'Products tracked', context: 'M5 CA_1 demo products', icon: Boxes },
  { key: 'onHand', label: 'Available stock', context: 'Ready for sale', icon: PackageCheck },
  { key: 'incoming', label: 'Incoming stock', context: 'Open purchase orders', icon: ArrowDownToLine },
  { key: 'new', label: 'Pending recommendations', context: 'Awaiting review', icon: ClipboardCheck },
]
const riskColors = { STOCKOUT_RISK: '#dc2626', REORDER_NEEDED: '#d97706', HEALTHY: '#16a34a', OVERSTOCK_RISK: '#4f46e5' }

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
  const values = {
    products: (products.data || []).length,
    onHand: inv.reduce((sum, item) => sum + item.on_hand, 0),
    incoming: inv.reduce((sum, item) => sum + item.incoming_quantity, 0),
    new: rec.filter((item) => item.status === 'NEW').length,
  }
  const risks = ['STOCKOUT_RISK', 'REORDER_NEEDED', 'HEALTHY', 'OVERSTOCK_RISK'].map((name) => ({ name: displayStatus(name), count: dec.filter((item) => item.risk_status === name).length, color: riskColors[name] }))

  return <div className="stack">
    <section className="hero-copy"><div><p className="eyebrow">M5 CA_1 · Thesis demo</p><h2>Inventory signals, ready for review.</h2><p>Live operational data informs every signal. Restock recommendations remain human-reviewed.</p></div><div className="hero-note"><AlertTriangle size={18}/><span>Forecasts use the frozen M5-compatible thesis model only.</span></div></section>
    <section className="kpis">{cards.map(({ key, label, context, icon: Icon }) => <article className={`kpi ${key}`} key={key}><div><span>{label}</span><strong>{key === 'products' || key === 'new' ? values[key].toLocaleString() : formatUnits(values[key])}</strong><small>{context}</small></div><i><Icon size={20}/></i></article>)}</section>
    <section className="two-grid"><article className="panel chart-panel"><header><div><p className="eyebrow">Inventory health</p><h2>Stock status overview</h2></div></header>{dec.length ? <ResponsiveContainer width="100%" height={250}><BarChart data={risks}><XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis allowDecimals={false}/><Tooltip/><Bar dataKey="count" radius={[5,5,0,0]}>{risks.map((entry) => <Cell key={entry.name} fill={entry.color}/>)}</Bar></BarChart></ResponsiveContainer> : <Empty title="Inventory insights aren't available yet">Add a supplier and generate a forecast to calculate stock risk.</Empty>}</article><article className="panel"><header><div><p className="eyebrow">Needs attention</p><h2>Restock recommendations</h2></div></header>{rec.length ? <div className="mini-list">{rec.slice(0,5).map((item) => { const product = displayProduct(productById.get(item.product_id) || { sku: `Product ${item.product_id}` }); return <div key={item.id}><div><strong>{product.name}</strong><span>{product.sku} · Suggested {formatUnits(item.recommended_quantity)}</span></div><Badge tone={toneFor(item.status)}>{displayStatus(item.status)}</Badge></div> })}</div> : <Empty title="No restock recommendations yet">Recommendations appear when a product genuinely needs more stock.</Empty>}</article></section>
    <section className="two-grid"><article className="panel"><header><div><p className="eyebrow">Stock to review</p><h2>Inventory attention</h2></div></header>{dec.filter((item) => item.risk_status !== 'HEALTHY').length ? <div className="mini-list">{dec.filter((item) => item.risk_status !== 'HEALTHY').slice(0,5).map((item) => <div key={item.product_id}><div><strong>{displayProduct(item).name}</strong><span>{item.sku} · {formatUnits(item.inventory_position)} in position · {formatUnits(item.recommended_quantity)} suggested</span></div><Badge tone={toneFor(item.risk_status)}>{displayStatus(item.risk_status)}</Badge></div>)}</div> : <Empty title="Inventory looks balanced">Stock risk will appear here when a product needs attention.</Empty>}</article><article className="panel"><header><div><p className="eyebrow">Procurement</p><h2>Recent purchase orders</h2></div></header>{(orders.data || []).length ? <div className="mini-list">{orders.data.slice(0,5).map((item) => <div key={item.id}><div><strong>{item.po_number}</strong><span>{item.items.length} line item{item.items.length === 1 ? '' : 's'}</span></div><Badge tone={toneFor(item.status)}>{displayStatus(item.status)}</Badge></div>)}</div> : <Empty title="No purchase orders yet">Create a purchase order when stock needs to be replenished.</Empty>}</article></section>
  </div>
}
