export function summarizePurchaseOrder(items = []) {
  return items.reduce(
    (summary, item) => {
      const ordered = Number(item.ordered_quantity) || 0;
      const received = Number(item.received_quantity) || 0;
      summary.ordered += ordered;
      summary.received += received;
      return summary;
    },
    { ordered: 0, received: 0, remaining: 0, lineCount: items.length },
  );
}

export function fulfillmentForPurchaseOrder(items = []) {
  const summary = summarizePurchaseOrder(items);
  summary.remaining = Math.max(0, summary.ordered - summary.received);
  summary.percentReceived = summary.ordered
    ? Math.round((summary.received / summary.ordered) * 100)
    : 0;
  return summary;
}

export function inventoryContextForProduct(inventoryByProduct, productId) {
  const inventory = inventoryByProduct.get(productId);
  if (!inventory) return null;
  const onHand = Number(inventory.on_hand) || 0;
  const incoming = Number(inventory.incoming_quantity) || 0;
  const reportedPosition = Number(inventory.inventory_position);
  return {
    onHand,
    incoming,
    inventoryPosition: Number.isFinite(reportedPosition)
      ? reportedPosition
      : onHand + incoming,
  };
}
