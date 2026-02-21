import json


class AlertService:
    @staticmethod
    def _indexar_mediciones(lines_data):
        idx = {}
        for m in lines_data or []:
            lado = m.get("lado")
            tipo = m.get("tipo")
            valor = m.get("valor_mm")
            if lado and tipo and isinstance(valor, (int, float)):
                idx[(lado, tipo)] = float(valor)
        return idx

    @staticmethod
    def generar_alertas_detalladas(lines_data):
        """Genera alertas con severidad: info, warn, critical."""
        idx = AlertService._indexar_mediciones(lines_data)
        if not idx:
            return []

        alertas = []

        for lado in ("IZQ", "DER"):
            meta = idx.get((lado, "Ancho Metatarso"))
            istmo = idx.get((lado, "Ancho Istmo"))
            if meta and istmo and meta > 0:
                ratio = istmo / meta
                if ratio > 0.70:
                    alertas.append({"severity": "critical", "message": f"{lado}: posible pie plano marcado (ratio {ratio:.2f})."})
                elif ratio > 0.65:
                    alertas.append({"severity": "warn", "message": f"{lado}: posible tendencia a pie plano (ratio {ratio:.2f})."})
                elif ratio < 0.30:
                    alertas.append({"severity": "critical", "message": f"{lado}: posible pie cavo marcado (ratio {ratio:.2f})."})
                elif ratio < 0.35:
                    alertas.append({"severity": "warn", "message": f"{lado}: posible tendencia a pie cavo (ratio {ratio:.2f})."})

        for tipo in ("Ancho Metatarso", "Ancho Istmo", "Ancho Talón", "Largo Total"):
            izq = idx.get(("IZQ", tipo))
            der = idx.get(("DER", tipo))
            if izq and der and max(izq, der) > 0:
                delta = abs(izq - der)
                ratio = delta / max(izq, der)
                if ratio >= 0.20:
                    sev = "critical"
                elif ratio >= 0.10:
                    sev = "warn"
                else:
                    sev = None
                if sev:
                    alertas.append({"severity": sev, "message": f"Asimetría {tipo}: diferencia de {delta:.1f} mm entre IZQ y DER."})

        return alertas

    @staticmethod
    def generar_alertas_mediciones(lines_data):
        return [a["message"] for a in AlertService.generar_alertas_detalladas(lines_data)]

    @staticmethod
    def desde_mediciones_json(mediciones_json):
        try:
            meds = json.loads(mediciones_json) if mediciones_json else []
        except Exception:
            meds = []
        return AlertService.generar_alertas_detalladas(meds)

    @staticmethod
    def resumen_semaforo(alertas_detalladas):
        if not alertas_detalladas:
            return {"nivel": "VERDE", "color": "#16a34a", "mensaje": "Sin alertas automáticas"}

        sevs = {a.get("severity") for a in alertas_detalladas}
        if "critical" in sevs:
            return {"nivel": "ROJO", "color": "#dc2626", "mensaje": "Alertas críticas detectadas"}
        if "warn" in sevs:
            return {"nivel": "AMARILLO", "color": "#d97706", "mensaje": "Alertas moderadas detectadas"}
        return {"nivel": "VERDE", "color": "#16a34a", "mensaje": "Sin alertas relevantes"}
