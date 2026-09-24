# Cart review and change: assessment

**Scope:** customer `history_customer` on the UI at http://127.0.0.1:8081, which calls the API at http://localhost:4001. The cart started with 2 × Desk lamp (product 9, $49.95, stock 20). I tested with the browser (playwright-cli) and with the API (curl), and read the source in `app/frontend/src/components/cart/`.

## Verdict
**Not ready.** After a successful quantity update, the cart page shows the wrong quantity. If the customer then presses the "Update" button that stays on screen, the cart quietly goes back to the old quantity.

## Defect 1 (high): the quantity control shows the old value after an update, and the leftover "Update" button undoes the change
Steps (browser):
1. Log in and open `/cart`. The row shows 2, $99.90, and the summary shows Items 2 / $99.90 (`evidence/cart-ui-1.yml`).
2. Click `+`. The control shows 3 and an "Update" button appears (`evidence/cart-ui-2.yml`).
3. Click **Update**. The server saves quantity 3, total $149.85 (`evidence/cart-after-update.json`).
   The page then shows a contradiction (`evidence/cart-ui-3-*.yml`, `evidence/stale-stepper.png`):
   - the quantity control shows **2**
   - the line total is **$149.85**
   - the summary shows **Items: 3**, **$149.85**
   - the **"Update" button is still showing**, even after waiting about 6 s.
4. Click that "Update" button. The UI sends quantity 2 and the server returns to 2 / $99.90 (`evidence/cart-after-stale-update.json`). Now the control shows **3** while the line total and summary show 2 / $99.90 (`evidence/cart-ui-4.yml`). The page is still wrong, just in the opposite direction.

Impact: customers can't trust the quantity shown. A natural "confirm" click reverses the change they just made, with no warning, so they may check out with a quantity they didn't intend.

Likely cause (from reading the code, not a fix):
- `CartItem` copies `item.quantity` into its local state (`useState`) only once, when it first appears.
- After an update, `CartPage` first redraws the rows from the old `enrichedItems`. These are replaced only later, in an async `useEffect`. The `key={productId}` doesn't change, so the local state never re-syncs with the new data.

## Other observations (lower severity or unconfirmed)
- **Failures give no feedback (from reading the code).** `handleQuantityChange` and `handleRemove` only call `console.error`, so a failed update or remove shows the customer nothing. The quantity quietly snaps back and the item stays in the cart. I didn't trigger this in the browser.
- **Quantities above stock are accepted.** `PUT /api/cart/items/9 {"quantity":21}` returned 200 with total $1048.95, although stock is 20 (`evidence/api-edge.txt`). This may be intended if stock is only checked at order time; I didn't test checkout.
- **Positive:** the API rejects quantity 0 and -1 with a 400 "must be greater than or equal to 1". The UI's `-` button also stops at 1. The first cart view, including the product name and price looked up from the product, was correct.

## Not covered (time limit of 8 minutes)
Remove, Clear Cart (which asks for confirmation), checkout and order creation, several items in the cart, and clicking quickly or repeatedly while the gateway is slow.

## State left behind
The cart is back to 2 × Desk lamp (confirmed by a 200 on the final PUT). I closed only my own browser session. No orders were created.
