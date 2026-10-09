import { Activity, BarChart3, Box, ChevronLeft, ClipboardList, Menu, Package, ShoppingCart, Store, TrendingUp, Truck, X } from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'

const links = [
  ['/', 'Dashboard', Activity], ['/products', 'Products', Package], ['/inventory', 'Inventory', Box], ['/suppliers', 'Suppliers', Truck], ['/purchase-orders', 'Purchase Orders', ShoppingCart], ['/sales', 'Sales', Store], ['/forecasts', 'Forecasts', TrendingUp], ['/decisions', 'Inventory Decisions', ClipboardList],
]

export function Shell({ children, collapsed, setCollapsed, mobileOpen, setMobileOpen }) {
  const location = useLocation()
  const health = useQuery({ queryKey: ['health'], queryFn: api.health, retry: 1, refetchInterval: 30000 })
  const label = links.find(([path]) => path === location.pathname)?.[1] || 'Smart Inventory Market'
  return <div className={`app-shell ${collapsed ? 'collapsed' : ''}`}>
    {mobileOpen && <button className="scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <aside className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="brand"><div className="brand-mark"><BarChart3 size={20} /></div><span>Smart<span>Inventory</span></span><button className="mobile-close icon-button" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18}/></button></div>
      <nav>{links.map(([path, name, Icon]) => <NavLink key={path} to={path} end={path === '/'} onClick={() => setMobileOpen(false)} title={name}><Icon size={19}/><span>{name}</span></NavLink>)}</nav>
      <button className="collapse" onClick={() => setCollapsed(!collapsed)} aria-label="Toggle sidebar"><ChevronLeft size={18}/><span>Collapse sidebar</span></button>
    </aside>
    <main><header className="topbar"><button className="icon-button menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div><p className="eyebrow">Operations workspace</p><h1>{label}</h1></div><div className={`connection ${health.isSuccess ? 'online' : 'offline'}`}><i />{health.isSuccess ? 'Database connected' : 'Checking connection'}<span>Thesis Demo</span></div></header><div className="page-content">{children}</div></main>
  </div>
}
