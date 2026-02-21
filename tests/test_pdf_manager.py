import os
import tempfile
import unittest

from PIL import Image
from reportlab.pdfgen import canvas

from pdf_manager import PDFManager


class PDFManagerTests(unittest.TestCase):
    def test_wrap_text_respeta_saltos_y_retorna_y_menor(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dummy.pdf")
            c = canvas.Canvas(out)
            y_inicial = 700
            texto = "Linea uno\n\nLinea dos"

            y_final = PDFManager._wrap_text(c, texto, 50, y_inicial, 200)
            c.save()

            self.assertLess(y_final, y_inicial)
            # 3 descensos esperados: linea uno, linea vacia, linea dos
            self.assertEqual(y_final, y_inicial - (14 * 3))


    def test_wrap_text_soporta_none_y_ancho_invalido(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dummy.pdf")
            c = canvas.Canvas(out)
            y_inicial = 700

            y_none = PDFManager._wrap_text(c, None, 50, y_inicial, 200)
            self.assertEqual(y_none, y_inicial)

            y_invalido = PDFManager._wrap_text(c, "texto", 50, y_inicial, 0)
            self.assertEqual(y_invalido, y_inicial)
            c.save()

    def test_wrap_text_no_agrega_linea_vacia_por_palabra_larga(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "dummy2.pdf")
            c = canvas.Canvas(out)
            y_inicial = 700
            texto = "x" * 200  # una palabra muy larga

            y_final = PDFManager._wrap_text(c, texto, 50, y_inicial, 30)
            c.save()

            self.assertEqual(y_final, y_inicial - 14)

    def test_generar_simple_crea_pdf_con_imagenes(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = os.path.join(tmp, "estudio_original.png")
            mapa = os.path.join(tmp, "estudio_mapa_calor.png")
            salida = os.path.join(tmp, "informe.pdf")

            Image.new("RGB", (50, 50), "white").save(original)
            Image.new("RGB", (50, 50), "red").save(mapa)

            paciente = (1, "Ana", "30", "OSDE", "mail@x.com", "123", "38")
            informe = (
                1,
                "2026-02-20",
                1,
                original,
                "Observación de prueba",
                "Recomendación de prueba",
                "[]",
            )

            ok = PDFManager.generar_simple(paciente, informe, salida)

            self.assertTrue(ok)
            self.assertTrue(os.path.exists(salida))
            self.assertGreater(os.path.getsize(salida), 0)


if __name__ == "__main__":
    unittest.main()
