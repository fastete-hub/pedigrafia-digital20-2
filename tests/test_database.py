import os
import tempfile
import unittest

import database


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.original_db_name = database.Config.DB_NAME
        database.Config.DB_NAME = os.path.join(self.tmpdir.name, "test.db")
        self.db = database.Database()

    def tearDown(self):
        self.db.close()
        database.Config.DB_NAME = self.original_db_name
        self.tmpdir.cleanup()

    def test_actualizar_informe_con_datos_vacios_no_falla(self):
        pid = self.db.insertar_paciente("Ana", "30", "OS", "a@a.com", "123", "38")
        iid = self.db.insertar_informe(
            {
                "fecha": "2026-02-20",
                "paciente_id": pid,
                "imagen": "img.png",
                "obs_profesional": "ok",
                "recomendacion_plantilla": "ninguna",
                "mediciones": "{}",
            }
        )
        updated_rows = self.db.actualizar_informe(iid, {})
        self.assertEqual(updated_rows, 0)

    def test_actualizar_informe_con_columna_invalida_lanza_error(self):
        pid = self.db.insertar_paciente("Ana", "30", "OS", "a@a.com", "123", "38")
        iid = self.db.insertar_informe(
            {
                "fecha": "2026-02-20",
                "paciente_id": pid,
                "imagen": "img.png",
                "obs_profesional": "ok",
                "recomendacion_plantilla": "ninguna",
                "mediciones": "{}",
            }
        )
        with self.assertRaises(ValueError):
            self.db.actualizar_informe(iid, {"columna_invalida": "x"})


if __name__ == "__main__":
    unittest.main()
