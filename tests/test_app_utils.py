import unittest

from app_utils import normalize_patient_name, validate_email, validate_phone


class AppUtilsTests(unittest.TestCase):
    def test_normalize_patient_name(self):
        self.assertEqual(normalize_patient_name("  jUAn   pErez  "), "Juan Perez")

    def test_validate_email(self):
        self.assertTrue(validate_email("ana@mail.com")[0])
        self.assertFalse(validate_email("ana_mail.com")[0])

    def test_validate_phone(self):
        self.assertTrue(validate_phone("+54 (11) 5555-1234")[0])
        self.assertFalse(validate_phone("abc###")[0])


if __name__ == "__main__":
    unittest.main()
