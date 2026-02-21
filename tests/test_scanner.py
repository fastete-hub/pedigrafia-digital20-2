import unittest
from unittest.mock import patch

from scanner import Scanner


class ScannerTests(unittest.TestCase):
    def test_escanear_con_reintentos_recupera_en_tercer_intento(self):
        with patch.object(Scanner, "escanear", side_effect=[None, None, "scan.png"]):
            path, intentos = Scanner.escanear_con_reintentos(max_reintentos=3, espera_s=0)
            self.assertEqual(path, "scan.png")
            self.assertEqual(intentos, 3)

    def test_escanear_con_reintentos_devuelve_none_al_agotar(self):
        with patch.object(Scanner, "escanear", return_value=None):
            path, intentos = Scanner.escanear_con_reintentos(max_reintentos=2, espera_s=0)
            self.assertIsNone(path)
            self.assertEqual(intentos, 2)

    def test_ruta_escaneo_va_a_temp(self):
        path = Scanner._ruta_escaneo_unica("png")
        self.assertIn("temp", path)


if __name__ == "__main__":
    unittest.main()
