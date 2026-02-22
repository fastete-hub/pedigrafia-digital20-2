import math


class PostureAnalysisService:
    @staticmethod
    def _angle_deg(p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.degrees(math.atan2(dy, dx))

    @staticmethod
    def _horizontal_tilt_deg(p1, p2):
        return abs(PostureAnalysisService._angle_deg(p1, p2))

    @staticmethod
    def _vertical_tilt_deg(p1, p2):
        ang = abs(PostureAnalysisService._angle_deg(p1, p2))
        return abs(90 - ang)

    @staticmethod
    def calcular_metricas(protocol_name, points_map, px_per_mm=None):
        m = {}
        if protocol_name in ("frontal_basico_v1", "posterior_basico_v1"):
            if all(k in points_map for k in ("acromion_izq", "acromion_der")):
                m["angulo_hombros_horizontal_deg"] = PostureAnalysisService._horizontal_tilt_deg(
                    points_map["acromion_izq"], points_map["acromion_der"]
                )
            if all(k in points_map for k in ("eias_izq", "eias_der")):
                m["angulo_pelvis_horizontal_deg"] = PostureAnalysisService._horizontal_tilt_deg(
                    points_map["eias_izq"], points_map["eias_der"]
                )
            elif all(k in points_map for k in ("eips_izq", "eips_der")):
                m["angulo_pelvis_horizontal_deg"] = PostureAnalysisService._horizontal_tilt_deg(
                    points_map["eips_izq"], points_map["eips_der"]
                )

        if protocol_name == "lateral_basico_v1":
            if all(k in points_map for k in ("acromion", "trocanter")):
                m["angulo_tronco_vertical_deg"] = PostureAnalysisService._vertical_tilt_deg(
                    points_map["acromion"], points_map["trocanter"]
                )
            if px_per_mm and all(k in points_map for k in ("trago", "acromion")):
                dx = abs(points_map["trago"][0] - points_map["acromion"][0])
                m["desvio_cabeza_mm"] = dx / px_per_mm

        return m

    @staticmethod
    def evaluar_semaforo(metricas, thresholds):
        alertas = []
        worst = "VERDE"
        for key, val in metricas.items():
            t = thresholds.get(key)
            if not t:
                continue
            if val > t["critical"]:
                worst = "ROJO"
                alertas.append({"severity": "critical", "metric": key, "value": val})
            elif val > t["warn"]:
                if worst != "ROJO":
                    worst = "AMARILLO"
                alertas.append({"severity": "warn", "metric": key, "value": val})
        return worst, alertas
