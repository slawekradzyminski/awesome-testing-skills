# Cart review and change: exploratory assessment

**Target:** UI http://127.0.0.1:8081, API http://localhost:4001. User: history_customer. Browser: Playwright CLI (Chromium), desktop viewport. Date: 2026-09-24.
**Source:** app/ (the working copy I was given; I could not tell which revision this is). The running build is not identified, so the source may not match what is deployed.
**Charter:** the customer reviews the cart and changes item quantities, and the change must persist correctly. Out of scope: catalog/account administration and external delivery. I did not look at latency.
**Budget:** 8 minutes. I used about 8 API calls and about 15 browser actions.

## Summary
I found one serious, confirmed defect in the quantity-change flow. After a successful update, the quantity stepper keeps showing the **old** quantity and the **Update** button stays visible. If the customer clicks it, the cart is quietly set back to the old quantity. Everything else on the page (line total, summary count, summary total) shows the new value, so the page contradicts itself.

## Findings

### CART-01: After updating a quantity, the stepper shows the old value and clicking Update undoes the change
- **Type:** Functional / data integrity. Confirmed in the running app and explained by the code.
- **Severity:** High. The customer changes their quantity, gets no error, and the page then encourages a click that reverts the change. They could check out with a quantity they did not choose. It happens every time on the main cart-edit path, and a page reload is the only way out.
- **Steps (starting cart: Desk lamp ×2, $99.90):**
  1. Open /cart and click **+** twice. The stepper shows 4 and an **Update** button appears.
  2. Click **Update**. `PUT /api/cart/items/9 {quantity:4}` succeeds, and `GET /api/cart` then returns quantity 4, total 199.80 (`evidence/api-cart-after-update.json`).
  3. **Actual:** the stepper shows **2**, the **Update** button is still there, and the line total, summary Items and summary Total show **$199.80 / 4** (`evidence/02-after-update.png`).
  4. Click the leftover **Update**. The server cart goes back to quantity 2, $99.90 (`evidence/api-cart-after-stale-update.json`, `evidence/03-after-stale-update.png`). The page now shows the opposite mismatch: stepper 4, totals 2.
  5. A reload shows the correct state again, with no Update button.
- **Expected:** after a successful update, the stepper shows the saved quantity (4) and no Update button is offered.
- **Likely cause (code):** `CartItem.tsx` copies `item.quantity` into its own state with `useState(safeItem.quantity)` and never updates that copy when the prop changes. In `CartPage.tsx`, `handleCartUpdate` shows "Loading cart…" (which removes the item rows), refetches, and then shows the rows again. At that moment `enrichedItems` is still the old list, because the `useEffect` that fills it runs after that render and waits on a product fetch. So each `CartItem` is created again with the old quantity. When `enrichedItems` updates, only the prop changes and the local state stays old.
- **Retest:** rerun steps 1–4. After step 2, the stepper should equal the quantity from `GET /api/cart` and there should be no Update button. Clicking nothing further must leave the server quantity unchanged.

## Check ledger
| Check | Result | Evidence |
|---|---|---|
| Log in and open the cart; items, prices and totals match the API | Passed (Desk lamp 2 × $49.95 = $99.90, matches API and product) | 01-cart-initial.png, api-cart-before.json, api-product-9.json |
| Increase quantity and Update; saved on the server | Passed (server = 4) | api-cart-after-update.json |
| After Update, the UI reflects the saved state consistently | **Failed**: CART-01 | 02-after-update.png |
| Leftover Update button has no side effect | **Failed**: reverts the server cart to 2 | 03-after-stale-update.png, api-cart-after-stale-update.json |
| Reload shows the correct state again | Passed | (snapshot in session) |
| Remove item, Clear cart (confirm dialog), decrement to the minimum of 1, checkout | Not run (out of time) | |
| Error paths (failed PUT: UI rolls back to the server value), double-click, mobile layout, accessibility of the −/+ buttons (no accessible label beyond "-"/"+") | Not run / code review only | |

## Remaining risks (from code, not checked in the running app)
- **Remove and Clear cart** use the same "Loading cart… → refetch" path, so the same stale-state problem may affect the remaining rows after one item is removed from a cart with several items. This needs a test with 2 or more items.
- **Wrong price shown:** the cart API returns only productId and quantity. The UI shows the product's *current* price for each line, but the summary total uses the price *saved* in the cart. If a product's price changes, the line totals and the summary total could disagree. I did not test this because changing prices needs catalog admin, which is out of scope.
- **Hidden failures:** a failed update or remove only logs to the console, and the customer sees no message.
- The −/+ controls are unlabeled buttons with only the text "-"/"+", and the quantity is not announced to screen readers.

## Suggested regression tests
1. Change a quantity and click Update. The stepper, line total and summary all equal `GET /api/cart`, and no Update button is left. Forbidden side effect: no further PUT is sent.
2. With 2 or more items, remove one. The remaining rows keep their server quantities.
3. Force a failed PUT. The UI shows an error and returns to the server quantity.

## Cleanup
- The cart is back at its original state (Desk lamp ×2) because the defect itself reverted it. I placed no orders.
- My browser session is closed. I added no mocks or interceptors, and I deleted the temporary token file.
