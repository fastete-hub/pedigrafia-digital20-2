import sqlite3
from pathlib import Path

from config_mejorado import Config


class Database:
    VALID_INFORME_COLUMNS = {
        "fecha",
        "paciente_id",
        "imagen",
        "obs_profesional",
        "recomendacion_plantilla",
        "mediciones",
    }

    def __init__(self):
        db_path = Path(Config.DB_NAME)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.cursor = self.conn.cursor()
        self.crear_tablas()
        self.reparar_tabla_pacientes()
        self.aplicar_migraciones()

    def crear_tablas(self):
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS pacientes
            (id INTEGER PRIMARY KEY, nombre TEXT, edad TEXT, obra_social TEXT, mail TEXT, tel TEXT, talle TEXT)'''
        )
        self.cursor.execute(
            '''CREATE TABLE IF NOT EXISTS informes
            (id INTEGER PRIMARY KEY, fecha TEXT, paciente_id INTEGER, imagen TEXT,
            obs_profesional TEXT, recomendacion_plantilla TEXT, mediciones TEXT,
            FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE)'''
        )
        self.conn.commit()

    def reparar_tabla_pacientes(self):
        """Agrega columnas faltantes si la tabla ya existía de versiones viejas."""
        columnas_necesarias = ["mail", "tel", "talle"]
        self.cursor.execute("PRAGMA table_info(pacientes)")
        columnas_actuales = [col[1] for col in self.cursor.fetchall()]

        for col in columnas_necesarias:
            if col not in columnas_actuales:
                try:
                    self.cursor.execute(f"ALTER TABLE pacientes ADD COLUMN {col} TEXT")
                except sqlite3.OperationalError:
                    # Si hay una condición de carrera o la columna ya existe, continuamos.
                    pass
        self.conn.commit()

    def aplicar_migraciones(self):
        """Migraciones no destructivas para mejorar estabilidad y performance."""
        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )

        self.cursor.execute("SELECT version FROM schema_migrations")
        existentes = {row[0] for row in self.cursor.fetchall()}

        if 1 not in existentes:
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_informes_paciente_fecha ON informes(paciente_id, fecha)"
            )
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_informes_fecha ON informes(fecha)"
            )
            self.cursor.execute("INSERT INTO schema_migrations(version) VALUES (1)")

        if 2 not in existentes:
            self.cursor.execute(
                '''CREATE TABLE IF NOT EXISTS postura_estudios (
                id INTEGER PRIMARY KEY,
                paciente_id INTEGER NOT NULL,
                informe_id INTEGER,
                fecha TEXT,
                vista TEXT,
                protocolo TEXT,
                imagen_path TEXT,
                escala_px_por_mm REAL,
                puntos_json TEXT,
                metricas_json TEXT,
                alertas_json TEXT,
                obs_postural TEXT,
                FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
                FOREIGN KEY(informe_id) REFERENCES informes(id) ON DELETE SET NULL
            )'''
            )
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_postura_paciente_fecha ON postura_estudios(paciente_id, fecha)"
            )
            self.cursor.execute("INSERT INTO schema_migrations(version) VALUES (2)")


        if 3 not in existentes:
            self.cursor.execute(
                """CREATE TABLE IF NOT EXISTS gait_estudios (
                id INTEGER PRIMARY KEY,
                paciente_id INTEGER NOT NULL,
                informe_id INTEGER,
                fecha TEXT,
                fuente_path TEXT,
                resumen_json TEXT,
                curva_izq_json TEXT,
                curva_der_json TEXT,
                grafico_path TEXT,
                observaciones TEXT,
                FOREIGN KEY(paciente_id) REFERENCES pacientes(id) ON DELETE CASCADE,
                FOREIGN KEY(informe_id) REFERENCES informes(id) ON DELETE SET NULL
            )"""
            )
            self.cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_gait_paciente_fecha ON gait_estudios(paciente_id, fecha)"
            )
            self.cursor.execute("INSERT INTO schema_migrations(version) VALUES (3)")

        self.conn.commit()

    def contar_stats(self):
        p = self.cursor.execute("SELECT COUNT(*) FROM pacientes").fetchone()[0]
        i = self.cursor.execute("SELECT COUNT(*) FROM informes").fetchone()[0]
        return p, i

    def insertar_paciente(self, nom, edad, os, mail, tel, talle):
        self.cursor.execute(
            "INSERT INTO pacientes (nombre, edad, obra_social, mail, tel, talle) VALUES (?,?,?,?,?,?)",
            (nom, edad, os, mail, tel, talle),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def buscar_pacientes(self, query):
        return self.cursor.execute("SELECT * FROM pacientes WHERE nombre LIKE ?", (f'%{query}%',)).fetchall()

    def obtener_paciente_real(self, pid):
        return self.cursor.execute("SELECT * FROM pacientes WHERE id = ?", (pid,)).fetchone()

    def listar_informes_paciente(self, pid):
        return self.cursor.execute("SELECT id, fecha, imagen FROM informes WHERE paciente_id = ?", (pid,)).fetchall()

    def obtener_informe(self, eid):
        return self.cursor.execute("SELECT * FROM informes WHERE id = ?", (eid,)).fetchone()

    def eliminar_informe(self, eid):
        self.cursor.execute("DELETE FROM informes WHERE id = ?", (eid,))
        self.conn.commit()

    def eliminar_paciente(self, pid):
        """Elimina paciente y sus informes, compatible con esquemas viejos sin FK."""
        self.cursor.execute("DELETE FROM informes WHERE paciente_id = ?", (pid,))
        self.cursor.execute("DELETE FROM pacientes WHERE id = ?", (pid,))
        self.conn.commit()

    def insertar_informe(self, d):
        self.cursor.execute(
            "INSERT INTO informes (fecha, paciente_id, imagen, obs_profesional, recomendacion_plantilla, mediciones) VALUES (?,?,?,?,?,?)",
            (
                d['fecha'],
                d['paciente_id'],
                d['imagen'],
                d['obs_profesional'],
                d['recomendacion_plantilla'],
                d['mediciones'],
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def actualizar_informe(self, iid, datos):
        if not datos:
            return 0

        invalid_columns = set(datos) - self.VALID_INFORME_COLUMNS
        if invalid_columns:
            raise ValueError(f"Columnas inválidas para informes: {sorted(invalid_columns)}")

        sets = ", ".join([f"{k} = ?" for k in datos.keys()])
        sql = f"UPDATE informes SET {sets} WHERE id = ?"
        params = list(datos.values()) + [iid]
        self.cursor.execute(sql, params)
        self.conn.commit()
        return self.cursor.rowcount

    def insertar_gait_estudio(self, d):
        self.cursor.execute(
            """INSERT INTO gait_estudios
            (paciente_id, informe_id, fecha, fuente_path, resumen_json, curva_izq_json, curva_der_json, grafico_path, observaciones)
            VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                d.get("paciente_id"),
                d.get("informe_id"),
                d.get("fecha"),
                d.get("fuente_path"),
                d.get("resumen_json"),
                d.get("curva_izq_json"),
                d.get("curva_der_json"),
                d.get("grafico_path"),
                d.get("observaciones"),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def listar_gait_paciente(self, paciente_id):
        return self.cursor.execute(
            "SELECT id, fecha, fuente_path, grafico_path FROM gait_estudios WHERE paciente_id = ? ORDER BY fecha DESC",
            (paciente_id,),
        ).fetchall()

    def close(self):
        if getattr(self, "cursor", None) is not None:
            self.cursor.close()
            self.cursor = None
        if getattr(self, "conn", None) is not None:
            self.conn.close()
            self.conn = None

    def __del__(self):
        self.close()

    def insertar_postura_estudio(self, d):
        self.cursor.execute(
            """INSERT INTO postura_estudios
            (paciente_id, informe_id, fecha, vista, protocolo, imagen_path, escala_px_por_mm,
             puntos_json, metricas_json, alertas_json, obs_postural)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                d.get("paciente_id"),
                d.get("informe_id"),
                d.get("fecha"),
                d.get("vista"),
                d.get("protocolo"),
                d.get("imagen_path"),
                d.get("escala_px_por_mm"),
                d.get("puntos_json"),
                d.get("metricas_json"),
                d.get("alertas_json"),
                d.get("obs_postural"),
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid


    def obtener_postura_por_informe(self, informe_id):
        if informe_id is None:
            return None
        return self.cursor.execute(
            """SELECT id, fecha, vista, protocolo, imagen_path, escala_px_por_mm,
                      puntos_json, metricas_json, alertas_json, obs_postural
               FROM postura_estudios
               WHERE informe_id = ?
               ORDER BY id DESC LIMIT 1""",
            (informe_id,),
        ).fetchone()

    def listar_postura_por_informe(self, informe_id):
        if informe_id is None:
            return []
        return self.cursor.execute(
            """SELECT id, fecha, vista, protocolo, imagen_path, escala_px_por_mm,
                      puntos_json, metricas_json, alertas_json, obs_postural
               FROM postura_estudios
               WHERE informe_id = ?
               ORDER BY id DESC""",
            (informe_id,),
        ).fetchall()

    def listar_postura_paciente(self, paciente_id):
        return self.cursor.execute(
            "SELECT id, fecha, vista, protocolo, imagen_path FROM postura_estudios WHERE paciente_id = ? ORDER BY fecha DESC",
            (paciente_id,),
        ).fetchall()
