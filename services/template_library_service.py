class TemplateLibraryService:
    """Biblioteca base de plantillas clínicas para observaciones y recomendaciones."""

    OBSERVACION_TEMPLATES = {
        "normal": (
            "Apoyo plantar dentro de parámetros funcionales para estudio estático. "
            "No se observan asimetrías relevantes en la distribución de cargas."
        ),
        "plano": (
            "Se evidencia tendencia a pie plano con incremento relativo de apoyo en mediopié. "
            "Correlacionar con evaluación clínica, dolor y antecedentes biomecánicos."
        ),
        "cavo": (
            "Se observa tendencia a pie cavo con disminución de apoyo en mediopié y mayor carga en antepié/talón. "
            "Correlacionar con rigidez, sobrecarga lateral y antecedentes funcionales."
        ),
        "asimetria": (
            "Se detecta asimetría de carga entre pie izquierdo y derecho en estudio estático. "
            "Sugerida reevaluación de eje postural y cadena ascendente."
        ),
        "seguimiento": (
            "Comparado con controles previos, se registran cambios en el patrón de apoyo. "
            "Se recomienda seguimiento clínico con misma metodología de captura."
        ),
    }

    RECOMENDACION_TEMPLATES = {
        "descarga": (
            "Indicar plantilla con descarga selectiva en zonas de mayor presión según hallazgos del estudio."
        ),
        "arco": (
            "Considerar soporte de arco longitudinal medial progresivo, con control clínico de adaptación."
        ),
        "talon": (
            "Evaluar elemento de amortiguación/descarga en retropié para reducir sobrecarga de talón."
        ),
        "control": (
            "Sugerir control evolutivo en 60-90 días con nuevo estudio para validar respuesta al tratamiento."
        ),
        "educacion": (
            "Reforzar higiene postural, progresión de uso de plantilla y pauta de ejercicios complementarios."
        ),
    }

    @staticmethod
    def listar_tipos_observacion():
        return sorted(TemplateLibraryService.OBSERVACION_TEMPLATES.keys())

    @staticmethod
    def listar_tipos_recomendacion():
        return sorted(TemplateLibraryService.RECOMENDACION_TEMPLATES.keys())

    @staticmethod
    def obtener_observacion(tipo: str):
        return TemplateLibraryService.OBSERVACION_TEMPLATES.get(tipo)

    @staticmethod
    def obtener_recomendacion(tipo: str):
        return TemplateLibraryService.RECOMENDACION_TEMPLATES.get(tipo)
