const normalized = (value) => String(value || '').trim().toLocaleLowerCase()

export function includesSearch(query, ...values) {
  const needle = normalized(query)
  return !needle || values.some((value) => normalized(value).includes(needle))
}

export function filterInventoryRows(rows, productsById, query) {
  return rows.filter((row) => {
    const product = productsById.get(row.product_id) || row
    return includesSearch(query, row.sku, row.product_name, product.sku, product.name)
  })
}

export function filterSuppliers(rows, query) {
  return rows.filter((supplier) => includesSearch(query, supplier.name, supplier.code, supplier.email, supplier.phone))
}

export function filterSupplierMappings(rows, productsById, suppliersById, query) {
  return rows.filter((mapping) => {
    const product = productsById.get(mapping.product_id) || {}
    const supplier = suppliersById.get(mapping.supplier_id) || {}
    return includesSearch(query, product.sku, product.name, supplier.name, supplier.code)
  })
}

export function filterPurchaseOrders(rows, suppliersById, query, status) {
  return rows.filter((order) => {
    const supplier = suppliersById.get(order.supplier_id) || {}
    return (!status || order.status === status) && includesSearch(query, order.po_number, supplier.name, supplier.code)
  })
}
