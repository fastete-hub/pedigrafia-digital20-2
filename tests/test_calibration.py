import os
import tempfile
import unittest

from PIL import Image

from config_mejorado import Config

try:
    from analysis_mejorado import ImageAnalyzer
    ANALYSIS_AVAILABLE = True
except Exception:
    ANALYSIS_AVAILABLE = False


@unittest.skipUnless(ANALYSIS_AVAILABLE, "analysis_mejorado/cv2 no disponible en este entorno")
class CalibrationTests(unittest.TestCase):
    def test_detectar_calibracion_usa_dpi_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "scan.png")
            Image.new("RGB", (100, 100), "white").save(path, dpi=(300, 300))
            ppm, fuente = ImageAnalyzer.detectar_calibracion_automatica((100, 100, 3), path_img=path, devolver_fuente=True)
            self.assertAlmostEqual(ppm, (300 / 25.4) * Config.CALIBRACION_CORRECCION_PXMM, places=2)
            self.assertEqual(fuente, "DPI")

    def test_detectar_calibracion_fallback_compensa_imagen_unida(self):
        ppm, fuente = ImageAnalyzer.detectar_calibracion_automatica((3508, 4960, 3), path_img=None, devolver_fuente=True)
        self.assertGreater(ppm, 8)
        self.assertLess(ppm, 15)
        self.assertEqual(fuente, "A4")


if __name__ == "__main__":
    unittest.main()
