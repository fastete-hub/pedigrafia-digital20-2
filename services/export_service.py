import csv


class ExportService:
    @staticmethod
    def exportar_csv_paciente(db, paciente, ruta_csv):
        if not db or not paciente or not ruta_csv:
            raise ValueError("Datos inválidos para exportar CSV")

        estudios = db.listar_informes_paciente(paciente[0])
        with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "paciente_id",
                "paciente_nombre",
                "edad",
                "estudio_id",
                "fecha",
                "imagen",
                "obs_profesional",
                "recomendacion_plantilla",
                "mediciones_json",
            ])
            for eid, fecha, imagen in sorted(estudios, key=lambda x: x[1]):
                inf = db.obtener_informe(eid)
                if not inf:
                    continue
                writer.writerow([
                    paciente[0],
                    paciente[1],
                    paciente[2],
                    inf[0],
                    inf[1],
                    inf[3],
                    inf[4],
                    inf[5],
                    inf[6],
                ])
        return ruta_csv
