import unittest
import math

from services.posture_rules_service import PostureRulesService
from services.posture_analysis_service import PostureAnalysisService


class PostureServicesTests(unittest.TestCase):
    def test_protocolos_disponibles(self):
        protos = PostureRulesService.listar_protocolos()
        self.assertIn("frontal_basico_v1", protos)

    def test_calculo_frontal(self):
        points = {
            "acromion_izq": (10, 10),
            "acromion_der": (100, 12),
            "eias_izq": (20, 50),
            "eias_der": (110, 50),
            "trocanter_izq": (25, 80),
            "rodilla_izq": (28, 130),
            "maleolo_medial_izq": (30, 190),
            "trocanter_der": (95, 80),
            "rodilla_der": (92, 130),
            "maleolo_medial_der": (90, 190),
        }
        m = PostureAnalysisService.calcular_metricas("frontal_basico_v1", points)
        self.assertIn("angulo_hombros_horizontal_deg", m)
        self.assertIn("angulo_pelvis_horizontal_deg", m)
        self.assertIn("angulo_rodilla_izq_deg", m)
        self.assertIn("angulo_rodilla_der_deg", m)


    def test_calculo_frontal_con_linea_base(self):
        # Hombros con 3° respecto de la horizontal de imagen
        p1 = (0.0, 0.0)
        p2 = (100.0, math.tan(math.radians(3.0)) * 100.0)
        points = {
            "acromion_izq": p1,
            "acromion_der": p2,
            "eias_izq": (0.0, 50.0),
            "eias_der": (100.0, 50.0),
        }
        m = PostureAnalysisService.calcular_metricas("frontal_basico_v1", points, baseline_deg=3.0)
        self.assertAlmostEqual(m["angulo_hombros_horizontal_deg"], 0.0, places=2)

    def test_calculo_lateral_con_mm(self):
        points = {
            "trago": (80, 30),
            "acromion": (60, 40),
            "trocanter": (58, 120),
            "rodilla_lateral": (60, 160),
            "maleolo_lateral": (62, 200),
        }
        m = PostureAnalysisService.calcular_metricas("lateral_basico_v1", points, px_per_mm=2.0)
        self.assertIn("angulo_tronco_vertical_deg", m)
        self.assertIn("desvio_cabeza_mm", m)
        self.assertIn("angulo_rodilla_lateral_deg", m)

    def test_semaforo(self):
        prot = PostureRulesService.obtener_protocolo("frontal_basico_v1")
        nivel, alertas = PostureAnalysisService.evaluar_semaforo(
            {"angulo_hombros_horizontal_deg": 6.0},
            prot["thresholds"],
        )
        self.assertEqual(nivel, "ROJO")
        self.assertTrue(alertas)


if __name__ == "__main__":
    unittest.main()
