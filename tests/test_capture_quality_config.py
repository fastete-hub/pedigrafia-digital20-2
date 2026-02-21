import unittest

from config_mejorado import Config


class CaptureQualityConfigTests(unittest.TestCase):
    def test_quality_thresholds_exist(self):
        self.assertGreater(Config.CALIDAD_CAPTURA_AREA_MIN_MM2, 0)
        self.assertGreater(Config.CALIDAD_CAPTURA_DESBALANCE_MAX, 0)
        self.assertGreater(Config.CALIBRACION_CORRECCION_PXMM, 0)


if __name__ == "__main__":
    unittest.main()
