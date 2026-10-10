import { useState } from 'react'
import { Navigate, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { Toaster, toast } from 'sonner'
import { Shell } from './components/layout'
import { Loading } from './components/ui'
import AuthPage from './pages/AuthPage'
import DashboardPage from './pages/DashboardPage'
import { InventoryPage, ProductsPage, SuppliersPage } from './pages/CatalogPages'
import { ForecastsPage, PurchaseOrdersPage, SalesPage } from './pages/OperationalPages'
import DecisionsPage from './pages/DecisionsPage'
import { api } from './api/client'
import './App.css'
import './sidebar.css'
import './premium.css'
import './auth.css'

function ProtectedWorkspace() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const client = useQueryClient()
  const navigate = useNavigate()
  const location = useLocation()
  const me = useQuery({ queryKey: ['auth-me'], queryFn: api.me, retry: false, staleTime: 300000 })
  if (me.isLoading) return <Loading />
  if (me.isError) return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />
  const logout = async () => { try { await api.logout() } finally { client.clear(); toast.success('Signed out'); navigate('/login', { replace: true }) } }
  return <Shell collapsed={collapsed} setCollapsed={setCollapsed} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen} user={me.data} onLogout={logout}><Routes><Route path="/" element={<DashboardPage/>}/><Route path="/products" element={<ProductsPage/>}/><Route path="/inventory" element={<InventoryPage/>}/><Route path="/suppliers" element={<SuppliersPage/>}/><Route path="/purchase-orders" element={<PurchaseOrdersPage/>}/><Route path="/sales" element={<SalesPage/>}/><Route path="/forecasts" element={<ForecastsPage/>}/><Route path="/decisions" element={<DecisionsPage/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Routes></Shell>
}

export default function App() { return <><Routes><Route path="/login" element={<AuthPage key="login" initialMode="login"/>}/><Route path="/register" element={<AuthPage key="register" initialMode="register"/>}/><Route path="/*" element={<ProtectedWorkspace/>}/></Routes><Toaster richColors position="top-right"/></> }
