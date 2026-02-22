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

    def _crear_informe_base(self):
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
        return pid, iid

    def test_actualizar_informe_con_datos_vacios_no_falla(self):
        _, iid = self._crear_informe_base()
        updated_rows = self.db.actualizar_informe(iid, {})
        self.assertEqual(updated_rows, 0)

    def test_actualizar_informe_con_columna_invalida_lanza_error(self):
        _, iid = self._crear_informe_base()
        with self.assertRaises(ValueError):
            self.db.actualizar_informe(iid, {"columna_invalida": "x"})

    def test_actualizar_informe_valido_devuelve_una_fila(self):
        _, iid = self._crear_informe_base()
        updated_rows = self.db.actualizar_informe(iid, {"obs_profesional": "actualizado"})
        self.assertEqual(updated_rows, 1)

        informe = self.db.obtener_informe(iid)
        self.assertEqual(informe[4], "actualizado")

    def test_eliminar_paciente_cascada_elimina_informes(self):
        pid, iid = self._crear_informe_base()
        self.db.eliminar_paciente(pid)

        self.assertIsNone(self.db.obtener_paciente_real(pid))
        self.assertIsNone(self.db.obtener_informe(iid))

    def test_eliminar_informe_puntual(self):
        _, iid = self._crear_informe_base()
        self.db.eliminar_informe(iid)
        self.assertIsNone(self.db.obtener_informe(iid))

    def test_close_es_idempotente(self):
        self.db.close()
        # No debe lanzar excepción si se cierra más de una vez
        self.db.close()

    def test_migracion_crea_indices(self):
        idx_rows = self.db.cursor.execute("PRAGMA index_list(informes)").fetchall()
        idx_names = {row[1] for row in idx_rows}
        self.assertIn("idx_informes_paciente_fecha", idx_names)
        self.assertIn("idx_informes_fecha", idx_names)

    def test_guardar_y_listar_postura_estudio(self):
        pid, iid = self._crear_informe_base()
        self.db.insertar_postura_estudio(
            {
                "paciente_id": pid,
                "informe_id": iid,
                "fecha": "2026-02-21",
                "vista": "frente",
                "protocolo": "frontal_basico_v1",
                "imagen_path": "foto.png",
                "escala_px_por_mm": 2.5,
                "puntos_json": "{}",
                "metricas_json": "{}",
                "alertas_json": "[]",
                "obs_postural": "ok",
            }
        )
        rows = self.db.listar_postura_paciente(pid)
        self.assertTrue(rows)


if __name__ == "__main__":
    unittest.main()
