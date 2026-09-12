# Workshop cart requirements

This small sample follows Awesome LocalStack's `/api/v1/products`, `/api/v1/cart`, and `PUT /api/v1/cart/items/{productId}` conventions. It is a separate Python/JavaScript implementation, not the real Spring/React stack and not an equivalent security system.

Scope is viewing an existing cart and updating its existing item. Checkout, adding removed items, and production authentication are not implemented. Restarting the app restores the fixtures.

- **CART-1 — Identity isolation:** a caller sees and changes only their own cart. Anonymous API access is rejected. Use `Authorization: Bearer demo-alice` or `Bearer demo-bob`; these are public disposable fixture tokens. Alice starts with one notebook and Bob with two.
- **CART-2 — Quantity:** updates accept non-negative integers; zero removes the item. Negative, fractional, missing, null, string, and boolean quantities are rejected with 400 and leave the cart unchanged.
- **CART-3 — Availability:** requesting more than the product's five units of stock returns 409 and leaves the cart unchanged. Cart changes do not reserve or decrement stock.
- **CART-4 — Totals:** `totalItems` is the sum of quantities and `totalPrice` is quantity × the current unit price (12 in this fixture).
- **UI-1 — Explicit save:** editing a quantity is provisional. Save updates the cart and refreshes its visible total. Cancel discards that edit without sending an update request or changing persisted cart state. Reopening Edit shows the saved value.
- **UI-2 — Feedback:** errors are visible, successful saves are acknowledged, and the primary flow remains usable by keyboard at narrow and desktop widths.

Report actual discrepancies against these requirements and prioritize remaining risks. Missing tests or unimplemented out-of-scope features are not automatically product defects.
