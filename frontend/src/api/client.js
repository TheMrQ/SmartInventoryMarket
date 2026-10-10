const baseUrl = import.meta.env.VITE_API_BASE_URL || ''

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.status = status
  }
}

export async function request(path, options = {}) {
  const headers = options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }
  const csrf = document.cookie.split('; ').find((value) => value.startsWith('sim_csrf='))?.split('=')[1]
  const response = await fetch(`${baseUrl}${path}`, { ...options, credentials: 'include', headers: { ...headers, ...(csrf && { 'X-CSRF-Token': decodeURIComponent(csrf) }), ...options.headers } })
  const contentType = response.headers.get('content-type') || ''
  const body = contentType.includes('application/json') ? await response.json() : null
  if (!response.ok) throw new ApiError(body?.detail || 'The request could not be completed.', response.status)
  return body
}

export const api = {
  me: () => request('/api/auth/me'),
  login: (data) => request('/api/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data) => request('/api/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  logout: () => request('/api/auth/logout', { method: 'POST' }),
  health: () => request('/health/db'),
  products: (params = {}) => request(`/api/products?${new URLSearchParams(params)}`),
  categories: () => request('/api/categories?limit=100'),
  createProduct: (data) => request('/api/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id, data) => request(`/api/products/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  inventory: () => request('/api/inventory?limit=100'),
  adjust: (id, data) => request(`/api/inventory/${id}/adjustments`, { method: 'POST', body: JSON.stringify(data) }),
  transactions: (params = {}) => request(`/api/stock-transactions?${new URLSearchParams({ limit: 100, ...params })}`),
  suppliers: () => request('/api/suppliers?limit=100'),
  supplierProducts: () => request('/api/supplier-products?limit=100'),
  createSupplier: (data) => request('/api/suppliers', { method: 'POST', body: JSON.stringify(data) }),
  updateSupplier: (id, data) => request(`/api/suppliers/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  createSupplierProduct: (data) => request('/api/supplier-products', { method: 'POST', body: JSON.stringify(data) }),
  purchaseOrders: () => request('/api/purchase-orders?limit=100'),
  createPurchaseOrder: (data) => request('/api/purchase-orders', { method: 'POST', body: JSON.stringify(data) }),
  transitionOrder: (id, data) => request(`/api/purchase-orders/${id}/transition`, { method: 'POST', body: JSON.stringify(data) }),
  receiveOrder: (id, data) => request(`/api/purchase-orders/${id}/receive`, { method: 'POST', body: JSON.stringify(data) }),
  sales: (params = {}) => request(`/api/sales?${new URLSearchParams({ limit: 100, ...params })}`),
  recordSale: (data) => request('/api/sales/record', { method: 'POST', body: JSON.stringify(data) }),
  importSales: (file) => { const form = new FormData(); form.append('file', file); return request('/api/sales/import', { method: 'POST', body: form }) },
  forecastRuns: () => request('/api/forecast-runs?limit=50'),
  latestForecast: (productId) => request(`/api/forecasts/latest?product_id=${productId}`),
  createForecast: (data) => request('/api/forecasts', { method: 'POST', body: JSON.stringify(data) }),
  decisions: (params = {}) => request(`/api/inventory-decisions?${new URLSearchParams({ limit: 100, ...params })}`),
  recommendations: () => request('/api/reorder-recommendations?limit=100'),
  generateRecommendation: (product_id) => request('/api/reorder-recommendations/generate', { method: 'POST', body: JSON.stringify({ product_id }) }),
  reviewRecommendation: (id, data) => request(`/api/reorder-recommendations/${id}/review`, { method: 'POST', body: JSON.stringify(data) }),
}
