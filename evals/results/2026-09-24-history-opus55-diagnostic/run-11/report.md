# Cart review and change: exploratory assessment (history_customer)

**Date:** 2026-09-24. **UI:** http://127.0.0.1:8081. **API:** http://localhost:4001, the origin the UI calls, as TASK.md assigns. **Source:** app/ as supplied. The deployed build revision is unknown.
**Budget:** 8 minutes. About 8 API requests and about 12 browser actions used. Browser session `history-opus-5-5-run-11` is closed.

## Summary
There is one functional defect in the main "change quantity" journey, and I confirmed it at runtime. After a successful quantity update, the quantity control shows the **old** quantity next to an "Update" button. The line total and cart summary show the **new** quantity. If the customer clicks that Update button, it sends the stale quantity back to the server.

## Finding CART-01: the quantity control goes back to the old value after Update (Functional, severity High)
**Steps (runtime-confirmed):**
1. Log in as history_customer and open /cart. The cart starts with Desk lamp × 2 at $99.90 (`evidence/cart-initial.json`).
2. Click "+" twice. The control shows 4 and an "Update" button appears.
3. Click "Update".

**Expected:** the control shows 4, the Update button goes away, and the totals show 4 / $199.80.
**Actual:** the control shows **2** and the **"Update" button is still visible**. The line total is $199.80 and the summary says Items 4, Total $199.80 (`evidence/after-update.png`). The server stored 4 (`evidence/cart-after-update.json`). Reloading the page shows 4 everywhere and no Update button (`evidence/after-reload.txt`), so the bug is in the UI state only.

**Cause (from reading the code, not tested):** `CartPage.handleCartUpdate` sets `isUpdating`, which unmounts the list while it shows "Loading cart...". The `CartItem`s then mount again using the old `enrichedItems` (quantity 2) before the `useEffect` recomputes them. `CartItem` keeps `useState(safeItem.quantity)` and never updates it when the `item.quantity` prop changes, so it stays at 2 while the props say 4.

**Impact:** the page contradicts itself about how many items are in the cart. The Update button prompts the customer to click again, and that would silently set the quantity back to 2 (the `quantity !== safeItem.quantity` path sends a PUT with 2). This is likely to cause wrong orders in the most common way customers change their cart.

**Severity reasoning:** High, because it affects the main editing flow, it's misleading, and one natural click leads to data the customer didn't intend. It isn't Critical because a reload fixes the display.

## Risks from reading the code (not tested at runtime because of the time limit)
| Risk | Evidence | Next experiment |
|---|---|---|
| Line prices can disagree with the summary total | `CartService` totals use the price stored on the cart item. `CartPage` gets unit and line prices from the *current* product price (`/api/products/{id}`), because the cart DTO only returns productId and quantity. | Change a product price (needs admin, which is out of scope), then compare the line total with the summary. |
| Quantity above stock is accepted | `updateCartItem` only checks `@Min(1)` and has no stock check. Desk lamp stock is 20. | Set the quantity to 21 and then check out. See whether the order is rejected and what the UI shows. |
| Failed Remove or Clear gives no feedback | `handleRemove` and `handleClearCart` only write to `console.error` and show no message to the customer. | Force a 404 or 500 on DELETE, for example by removing in two tabs. |
| Very long product name (id 11) may break the layout | `CartItem` uses flex and doesn't truncate or wrap long names. | Add product 11 and check the page at a mobile width. |
| Controls have weak accessible names | The quantity buttons are labelled only "-" and "+". The quantity is a plain span with no label. | Screen-reader and axe pass. |

## Check ledger
| Check | Result |
|---|---|
| Cart review: the item, unit price, line total and summary match the API | Passed |
| Quantity increase and Update are saved on the server | Passed (API shows 4) |
| After Update, the quantity control and Update button match the new state | **Failed (CART-01)** |
| State after reload | Passed |
| Remove, Clear Cart, checkout and order creation | Not run (time limit) |
| Over-stock quantity, errors, long name, mobile layout, a11y | Not run (see risks above) |

## Leftovers
The cart for history_customer now holds Desk lamp × 4. The database is disposable, so I didn't restore it. No orders were created.

## Suggested regression scenarios
1. Change the quantity and click Update. Check that the control, line total and summary all show the new quantity, the Update button is gone, and no second PUT is sent.
2. Remove one line out of several. Check that the remaining lines keep their quantities.
3. Enter a quantity above stock. Check that the customer sees a clear message and that no order is created with an impossible quantity.
