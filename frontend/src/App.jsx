import { useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'sonner'
import { Shell } from './components/layout'
import DashboardPage from './pages/DashboardPage'
import { InventoryPage, ProductsPage, SuppliersPage } from './pages/CatalogPages'
import { ForecastsPage, PurchaseOrdersPage, SalesPage } from './pages/OperationalPages'
import DecisionsPage from './pages/DecisionsPage'
import './App.css'
import './sidebar.css'
import './premium.css'

export default function App() {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  return <><Shell collapsed={collapsed} setCollapsed={setCollapsed} mobileOpen={mobileOpen} setMobileOpen={setMobileOpen}><Routes><Route path="/" element={<DashboardPage/>}/><Route path="/products" element={<ProductsPage/>}/><Route path="/inventory" element={<InventoryPage/>}/><Route path="/suppliers" element={<SuppliersPage/>}/><Route path="/purchase-orders" element={<PurchaseOrdersPage/>}/><Route path="/sales" element={<SalesPage/>}/><Route path="/forecasts" element={<ForecastsPage/>}/><Route path="/decisions" element={<DecisionsPage/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Routes></Shell><Toaster richColors position="top-right"/></>
}
