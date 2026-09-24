# Cart review and change: assessment

## Session
- **Scope:** how history_customer reviews the cart and changes quantities on the historical UI at http://127.0.0.1:8081 (API at http://localhost:4001). I only had time to test changing quantities. I did not test Remove, Clear Cart or checkout.
- **Context:** source in `app/` (`CartPage.tsx`, `CartItem.tsx`, `CartSummary.tsx`, `CartService.java`). Starting cart: Desk lamp (id 9, $49.95) × 2 = $99.90.
- **Limits:** 8-minute budget; about 10 API requests and 25 browser actions used. The gateway adds latency, but I made no timing or performance claims.
- **Overall:** The cart displays correctly when the page first loads, and the server applies quantity updates correctly. But after every successful update the quantity box shows the wrong number and a leftover **Update** button stays on screen. Clicking that button quietly changes the cart back to the old quantity. **One confirmed High-severity defect.**

## Findings

### CART-01: After an update the quantity box shows the old number, and clicking the leftover "Update" undoes the change
- **Type:** Functional defect (UI state out of sync with the server). **Evidence:** Confirmed, reproduced 3 times (2→3, 3→4, then the revert). **Status:** Open.
- **Preconditions:** Logged in as history_customer with at least one cart line (here Desk lamp × 2).
- **Steps to reproduce:**
  1. Open `/cart`. The row shows qty 2, $99.90, and the summary shows 2 items / $99.90 (`evidence/01-cart-initial.png`).
  2. Click **+** (the box shows 3), then click **Update**.
  3. Wait for the reload to finish.
- **Expected:** The quantity box shows 3 and the Update button goes away. The component only shows Update when the entered quantity differs from the saved one (`quantity !== safeItem.quantity` in `CartItem.tsx`), so a finished update should leave nothing pending. Basis: the component's own logic and ordinary cart behaviour.
- **Actual:** The server saved qty 3, total $149.85 (`evidence/api-cart-after-update.json`). On screen:
  - line total $149.85 and summary 3 items / $149.85, which are correct;
  - quantity box **2** with an **Update** button still showing (`evidence/02-after-update.png`).

  Clicking that Update sends the old quantity. In the second run (3→4), the server had 4 (`evidence/snap-after-update-to-4.txt`). Clicking the leftover Update changed the server cart back to **3 / $149.85** without any warning (`evidence/api-cart-after-stale-update.json`, `evidence/snap-after-stale-update.txt`, `evidence/03-after-stale-update.png`). Reloading the page shows the correct quantity, which confirms the problem is only in what the page displays (check done after the first update).
- **Likely cause (not verified):** During the reload `CartPage` briefly renders `CartItem` with the old `enrichedItems`, and `useState(safeItem.quantity)` keeps that old number after the new data arrives.
- **Affected users / impact:** Every customer who changes a quantity on the cart page. The row contradicts itself (qty 2 but $149.85) and the summary. The screen suggests the change was not saved, which invites a click on Update that undoes it. The customer can then check out with a quantity they did not choose.
- **Workaround:** Reload the cart page after each update, or check the summary instead of the quantity box.
- **Severity: High.** It breaks the main job of changing the cart. It quietly overwrites a saved change, which can lead to wrong orders, and it happens on every update.
- **Acceptance criteria:** After an update finishes, the quantity box equals the server quantity, no Update button is shown, and the row and summary agree. With nothing changed, no action should be able to send an old quantity. **Retest:** not retested (no fix available).

## Coverage and handoff
- **Passed:** login; the first cart load shows name, unit price, line total, item count and total matching the API; **+** changes the box and shows Update; the server applies PUT updates and recalculates totals correctly.
- **Not tested (time):** Remove, Clear Cart (confirm dialog), the **−** button and the minimum of 1, updates with several cart lines, API checks on quantities of 0 or below or above stock, adding from product pages, checkout and the resulting order.
- **Next work:** retest CART-01 with several cart lines and after Remove; check that the quantity sent at checkout is the server value; run API checks on quantity limits (`UpdateCartItemDto` validation vs. `stockQuantity`).
- **Cleanup:** Browser session closed. The customer's cart was changed to Desk lamp × 3 (it started at × 2). No orders were created. The owner discards the database.
