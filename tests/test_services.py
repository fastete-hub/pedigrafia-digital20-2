import unittest
from unittest.mock import patch

from services.patient_service import PatientService
from services.report_service import ReportService


class PatientServiceTests(unittest.TestCase):
    def test_validar_y_normalizar_ok(self):
        datos = PatientService.validar_y_normalizar(
            "  jUAn   pErez ", "30", "OS", "juan@mail.com", "+54 11 5555-1111", "250"
        )
        self.assertEqual(datos["nombre"], "Juan Perez")

    def test_validar_y_normalizar_falla_email(self):
        with self.assertRaises(ValueError):
            PatientService.validar_y_normalizar("Ana", "30", "OS", "ana_mail.com", "123456", "250")


class ReportServiceTests(unittest.TestCase):
    def test_generar_pdf_valida_entrada(self):
        with self.assertRaises(ValueError):
            ReportService.generar_pdf(None, None, "")

    def test_generar_pdf_ok(self):
        with patch("services.report_service.PDFManager.generar_simple", return_value=True):
            ruta = ReportService.generar_pdf((1,), (1,), "x.pdf")
            self.assertEqual(ruta, "x.pdf")

    def test_generar_pdf_comparativo_valida_entrada(self):
        with self.assertRaises(ValueError):
            ReportService.generar_pdf_comparativo(None, None, None, "")

    def test_generar_pdf_comparativo_ok(self):
        with patch("services.report_service.PDFManager.generar_comparativo", return_value=True):
            ruta = ReportService.generar_pdf_comparativo((1,), (1,), (2,), "comparativo.pdf")
            self.assertEqual(ruta, "comparativo.pdf")

    def test_generar_pdf_comparativo_con_historial(self):
        with patch("services.report_service.PDFManager.generar_comparativo", return_value=True) as mocked:
            ruta = ReportService.generar_pdf_comparativo(
                (1,), (1,), (2,), "comparativo.pdf", historial_informes=[(1,), (2,), (3,)]
            )
            self.assertEqual(ruta, "comparativo.pdf")
            self.assertTrue(mocked.called)


if __name__ == "__main__":
    unittest.main()
