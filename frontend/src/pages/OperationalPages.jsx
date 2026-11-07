import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  FileUp,
  Plus,
  ReceiptText,
  ShoppingCart,
  TrendingUp,
} from "lucide-react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { api } from "../api/client";
import { DemandForecastChart } from "../components/DemandForecastChart";
import {
  Badge,
  Button,
  ConfirmationDialog,
  Empty,
  Loading,
  Modal,
  QueryError,
  ResultCount,
  SearchField,
} from "../components/ui";
import { filterPurchaseOrders } from "../utils/dataFilters";
import { hasBlockingQueryError } from "../utils/queryState";
import {
  displayProduct,
  displayStatus,
  formatForecast,
  formatApplicationDateTime,
  formatShortDate,
} from "../utils/presentation";
import { toneFor } from "../utils/status";
import {
  createSaleIdempotencyKey,
  receiptLinesForSubmission,
  canGenerateForecast,
} from "../utils/operationalWorkflows";
import {
  fulfillmentForPurchaseOrder,
  inventoryContextForProduct,
} from "../utils/purchaseOrderWorkspace";

const errorToast = (error) => toast.error(error.message || "Operation failed");
const revalidate = (client, keys) =>
  keys.forEach((key) => client.invalidateQueries({ queryKey: [key] }));
function Heading({ title, text, children, icon: Icon }) {
  const HeaderIcon =
    Icon ||
    (title === "Sales"
      ? ReceiptText
      : title === "Forecasts"
        ? TrendingUp
        : null);
  const semanticName = title.toLowerCase().replaceAll(" ", "-");
  return (
    <header className={`page-heading page-heading-${semanticName}`}>
      <div className="page-heading-copy">
        {HeaderIcon && (
          <i className="page-heading-icon">
            <HeaderIcon size={19} />
          </i>
        )}
        <div>
          <h2>{title}</h2>
          <p>{text}</p>
        </div>
      </div>
      {children}
    </header>
  );
}
function ProductOption({ product }) {
  const item = displayProduct(product);
  return (
    <option value={product.id}>
      {item.name} · {item.sku}
    </option>
  );
}

export function PurchaseOrdersPage() {
  const client = useQueryClient();
  const [create, setCreate] = useState(false);
  const [manage, setManage] = useState(null);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const orders = useQuery({
    queryKey: ["orders"],
    queryFn: api.purchaseOrders,
  });
  const suppliers = useQuery({
    queryKey: ["suppliers"],
    queryFn: api.suppliers,
  });
  const products = useQuery({
    queryKey: ["products"],
    queryFn: () => api.products({ limit: 100 }),
  });
  const inventory = useQuery({
    queryKey: ["inventory"],
    queryFn: api.inventory,
  });
  const recommendations = useQuery({
    queryKey: ["recommendations"],
    queryFn: api.recommendations,
  });
  const transition = useMutation({
    mutationFn: ({ id, target_status }) =>
      api.transitionOrder(id, { target_status }),
    onSuccess: () => {
      revalidate(client, ["orders", "inventory", "transactions"]);
      toast.success("Purchase order updated");
    },
    onError: errorToast,
  });
  if ([orders, suppliers, products].some((query) => query.isLoading))
    return <Loading />;
  if (hasBlockingQueryError([orders, suppliers, products]))
    return <QueryError queries={[orders, suppliers, products]} />;
  const nextAction = {
    DRAFT: ["APPROVED", "Approve order"],
    APPROVED: ["ORDERED", "Place order"],
    ORDERED: ["IN_TRANSIT", "Mark as in transit"],
  };
  const suppliersById = new Map(
    (suppliers.data || []).map((supplier) => [supplier.id, supplier]),
  );
  const productsById = new Map(
    (products.data || []).map((product) => [product.id, product]),
  );
  const inventoryByProduct = new Map(
    (inventory.data || []).map((item) => [item.product_id, item]),
  );
  const recommendationsById = new Map(
    (recommendations.data || []).map((recommendation) => [
      recommendation.id,
      recommendation,
    ]),
  );
  const visibleOrders = filterPurchaseOrders(
    orders.data || [],
    suppliersById,
    search,
    status,
  ).map((order) => ({
    ...order,
    raw_expected_arrival_date: order.expected_arrival_date,
    expected_arrival_date: order.expected_arrival_date
      ? formatShortDate(order.expected_arrival_date)
      : "Not scheduled",
  }));
  return (
    <div className="stack">
      <Heading
        icon={ShoppingCart}
        title="Purchase Orders"
        text="Create, approve, place, and receive supplier orders through controlled steps."
      >
        <Button onClick={() => setCreate(true)}>
          <Plus size={16} />
          Create purchase order
        </Button>
      </Heading>
      <div className="data-toolbar">
        <SearchField
          value={search}
          onChange={setSearch}
          label="Search purchase orders"
          placeholder="Search PO number or supplier"
          ariaLabel="Search purchase orders by number or supplier"
        />
        <label className="toolbar-filter">
          Status
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            <option value="DRAFT">Draft</option>
            <option value="APPROVED">Approved</option>
            <option value="ORDERED">Ordered</option>
            <option value="IN_TRANSIT">In transit</option>
            <option value="RECEIVED">Received</option>
            <option value="CANCELLED">Cancelled</option>
          </select>
        </label>
        <ResultCount
          count={visibleOrders.length}
          label={
            search.trim() || status ? "matching orders" : "purchase orders"
          }
          detail="Search and status filters combine"
        />
      </div>
      <article className="panel table-wrap purchase-orders-table">
        <table>
          <thead>
            <tr>
              <th>Purchase order</th>
              <th>Supplier</th>
              <th>Status</th>
              <th>Fulfillment</th>
              <th>Expected arrival</th>
              <th>Lines</th>
              <th className="row-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            {visibleOrders.map((order) => {
              const next = nextAction[order.status];
              const supplier = suppliersById.get(order.supplier_id);
              const fulfillment = fulfillmentForPurchaseOrder(order.items);
              return (
                <tr
                  key={order.id}
                  className="interaction-row interaction-row-actionable"
                >
                  <td>
                    <strong>{order.po_number}</strong>
                  </td>
                  <td className="po-supplier-cell">
                    <strong>{supplier?.name || "Supplier unavailable"}</strong>
                    {supplier?.code && <small>{supplier.code}</small>}
                  </td>
                  <td>
                    <Badge tone={toneFor(order.status)}>
                      {displayStatus(order.status)}
                    </Badge>
                  </td>
                  <td>
                    <FulfillmentCell fulfillment={fulfillment} />
                  </td>
                  <td>{order.expected_arrival_date || "—"}</td>
                  <td className="numeric-value">{fulfillment.lineCount}</td>
                  <td className="row-actions">
                    <div className="row-action-group">
                      <button
                        className="link-button row-action-manage"
                        onClick={() => setManage(order)}
                      >
                        Manage
                      </button>
                      {next && (
                        <button
                          className="link-button row-action-workflow"
                          onClick={() =>
                            transition.mutate({
                              id: order.id,
                              target_status: next[0],
                            })
                          }
                        >
                          {next[1]}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!visibleOrders.length && (
          <Empty
            title={
              search.trim() || status
                ? "No matching purchase orders"
                : "No purchase orders yet"
            }
          >
            {search.trim() || status
              ? "Try another PO number, supplier, or status."
              : "Create a supplier order when stock needs to be replenished."}
          </Empty>
        )}
      </article>
      {create && (
        <OrderModal
          suppliers={suppliers.data}
          products={products.data}
          onClose={() => setCreate(false)}
          client={client}
        />
      )}{" "}
      {manage && (
        <PurchaseOrderManageModal
          order={manage}
          onClose={() => setManage(null)}
          client={client}
          supplier={suppliersById.get(manage.supplier_id)}
          productsById={productsById}
          inventoryByProduct={inventoryByProduct}
          recommendationsById={recommendationsById}
          inventoryState={inventory}
          recommendationsState={recommendations}
        />
      )}
    </div>
  );
}

function FulfillmentCell({ fulfillment }) {
  return (
    <div className="po-fulfillment-cell">
      <strong>
        {fulfillment.received} / {fulfillment.ordered} received
      </strong>
      <span>{fulfillment.remaining} remaining</span>
      <i aria-hidden="true">
        <b style={{ width: `${fulfillment.percentReceived}%` }} />
      </i>
    </div>
  );
}

function InventoryContext({ context, loading, failed }) {
  if (loading)
    return (
      <span className="po-context-status">Loading inventory context…</span>
    );
  if (failed || !context)
    return (
      <span className="po-context-status">Inventory context unavailable</span>
    );
  return (
    <dl className="po-inventory-context">
      <div>
        <dt>On-hand</dt>
        <dd>{context.onHand}</dd>
      </div>
      <div>
        <dt>Incoming</dt>
        <dd>{context.incoming}</dd>
      </div>
      <div>
        <dt>Position</dt>
        <dd>{context.inventoryPosition}</dd>
      </div>
    </dl>
  );
}

function PurchaseOrderManageModal({
  order,
  onClose,
  client,
  supplier,
  productsById,
  inventoryByProduct,
  recommendationsById,
  inventoryState,
  recommendationsState,
}) {
  const [quantities, setQuantities] = useState(() =>
    Object.fromEntries(
      order.items.map((item) => [item.id, item.ordered_quantity]),
    ),
  );
  const [receipts, setReceipts] = useState(() =>
    Object.fromEntries(
      order.items.map((item) => [
        item.id,
        item.ordered_quantity - item.received_quantity,
      ]),
    ),
  );
  const [confirmation, setConfirmation] = useState(null);
  const refresh = () => {
    revalidate(client, ["orders", "inventory", "transactions", "decisions"]);
    onClose();
  };
  const updateLine = useMutation({
    mutationFn: ({ itemId, quantity }) =>
      api.updatePurchaseOrderItem(order.id, itemId, {
        ordered_quantity: quantity,
      }),
    onSuccess: refresh,
    onError: errorToast,
  });
  const removeLine = useMutation({
    mutationFn: (itemId) => api.deletePurchaseOrderItem(order.id, itemId),
    onSuccess: refresh,
    onError: errorToast,
  });
  const transition = useMutation({
    mutationFn: (target_status) =>
      api.transitionOrder(order.id, { target_status }),
    onSuccess: refresh,
    onError: errorToast,
  });
  const receive = useMutation({
    mutationFn: (items) => api.receiveOrder(order.id, { items }),
    onSuccess: refresh,
    onError: errorToast,
  });
  const canCancel = ["DRAFT", "APPROVED", "ORDERED", "IN_TRANSIT"].includes(
    order.status,
  );
  const fulfillment = fulfillmentForPurchaseOrder(order.items);
  const linkedRecommendation = order.reorder_recommendation_id
    ? recommendationsById.get(order.reorder_recommendation_id)
    : null;
  const expectedArrival =
    order.raw_expected_arrival_date ?? order.expected_arrival_date;
  const requestReceiptConfirmation = () => {
    try {
      const items = receiptLinesForSubmission(order.items, receipts);
      setConfirmation({ type: "receipt", items });
    } catch (error) {
      toast.error(error.message);
    }
  };
  const selectedReceiptQuantity = confirmation?.type === "receipt"
    ? confirmation.items.reduce((total, item) => total + item.quantity, 0)
    : 0;
  const confirmedLine = confirmation?.type === "remove-line" ? confirmation.item : null;
  const confirmedProduct = confirmedLine
    ? displayProduct(productsById.get(confirmedLine.product_id))
    : null;
  const confirmAction = () => {
    if (confirmation?.type === "receipt") receive.mutate(confirmation.items);
    if (confirmation?.type === "cancel") transition.mutate("CANCELLED");
    if (confirmation?.type === "remove-line") removeLine.mutate(confirmation.item.id);
  };
  const confirmationPending = confirmation?.type === "receipt"
    ? receive.isPending
    : confirmation?.type === "cancel"
      ? transition.isPending
      : confirmation?.type === "remove-line"
        ? removeLine.isPending
        : false;
  return (
    <>
    <Modal
      title="Purchase order"
      className="purchase-order-workspace"
      onClose={onClose}
    >
      <div className="po-workspace">
        <section className="po-workspace-identity">
          <div>
            <span>Purchase order</span>
            <strong>{order.po_number}</strong>
          </div>
          <Badge tone={toneFor(order.status)}>
            {displayStatus(order.status)}
          </Badge>
        </section>
        <section className="po-overview" aria-labelledby="po-overview-title">
          <header>
            <h3 id="po-overview-title">Order overview</h3>
            <span>
              {fulfillment.lineCount}{" "}
              {fulfillment.lineCount === 1 ? "line" : "lines"}
            </span>
          </header>
          <dl>
            <div>
              <dt>Supplier</dt>
              <dd>
                {supplier?.name || "Supplier unavailable"}
                {supplier?.code && <small>{supplier.code}</small>}
              </dd>
            </div>
            <div>
              <dt>Order date</dt>
              <dd>{formatShortDate(order.order_date)}</dd>
            </div>
            <div>
              <dt>Expected arrival</dt>
              <dd>
                {expectedArrival
                  ? formatShortDate(expectedArrival)
                  : "Not scheduled"}
              </dd>
            </div>
            {order.received_at && (
              <div>
                <dt>Received at</dt>
                <dd>{formatApplicationDateTime(order.received_at)}</dd>
              </div>
            )}
            <div>
              <dt>Recommendation</dt>
              <dd>
                {order.reorder_recommendation_id ? (
                  <>
                    <strong>#{order.reorder_recommendation_id}</strong> ·{" "}
                    {linkedRecommendation
                      ? displayStatus(linkedRecommendation.status)
                      : recommendationsState.isLoading
                        ? "Loading…"
                        : "Linked"}
                  </>
                ) : (
                  "Manual purchase order"
                )}
                {linkedRecommendation && (
                  <small>
                    {linkedRecommendation.approved_quantity ??
                      linkedRecommendation.recommended_quantity}{" "}
                    units approved
                  </small>
                )}
                {recommendationsState.isError &&
                  order.reorder_recommendation_id && (
                    <small>Recommendation context unavailable</small>
                  )}
              </dd>
            </div>
          </dl>
        </section>
        <section
          className={`po-fulfillment-summary ${order.status === "RECEIVED" ? "is-complete" : ""}`}
          aria-labelledby="po-fulfillment-title"
        >
          <header>
            <div>
              <span>Fulfillment</span>
              <h3 id="po-fulfillment-title">
                {fulfillment.percentReceived}% received
              </h3>
            </div>
            <span>
              {fulfillment.received} of {fulfillment.ordered} units
            </span>
          </header>
          <div
            className="po-progress"
            role="progressbar"
            aria-label="Purchase order fulfillment"
            aria-valuemin="0"
            aria-valuemax={fulfillment.ordered}
            aria-valuenow={fulfillment.received}
          >
            <i style={{ width: `${fulfillment.percentReceived}%` }} />
          </div>
          <div className="po-fulfillment-metrics">
            <div>
              <span>Ordered</span>
              <strong>{fulfillment.ordered}</strong>
            </div>
            <div>
              <span>Received</span>
              <strong>{fulfillment.received}</strong>
            </div>
            <div>
              <span>Remaining</span>
              <strong>{fulfillment.remaining}</strong>
            </div>
          </div>
        </section>
        <section className="po-lines-section" aria-labelledby="po-lines-title">
          <header>
            <div>
              <span>Line items</span>
              <h3 id="po-lines-title">Products in this order</h3>
            </div>
            <p>Inventory context is read from the current inventory view.</p>
          </header>
          <div className="po-line-table">
            <table>
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Ordered</th>
                  <th>Received</th>
                  <th>Remaining</th>
                  <th>Receive now / action</th>
                </tr>
              </thead>
              <tbody>
                {order.items.map((item) => {
                  const remaining =
                    item.ordered_quantity - item.received_quantity;
                  const product = displayProduct(
                    productsById.get(item.product_id),
                  );
                  const inventoryContext = inventoryContextForProduct(
                    inventoryByProduct,
                    item.product_id,
                  );
                  return (
                    <tr key={item.id}>
                      <td data-label="Product">
                        <strong>{product.name}</strong>
                        <small>{product.sku || "SKU unavailable"}</small>
                        <InventoryContext
                          context={inventoryContext}
                          loading={inventoryState.isLoading}
                          failed={inventoryState.isError}
                        />
                      </td>
                      <td data-label="Ordered">
                        {order.status === "DRAFT" ? (
                          <label className="po-number-field">
                            <span>Ordered quantity</span>
                            <input
                              aria-label={`Ordered quantity for ${product.sku || product.name}`}
                              type="number"
                              min="1"
                              value={quantities[item.id]}
                              onChange={(event) =>
                                setQuantities({
                                  ...quantities,
                                  [item.id]: event.target.value,
                                })
                              }
                            />
                          </label>
                        ) : (
                          item.ordered_quantity
                        )}
                      </td>
                      <td data-label="Received">{item.received_quantity}</td>
                      <td data-label="Remaining">
                        <strong>{remaining}</strong>
                      </td>
                      <td
                        data-label="Receive now / action"
                        className="po-line-action"
                      >
                        {order.status === "DRAFT" && (
                          <div className="po-line-actions">
                            <button
                              className="link-button"
                              onClick={() =>
                                updateLine.mutate({
                                  itemId: item.id,
                                  quantity: Number(quantities[item.id]),
                                })
                              }
                            >
                              Save line
                            </button>
                            <button
                              className="link-button po-remove-line"
                              onClick={() => setConfirmation({ type: "remove-line", item })}
                            >
                              Remove
                            </button>
                          </div>
                        )}
                        {order.status === "IN_TRANSIT" && remaining > 0 && (
                          <label className="po-receipt-field">
                            <span>Receive now</span>
                            <input
                              aria-label={`Receive now for ${product.sku || product.name}`}
                              type="number"
                              min="0"
                              max={remaining}
                              value={receipts[item.id]}
                              onChange={(event) =>
                                setReceipts({
                                  ...receipts,
                                  [item.id]: event.target.value,
                                })
                              }
                            />
                            <small>
                              Maximum {remaining}; {remaining} remaining
                            </small>
                          </label>
                        )}
                        {order.status !== "DRAFT" &&
                          !(order.status === "IN_TRANSIT" && remaining > 0) && (
                            <span className="po-no-line-action">
                              No line action available
                            </span>
                          )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
        {order.notes && (
          <section className="po-notes">
            <h3>Order notes</h3>
            <p>{order.notes}</p>
          </section>
        )}
        {order.status === "IN_TRANSIT" && fulfillment.remaining > 0 && (
          <section className="po-receipt-area">
            <div>
              <span>Receiving effect</span>
              <h3>Confirm the quantities received today</h3>
              <p>
                Confirming a receipt increases on-hand stock by the confirmed
                quantity and reduces the remaining incoming amount for this
                in-transit order. It moves existing supply from incoming to
                on-hand; it does not add extra inventory position.
              </p>
            </div>
            <Button
              loading={receive.isPending}
              onClick={requestReceiptConfirmation}
            >
              Confirm receipt
            </Button>
          </section>
        )}
        {order.status === "RECEIVED" && (
          <p className="po-complete-note">
            This purchase order is complete. All ordered quantities have been
            received.
          </p>
        )}
        <footer className="po-workspace-actions">
          {canCancel && (
            <Button
              className="secondary po-cancel-order"
              loading={transition.isPending}
              onClick={() => setConfirmation({ type: "cancel" })}
            >
              Cancel purchase order
            </Button>
          )}
          <Button className="secondary" onClick={onClose}>
            Close
          </Button>
        </footer>
      </div>
    </Modal>
    {confirmation && <ConfirmationDialog
      title={confirmation.type === "receipt" ? "Confirm receipt" : confirmation.type === "cancel" ? "Cancel purchase order?" : "Remove product from draft?"}
      description={confirmation.type === "receipt" ? `You are about to receive ${selectedReceiptQuantity} unit${selectedReceiptQuantity === 1 ? "" : "s"} for this purchase order.` : confirmation.type === "cancel" ? "Cancellation cannot be undone through the current workflow." : "This product line will be removed from the draft purchase order."}
      cancelLabel={confirmation.type === "cancel" ? "Keep order" : confirmation.type === "remove-line" ? "Keep line" : "Cancel"}
      confirmLabel={confirmation.type === "receipt" ? "Confirm receipt" : confirmation.type === "cancel" ? "Cancel purchase order" : "Remove line"}
      destructive={confirmation.type !== "receipt"}
      pending={confirmationPending}
      onCancel={() => setConfirmation(null)}
      onConfirm={confirmAction}
    >
      {confirmation.type === "receipt" && <><div className="confirmation-dialog-context"><strong>{order.items.filter((item) => confirmation.items.some((receipt) => receipt.purchase_order_item_id === item.id)).map((item) => displayProduct(productsById.get(item.product_id)).name).join(", ")}</strong><small>{order.items.filter((item) => confirmation.items.some((receipt) => receipt.purchase_order_item_id === item.id)).map((item) => displayProduct(productsById.get(item.product_id)).sku).filter(Boolean).join(", ")}</small></div><p className="confirmation-dialog-note">Receiving these units increases on-hand stock and reduces the corresponding incoming quantity. The operation creates an audited stock transaction.</p></>}
      {confirmation.type === "remove-line" && confirmedProduct && <div className="confirmation-dialog-context"><strong>{confirmedProduct.name}</strong><small>{confirmedProduct.sku || "SKU unavailable"}</small></div>}
    </ConfirmationDialog>}
    </>
  );
}

function OrderModal({ suppliers, products, onClose, client }) {
  const [form, setForm] = useState({
    po_number: "",
    supplier_id: "",
    expected_arrival_date: "",
    notes: "",
    items: [{ product_id: "", ordered_quantity: 1, unit_cost: "" }],
  });
  const create = useMutation({
    mutationFn: (data) => api.createPurchaseOrder(data),
    onSuccess: () => {
      revalidate(client, ["orders", "inventory"]);
      toast.success("Draft purchase order created");
      onClose();
    },
    onError: errorToast,
  });
  const submit = (event) => {
    event.preventDefault();
    create.mutate({
      ...form,
      supplier_id: Number(form.supplier_id),
      items: form.items.map((item) => ({
        ...item,
        product_id: Number(item.product_id),
        ordered_quantity: Number(item.ordered_quantity),
        unit_cost: item.unit_cost || null,
      })),
    });
  };
  return (
    <Modal title="Create purchase order" onClose={onClose}>
      <form className="form-grid" onSubmit={submit}>
        <label>
          Purchase order number
          <input
            required
            placeholder="PO-2026-001"
            value={form.po_number}
            onChange={(event) =>
              setForm({ ...form, po_number: event.target.value })
            }
          />
        </label>
        <label>
          Supplier
          <select
            required
            value={form.supplier_id}
            onChange={(event) =>
              setForm({ ...form, supplier_id: event.target.value })
            }
          >
            <option value="">Select supplier</option>
            {suppliers
              .filter((supplier) => supplier.is_active)
              .map((supplier) => (
                <option key={supplier.id} value={supplier.id}>
                  {supplier.name}
                </option>
              ))}
          </select>
        </label>
        <label>
          Expected arrival
          <input
            type="date"
            value={form.expected_arrival_date}
            onChange={(event) =>
              setForm({ ...form, expected_arrival_date: event.target.value })
            }
          />
        </label>
        <label>
          Notes
          <textarea
            value={form.notes}
            onChange={(event) =>
              setForm({ ...form, notes: event.target.value })
            }
          />
        </label>
        <div className="line-items">
          {form.items.map((line, index) => (
            <div className="line" key={index}>
              <select
                required
                value={line.product_id}
                onChange={(event) =>
                  setForm({
                    ...form,
                    items: form.items.map((item, itemIndex) =>
                      itemIndex === index
                        ? { ...item, product_id: event.target.value }
                        : item,
                    ),
                  })
                }
              >
                <option value="">Select product</option>
                {products
                  .filter((product) => product.is_active)
                  .map((product) => (
                    <ProductOption key={product.id} product={product} />
                  ))}
              </select>
              <input
                type="number"
                min="1"
                value={line.ordered_quantity}
                onChange={(event) =>
                  setForm({
                    ...form,
                    items: form.items.map((item, itemIndex) =>
                      itemIndex === index
                        ? { ...item, ordered_quantity: event.target.value }
                        : item,
                    ),
                  })
                }
              />
              <button
                type="button"
                className="link-button"
                disabled={form.items.length === 1}
                onClick={() =>
                  setForm({
                    ...form,
                    items: form.items.filter(
                      (_, itemIndex) => itemIndex !== index,
                    ),
                  })
                }
              >
                Remove
              </button>
            </div>
          ))}
          <button
            type="button"
            className="link-button"
            onClick={() =>
              setForm({
                ...form,
                items: [
                  ...form.items,
                  { product_id: "", ordered_quantity: 1, unit_cost: "" },
                ],
              })
            }
          >
            + Add product
          </button>
        </div>
        <footer>
          <Button type="button" className="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button loading={create.isPending}>Create draft</Button>
        </footer>
      </form>
    </Modal>
  );
}

export function SalesPage() {
  const client = useQueryClient();
  const [record, setRecord] = useState(false);
  const [upload, setUpload] = useState(false);
  const [selected, setSelected] = useState("");
  const sales = useQuery({
    queryKey: ["sales", selected],
    queryFn: () => api.sales(selected ? { product_id: selected } : {}),
  });
  const products = useQuery({
    queryKey: ["products"],
    queryFn: () => api.products({ limit: 100 }),
  });
  if (sales.isLoading || products.isLoading) return <Loading />;
  if (hasBlockingQueryError([sales, products]))
    return <QueryError queries={[sales, products]} />;
  const byId = new Map(
    (products.data || []).map((product) => [product.id, product]),
  );
  return (
    <div className="stack">
      <Heading
        title="Sales"
        text="Record daily sales and import historical sales without changing current stock."
      >
        <div className="button-group">
          <Button className="secondary" onClick={() => setUpload(true)}>
            <FileUp size={16} />
            Import historical CSV
          </Button>
          <Button onClick={() => setRecord(true)}>
            <ShoppingCart size={16} />
            Record sale
          </Button>
        </div>
      </Heading>
      <div className="callout">
        Historical imports update sales history only. They do not reduce
        available inventory.
      </div>
      <div className="toolbar">
        <label>
          Product
          <select
            value={selected}
            onChange={(event) => setSelected(event.target.value)}
          >
            <option value="">All products</option>
            {products.data?.map((product) => (
              <ProductOption key={product.id} product={product} />
            ))}
          </select>
        </label>
      </div>
      <article className="panel table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Product</th>
              <th>Quantity</th>
              <th>Sell price</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {sales.data?.map((row) => {
              const product = displayProduct(
                byId.get(row.product_id) || {
                  sku: `Product ${row.product_id}`,
                },
              );
              return (
                <tr
                  key={row.id}
                  className="interaction-row interaction-row-scan"
                >
                  <td>{row.sale_date}</td>
                  <td>
                    <strong>{product.name}</strong>
                    <small>{product.sku}</small>
                  </td>
                  <td>
                    <strong>{row.quantity_sold}</strong>
                  </td>
                  <td>{row.sell_price || "—"}</td>
                  <td>{row.source || "—"}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {!sales.data?.length && (
          <Empty title="No sales records yet">
            Record a sale or import historical sales to begin.
          </Empty>
        )}
      </article>
      {record && (
        <SaleModal
          products={products.data}
          onClose={() => setRecord(false)}
          client={client}
        />
      )}{" "}
      {upload && (
        <UploadModal onClose={() => setUpload(false)} client={client} />
      )}
    </div>
  );
}

function SaleModal({ products, onClose, client }) {
  const [form, setForm] = useState({
    product_id: "",
    quantity: 1,
    sale_date: new Date().toISOString().slice(0, 10),
    sell_price: "",
    source: "MANUAL",
  });
  const mutation = useMutation({
    mutationFn: (data) => api.recordSale(data),
    onSuccess: () => {
      revalidate(client, ["sales", "inventory", "transactions", "decisions"]);
      toast.success("Sale recorded");
      onClose();
    },
    onError: errorToast,
  });
  const [idempotencyKey] = useState(() => createSaleIdempotencyKey());
  return (
    <Modal title="Record sale" onClose={onClose}>
      <form
        className="form-grid"
        onSubmit={(event) => {
          event.preventDefault();
          mutation.mutate({
            ...form,
            product_id: Number(form.product_id),
            quantity: Number(form.quantity),
            sell_price: form.sell_price || null,
            idempotency_key: idempotencyKey,
          });
        }}
      >
        <label>
          Product
          <select
            required
            value={form.product_id}
            onChange={(event) =>
              setForm({ ...form, product_id: event.target.value })
            }
          >
            <option value="">Select product</option>
            {products
              .filter((product) => product.is_active)
              .map((product) => (
                <ProductOption key={product.id} product={product} />
              ))}
          </select>
        </label>
        <label>
          Quantity
          <input
            type="number"
            min="1"
            value={form.quantity}
            onChange={(event) =>
              setForm({ ...form, quantity: event.target.value })
            }
          />
        </label>
        <label>
          Sale date
          <input
            type="date"
            value={form.sale_date}
            onChange={(event) =>
              setForm({ ...form, sale_date: event.target.value })
            }
          />
        </label>
        <label>
          Sell price (optional)
          <input
            type="number"
            min="0"
            step="0.01"
            value={form.sell_price}
            onChange={(event) =>
              setForm({ ...form, sell_price: event.target.value })
            }
          />
        </label>
        <label>
          Source
          <input
            value={form.source}
            onChange={(event) =>
              setForm({ ...form, source: event.target.value })
            }
          />
        </label>
        <footer>
          <Button type="button" className="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button loading={mutation.isPending}>Record sale</Button>
        </footer>
      </form>
    </Modal>
  );
}

function UploadModal({ onClose, client }) {
  const [file, setFile] = useState(null);
  const mutation = useMutation({
    mutationFn: api.importSales,
    onSuccess: (data) => {
      revalidate(client, ["sales", "forecasts"]);
      toast.success(
        `${data.rows_inserted} inserted, ${data.rows_updated} updated`,
      );
      onClose();
    },
    onError: errorToast,
  });
  return (
    <Modal title="Import historical sales CSV" onClose={onClose}>
      <div className="stack">
        <p>
          Expected columns:{" "}
          <code>sku,sale_date,quantity_sold,sell_price,source</code>. Duplicate
          SKU/date rows are rejected.
        </p>
        <label className="upload">
          <FileUp size={22} />
          <span>{file?.name || "Choose CSV file"}</span>
          <input
            type="file"
            accept=".csv,text/csv"
            onChange={(event) => setFile(event.target.files?.[0] || null)}
          />
        </label>
        <footer>
          <Button className="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            loading={mutation.isPending}
            disabled={!file}
            onClick={() => mutation.mutate(file)}
          >
            Import file
          </Button>
        </footer>
      </div>
    </Modal>
  );
}

export function ForecastsPage() {
  const client = useQueryClient();
  const [searchParams, setSearchParams] = useSearchParams();
  const productId = searchParams.get("product") || "";
  const requestedHorizon = Number(searchParams.get("horizon"));
  const horizon = [7, 14, 28].includes(requestedHorizon)
    ? requestedHorizon
    : 28;
  const products = useQuery({
    queryKey: ["products"],
    queryFn: () => api.products({ limit: 100 }),
  });
  const eligibility = useQuery({
    queryKey: ["forecastEligibility"],
    queryFn: api.forecastEligibility,
  });
  const latestForecast = useQuery({
    queryKey: ["latestForecast", productId],
    queryFn: () => api.latestForecast(productId),
    enabled: Boolean(productId),
    retry: false,
  });
  const generate = useMutation({
    mutationFn: api.createForecast,
    onSuccess: (data) => {
      client.setQueryData(["latestForecast", productId], data);
      client.invalidateQueries({ queryKey: ["latestForecast", productId] });
      revalidate(client, ["forecastRuns", "decisions"]);
      toast.success(
        latestForecast.data ? "Forecast refreshed" : "Forecast generated",
      );
    },
    onError: errorToast,
  });
  const product = (products.data || []).find(
    (item) => item.id === Number(productId),
  );
  const updateSelection = (
    nextProductId = productId,
    nextHorizon = horizon,
  ) => {
    const next = new URLSearchParams();
    if (nextProductId) next.set("product", nextProductId);
    next.set("horizon", String(nextHorizon));
    setSearchParams(next);
  };
  if (products.isLoading || eligibility.isLoading) return <Loading />;
  if (hasBlockingQueryError([products, eligibility]))
    return <QueryError queries={[products, eligibility]} />;
  const active = latestForecast.data;
  const eligibilityByProduct = new Map(
    (eligibility.data || []).map((item) => [item.product_id, item]),
  );
  const selectedEligibility = eligibilityByProduct.get(Number(productId));
  const canGenerate = canGenerateForecast(productId, selectedEligibility);
  const activeTotals = active?.totals_by_product?.[productId];
  return (
    <div className="stack">
      <Heading
        title="Forecasts"
        text="Analyze historical sales and future expected demand. Inventory Insights turns the same saved forecast into restocking guidance."
      />
      <QueryError queries={[products, eligibility, latestForecast]} />
      <article className="panel forecast-control">
        <div>
          <strong>XGBoost forecasting model</strong>
          <span>
            Only eligible M5 CA_1 / FOODS SKUs can use the frozen XGBoost V1
            model.
          </span>
        </div>
        <select
          value={productId}
          onChange={(event) => updateSelection(event.target.value)}
        >
          <option value="">Select product</option>
          {products.data
            ?.filter((item) => item.is_active)
            .map((item) => {
              const itemEligibility = eligibilityByProduct.get(item.id);
              return (
                <option
                  key={item.id}
                  value={item.id}
                  disabled={itemEligibility && !itemEligibility.eligible}
                >
                  {displayProduct(item).name} ·{" "}
                  {itemEligibility?.eligible
                    ? "M5 eligible"
                    : "Not forecastable"}
                </option>
              );
            })}
        </select>
        <select
          value={horizon}
          onChange={(event) =>
            updateSelection(productId, Number(event.target.value))
          }
        >
          <option value={7}>7 days</option>
          <option value={14}>14 days</option>
          <option value={28}>28 days</option>
        </select>
        <Button
          loading={generate.isPending}
          disabled={!canGenerate}
          onClick={() =>
            generate.mutate({
              product_ids: [Number(productId)],
              horizon_days: horizon,
            })
          }
        >
          {active ? "Refresh forecast" : "Generate forecast"}
        </Button>
      </article>
      {productId && selectedEligibility && !selectedEligibility.eligible && (
        <div className="callout">
          <strong>Forecast unavailable for this product</strong>
          <span>
            {selectedEligibility.reason ||
              "The frozen model supports only compatible M5 CA_1 / FOODS SKUs."}
          </span>
        </div>
      )}
      {latestForecast.isLoading && productId ? (
        <Loading />
      ) : active && productId ? (
        <>
          <section className="kpis">
            {[7, 14, 28].map((days) => (
              <article className="kpi products" key={days}>
                <div>
                  <span>{days}-day forecast</span>
                  <strong>
                    {formatForecast(activeTotals?.[`days_${days}`])}
                  </strong>
                  <small>{displayProduct(product).name}</small>
                </div>
              </article>
            ))}
          </section>
          <article className="panel chart-panel">
            <DemandForecastChart
              forecast={active}
              productId={productId}
              horizon={horizon}
              productName={displayProduct(product).name}
            />
          </article>
          <details className="panel model-details">
            <summary>Forecast model details</summary>
            <div>
              <span>Model ID: {active.model_name}</span>
              <span>Feature set: {active.feature_set} (25 features)</span>
              <span>Forecast origin: {active.history_end_date}</span>
              <span>Dataset context: M5 CA_1 / FOODS</span>
            </div>
          </details>
        </>
      ) : productId &&
        !latestForecast.isError &&
        selectedEligibility?.eligible ? (
        <Empty title="No saved forecast for this product yet">
          Generate a forecast when you are ready. Opening this page never runs
          the model automatically.
        </Empty>
      ) : !productId ? (
        <Empty title="Choose an eligible M5 product">
          Select a compatible thesis-demo product to compare recent sales with
          future expected demand.
        </Empty>
      ) : null}
    </div>
  );
}
