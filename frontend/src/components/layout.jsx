import { BarChart3, Box, ChevronLeft, ClipboardList, LayoutDashboard, LogOut, Menu, Package, ShoppingCart, Store, TrendingUp, Truck, UserRound, X } from 'lucide-react'
import { NavLink, useLocation } from 'react-router-dom'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import { Tooltip } from './ui'

const navGroups = [
  ['Overview', [['/', 'Dashboard', LayoutDashboard]]],
  ['Management', [['/products', 'Products', Package], ['/inventory', 'Inventory', Box], ['/suppliers', 'Suppliers', Truck], ['/purchase-orders', 'Purchase Orders', ShoppingCart]]],
  ['Intelligence', [['/sales', 'Sales', Store], ['/forecasts', 'Forecasts', TrendingUp], ['/decisions', 'Inventory Insights', ClipboardList]]],
]
const links = navGroups.flatMap(([, items]) => items)

export function Shell({ children, collapsed, setCollapsed, mobileOpen, setMobileOpen, user, onLogout }) {
  const location = useLocation()
  const sidebarRef = useRef(null)
  const [ribbon, setRibbon] = useState(null)
  const health = useQuery({ queryKey: ['health'], queryFn: api.health, retry: 1, refetchInterval: 30000 })
  const label = links.find(([path]) => path === location.pathname)?.[1] || 'Smart Inventory Market'
  const updateRibbon = useCallback(() => {
    const sidebar = sidebarRef.current
    if (!sidebar || !collapsed || mobileOpen || window.innerWidth <= 900) return setRibbon(null)
    const activeLink = sidebar.querySelector('nav a.active')
    if (!activeLink) return setRibbon(null)
    const sidebarBox = sidebar.getBoundingClientRect()
    const activeBox = activeLink.getBoundingClientRect()
    setRibbon({ top: activeBox.top - sidebarBox.top, height: activeBox.height })
  }, [collapsed, mobileOpen])
  useEffect(() => {
    updateRibbon()
    window.addEventListener('resize', updateRibbon)
    return () => window.removeEventListener('resize', updateRibbon)
  }, [updateRibbon, location.pathname])
  return <div className={`app-shell ${collapsed ? 'collapsed' : ''}`}>
    {mobileOpen && <button className="scrim" aria-label="Close navigation" onClick={() => setMobileOpen(false)} />}
    <aside ref={sidebarRef} className={`sidebar ${mobileOpen ? 'mobile-open' : ''}`}>
      <div className="brand"><div className="brand-mark"><BarChart3 size={20} /></div><span className="brand-name">Smart<span>Inventory</span></span><button className="mobile-close icon-button" onClick={() => setMobileOpen(false)} aria-label="Close navigation"><X size={18}/></button></div>
      <nav onScroll={updateRibbon}>{navGroups.map(([group, items]) => <section className="nav-group" key={group}><p className="nav-group-label">{group}</p>{items.map(([path, name, Icon]) => <Tooltip key={path} label={name} portal disabled={!collapsed || mobileOpen}><NavLink to={path} end={path === '/'} onClick={() => setMobileOpen(false)}><Icon className="nav-icon" size={19}/><span className="nav-label">{name}</span></NavLink></Tooltip>)}</section>)}</nav>
      <section className="sidebar-profile" aria-label="Authenticated user"><div className="profile-avatar" aria-hidden="true"><UserRound size={22}/></div><div className="profile-tail"><div className="profile-copy"><strong className="profile-name">{user.full_name}</strong><span className="profile-role">{user.role.replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase())}</span></div><button className="profile-logout" onClick={onLogout} aria-label="Log out"><LogOut size={16}/></button></div></section>
      {ribbon && <span className="sidebar-active-ribbon" aria-hidden="true" style={ribbon} />}
      <button className="collapse" onClick={() => setCollapsed(!collapsed)} aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}><ChevronLeft size={17}/></button>
    </aside>
    <main><header className="topbar"><button className="icon-button menu" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><Menu size={20}/></button><div className="topbar-brand"><p className="eyebrow">Smart Inventory Market</p><h1>{label}</h1></div><div className={`connection ${health.isSuccess ? 'online' : 'offline'}`}><i />{health.isSuccess ? 'Database connected' : 'Checking connection'}<span>M5 CA_1 · Thesis Demo</span></div></header><div className="page-content"><div className="page-transition" key={location.pathname}>{children}</div></div></main>
  </div>
}
