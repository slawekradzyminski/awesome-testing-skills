"""Existing routine tests; not a complete release assessment."""
import unittest
from domain import Desk


class RoutineTests(unittest.TestCase):
    def test_partial_refund(self):
        desk = Desk()
        status, order = desk.refund('alice', 'A100', {'amount': 1000})
        self.assertEqual((status, order['refunded']), (200, 1000))

    def test_address_save(self):
        desk = Desk()
        status, order = desk.address('alice', 'A100', {'address': 'New Street', 'version': 1})
        self.assertEqual((status, order['version']), (200, 2))

    def test_services(self):
        desk = Desk()
        status, result = desk.services('alice', {'ids': ['A100', 'A200'], 'service': 'express'})
        self.assertEqual(status, 200)
        self.assertTrue(all(o['service'] == 'express' for o in result['orders']))

    def test_note_rejection(self):
        desk = Desk()
        self.assertEqual(desk.note('alice', 'A100', {'note': 'LOCKER: 1'})[0], 422)


if __name__ == '__main__':
    unittest.main()
