"""Small in-memory product/cart domain, inspired by Awesome LocalStack."""

from copy import deepcopy


class ApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


class Store:
    def __init__(self):
        self.products = [{"id": 1, "name": "Workshop notebook", "price": 12, "stockQuantity": 5}]
        self.carts = {"alice": {1: 1}, "bob": {1: 2}}

    def cart(self, username):
        items = [{"productId": pid, "quantity": qty} for pid, qty in self.carts[username].items()]
        return {"username": username, "items": items,
                "totalItems": sum(item["quantity"] for item in items),
                "totalPrice": sum(item["quantity"] * 12 for item in items)}

    def update(self, username, product_id, quantity):
        if type(quantity) is not int or quantity < 0:
            raise ApiError(400, "Quantity must be a non-negative integer")
        if product_id not in self.carts[username]:
            raise ApiError(404, "Cart item not found")
        product = next((p for p in self.products if p["id"] == product_id), None)
        if not product:
            raise ApiError(404, "Product not found")
        if quantity > product["stockQuantity"]:
            raise ApiError(409, "Requested quantity exceeds available stock")
        if quantity == 0:
            del self.carts[username][product_id]
        else:
            self.carts[username][product_id] = quantity
        return self.cart(username)

    def catalog(self):
        return deepcopy(self.products)
