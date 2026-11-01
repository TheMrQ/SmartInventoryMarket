export function hasBlockingQueryError(queries) {
  return queries.some((query) => query.isError && query.data === undefined)
}
