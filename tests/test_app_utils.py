import unittest
from app_utils import (
    normalize_patient_name,
    validate_email,
    validate_phone,
    get_temp_dir,
    get_temp_file_path,
    limpiar_temporales,
    save_runtime_setting,
    load_runtime_settings,
    get_calibracion_correccion_por_modo,
    save_calibracion_correccion_por_modo,
)


class AppUtilsTests(unittest.TestCase):
    def test_normalize_patient_name(self):
        self.assertEqual(normalize_patient_name("  jUAn   pErez  "), "Juan Perez")

    def test_validate_email(self):
        self.assertTrue(validate_email("ana@mail.com")[0])
        self.assertFalse(validate_email("ana_mail.com")[0])

    def test_validate_phone(self):
        self.assertTrue(validate_phone("+54 (11) 5555-1234")[0])
        self.assertFalse(validate_phone("abc###")[0])

    def test_temp_helpers(self):
        d = get_temp_dir("tests")
        self.assertTrue(d.exists())
        f = get_temp_file_path("x", ".tmp", subdir="tests")
        self.assertEqual(f.suffix, ".tmp")

    def test_limpiar_temporales(self):
        stale = get_temp_file_path("old", ".png", subdir="scans")
        stale.write_text("x", encoding="utf-8")
        eliminados = limpiar_temporales(max_horas=0)
        self.assertGreaterEqual(eliminados, 1)

    def test_runtime_settings(self):
        save_runtime_setting("calibracion_correccion_pxmm", 0.9)
        data = load_runtime_settings()
        self.assertIn("calibracion_correccion_pxmm", data)

    def test_calibracion_por_modo(self):
        save_calibracion_correccion_por_modo("Digital", 0.85)
        save_calibracion_correccion_por_modo("Tinta (Papel)", 0.95)

        self.assertEqual(get_calibracion_correccion_por_modo("Digital", 0.8), 0.85)
        self.assertEqual(get_calibracion_correccion_por_modo("Tinta", 0.8), 0.95)


if __name__ == "__main__":
    unittest.main()
