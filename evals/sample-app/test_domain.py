"""Existing narrow tests: their green result is not a complete coverage claim."""

import unittest
from domain import ApiError, Store


class CartTests(unittest.TestCase):
    def test_updates_total_and_leaves_other_identity_unchanged(self):
        store = Store()
        self.assertEqual(store.update("alice", 1, 3)["totalPrice"], 36)
        self.assertEqual(store.cart("bob")["totalItems"], 2)

    def test_stock_rejection_preserves_previous_value(self):
        store = Store()
        with self.assertRaises(ApiError) as error:
            store.update("alice", 1, 6)
        self.assertEqual(error.exception.status, 409)
        self.assertEqual(store.cart("alice")["totalItems"], 1)


if __name__ == "__main__":
    unittest.main()
