class PostureRulesService:
    """Biblioteca de protocolos posturales estáticos (screening orientativo)."""

    PROTOCOLOS = {
        "frontal_basico_v1": {
            "vista": "frente",
            "points": ["acromion_izq", "acromion_der", "eias_izq", "eias_der"],
            "metrics": ["angulo_hombros_horizontal_deg", "angulo_pelvis_horizontal_deg"],
            "thresholds": {
                "angulo_hombros_horizontal_deg": {"warn": 2.0, "critical": 5.0},
                "angulo_pelvis_horizontal_deg": {"warn": 2.0, "critical": 5.0},
            },
        },
        "lateral_basico_v1": {
            "vista": "lateral",
            "points": ["trago", "acromion", "trocanter", "maleolo_lateral"],
            "metrics": ["angulo_tronco_vertical_deg", "desvio_cabeza_mm"],
            "thresholds": {
                "angulo_tronco_vertical_deg": {"warn": 3.0, "critical": 7.0},
                "desvio_cabeza_mm": {"warn": 15.0, "critical": 30.0},
            },
        },
        "posterior_basico_v1": {
            "vista": "espalda",
            "points": ["acromion_izq", "acromion_der", "eips_izq", "eips_der"],
            "metrics": ["angulo_hombros_horizontal_deg", "angulo_pelvis_horizontal_deg"],
            "thresholds": {
                "angulo_hombros_horizontal_deg": {"warn": 2.0, "critical": 5.0},
                "angulo_pelvis_horizontal_deg": {"warn": 2.0, "critical": 5.0},
            },
        },
    }

    @staticmethod
    def listar_protocolos():
        return sorted(PostureRulesService.PROTOCOLOS.keys())

    @staticmethod
    def obtener_protocolo(nombre):
        return PostureRulesService.PROTOCOLOS.get(nombre)
