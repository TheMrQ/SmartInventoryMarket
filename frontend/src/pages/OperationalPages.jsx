import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip as RechartsTooltip, XAxis, YAxis } from 'recharts'
import { FileUp, Plus, ShoppingCart } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { Badge, Button, Empty, Loading, Modal } from '../components/ui'
import { displayProduct, displayStatus, formatForecast, formatShortDate } from '../utils/presentation'
import { toneFor } from '../utils/status'

const errorToast = (error) => toast.error(error.message || 'Operation failed')
const revalidate = (client, keys) => keys.forEach((key) => client.invalidateQueries({ queryKey: [key] }))
const dateOffset = (value, days) => {
  const date = new Date(`${value}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}
function Heading({ title, text, children }) { return <header className="page-heading"><div><h2>{title}</h2><p>{text}</p></div>{children}</header> }
function ProductOption({ product }) { const item = displayProduct(product); return <option value={product.id}>{item.name} · {item.sku}</option> }

export function PurchaseOrdersPage() {
  const client = useQueryClient()
  const [create, setCreate] = useState(false)
  const orders = useQuery({ queryKey: ['orders'], queryFn: api.purchaseOrders })
  const suppliers = useQuery({ queryKey: ['suppliers'], queryFn: api.suppliers })
  const products = useQuery({ queryKey: ['products'], queryFn: () => api.products({ limit: 100 }) })
  const transition = useMutation({
    mutationFn: ({ id, target_status }) => api.transitionOrder(id, { target_status }),
    onSuccess: () => { revalidate(client, ['orders', 'inventory', 'transactions']); toast.success('Purchase order updated') },
    onError: errorToast,
  })
  if ([orders, suppliers, products].some((query) => query.isLoading)) return <Loading />
  const nextAction = {
    DRAFT: ['APPROVED', 'Approve order'],
    APPROVED: ['ORDERED', 'Place order'],
    ORDERED: ['IN_TRANSIT', 'Mark as in transit'],
  }
  return <div className="stack">
    <Heading title="Purchase Orders" text="Create, approve, place, and receive supplier orders through controlled steps."><Button onClick={() => setCreate(true)}><Plus size={16}/>Create purchase order</Button></Heading>
    <article className="panel table-wrap"><table><thead><tr><th>Purchase order</th><th>Supplier</th><th>Status</th><th>Expected arrival</th><th>Lines</th><th /></tr></thead><tbody>{orders.data?.map((order) => {
      const next = nextAction[order.status]
      return <tr key={order.id}><td><strong>{order.po_number}</strong></td><td>{suppliers.data?.find((supplier) => supplier.id === order.supplier_id)?.name || `Supplier #${order.supplier_id}`}</td><td><Badge tone={toneFor(order.status)}>{displayStatus(order.status)}</Badge></td><td>{order.expected_arrival_date || '—'}</td><td>{order.items.length}</td><td>{next && <button className="link-button" onClick={() => transition.mutate({ id: order.id, target_status: next[0] })}>{next[1]}</button>}{order.status === 'IN_TRANSIT' && <ReceiveButton order={order} client={client}/>}</td></tr>
    })}</tbody></table>{!orders.data?.length && <Empty title="No purchase orders yet">Create a supplier order when stock needs to be replenished.</Empty>}</article>
    {create && <OrderModal suppliers={suppliers.data} products={products.data} onClose={() => setCreate(false)} client={client}/>}
  </div>
}

function ReceiveButton({ order, client }) {
  const [confirming, setConfirming] = useState(false)
  const receive = useMutation({
    mutationFn: () => api.receiveOrder(order.id, { items: order.items.filter((item) => item.received_quantity < item.ordered_quantity).map((item) => ({ purchase_order_item_id: item.id, quantity: item.ordered_quantity - item.received_quantity })) }),
    onSuccess: () => { revalidate(client, ['orders', 'inventory', 'transactions']); toast.success('Goods receipt recorded'); setConfirming(false) },
    onError: errorToast,
  })
  return <><button className="link-button" disabled={receive.isPending} onClick={() => setConfirming(true)}>Receive goods</button>{confirming && <Modal title="Receive goods" onClose={() => setConfirming(false)}><div className="stack"><p>Record receipt for all remaining quantities. This increases available stock and creates receipt audit transactions.</p><footer><Button className="secondary" onClick={() => setConfirming(false)}>Cancel</Button><Button loading={receive.isPending} onClick={() => receive.mutate()}>Confirm receipt</Button></footer></div></Modal>}</>
}

function OrderModal({ suppliers, products, onClose, client }) {
  const [form, setForm] = useState({ po_number: '', supplier_id: '', expected_arrival_date: '', notes: '', items: [{ product_id: '', ordered_quantity: 1, unit_cost: '' }] })
  const create = useMutation({
    mutationFn: (data) => api.createPurchaseOrder(data),
    onSuccess: () => { revalidate(client, ['orders', 'inventory']); toast.success('Draft purchase order created'); onClose() },
    onError: errorToast,
  })
  const submit = (event) => { event.preventDefault(); create.mutate({ ...form, supplier_id: Number(form.supplier_id), items: form.items.map((item) => ({ ...item, product_id: Number(item.product_id), ordered_quantity: Number(item.ordered_quantity), unit_cost: item.unit_cost || null })) }) }
  return <Modal title="Create purchase order" onClose={onClose}><form className="form-grid" onSubmit={submit}><label>Purchase order number<input required placeholder="PO-2026-001" value={form.po_number} onChange={(event) => setForm({ ...form, po_number: event.target.value })}/></label><label>Supplier<select required value={form.supplier_id} onChange={(event) => setForm({ ...form, supplier_id: event.target.value })}><option value="">Select supplier</option>{suppliers.filter((supplier) => supplier.is_active).map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}</select></label><label>Expected arrival<input type="date" value={form.expected_arrival_date} onChange={(event) => setForm({ ...form, expected_arrival_date: event.target.value })}/></label><label>Notes<textarea value={form.notes} onChange={(event) => setForm({ ...form, notes: event.target.value })}/></label><div className="line-items">{form.items.map((line, index) => <div className="line" key={index}><select required value={line.product_id} onChange={(event) => setForm({ ...form, items: form.items.map((item, itemIndex) => itemIndex === index ? { ...item, product_id: event.target.value } : item) })}><option value="">Select product</option>{products.filter((product) => product.is_active).map((product) => <ProductOption key={product.id} product={product}/>)}</select><input type="number" min="1" value={line.ordered_quantity} onChange={(event) => setForm({ ...form, items: form.items.map((item, itemIndex) => itemIndex === index ? { ...item, ordered_quantity: event.target.value } : item) })}/><button type="button" className="link-button" disabled={form.items.length === 1} onClick={() => setForm({ ...form, items: form.items.filter((_, itemIndex) => itemIndex !== index) })}>Remove</button></div>)}<button type="button" className="link-button" onClick={() => setForm({ ...form, items: [...form.items, { product_id: '', ordered_quantity: 1, unit_cost: '' }] })}>+ Add product</button></div><footer><Button type="button" className="secondary" onClick={onClose}>Cancel</Button><Button loading={create.isPending}>Create draft</Button></footer></form></Modal>
}

export function SalesPage() {
  const client = useQueryClient()
  const [record, setRecord] = useState(false)
  const [upload, setUpload] = useState(false)
  const [selected, setSelected] = useState('')
  const sales = useQuery({ queryKey: ['sales', selected], queryFn: () => api.sales(selected ? { product_id: selected } : {}) })
  const products = useQuery({ queryKey: ['products'], queryFn: () => api.products({ limit: 100 }) })
  if (sales.isLoading || products.isLoading) return <Loading />
  const byId = new Map((products.data || []).map((product) => [product.id, product]))
  return <div className="stack"><Heading title="Sales" text="Record daily sales and import historical sales without changing current stock."><div className="button-group"><Button className="secondary" onClick={() => setUpload(true)}><FileUp size={16}/>Import historical CSV</Button><Button onClick={() => setRecord(true)}><ShoppingCart size={16}/>Record sale</Button></div></Heading><div className="callout">Historical imports update sales history only. They do not reduce available inventory.</div><div className="toolbar"><label>Product<select value={selected} onChange={(event) => setSelected(event.target.value)}><option value="">All products</option>{products.data?.map((product) => <ProductOption key={product.id} product={product}/>)}</select></label></div><article className="panel table-wrap"><table><thead><tr><th>Date</th><th>Product</th><th>Quantity</th><th>Sell price</th><th>Source</th></tr></thead><tbody>{sales.data?.map((row) => { const product = displayProduct(byId.get(row.product_id) || { sku: `Product ${row.product_id}` }); return <tr key={row.id}><td>{row.sale_date}</td><td><strong>{product.name}</strong><small>{product.sku}</small></td><td><strong>{row.quantity_sold}</strong></td><td>{row.sell_price || '—'}</td><td>{row.source || '—'}</td></tr> })}</tbody></table>{!sales.data?.length && <Empty title="No sales records yet">Record a sale or import historical sales to begin.</Empty>}</article>{record && <SaleModal products={products.data} onClose={() => setRecord(false)} client={client}/>} {upload && <UploadModal onClose={() => setUpload(false)} client={client}/>}</div>
}

function SaleModal({ products, onClose, client }) {
  const [form, setForm] = useState({ product_id: '', quantity: 1, sale_date: new Date().toISOString().slice(0, 10), sell_price: '', source: 'MANUAL' })
  const mutation = useMutation({ mutationFn: (data) => api.recordSale(data), onSuccess: () => { revalidate(client, ['sales', 'inventory', 'transactions', 'decisions']); toast.success('Sale recorded'); onClose() }, onError: errorToast })
  return <Modal title="Record sale" onClose={onClose}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); mutation.mutate({ ...form, product_id: Number(form.product_id), quantity: Number(form.quantity), sell_price: form.sell_price || null }) }}><label>Product<select required value={form.product_id} onChange={(event) => setForm({ ...form, product_id: event.target.value })}><option value="">Select product</option>{products.filter((product) => product.is_active).map((product) => <ProductOption key={product.id} product={product}/>)}</select></label><label>Quantity<input type="number" min="1" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: event.target.value })}/></label><label>Sale date<input type="date" value={form.sale_date} onChange={(event) => setForm({ ...form, sale_date: event.target.value })}/></label><label>Sell price (optional)<input type="number" min="0" step="0.01" value={form.sell_price} onChange={(event) => setForm({ ...form, sell_price: event.target.value })}/></label><label>Source<input value={form.source} onChange={(event) => setForm({ ...form, source: event.target.value })}/></label><footer><Button type="button" className="secondary" onClick={onClose}>Cancel</Button><Button loading={mutation.isPending}>Record sale</Button></footer></form></Modal>
}

function UploadModal({ onClose, client }) {
  const [file, setFile] = useState(null)
  const mutation = useMutation({ mutationFn: api.importSales, onSuccess: (data) => { revalidate(client, ['sales', 'forecasts']); toast.success(`${data.rows_inserted} inserted, ${data.rows_updated} updated`); onClose() }, onError: errorToast })
  return <Modal title="Import historical sales CSV" onClose={onClose}><div className="stack"><p>Expected columns: <code>sku,sale_date,quantity_sold,sell_price,source</code>. Duplicate SKU/date rows are rejected.</p><label className="upload"><FileUp size={22}/><span>{file?.name || 'Choose CSV file'}</span><input type="file" accept=".csv,text/csv" onChange={(event) => setFile(event.target.files?.[0] || null)}/></label><footer><Button className="secondary" onClick={onClose}>Cancel</Button><Button loading={mutation.isPending} disabled={!file} onClick={() => mutation.mutate(file)}>Import file</Button></footer></div></Modal>
}

export function ForecastsPage() {
  const client = useQueryClient()
  const [productId, setProductId] = useState('')
  const [horizon, setHorizon] = useState(28)
  const [selected, setSelected] = useState(null)
  const products = useQuery({ queryKey: ['products'], queryFn: () => api.products({ limit: 100 }) })
  const runs = useQuery({ queryKey: ['forecastRuns'], queryFn: api.forecastRuns })
  const active = selected || runs.data?.[0]
  const history = useQuery({
    queryKey: ['sales', 'forecast-history', productId, active?.history_end_date],
    enabled: Boolean(productId && active?.history_end_date),
    queryFn: () => api.sales({ product_id: productId, start_date: dateOffset(active.history_end_date, -27), end_date: active.history_end_date, limit: 28 }),
  })
  const generate = useMutation({
    mutationFn: api.createForecast,
    onSuccess: (data) => { setSelected(data); revalidate(client, ['forecastRuns', 'decisions']); toast.success('Forecast generated') },
    onError: errorToast,
  })
  const product = (products.data || []).find((item) => item.id === Number(productId))
  const chart = useMemo(() => {
    if (!active || !productId) return []
    const observed = [...(history.data || [])].sort((left, right) => left.sale_date.localeCompare(right.sale_date)).map((row) => ({ date: row.sale_date, historical: Number(row.quantity_sold), forecast: null }))
    const future = active.values.filter((value) => value.product_id === Number(productId) && value.horizon_day <= horizon).map((value) => ({ date: value.forecast_date, historical: null, forecast: Number(value.predicted_demand) }))
    return [...observed, ...future]
  }, [active, history.data, horizon, productId])
  if (products.isLoading || runs.isLoading) return <Loading />
  const activeTotals = active?.totals_by_product?.[productId]
  return <div className="stack">
    <Heading title="Forecasts" text="Review recent sales history and forecast future demand for the thesis demo products."/>
    <article className="panel forecast-control"><div><strong>XGBoost forecasting model</strong><span>Demo forecasts are available for products from the M5 thesis dataset.</span></div><select value={productId} onChange={(event) => setProductId(event.target.value)}><option value="">Select product</option>{products.data?.filter((item) => item.is_active).map((item) => <ProductOption key={item.id} product={item}/>)}</select><select value={horizon} onChange={(event) => setHorizon(Number(event.target.value))}><option value={7}>7 days</option><option value={14}>14 days</option><option value={28}>28 days</option></select><Button loading={generate.isPending} disabled={!productId} onClick={() => generate.mutate({ product_ids: [Number(productId)], horizon_days: horizon })}>Generate forecast</Button></article>
    {active && productId ? <><section className="kpis">{[7, 14, 28].map((days) => <article className="kpi products" key={days}><div><span>{days}-day forecast</span><strong>{formatForecast(activeTotals?.[`days_${days}`])}</strong><small>{displayProduct(product).name}</small></div></article>)}</section><article className="panel chart-panel"><header><div><p className="eyebrow">Demand outlook</p><h2>Sales history & demand forecast</h2><p>{displayProduct(product).name} · known sales through {formatShortDate(active.history_end_date)}</p></div></header>{history.isLoading ? <Loading /> : chart.length ? <ResponsiveContainer width="100%" height={340}><LineChart data={chart}><CartesianGrid vertical={false}/><XAxis dataKey="date" tickFormatter={formatShortDate} tick={{ fontSize: 11 }}/><YAxis allowDecimals={false}/><RechartsTooltip labelFormatter={formatShortDate} formatter={(value, name) => [formatForecast(value), name === 'historical' ? 'Historical sales' : 'Forecast demand']}/><Legend formatter={(value) => value === 'historical' ? 'Historical sales' : 'Forecast demand'}/><ReferenceLine x={active.forecast_start_date} stroke="#64748b" strokeDasharray="4 4" label={{ value: 'Forecast starts', position: 'insideTopRight', fill: '#64748b', fontSize: 11 }}/><Line type="monotone" dataKey="historical" stroke="#64748b" strokeWidth={2} dot={false}/><Line type="monotone" dataKey="forecast" stroke="#2563eb" strokeWidth={2.5} dot={false}/></LineChart></ResponsiveContainer> : <Empty title="Sales history is not available yet">Record or import sales for this product before viewing the forecast context.</Empty>}</article><details className="panel model-details"><summary>Forecast model details</summary><div><span>Model ID: {active.model_name}</span><span>Feature set: {active.feature_set} (25 features)</span><span>Forecast origin: {active.history_end_date}</span><span>Dataset context: M5 CA_1 / FOODS</span></div></details></> : <Empty title="Choose a product to explore demand">Select a thesis-demo product to compare its recent sales with forecast demand.</Empty>}
  </div>
}
