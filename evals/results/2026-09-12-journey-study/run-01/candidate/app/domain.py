"""Dispatch Desk domain. Amounts use integer cents; state is disposable."""
from copy import deepcopy


class Desk:
    def __init__(self):
        self.orders = {
            "A100": {"id": "A100", "owner": "alice", "paid": 10000, "refunded": 0,
                     "address": "10 Oak Street", "version": 1, "note": "Leave with reception", "service": "standard"},
            "A200": {"id": "A200", "owner": "alice", "paid": 6000, "refunded": 0,
                     "address": "20 Pine Street", "version": 1, "note": "Ring twice", "service": "standard"},
            "B100": {"id": "B100", "owner": "bob", "paid": 4000, "refunded": 0,
                     "address": "30 Elm Street", "version": 1, "note": "Side entrance", "service": "standard"}}

    def visible(self, actor):
        return [deepcopy(o) for o in self.orders.values() if o["owner"] == actor]

    def order(self, actor, order_id):
        row = self.orders.get(order_id)
        if row is None:
            return 404, {"error": "Order not found"}
        if row["owner"] != actor:
            return 403, {"error": "Access denied"}
        return 200, row

    def refund(self, actor, order_id, body):
        status, row = self.order(actor, order_id)
        if status != 200:
            return status, row
        amount = body.get("amount")
        if type(amount) is not int or amount <= 0:
            return 400, {"error": "Amount must be a positive integer in cents"}
        if amount > row["paid"]:
            return 409, {"error": "Refund exceeds remaining paid amount"}
        row["refunded"] += amount
        return 200, deepcopy(row)

    def address(self, actor, order_id, body):
        status, row = self.order(actor, order_id)
        if status != 200:
            return status, row
        address, version = body.get("address"), body.get("version")
        if not isinstance(address, str) or not 1 <= len(address.strip()) <= 120 or type(version) is not int:
            return 400, {"error": "Address and integer version required"}
        if version > row["version"]:
            return 409, {"error": "Order changed; reload before saving"}
        row["address"] = address.strip()
        row["version"] += 1
        return 200, deepcopy(row)

    def services(self, actor, body):
        ids, service = body.get("ids"), body.get("service")
        if not isinstance(ids, list) or not ids or any(not isinstance(i, str) for i in ids) or service not in ("standard", "express"):
            return 400, {"error": "Order IDs and a supported service required"}
        selected = []
        for order_id in ids:
            status, row = self.order(actor, order_id)
            if status != 200:
                return status, row
            row["service"] = service
            selected.append(row)
        for row in selected:
            row["service"] = service
        return 200, {"orders": deepcopy(selected)}

    def note(self, actor, order_id, body):
        status, row = self.order(actor, order_id)
        if status != 200:
            return status, row
        note = body.get("note")
        if not isinstance(note, str) or not 1 <= len(note.strip()) <= 160:
            return 400, {"error": "Note must contain 1 to 160 characters"}
        if note.strip().upper().startswith("LOCKER:"):
            return 422, {"error": "Locker delivery is unavailable; enter another instruction"}
        row["note"] = note
        return 200, deepcopy(row)
