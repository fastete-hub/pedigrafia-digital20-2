import unittest

from config_mejorado import Config


class HeatmapConfigTests(unittest.TestCase):
    def test_homogeneidad_configurada_por_modo(self):
        self.assertGreaterEqual(Config.HEATMAP_HOMOGENEIDAD_DIGITAL_MEDIAN, 1)
        self.assertGreaterEqual(Config.HEATMAP_HOMOGENEIDAD_DIGITAL_GAUSS, 1)
        self.assertGreaterEqual(Config.HEATMAP_HOMOGENEIDAD_TINTA_MEDIAN, 1)
        self.assertGreaterEqual(Config.HEATMAP_HOMOGENEIDAD_TINTA_GAUSS, 1)


if __name__ == "__main__":
    unittest.main()
