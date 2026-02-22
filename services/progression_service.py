import json


class ProgressionService:
    """Calcula score de progresión clínica básica entre estudios."""

    @staticmethod
    def _mediciones_por_clave(mediciones_json):
        if not mediciones_json:
            return {}
        try:
            meds = json.loads(mediciones_json)
        except Exception:
            return {}

        out = {}
        for m in meds:
            lado = m.get("lado")
            tipo = m.get("tipo")
            valor = m.get("valor_mm")
            if valor is None:
                valor = (m.get("valor_cm") or 0) * 10
            if not lado or not tipo:
                continue
            try:
                out[(lado, tipo)] = float(valor)
            except Exception:
                continue
        return out

    @staticmethod
    def score_progresion(informe_anterior, informe_actual):
        ant = ProgressionService._mediciones_por_clave(informe_anterior[6] if informe_anterior and len(informe_anterior) > 6 else None)
        act = ProgressionService._mediciones_por_clave(informe_actual[6] if informe_actual and len(informe_actual) > 6 else None)
        claves = sorted(set(ant) & set(act))
        if not claves:
            return {"score": 50, "nivel": "NEUTRO", "detalle": "Sin mediciones comparables suficientes."}

        variaciones = []
        for key in claves:
            base = ant.get(key)
            nuevo = act.get(key)
            if base and nuevo:
                variaciones.append(abs((nuevo - base) / base))

        if not variaciones:
            return {"score": 50, "nivel": "NEUTRO", "detalle": "Sin variaciones cuantificables."}

        cambio_medio = sum(variaciones) / len(variaciones)
        # cuanto menor el cambio global, mayor estabilidad clínica del soporte
        score = max(0, min(100, int(round(100 - (cambio_medio * 200)))))

        if score >= 75:
            nivel = "ESTABLE"
            detalle = "Evolución estable en mediciones principales."
        elif score >= 45:
            nivel = "MODERADO"
            detalle = "Cambios moderados; sugerido seguimiento clínico."
        else:
            nivel = "CAMBIO ALTO"
            detalle = "Cambios altos; reevaluar estrategia de plantilla."

        return {"score": score, "nivel": nivel, "detalle": detalle}
