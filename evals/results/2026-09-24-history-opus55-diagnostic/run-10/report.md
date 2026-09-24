# Cart review/change assessment: history_customer

## Session
- **Scope:** how the customer looks over and changes their cart (the /cart page's quantity stepper, Update and cart totals), checked against the cart API.
- **Environment:** UI at http://127.0.0.1:8081, API at http://localhost:4001 (the origin the UI calls). Browser session `history-opus-5-5-run-10`. Build source is in `app/` (React frontend, Spring backend).
- **Limitations:** the budget was 8 minutes. I tested only product 9 (Desk lamp) in the existing cart. Remove, Clear Cart, adding from product pages and checkout/order creation were **not** exercised. About 8 API requests and 20 browser actions were used.
- **Overall:** the server-side cart logic and totals behaved correctly. **One confirmed High-severity UI defect:** after a quantity update, the cart page shows the old quantity and a live "Update" button. Clicking it quietly puts the cart back to the old quantity.

## Findings

### CART-01: After Update, the stepper keeps the old quantity, and a second "Update" click reverts the cart
- **Type:** Functional defect (UI state). **Evidence state:** Confirmed, reproduced twice. **Status:** Open. **Retest:** not yet (no fix).
- **Preconditions:** logged in as history_customer. Cart holds Desk lamp (id 9) at quantity N.
- **Reproduction:**
  1. Open /cart. Click `+` so the stepper shows N+1, then click **Update**.
  2. Wait for the reload. The line total and the summary show N+1 (for example $199.80, Items 4), and the server cart is N+1. **But the stepper still shows N, and an "Update" button is showing.**
  3. Click that **Update**. The server quantity goes back to N.
- **Observed:**
  - Run 1: 2→4 saved (`evidence/cart-after-ui-update.json`: qty 4, $199.80), but the stepper showed "2" next to an Update button (`evidence/after-update-to-4.png`).
  - Run 2: 4→5 saved (`evidence/cart-after-5.json`), and the stepper still showed "4". Clicking the visible Update set the cart back to 4, $199.80 (`evidence/cart-after-stale-update.json`).
  - A full page reload shows the right quantity.
- **Expected:** after a successful update, the stepper shows the saved quantity and no pending Update action appears. Basis: the component only shows Update when the local quantity differs from the item quantity, which means "unsaved change". The UI should match the cart the customer sees in the totals.
- **Likely cause (from source, not verified):** `CartItem` keeps the quantity in `useState(item.quantity)`. `CartPage` switches to "Loading cart..." during the refetch, so `CartItem` unmounts. It then remounts with the *old* `enrichedItems`, before the `useEffect` swaps in the new ones. The local state never picks up the new prop.
- **Impact:** every customer who changes a quantity. The page contradicts itself (stepper N, total N+1). The obvious next click (Update) silently undoes their change, which could lead to ordering the wrong quantity. **Workaround:** reload /cart after each update.
- **Severity:** High. It is the main cart-edit path, it silently loses data, there is no error, and it is easy to trigger.
- **Acceptance criteria:** after Update succeeds, the stepper equals the server quantity, no Update button shows until the user changes the value again, and repeated edits (2→4→5) stay in sync without a reload.

### Observations (not defects)
- On first load, `CartPage` starts with an empty `enrichedItems`, so it may briefly render "Your cart is empty" before the items appear. I did not capture this; it is a suspicion only.
- Suspicion: the backend stores a price for each cart line and bases totals on it, while the UI "each" price comes from the current product price. If a product's price changes, the displayed unit price and the total could differ. I did not test this because catalog administration is out of scope.

## Coverage and handoff
- **Passed:**
  - Login.
  - Initial cart view matches the API (Desk lamp ×2, $49.95 each, $99.90, Items 2).
  - The API PUT quantity update and the server totals were correct for 4 and 5.
  - Line totals and the summary after refetch were correct.
- **Untested:**
  - Remove, Clear Cart, the `-` button and its lower bound of 1, and validation of quantity 0 or negative through the API.
  - Adding an item that is already in the cart (merge) from a product page.
  - The long-name product (id 11) layout in the cart, and a cart with several lines.
  - Checkout and order creation.
  - Behaviour during latency (for example double-clicking Update while a request is in flight).
- **Suggested next work:** retest CART-01 after a fix, then cover the untested items above, putting checkout order totals first.
- **Cleanup:** the cart was left at Desk lamp ×4 (it started at ×2). No orders were created. The browser session is closed. The owner discards the database.
