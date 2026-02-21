import os
import tempfile
import unittest

from PIL import Image

import database
from pdf_manager import PDFManager


class IntegrationFlowTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_name = database.Config.DB_NAME
        database.Config.DB_NAME = os.path.join(self.tmpdir.name, "integration.db")
        self.db = database.Database()

    def tearDown(self):
        self.db.close()
        database.Config.DB_NAME = self.original_db_name
        self.tmpdir.cleanup()

    def test_flujo_crear_informe_generar_pdf_y_borrar(self):
        paciente_id = self.db.insertar_paciente("Ana Test", "30", "OS", "ana@test.com", "+54 11 5555 0000", "250")

        original = os.path.join(self.tmpdir.name, "estudio_original.png")
        mapa = os.path.join(self.tmpdir.name, "estudio_mapa_calor.png")
        salida_pdf = os.path.join(self.tmpdir.name, "informe.pdf")

        Image.new("RGB", (60, 60), "white").save(original)
        Image.new("RGB", (60, 60), "red").save(mapa)

        informe_id = self.db.insertar_informe(
            {
                "fecha": "2026-03-01",
                "paciente_id": paciente_id,
                "imagen": original,
                "obs_profesional": "Obs",
                "recomendacion_plantilla": "Reco",
                "mediciones": "[]",
            }
        )

        paciente = self.db.obtener_paciente_real(paciente_id)
        informe = self.db.obtener_informe(informe_id)
        self.assertTrue(PDFManager.generar_simple(paciente, informe, salida_pdf))
        self.assertTrue(os.path.exists(salida_pdf))

        self.db.eliminar_paciente(paciente_id)
        self.assertIsNone(self.db.obtener_paciente_real(paciente_id))
        self.assertIsNone(self.db.obtener_informe(informe_id))


if __name__ == "__main__":
    unittest.main()
