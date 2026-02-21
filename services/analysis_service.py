import json


class AnalysisService:
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
            if not lado or not tipo:
                continue
            valor = m.get("valor_mm")
            if valor is None:
                valor = (m.get("valor_cm") or 0) * 10
            try:
                out[(lado, tipo)] = float(valor)
            except Exception:
                continue
        return out

    @staticmethod
    def comparar_ultimos_dos_estudios(db, paciente_id):
        estudios = db.listar_informes_paciente(paciente_id)
        if len(estudios) < 2:
            raise ValueError("Se necesitan al menos 2 estudios para comparar.")

        # ordenar por fecha ascendente y tomar últimos dos
        estudios_ordenados = sorted(estudios, key=lambda x: x[1])
        ant_id, ant_fecha, _ = estudios_ordenados[-2]
        act_id, act_fecha, _ = estudios_ordenados[-1]

        ant = db.obtener_informe(ant_id)
        act = db.obtener_informe(act_id)

        ant_map = AnalysisService._mediciones_por_clave(ant[6] if ant else None)
        act_map = AnalysisService._mediciones_por_clave(act[6] if act else None)

        claves = sorted(set(ant_map) | set(act_map))
        if not claves:
            return f"Comparación {ant_fecha} → {act_fecha}\n\nNo hay mediciones comparables."

        lineas = [f"Comparación {ant_fecha} → {act_fecha}", ""]
        for lado, tipo in claves:
            v_ant = ant_map.get((lado, tipo))
            v_act = act_map.get((lado, tipo))
            if v_ant is None:
                lineas.append(f"{lado} | {tipo}: nuevo valor {v_act:.1f} mm")
            elif v_act is None:
                lineas.append(f"{lado} | {tipo}: sin dato actual (antes {v_ant:.1f} mm)")
            else:
                delta = v_act - v_ant
                signo = "+" if delta >= 0 else ""
                lineas.append(f"{lado} | {tipo}: {v_ant:.1f} → {v_act:.1f} mm ({signo}{delta:.1f} mm)")

        return "\n".join(lineas)
