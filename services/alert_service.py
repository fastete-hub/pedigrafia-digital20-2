class AlertService:
    @staticmethod
    def generar_alertas_mediciones(lines_data):
        """Genera alertas básicas clínicas a partir de mediciones manuales."""
        if not lines_data:
            return []

        # Indexar por (lado, tipo)
        idx = {}
        for m in lines_data:
            lado = m.get("lado")
            tipo = m.get("tipo")
            valor = m.get("valor_mm")
            if lado and tipo and isinstance(valor, (int, float)):
                idx[(lado, tipo)] = float(valor)

        alertas = []

        # Alerta por posible pie plano/cavo usando ratio istmo/metatarso
        for lado in ("IZQ", "DER"):
            meta = idx.get((lado, "Ancho Metatarso"))
            istmo = idx.get((lado, "Ancho Istmo"))
            if meta and istmo and meta > 0:
                ratio = istmo / meta
                if ratio > 0.65:
                    alertas.append(f"{lado}: posible tendencia a pie plano (ratio istmo/metatarso {ratio:.2f}).")
                elif ratio < 0.35:
                    alertas.append(f"{lado}: posible tendencia a pie cavo (ratio istmo/metatarso {ratio:.2f}).")

        # Asimetría entre lados en mediciones comparables
        for tipo in ("Ancho Metatarso", "Ancho Istmo", "Ancho Talón", "Largo Total"):
            izq = idx.get(("IZQ", tipo))
            der = idx.get(("DER", tipo))
            if izq and der and max(izq, der) > 0:
                delta = abs(izq - der)
                if delta / max(izq, der) >= 0.10:
                    alertas.append(f"Asimetría {tipo}: diferencia de {delta:.1f} mm entre IZQ y DER.")

        return alertas
