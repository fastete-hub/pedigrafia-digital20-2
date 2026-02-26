from pdf_manager import PDFManager


class ReportService:
    @staticmethod
    def generar_pdf(paciente, informe, ruta_pdf, postura_estudio=None, postura_estudios=None, postural_mode="compacto"):
        if not paciente or not informe:
            raise ValueError("Paciente o informe inválido")
        if not ruta_pdf:
            raise ValueError("Ruta de PDF inválida")

        ok = PDFManager.generar_simple(paciente, informe, ruta_pdf, postura_estudio=postura_estudio, postura_estudios=postura_estudios, postural_mode=postural_mode)
        if not ok:
            raise RuntimeError("No se pudo generar el PDF")
        return ruta_pdf

    @staticmethod
    def generar_pdf_comparativo(paciente, informe_anterior, informe_actual, ruta_pdf, historial_informes=None):
        if not paciente or not informe_anterior or not informe_actual:
            raise ValueError("Datos inválidos para comparación")
        if not ruta_pdf:
            raise ValueError("Ruta de PDF inválida")

        ok = PDFManager.generar_comparativo(
            paciente,
            informe_anterior,
            informe_actual,
            ruta_pdf,
            historial_informes=historial_informes,
        )
        if not ok:
            raise RuntimeError("No se pudo generar el PDF comparativo")
        return ruta_pdf
