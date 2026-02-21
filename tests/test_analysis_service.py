import os
import tempfile
import unittest

import database
from services.analysis_service import AnalysisService


class AnalysisServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_name = database.Config.DB_NAME
        database.Config.DB_NAME = os.path.join(self.tmpdir.name, "analysis.db")
        self.db = database.Database()

    def tearDown(self):
        self.db.close()
        database.Config.DB_NAME = self.original_db_name
        self.tmpdir.cleanup()

    def test_comparar_ultimos_dos_estudios_ok(self):
        pid = self.db.insertar_paciente("Ana", "30", "OS", "a@a.com", "123456", "250")
        self.db.insertar_informe(
            {
                "fecha": "2026-03-01",
                "paciente_id": pid,
                "imagen": "img1.png",
                "obs_profesional": "",
                "recomendacion_plantilla": "",
                "mediciones": '[{"lado":"IZQ","tipo":"Ancho Metatarso","valor_mm":100}]',
            }
        )
        self.db.insertar_informe(
            {
                "fecha": "2026-03-02",
                "paciente_id": pid,
                "imagen": "img2.png",
                "obs_profesional": "",
                "recomendacion_plantilla": "",
                "mediciones": '[{"lado":"IZQ","tipo":"Ancho Metatarso","valor_mm":110}]',
            }
        )

        txt = AnalysisService.comparar_ultimos_dos_estudios(self.db, pid)
        self.assertIn("Comparación 2026-03-01 → 2026-03-02", txt)
        self.assertIn("+10.0 mm", txt)

    def test_comparar_requiere_dos_estudios(self):
        pid = self.db.insertar_paciente("Ana", "30", "OS", "a@a.com", "123456", "250")
        with self.assertRaises(ValueError):
            AnalysisService.comparar_ultimos_dos_estudios(self.db, pid)


if __name__ == "__main__":
    unittest.main()
