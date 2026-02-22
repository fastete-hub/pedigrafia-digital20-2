class PostureRulesService:
    """Biblioteca de protocolos posturales estáticos (screening orientativo).

    Referencias orientativas usadas para definir puntos/umbrales:
    - observación postural estática clínica en planos frontal y sagital,
    - inclinación de cinturas escapular/pélvica,
    - alineación de eje de miembro inferior y control de valgo/varo funcional.
    """

    PROTOCOLOS = {
        "frontal_basico_v1": {
            "vista": "frente",
            "points": [
                "acromion_izq", "acromion_der",
                "eias_izq", "eias_der",
                "trocanter_izq", "trocanter_der",
                "rodilla_izq", "rodilla_der",
                "maleolo_medial_izq", "maleolo_medial_der",
            ],
            "segments": [
                ["acromion_izq", "acromion_der"],
                ["eias_izq", "eias_der"],
                ["trocanter_izq", "rodilla_izq"],
                ["rodilla_izq", "maleolo_medial_izq"],
                ["trocanter_der", "rodilla_der"],
                ["rodilla_der", "maleolo_medial_der"],
            ],
            "metrics": [
                "angulo_hombros_horizontal_deg",
                "angulo_pelvis_horizontal_deg",
                "angulo_rodilla_izq_deg",
                "angulo_rodilla_der_deg",
            ],
            "thresholds": {
                "angulo_hombros_horizontal_deg": {"warn": 2.0, "critical": 5.0},
                "angulo_pelvis_horizontal_deg": {"warn": 2.0, "critical": 5.0},
                "angulo_rodilla_izq_deg": {"warn": 15.0, "critical": 20.0},
                "angulo_rodilla_der_deg": {"warn": 15.0, "critical": 20.0},
            },
        },
        "lateral_basico_v1": {
            "vista": "lateral",
            "points": ["trago", "acromion", "trocanter", "rodilla_lateral", "maleolo_lateral"],
            "segments": [
                ["trago", "acromion"],
                ["acromion", "trocanter"],
                ["trocanter", "rodilla_lateral"],
                ["rodilla_lateral", "maleolo_lateral"],
            ],
            "metrics": ["angulo_tronco_vertical_deg", "desvio_cabeza_mm", "angulo_rodilla_lateral_deg"],
            "thresholds": {
                "angulo_tronco_vertical_deg": {"warn": 3.0, "critical": 7.0},
                "desvio_cabeza_mm": {"warn": 15.0, "critical": 30.0},
                "angulo_rodilla_lateral_deg": {"warn": 15.0, "critical": 20.0},
            },
        },
        "posterior_basico_v1": {
            "vista": "espalda",
            "points": [
                "acromion_izq", "acromion_der",
                "eips_izq", "eips_der",
                "rodilla_izq", "rodilla_der",
                "calcaneo_izq", "calcaneo_der",
            ],
            "segments": [
                ["acromion_izq", "acromion_der"],
                ["eips_izq", "eips_der"],
                ["rodilla_izq", "calcaneo_izq"],
                ["rodilla_der", "calcaneo_der"],
            ],
            "metrics": [
                "angulo_hombros_horizontal_deg",
                "angulo_pelvis_horizontal_deg",
                "inclinacion_retropie_izq_deg",
                "inclinacion_retropie_der_deg",
            ],
            "thresholds": {
                "angulo_hombros_horizontal_deg": {"warn": 2.0, "critical": 5.0},
                "angulo_pelvis_horizontal_deg": {"warn": 2.0, "critical": 5.0},
                "inclinacion_retropie_izq_deg": {"warn": 5.0, "critical": 8.0},
                "inclinacion_retropie_der_deg": {"warn": 5.0, "critical": 8.0},
            },
        },
    }

    @staticmethod
    def listar_protocolos():
        return sorted(PostureRulesService.PROTOCOLOS.keys())

    @staticmethod
    def obtener_protocolo(nombre):
        return PostureRulesService.PROTOCOLOS.get(nombre)
