import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { HelpCircle, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { api } from '../api/client'
import { Badge, Button, Empty, Loading, Modal, Tooltip } from '../components/ui'
import { displayProduct, displayStatus, formatUnits } from '../utils/presentation'
import { toneFor } from '../utils/status'

const tell = (error) => toast.error(error.message || 'Operation failed')
function PageHeader({ title, text, action }) { return <header className="page-heading"><div><h2>{title}</h2><p>{text}</p></div>{action}</header> }
function ProductOption({ product }) { const item = displayProduct(product); return <option value={product.id}>{item.name} · {item.sku}</option> }

export function ProductsPage() {
  const client = useQueryClient()
  const [search, setSearch] = useState('')
  const [editor, setEditor] = useState(null)
  const products = useQuery({ queryKey: ['products', search], queryFn: () => api.products({ limit: 100, search }) })
  const categories = useQuery({ queryKey: ['categories'], queryFn: api.categories })
  const save = useMutation({ mutationFn: ({ id, data }) => id ? api.updateProduct(id, data) : api.createProduct(data), onSuccess: () => { client.invalidateQueries({ queryKey: ['products'] }); client.invalidateQueries({ queryKey: ['inventory'] }); toast.success('Product saved'); setEditor(null) }, onError: tell })
  if (products.isLoading || categories.isLoading) return <Loading />
  return <div className="stack"><PageHeader title="Products" text="Maintain the product catalog used across stock, sales, forecasts, and supplier workflows." action={<Button onClick={() => setEditor({})}><Plus size={16}/>New product</Button>}/><div className="toolbar"><label>Search<input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="SKU or product name" /></label><span>{products.data?.length || 0} products</span></div><article className="panel table-wrap"><table><thead><tr><th>Product</th><th>Category</th><th>Unit</th><th>Status</th><th /></tr></thead><tbody>{products.data?.map((product) => { const item = displayProduct(product); return <tr key={product.id}><td><strong>{item.name}</strong><small>{item.sku}</small></td><td>{categories.data?.find((category) => category.id === product.category_id)?.name || '—'}</td><td>{product.unit}</td><td><Badge tone={product.is_active ? 'success' : 'neutral'}>{displayStatus(product.is_active ? 'ACTIVE' : 'INACTIVE')}</Badge></td><td><button className="link-button" onClick={() => setEditor(product)}>Edit</button></td></tr> })}</tbody></table>{!products.data?.length && <Empty title="No products yet">Create a product to begin inventory setup.</Empty>}</article>{editor && <ProductModal product={editor} categories={categories.data} onClose={() => setEditor(null)} onSave={(data) => save.mutate({ id: editor.id, data })} loading={save.isPending}/>}</div>
}

function ProductModal({ product, categories, onClose, onSave, loading }) {
  const [form, setForm] = useState({ sku: product.sku || '', name: product.name || '', category_id: product.category_id || categories[0]?.id || '', unit: product.unit || 'unit', is_active: product.is_active ?? true })
  const submit = (event) => { event.preventDefault(); onSave({ ...form, category_id: Number(form.category_id) }) }
  return <Modal title={product.id ? 'Edit product' : 'Create product'} onClose={onClose}><form className="form-grid" onSubmit={submit}><label>SKU<input required value={form.sku} onChange={(event) => setForm({ ...form, sku: event.target.value })}/></label><label>Product name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })}/></label><label>Category<select value={form.category_id} onChange={(event) => setForm({ ...form, category_id: event.target.value })}>{categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}</select></label><label>Unit<input required value={form.unit} onChange={(event) => setForm({ ...form, unit: event.target.value })}/></label>{product.id && <label className="check"><input type="checkbox" checked={form.is_active} onChange={(event) => setForm({ ...form, is_active: event.target.checked })}/> Active product</label>}<footer><Button type="button" className="secondary" onClick={onClose}>Cancel</Button><Button loading={loading} type="submit">Save product</Button></footer></form></Modal>
}

export function InventoryPage() {
  const client = useQueryClient()
  const [adjust, setAdjust] = useState(null)
  const inventory = useQuery({ queryKey: ['inventory'], queryFn: api.inventory })
  const transactions = useQuery({ queryKey: ['transactions'], queryFn: api.transactions })
  const products = useQuery({ queryKey: ['products'], queryFn: () => api.products({ limit: 100 }) })
  const save = useMutation({ mutationFn: ({ id, data }) => api.adjust(id, data), onSuccess: () => { ['inventory', 'transactions', 'decisions'].forEach((key) => client.invalidateQueries({ queryKey: [key] })); toast.success('Inventory adjustment recorded'); setAdjust(null) }, onError: tell })
  if ([inventory, transactions, products].some((query) => query.isLoading)) return <Loading />
  const byId = new Map((products.data || []).map((product) => [product.id, product]))
  return <div className="stack"><PageHeader title="Inventory" text="Track available stock, incoming goods, and audited stock movements."/><article className="panel table-wrap"><table><thead><tr><th>Product</th><th>Available</th><th>Incoming</th><th><Tooltip label="Available stock + incoming stock"><span>Inventory position <HelpCircle size={13}/></span></Tooltip></th><th>Updated</th><th /></tr></thead><tbody>{inventory.data?.map((row) => { const item = displayProduct({ ...byId.get(row.product_id), sku: row.sku, name: row.product_name }); return <tr key={row.product_id}><td><strong>{item.name}</strong><small>{item.sku}</small></td><td>{formatUnits(row.on_hand)}</td><td>{formatUnits(row.incoming_quantity)}</td><td><strong>{formatUnits(row.inventory_position)}</strong></td><td>{new Date(row.updated_at).toLocaleDateString()}</td><td><button className="link-button" onClick={() => setAdjust(row)}>Adjust stock</button></td></tr> })}</tbody></table>{!inventory.data?.length && <Empty title="No inventory yet">Products will appear here after they are created.</Empty>}</article><article className="panel table-wrap"><header><h2>Transaction history</h2></header><table><thead><tr><th>Type</th><th>Product</th><th>Quantity</th><th>Reason</th><th>Time</th></tr></thead><tbody>{transactions.data?.slice(0, 20).map((row) => { const item = displayProduct(byId.get(row.product_id) || { sku: `Product ${row.product_id}` }); return <tr key={row.id}><td><Badge tone={toneFor(row.transaction_type)}>{displayStatus(row.transaction_type)}</Badge></td><td><strong>{item.name}</strong><small>{item.sku}</small></td><td>{formatUnits(row.quantity)}</td><td>{row.reason || '—'}</td><td>{new Date(row.occurred_at).toLocaleString()}</td></tr> })}</tbody></table></article>{adjust && <AdjustmentModal item={adjust} onClose={() => setAdjust(null)} onSave={(data) => save.mutate({ id: adjust.product_id, data })} loading={save.isPending}/>}</div>
}

function AdjustmentModal({ item, onClose, onSave, loading }) {
  const [form, setForm] = useState({ transaction_type: 'ADJUSTMENT_IN', quantity: 1, reason: '' })
  return <Modal title={`Adjust ${displayProduct(item).name}`} onClose={onClose}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); onSave({ ...form, quantity: Number(form.quantity) }) }}><p className="callout">Stock is not freely editable. This creates an immutable adjustment record.</p><label>Adjustment type<select value={form.transaction_type} onChange={(event) => setForm({ ...form, transaction_type: event.target.value })}><option value="ADJUSTMENT_IN">Stock added</option><option value="ADJUSTMENT_OUT">Stock removed</option></select></label><label>Quantity<input type="number" min="1" value={form.quantity} onChange={(event) => setForm({ ...form, quantity: event.target.value })}/></label><label>Reason<textarea required value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })}/></label><footer><Button type="button" className="secondary" onClick={onClose}>Cancel</Button><Button loading={loading}>Record adjustment</Button></footer></form></Modal>
}

export function SuppliersPage() {
  const client = useQueryClient()
  const [open, setOpen] = useState(false)
  const suppliers = useQuery({ queryKey: ['suppliers'], queryFn: api.suppliers })
  const mappings = useQuery({ queryKey: ['supplierProducts'], queryFn: api.supplierProducts })
  const products = useQuery({ queryKey: ['products'], queryFn: () => api.products({ limit: 100 }) })
  const save = useMutation({ mutationFn: api.createSupplier, onSuccess: () => { client.invalidateQueries({ queryKey: ['suppliers'] }); toast.success('Supplier created'); setOpen(false) }, onError: tell })
  const map = useMutation({ mutationFn: api.createSupplierProduct, onSuccess: () => { client.invalidateQueries({ queryKey: ['supplierProducts'] }); client.invalidateQueries({ queryKey: ['decisions'] }); toast.success('Supplier mapping saved') }, onError: tell })
  if ([suppliers, mappings, products].some((query) => query.isLoading)) return <Loading />
  const byId = new Map((products.data || []).map((product) => [product.id, product]))
  return <div className="stack"><PageHeader title="Suppliers" text="Map active suppliers to products so stock insights can use delivery lead times." action={<Button onClick={() => setOpen(true)}><Plus size={16}/>New supplier</Button>}/><section className="two-grid"><article className="panel table-wrap"><header><h2>Suppliers</h2></header><table><thead><tr><th>Supplier</th><th>Contact</th><th>Status</th></tr></thead><tbody>{suppliers.data?.map((supplier) => <tr key={supplier.id}><td><strong>{supplier.name}</strong><small>{supplier.code}</small></td><td>{supplier.email || supplier.phone || '—'}</td><td><Badge tone={supplier.is_active ? 'success' : 'neutral'}>{displayStatus(supplier.is_active ? 'ACTIVE' : 'INACTIVE')}</Badge></td></tr>)}</tbody></table></article><article className="panel"><header><h2>Product mappings</h2></header><MappingForm suppliers={suppliers.data} products={products.data} onSave={map.mutate} loading={map.isPending}/><div className="mini-list">{mappings.data?.map((mapping) => { const item = displayProduct(byId.get(mapping.product_id) || { sku: `Product ${mapping.product_id}` }); return <div key={mapping.id}><div><strong>{item.name}</strong><span>{item.sku} · Supplier lead time {mapping.lead_time_days} days</span></div>{mapping.is_preferred && <Badge tone="success">Preferred</Badge>}</div> })}</div></article></section>{open && <SupplierModal onClose={() => setOpen(false)} onSave={save.mutate} loading={save.isPending}/>}</div>
}

function SupplierModal({ onClose, onSave, loading }) {
  const [form, setForm] = useState({ code: '', name: '', email: '', phone: '' })
  return <Modal title="Create supplier" onClose={onClose}><form className="form-grid" onSubmit={(event) => { event.preventDefault(); onSave(form) }}><label>Supplier code<input required value={form.code} onChange={(event) => setForm({ ...form, code: event.target.value })}/></label><label>Name<input required value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })}/></label><label>Email<input type="email" value={form.email} onChange={(event) => setForm({ ...form, email: event.target.value })}/></label><label>Phone<input value={form.phone} onChange={(event) => setForm({ ...form, phone: event.target.value })}/></label><footer><Button type="button" className="secondary" onClick={onClose}>Cancel</Button><Button loading={loading}>Save supplier</Button></footer></form></Modal>
}

function MappingForm({ suppliers, products, onSave, loading }) {
  const [form, setForm] = useState({ supplier_id: '', product_id: '', lead_time_days: 7, unit_cost: '', is_preferred: false })
  const submit = (event) => { event.preventDefault(); onSave({ ...form, supplier_id: Number(form.supplier_id), product_id: Number(form.product_id), lead_time_days: Number(form.lead_time_days), unit_cost: form.unit_cost || null }) }
  return <form className="inline-form" onSubmit={submit}><select required value={form.supplier_id} onChange={(event) => setForm({ ...form, supplier_id: event.target.value })}><option value="">Supplier</option>{suppliers.filter((supplier) => supplier.is_active).map((supplier) => <option key={supplier.id} value={supplier.id}>{supplier.name}</option>)}</select><select required value={form.product_id} onChange={(event) => setForm({ ...form, product_id: event.target.value })}><option value="">Product</option>{products.map((product) => <ProductOption key={product.id} product={product}/>)}</select><input type="number" min="1" placeholder="Lead days" value={form.lead_time_days} onChange={(event) => setForm({ ...form, lead_time_days: event.target.value })}/><label className="check"><input type="checkbox" checked={form.is_preferred} onChange={(event) => setForm({ ...form, is_preferred: event.target.checked })}/> Preferred</label><Button loading={loading}>Save mapping</Button></form>
}
