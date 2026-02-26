import math


class PostureAnalysisService:
    @staticmethod
    def _angle_deg(p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.degrees(math.atan2(dy, dx))

    @staticmethod
    def _normalize_relative_angle_deg(angle_deg, baseline_deg=0.0):
        """Normaliza un ángulo relativo a una línea base en rango [-90, 90]."""
        rel = angle_deg - baseline_deg
        while rel <= -180:
            rel += 360
        while rel > 180:
            rel -= 360
        if rel > 90:
            rel -= 180
        elif rel < -90:
            rel += 180
        return rel

    @staticmethod
    def _horizontal_tilt_deg(p1, p2, baseline_deg=0.0):
        ang = PostureAnalysisService._angle_deg(p1, p2)
        return abs(PostureAnalysisService._normalize_relative_angle_deg(ang, baseline_deg))

    @staticmethod
    def _vertical_tilt_deg(p1, p2, baseline_deg=0.0):
        ang = PostureAnalysisService._angle_deg(p1, p2)
        rel = PostureAnalysisService._normalize_relative_angle_deg(ang, baseline_deg)
        return abs(90 - abs(rel))

    @staticmethod
    def _joint_angle_deg(a, b, c):
        """Ángulo ABC en grados (vértice en b)."""
        ba = (a[0] - b[0], a[1] - b[1])
        bc = (c[0] - b[0], c[1] - b[1])
        nba = math.hypot(*ba)
        nbc = math.hypot(*bc)
        if nba == 0 or nbc == 0:
            return 0.0
        dot = ba[0] * bc[0] + ba[1] * bc[1]
        cosang = max(-1.0, min(1.0, dot / (nba * nbc)))
        return math.degrees(math.acos(cosang))

    @staticmethod
    def calcular_metricas(protocol_name, points_map, px_per_mm=None, baseline_deg=0.0):
        m = {}
        if protocol_name in ("frontal_basico_v1", "posterior_basico_v1"):
            if all(k in points_map for k in ("acromion_izq", "acromion_der")):
                m["angulo_hombros_horizontal_deg"] = PostureAnalysisService._horizontal_tilt_deg(
                    points_map["acromion_izq"], points_map["acromion_der"], baseline_deg=baseline_deg
                )
            if all(k in points_map for k in ("eias_izq", "eias_der")):
                m["angulo_pelvis_horizontal_deg"] = PostureAnalysisService._horizontal_tilt_deg(
                    points_map["eias_izq"], points_map["eias_der"], baseline_deg=baseline_deg
                )
            elif all(k in points_map for k in ("eips_izq", "eips_der")):
                m["angulo_pelvis_horizontal_deg"] = PostureAnalysisService._horizontal_tilt_deg(
                    points_map["eips_izq"], points_map["eips_der"], baseline_deg=baseline_deg
                )

        if protocol_name == "frontal_basico_v1":
            if all(k in points_map for k in ("trocanter_izq", "rodilla_izq", "maleolo_medial_izq")):
                m["angulo_rodilla_izq_deg"] = PostureAnalysisService._joint_angle_deg(
                    points_map["trocanter_izq"], points_map["rodilla_izq"], points_map["maleolo_medial_izq"]
                )
            if all(k in points_map for k in ("trocanter_der", "rodilla_der", "maleolo_medial_der")):
                m["angulo_rodilla_der_deg"] = PostureAnalysisService._joint_angle_deg(
                    points_map["trocanter_der"], points_map["rodilla_der"], points_map["maleolo_medial_der"]
                )

        if protocol_name == "posterior_basico_v1":
            if all(k in points_map for k in ("rodilla_izq", "calcaneo_izq")):
                m["inclinacion_retropie_izq_deg"] = PostureAnalysisService._vertical_tilt_deg(
                    points_map["rodilla_izq"], points_map["calcaneo_izq"], baseline_deg=baseline_deg
                )
            if all(k in points_map for k in ("rodilla_der", "calcaneo_der")):
                m["inclinacion_retropie_der_deg"] = PostureAnalysisService._vertical_tilt_deg(
                    points_map["rodilla_der"], points_map["calcaneo_der"], baseline_deg=baseline_deg
                )

        if protocol_name == "lateral_basico_v1":
            if all(k in points_map for k in ("acromion", "trocanter")):
                m["angulo_tronco_vertical_deg"] = PostureAnalysisService._vertical_tilt_deg(
                    points_map["acromion"], points_map["trocanter"], baseline_deg=baseline_deg
                )
            if px_per_mm and all(k in points_map for k in ("trago", "acromion")):
                dx = abs(points_map["trago"][0] - points_map["acromion"][0])
                m["desvio_cabeza_mm"] = dx / px_per_mm
            if all(k in points_map for k in ("trocanter", "rodilla_lateral", "maleolo_lateral")):
                m["angulo_rodilla_lateral_deg"] = PostureAnalysisService._joint_angle_deg(
                    points_map["trocanter"], points_map["rodilla_lateral"], points_map["maleolo_lateral"]
                )

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
