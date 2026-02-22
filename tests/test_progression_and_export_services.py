import os
import tempfile
import unittest

import database
from services.export_service import ExportService
from services.progression_service import ProgressionService


class ProgressionAndExportServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_name = database.Config.DB_NAME
        database.Config.DB_NAME = os.path.join(self.tmpdir.name, "svc.db")
        self.db = database.Database()
        self.pid = self.db.insertar_paciente("Ana", "30", "OS", "a@a.com", "123", "38")

    def tearDown(self):
        self.db.close()
        database.Config.DB_NAME = self.original_db_name
        self.tmpdir.cleanup()

    def test_progression_score(self):
        ant = (1, "2026-01-01", self.pid, "img1.png", "", "", '[{"lado":"IZQ","tipo":"Ancho Metatarso","valor_mm":100}]')
        act = (2, "2026-02-01", self.pid, "img2.png", "", "", '[{"lado":"IZQ","tipo":"Ancho Metatarso","valor_mm":102}]')
        out = ProgressionService.score_progresion(ant, act)
        self.assertIn("score", out)
        self.assertIn("nivel", out)

    def test_export_csv_paciente(self):
        self.db.insertar_informe(
            {
                "fecha": "2026-03-01",
                "paciente_id": self.pid,
                "imagen": "img1.png",
                "obs_profesional": "obs",
                "recomendacion_plantilla": "rec",
                "mediciones": "[]",
            }
        )
        out_csv = os.path.join(self.tmpdir.name, "out.csv")
        ruta = ExportService.exportar_csv_paciente(self.db, self.db.obtener_paciente_real(self.pid), out_csv)
        self.assertTrue(os.path.exists(ruta))
        self.assertGreater(os.path.getsize(ruta), 0)


if __name__ == "__main__":
    unittest.main()
