# Cart review and editing: assessment (history_customer, 2026-09-24)

Scope: the /cart page at http://127.0.0.1:8081, backed by the API at http://localhost:4001. I checked the API directly with curl and used the UI through Playwright. I did not test checkout or order creation because I ran out of time.

## Verdict
The backend cart data is correct at every step I checked. The cart page has **two customer-facing defects**. The main one: after the customer changes a quantity, the row keeps showing the old quantity.

## Defect 1 (high): the row shows the old quantity after "Update"
Steps:
1. Start with a cart of Desk lamp ×2 ($99.90).
2. On /cart, click "+". The row shows 3 and an "Update" button appears.
3. Click "Update".

Expected: the row shows 3.
Actual: the row goes back to **"2"**. Next to it, the line total shows $149.85 and the summary shows Items 3 / $149.85. The API confirms quantity 3 (`evidence/cart_after_update.json`).

So the page contradicts itself. The customer may think the update failed and click "+" again, which would over-order. The numbers only agree again after a page reload (`evidence/cart_ui_3.txt`).
Evidence: `evidence/cart_ui_2.txt`, `evidence/cart_after_update.png`.
Likely cause: `CartItem` copies `quantity` into local state with `useState(item.quantity)` and never updates it when new data arrives. The component is recreated while the enriched item list still holds the old quantity. The line total comes straight from the new data, so it is correct, but the quantity stays at the old value.

## Defect 2 (medium): a long product name pushes the line total and "Remove" out of view
I added product 11 ("ReplacementCartridgeSeriesIndustrialCompatibilityEditionABC123456789", $49.95) through the API and reloaded /cart at 1280 px wide. The unbroken name squeezes the row. The quantity controls stick out past the card, and **the line total and the Remove button can't be seen**, so the customer can't check what that line costs or remove it from its own row.
Evidence: `evidence/cart_reload_longname.png`.

## What worked
- Login, and loading an existing cart: the page fills in names and prices from the product endpoint because the API cart returns only productId and quantity.
- The API update (PUT) stored the new quantity, and the backend totals were correct (3 × 49.95 = 149.85; with the second item, 4 items / $199.80).
- The summary and the header badge matched the backend.

## Not covered (time limit)
Decreasing a quantity, Remove, Clear Cart, checkout / order creation, and error handling. From reading the code: Remove and Clear Cart ask for no confirmation, and a failed update silently puts the old quantity back, with only a console error.

## State left behind
The cart now holds Desk lamp ×3 and product 11 ×1. The browser session is closed.
