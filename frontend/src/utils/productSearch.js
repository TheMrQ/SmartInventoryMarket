export const PRODUCT_SEARCH_DEBOUNCE_MS = 300

export function normalizedProductSearch(value) {
  return value.trim()
}

export function productSearchParams(search) {
  return { limit: 100, ...(search && { search }) }
}

export function productSearchPresentation({ hasProducts, isFetching, isError }) {
  return {
    keepTableMounted: hasProducts || isFetching || isError,
    showUpdating: hasProducts && isFetching,
    showNoResults: hasProducts && !isFetching,
  }
}
