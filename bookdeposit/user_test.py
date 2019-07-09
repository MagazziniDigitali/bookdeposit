import unittest
from user import User


class LoginTestCase(unittest.TestCase):

    def test_password_ok(self):
        user = User("raffaele", "messuti")
        resp = user.login()
        self.assertEqual(resp['status'], "OK")

    def test_password_ko(self):
        user = User("raffaele", "666")
        resp = user.login()

        self.assertEqual(resp['status'], "KO")
        self.assertEqual(resp['error'], "PASSWORDERROR")


if __name__ == '__main__':
    unittest.main()
