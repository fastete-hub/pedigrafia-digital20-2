import unittest

from services.alert_service import AlertService


class AlertServiceTests(unittest.TestCase):
    def test_alertas_genera_asimetria_y_tendencia(self):
        lines = [
            {"lado": "IZQ", "tipo": "Ancho Metatarso", "valor_mm": 100},
            {"lado": "IZQ", "tipo": "Ancho Istmo", "valor_mm": 70},
            {"lado": "DER", "tipo": "Ancho Metatarso", "valor_mm": 80},
            {"lado": "DER", "tipo": "Ancho Istmo", "valor_mm": 20},
        ]
        alertas = AlertService.generar_alertas_mediciones(lines)
        self.assertTrue(any("pie plano" in a.lower() for a in alertas))
        self.assertTrue(any("pie cavo" in a.lower() for a in alertas))
        self.assertTrue(any("asimetría" in a.lower() for a in alertas))

    def test_semaforo_rojo(self):
        lines = [
            {"lado": "IZQ", "tipo": "Ancho Metatarso", "valor_mm": 100},
            {"lado": "IZQ", "tipo": "Ancho Istmo", "valor_mm": 80},
        ]
        det = AlertService.generar_alertas_detalladas(lines)
        sem = AlertService.resumen_semaforo(det)
        self.assertEqual(sem["nivel"], "ROJO")


if __name__ == "__main__":
    unittest.main()
